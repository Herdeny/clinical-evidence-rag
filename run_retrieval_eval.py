from urllib import parse

import numpy as np
import pandas as pd
import argparse
import json
from dotenv import load_dotenv

from pathlib import Path
from functools import partial
from retrieve_core import retrieve
from retrieve_evalution import evaluate_retrieval
from retrieve_bm25 import build_bm25, retrieve_bm25
from retrieval_results_io import save_retrieval_results
from langchain_deepseek import ChatDeepSeek
from langchain_huggingface import HuggingFaceEmbeddings
from embedding_index import prepare_document_embeddings
from retrieve_rrf import retrieve_rrf
from openai import APIError
from evidence_review import review_evidence

def main(method, cache_dir, cases_path, evidence_path, run_name, *, config_dir, result_dir, profile_name="deepseek_flash", review=False):
    if any((result_dir / f"{run_name}_{suffix}").exists() for suffix in ("results.jsonl", "summary.json")):
        raise ValueError("Results files has been existed")
    
    root = Path(__file__).resolve().parent
            
    cases_df = pd.read_json(cases_path, lines=True)
    evidence_df = pd.read_json(evidence_path, lines=True)
    config = {
            "cases_path": str(cases_path.resolve()),
            "corpus_name": "medical_v3",
            "evidence_path": str(evidence_path.resolve()),
            "query_template": "Report: {report}\nQuestion: {question}"
        }
    
    config["review"] = {"enabled": False}
    
    review_fn = None
    if review:
        profile_path = config_dir / "llm_profiles.json"
        profile = json.loads(profile_path.read_text(encoding="utf-8"))[profile_name]
        load_dotenv(root / ".env", override=False)
        llm = ChatDeepSeek(**profile)
        
        config["review"]["enabled"] = True
        config["review"]["profile_name"] = profile_name
        config["review"]["llm_profile"] = profile
        
        def review_fn(query, hits):
            try:
                result = review_evidence(query, hits, llm=llm)  # 将当前题交给同一个客户端评估。
                return result
            except APIError as exc:
                result = {
                    "original_query": query,
                    "status": "error",
                    "review": None,
                    "usage_metadata": None,
                    "response_metadata": None,
                    "error": f"{type(exc).__name__}: {exc}"
                }
                return result
                
    
    if method in ("dense", "rrf"):

        PREFIX = "Represent this sentence for searching relevant passages: "
        
        embedding_model = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs = {"device": "cuda", "revision": "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a", "local_files_only": True}, # 最后两个参数的意义是什么？
            encode_kwargs = {"batch_size": 8, "normalize_embeddings": True, "prompt": ""},
            query_encode_kwargs = {"batch_size": 1, "normalize_embeddings": True, "prompt": PREFIX}
        )

        embeddings, cache_info = prepare_document_embeddings(
            evidence_df, embedding_model, evidence_path=evidence_path, cache_dir=cache_dir, chunk_size=512
            )

        dense_retrieve_fn = partial(
            retrieve,
            embedding_model=embedding_model,
            evidences=evidence_df,
            embeddings=embeddings
        )
        config["dense"] = {
            "device": embedding_model.model_kwargs["device"],
            "embeddings_cache": cache_info,
            "embeddings_shape": embeddings.shape,
            "encode_kwargs": embedding_model.encode_kwargs,
            "model_name": embedding_model.model_name,
            "query_encode_kwargs": embedding_model.query_encode_kwargs,
            "query_prefix": PREFIX
        }

        
    if method in ("bm25", "rrf"):
        bm25_results = build_bm25(evidence_df, k1=1.5, b=0.75, epsilon=0.25)
        bm25_retrieve_fn = partial(
            retrieve_bm25,
            bm25_index=bm25_results,
            evidences=evidence_df
        )
        config["bm25"] = {
            "model_name": "rank_bm25.BM25Okapi",
            "device": "cpu",
            "query_prefix": "",
            "k1": 1.5,
            "b": 0.75,
            "epsilon": 0.25
        }
        
    if method == "dense":
        retrieve_fn = dense_retrieve_fn
        config["retrieval_method"] = "dense"
    elif method == "bm25":
        retrieve_fn = bm25_retrieve_fn
        config["retrieval_method"] = "bm25"
    elif method == "rrf":
        retrieve_fn = partial(
            retrieve_rrf,
            dense_retrieve_fn=dense_retrieve_fn,
            bm25_retrieve_fn=bm25_retrieve_fn,
            candidate_k=20,
            rrf_constant=60
        )
        config["retrieval_method"] = "rrf"
        config["rrf"] = {
            "candidate_k": 20,
            "rrf_constant": 60
        }
    
    eval_df = evaluate_retrieval(cases_df, retrieve_fn, ks=(1, 3, 5), review_fn=review_fn)
    summary = save_retrieval_results(
        eval_df,
        config=config,
        run_name=run_name,
        result_dir=result_dir
    )
    return summary
        

if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=["dense", "bm25", "rrf"], default="dense") # 指定检索方法
    parser.add_argument("--cache", type=Path, default=root / "cache" / "embeddings") # 指定缓存文件路径
    parser.add_argument("--cases", type=Path, default=root / "data" / "v3" / "cases.ct.dev.jsonl") # 指定题目文件路径
    parser.add_argument("--evidences", type=Path, default=root / "data" / "v3" / "evidence.jsonl") # 指定证据文件路径
    parser.add_argument("--review", default=False, action="store_true") # action = store_true 这个参数作用？
    parser.add_argument("--config", type=Path, default=root / "configs")
    parser.add_argument("--result-dir", type=Path, default=root / "results")
    parser.add_argument("--profile", default="deepseek_flash")
    parser.add_argument("--run-name") # 指定本次结果名称
    args = parser.parse_args()
    
    method = args.method
    cache_path = args.cache
    cases_path =  args.cases
    evidences_path = args.evidences
    review = args.review
    config_path = args.config
    profile_name = args.profile
    result_path = args.result_dir
    run_name = args.run_name if args.run_name else f"medical_v3_{method}_ct_dev"
    
    summary = main(method, cache_path, cases_path, evidences_path, run_name, config_dir=config_path, result_dir=result_path, profile_name=profile_name, review=review)
    
    if review:  # 开启评估时展示状态、用量和分阶段耗时。
        print(json.dumps(summary, ensure_ascii=False, indent=2))  # 打印完整摘要。
    else:  # 关闭评估时沿用原来的输出。
        print(summary["metrics"])  # 打印检索指标。
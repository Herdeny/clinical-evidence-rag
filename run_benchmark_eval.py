import argparse
from functools import partial
from langchain_huggingface import HuggingFaceEmbeddings
from pathlib import Path
from benchmark_data import load_beir_dataset
from benchmark_eval import evaluate_beir_retrieval
from embedding_index import prepare_document_embeddings
from retrieval_results_io import save_beir_results
from retrieve_bm25 import build_bm25
from retrieve_bm25 import retrieve_bm25
from retrieve_core import retrieve
from retrieve_rrf import retrieve_rrf

def main(method, data_dir, split, cache_dir, run_name):
    if not method in ("dense", "bm25", "rrf"): raise ValueError(f"Unknown method: {method}")
    evidence_path = data_dir / "corpus.jsonl"
    
    corpus_df, queries_df, qrels = load_beir_dataset(data_dir, split=split)
     
    config = {
            "cache_path": str(cache_dir.resolve()),
            "corpus_text": "title + space + body; strip",
            "dataset_name": data_dir.name,
            "data_dir": str(data_dir.resolve()),
            "ks": [10, 100],
            "query_template": "{query}",
            "split": split,
            "retrieval_method": method
        }
    
    if method in ("dense", "rrf"):

        PREFIX = "Represent this sentence for searching relevant passages: "
        
        embedding_model = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs = {"device": "cuda", "revision": "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a", "local_files_only": True}, # 最后两个参数的意义是什么？
            encode_kwargs = {"batch_size": 8, "normalize_embeddings": True, "prompt": ""},
            query_encode_kwargs = {"batch_size": 1, "normalize_embeddings": True, "prompt": PREFIX}
        )

        embeddings, cache_info = prepare_document_embeddings(
            corpus_df, embedding_model, evidence_path=evidence_path, cache_dir=cache_dir, chunk_size=512
            )

        dense_retrieve_fn = partial(
            retrieve,
            embedding_model=embedding_model,
            evidences=corpus_df,
            embeddings=embeddings
        )
        config["dense"] = {
            "device": embedding_model.model_kwargs["device"],
            "embeddings_cache": cache_info,
            "embeddings_shape": embeddings.shape,
            "encode_kwargs": embedding_model.encode_kwargs,
            "max_seq_length": 512,
            "model_kwargs": embedding_model.model_kwargs,
            "model_name": embedding_model.model_name,
            "query_encode_kwargs": embedding_model.query_encode_kwargs,
            "query_prefix": PREFIX
        }

        
    if method in ("bm25", "rrf"):
        bm25_results = build_bm25(corpus_df, k1=1.5, b=0.75, epsilon=0.25)
        bm25_retrieve_fn = partial(
            retrieve_bm25,
            bm25_index=bm25_results,
            evidences=corpus_df
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
            candidate_k=100,
            rrf_constant=60
        )
        config["retrieval_method"] = "rrf"
        config["rrf"] = {
            "candidate_k": 100,
            "rrf_constant": 60
        }
    
    eval_df, run = evaluate_beir_retrieval(queries_df, qrels, retrieve_fn, ks=(10,100))
    summary = save_beir_results(
        eval_df,
        run,
        config=config,
        run_name=run_name,
        result_dir=Path(__file__).resolve().parent / "results"
    )
    return summary


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=["dense", "bm25", "rrf"], default="bm25") # 指定检索方法
    parser.add_argument("--cache", type=Path, default=root / "cache" / "embeddings") # 指定缓存文件路径
    parser.add_argument("--data-dir", type=Path, default=root / "data" / "external" / "nfcorpus" / "prepared" / "nfcorpus" ) # 指定数据文件路径
    parser.add_argument("--split", choices=["dev", "train", "test"], default="dev") # 指定划分方式
    parser.add_argument("--run-name") # 指定本次结果名称
    args = parser.parse_args()
    
    method = args.method
    cache_dir = args.cache
    data_dir =  args.data_dir
    split = args.split
    run_name = args.run_name if args.run_name else f"{data_dir.name}_{method}_{split}"
    
    summary = main(method, data_dir, split, cache_dir, run_name)
    
    print(summary["metrics"])
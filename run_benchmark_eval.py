import argparse
from functools import partial
import json
from pathlib import Path

from benchmark_data import load_beir_dataset
from benchmark_eval import evaluate_beir_retrieval
from embedding_index import prepare_document_embeddings
from embedding_adapter import build_embedding_model
from retrieval_results_io import save_beir_results
from retrieve_bm25 import build_bm25
from retrieve_bm25 import retrieve_bm25
from retrieve_core import retrieve
from retrieve_rrf import retrieve_rrf

def main(method, config_dir, data_dir, split, cache_dir, run_name, *, config_embedding_model="bge_small"):
    if not method in ("bm25", "dense", "rrf"): raise ValueError("Unknown method: " + method)

    if method == "bm25" and config_embedding_model == "qwen3_8b": raise ValueError("qwen3_8b doesn't fit with bm25.")

    config_path = config_dir / "embedding_profiles.json"
    evidence_path = data_dir / "corpus.jsonl"

    profiles = json.loads(config_path.read_text(encoding="utf-8"))

    if not config_embedding_model in profiles: raise ValueError("Unknown embedding model profile: " + config_embedding_model)

    embedding_profile = profiles[config_embedding_model]

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
        embedding_model = build_embedding_model(
            profile=embedding_profile
        )

        # 核对模型的真实维度、长度与配置一致
        if not (
            embedding_model._client.get_embedding_dimension() == embedding_profile['dimension']
            and
            embedding_model._client.max_seq_length == embedding_profile['max_seq_length']
            ):
            raise ValueError("embedding_profile is not consistent with the real model")

        embeddings, cache_info = prepare_document_embeddings(
            corpus_df, embedding_model, evidence_path=evidence_path, cache_dir=cache_dir, chunk_size=512, dimension=embedding_profile['dimension']
            )

        dense_retrieve_fn = partial(
            retrieve,
            embedding_model=embedding_model,
            evidences=corpus_df,
            embeddings=embeddings
        )
        config["dense"] = {
            "device": embedding_model.model_kwargs["device"],
            "embedding_dimension": embedding_profile['dimension'],
            "embedding_profile": config_embedding_model,
            "embeddings_cache": cache_info,
            "embeddings_shape": embeddings.shape,
            "encode_kwargs": embedding_model.encode_kwargs,
            "max_seq_length": embedding_profile['max_seq_length'],
            "model_kwargs": embedding_model.model_kwargs,
            "model_name": embedding_model.model_name,
            "query_encode_kwargs": embedding_model.query_encode_kwargs,
            "query_prefix": embedding_model.query_encode_kwargs["prompt"]
        }

        if getattr(embedding_model, "output_normalization", None):
            config["dense"]["output_normalization"] = embedding_model.output_normalization
        else:
            config["dense"]["output_normalization"] = "model_native"

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
    parser.add_argument("--config", type=Path, default=root / "configs") # 指定配置文件路径
    parser.add_argument("--data-dir", type=Path, default=root / "data" / "external" / "nfcorpus" / "prepared" / "nfcorpus" ) # 指定数据文件路径
    parser.add_argument("--config-embedding-model", choices=["bge_small", "qwen3_8b"], default="bge_small")
    parser.add_argument("--split", choices=["dev", "train", "test"], default="dev") # 指定划分方式
    parser.add_argument("--run-name") # 指定本次结果名称
    args = parser.parse_args()

    method = args.method
    cache_dir = args.cache
    config_dir = args.config
    config_embedding_model = args.config_embedding_model
    data_dir =  args.data_dir
    split = args.split
    run_name = args.run_name if args.run_name else f"{data_dir.name}_{method}_{config_embedding_model}_{split}"

    summary = main(method, config_dir, data_dir, split, cache_dir, run_name, config_embedding_model=config_embedding_model)

    print(summary["metrics"])

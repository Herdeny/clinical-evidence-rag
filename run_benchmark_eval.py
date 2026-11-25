import argparse
import json
import hashlib

from pathlib import Path
from functools import partial

from benchmark_data import load_beir_dataset
from benchmark_eval import evaluate_beir_retrieval, evaluate_query_rewrite_retrieval
from embedding_index import prepare_document_embeddings
from embedding_adapter import build_embedding_model
from retrieval_results_io import save_beir_results
from retrieve_bm25 import build_bm25
from retrieve_bm25 import retrieve_bm25
from retrieve_core import retrieve
from retrieve_rrf import retrieve_rrf

def main(method, config_dir, data_dir, split, cache_dir, run_name, *, config_embedding_model="bge_small", rewrite_path=None):
    if not method in ("bm25", "dense", "rrf"): raise ValueError("Unknown method: " + method)

    result_dir = Path(__file__).resolve().parent / "results"  # 沿用项目原来的输出目录。
    prefixes = (run_name,) if rewrite_path is None else (f"{run_name}_original", f"{run_name}_rewritten")  # 根据模式确定一个或两个输出前缀。
    for prefix in prefixes:  # 检查本轮每一组输出。
        for suffix in ("results.jsonl", "run.json", "summary.json"):  # 每组都有这三份文件。
            output_path = result_dir / f"{prefix}_{suffix}"  # 拼出实际保存路径。
            if output_path.exists():  # 任意一份已存在，就在模型或索引构造前停止。
                raise FileExistsError(output_path)  # 明确指出发生冲突的文件。
        
    corpus_df, queries_df, qrels = load_beir_dataset(data_dir, split=split)
    
    if rewrite_path is not None:  # 只有提供了改写文件，才读取保存记录。
        rewrite_bytes = rewrite_path.read_bytes()  # 读取文件字节，后续计算SHA也使用这份内容。
        rewrite_records = [json.loads(line) for line in rewrite_bytes.decode("utf-8").splitlines() if line.strip()]  # 将JSONL解析为记录字典列表。
        

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
        config_path = config_dir / "embedding_profiles.json"
        
        evidence_path = data_dir / "corpus.jsonl"
        
        profiles = json.loads(config_path.read_text(encoding="utf-8"))
    
        if not config_embedding_model in profiles: raise ValueError("Unknown embedding model profile: " + config_embedding_model)
    
        embedding_profile = profiles[config_embedding_model]
                
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
    
    if rewrite_path is None:
        eval_df, run = evaluate_beir_retrieval(queries_df, qrels, retrieve_fn, ks=(10,100))
        summary = save_beir_results(
            eval_df,
            run,
            config=config,
            run_name=run_name,
            result_dir=Path(__file__).resolve().parent / "results"
        )
        return summary
    else:
        paired = evaluate_query_rewrite_retrieval(queries_df, qrels, retrieve_fn, rewrite_records=rewrite_records, ks=(10, 100))  # 由当前检索方法比较同一批原问题和保存表达。
        summaries = {}
        config["query_subset_ids"] = paired["query_inputs"]["id"].tolist()  # 将实际参评表的题号列转成列表。
        config["rewrite_source"] = {  # 组装本轮改写输入的来源信息。
            "path": str(rewrite_path.resolve()),  # 将改写文件绝对路径保存为字符串。
            "sha256": hashlib.sha256(rewrite_bytes).hexdigest(),  # 使用前面已经读入的字节计算指纹。
            "query_inputs": paired["query_inputs"].to_dict(orient="records"),  # 将输入表转换成每行一个字典的列表。
        }  # 结束来源信息字典。
        for key in ("original", "rewritten"):
            group = paired[key]
            group_config = {**config, "query_variant": key}
            summary = save_beir_results(
                group["eval_df"],
                group["run"],
                config=group_config,
                run_name=f"{run_name}_{key}",
                result_dir=Path(__file__).resolve().parent / "results"
            )
            summaries[key]=summary
        return summaries
        

if __name__ == "__main__":
    root = Path(__file__).resolve().parent

    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=["dense", "bm25", "rrf"], default="bm25") # 指定检索方法
    parser.add_argument("--cache", type=Path, default=root / "cache" / "embeddings") # 指定缓存文件路径
    parser.add_argument("--config", type=Path, default=root / "configs") # 指定配置文件路径
    parser.add_argument("--data-dir", type=Path, default=root / "data" / "external" / "nfcorpus" / "prepared" / "nfcorpus" ) # 指定数据文件路径
    parser.add_argument("--config-embedding-model", choices=["bge_small", "qwen3_8b"], default="bge_small")
    parser.add_argument("--split", choices=["dev", "train", "test"], default="dev") # 指定划分方式
    parser.add_argument("--rewrite-results", type=Path, default=None) # 改写结果路径
    parser.add_argument("--run-name") # 指定本次结果名称
    args = parser.parse_args()

    method = args.method
    cache_dir = args.cache
    config_dir = args.config
    config_embedding_model = args.config_embedding_model
    data_dir =  args.data_dir
    split = args.split
    rewrite_results_path = args.rewrite_results
    run_name = args.run_name if args.run_name else f"{data_dir.name}_{method}_{config_embedding_model}_{split}"

    summary = main(method, config_dir, data_dir, split, cache_dir, run_name, config_embedding_model=config_embedding_model, rewrite_path=rewrite_results_path)

    if rewrite_results_path is None:  # 原模式返回一个摘要。
        print(summary["metrics"])  # 沿用原来的指标输出。
    else:  # 改写模式返回两个组的摘要。
        print(json.dumps({variant: item["metrics"] for variant, item in summary.items()}, ensure_ascii=False, indent=2))  # 分别打印两组指标。

import os 
import json
import argparse
from urllib import parse


from langchain_deepseek import ChatDeepSeek
from pathlib import Path

from dotenv import load_dotenv
from benchmark_data import load_beir_dataset
from query_rewrite import rewrite_queries
from query_rewrite_io import save_rewrite_results

def main(config_dir, data_dir, *, profile_name, split, limit, run_name, result_dir):
    if not limit > 0: raise ValueError(f"Expected limit > 0 but got: {limit}")
    if any((result_dir / f"{run_name}_{suffix}").exists() for suffix in ("results.jsonl", "summary.json", "run.json")):
        raise ValueError("results files have been existed")
    
    corpus_df, queries_df, qrels = load_beir_dataset(data_dir, split=split)
    
    queries = queries_df.head(limit)
    if queries.empty: raise ValueError("Queries is empty")

    profile_path = config_dir / "llm_profiles.json"
    full_profile = json.loads(profile_path.read_text(encoding="utf-8"))
    rerank_profile = full_profile[profile_name]
    
    root = Path(__file__).resolve().parent

    load_dotenv(root / ".env", override=False)
    
    llm = ChatDeepSeek(**rerank_profile)
    
    results = rewrite_queries(queries, llm=llm)
    
    config = {
        "dataset_name": data_dir.resolve().name,
        "data_dir": str(data_dir.resolve()),
        "split": split,
        "limit": limit,
        "query_count": len(queries),
        "query_ids": queries['id'].to_list(),
        "profile_name": profile_name,
        "llm_profile": rerank_profile
    }
    
    summary = save_rewrite_results(records=results, config=config, run_name=run_name, result_dir=result_dir)
    return summary

if __name__ == "__main__":
    root = Path(__file__).resolve().parent

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=root / "configs") # 指定配置文件路径
    parser.add_argument("--data-dir", type=Path, default=root / "data" / "external" / "nfcorpus" / "prepared" / "nfcorpus" ) # 指定数据文件路径
    parser.add_argument("--profile", default="deepseek_flash")
    parser.add_argument("--split", choices=["dev", "train", "test"], default="dev") # 指定划分方式
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--run-name") # 指定本次结果名称
    parser.add_argument("--result-dir", type=Path, default=root / "results")
    args = parser.parse_args()
    
    config_dir = args.config
    data_dir = args.data_dir
    profile_name = args.profile
    split = args.split
    limit = args.limit
    result_dir = args.result_dir
    run_name = args.run_name
    
    run_name = run_name if run_name else f"{data_dir.name}_query_rewrite_{profile_name}_{split}"
    
    summary = main(config_dir, data_dir, profile_name=profile_name, split=split, limit=limit, run_name=run_name, result_dir=result_dir)
    
    print(json.dumps(summary, ensure_ascii=False, indent=2))  # 输出完整的批量改写摘要。
    
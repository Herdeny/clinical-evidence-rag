import argparse
import json
from pathlib import Path
from urllib import parse
from frozen_candidates_io import load_frozen_candidates # 加载冻结候选
from reranker_adapter import build_reranker # 根据配置创建重排模型
from reranker_adapter import describe_reranker # 读取模型实际运行属性，返回字典
from benchmark_eval import evaluate_frozen_reranking
from retrieval_results_io import save_beir_results

# receipt_path: 固定候选描述文件
def main(config_dir, data_dir, receipt_path, profile_name, run_name, result_dir):
    reranker_profile_path = config_dir / "reranker_profiles.json"
    full_rerank_profile = json.loads(reranker_profile_path.read_text(encoding="utf-8"))
    current_rerank_profile = full_rerank_profile[profile_name]
    
    frozen = load_frozen_candidates(receipt_path, data_dir=data_dir)
    source_info = frozen.info # 具体内容？
    
    run_name = run_name if run_name else f"{source_info["dataset_name"]}_rerank_{profile_name}_{source_info["split"]}"
    
    reranker = build_reranker(current_rerank_profile)
    rerank_info = describe_reranker(reranker, profile_name=profile_name, profile=current_rerank_profile, config_path=reranker_profile_path) # 函数作用？
    
    eval_df, run = evaluate_frozen_reranking(frozen, reranker, ks=(10, 100), batch_size=current_rerank_profile['batch_size'])
    
    config = {
        "dataset_name": source_info["dataset_name"],
        "data_dir": source_info["data_dir"],
        "split": source_info["split"],
        "retrieval_method": "frozen_rerank",
        "ks": [10, 100],
        "candidate_source": source_info,
        "rerank": rerank_info
    }
    
    
    summary = save_beir_results(
        eval_df,
        run,
        config=config,
        run_name=run_name,
        result_dir=result_dir
    )
    
    return summary


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
        
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=root / "configs")  # 沿用既有入口的配置目录参数。
    parser.add_argument("--data-dir", type=Path, default=root / "data" / "external" / "nfcorpus" / "prepared" / "nfcorpus")
    parser.add_argument("--receipt",  type=Path, default=root / "results" / "nfcorpus_qwen3_8b_frozen_candidates.json")
    parser.add_argument("--profile", choices=["qwen3_4b", "qwen3_8b", "bge_v2_m3"], default="qwen3_4b")
    parser.add_argument("--run-name")
    parser.add_argument("--result-dir", type=Path, default=root / "results")
    args = parser.parse_args()
    
    config_dir = args.config  # 将统一的命令行属性传给既有函数参数。
    data_dir = args.data_dir
    receipt_path = args.receipt
    profile_name = args.profile
    run_name = args.run_name
    result_dir = args.result_dir
    
    summary = main(config_dir, data_dir, receipt_path, profile_name, run_name, result_dir)
    
    print(summary['metrics'])
    

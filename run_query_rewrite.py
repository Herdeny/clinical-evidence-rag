import argparse
import json
from pathlib import Path
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from query_rewrite import rewrite_query

def main(config_dir, *, profile_name, query):
    profile_path = config_dir / "llm_profiles.json"
    full_profile = json.loads(profile_path.read_text(encoding="utf-8"))
    rerank_profile = full_profile[profile_name]
    
    root = Path(__file__).resolve().parent
    load_dotenv(root / ".env", override=False)
    
    llm = ChatDeepSeek(**rerank_profile)
    
    results = rewrite_query(query, llm=llm)
    
    return results

if __name__ == "__main__":
    root = Path(__file__).resolve().parent
        
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=root / "configs")  # 沿用既有入口的配置目录参数。
    parser.add_argument("--profile", default="deepseek_flash")
    parser.add_argument("--query", required=True)
    args = parser.parse_args()
    
    config_dir = args.config
    profile_name = args.profile
    query = args.query
    
    results = main(config_dir, profile_name=profile_name, query=query)
    
    print(json.dumps(results, ensure_ascii=False, indent=2))  # 将返回字典格式化输出，保留中文。
    

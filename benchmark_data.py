import pandas as pd
from pathlib import Path
def load_beir_dataset(data_dir, *, split="dev"):    
    data_dir_path = Path(data_dir).resolve()
    qrels_dir_path = data_dir_path / "qrels" / f"{split}.tsv"
    corpus_path = data_dir_path / "corpus.jsonl"
    queries_path = data_dir_path / "queries.jsonl"
    
    if split not in ("train", "test", "dev"):
        raise ValueError(f"split must be train/test/dev, but got {split}")
    if not qrels_dir_path.is_file():
        raise FileNotFoundError(f"{qrels_dir_path} is not exists")
    if not corpus_path.is_file():
        raise FileNotFoundError(f"{corpus_path} is not exists")
    if not queries_path.is_file():
        raise FileNotFoundError(f"{queries_path} is not exists")
    
    corpus_df = pd.read_json(corpus_path, lines=True, dtype=False) # dtype 的作用？ # dtype表示 df 是否会自动识别数据类型，比如 “001” 会被自动转换为 1
    corpus_df.rename(columns={"_id": "id", "text": "body"}, inplace=True) # inplace 属性表示是否修改原 DataFrame
    
    if corpus_df["id"].duplicated().any():
        raise ValueError("document_id cuplicated in corpus")
    
    corpus_df["text"] = (
        corpus_df["title"].fillna("") # 用空字符串填补空缺值
        + " " + 
        corpus_df["body"].fillna("")
        ).str.strip() # .str 表示对一列中的字符串逐个操作，.strip() 用于去除首尾空白，包括空格、\n、\t 等
    
    if any(corpus_df["body"].isna() | corpus_df["body"].str.strip().eq("")):
        raise ValueError(f"body is empty in corpus")
    
    corpus_df["source_id"] = corpus_df["id"]
    corpus_df["locator"] = [
        {
        "dataset": data_dir_path.name,
        "document_id": id 
    }
        for id in corpus_df["id"]
        ]
    
    
    qrels_df = pd.read_csv(
        qrels_dir_path,
        sep='\t',
        dtype={
            "query-id": str,
            "corpus-id": str,
            "score": int
        })
    if qrels_df.empty:
        raise ValueError("qrels is empty")
    
    if qrels_df.duplicated(subset=["query-id", "corpus-id"]).any():
        raise ValueError("query-corpus pair duplicated in qrels")
    
    qrels = dict()
        
    for _, qrel in qrels_df.iterrows():
        query_id = qrel["query-id"]
        document_id = qrel["corpus-id"]
        score = qrel["score"]
        if qrel["query-id"] in qrels:
            qrels[query_id][document_id] = score
        else:
            qrels[query_id] = {document_id: score}
    
    queries_df = pd.read_json(queries_path, lines=True, dtype=False).rename(columns={"_id": "id", "text": "query"})
    
    if queries_df["id"].duplicated().any():
        raise ValueError("queries id duplicated")
    
    if (set(qrels) - set(queries_df["id"])):
        raise ValueError("qrels id not fount in queries")
    
    if (set(qrels_df["corpus-id"]) - set(corpus_df["id"])):
        raise ValueError("missing document incitement")
    
    queries_df = queries_df[queries_df["id"].isin(qrels)]
    
    return corpus_df, queries_df, qrels
    
def apply_query_rewrites(queries_df, rewrite_records):
    if queries_df["id"].duplicated().any(): raise ValueError("Duplicated id in queries_df")
    
    record_map = dict()
    
    for record in rewrite_records:
        query_id = record["query_id"]
        if query_id in record_map:
            raise ValueError(f"{query_id} duplicated in record_map")
        record_map[query_id] = record
    
    unknown_ids = set(record_map) - set(queries_df["id"])
    if unknown_ids: raise ValueError(f"Unknown ids in queries_df: {unknown_ids}")
    
    mask = queries_df["id"].isin(record_map)
    result_df = queries_df[mask].copy()
    
    result_df["original_query"] = result_df["query"]
    result_df["query_source"] = ""
    result_df["rewrite_status"] = ""
    
    for index, row in result_df.iterrows():
        record = record_map[row["id"]]
        if not record["original_query"] == row["original_query"]: raise ValueError("Inconsistent between record and result")
        if record["status"] == "ok": 
            query = record["retrieval_query"].strip()
            if not query: raise ValueError("Query is blank")
            query_source = "llm_rewrite_query"
            rewrite_status = "ok"
        elif record["status"] == "error":
            query = record["original_query"]
            if not query: raise ValueError("Query is blank")
            query_source = "original_fallback"
            rewrite_status = "error"
        else:
            raise ValueError(f"Incorrect status: {record["status"]}")
        
        result_df.at[index, "query"] = query
        result_df.at[index, "query_source"] = query_source
        result_df.at[index, "rewrite_status"] = rewrite_status
    
    return result_df
        
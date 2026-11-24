from typing import Set
import pytrec_eval
import pandas as pd 
from tqdm import tqdm
from time import perf_counter
from math import isfinite
from rerank_core import rerank

import retrieval_results_io

def evaluate_beir_retrieval(queries_df, qrels, retrieve_fn, ks=(10, 100), pass_query_id=False):
    if not ks or any(type(k) is not int or k <= 0 for k in ks) or len(ks) != len(set(ks)):
        raise ValueError(f"ks should be positive int, not NaN and different, but got {ks}")
    if queries_df.empty:
        raise ValueError(f"queries is empty")
    if queries_df['id'].duplicated().any():
        raise ValueError("queries_df")
    if not (set(qrels) == set(queries_df["id"])):
        raise ValueError("missing qrels id")
    
    run = dict()
    eval_rows = list()
    
    for _, query in tqdm(queries_df.iterrows(), total=len(queries_df)):
        query_text = query["query"]
        query_id = query["id"]
        run[query_id] = {}
        try:
            if pass_query_id:
                time_1 = perf_counter()
                retrieved_results = retrieve_fn(query_text, max(ks), query_id=query_id)
                time_2 = perf_counter()
            else:
                time_1 = perf_counter()
                retrieved_results = retrieve_fn(query_text, max(ks))
                time_2 = perf_counter()
            if len(retrieved_results) > max(ks):
                raise ValueError("retrieved results exceed the max ks")
            duration_ms = (time_2 - time_1) * 1000
            retrieved_ids = list()
            scores = list()
            for retrieved_result in retrieved_results:
                document_id = retrieved_result["id"]
                score = float(retrieved_result["score"])
                
                if document_id in run[query_id]:
                    raise ValueError("duplicated document_id")
                
                if not isfinite(score):
                    raise ValueError("score is infinite")
                    
                retrieved_ids.append(document_id)
                scores.append(score)
                
                run[query_id].setdefault(retrieved_result["id"], float(retrieved_result["score"]))
        except Exception as exc:
            raise RuntimeError(f"query_id={query_id}: {exc}") from exc # RuntimeError是什么 Error？ from exc 是什么意思？
            # from exc 表示提出的异常是由 exc 直接引起的，如果没有 from，就会有 exc 和 RuntimeError 两个异常。RuntimeError：运行时出错
            
        eval_row = {
                    "query_id": query_id,
                    "query": query_text,
                    "latency_ms": duration_ms,
                    "retrieved_ids": retrieved_ids,
                    "scores": scores
                    }
        eval_rows.append(eval_row)
    
    # 使用标注等级，计算两个截断位置的 nDCG 和 Recall。
    # 请求用 ndcg_cut.10，取结果用 ndcg_cut_10，保存到表中用 ndcg_at_10
    ndcg_cut_text = "ndcg_cut." + ",".join(map(str, ks)) # map 函数：对 ks 中的每个元素执行 str 函数
    recall_text = "recall." + ",".join(map(str, ks)) # join 函数：将字符串列表拼接为一个字符串
    evaluator = pytrec_eval.RelevanceEvaluator(qrels, {ndcg_cut_text, recall_text})
    # 返回按查询 ID 组织的逐题指标。
    per_query = evaluator.evaluate(run)
    
    for index, eval_row in enumerate(eval_rows):
        query_id = eval_row['query_id']
    
        for k in ks:
            eval_rows[index][f"ndcg_at_{k}"] = per_query[query_id][f"ndcg_cut_{k}"]
            eval_rows[index][f"recall_at_{k}"] = per_query[query_id][f"recall_{k}"]
            
    eval_df = pd.DataFrame(eval_rows)
    return eval_df, run
        
def evaluate_frozen_reranking(frozen, reranker, ks=(10, 100), *, batch_size=16):    
    def retrieve_fn(query, k, *, query_id):
        query_hits = frozen.get_hits(query_id) # 取回已经检索过的结果
        results = rerank(query, query_hits, k, reranker=reranker, batch_size=batch_size)
        return results
    
    eval_df, run = evaluate_beir_retrieval(frozen.queries_df, frozen.qrels, retrieve_fn=retrieve_fn, ks=ks, pass_query_id=True)
    return eval_df, run
    
    
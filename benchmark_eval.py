from typing import Set
import pytrec_eval
import pandas as pd 
from tqdm import tqdm
from time import perf_counter
from math import isfinite
from rerank_core import rerank
from benchmark_data import apply_query_rewrites
from sklearn.metrics import f1_score

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

def evaluate_query_rewrite_retrieval(queries_df, qrels, retrieve_fn, *, rewrite_records, ks=(10, 100)):
    rewritten_queries_df = apply_query_rewrites(queries_df, rewrite_records) # 改写问题 DataFrame
    ids = rewritten_queries_df["id"]
    mask = queries_df["id"].isin(ids)
    original_queries_df = queries_df[mask].copy() # 原始问题 DataFrame
    seleted_qrels = {query_id: qrels[query_id] for query_id in ids}
    original_eval_df, original_run = evaluate_beir_retrieval(original_queries_df, seleted_qrels, retrieve_fn, ks=ks)
    rewritten_eval_df, rewritten_run = evaluate_beir_retrieval(rewritten_queries_df, seleted_qrels, retrieve_fn, ks=ks)
    
    return {  # 将两组评价结果交给后续运行入口。
    "original": {"eval_df": original_eval_df, "run": original_run},  # 原问题组的指标表和排名。
    "rewritten": {"eval_df": rewritten_eval_df, "run": rewritten_run},  # 新表达组的指标表和排名。
    "query_inputs": rewritten_queries_df,  # 保留原问题、检索表达、来源与状态。
}  # 其中包含DataFrame，后续由保存辅助分别落盘。

def evaluate_multiple_choice(questions_df, gold_answers, answer_records):
    if questions_df.empty: raise ValueError("Questions_df is blank")
    if questions_df['id'].duplicated().any(): raise ValueError("Questions duplicated in questions_df")
    if not set(questions_df['id']) == set(gold_answers): raise ValueError("Inconsistent between questions and answers")
    
    record_map = {}
    for record in answer_records:
        query_id = record['query_id']
        if query_id in record_map: raise ValueError("Duplicated query id in records")
        record_map[query_id] = record
    
    if not set(record_map) == set(gold_answers): raise ValueError("Inconsistent between answers and records")
    eval_rows = list()
    
    for _, question in questions_df.iterrows():
        question_id = question["id"]
        answer = gold_answers[question_id]
        record = record_map[question_id]["result"]
        if not record["original_query"] == question["query"]: raise ValueError("Query is inconsitent with original")
        if record["status"] == "error":
            predited_answer = None
            correct = 0
        elif record["status"] == "ok":
            predited_answer = record["answer"]["answer_choice"]
            if predited_answer in question["options"]:
                correct = int(predited_answer == answer)
            else: raise ValueError(f"Predicted answer {predited_answer} doesn't belong to the question {question_id}")
        else: raise ValueError(f"Unpredicted status in question {question_id}")
        eval_row = {
            "query_id": question_id,
            "task": question["task"],
            "gold_answer": answer,
            "predicted_answer": predited_answer,
            "status": record["status"],
            "correct": correct
        }
        eval_rows.append(eval_row)        

    eval_df = pd.DataFrame(eval_rows)
    
    global_accurancy = eval_df["correct"].mean()
    per_task = {}
    groups = eval_df.groupby("task", sort=False)
    tasks_num = len(groups)
    
    total_accuracy = 0
    total_query_count = 0
    summary = {}
    
    for task, group in groups:
        query_count = len(group)
        total_query_count += query_count
        accuracy = group["correct"].mean()
        total_accuracy += accuracy
        per_task[task] = {
            "query_count": query_count,
            "accuracy": accuracy
        }
        if task == "pubmedqa":
            task_questions = questions_df[questions_df["task"] == task]  # 找到当前任务的原始题目表。
            label_keys = sorted({key for opts in task_questions["options"] for key in opts})  # 汇总所有合法选项键并排序。
            label_to_index = {key: index for index, key in enumerate(label_keys)}  # 将答案键映射为0、1、2等整数。
            truth = [label_to_index[key] for key in group["gold_answer"]]  # 转换标准答案。
            pred = [label_to_index.get(key, -1) for key in group["predicted_answer"]]  # 无有效答案时使用-1。
            macro_f1 = f1_score(truth, pred, labels=list(label_to_index.values()), average="macro", zero_division=0)
            per_task[task]["macro_f1"] = macro_f1
            
    macro_accuracy = total_accuracy / tasks_num  
    summary = {
        "query_count": total_query_count,
        "ok_count": int((eval_df["status"] == "ok").sum()),  # 统计状态为ok的行，转成普通整数便于保存。
        "error_count": int((eval_df["status"] == "error").sum()),  # 统计失败行，失败题仍然留在评分表中。
        "accuracy": global_accurancy,
        "macro_accuracy": macro_accuracy,
        "per_task": per_task
    }
    
    return eval_df, summary
    
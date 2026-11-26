import retrieve_core


def recall_at_k(retrieved_ids, gold_ids, k):
    if not gold_ids: raise ValueError("gold_ids 不能为空")
    if k == 0: raise ValueError("k 必须为正整数")
    total = len(set(gold_ids)) # 标注卡总数(标注卡是题目中给出的应检索到的证据卡的序号列表)
    goat = len(set(gold_ids).intersection(retrieved_ids[:k])) # 取交集
    return goat / total


def group_recall_at_k(retrieved_ids, gold_groups, k):
    if not gold_groups: raise ValueError("gold_groups 不能为空")
    if k == 0: raise ValueError("k 必须为正整数")
    count = 0
    total = len(gold_groups)
    for gold_ids in gold_groups:
        if recall_at_k(retrieved_ids, gold_ids, k) > 0:
            count += 1
    return count / total


def evaluate_retrieval(cases, retrieve_fn, ks=(1, 3, 5), *, review_fn=None):
    
    if not ks or any(type(k) is not int or k <= 0 for k in ks):
        raise ValueError("ks 必须为非空的正整数序列")
    
    import time
    import pandas as pd
    eval_rows = []
    for _, case in cases.iterrows():
        eval_case = {
            "case_id": case['id'],
            "split": case['split'],
            "group": case['group'],
            "report": case['report'],
            "question": case['question'],
            "gold_evidence_ids": case['gold_evidence_ids'],
            "gold_evidence_groups": case['gold_evidence_groups']
        }
        query = f"Report: {case['report']}\nQuestion: {case['question']}"
        time_1 = time.perf_counter()
        retrieved_results = retrieve_fn(query, max(ks))
        time_2 = time.perf_counter()
        duration = (time_2 - time_1) * 1000
        eval_case['retrieve_latency_ms'] = duration
        
        retrieved_ids = [x['id'] for x in retrieved_results]
        eval_case['retrieved_ids'] = retrieved_ids
        eval_case['scores'] = [x['score'] for x in retrieved_results]
                
        for k in ks:
            eval_case[f"canonical_recall_at_{k}"] = recall_at_k(retrieved_ids, case['gold_evidence_ids'], k)
            eval_case[f"group_recall_at_{k}"] = group_recall_at_k(retrieved_ids, case['gold_evidence_groups'], k)

        if review_fn:
            time_3 = time.perf_counter()
            review_result = review_fn(query, retrieved_results)
            time_4 = time.perf_counter()
            eval_case["review_latency_ms"] = (time_4 - time_3) * 1000
            eval_case["evidence_review"] = review_result
        eval_rows.append(eval_case)

    eval_df = pd.DataFrame(eval_rows)
    return eval_df
        
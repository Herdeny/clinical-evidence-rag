import numpy as np

from math import isfinite
from math import isnan

def rerank(query, hits, k, *, reranker, batch_size=16):
    if not type(query) == str or not query.strip(): raise ValueError(f"Invalid query: {(query, type(query))}")
    if not type(hits) == list: raise ValueError(f"Incorrect hits type: {type(hits)}")
    if not type(k) == int or k <= 0: raise ValueError(f"Expected k positive int, but got {k}")
    if not type(batch_size) == int or batch_size <= 0: raise ValueError(f"Expected batch_size positive int, but got {batch_size}")

    seen = set()
    for hit in hits:
        if not type(hit) == dict: raise ValueError("Incorrect hit type")
        if not ("id" in hit and "text" in hit and "score" in hit): raise ValueError("Missing attr for hit")
        if not (type(hit['id']) == str and type(hit['text']) == str and hit['id'].strip() and hit['text'].strip()): raise ValueError("Incorrect type or empty id/text for hit")
        if hit['id'] in set(seen): raise ValueError("Duplicated id in hits")
        seen.add(hit['id'])
        retrieval_score = float(hit['score'])
        if isnan(retrieval_score) or not isfinite(retrieval_score): raise ValueError("Retrieval_score is NaN/inf")

    if not hits: return []

    pairs = [(query, hit['text']) for hit in hits]
    scores = reranker.predict(pairs, batch_size=batch_size, show_progress_bar=False, convert_to_numpy=True)

    scores = np.asarray(scores)
    # 维度错误时安全显示整数，避免错误提示本身触发TypeError。
    if not scores.ndim == 1: raise ValueError(f"Dimension expected 1, but got {scores.ndim}")
    # 数量错误时显示整个分数数组长度，空数组也能正常报告。
    if not len(scores) == len(hits): raise ValueError(f"Inconsistent between hits and scores, which presents as ({len(hits)}, {len(scores)})")
    if not np.isfinite(scores).all(): raise ValueError("Infinite num in scores")


    new_hits = list()


    for index, hit in enumerate(hits):
        temp = hit.copy()
        retrieval_score = float(hit['score'])
        score = float(scores[index])

        if isnan(score) or not isfinite(score): raise ValueError("Score is NaN/inf")

        temp['retrieval_score'] = retrieval_score
        temp['score'] = score
        new_hits.append(temp)

    results = sorted(new_hits, key=lambda x: (-x['score'], x['id']))[:k]
    return results

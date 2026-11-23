def fuse_rankings(rankings, k, *, rrf_constant=60):
    if not type(k) is int or k <= 0: raise ValueError("k 必须为正整数")
    if not type(rrf_constant) is int or rrf_constant <= 0: raise ValueError("rrf 参数必须为正整数")
    new_hits = dict()
    for hits in rankings:
        seen = set() # 检查 hits 内部是否有重复 ID
        for index, hit in enumerate(hits, start=1):
            if hit['id'] in seen: raise ValueError("hits 存在重复 ID")
            seen.add(hit['id'])
            contribute = 1 / (rrf_constant + index)
            evidence_id = hit['id']
            if evidence_id not in new_hits:
                temp_hit = hit.copy()
                temp_hit['score'] = contribute
                new_hits[evidence_id] = temp_hit
            else:
                new_hits[evidence_id]['score'] += contribute
    new_hits = sorted(new_hits.items(), key=lambda x:(-x[1]['score'], x[1]['id']))[:k]
    return [x[1] for x in new_hits]

def retrieve_rrf(query, k, *, dense_retrieve_fn, bm25_retrieve_fn, candidate_k=20, rrf_constant=60):
    if not (all(type(x) is int for x in (k, rrf_constant, candidate_k))  and 0 < k <= candidate_k and rrf_constant > 0):
        raise ValueError(f"k, rrf_constant, candidate_k should be positive int and k <= candidate_k, but got {k}, {rrf_constant}, {candidate_k}")
    rank_1 = dense_retrieve_fn(query, candidate_k)
    rank_2 = bm25_retrieve_fn(query, candidate_k)
    fuse_result = fuse_rankings([rank_1, rank_2], k, rrf_constant=rrf_constant)
    return fuse_result
        
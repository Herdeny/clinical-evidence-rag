import re
import numpy as np
from rank_bm25 import BM25Okapi

def tokenize(text):
    pattern = r"[a-z]+|\d+(?:\.\d+)?"
    return re.findall(pattern, text.lower())

def build_bm25(evidences, *, k1=1.5, b=0.75, epsilon=0.25):
    texts = evidences['text'].to_list()
    corpus = list()
    for text in texts:
        if text == None: raise ValueError("证据正文为空")
        tokenize_text = tokenize(text)
        corpus.append(tokenize_text)
    if not corpus:
        raise ValueError("空语料")
    if not any(corpus):
        raise ValueError("所有正文都没有词项")
    results = BM25Okapi(corpus, k1=k1, b=b, epsilon=epsilon)
    if results.corpus_size != len(corpus): raise ValueError
    return results

def retrieve_bm25(query, k, *, bm25_index, evidences):
    if type(k) is not int or k <= 0: raise ValueError("k 必须为正整数")
    query_tokens = tokenize(query)
    scores = bm25_index.get_scores(query_tokens)
    order = np.argsort(-scores, kind="stable") # 稳定排序，对负分数排序相当于原分数降序
    results = list()
    for index in order[:k]:
        evidence = evidences.iloc[index]
        result = {
            "id": evidence['id'],
            "score": scores[index],
            "source_id": evidence['source_id'],
            "locator": evidence['locator'],
            "text": evidence['text']
        }
        results.append(result)
    return results
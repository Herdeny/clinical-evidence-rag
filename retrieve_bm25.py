import re
import json
import numpy as np
from pathlib import Path
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

def load_lucene_bm25(index_path, *, k1=0.9, b=0.4):
    index_dir = Path(index_path)
    if not index_dir.exists(): raise FileNotFoundError("Index-dir not found.")
    if not index_dir.is_dir(): raise NotADirectoryError("Index-dir is not a directory.")
    
    from pyserini.search.lucene import LuceneSearcher
    searcher = LuceneSearcher(str(index_dir))
    searcher.set_bm25(k1, b)
    return searcher

def retrieve_lucene_bm25(query, k, *, searcher):
    if not type(query) == str: raise TypeError("Query is not str.")
    if not query.strip(): raise ValueError("Query is empty.")  # 拒绝空字符串以及只有空格、换行的问题。
    if not type(k) == int: raise TypeError("K is not int.")
    if k <= 0: raise ValueError(f"Expected k positive int, but got {k}")

    hits = searcher.search(query, k=k)
    records = list()
    for hit in hits:
        document = json.loads(searcher.doc(hit.docid).raw())
        record = {
            "id": hit.docid,
            "score": float(hit.score),
            "text": document["contents"],
            "source_id": f"pubmed:{document["PMID"]}",
            "locator": f"MedRAG/pubmed | {document['id']} | contents"
        }
        records.append(record)
    return records
        
    
    
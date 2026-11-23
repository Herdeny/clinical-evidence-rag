import numpy as np

def retrieve(query, k, *, embedding_model, evidences, embeddings):
    if type(k) is not int or k <= 0: raise ValueError("k 必须为正整数")
    query_embedding = embedding_model.embed_query(query)
    scores = np.matmul(embeddings, query_embedding)
    rank = np.argsort(scores)
    top_indices = rank[-k::][::-1]
    
    hits = list()
    for rank, index in enumerate(top_indices):
        card = evidences.iloc[index]
        hits.append({
            'id': card['id'],
            'score': scores[index],
            'source_id': card['source_id'],
            'locator': card['locator'],
            'text': card['text']
        })
    return hits
    
    
    
    
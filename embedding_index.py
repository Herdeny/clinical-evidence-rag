from tqdm import tqdm
from embedding_cache_io import DocumentEmbeddingCache

def prepare_document_embeddings(
    evidences, embedding_model, *, evidence_path, cache_dir, chunk_size=512, # 512 是一次保存进度的证据条数，模型的 batch_size是 GPU 每次前向处理的条数，即使一次提交 512 条，GPU 每次仍只处理 batch_size 条
    dimension=384
):
    if not type(chunk_size) is int or chunk_size <= 0: raise ValueError("chunk_size should be positive int")
    with DocumentEmbeddingCache(
        evidences, embedding_model,
        evidence_path=evidence_path,
        cache_dir=cache_dir,
        dimension=dimension
    ) as cache:
        if cache.is_complete:
            embeddings = cache.load()
        else:
            start = cache.completed_rows
            total = cache.total_rows
            for index in tqdm(range(start, total, chunk_size)):
                end = min(chunk_size + index, total)
                texts = evidences.iloc[index:end]["text"].to_list()
                vectors = embedding_model.embed_documents(texts) # embed_documents 与其他的 embed_query 等有何不同？ # docunments 是多条正文组成的列表，输出多个向量组成的列表，而 query 是一条查询字符串输出一个向量
                cache.write_batch(index, vectors) # cache 既然是原文文本块，为什么要写回去？ write_batch是什么函数？ # write_batch 是自定义函数，负责检查向量形状、数值、归一化情况，写入磁盘上的向量矩阵后，更新成功保存的行数
                print(f"已缓存 {cache.completed_rows}/{cache.total_rows} 条 ({round((cache.completed_rows/cache.total_rows) * 100)}%)")
            embeddings = cache.finish() # 返回值是什么？ # 返回值是全部证据的完整向量矩阵，类型为只读的np.memamp，数值类型为 float32
        cache_info = cache.info
        return embeddings, cache_info

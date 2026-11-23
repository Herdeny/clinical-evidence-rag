# 当前工作单元：Dense 分批编码与可复用缓存

日期：2026-11-19。医学 v3 的 BM25 全库基线已完成，不重跑。现在为同一语料建立 Dense 基线，保持 LangChain HuggingFaceEmbeddings / BGE-small-en-v1.5 / CUDA，先接缓存再编码全库。

## 最新验收与当前任务

**2026-11-20完成：用户续跑成功，全库Dense及原32题已独立核验通过。** Canonical／Group Recall@1／3／5均为0.1875／0.359375／0.421875，查询均值330.062ms；矩阵(783847,384)、float32只读、所有行有限且归一化，原始行序和文件指纹核对一致。审计状态complete_integrity_validated，详见[完整归档](medical_v3_dense_baseline.md)。两段8:43.33与3:52.87分开记录，不叫单次冷启动时间。用户新增tqdm只影响进度显示，运行后版本单独归档。当前转入[用户实现RRF](rrf_task.md)，不再编码。以下11月19日设计／等待／运行状态均为历史记录。

**最新移交：用户要求自己在可见终端运行。** 助手已用中断停止后台会话4565，退出130，最后成功断点529,408／783,847行，缓存锁已验证释放。第一段日志／资源保存为results/medical_v3_dense_ct_dev_encoding_part1.log及_encoding_part1_resources.txt。用户接着运行原CLI并用tee保存_encoding_part2.log、GNU time保存_encoding_part2_resources.txt。审计状态interrupted_for_user_terminal_resume；助手不再自行启动。下一次先检查用户续跑与最终产物，不重复编码；分段耗时分别报告，不能将第二段称作完整冷启动编码耗时。下面“正在后台运行”为历史状态。

2026-11-19最新状态：用户已接通run_retrieval_eval.py，main(cases_path,evidence_path,cache_dir,method)。12项合成入口检查通过，实际缓存元数据键为embeddings_cache，保存与复用均正常，后续按此实际字段读取；记录results/embedding_entry_validation.json。RTX 4090真实8条小批也通过，输出(8,384)、float32、归一化、只读矩阵和复用零正文编码调用，记录results/dense_cuda_preflight.json。下文“入口尚未接入”为此前教学记录，以本段为准。

全库Dense已启动，exec session4565，审计results/medical_v3_dense_ct_dev_run_audit.json状态running；日志results/medical_v3_dense_ct_dev_run.log，资源_resources.txt，源码_code_snapshot。缓存为cache/embeddings/03f83f8aee178e40b006d7b80f395c7f50cdbc6ef292ee190e00b8a423c60b34。默认工具环境没有/dev/nvidia0，获准的GPU执行环境实测正常，不要误判服务器驱动故障或切换CPU。正式进程启动前设置HF_HUB_OFFLINE=1、TRANSFORMERS_OFFLINE=1：本机加载链在local_files_only=True时仍曾探测processor_config.json远端HEAD，首次结果另存dense_cuda_preflight_initial.json，离线复核成功。完成并独立核验前没有全库Dense成绩，不重复启动编码。

2026-11-19：用户已实现 embedding_index.py 中的 prepare_document_embeddings，并修正循环内初始断点 start 与当前批次 index 的混用。6 项合成集成检查全部通过：首次分批／尾批／位置映射、完整缓存零编码调用、中途模型失败后恢复、全部行已提交但尚未发布的恢复、查询前缀变化复用、非法 chunk_size 拒绝。测试为 tests/test_embedding_index.py，指纹与结果为 results/embedding_index_validation.json。没有改写用户函数，也没有调用真实模型、GPU 或进行全库编码。

**当前由用户修改 run_retrieval_eval.py 的 dense 分支：** 导入 prepare_document_embeddings；model_kwargs 保留 cuda 并指定下文的 revision 和 local_files_only；用该函数替代原来的整库正文列表与 embed_documents／np.float32 转换，接收 embeddings 和 cache_info；config 增加 embedding_cache=cache_info。缓存目录必须从脚本位置确定为项目根目录下 cache/embeddings。入口当前尚未接入，不把模块合成验收当作 Dense 全库完成。用户保存后先验收入口，再检查 CUDA 和真实模型小批，最后建立全库基线。

## 助手已完成的辅助部分

embedding_cache_io.py 提供 DocumentEmbeddingCache，只做文件读写、指纹、数组检查及恢复，不调用模型。8 项合成测试通过，记录见 results/embedding_cache_preparation_validation.json。没有下载／加载真实模型、运行 GPU 或全库编码，不把 I/O 测试当成 Dense 检索成绩。

向量用 NumPy 的 .npy 内存映射保存；不需要先收集几十万条 Python 向量列表再整体转换。矩阵为 float32、形状 (783847, 384)，数据本体约 1.121 GiB；该数字不是整个编码进程的峰值内存。

缓存身份包含原始证据文件 SHA-256、实际 id/text 的内容与行序、模型名与固定 revision、模型参数、文档 encode_kwargs、维度、dtype 和相关依赖版本。查询前缀不影响已有文档向量，单独调整 query_encode_kwargs 不让文档缓存失效。数据／行序／文档编码配置变化产生不同缓存目录。

这是固定语料快照的复用和断点恢复，不是逐文档增量索引；不声称扩库后能自动只编码新增行。现有主库冻结，随后方法对照复用同一缓存。

## 用户新增 embedding_index.py

实现一个函数，模块导入时不读文件、不创建模型：

```python
def prepare_document_embeddings(
    evidences, embedding_model, *, evidence_path, cache_dir, chunk_size=512
):
    ...
```

返回 `(embeddings, cache_info)`：

- embeddings：完整矩阵，直接返回缓存的只读 np.memmap，兼容现有 retrieve 中的 np.matmul，不额外复制整个矩阵。
- cache_info：缓存对象的 info 字典，用于写入运行摘要；其中 cache_hit 表示进入时是否已有完整缓存，不会把刚编码完成误写为命中缓存。
- evidences：当前证据 DataFrame，按原行顺序编码。
- embedding_model：运行入口创建的现有 HuggingFaceEmbeddings 实例。
- evidence_path：这批证据原始 JSONL 的路径，辅助模块计算输入指纹。
- cache_dir：缓存根目录，正式运行使用项目根目录下 cache/embeddings。辅助模块自动再按 fingerprint 分目录。
- chunk_size：每次交给 embed_documents 并保存的证据条数，固定先用 512。必须是正整数。

### 需要导入的辅助类

```python
from embedding_cache_io import DocumentEmbeddingCache
```

通过下面的接口打开一次缓存：

```python
with DocumentEmbeddingCache(
    evidences,
    embedding_model,
    evidence_path=evidence_path,
    cache_dir=cache_dir,
) as cache:
    ...
```

with 在函数正常返回或异常退出时都会释放文件资源，已经提交的批次会保留。不要把打开缓存放进每个批次的循环里。

| 接口 | 用途 |
| --- | --- |
| cache.is_complete | 是否已有完整缓存 |
| cache.completed_rows | 已保存的连续行数，也是下一批起始位置 |
| cache.total_rows | 总行数 |
| cache.load() | 读取完整缓存，返回只读内存映射；不允许将半成品当完整矩阵 |
| cache.write_batch(start, vectors) | 写入从 start 开始的连续模型输出并记录进度；内部转 float32、校验维度和归一化 |
| cache.finish() | 所有行完成后校验并发布完整文件，返回只读内存映射 |
| cache.info | 可直接存入 config 的 JSON 字典，包含指纹、文件位置、是否命中以及最初已完成行数 |

### 你负责组合的逻辑

1. 检查 chunk_size 是正整数，打开一次缓存。
2. 完整缓存直接读取，模型文档编码调用数应为零。
3. 未完成时，从 cache.completed_rows 开始分块，每块最多 chunk_size 行。若把初始断点记为 start、循环变量记为 index，则 start 不会随循环更新，index 才是当前批次起点。
4. 通过 `evidences.iloc[index:end]["text"].tolist()` 取得本块正文，保持原始位置；end 不超过总行数。
5. 调用已有 `embedding_model.embed_documents(texts)`，再将这批输出交给 cache.write_batch(index, vectors)。取正文与保存必须使用同一个当前批次起点。使用助手提供的输出语句打印进度。
6. 全部写完后调用 cache.finish()，返回矩阵和 cache.info。模型出错时让异常正常向外传递，缓存保留最后一次成功提交的位置。

可用 `range(start, stop, step)` 遍历分块起点：stop 为总行数，step 为 chunk_size。核心分块循环和模型调用由用户自己写；这里不提供完整函数实现。

进度语句可直接使用：

```python
print(f"已缓存 {cache.completed_rows}/{cache.total_rows} 条")
```

外层 chunk_size=512 是保存检查点的粒度；模型内部 encode_kwargs.batch_size=8 是 GPU 每次前向处理的条数。二者不同，当前不改既定的 GPU batch_size。

## 接入现有 run_retrieval_eval.py

只修改 dense 分支。沿用现有 embedding_model 初始化，并在 model_kwargs 中保留 device=cuda，同时补充：

```python
"revision": "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a",
"local_files_only": True,
```

该提交的 config／tokenizer／model.safetensors 已在当前机器缓存中核实。固定 revision 是为了让向量缓存绑定确定的模型版本；local_files_only 让本轮使用现有快照。库版本已确认支持这两个参数，不改变模型、权重或向量维度。

文档仍 normalize_embeddings=True、prompt=""、batch_size=8；查询仍 normalize_embeddings=True、batch_size=1、prompt 为既有 BGE 前缀。不要把查询前缀拼到文档正文。

用 prepare_document_embeddings 替换原先整库 embed_documents / np.float32 的两行；传入当前 evidence_df、embedding_model、evidence_path 和基于脚本根目录的 cache/embeddings。解包 embeddings、cache_info，继续交给原 retrieve_fn。config 增加 embedding_cache=cache_info；现有模型配置和结果名 medical_v3_dense_ct_dev 保留。

BM25 分支及已有结果保持原样。辅助缓存不替用户创建模型、选择文本或计算相似度，后续 Qdrant 接入也可以读取这份已绑定行序的矩阵。

## 一次验收

用户保存模块和入口后，助手先用临时小样本和可计数的合成编码器检查以下行为，不直接启动 783,847 条编码：

- 首次分块编码，所有行恰好一次，尾块不漏，返回 float32 矩阵且位置正确。
- 再次调用同一输入，文档编码调用数为 0，cache_info.cache_hit=True，矩阵一致。
- 中途失败后重试，从最后成功提交的位置继续；已保存行不重复编码。
- 证据顺序、正文、模型版本或文档编码参数变化时不误用旧缓存；查询前缀单独变化可复用文档向量。
- 接入入口、缓存元数据和保存兼容；导入新模块不加载模型或读数据。

通过后再检查 CUDA 资源、实际模型小批编码与归一化，随后运行一次同库全量 Dense 开发集并核验。GPU 实测和全库完成前，不将这些计划写为已实现效果。

参考：[NumPy open_memmap](https://numpy.org/doc/stable/reference/generated/numpy.lib.format.open_memmap.html)、[NumPy load](https://numpy.org/doc/stable/reference/generated/numpy.load.html)、[SentenceTransformer 构造参数](https://sbert.net/docs/package_reference/sentence_transformer/model.html)。公开接口同时已核对本地安装版本。

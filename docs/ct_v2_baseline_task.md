# 当前工作单元：CT v2 纯向量检索基线

**状态：本轮 238 条证据、32 道开发题的纯向量实测已完成并核验通过。结果见 [实测归档](ct_v2_dense_baseline.md)。下文保留既定接口、配置与复现要求；后续进入固定数据下的 BM25／RRF 对照。**

日期：2026-11-18。由用户实现核心检索与评分，助手提供结果保存辅助。目标是将已有 B0 整理成可复用的检索与评测流程，再完成当前数据快照的基线；不重复 B0 的读文件和单条编码小练习。238 条语料、32 道开发题是本次输入的验收数量，不是程序常量，也不是最终规模。

用户已明确 OKF 留到完整数据扩充后再做对照；本轮按原计划进行，不增加 OKF 导出、工具或相关实验。

**当前执行顺序（2026-11-17 用户已确认）：先由用户编写两个核心模块，再编写正式基线运行脚本。** 实际文件为 retrieve_core.py、retrieve_evalution.py，接口沿用下述约定。2026-11-18 最新合成检查中，正常两题 2×16、六项指标与调用次数、来源返回、临时保存读回、评分空标注及评测 ks 入口校验均通过。retrieve 的 k<=0 校验已由用户修正，-1、0、1.0 均在编码前以 ValueError 拒绝，两个核心模块的合成验收通过。正式运行脚本已完成真实开发集运行并保存结果；原始结果核验通过，入口路径、main() 组织及后续完整配置记录一并收尾，不要求重跑模型。模块接收显式参数，不在导入时读取项目数据、实例化模型或运行评测。运行脚本导入这两个模块属于正常的单向依赖；核心模块不读取运行入口的全局变量。

## 向量模型接口：现在采用成品接口

  2026-11-17 用户明确要求最终项目使用什么接口，现在就使用，不安排以后再换封装。因此本轮统一使用 `langchain_huggingface.HuggingFaceEmbeddings`，遵循 LangChain 的 Embeddings 接口；底层仍为 Sentence Transformers 和同一个 BGE 模型。原 B0 Notebook 保留为历史实现，本轮及后续检索、Qdrant 集成使用统一接口。该设计现已由用户实现，并完成 CT v2 开发集纯向量实测。

已核对本地安装 langchain-huggingface 0.3.1、langchain-core 0.3.71、sentence-transformers 5.7.0；本地封装支持以下参数，无需升级环境。可对照[官方说明](https://docs.langchain.com/oss/python/integrations/embeddings/sentence_transformers)。用户自行创建 embedding_model，参数要求如下：

- `model_name`：`BAAI/bge-small-en-v1.5`，本轮不同时更换模型权重。
- `model_kwargs`：设置实际 `device`，如沿用已有可用的 cuda；模型加载参数与编码参数分开。
- `encode_kwargs`：文档编码设置 `batch_size=8`、`normalize_embeddings=True`、`prompt=""`，正文不附查询前缀。
- `query_encode_kwargs`：查询编码设置 `batch_size=1`、`normalize_embeddings=True`、`prompt=prefix`；prefix 仍为已有的英文检索前缀。查询参数独立指定，归一化也要显式给出。

文档调用 `embedding_model.embed_documents(texts)`，返回二维 Python 列表；查询调用 `embedding_model.embed_query(query)`，返回一维 Python 列表。参与已有 NumPy 点积前自行转成 float32 数组。前缀已经通过查询 prompt 配置，retrieve 不再手工拼接 prefix，不使用私有 _client 继续调用 encode。

模型在运行入口创建一次，作为依赖传入 retrieve。手写相似度、Top-K、指标和评测保留为用户核心代码，不替换成自动检索链。

本地 0.3.1 封装会将编码输入的换行替换为空格，这是接口层的实际预处理行为；查询记录仍保留原报告加问题模板，同时在配置中记录该行为。少量样例核对时检查模型、前缀次数、归一化及预处理，不能未经实测声称新旧接口逐位一致，也不要求额外用旧接口全量编码一次。

## 复用边界：本轮整理一次，以后更换输入

用户提出后续扩数据不能反复重做相同练习，因此本轮增加必要的接口整理，不改检索算法。以下是各文件的固定职责；两个核心模块已有用户实现并通过合成验收，正式运行脚本已接通并完成实测，入口组织待收尾：

- `retrieve_core.py`（原规划名 retrieval_core.py）：迁移已有向量检索函数，显式传入遵循 Embeddings 接口的编码对象、证据表和对应向量，避免依赖旧 Notebook 的全局状态。可采用接口 `retrieve(query, k, *, embedding_model, evidences, embeddings)`；内部查询编码使用 embed_query，前缀由编码对象的配置管理。相似度与排序继续复用已有实现，保持行顺序和输入绑定。
- `retrieve_evalution.py`（原规划名 retrieval_evaluation.py）：迁移原 recall_at_k，新增 group_recall_at_k，并将逐题检索、计时、评分整理成 `evaluate_retrieval(cases, retrieve_fn, ks=(1, 3, 5))`，返回 eval_df。retrieve_fn 是绑定当前语料和模型后的检索调用；只接收 query、k。此函数处理当前 CT 检索评测，不声称已经实现 MIRAGE 回答准确率评测。
- `run_retrieval_eval.py`：作为正式基线运行入口，集中设置文件路径、模型、查询模板、K 和 run_name，加载数据、准备向量、调用上述函数及保存辅助。装配流程放入 main()，通过脚本入口启动，导入时不执行。以后同结构数据扩充继续使用此入口，更新配置与运行名称，不复制另一套程序。

先在当前数据的少量开发题上检查新接口的向量形状、归一化、前缀处理及检索返回结构；同一新接口下核对整理前后的 ID、得分和顺序一致，再运行完整开发集。不用留出题检查或调试，不把未经实测的不同编码接口结果声称为完全等价。

循环长度、向量行数、评测题数都来自实际数据；检查向量行数等于 len(evidences)，结果题目集合等于当前开发题 ID 集合。本轮仍用 Top-5、K=1／3／5，不能同时增加新的检索策略。

以后新增同格式数据时，重新准备数据快照、生成新证据向量并运行同一评测入口，使用新的 run_name 和输入指纹保留旧结果。当前只要求全量编码，尚未实现向量缓存或增量索引，不能称为已有能力；将来有缓存时，正文、模型及编码设置相同才能复用，改变切分或模型时需重建受影响的向量。

扩充带来的必要工作仍需做：新来源需核验使用条件和解析质量，新题需标注和复核；新任务需适配查询与评测，例如 MIRAGE 使用 question-only 而非 CT 的报告加问题。复用检索引擎不等于可以跳过这些工作。比较算法时冻结相同数据版本；数据扩充本身的分数变化单独记录。

## 文件与固定设置

用户新建 `run_retrieval_eval.py` 作为正式运行脚本，使用上述成品编码接口，导入现有 retrieve_core.py、retrieve_evalution.py 和 retrieval_results_io.py，依次完成数据加载、模型初始化、证据编码、检索器绑定、批量评测与结果保存。保留既定函数接口与算法，不将检索或评分复制进脚本。数据版本、模型参数和结果验收沿用原约定；下载与数据构建仍是独立的数据准备流程。原 B0 实验及结果保留为历史记录。

- 证据：`data/v2/evidence.jsonl`，238 条。
- 题目：`data/v2/cases.dev.jsonl`，32 道；不加载 holdout 文件。
- 模型：`BAAI/bge-small-en-v1.5`，正文向量维度 384，正文和查询均归一化。
- 正文批量 8，查询批量 1；记录实际运行设备。
- 正文仅编码 text，不同时引入标题拼接、重排或改写。
- CT 查询模板仍为 `Report: {report}\nQuestion: {question}`，这里的 `\n` 为换行。
- 查询前缀仍为 `Represent this sentence for searching relevant passages: `，通过 query_encode_kwargs 的 prompt 配置，只加一次。
- 每题调用一次 retrieve，取得 Top-5，计算 K=1／3／5 的指标时截取同一次结果。

本次向量矩阵应为 `(238, 384)`，程序按实际证据条数核对行数，行顺序与证据表一致。原 retrieve 依赖全局 model、embeddings、evidences 和 prefix；本轮按新接口整理为显式依赖，不能把旧的 15 行向量与新表混用。相似度及排序算法保持一致，先做少量接口检查再完整评测。

## 由用户新增的评分函数

接口：`group_recall_at_k(retrieved_ids, gold_groups, k)`。

每个 group 表示一个必需证据需求，组内多个 ID 可以互相替代。前 K 条命中其中任意一个 ID，该组就记为命中；返回命中组数除以总组数。空的 gold 组列表应报错，避免把没有定义的指标记录成零或满分。

用于自己验证的小例子：检索结果 `[B, X, C]`，证据组 `[[A, B], [C]]`，组召回在 K=1／2／3 时分别为 0.5／0.5／1.0。同组同时命中 A 和 B 也只计一组。

同时复用原 `recall_at_k`，针对 gold_evidence_ids 计算规范 ID 召回。两者分开命名，不将一个替代 ID 未命中规范 ID 的情况直接当成缺失整个证据需求。最终对每题分数取平均。

retrieve_evalution.py 接收的 cases 为 pandas DataFrame。evaluate_retrieval 的 retrieve_fn 只需要接收 query 和 k，由后续运行入口绑定模型、证据表和向量；评测模块不创建模型。按既定 CT 模板组装报告加问题，检索 max(ks) 一次，再分别计算各个 K；返回与保存辅助约定一致的 eval_df。case_id 对应输入行的 id，gold_evidence_ids 和 gold_evidence_groups 只用于评分，不拼入查询。每题同时拥有这两份标注，需要计算两种指标，不根据 gold_evidence_ids 的列表类型二选一。

## 逐题结果与计时

每行保留 case_id、split、group、report、question、gold_evidence_ids、gold_evidence_groups、retrieved_ids、scores、latency_ms，以及以下六列：

- canonical_recall_at_1、canonical_recall_at_3、canonical_recall_at_5。
- group_recall_at_1、group_recall_at_3、group_recall_at_5。

latency_ms 只围绕 retrieve 调用计时，包括查询编码、相似度、排序和返回组装；打印、评分、模型加载和证据编码在计时范围外，保留首题。此次语料与题目版本已变化，指标变化不能归因于算法提升；设备不同也不能混为同条件延迟对照。

## 保存辅助：已由助手实现

[retrieval_results_io.py](../retrieval_results_io.py) 只检查并保存用户已经算好的结果，不执行编码、检索或评分。待 eval_df 完成后可使用以下辅助调用；配置需与实际执行一致：

```python
from retrieval_results_io import save_retrieval_results

config = {
    "data_version": "ct-v2.0-draft",
    "model_name": "BAAI/bge-small-en-v1.5",
    "embedding_interface": "langchain_huggingface.HuggingFaceEmbeddings",
    "device": embedding_model.model_kwargs["device"],
    "embedding_dim": int(embeddings.shape[1]),
    "normalize_embeddings": True,
    "document_batch_size": 8,
    "query_batch_size": 1,
    "query_prefix": prefix,
    "query_prefix_handling": "query_encode_kwargs.prompt; no manual concatenation",
    "embedding_text_preprocessing": "newline_to_space (langchain-huggingface 0.3.1)",
    "query_template": "Report: {report}\nQuestion: {question}",
    "retrieval_k": 5,
    "eval_ks": [1, 3, 5],
    "evidence_path": "data/v2/evidence.jsonl",
    "cases_path": "data/v2/cases.dev.jsonl",
}
summary = save_retrieval_results(eval_df, config, run_name="ct_v2_dense_dev")
print(summary["metrics"])
```

保存到 results/ct_v2_dense_dev_results.jsonl 与 results/ct_v2_dense_dev_summary.json，并记录实际输入文件指纹。此帮助代码已用临时目录中的合成 I/O 数据做读回检查；没有生成或声称真实检索成绩。

## 验收与下一步

本次 32 行开发题结果完整；每题 5 个不同证据 ID，均属于当前 238 条；得分降序；六个指标在 0–1，按题宏平均；原始定位保留。函数不依赖固定的 238／32，检索与评测模块不依赖运行入口的全局变量。提交向量形状、六项均值和逐题结果保存文件，助手检查代码与实际结果。无需先取得比 v1 更高的分数才算完成实现。

检查后进入固定数据下的 BM25／RRF 对照。并行保留 MIRAGE 必做工作：原题下载、上游条件核验、广泛医学语料选择与评测适配。MIRAGE 的检索输入是 question-only，CT 的报告加问题模板不能直接套用到该基准。

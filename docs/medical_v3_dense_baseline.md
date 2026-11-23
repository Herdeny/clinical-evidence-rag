# 医学主语料 v3 的 Dense 开发集基线

完成与独立核验日期：2026-11-20。核心编码编排、检索、评分和运行入口由用户实现；缓存I/O和独立核验由助手辅助。用户在自己的终端从529,408行断点继续，完成783,847行向量及原32道CT开发题。没有新增LLM生成、留出或MIRAGE评测。

## 固定输入与配置

- evidence.jsonl：783,847条，SHA-256为d120657651a681df56b29353fe69da5cabe8dff0c94bad55f673e99145c0bbd5。
- cases.ct.dev.jsonl：32道，SHA-256为f13291a4718866e06701370a0a6b1622bbf329f1514faac2885105f0fdc6f786。
- 接口为LangChain HuggingFaceEmbeddings，模型BAAI/bge-small-en-v1.5，revision固定5c38ec7c405ec4b44b94cc5a9bb96e735b38267a，device=cuda，local_files_only=True。
- 文档batch_size=8、normalize_embeddings=True、prompt为空；查询batch_size=1、normalize_embeddings=True、prompt为既有BGE查询前缀。封装会把换行替换为空格，实际依赖版本保存在缓存清单和审计。
- 查询保持Report加Question；NumPy矩阵乘法与完整分数排序，返回Top-5。GPU用于模型编码，NumPy相似度与排序仍在CPU执行。
- 外层chunk_size=512用于检查点，不等于GPU内部batch_size。没有改变语料、题目、标注或模型来解释本轮指标。

## 同库实测

| 方法 | Canonical／Group Recall@1 | @3 | @5 | 平均每题检索 |
| --- | ---: | ---: | ---: | ---: |
| BM25 | 0.28125 | 0.34375 | 0.453125 | 4332.917 ms |
| Dense | 0.1875 | 0.359375 | 0.421875 | 330.062 ms |

本轮两类指标的均值恰好一致，仍分别逐题重算。Dense中位数328.447 ms，32次检索合计10.562秒；计时包括首条查询编码、全库相似度、排序和组装，不包括加载、文档编码或保存。为单次开发集测量，不是生产服务压测。

Dense的Top-5需求组完整13题、部分1题、零18题。BM25为完整14、部分1、零17题。在现有标注下，Dense的@5低3.125个百分点；按题比较，Dense较高3题、BM25较高4题、相同25题。3题仅Dense有非零需求组覆盖，4题仅BM25有，11题两路均有，14题两路均零覆盖。

两路各Top-5合并成最多10条候选时，需求组平均覆盖为0.546875。它只展示候选互补性，没有实际融合排序、没有取融合Top-5，不能叫RRF成绩。题目仍为AI初标，证据召回不等于回答准确率或医学正确性。

Dense的160次命中来源类型为guideline 41、recommendation_statement 52、paper 50、evidence_summary 17。来源类型本身不证明内容适用或结论受支持。

## 完整缓存与恢复

缓存指纹为03f83f8aee178e40b006d7b80f395c7f50cdbc6ef292ee190e00b8a423c60b34，位于cache/embeddings下同名目录。正式vectors.npy为只读float32矩阵，形状(783847,384)，文件1,203,989,120字节，包含128字节NPY头；矩阵数据本体约1.121GiB，不是进程总内存。

向量文件SHA-256为83d0ea30b5bc6588391a6f3cd13f012bbe9467e58c82402110148dacef339688。已分块检查全库数值有限及归一化，L2范数范围0.9999998807907104至1.0000001192092896。逐行重算id/text有序指纹，与编码清单的d40c580df124b12c31cc4335f12e865a7fbe7e68b0ca0ab2c6a66dfd3b461dab一致。

首段主动中断并释放锁，断点529,408；用户第二段确实从该断点开始，提交剩余254,439行并发布完整矩阵。摘要cache_hit=False表示进入时只有半成品，initial_completed_rows=529408；不应将最终complete误读成进入时已经命中完整缓存。后续同配置调用应走完整读取分支。

## 分段资源与源码记录

| 运行段 | 范围 | 进程墙钟 | 峰值RSS | 结束 |
| --- | --- | ---: | ---: | --- |
| 第一段 | 助手后台编码，按用户要求移交 | 8:43.33 | 18,134,796 KiB | signal 2，实际会话退出130 |
| 第二段 | 用户终端恢复、完成及评测 | 3:52.87 | 18,135,152 KiB | 退出0 |

两段进程耗时之和756.20秒，即12:36.20，包含重复加载和首段未提交计算，不含移交等待。不能称为单次不中断冷启动编码耗时，第二段3:52.87也不是全库从零编码耗时。两段中较大的RSS约17.295GiB，内存峰值不相加。本轮没有单独计时纯文档编码。

首段GNU time同时写有Command terminated by signal 2与Exit status: 0，核验按信号和工具会话的130识别中断，保留原始文件，不把单个Exit status字段当作唯一依据。

第一段源码在启动前保存。用户续跑时给embedding_index.py增加tqdm和进度百分比；本次保留当前源码为segment2_observed_after_run，明确是运行后观察，不冒充续跑前固定。忽略这些进度显示语句后，语法树与首段一致；其余6个模块字节指纹一致。原CT v2和BM25全部受保护成绩指纹保持不变。

## 核验与下一步

- [原始摘要](../results/medical_v3_dense_ct_dev_summary.json)和[逐题结果](../results/medical_v3_dense_ct_dev_results.jsonl)。
- [独立核验](../results/medical_v3_dense_ct_dev_validation.json)：六指标、原题字段、标注／命中ID、完整矩阵、行序、输入、执行快照和历史结果。
- [运行审计](../results/medical_v3_dense_ct_dev_run_audit.json)：两段状态、资源、产物指纹及源码观察时间。
- results/medical_v3_dense_ct_dev_encoding_part1.log与_encoding_part2.log保存两段终端输出，对应_resources.txt保存资源原文。
- results/medical_v3_dense_ct_dev_code_snapshot/validate_saved_run.py保存本次独立验证程序；运行仅扫描产物，没有重新编码或检索。

下一步由用户实现[排名融合](rrf_task.md)。模型、语料和查询设置保持不变，同库比较RRF与两种单独基线。完整缓存可复用，无需再编码783,847条文档。

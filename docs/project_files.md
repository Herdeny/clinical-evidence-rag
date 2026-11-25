# 现在应该看哪些文件

整理日期：2026-11-19，进度更新2026-11-25。根目录现有18个Python模块，14个数据维护工具集中到scripts/data；用户query_rewrite.py及run_query_rewrite.py已通过本地假响应及CLI接线检查，尚无真实API或改写检索成绩，下一步用户终端真实单题。Qwen Dense与4B batch1／batch4、8B batch4、BGE batch4同候选dev均已实测。BGE保留负向对照，历史资源异常继续披露；助手未执行GPU或真实LLM调用。

| 根目录文件 | 职责 | 代码来源 |
| --- | --- | --- |
| retrieve_core.py | 已实现的向量相似度与 Top-K | 用户 |
| retrieve_bm25.py | 分词、BM25 构建与检索 | 用户 |
| retrieve_rrf.py | 多路排名融合与统一查询编排，12项合成检查通过；CLI已接入 | 用户 |
| rerank_core.py | 纯函数12项无权重验收通过，保留原生转换异常；Qwen4B／8B及BGE真实完整运行已共用 | 用户；助手仅整理异常提示及无用导入／空白 |
| query_rewrite.py | 单条检索表达改写与结构化结果，12个本地输入情形核对通过；原问题／用量保留，无真实API或收益结果 | 用户；助手未修改核心 |
| run_query_rewrite.py | 独立读取LLM配置、加载项目环境、构造客户端并单次调用核心；CLI到实际核心的假响应检查通过，真实单题待用户运行 | 用户；助手未修改实现 |
| frozen_candidates_io.py | 核对冻结产物和数据身份，按query_id恢复候选原文／分数／来源；6项检查及真实324题加载通过，不加载模型或向量 | 助手辅助，逐行中文注释 |
| retrieve_evalution.py | 两类 Recall 与逐题批量评测，沿用实际文件名 | 用户 |
| run_retrieval_eval.py | CLI、方法选择与评测入口 | 用户 |
| embedding_index.py | 分批模型编码、缓存复用和恢复；已完成全库及用户终端续跑验证 | 用户 |
| embedding_adapter.py | 共享模型构造与显式FP32输出归一化；6项无权重验证通过，预检和正式入口已共用，真实GPU预检03通过 | 助手辅助，逐行中文注释 |
| reranker_adapter.py | build_reranker加载固定CrossEncoder；describe_reranker记录实际设备／精度／长度／指令等；Qwen4B／8B及BGE真实完整运行均已核对 | 助手辅助，逐行中文注释 |
| embedding_cache_io.py | 向量缓存文件、身份、断点、发布与校验；实际输出策略进入身份，BGE旧指纹保留 | 助手辅助，逐行中文注释 |
| retrieval_results_io.py | 验证并保存CT及BEIR既有结果；save_beir_results支持原方法及frozen_rerank，保留候选来源和正确计时范围 | 助手辅助，逐行中文注释 |
| benchmark_data.py | BEIR基准读取适配，真实dev、通用目录、ID保真及既定输入检查9项全部通过 | 用户 |
| benchmark_eval.py | 公共查询循环与逐题评分；新增可选query_id回调和冻结候选重排包装，10项小样本检查通过，真实324题假打分衔接核对通过 | 用户 |
| run_benchmark_eval.py | 三方法及BGE／Qwen配置选择，config_dir必填，15项临时集成检查通过；旧三方法dev已核验，Qwen完整dev已实测核验，未接重排 | 用户 |
| run_reranking_eval.py | 固定候选重排入口；Qwen4B batch1／batch4、8B batch4及BGE batch4完整dev、指标已核对；旧历史资源异常另有披露 | 用户 |

## 数据维护模块

configs/llm_profiles.json由助手补充，保存DeepSeek公开参数，不含密钥；run_query_rewrite.py已由用户实现并通过本地CLI接线检查，不从Notebook导入。完整逻辑、参数及用户首次真实单题命令见query_rewrite_task.md。本地核验记录results/query_rewrite_entry_validation_01.json，不是API或检索成绩。

configs/reranker_profiles.json保存三种重排候选的固定版本与运行参数。tests现有21个模块；原模型支持／入口相关50项与预检辅助相关14项均通过，真实GPU预检另有已保存报告。新增test_beir_run_validation.py的4项验证新重排／原BM25的完整临时产物协议、候选集合、固定配置与资源CLI身份；未加载模型。当前用户下一项见reranking_runtime_task.md完整开发集节；文末“17个模块”属于此前整理记录。

| scripts/data 内的模块 | 保留理由 |
| --- | --- |
| prepare_medical_corpus.py | PMC 候选查询与原始 XML 下载可复现 |
| prepare_drug_sources.py | DailyMed 产品身份解析及官方来源下载可复现 |
| prepare_mirage_data.py | 独立外部题库的下载、许可保留与快照核验 |
| medical_corpus_parsing.py | 主库结构化正文、表格与长度处理，构建和测试仍依赖 |
| build_medical_corpus.py | 从原始快照重建统一主库和来源清单 |
| validate_medical_corpus.py | 独立核对主库片段、位置、指纹和 token |
| document_parsing.py | CT PDF 编号注释分段，CT 构建和测试仍依赖 |
| ct_data_pipeline.py | CT 原始资料适配及统一证据构建 |
| ct_case_blueprints.py | 保存合成题家族与初标依据，不是废弃样例 |
| validate_ct_data.py | CT 来源位置、划分与标注引用的完整性核验 |
| build_ct_evaluation.py | 以固定条款扩展评测题，保护旧题与人工复核表，不做检索 |
| validate_ct_evaluation.py | 独立核对扩题划分、原文位置、旧成绩与完整文档向量身份 |
| prepare_nfcorpus.py | 固定BEIR官方镜像提交和原始文件，转换标准BEIR容器并核对ID／划分 |
| validate_nfcorpus.py | 独立核验原始字段、标签文件、数据身份及本地token长度，不执行模型 |

这些脚本不进入检索／编码运行时的隐式调用。日常从根目录入口开发；需要维护数据时，按[下载和处理记录](data_acquisition_and_processing.md)使用 `python -m scripts.data.模块名`。

## 评测核验工具

scripts/evaluation/preflight_reranker.py由助手提供，调用与正式入口相同的加载器和模型构造接口，扫描全部固定候选的真实联合输入长度；batch1保留首两对加最长一对，batch>1选出最长batch_size对实际覆盖完整批次，报告实际样本数及是否覆盖整批，记录CUDA／BF16／预算／显存及来源指纹，不运行完整排序评分。Qwen4B batch1、8B batch4预检01及4B batch4预检02均已完成，正式dev也已执行；4B预检02资源后来被中断尝试覆盖，原JSON与日志保留，历史异常见ENG-025，不能将当前资源文件与旧成功JSON拼作同一轮。tests/test_reranker_preflight.py现5项CPU检查，BGE下载后继续复用工具独立预检。

scripts/evaluation/validate_beir_run.py已适配frozen_rerank：固定候选集合／模型实际配置与原最大K召回不变量核对，按重排入口实际--profile检查资源命令，旧方法保留--method。4项新临时检查通过；正式完整运行结束后再核对原始产物，不为适配核验工具修改用户CLI。

scripts/evaluation/validate_beir_run.py从已保存run及原始标注重新评分，检查题目覆盖、原query、分数、指标均值、输入／源码与资源统计，验证通过后更新本地审计。它不重新检索或加载模型，不在检索入口中隐式运行。三种方法首轮均通过；Dense缓存分块核对形状、数值、范数与文件身份，RRF还从归档两路排名独立重算324题的名次贡献并检查旧产物未改。历史执行快照必须匹配回执，后续开发后的当前工作区是否一致另报布尔值；结果汇总见docs/nfcorpus_retrieval_baselines.md。

## 清理范围与记录

本轮新增scripts/evaluation/preflight_embeddings.py，负责用户终端的小批模型预检，检查真实设备／精度、输入长度、向量与GPU峰值；不创建全库向量或评测效果。tests/test_embedding_preflight.py有4项无权重检查通过。完整运行命令及分工见docs/dense_model_selection_task.md。

本次将 10 个数据脚本移出根目录，同步脚本之间及测试中的导入，调整 3 个 ROOT 定位和构建清单中的代码路径。没有发现可以直接丢弃且完全没有复现／测试用途的独立临时源码，因此没有为了减少数量而删掉下载与验证能力。9 个旧路径的自动编译 .pyc 已删除，可由 Python 自动重建。

tests中现有17个测试模块，均有逐行中文注释。test_embedding_index.py验证编码恢复；test_rrf_fusion.py含7项融合和5项编排，已通过。test_retrieval_entry.py的5项入口检查已通过，使用临时数据、假模型及真实小型检索／评分／保存。test_retrieval_results_io.py的6项检查验证分组／旧平铺保存、配置不变与错误定位。test_ct_evaluation.py的4项检查验证来源选择漂移、家族边界及实际快照重建／人工修改保护。test_benchmark_data.py的9个方法检查公开dev、通用目录和数据完整性，已全部通过。test_benchmark_eval.py现有10个方法，原7项验证单次预算、原查询、等级排序、自定义K、空命中分母和异常输入，新3项验证ID回调、完整重排句对／候选副本和空题分母，均已通过；只用小型材料与假打分器。加载器6项及重排核心12项同时通过，共28项，真实324题另外验证候选联结和召回集合不变量，不是模型效果。test_beir_results_io.py的6项检查验证BEIR三份产物、空题分母、输入指纹、配置保真、矛盾run拒绝与覆盖保护，已通过；旧保存6项也复验通过。test_benchmark_entry.py的15项检查使用临时BEIR、假模型和真实小型检索／保存验证入口，已全部通过。其他覆盖来源位置、数据划分和缓存恢复。scripts的两个__init__.py仅标记Python包。

原始数据、冻结清单、历史执行源码快照、结果及 Notebook 作为已有记录保留。Notebook 中的历史根目录导入可能是当时的路径，当前操作以脚本和本文目录为准，不把 Notebook 重新作为生产依赖。

整理前源码与迁移清单：results/source_maintenance_2026-11-19。该目录是历史审计，不是新的运行入口。未来真正无依赖的一次性探测脚本可以删除，但其输入来源、命令／参数、时间与指纹、失败原因及最终产物必须先进入文档或审计记录。

模型命令通过scripts/project_env.sh启动；它只对子进程设置项目内模型／下载后端缓存，不更改全局shell配置。缓存迁移记录在results/model_cache_migration_2026-11-24.json，下载和加载命令以docs/dense_model_selection_task.md更新版为准。

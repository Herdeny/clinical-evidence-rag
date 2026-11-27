# 现在应该看哪些文件

**当前任务：核查并接入原作者公开发布的检索语料。** 用户已删除v3并明确检索语料也只用可考据的公开数据集，不恢复旧库。QA RAG入口已通过10组本地检查，三方法、闭卷、引用映射、错误处理、配置保存及原BEIR路径均通过，无真实新模型／API／GPU调用。CLI沿用--model-name／--config，Embedding参数统一为--embedding-model。下一项见[公开配套语料核查](benchmark_scope.md#2026-11-27检索语料也只采用公开发布的数据集)：PubMed优先候选但尚未下载或冻结版本，先核查容量；不再给v3运行命令。用户已完成500题闭卷实测61.0%／Macro-F1 0.470773，最终MIRAGE及真实RAG未运行。

PubMedQA开发池已由用户亲自准备并通过实际核查：固定原作者提交1cbae8e，1000专家题减官方500测试得到500开发，MIRAGE测试ID／全题库规范化题干／记录中参考PMID交集均0。读取shape=(500,4)，标签yes／no／maybe为276／169／55；已有数据加载器直接复用。真实日志／资源及数据指纹见results/pubmedqa_development_prepare_01_validation.json，没有模型成绩。原准备记录保留历史状态；PR #1已合并，一次性例外结束，本轮恢复main提交推送。

**最新验收：load_mirage_dataset已通过离线读取验证。** 全量(7663,4)与7663项答案字典、五任务数量／顺序、原文／选项／答案保真、唯一ID和独立gold均通过；空与未知任务名正确拒绝，三份原件及旧函数AST未变。既有BEIR的9项测试通过；没有模型／API调用。验证保存在本地results/mirage_loader_validation_01.json，先前review_01／02保留。按用户仅本次要求通过codex/mirage-dataset-loader分支创建PR后直接合并；后续恢复原提交同步方式。

**已实现：benchmark_data.py中的load_mirage_dataset(benchmark_path, *, task=None)。** MIRAGE五上游公开声明与任务角色已核查；五部分都作最终评测，上游dev不等于本项目调参集。函数返回四列questions_df（id／task／query／options）和单独gold_answers；不传answer／参考PMID给检索或生成。按官方sorted字符串题号，保留前导零和原文本，None读取全量7663，单任务可选。完整约定与验收见[读取适配记录](benchmark_scope.md#mirage读取函数已验收)。独立官方开发池500题无检索生成及评分已完成，最终MIRAGE与RAG对照待完成。

**2026-11-26最新要求：评测只用可核查的公开benchmark。** 324题来自NFCorpus官方dev，120题来自助手自建CT初稿，二者不能混称。刚提出的120题运行计划已撤回，未执行；自建题及成绩仅保留历史，不继续扩题、调参或作效果依据。当前公开主线为已完成dev对照的NFCorpus及待QA适配的MIRAGE7663；下一项先核查MIRAGE上游条件与开发／测试协议，再复用既有模块增量接入。专项追问／引用／多模态需另选覆盖相应标注的公开benchmark。详见[当前评测范围](benchmark_scope.md#2026-11-26仅使用可核查的公开benchmark)，以下CT待运行安排按历史理解。

整理日期：2026-11-19，进度更新2026-11-26。根目录共22个受版本管理的Python模块（含进行中的qa_core.py），另有用户未完成／未跟踪的run_query_rewrite_retrieval_eval.py草稿，保留待整理；14个数据维护工具集中到scripts/data。用户已亲自完成324题三方法改写对照，并完成CT单轮评估3题真实联调。结构化响应均有效，但观察到过度追问、已知事实误列缺项和适用条件推断错误，待受控上下文诊断。有限补查与图编排待完成。此前误代跑及权限纠正、负结果和历史异常继续保留。

原retrieve_evalution.py的可选review_fn增量已通过合成联结验收：关闭／开启均保留题目，完整核验字典及独立review_latency_ms可保存；CT检索耗时采用用户命名retrieve_latency_ms，保存辅助及其既有检查随核心更新，不要求旧名或添加兼容别名。下一步仍在原run_retrieval_eval.py按需开启，三方法共同复用，不新增运行脚本。三份既有本地控制输入位于data/evaluation/evidence_review/smoke_01，保留不冒充实际检索结果。完整任务见下段与PROJECT_CONTEXT.md第1节／10.5.1；助手不代写核心或代跑，后续LangGraph直接复用review_evidence，不依赖含gold的评测main。

原run_retrieval_eval.py可选评估已通过5项入口／CLI与9组假模型联结，并完成medical_v3_bm25_ct_review_smoke_3_01真实3题。三次有效结构化响应共7527 tokens，语义问题见[联调记录](medical_v3_bm25_baseline.md)。当前复用同入口和原--evidences参数，以scope_context_control_5.jsonl给同三题提供明确范围依据，只做评估器诊断；索引实际仅5条，不计作全库检索改进。准备记录在本地results/medical_v3_bm25_ct_review_scope_control_3_01_preparation.json；助手不改核心或prompt、不代跑，真实调用由用户执行。完整进度见PROJECT_CONTEXT.md第1节。

受控对照现已由用户完成：三题充分性由false／false／false变为true／true／false，前两题不必要缺项消失，第三题仍索要超出当前范围的资料。用户随后只改evidence_review.py现有system提示词，强化当前决策层次、缺失事实的必要性、上游适用条件与两类缺口独立判断；五字段和Python校验、模型、数据均保持。助手已通过语法／消息构造检查，并以AST确认提示词以外代码不变，未修改核心或发起新调用。下一项由用户运行medical_v3_bm25_ct_review_scope_control_3_02，同组3题／5片段／deepseek_flash；本地_preparation.json保存新旧身份，真实效果待回归，完整开发验证仍待完成。

02与03现已由用户完成，分别使用Flash和新增deepseek_v4_pro profile；模型响应标识与命令／配置一致。三轮逐题问题、候选ID／分数及Recall相同，02标签true／true／false，03全false；02第三题仍过度追问和补查，03前两题反而混淆已知筛查背景与资格条件，第一题还把证据内容归入报告。03第三题的missing_evidence为空，是两类缺口区分的局部改善。详见[实测对照](medical_v3_bm25_baseline.md#2026-11-26提示词增量后的flash与v4-pro对照)，不据标签数认定安全或准确，不因三题切换默认。两个_validation.json及03_comparison.json保留本地，下一项是既定正式开发验证；助手未调用模型或新增脚本。

| 根目录文件 | 职责 | 代码来源 |
| --- | --- | --- |
| retrieve_core.py | 已实现的向量相似度与 Top-K | 用户 |
| retrieve_bm25.py | 分词、BM25 构建与检索 | 用户 |
| retrieve_rrf.py | 多路排名融合与统一查询编排，12项合成检查通过；CLI已接入 | 用户 |
| rerank_core.py | 纯函数12项无权重验收通过，保留原生转换异常；Qwen4B／8B及BGE真实完整运行已共用 | 用户；助手仅整理异常提示及无用导入／空白 |
| query_rewrite.py | 单题真实CT通过；批量rewrite_queries已通过4题混合假响应及编程异常传播检查，失败记录／用量保留；无批量API或改写检索收益 | 用户；助手未修改核心 |
| qa_core.py | 单题真实联调通过；iter_question_answers通过19项本地检查，支持惰性逐题产出、统一检索与API失败继续，无真实批量成绩 | 用户；助手只读检查，未修改核心 |
| evidence_review.py | 五字段与单轮评估通过18项假响应检查；用户完成提示词增量及Flash／V4 Pro三题对照，仍有任务边界与报告事实混淆，待正式开发验证 | 用户；助手只读审查，未改核心 |
| run_query_rewrite.py | 独立读取LLM配置、加载项目环境并单次调用核心；用户真实CT单题通过，422／96／518 tokens，CLI已统一--config | 用户；助手只纠正CLI参数，业务函数未改 |
| run_query_rewrite_batch.py | 指定划分／limit、共享客户端、保存结果；用户真实8题已核验，1变化有语义观察，尚无检索收益 | 用户；助手未修改实现 |
| query_rewrite_io.py | save_rewrite_results保存逐题JSONL、状态／已知token摘要及公开运行配置，防覆盖；实际单题已无损归档 | 助手辅助，每行中文注释；不调用模型或读取环境 |
| frozen_candidates_io.py | 核对冻结产物和数据身份，按query_id恢复候选原文／分数／来源；6项检查及真实324题加载通过，不加载模型或向量 | 助手辅助，逐行中文注释 |
| retrieve_evalution.py | 两类Recall、逐题批量评测及可选review_fn；合成联结通过，CT分阶段计时为retrieve_latency_ms／review_latency_ms | 用户；助手未改核心 |
| run_retrieval_eval.py | 三方法可选评估入口；假模型联结及3题真实链路完成，复用--evidences做固定问题的上下文诊断 | 用户；助手未改核心 |
| embedding_index.py | 分批模型编码、缓存复用和恢复；已完成全库及用户终端续跑验证 | 用户 |
| embedding_adapter.py | 共享模型构造与显式FP32输出归一化；6项无权重验证通过，预检和正式入口已共用，真实GPU预检03通过 | 助手辅助，逐行中文注释 |
| reranker_adapter.py | build_reranker加载固定CrossEncoder；describe_reranker记录实际设备／精度／长度／指令等；Qwen4B／8B及BGE真实完整运行均已核对 | 助手辅助，逐行中文注释 |
| embedding_cache_io.py | 向量缓存文件、身份、断点、发布与校验；实际输出策略进入身份，BGE旧指纹保留 | 助手辅助，逐行中文注释 |
| retrieval_results_io.py | 原CT／BEIR保存保留；save_qa_results流式保存、调用用户评分并保留中断记录，11项本地检查通过，未知用量不补0 | 助手辅助，逐行中文注释，旧四函数AST未改 |
| benchmark_data.py | BEIR读取与apply_query_rewrites已完成；MIRAGE全量／五单任务读取、四列问题表与独立gold字典已验收，旧函数不变 | 用户；助手未改核心 |
| benchmark_eval.py | 原检索评测保留；evaluate_multiple_choice支持任务宏平均及PubMedQA F1，已用于500题真实无检索开发基线 | 用户；助手未改核心 |
| run_benchmark_eval.py | 三方法可选改写及防覆盖已验收；用户324题三方法02已实测核验，无需重写；改写收益与退化均归档 | 用户；助手未改核心 |
| run_reranking_eval.py | 固定候选重排入口；四套重排dev已核对，旧历史资源异常继续披露；CLI统一--config且原业务函数不变 | 用户；助手只纠正CLI参数 |

## 数据维护模块

configs/llm_profiles.json由助手补充，保存公开参数，不含密钥；真实8题生成核验及语义观察原件保留。适配及两组评测记录分别为results/query_rewrite_input_adapter_validation_01.json、query_rewrite_paired_eval_validation_01.json；成功来源标签沿用用户的llm_rewrite_query。下一项在原入口增量接入三方法可选改写，具体任务见query_rewrite_task.md，不继续独立入口。复用保存的改写和原文档缓存，不重发API；CLI只用--config／args.config，保留原默认参数和run-name可选公式。未跟踪草稿不由助手删除。

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

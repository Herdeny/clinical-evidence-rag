# 医疗证据检索项目 · 医学主语料 v3 已冻结

项目完整背景、当前进度、后续路线与合作约定见 [项目交接总记录](PROJECT_CONTEXT.md)。继续开发或切换对话时先读该文件，再核对最新代码和输出。

代码目录已整理：根目录已有20个受版本管理的Python模块，14个可复现数据工具集中在scripts/data。参见[文件导航](docs/project_files.md)与[数据下载和处理过程](docs/data_acquisition_and_processing.md)。

**2026-11-26当前：用户已完成324题三方法查询改写对照并核验。** 同一NFCorpus324dev，BM25、Qwen8B Dense及Qwen8B RRF各比较原问题／保存表达。仅12条表达变化、312条原样；Dense nDCG@10为0.392196→0.392264、Recall@100为0.397097→0.397362，Recall@10略降，原32道零召回题全部未被改写且仍零召回。BM25及RRF的Recall@100略降。当前保留原查询默认与改写可选，不宣称通用改写必然改善召回。完整四指标、逐题差异和成本范围见[全量归档](docs/nfcorpus_retrieval_baselines.md#用户324题查询改写三方法02收益很小且不一致)。下一阶段按原计划开展证据核验与有限补查，尚未实现；真实模型／API／GPU由用户执行。

**重排阶段归档：既定候选对照完成。** 同一324题／原Qwen Dense Top100，4B batch1的nDCG@10／Recall@10为0.409974／0.206984、重排均值3.258秒/题；4B batch4为0.407701／0.205120、3.236秒/题；8B batch4为0.416582／0.202992、5.430秒/题。BGE-v2-m3 batch4为0.329419／0.147297、267.758ms/题，对原Dense两指标下降16.01%／23.36%，保留负向结果，不因快而启用。全部Recall@100保持0.397097。BGE本周期的逐题指标、候选、源码／配置及86个文件身份通过核验，旧资源异常继续继承披露，详见[完整实测与边界](docs/nfcorpus_retrieval_baselines.md#bge-v2-m3重排负向结果与阶段结论)。Qwen8B保留效果对照、4B保留成本对照；后续固定Qwen Dense的改写全量结果见上方。医学专项与MIRAGE全量问答仍待完成。

**2026-11-21：CT专项评测扩充草稿已完成。** 新增132题，加原48题，共120开发／60留出、30规则家族，每族6个相关变体。4项构建器检查及独立结构复验通过，主库、完整向量与旧成绩未变；所有标签仍待独立人工复核。下一步在固定120道开发草稿上做三方法探索性对照，明确披露AI初标；不要求用户先逐题填写复核表，正式结论另行核查标签质量。详见[题集说明](data/evaluation/ct_v3/DATA_CARD.md)。

**2026-11-20：医学v3全库BM25和Dense基线均已完成并核验。** 783,847片段／32开发题，BM25的Group Recall@1／3／5为0.28125／0.34375／0.453125，Dense为0.1875／0.359375／0.421875；平均查询分别4332.917ms与330.062ms。完整Dense矩阵可复用。见[BM25归档](docs/medical_v3_bm25_baseline.md)与[Dense归档及分段资源](docs/medical_v3_dense_baseline.md)。RRF功能现已接入，等待新题复核后做正式对照，不重编码。

医学主语料 v3 已完成扩充与完整性验证：**10,840 来源、783,847 个片段、594,483 条不同正文**。其中 9,836 篇 PMC 论文、998 份产品说明书和原 CT 238 条。见 [v3 数据说明](data/v3/DATA_CARD.md)、[调研与使用条件](docs/medical_corpus_v3_research.md)和[核验记录](results/medical_corpus_v3_validation.json)。两种单独基线已完成本库实测，接下来按同一输入做RRF，已有接口与辅助继续复用。

[数据扩充节点](docs/data_expansion_milestones.md)现已提前：先核验并批量接入主要医学检索语料、固定新版本，再做正式方法对照。现有 CT 小库用于回归，不要求再在其上完成一轮 BM25／RRF 正式实验。

当前RRF功能接入已完成：融合／编排12项、入口5项、保存辅助6项相应检查通过。model_name等信息保留在各自方法层，保存辅助原样支持该结构并兼容旧平铺配置。专项评测已扩题，下一步[运行开发集探索性对照](docs/data_expansion_milestones.md)，原32题保留为回归；目前没有真实全库RRF成绩。此前[Dense完整缓存](docs/dense_cache_task.md)继续复用。

开发方式已确定：所有任务按成品方向增量建设，核心代码由用户实现，阶段推进复用同一套模块与接口；不为教学便利先写临时版本再重做。详细约定见 [合作方式](PROJECT_CONTEXT.md#138-全部任务按成品方向增量开发保持标准连续)。

最终验收必须完成 **MIRAGE 全量 7,663 题的公开基准对标**，并交付报告／用药／多模态的专项证据链验证。要求与当前未完成项见 [对标范围与验收](docs/benchmark_scope.md)。当前 CT 数据包为阶段成果，尚无 MIRAGE 成绩。

当前 CT v2 数据准备已整批完成：**238 条本地检索输入、48 道 AI 初标题、24 个场景家族，32 开发／16 留出**。先看 [数据说明与复现](data/v2/DATA_CARD.md) 和 [批量交付记录](docs/ct_v2_delivery.md)。12 项测试及数据指纹复现通过；题目未独立人工或医生复核，已有 CT v2 开发集纯向量检索实测，尚无新增生成回答或临床有效性成绩。

[CT v2 纯向量基线](docs/ct_v2_dense_baseline.md)已完成 32 道开发题实测与独立复算核验，Group Recall@1／3／5 为 0.21875／0.421875／0.484375；正式入口为 `run_retrieval_eval.py`。医学v3主语料的BM25和Dense正式对照也已完成，接下来做RRF；新旧语料规模不同，不将其分数差直接归因于算法。MIRAGE 原始7,663题已下载并核验快照，全量模型对标仍待完成。

下面保留原 B0 起始练习与 v1 资料说明。继续开发使用 v3 主语料及原 CT 开发题做新库对照，不从本页“第一步”重新开始。

实际开发中遇到的问题、处理状态和面试复盘见 [工程问题与面试复盘](docs/engineering_issues.md)。记录区分已修正、待复测和后续计划，并保留可回查的实验快照。

当前扩充与待补项见 [数据扩充节点](docs/data_expansion_milestones.md)。原 [CT 数据集 v2 来源核验与计划](docs/data_v2_plan.md)及[v2 候选来源清单](data/v2/source_candidates.json)保留作历史记录。

| 文件 | 内容 |
| --- | --- |
| `data/sources.json` | 5 个可回查的原始来源，含发布机构、标题和链接 |
| `data/evidence.jsonl` | 15 张英文证据卡，每张有原文定位。正文为供本项目使用的转述 |
| `data/cases.jsonl` | 12 道合成报告题，8 道开发题、4 道留出题，带人工初标的证据 ID |

两个核心来源是 [ACR Lung-RADS](https://www.acr.org/clinical-resources/clinical-tools-and-reference/reporting-and-data-systems/lung-rads) 和 [Fleischner 2017](https://pubs.rsna.org/doi/full/10.1148/radiol.2017161659)。ACR 偶发结节影像适宜性标准和 USPSTF 筛查建议提供与主任务接近但用途不同的证据。使用时通过卡片的来源链接核对原文。开发集和留出集按场景组分开，标签用于教学，尚未经过医生复核。

## 第一步：读取证据卡

打开 `data/evidence.jsonl` 看前两行。每一行是一张独立的证据卡，`text` 是证据正文，`id` 是卡片编号，`source_id` 和 `locator` 用于定位原始来源。

新建 `b0_practice.py`，把每一行非空内容解析成字典，存进同一个列表。用 Python 标准库里的 `json` 模块就够了。

验收时打印卡片总数、第一张卡片的 `id` 和 `text`。总数应为 15，第一张卡片的内容应和原文件第一行一致。

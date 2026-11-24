# 现在应该看哪些文件

整理日期：2026-11-19，进度更新2026-11-24。根目录现有10个Python模块，14个数据维护工具集中到scripts/data；Dense缓存、RRF两函数和三个方法入口已通过相应检查，方法层配置原样保存。NFCorpus公开基准读取适配9项、公共检索评测7项检查均已通过，保存辅助已提供，当前由用户实现独立运行入口run_benchmark_eval.py，该入口尚未计入现有模块数。

| 根目录文件 | 职责 | 代码来源 |
| --- | --- | --- |
| retrieve_core.py | 已实现的向量相似度与 Top-K | 用户 |
| retrieve_bm25.py | 分词、BM25 构建与检索 | 用户 |
| retrieve_rrf.py | 多路排名融合与统一查询编排，12项合成检查通过；CLI已接入 | 用户 |
| retrieve_evalution.py | 两类 Recall 与逐题批量评测，沿用实际文件名 | 用户 |
| run_retrieval_eval.py | CLI、方法选择与评测入口 | 用户 |
| embedding_index.py | 分批模型编码、缓存复用和恢复；已完成全库及用户终端续跑验证 | 用户 |
| embedding_cache_io.py | 向量缓存文件、身份、断点、发布与校验 | 助手辅助，逐行中文注释 |
| retrieval_results_io.py | 验证并保存CT及BEIR既有结果；新增save_beir_results，支持方法层配置，保留旧接口 | 助手辅助，逐行中文注释 |
| benchmark_data.py | BEIR基准读取适配，真实dev、通用目录、ID保真及既定输入检查9项全部通过 | 用户 |
| benchmark_eval.py | 公共查询循环与逐题评分，7项临时数据验收全部通过；无公开基准成绩 | 用户 |

## 数据维护模块

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

## 清理范围与记录

本次将 10 个数据脚本移出根目录，同步脚本之间及测试中的导入，调整 3 个 ROOT 定位和构建清单中的代码路径。没有发现可以直接丢弃且完全没有复现／测试用途的独立临时源码，因此没有为了减少数量而删掉下载与验证能力。9 个旧路径的自动编译 .pyc 已删除，可由 Python 自动重建。

tests中现有12个测试模块，均有逐行中文注释。test_embedding_index.py验证编码恢复；test_rrf_fusion.py含7项融合和5项编排，已通过。test_retrieval_entry.py的5项入口检查已通过，使用临时数据、假模型及真实小型检索／评分／保存。test_retrieval_results_io.py的6项检查验证分组／旧平铺保存、配置不变与错误定位。test_ct_evaluation.py的4项检查验证来源选择漂移、缺事实／缺规则分离、家族边界及实际快照重建／人工修改保护。test_benchmark_data.py的9个方法检查公开dev、通用目录和数据完整性，已全部通过。新增test_benchmark_eval.py的7个方法验证单次预算、原查询、等级排序、自定义K、空命中分母和异常输入，已全部通过；只用临时材料，不运行公开题库或模型。test_beir_results_io.py的6项检查验证BEIR三份产物、空题分母、输入指纹、配置保真、矛盾run拒绝与覆盖保护，已通过；旧保存6项也复验通过。其他覆盖来源位置、数据划分和缓存恢复。scripts的两个__init__.py仅标记Python包。

原始数据、冻结清单、历史执行源码快照、结果及 Notebook 作为已有记录保留。Notebook 中的历史根目录导入可能是当时的路径，当前操作以脚本和本文目录为准，不把 Notebook 重新作为生产依赖。

整理前源码与迁移清单：results/source_maintenance_2026-11-19。该目录是历史审计，不是新的运行入口。未来真正无依赖的一次性探测脚本可以删除，但其输入来源、命令／参数、时间与指纹、失败原因及最终产物必须先进入文档或审计记录。

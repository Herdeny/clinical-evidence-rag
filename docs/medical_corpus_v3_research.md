# 医学主语料 v3：来源、相似工作与接入决定

核验日期：2026-11-18。本文描述助手负责的批量数据准备；不把下载、解析或别人的 README 宣传写成用户已经实现的检索／Agent 能力。实际数量与输入指纹以 data/v3/corpus_manifest.json 和 results/medical_corpus_v3_validation.json 为准。

## 本轮决定与边界

保留 CT v2 基线，先准备并冻结一个足以开展正式检索对照的医学主语料版本，再建立新版本的向量／BM25／RRF 对照。不是先在 238 条上完成所有方法，再为扩库重复所有实验。冻结的是这一轮主要检索输入，不代表用药评测、多模态和临床复核均已完成。

选择 PMC 官方 Cloud 的 CC BY／CC0 正文和 DailyMed 官方 SPL；保留现有 CT 原文证据及 ID。检索模块继续接收同一证据字段结构，不因条数增长更换 LangChain Embeddings 接口、重写评分或反向依赖 Notebook。文件数、可用来源数、片段数、去重内容数、评测题数分别统计。

只下载原文、使用本地 BGE tokenizer 计数，没有调用嵌入模型、GPU 推理或付费生成 API。没有读取 MIRAGE 测试问题、选项、答案或 gold 上下文来选库、分段或调参。下载的 7,663 题仍是独立评测材料。

## 来源条件及实际处理

| 来源 | 核验依据 | 本轮处理 |
| --- | --- | --- |
| PMC Open Access Cloud | [官方访问说明](https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/)与[桶内 README](https://pmc-oa-opendata.s3.amazonaws.com/README.txt) | 使用官方匿名 S3 元数据和 JATS XML，不抓文章网页。只接纳 CC BY／CC0、非撤稿、非作者手稿、非历史 OCR；保留逐篇元数据、许可链接、作者、引用、版本、SHA-256 和供应方 MD5。 |
| DailyMed SPL | [官方 API](https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm)、[列表参数](https://dailymed.nlm.nih.gov/dailymed/webservices-help/v2/spls_api.cfm)、[setID 接口](https://dailymed.nlm.nih.gov/dailymed/webservices-help/v2/spls_setid_api.cfm) | human prescription label；保留 setID、SPL 版本、有效时间、成分／活性基团、强度、剂型、NDC 产品代码及提交机构。NDA／ANDA／BLA 是标签自报类别，未逐一通过 Drugs@FDA 验证；DailyMed 的 in-use 标签不等同于保证为最新 FDA 批准标签。 |
| NIH 成人／青少年 ARV 指南 | [PI 相互作用表](https://clinicalinfo.hiv.gov/en/guidelines/hiv-clinical-guidelines-adult-and-adolescent-arv/drug-interactions-protease-inhibitors)、[心血管章节](https://clinicalinfo.hiv.gov/en/guidelines/hiv-clinical-guidelines-adult-and-adolescent-arv/cardiovascular-complications) | 浏览核验能访问；本机原文请求及网页提供的官方 PDF 链接均返回 403，失败记录保留，不假装已入库。未关闭证书检查、绕过限制或把浏览器提取文本冒充原始 HTML。 |
| 现有 CT v2 | data/v2/DATA_CARD.md 和 USAGE.md | 238 条正文及 ID 原样保留；ACR／USPSTF 原有再分发限制继续适用。Fleischner 403 资料不补成虚构全文。 |

PMC 的版本规则是“优先合法公开的出版版 v1，否则其他合法出版版”，是固定快照而非最新版本保证。元数据若发现撤稿则不收录；这是采集日检查，不是永久保证以后不撤稿。CC BY／CC0 接纳范围限正文；图像、补充文件及第三方素材不进入本轮索引。文字标准化、引用号／上下标显式化和分段都明确记录，不把处理后文本称为逐字逐节完全相同的原始字节。

DailyMed 与 NIH 资料保留为本地使用、来源具体再分发条件待审阅；公开 API 不自动授予公司提交说明书或嵌入第三方内容的无条件再分发权。最终混合 evidence.jsonl 因包含不同使用条件，不能整体当作开放数据包发布。PMC 文字子集另存，仍须随来源归属、许可及修改说明一起分发。

### 不接入的候选

- [MedRAG Textbooks 数据卡](https://huggingface.co/datasets/MedRAG/textbooks/raw/main/README.md)：列出教材和片段数，但未提供足以确认每本上游教材可再利用的授权。本轮不以仓库许可替代教材权利。
- [MedRAG StatPearls 数据页](https://huggingface.co/datasets/MedRAG/statpearls)：明确提示不能分发原内容；其旧抓取流程不能当作本项目已获得的使用授权。
- [OpenStax 教材目录／使用说明](https://openstax.org/books/anatomy-and-physiology-2e/pages/index)：当前说明明确限制未经许可的 LLM／生成式 AI 接入，不能只看到 CC 字样就用于本项目。未通过旧镜像绕过其条件，也未擅自联系出版社。

## 固定采样与数据质量

PMC 使用 32 个独立医学标题主题，English、CC BY／CC0、公开日期范围条件，每个主题最多取 600 个候选，按主题轮询去重。查询、返回顺序及响应指纹保存在 research/pmc_search；共得到 18,399 个候选，下载并通过原始许可／正文检查的 10,000 篇进入解析前池。这个池并不等于最终入库论文数：进一步排除新闻、审稿意见、评论等不在研究／综述／病例白名单内的记录；不为了凑 10,000 将其冒充医学研究。主题标签是检索分层标签，不是医生确认的专科覆盖标签。

DailyMed 使用 40 个预先确定的药物词，API 每词第一页最多 100 个记录，按药物轮询并按 setID 去重；有 2,132 个候选，其中 1,000 份通过 human-Rx、setID、产品类别及 XML 校验的记录选为主库。没有声称收齐所有说明书、剂型或厂商。同成分不同产品保留身份；正文精确去重只在同一来源内部做，不把不同产品合成一个标签。

论文正文按摘要／章节段落提取，图、表、参考文献及补充材料不平铺入库；研究结论不升级为指南推荐。SPL 按章节和表格行提取，行列跨度展开后保留原始单元格 XPath 与标题。未可靠解析的数学标记、超过 480 tokens 的完整表格行隔离；长普通段落切分但保留父单元和片段标记，后续证据核验仍需回读父上下文。自动表格结构检查不能替代医学语义复核。

每段索引文本都能按 canonical unit 的字符范围还原；canonical unit 保留原始 XML XPath、来源文件与 SHA-256。对整库独立复核来源指纹、源节点／表格单元、ID、正文字符范围、所有 BGE token 数和 CT 旧数据未改动。正确性范围是数据完整性，不是医学判断或语料已覆盖所有 MIRAGE 答案。

## 相似工作与自己的贡献边界

| 工作 | 实际核验程度 | 对本项目的含义 |
| --- | --- | --- |
| [MedRAG／MIRAGE](https://github.com/gzxiong/MedRAG) | 已核验原论文／官方说明、语料统计和原始 benchmark 快照 | 本项目使用自定义医学语料；遵守 question-only 等原协议后可做完整比较，不能称为复现原始 MedCorp 设置。 |
| [pharma-agent](https://github.com/nikhilreddy00/pharma-agent) | README 描述 LangGraph、多源与引用；没有完成源码和成绩审计 | 多源、LangGraph、药品资料、引用本身已有同类工作；README 的分类和宣传不直接当作事实依据。 |
| [openFDA-rag](https://github.com/kavinmahendran09/openFDA-rag) | README 描述标签规模、混合检索及产品／厂商区分；没有复现审计 | 产品身份和 RRF 不能单独当作新颖贡献。其报告规模与成绩不是本项目实测。 |
| [DailyMed 生物制剂 RAG 论文](https://pubmed.ncbi.nlm.nih.gov/41566090/) | 核验原论文记录，研究使用 DailyMed 生物制剂资料 | 说明书 RAG 已有研究；本项目需用可复现的任务和错误对照证明自己的改造。 |

拟定的用药专项是美国 HIV 抗逆转录病毒治疗与他汀合并用药核对。选它是因为官方指南、产品说明书与研究证据可以形成不同的查证职责，且已有公开资料；不是因为它没有同类工作。当前已取得相关 SPL 与广泛 PMC 原文，但 NIH 本地原文接入受 403 阻碍，专门论文清单、病例题、参考结论和医生复核均未完成，暂不声称该专项可验收。

计划证明的个人贡献是适用条件核验、产品身份匹配、命题到原始证据的位置映射、必要澄清与定向补查，以及文本／图片报告配对和完整对照评测。上述能力在实现并测试前仍是计划，不能把本轮辅助数据脚本写成用户已经实现了 Agentic RAG。后续 Agent 仅在缺证据时选择来源、构造定向查询并有限补查；固定检索已足够的题目不为“有 Agent”增加多轮调用。

## 后续执行

冻结主语料后，先让用户实现 BM25 基线，并为现有向量方法建立这个新语料的可复用向量缓存；两种方法用同一输入做正式对照，再做 RRF。新增文档编码、词项统计和新库评测是必要工作，核心检索／评测函数可复用。原 v2 结果保留，不拿换库前后差异归因于 BM25 或 RRF。

MIRAGE 7,663 题全量、五任务准确率与宏平均、无检索／基础 RAG／改进 RAG、公平配置、成本和逐题 trace 的最终要求不变。上游五套题目的许可审计、评测适配、用药／跨来源题组、多模态配对和临床复核分别跟踪，不能用本轮文档量代替完成状态。OKF 仍按用户决定留到完整专项数据补齐后比较。

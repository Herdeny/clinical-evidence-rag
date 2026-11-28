# 数据是怎样下载、处理和保存的

**2026-11-27状态更新：用户已删除v3，后续检索语料也只采用原作者公开发布、来源及版本可核查的数据集。本页v2／v3采集构建流程仅保留历史，不再作为运行指令或恢复旧库。公开NFCorpus／PubMedQA／MIRAGE材料继续按原来源使用；下一步见[当前数据范围](benchmark_scope.md#2026-11-27检索语料也只采用公开发布的数据集)。**

当前MedRAG/PubMed来源固定为作者提交33da3593d5756bc04c8909f170003c0b14197957，完整1166分片身份在configs/corpus_profiles.json。2026-11-28用户已完成首分片下载，03轮进程7.10s、RSS93224KiB、退出0；前两次退出1记录保留。实际文件data/external/medrag_pubmed/raw/chunk/pubmed23n0001.jsonl为34168949字节，SHA256=6bd70117f34f7293a7e6e017b2abd3bd2fd0a508abfed4d9613d7616d599afca，逐条解析15377记录且ID唯一。原五字段id／title／content／contents为字符串，PMID为正整数，不改写原文件；没有末尾换行导致wc -l为15376，不将其作为记录数。验收保存在results/medrag_pubmed_first_shard_03_validation.json，三轮日志、资源、原件及配置指纹都记录；旧catalog和01准备记录继续保留当时状态。

下一项由用户安装固定兼容候选Pyserini1.3.0，安装缓存放cache/pip；当前发行版版本约束保存在results/pyserini_bm25_install_01_constraints.txt，兼容性待实际导入检查。随后首分片直接进入Lucene，保留原id／contents并通过storeRaw回读原记录，不再改写或重切正文。正式数据范围仍为完整作者清单，首分片仅验证下载与索引资源，不做局部医学效果评测。详见[固定快照及容量](benchmark_scope.md#pubmed固定快照容量与当前下载任务)。

记录日期：2026-11-19；主要原文快照采集于 2026-11-18，CT 快照使用此前已保存版本。本文记录已经做过的流程与本地证据，不表示本轮清理又重新下载了一遍。完整来源、使用条件、指纹与失败记录继续以对应清单为准。

## 数据与代码的位置

2026-11-26公开QA开发材料已由用户亲自准备并通过只读核查：既有scripts.data.prepare_mirage_data以--development取得PubMedQA原作者PQA-L的官方500题CV池，固定提交1cbae8e92f72f20c8d3747cbb3bf5bc53554d997。原1000专家题减去官方500测试ID，实际500开发题；与MIRAGE测试ID、全7663题规范化题干及记录中的参考PMID交集均为0，不宣称语义主题完全隔离。

开发模式保存官方ori_pqal.json、test_ground_truth.json、LICENSE、README.md、preprocess/split_dataset.py到data/external/pubmedqa_development/raw/固定提交/原路径；按官方测试ID从1000专家题中取CV池，不合成题目或重标答案。先核对原测试与固定MIRAGE的ID／问题／标签，再检查CV题干与全MIRAGE不重叠；共同参考PMID另计。转换结果prepared/benchmark.json只保留question／options／answer，原给定context及LONG_ANSWER保留raw而不送模型；文件身份、实际数量与隔离结果写source_manifest.json。

运行命令为python -u -m scripts.data.prepare_mirage_data --development，由用户终端执行，支持单文件字节进度。无--development时沿用原MIRAGE流程；已有开发包只离线复核，不覆盖原件，--verify-only缺包直接退出。完整包在项目内临时目录准备后整体落位。详情见[公开开发池](benchmark_scope.md#官方pubmedqa开发池真实准备已验收)，不能把本项目使用整个CV池的开发验证宣称为原论文十折结果。

转换文件SHA-256=2afd9c360b5b59dd07059743630358f1f480be46650e4f5cb53f1e0756d6ca82，已验收读取器返回500行四列及独立500项gold。标签yes／no／maybe为276／169／55；55.2%是始终选yes的统计基线，尚非模型成绩。真实准备3.95s、RSS74076KiB、退出0，无模型调用；五份原件、manifest和运行日志／资源指纹见results/pubmedqa_development_prepare_01_validation.json。助手仅离线核对；此前_preparation.json仍保留准备时的未执行状态。

2026-11-21新增公开检索基准NFCorpus，位于data/external/nfcorpus。原站ZIP连接失败后采用BEIR官方HF镜像具体提交，保存原始Parquet／TSV／数据卡，再保真转换成标准BEIR目录；没有合成问题或标签。实际3633文档、2590 train／324 dev／323 test查询。下载／复验入口scripts.data.prepare_nfcorpus，独立校验scripts.data.validate_nfcorpus；命令与全部版本指纹见[数据说明](../data/external/nfcorpus/DATA_CARD.md)。未编码或跑分，用户读取适配见[任务契约](nfcorpus_benchmark_task.md)。

2026-11-21新增专项评测目录data/evaluation/ct_v3：原48题保留，新增132题，共120开发／60留出、30家族。它是查询侧数据扩充，不更改主语料或重编码；来源身份、预期行为、必要缺项、引用及复核状态见[数据说明](../data/evaluation/ct_v3/DATA_CARD.md)。全部仍待独立人工复核，当前从review.dev.csv开始。

| 对象 | 本地位置 | 作用 |
| --- | --- | --- |
| CT 原始资料 | data/v2/raw、data/v2/sources.json | 6 份成功快照及官方链接、字节指纹 |
| PMC 候选与原文 | data/v3/research/pmc_search、pmc_candidates.json、raw/pmc | 固定查询、候选顺序、每篇元数据和 XML |
| PMC 下载清单 | data/v3/pmc_raw_manifest.json | 原始选择的 10,000 份合格 XML；不是最终入库数 |
| DailyMed 候选与原文 | data/v3/research/dailymed_search、dailymed_candidates.json、raw/dailymed | API 响应、产品 setID、版本及原始 SPL |
| DailyMed 下载清单 | data/v3/dailymed_raw_manifest.json | 选中的 1,000 份原始产品标签 |
| NIH 失败记录 | data/v3/nih_arv_raw_manifest.json、nih_arv_pdf_manifest.json | 两个网页与三个官方 PDF 的失败状态，成功正文为 0 |
| 统一解析单元 | data/v3/parsed/documents | 正文、章节、XPath、表格单元格和原文指纹 |
| 正式检索输入 | data/v3/evidence.jsonl、sources.json | 783,847 片段、10,840 来源；以下游清单为准 |
| 质量隔离 | data/v3/exclusions.json、quarantine_manifest.json | 未准入文档、单元原因及没有入索引的试解析记录 |
| 外部评测题 | data/external/mirage | 独立保存的 7,663 道题，不混进检索库 |
| 公开QA开发池 | data/external/pubmedqa_development | 官方专家CV池500题；原件与独立开发转换保留，不作MIRAGE最终分数 |
| 可复现处理代码 | scripts/data | 下载、解析、构建、核验模块；逐行中文注释 |

根目录不再散放这些工具。它们仍然用于扩库和复现，因此集中保留，而不是按“只运行过一次”直接丢弃。模块迁移对照和删除的旧自动编译缓存记录在 results/source_maintenance_2026-11-19/maintenance.json。

## 1. CT 资料：官方 HTML 与 PDF 快照

第一批由本地数据准备过程请求公开的官方 URL，使用 requests 发起 GET，检查 HTTP 状态，再保存 response.content 原始字节。下载前后计算 SHA-256，确认写入磁盘的内容与响应一致。电子 PDF 保存原文件，HTML 保存原始页面，不把网页标题当正文。

成功来源为 ACR Lung-RADS 入口页、Lung-RADS v2022 PDF、ACR 偶发结节适宜性页面、USPSTF 肺癌筛查声明以及两个 NCI 专业人员版页面。官方 URL、标题和每个文件的实际指纹保存在 data/v2/sources.json。Fleischner 原文请求返回 403，没有把失败页或项目转述冒充原始全文。

处理方法分开：BeautifulSoup 按站点 DOM 提取正文和章节；HTML 表格保留列标题、完整行及所属 Variant；pypdf 提取 PDF 逐页文字。Lung-RADS 第 2 页 NOTES 按编号分段，保留页码和字符范围。第一页复杂合并表没有被直接平铺成已验证证据；含混单位表达等记录另行隔离。PDF 文本可读不等于表格关系已经恢复，也不表示报告 OCR 已完成。

对应代码：scripts.data.document_parsing、scripts.data.ct_data_pipeline、scripts.data.ct_case_blueprints、scripts.data.validate_ct_data。CT v2 为 241 条候选、238 条准入证据，以及 48 道 AI 初标合成题（32 开发／16 留出）。这些标注不是医生复核结果。

## 2. PMC：从官方 API 找候选，再下载开放 XML

采集使用 [NCBI ESearch](https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi) 和 [PMC 官方 Cloud](https://pmc.ncbi.nlm.nih.gov/tools/pmcaws/)，不抓文章网页。官方桶入口为 https://pmc-oa-opendata.s3.amazonaws.com/。

实际步骤如下：

1. 在 prepare_medical_corpus 中预先定义 32 个医学标题主题；每主题最多选取 600 个候选，限定 English、CC BY／CC0、公开日期范围与未处于 embargo。查询日期范围固定到 2026-11-18，没有读取 MIRAGE 测试题来确定查询。
2. 请求 ESearch 的 db=pmc、retmode=json、retmax=600、sort=pub date，保存完整响应、查询表达式和 SHA-256。按主题轮询去重，得到 18,399 个候选及固定 selection_rank。
3. 对候选 PMCID 请求官方 `metadata/PMC编号.版本.json`。优先符合条件的出版版 v1，否则尝试其他合格出版版本；这是固定快照，不保证是最新版本。
4. 逐篇检查元数据：许可只允许 CC BY／CC0，且 openaccess=true、retracted=false、manuscript=false、historical_ocr=false。来源进入下载池不表示其研究结论已被临床验证。
5. 从元数据的 xml_url 取得官方对象位置，将 s3 地址转为该官方桶的 HTTPS 路径。下载 JATS XML，核对供应方 MD5，并对本地元数据和 XML 分别计算 SHA-256。
6. 核对 XML 根节点、文章标识、许可链接及最低正文条件；保存 metadata.json、article.xml、receipt.json。单文件上限为 12 MiB，连接／读取超时分别 10／30 秒；对配置中的临时错误有限重试，403 不被绕过。
7. 按固定 256 个候选为一批、最多 8 个线程下载，优先级不受网络完成顺序影响。共处理 10,752 个候选，10,042 个通过原始下载检查；选前 10,000 个，42 个 reserve 不自动入主库，另有 710 条未准入或失败记录。
8. 最终构建时进一步按研究／综述／病例等文章类型白名单隔离 164 份新闻、评论或其他类型，实际入库 **9,836 篇论文、480,538 个片段**。

原文池清单见 pmc_raw_manifest.json，拒绝和失败原因见 research/pmc_exclusions.json。许可、作者、PMCID／PMID／DOI 与来源链接跟随 source_id 保留；论文没有被统一标成指南推荐。

## 3. DailyMed：按产品 setID 保存版本化 SPL

使用 [DailyMed 官方 v2 API](https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm)，地址前缀为 `https://dailymed.nlm.nih.gov/dailymed/services/v2/`。

1. 固定 40 个药物检索词，覆盖他汀、抗逆转录病毒及部分常见合并用药。
2. 请求 spls.json，传入 drug_name、human prescription 的 doctype=34391-3、pagesize=100、page=1。每个药物只取 API 第一页，保留官方总量，不能称为收齐所有厂商和剂型。
3. 按词轮询、按 setID 去重得到 2,132 个候选；请求 `spls/{setid}.xml` 取得产品原始标签。
4. 从 XML 核对 setID、versionNumber、标签类型，并读取 approval/code 中标签自报的 NDA／ANDA／BLA 类别；解析成分、活性基团、强度、剂型、产品代码及提交机构。没有把标签自报类别当作已独立通过 Drugs@FDA 核验。
5. 保存按版本命名的 XML 和 receipt.json，核对文件 SHA-256，并记录 API 与 XML 版本是否一致。同成分不同产品保留各自 setID 和版本。
6. 每批 64 个候选、最多 3 个线程。本次 1,024 个候选中 1,002 份通过原始检查，选前 1,000，保留 2 份 reserve 和 22 条排除记录。
7. 正文构建发现 2 份没有可索引章节，最终入库 **998 份说明书、303,071 个片段**。

DailyMed 的 in-use 公司提交标签不保证就是最新 FDA 批准标签。完整说明书的公开再分发条件仍按来源审阅，API 可访问不等于全部文本有统一开放许可。

## 4. NIH：失败也需要保留，不能计入规模

选择 NIH 成人／青少年 ARV 指南的 PI 相互作用与心血管章节作为种子，只允许沿同一官方指南路径继续查找。两个 HTML 请求均返回 HTTP 403；随后测试页面明确提供的完整指南、PI 相互作用和心血管章节三个官方 PDF 链接，也均返回 403。

URL、异常与状态保存在 nih_arv_raw_manifest.json 和 nih_arv_pdf_manifest.json。没有关闭 TLS 检查、用镜像绕过限制或把浏览工具提取文本冒充原始快照。evidence.nih.jsonl 因此为空。用药专项的指南原文接入和参考题仍待完成。

## 5. 从原文到统一 evidence.jsonl

medical_corpus_parsing 负责格式提取，build_medical_corpus 负责组装快照，validate_medical_corpus 独立核验。不同格式有各自适配器，统一输出不等于用一个无结构的提取器处理所有文件。

- JATS 提取摘要和正文段落，保留章节与 XPath；论文图、表和补充材料不平铺入库。
- SPL 提取章节段落和完整表格行；展开 rowspan／colspan，同时保留继承单元格的原始 XPath、表头与分组标题。
- 上下标显式表示；无可靠文本的数学标记或公式图隔离，不静默删除。数字、单位、否定及左右侧属于保真检查对象。
- 普通长段落按本地 BGE tokenizer 切分，保留 unit_id 和字符范围。完整表格行过长时隔离，不拆散条件后当成独立推荐。
- 正文片段最长 480 tokens，含特殊 token；检查不启用截断。这里只用 tokenizer，没有在构建阶段调用嵌入模型。
- 精确去重只在同来源内部做，并保留其他等价位置；不同产品相同文字保留产品身份，同时另报全库独立正文数量。
- 原 CT v2 的 238 条正文和 ID 原样保留。总计 **10,840 来源、783,847 片段、594,483 条不同正文**；不能把片段量当成病例数或独立医学知识数。

每条片段先定位到 parsed 文档内的 canonical unit，再按字符范围还原，最后通过 XPath／页码回到原始快照。完整性检查通过不能代替适用性、命题支持关系或医学正确性验证。

## 6. MIRAGE：独立的外部评测快照

从 [MIRAGE 官方仓库](https://github.com/gzxiong/MIRAGE) 取得 benchmark.json、LICENSE 和 README.md。实际成功下载记录为 2026-11-18；GitHub 提交元数据未取得，revision 明确为 null，改用每个原始文件的 SHA-256 固定快照，没有声称固定了 Git 提交。

本地仅检查字段结构、选项与答案对应关系及数量：MedQA 1,273、MedMCQA 4,183、PubMedQA 500、BioASQ 618、MMLU medical 1,089，总计 7,663。题目与答案没有作为主语料下载查询、训练材料或开发调参内容；检索只允许 question，options 供生成，answer 供评分。

原始仓库声明和五个上游题库的具体使用条件分别处理。当前没有全量对标成绩；下载题库、数据完整性检查和跑完模型是三个不同状态。

## 7. 复现命令

代码迁移后采用模块入口。先进入项目根目录，并使用现有 all-in-rag 环境。下面列的是准备／复现命令，本次清理没有执行重新下载或覆盖冻结语料；需要重建时在独立副本或新的数据版本上操作，保留原清单和指纹。

```bash
cd /home/wzh/clinical-evidence-rag

python -m scripts.data.prepare_medical_corpus --phase discover --per-topic 600
python -m scripts.data.prepare_medical_corpus --phase download --target 10000 --workers 8

python -m scripts.data.prepare_drug_sources --phase discover-labels
python -m scripts.data.prepare_drug_sources --phase download-labels --target 1000
python -m scripts.data.prepare_drug_sources --phase guidelines

python -m scripts.data.build_medical_corpus
python -m scripts.data.validate_medical_corpus

python -m scripts.data.prepare_mirage_data
```

重建既有 CT 数据的入口为：

```bash
python -m scripts.data.ct_data_pipeline
python -m scripts.data.validate_ct_data
```

下载 API 返回的是运行时来源状态，网页和产品版本可能更新；固定 DATE、候选响应、原始快照、版本和指纹，才能解释“当时用了什么”。当前脚本常量记录既有快照日期，不把日后重新联网得到的新内容伪装成原快照；新采集应新建版本并重新核验。

旧路径与整理前源码备份在 results/source_maintenance_2026-11-19/originals；对应历史指纹继续有效。维护记录区分目录迁移所需的导入／ROOT／代码位置更新与纯注释变化，已有 data 和评测结果不改写。

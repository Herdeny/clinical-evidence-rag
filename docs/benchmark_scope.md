# 对标范围与数据规模校准

原协议核对日期：2026-11-17；接入进度更新：2026-11-18。用户明确质疑几百条数据是否达到此前提及的七千余项对标规模。本记录纠正阶段交付与最终对标的混淆，不把新目标写成已实现。

**用户随后明确确认：最终项目必须完成对标。MIRAGE 全量外部评测是正式验收项；只有 CT 小库或少量抽样结果不能标记项目完成。**

## 2026-11-27：检索语料也只采用公开发布的数据集

用户已删除项目自行采集解析的v3语料，后续不恢复；检索语料同样采用原作者公开发布、来源与版本可核查的数据集。原783847片段及采集流程只保留历史，不属于当前已接入语料。撤回基于data/v3/evidence.jsonl的3题真实联调计划，没有执行或创建完整准备记录。独立PubMedQA官方开发池及500题闭卷成绩保留，MIRAGE7663继续为最终评测。

核查[MedRAG作者仓库](https://github.com/gzxiong/MedRAG)及作者HF发布页后，候选如下；这些是发布方统计，不是本项目已下载数量：

| 作者发布语料 | 发布页规模 | 核查与决定 |
| --- | --- | --- |
| [MedRAG/PubMed](https://huggingface.co/datasets/MedRAG/pubmed) | 23898701个标题／摘要片段；仓库约70GB | 已锁定1166分片，实收首分片15377条；完整记录数仍待复验。含PMID；HF约221万行预览不能当完整规模 |
| [MedRAG/Textbooks](https://huggingface.co/datasets/MedRAG/textbooks) | 18部教材、125847段、约212MB | 已有作者切块；卡片未声明明确数据许可，暂不默认采用。原MedQA仓库MIT不能独自证明第三方教材全部权利 |
| [MedRAG/StatPearls](https://huggingface.co/datasets/MedRAG/statpearls) | 作者描述301202段 | 页面明确不分发正文，HF无正文数据，不能当成可直接下载的现成301k语料 |

PubMed数据身份已固定，当前只实收首分片；其他两候选未采用，也不声明无条件商业／再分发许可。[NCBI政策](https://www.ncbi.nlm.nih.gov/home/about/policies/)指出PubMed摘要可能受出版社或作者版权保护；[官方数据下载页](https://pubmed.ncbi.nlm.nih.gov/download/)给出使用条件与下载入口。公开可访问不等于所有内容属于公有领域，不将第三方语料包直接提交GitHub。

当前进入固定分片下载与磁盘索引验证。适配只映射既有id、contents、PMID等字段，保留原文、原始ID与快照身份，不生成医学内容或根据gold筛语料；实际接入后独立复核数量与指纹。

### PubMed固定快照、容量与当前下载任务

作者提交固定为[33da3593d5756bc04c8909f170003c0b14197957](https://huggingface.co/datasets/MedRAG/pubmed/commit/33da3593d5756bc04c8909f170003c0b14197957)，提交于2024-02-27，文件名为PubMed23系列；不称其为当前最新PubMed资料。公开API按该提交核实全部1166个分片，总70007692549字节。完整文件配置在[corpus_profiles.json](../configs/corpus_profiles.json)，清单SHA-256=1a13edbc7993987a5610040ebba0747d6ad15558591c88ffe338362d6031b419；每文件记录原路径、字节数、内容SHA-256与Git blob SHA-1。空文件chunk/pubmed23n0654.jsonl是普通Git对象，按空内容校验，不虚报失败或删除版本事实。数据卡记录数仍是发布方声明，全文实收数量未验证。

| 容量项目 | 当前已核实或计算的量 | 范围 |
| --- | ---: | --- |
| 原始JSONL分片合计 | 65.199744GiB | 作者固定文件元数据；当前仅实收首分片34168949字节 |
| Qwen 4096维FP32向量 | 364.665237GiB | 按发布方23898701条计算的向量本体，不含索引／payload |
| Qwen 4096维FP16向量 | 182.332619GiB | 同上，仅容量估算，精度对结果的影响未实测 |
| 本机可用磁盘 | 约469.56GiB | 本轮观察，会随使用变化 |
| 本机内存 | 总125GiB、可用约107GiB | 本轮观察，不是索引内存实测 |

按[MedRAG作者实现](https://github.com/gzxiong/MedRAG/blob/main/src/utils.py)的BM25路线采用Pyserini／Lucene磁盘索引；原分片已有id／contents，可直接交给[JsonCollection](https://github.com/castorini/pyserini/blob/master/docs/usage-index.md)，storeRaw保存原记录用于回查PMID及证据。不再复制生成另一套70GB全文JSONL，查询时才映射程序所需证据字段。当前Python3.12及Java21与[Pyserini要求](https://github.com/castorini/pyserini#installation)吻合，Pyserini1.3.0已安装并通过JVM接口导入，Qdrant仍未安装；首分片建库及完整回读现已完成，完整库构建与查询成本仍待实测。新Lucene后端须明确记录库版本、分词及BM25参数，不能把其分数和旧rank_bm25混为同一实现的收益。

2026-11-28首分片已由用户下载并验收：chunk/pubmed23n0001.jsonl为34168949字节，SHA256=6bd70117f34f7293a7e6e017b2abd3bd2fd0a508abfed4d9613d7616d599afca；实际15377条、ID全部唯一。id／title／content／contents均为字符串，PMID原为正整数；原文件保持不变。首末ID为pubmed23n0001_0／pubmed23n0001_15376，所有ID后缀与零起始记录序号吻合。文件末尾没有换行，所以wc -l的15376不是JSON记录数。03成功进程7.10s、峰值RSS93224KiB、退出0；01／02失败记录保留。验收results/medrag_pubmed_first_shard_03_validation.json保存三轮原件及内容指纹。历史01准备记录和catalog不改写为事后状态。只验证下载／结构及索引资源，不计算局部医学效果；正式覆盖仍为完整1166分片。当前不能将原分片直接交给仍要求text/source_id/locator的内存RAG入口。

安装前选择固定候选[Pyserini1.3.0](https://pypi.org/project/pyserini/1.3.0/)并检查LuceneSearcher导入。官方发行元数据中1.3.0要求torch>=2.4、transformers>=4.6；[2.4.0元数据](https://pypi.org/pypi/pyserini/2.4.0/json)要求torch>=2.9、transformers>=5，不直接升级本机已实测torch2.6.0+cu126／transformers4.57.6。results/pyserini_release_metadata_01.json记录候选依赖；results/pyserini_bm25_install_01_constraints.txt固定当前已安装发行版，pip必须在这些约束内解析依赖，冲突则停止。该约束只保护当前环境，并非空环境完整锁文件；其后实际安装、JVM导入及首分片索引的验收见下段；完整库仍待实测。安装缓存显式指定cache/pip，日志及资源保留，助手不代装。之后试建首分片索引、确认15377条及storeRaw保真，再由用户在现有retrieve_bm25.py增量实现适配器，复用QA／评分。无须新增根目录运行脚本。

2026-11-28上述安装已由用户完成，LuceneSearcher实际导入成功。314个原有包版本全部未变，新增32个；pip报告中的Pyserini1.3.0原始发行包SHA与PyPI固定值一致。安装进程1:23.87、RSS561504KiB、退出0，资源只包括pip，不包含其后导入；详见results/pyserini_bm25_install_01_validation.json。未代跑模型或建索引，原preparation仍保留准备时状态。

已完成的首分片建库设置：直接读取data/external/medrag_pubmed/raw/chunk/，命令在开始前保护既有索引与输出，确认目录仅有该分片且内容SHA不变。输出cache/indexes/medrag_pubmed/lucene_first_shard_01，采用JsonCollection／DefaultLuceneDocumentGenerator、threads=1、language=en、stemmer=porter，保留默认keepStopwords=false，storeRaw=true；Java初始堆512MiB、最大堆4GiB，这不等于整个进程RSS上限。storeRaw用于回读作者的id／contents／PMID等原记录。BM25的k1／b是后续查询评分参数，不放进建库命令；未来适配器显式记录，与旧rank_bm25基线区分。

本机1.3.0的参数已通过--options核对（--help无效），准备记录results/medrag_pubmed_first_shard_index_01_preparation.json保留完整命令和输入／库指纹及当时prepared状态。用户随后完成真实建库；助手逐条只读核对全部15377条storeRaw记录，与原JSONL五字段及值全部一致，索引和原件未改。首分片仅验证工程链路，尚无局部医学问答成绩；之后优先在原retrieve_bm25.py增量实现磁盘检索，再接原QA入口，完整语料与7663题目标保留。

2026-11-28首分片建库实测通过：indexed15377，unindexable／empty／skipped／errors均0；建库进程1.59s、峰值RSS489696KiB、退出0，包含Python/JVM启动，不含之后回读。索引15文件合计15056284字节，文件分配空间15097856字节；du的15M是舍入展示。全部15377条回读与原记录一致、原件及索引指纹未改，见results/medrag_pubmed_first_shard_index_01_validation.json。没有运行排名查询或医学问答，不用单分片数值线性外推完整库。

当前由用户在已有retrieve_bm25.py增量添加两个函数：load_lucene_bm25(index_path, *, k1=0.9, b=0.4)加载现成索引并设置评分参数、返回LuceneSearcher；retrieve_lucene_bm25(query, k, *, searcher)调用search，按命中原序回读stored raw并映射五字段。Pyserini在加载函数内部导入，避免原rank_bm25使用者仅导入模块就启动JVM。查询保持原字符串，让Lucene分析器处理；不重复调用旧tokenize或排序。输出id=原hit.docid，score=普通float，text=contents，source_id=pubmed:{PMID}，locator=MedRAG/pubmed | {原记录id} | contents，定位到公开数据记录和字段，不编造论文页码。语料revision与索引身份随后写入入口运行配置。此轮默认0.9／0.4来自当前Pyserini，保留旧rank_bm25的1.5／0.75及原结果。边界校验按真实语义：类型错TypeError、空问题及非正k为ValueError；不为测试样式改算法或异常。搜索器由调用方加载一次、跨问题复用并最终关闭；两个函数不加载JSONL全库、不重建索引、不接LLM，不绑定首分片路径。先贴代码审查，再安排用户真实查询联调，后续复用原入口。

用户询问向量数据库后已澄清：Qdrant仍为Dense检索计划，当前未安装；Lucene是公开BM25参照路线。Qdrant官方当前也支持BM25、稀疏及混合查询，不因采用Lucene而将Qdrant排除，也不预设长期双后端必然更好；需用实际效果与维护成本判断。

## 2026-11-26：仅使用可核查的公开benchmark

用户明确要求评测只采用有公开依据、有说服力和可信度的公开benchmark。撤回刚提出的120道自建CT题运行计划；180道自建题及已完成的单例／检索记录仅留作历史，停止据其调参或证明效果。其来源是助手依据固定公开资料编写的病例／问题／行为初标，并非公开benchmark；复核表120行均pending、具名复核者0，来源真实不等于标注独立。未执行的120题准备记录保留其历史状态，不能再当成当前运行指令。

| 当前公开基准 | 可核查来源与实际版本 | 能评估的内容与进度 |
| --- | --- | --- |
| NFCorpus／BEIR | [原作者项目页](https://www.cl.uni-heidelberg.de/statnlpgroup/nfcorpus/)及[BEIR官方数据表](https://github.com/beir-cellar/beir#available-datasets)；本地固定镜像3633文档、324 dev／323 test | 检索相关性、排序及召回；已有dev完整对照，test未运行 |
| MIRAGE医学QA | [ACL 2024论文](https://aclanthology.org/2024.findings-acl.372/)及[官方仓库](https://github.com/gzxiong/MIRAGE)；本地原始快照7663题／五任务 | 医学选择题RAG准确率与成本；五上游公开声明与读取已核查，完整QA适配及全量运行待完成 |

以上官方来源已于2026-11-26重新浏览核实。NFCorpus原站明确相关性等级由网站引用／内部链接／主题关系构造，不能称医生逐题金标准；原站学术用途条件及镜像说明分别保存，不把BEIR软件许可套到数据。MIRAGE仓库有NCBI公共领域声明，但五个组成题库与检索语料仍需分别核查；保留原版本，不能因网页更新静默覆盖本地快照。

后续每个指标都应对应基准原有标注和官方评分协议。NFCorpus的qrels不是证据充分性标签；MIRAGE选择题准确率不能代替追问正确性、引用支持率、报告解析或临床有效性。这些专项能力应先寻找匹配的公开benchmark，核实原始标签、划分、版本与使用条件，覆盖不足就明确列为待评测；不再临时合成题目填补效果证明。无需将评测要求扩展为“检索库只能包含benchmark材料”：业务语料与评测题各自保留来源和许可，但检索基准必须使用配套corpus及ID。

当前已完成下段所列的五上游公开发布声明、MIRAGE角色核查、用户离线读取验收及独立PubMedQA开发池500题无检索实测；下一项复用既有检索构造接入同题RAG对照。不重跑已完成的324 dev，也不对MIRAGE正式测试题反复调参。下面较早保留自建题作产品回归的安排已由本次用户要求取代，原实验历史不改写。

### MIRAGE五个上游的发布条件与划分

核查日期为2026-11-26。各任务题数、来源划分与处理方式依据[MIRAGE官方说明](https://github.com/gzxiong/MIRAGE/blob/main/README.md)及[作者构建脚本](https://github.com/gzxiong/MIRAGE/blob/main/rawdata/build.py)，发布声明逐项查原作者入口，未用第三方合集替代。

| 本地任务键 | MIRAGE题数与来源 | 已找到的官方发布声明 |
| --- | --- | --- |
| mmlu | 1089；六个生物医学科目的test | [MMLU LICENSE](https://github.com/hendrycks/test/blob/master/LICENSE)：MIT |
| medqa | 1273；US四选项test | [MedQA LICENSE](https://github.com/jind11/MedQA/blob/master/LICENSE)：MIT |
| medmcqa | 4183；作者构建脚本读取原dev.json | [MedMCQA LICENSE](https://github.com/medmcqa/medmcqa/blob/main/LICENSE.md)：MIT |
| pubmedqa | 500；专家标注test，移除给定context | [PubMedQA LICENSE](https://github.com/pubmedqa/pubmedqa/blob/master/LICENSE)：MIT |
| bioasq | 618；2019—2023 Task B test的yes/no，移除给定snippets | [BioASQ官方数据条件](https://participants-area.bioasq.org/datasets/)：CC BY 2.5，注明来源并引用；原站下载需注册 |

本次完成的是官方公开声明和当前本地科研评测用途的核查，保留各原作者归属和许可说明；不把仓库声明扩成所有第三方原题、摘要或教材文本的无条件再分发许可，不将这些全文打包进GitHub。MIRAGE本身的NCBI声明不能替代上表。MedMCQA原仓库README的Valid／Test题数表与MIRAGE作者的dev文件映射有出入；本项目按MIRAGE固定快照和作者build.py定义对标，不根据表头自行改划分。

五部分在本项目均作最终评测，不因上游名叫dev就拿来调prompt。模型联调另用已固定且经重叠核查的PubMedQA官方CV池，实际准备结果见下节；MIRAGE测试材料不用于联调。只读格式核验不构成模型调参。保持零样本与question-only retrieval；options只用于生成，answer只用于评分。PubMedQA／BioASQ快照额外保存的PMID来自对应／参考文献，不能作为检索条件或直接补上下文。现有两套公开基准仍不能代证所有报告追问／引用／多模态能力。

助手只读复核三份原件SHA、五任务容器／字段／数量、选项与答案关系；未打印本地试题或答案、未运行模型、未下载新数据。审计保存在本地results/mirage_upstream_review_01.json，原source_manifest.json及其采集时pending状态不改写，Git revision未知仍为null，不把本次网页核查冒充重新固定提交。每任务排序对齐[官方QADataset](https://github.com/gzxiong/MIRAGE/blob/main/src/utils.py)的字符串题号排序。后续答题解析需另行声明失败处理；原工具解析失败回退A的行为不应无说明地沿用，失败计入分母，各方法同口径。

### MIRAGE读取函数：已验收

文件benchmark_data.py，新增load_mirage_dataset(benchmark_path, *, task=None)，已有两个函数保持。使用标准库json、已有Path与pandas，不增加脚本或依赖。benchmark_path显式指向固定raw/sha256-snapshot/benchmark.json；task为None读取全部，或精确选择五个任务键之一；这是原始评测集合读取，不伪造split=dev。

输入结构是外层任务字典→任务内原题号字典→题目记录，不是JSONL。当前实现用json.loads(benchmark_path.read_text(encoding="utf-8"))读取；task为None选原任务顺序，否则只选该任务。每任务按sorted(任务内字典)遍历字符串题号，不能先转int；全局id取“任务名:原题号”，例如medqa:0000。每行只选id／task／query／options，query保持原question字符串、options保持原字典，不拼成检索表达；标准答案另存gold_answers[id]=原answer。PMID和其他gold材料不进入题目表，原始文件保持完整。

返回questions_df与gold_answers两个对象。前者四列按id、task、query、options排列，后者为id到选项键的字典，双方ID集合相同且唯一；它不是检索qrels，没有文档相关性分数。检查任务存在、问题非空、options为非空字典且键／文本有效、answer属于options；空白检查不改写原问题或选项。不强制某种异常名称，不把题数硬编码进业务读取器。原模型／凭证／缓存／检索与评分均不在本函数中。

2026-11-26离线验收通过：全量shape=(7663,4)，gold为7663项字典，五单任务分别与全量子集内容及顺序一致；逐字段核对原问题／选项／标准答案、官方排序和题号前导零。ID唯一且双方集合相同，题目表无answer／PMID，空及未知任务名正确拒绝，三份原始文件指纹未变。旧两函数AST相同，既有BEIR的9项测试通过。只输出结构和计数，没有展示题干／答案、运行模型或下载数据；结果不能表述为问答或临床效果成绩。验证results/mirage_loader_validation_01.json对应源码SHA=81507dda72bb063ffabdca5c13cb2367e091c88005009ba8f3b5571c7742acd2，review_01／02保留历史，助手未修改用户核心。

### 官方PubMedQA开发池：真实准备已验收

开发材料选择[PubMedQA原作者发布的PQA-L](https://pubmedqa.github.io/)，不使用PQA-A人工生成部分。原作者[划分代码](https://github.com/pubmedqa/pubmedqa/blob/master/preprocess/split_dataset.py)说明1000专家题分为500测试和500交叉验证池；[公开测试标签](https://github.com/pubmedqa/pubmedqa/blob/master/data/test_ground_truth.json)给出测试ID。本项目取官方1000题减去官方500测试ID，保持原专家答案，使用整个官方CV池作开发材料；不把这一步说成原论文十折实验或MIRAGE最终成绩。

原作者仓库MIT声明沿用此前核查，固定提交1cbae8e92f72f20c8d3747cbb3bf5bc53554d997，不跟随master更新。已有数据准备脚本新增--development，下载ori_pqal.json、test_ground_truth.json、LICENSE、README及split_dataset.py，保留字节和SHA。转换为单任务MIRAGE结构，只保留question／三选项／原专家标签对应的答案键，question不拼给定摘要，后续复用已验收读取器，答案留评分侧。

准备时先要求官方500测试ID、题目及标签与当前固定MIRAGE的PubMedQA部分一致，再要求CV池与全部7663题的大小写／连续空白规范化题干没有重叠；规范化仅用于审计，实际输入不改。遇到冲突即停止，不静默删题或补题。共同参考论文PMID单独统计，不把同论文自动等同同题，也不宣称主题隔离。输出固定到data/external/pubmedqa_development，原MIRAGE原件不动。

助手准备阶段只用临时IO夹具与内存下载响应完成9项辅助检查，未形成合成评测数据。用户现已亲自执行python -u -m scripts.data.prepare_mirage_data --development，真实核对为1000专家题／500官方测试／500开发；与MIRAGE测试ID、全部规范化题干及记录中的参考PMID交集均为0。已验收读取器返回(500,4)及500项gold；标签yes 276、no 169、maybe 55，始终选yes的Accuracy为55.2%。后续开发报告同时提供Accuracy、macro-F1与失败计数，macro-F1参考[原作者评分脚本](https://github.com/pubmedqa/pubmedqa/blob/master/evaluation.py)；这不是新增模型成绩。

prepared/benchmark.json的SHA-256为2afd9c360b5b59dd07059743630358f1f480be46650e4f5cb53f1e0756d6ca82。真实运行3.95s、RSS74076KiB、退出0，无模型调用；原文件、manifest、用户日志和资源已只读核对，记录results/pubmedqa_development_prepare_01_validation.json。此前_preparation.json仍保留准备时未执行状态，不事后改写。已有包只离线核验，--verify-only缺包不会下载。

### 选择题生成核心：已完成单题联调

本单元的生成核心为qa_core.py，不新增单题项目入口。现有query_rewrite.py负责改写，evidence_review.py明确只核验不回答，benchmark_data.py负责保真读取；生成有独立职责，因此新增这一个核心模块有必要。具体代码由用户写，助手只审查，不代跑真实调用。

2026-11-27当前实现检查点：用户已完成输出类、输入整理、两模式消息和响应处理，源码SHA=5029c01bde71ccf4426ee18014a2958e46709a816711455303a0a9f5873c97ca。results/qa_core_validation_01.json记录14项本地检查：四类有效回答成功、七类无效输出拒绝、未知用量保留None、两种调用层异常原样传播；输入与原响应未改、已知用量与元数据保留，每次只调用一次替身。首次辅助比较对异常深拷贝产生误报，修正辅助方法后通过，核心未改。此前消息构造SHA=f68582d7f34250fee61dd970ed02c6eded21ebd74c82e57c7bfc78830e1d4dea和输入整理SHA=591b4e8bf03bb0e3f9e0b67fbf9ff2796d7212c082ff44d0ef8fb20c27653d97作为历史记录。没有真实API调用、永久新测试脚本或助手核心修改，软件验收不代表医学效果。

用户已运行pubmedqa_closed_book_smoke_1_01并通过只读核查：现有deepseek_flash、公开开发池第一题、closed_book；返回一条有效结构化回答、无引用，481＋125＝606 tokens，调用947.077ms、整进程1.71s、RSS179624KiB、退出0，实际模型标识与profile一致。日志与逐题JSON相同，材料／配置／读取器指纹一致；核心只删除两条无用导入，SHA=a4aa6725fd2311d8d5c7abab21fb59048925e0675a8f99bc8a51b7d75ad1718d，函数／类AST与14项软件验收版本相同。results/pubmedqa_closed_book_smoke_1_01_validation.json保留原三文件SHA及核查边界，原件和准备记录不覆盖，助手未重跑API。不验证回答中的医学断言，不计算单题准确率；全500开发及MIRAGE7663最终对标仍待完成。

**先固定答题语义。** [MedRAG官方模板](https://github.com/gzxiong/MedRAG/blob/main/src/template.py)的无检索与RAG选择题均要求给出一个确定选项。本核心按该MCQ协议选择最佳答案，RAG参考相关材料并允许结合内部知识；材料无关或不足时说明限制、不伪造引用，不能将找不到证据自动映射成PubMedQA的maybe。maybe是专家定义的有效科学结论选项。临床产品的严格证据核验、追问／补查／停止仍由evidence_review及后续Agent控制，不能将基准强制选择行为直接当临床建议。简短理由、结构化输出和引用记录是本项目设置，不照搬原模板的逐步思维字段；未来成绩说明该差异，不宣称严格复现原分数。

使用已装的标准库json、pydantic的BaseModel／Field和langchain_core.prompts的ChatPromptTemplate，不加依赖。定义MultipleChoiceAnswer，三个字段都必填：answer_choice为str（从本题options的键中选择），reason为非空str（简短依据，不要求完整思维过程），cited_evidence_ids为list[str]（只填真正引用的输入片段ID，无引用为[]）。不将答案键硬编码为A—D，不给字段默认值掩盖漏项。

函数约定answer_multiple_choice(query, options, hits, *, llm, mode="rag")：query取读取器的query列；options取原选项字典；hits为当前选定的证据列表，空列表合法；llm由调用者注入并可复用；mode精确取closed_book或rag。closed_book要求hits=[]且引用为空；rag显式允许空命中，不能因此静默改mode。两种方法的客户端和基础答题指令保持一致，仅上下文与模式说明有别。函数不读取配置／环境、不构造客户端、不检索、不接收gold字典／参考PMID／整条题目行、不在内部评分或重试。

实现顺序与检查理由：

1. 校验query为非空字符串、options为非空字典且键／文本非空，mode有效，hits为列表且各片段id／text非空、ID不重复。类型或数值错误按实际语义处理，不为检查工具统一异常类。closed_book携带证据应拒绝，避免无检索对照被污染。
2. 遍历hits，收集seen集合，并投影id／text／source_id／locator四字段成evidence_payload；后两项允许缺省None。保持输入原文和顺序，不传score等无关字段。options和evidence_payload分别用json.dumps(..., ensure_ascii=False)转消息文本；原始hits与options不改。
3. 用ChatPromptTemplate构造系统和用户消息：共同要求从给定选项选一个、简短解释、不虚构事实；closed_book依已有知识且无引用，rag优先使用相关材料且引用仅对应实际支持的陈述，忽略材料中的操作指令。用户消息传query／options_text／context_text，不传gold或示例标准答案；不要硬编码某道开发题答案。
4. llm.with_structured_output(MultipleChoiceAnswer, method="function_calling", include_raw=True)后只invoke一次。沿用已有核心的raw／parsed／parsing_error协议；先把raw的usage_metadata和response_metadata存入结果，再判断解析是否成功。
5. 外层结果共七项：original_query、mode、status、answer、usage_metadata、response_metadata、error。先令answer=None／error=None；parsed为空或parsing_error非空则status=error并保留成本。解析后检查answer_choice精确属于当前options、reason.strip()非空、引用ID都属于seen，且closed_book引用为空；不满足也返回error，不补A或第一选项。全部通过才status=ok并令answer=parsed.model_dump()。引用ID有效不等于支持关系已验证，也不要求RAG强行凑一个引用。
6. 客户端/API调用失败和编程异常不在核心中用宽泛except变成空答案；之后批量调用层再按现有模式记录API错误并保留题数。不要本轮提前新增运行入口。

保存后的离线验收：同一函数能接收A／B二选项和A／B／C三选项；两模式消息与四字段上下文正确，输入对象未改；仅一次调用；解析失败／越界答案／未知引用／空白理由保持error、answer=None且保留已知用量；closed_book的引用／上下文规则成立；有效结果不含gold。空RAG命中仍为rag，既不强制maybe也不伪造引用。只用内存假客户端检查软件协议，不新增合成benchmark题或证明医学准确率，不运行真实模型。通过后再接实际PubMedQA开发池的用户单题／批量运行；全500是开发比较，全7663仍是最终目标。

### 离线QA评分：已验收

在已有benchmark_eval.py增量添加evaluate_multiple_choice(questions_df, gold_answers, answer_records)，不新增脚本、不改变原BEIR评分。只读取调用者传入的内存对象，不检索或调用模型。questions_df四列id／task／query／options；gold_answers为id到标准答案键；answer_records直接采用本次保存结构，外层query_id、内层result.status与result.answer.answer_choice。返回逐题eval_df和summary，后续无检索／BM25／Dense／RRF共用。

先检查题目表非空、ID唯一、gold键集合一致；逐条建立record_map并拒绝重复，最后要求记录题号集合与本次参评表完全一致。只保存一题的联调文件不能拿去当500题完整结果，API失败也需批量层保存错误行后计错。按questions_df.iterrows()遍历，核对result.original_query与该题query相同，状态只允许ok／error。ok取实际answer_choice并检查属于本题options，error的predicted_answer=None、correct=0；不删除失败行，不改成默认A，不重复检查reason或引用支持。逐题表六列query_id／task／gold_answer／predicted_answer／status／correct，其中correct是0或1。

summary为query_count、ok_count、error_count、accuracy、per_task、macro_accuracy。全局accuracy对所有行的correct求均值；按task分组保存每组题数和准确率，macro_accuracy对参评子任务准确率等权平均。全MIRAGE正式报告必须包含五个任务，不能将只包含一个任务的平均称全量成绩。

PubMedQA另报告macro_f1，依据[原作者评分脚本](https://github.com/pubmedqa/pubmedqa/blob/master/evaluation.py)；MIRAGE任务间准确率等权平均依据[作者评测代码](https://github.com/gzxiong/MIRAGE/blob/main/src/evaluate.py)，本轮于2026-11-27重核。使用已安装scikit-learn 1.9.1的f1_score，按该任务options键并集排序生成label_to_index；gold用映射转整数、失败预测用-1，labels显式只列合法非负编号，average="macro"、zero_division=0。失败仍记入相应真实类漏判，不把错误符号当第四类。此失败政策与结构化解析差异须说明，不能称原脚本原样复现。数学验收例真值0／1／2、预测0／0／-1：Accuracy=1/3、Macro-F1=2/9，仅软件算术例而非新增医学benchmark。

2026-11-27用户已实现并通过16项本地软件检查，源码SHA=8be77919b64aa3ea0e1ea2998ddfb7fa033b2d0ac1e0f957b334d99166b380f8。失败分母、状态计数、题号乱序对齐、任务等权平均、全对／全错、动态键、无PubMedQA分组及各种ID／状态／文本错配均符合约定；摘要可JSON序列化、输入未改，原三个函数AST相同。结果在results/qa_scoring_validation_01.json，不是医学模型成绩；没有API调用或新建测试脚本，助手未修改核心。500开发和7663最终生成／评分尚未运行。

### 批量问答编排：已验收

在原qa_core.py添加iter_question_answers(questions_df, *, llm, mode="rag", retrieve_fn=None, k=32)，不新建批量脚本。复用answer_multiple_choice和统一retrieve_fn(query, k)接口；具体方法与客户端／索引由调用者准备。函数逐题yield记录，供入口收到一题即保存一行JSONL；不接收gold、不写文件或重做评分。k=32参考[MedRAG官方用法](https://github.com/gzxiong/MedRAG#usage)示例，仅参考设置，适用性及输入token预算待实际RAG开发核查。

先检查题目表非空、ID唯一、mode有效；rag要求可调用retrieve_fn和正整数k，closed_book不调用检索。循环用tqdm／iterrows；每题无检索给hits=[]及retrieve_latency_ms=None，RAG仅用query检索一次并计时，空命中仍为RAG。之后调用单题核心一次，共享外部llm；只捕获生成调用的openai.APIError并保留错误题，未知用量和响应元数据设None，不填0；核心已经返回的结构化错误保留其已知用量。编程／检索异常不吞掉，qa_latency_ms对成功或API异常均计时。

外层逐题record七字段query_id／task／options／hits／retrieve_latency_ms／qa_latency_ms／result；result是原单题七字段返回，已验收评分函数可直接读取。每轮for末尾yield record，让外层保存后再继续，不在内部返回全量列表。2026-11-27用户已实现并通过19项本地检查，源码SHA=5d023db042f06898d3f56ec6b141494a13e8fddb07d331c2739fe3e435ff1870；单题AST未改，记录results/qa_batch_validation_01.json。仅本地替身验证，未产生真实批量成绩或API调用。

### 当前用户任务：增量接入QA入口

助手已在原retrieval_results_io.py增量提供save_qa_results(records, *, score_fn, config, run_name, result_dir)，原四个保存辅助AST未改。三份输出沿用_results.jsonl／_summary.json／_run.json，开始消费生成器前防覆盖；每题写入并flush，完整生成后调用用户评分回调，摘要保存metrics／generation／latency／per_query。中断或异常保留已有响应并记录运行状态，原异常不改；全未知用量不填0、未执行检索耗时为None。11项临时IO检查通过，源码SHA=1743d719e46618955958c954fbdcb05986907d2a8cc11c54ea1d34f0325154bf，记录results/qa_stream_io_validation_01.json；没有新项目脚本、API调用或模型成绩。

用户在现有run_benchmark_eval.py新增main_qa(config_dir, benchmark_path, *, model_name, mode, task=None, limit=None, run_name=None, retrieve_fn=None, retrieval_config=None, k=32)。用现有读取器、可选task／limit筛选题目，gold按实际id取子集；保留可用／选中数量和完整题号，run_name显式优先或qa_{task or 'all'}_{mode}_{model_name}，无时间戳。默认名称在入口函数内处理，CLI原样传run_name。公开profile来自config_dir，沿现有dotenv和客户端构造，每批一个客户端；检索器及公开配置从参数传入，避免重写三种算法。

records直接保留iter_question_answers返回的生成器；score_fn用partial(evaluate_multiple_choice, questions_df, gold_answers)绑定前两个参数，交给save_qa_results在完整记录后评分。不要提前list(records)，文件保护与逐题保存要先于迭代。config记录输入／源码／公开profile指纹、实际选择及模式／k／检索配置，不保存对象或密钥；三输出先防覆盖，返回完整保存摘要。

2026-11-27用户已实现main_qa并通过8组本地联结检查，入口源码SHA=ff9d253d13b882b4479713a721289973d1cb4d7358a132d46400b652e1fd7777。覆盖有限子集、完整500题假响应遍历、默认名、task=None、API失败保留并继续、RAG空结果注入、三文件防覆盖及非法limit；使用真实核心／读取／评分／保存，dotenv和客户端边界被替换，未读取密钥或调用真实API。原BEIR main及CLI未变，助手未改核心；报告results/qa_entry_validation_01.json没有模拟医学成绩，真实500题仍未运行。

当前CLI已增加--benchmark（Path，默认None）、--model-name（默认deepseek_flash）、--task（默认None）、--limit（int，默认None）。--model-name为用户明确选择的QA参数名，其值对应公开配置键，Python形参同为model_name，保存字段为"profile_name": model_name；不增加--profile别名，也不擅改其他入口。提供benchmark时调用main_qa，直接传args.run_name，由QA函数决定其默认名，只打印metrics、generation、latency。未提供benchmark时进入原BEIR调用，默认名称也由main内部处理。--config沿用且不加别名，不新增脚本；--mode当前只开放closed_book，正式RAG命令行及检索器装配下一步在同文件复用现有实现。

2026-11-27完整CLI通过7组本地联结检查，源码SHA=6852a22313263d57fcd865c10f0031767eb29afa46adba67e13fb978717b4b7c。包括完整500题假响应、产物防覆盖、指定配置／名称／limit、直接函数复用默认名、参数解析、BEIR命名保护及旧检索逻辑范围核对；未读密钥、未调用真实模型或API，报告results/qa_cli_validation_01.json。随后准备pubmedqa_closed_book_dev_500_01：公开开发池全部500题、deepseek_flash、不传limit，先同步GitHub再由用户执行。准备记录及完整命令在results/pubmedqa_closed_book_dev_500_01_preparation.json，保留准备时的prepared_not_executed历史状态；用户现已完成真实运行，成绩与核验见下节，不把此前软件检查当作模型效果。

<a id="pubmedqa-closed-book-dev"></a>

### PubMedQA 500题无检索开发基线：已实测

2026-11-27用户亲自运行pubmedqa_closed_book_dev_500_01，使用已固定的公开专家CV池全部500题，deepseek_flash配置、temperature=0、max_tokens=2048、max_retries=0、thinking禁用；模型只接收问题、选项及共用／无检索提示，不提供原作者context或gold。实际响应模型标识均为deepseek-flash，500次结束原因为tool_calls，与结构化输出一致。题库SHA、公开profile及五个源码SHA与准备记录一致，运行入口SHA=6852a22313263d57fcd865c10f0031767eb29afa46adba67e13fb978717b4b7c。

| 指标 | 真实结果 |
| --- | ---: |
| 题数／答对／答错 | 500／305／195 |
| Accuracy | 0.610000 |
| PubMedQA Macro-F1 | 0.4707726705 |
| 接口及结构化结果成功／失败 | 500／0 |
| 输入／输出／总tokens | 238083／58430／296513 |
| QA调用均值／中位数 | 944.837307ms／915.937935ms |
| 整进程墙钟时间 | 7:53.74 |
| 最大常驻内存 | 254624KiB，约248.66MiB |

用量500条完整已知、未知0；cache_read=128000已包含在输入token内，不重复相加，也不据token总量臆测费用。检索未执行，retrieve_latency_ms统计count=0、mean／median=None。运行状态completed、保存500条、进程退出0；日志与摘要一致。仅一个子任务时macro_accuracy=accuracy，不是三类召回平均。

| 类别 | 真实数量 | 预测数量 | 答对数量 | 该类Recall | 该类F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| yes | 276 | 339 | 217 | 0.786232 | 0.705691 |
| no | 169 | 137 | 81 | 0.479290 | 0.529412 |
| maybe | 55 | 24 | 7 | 0.127273 | 0.177215 |

模型选择yes共339次，超过真实yes的276题；maybe中38题被选为yes、10题选为no。该类最弱，Macro-F1对三类等权，因此低于整体准确率。maybe是公开任务的合法标准类别，不是系统拒答。始终选yes的同池统计基线为55.2%，本轮高5.8个百分点；不能据此证明RAG收益、临床有效性或全部错题的成因。本轮不是MIRAGE最终测试，也不宣称原论文十折实验复现。

助手只读核对五份原始运行文件与准备记录，并复用用户评分／独立混淆矩阵公式复算全部题目、用量与计时，未重新调用模型或评判全部reason医学内容。results/pubmedqa_closed_book_dev_500_01_validation.json保存原件指纹、完整混淆矩阵和独立统计，原件及prepared历史状态未改。

### 下一用户任务：复用检索器构造

同一500题接入RAG前，在现有run_benchmark_eval.py添加build_retriever(method, corpus_df, *, config_dir, cache_dir, evidence_path, embedding_model="bge_small")，返回retrieve_fn和方法配置字典。corpus_df为已规范的语料表，evidence_path为其实际语料文件，用于已有缓存身份；它不是问题题库路径。函数只构建现有Dense／BM25／RRF及相应元数据，不接收gold、运行QA、读取问题／qrels或保存评测。当前参数名称按用户后续统一的embedding_model记录。

将当前main第54—142行构造段移入该函数，局部config={"retrieval_method": method}，保留现有模型配置、缓存调用及三种方法参数，最后return retrieve_fn, config。原第57行evidence_path=data_dir/'corpus.jsonl'改由调用者传入，通用函数不依赖BEIR的data_dir。原main保留BEIR读取、公共config及评测保存，用一次build_retriever调用取得两项，再config.update(retrieval_config)。先由用户完成此抽取，再以本地替身核对；随后在同文件接QA语料加载与RAG分支，不复制三套构造或新增入口脚本。模型选择继续由已有config_embedding_model参数控制，真实新运行仍由用户执行。

2026-11-27该抽取已由用户实现并通过8组本地检查，当前源码SHA=20c7eae58cb25c1cf4f2a2a6c74fccf38c7ddb78b108dbea50e04a491a2cb3bd。三种真实检索核心配假Embedding与小型格式文本可调用，来源字段及方法配置保留；真实单组／改写两组读取、评测、保存各三种方法通过，缓存参数／配置选择／归一化记录正确；错误选择和已有产物提前拒绝。QA及CLI的AST未变，助手未修改核心或运行真实模型／API／GPU；临时文件已清理，记录results/shared_retriever_validation_01.json，不是医学效果或全库性能验证。

### 下一用户任务：接入QA的RAG分支

该接入已在原run_benchmark_eval.py实现，不新增入口或复制检索算法。main_qa追加method="bm25"、evidence_path=None、cache_dir=None、embedding_model="bge_small"四个仅关键字参数；保留原retrieve_fn／retrieval_config供已经准备好索引的调用者使用。共享构造在main_qa的输出保护与题目筛选之后、LLM配置与客户端创建之前执行，避免先建大索引再发现本轮输出冲突。Embedding参数按用户当前选择统一为embedding_model，历史config_embedding_model记录不覆写。

mode=rag时先检查k为正整数。retrieve_fn为None时，要求evidence_path，使用pandas.read_json(path, lines=True, dtype=False)读取规范证据表，检查非空、四个共同字段id／text／source_id／locator、ID唯一；cache_dir未给时取root/cache/embeddings。调用build_retriever取得回调与方法配置，补充evidence_path绝对路径字符串、evidence_sha256、evidence_count、cache_path、corpus_text="text"；大语料SHA用已有hashlib分块读取，每块1MiB，不能read_bytes一次额外分配约1.2GB。传入了现成回调时检查可调用及非空配置字典，不重复读取文件或建库。闭卷跳过该段，原输出中的检索配置和k继续为None。

CLI已增加--evidences（Path、默认None）和--k（int、默认32），--mode开放closed_book及rag，Embedding选择统一为--embedding-model；--model-name、--config和可选run_name保持。2026-11-27通过10组本地联结检查，源码SHA=968bd4b0fd00c72360bb1edab3aaece0a80abe077144d9174d5998ded5f58ff3：三方法从真实CLI走完假生成／实际评分／保存，引用与来源字段、缓存和文件身份正确，闭卷、外部回调、错误输入／API异常、输出保护及原BEIR路径均通过。报告results/qa_rag_entry_validation_01.json，无真实模型／API／GPU调用或医学效果成绩，助手未改核心，临时文件已清理。首次替身错误返回ndarray，核对真实LangChain返回list[float]后仅修替身，未为检查工具修改用户算法或保存层。真实运行等待本页开头的公开语料接入，v3联调计划已撤回。

## 2026-11-24 当前实测进度

NFCorpus BM25、Dense与RRF dev已运行并独立核验：3633文档／324查询，BM25的nDCG@10／Recall@100为0.265738／0.205678、平均查询2.839ms；Dense为0.327186／0.315082、23.262ms；RRF为0.312468／0.300335、35.872ms。文档缓存完整并由RRF复用，324题融合顺序和分数独立核对一致。见[开发集对照](nfcorpus_retrieval_baselines.md)。当前Dense四指标均值最高，下一步固定其Top100候选测试重排；尚无重排成绩。官方test未运行，MIRAGE全量7663问答对标仍是最终验收要求。以下11月21日及更早的“尚无成绩／待下载”状态按历史日期理解。

## 2026-11-21 来源澄清和当前优先级

公开检索基准已经实际接入数据：NFCorpus官方HF镜像固定两份提交，实际3633文档、2590 train／324 dev／323 test查询；原始及规范文件保留，结构和身份复验通过。当前用户实现[读取适配](nfcorpus_benchmark_task.md)，还没有检索或模型成绩。下面“仅候选、未下载”的叙述为本次交付前的核查记录；实际来源、转换与使用条件见[数据说明](../data/external/nfcorpus/DATA_CARD.md)。

当前CT专项题为180道（120开发／60留出、30家族），全部由助手生成与初标，尚无独立人工或医生复核。原文快照真实不等于题目是公开基准；同一作者产生的家族隔离留出仍不能替代外部测试。保留其用于检查目的、适用条件、必要澄清与引用的产品回归，停止通过继续扩合成题承担主要效果证明。

公共基准接入应提前。MIRAGE原题已下载但尚无完整问答评分适配或模型成绩；其选择题答案不能直接转换为本项目v3证据ID的Recall标签。当前纯检索可以使用带配套corpus、queries、qrels的公开检索基准；最终问答继续按原计划跑MIRAGE7663。分别报告检索排序、最终答案及产品行为，不能用一类分数替代另两类。

已经核查的检索候选为[BEIR NFCorpus](https://github.com/beir-cellar/beir#available-datasets)：官方BEIR表列323测试查询、约3.6K文档，支持train／dev／test。其[原始网站](https://www.cl.uni-heidelberg.de/statnlpgroup/nfcorpus/)统计的是完整版，规模不同；qrels来自网站链接自动构造，不是医生逐条标注。原站明确学术用途条件，其他用途需另核，不能套用BEIR软件的Apache许可。当前仅完成候选来源核查，未下载或评测；不能把该qrels映射到任意自定义医学库，必须保留其配套文档与ID。

以下按日期保留阶段记录，旧“专项仍48题／没有向量成绩”不代表当前状态。项目主语料和向量已存在，公共基准成绩仍为0。

## 最终验收要求

| 项目 | 必须交付的结果 | 当前状态 |
| --- | --- | --- |
| 基准与语料接入 | 固定 MIRAGE 原始 7,663 题和五个子任务的版本；核实数据条件；准备医学检索语料并记录规模、来源与使用条件 | 原题、五上游公开声明、读取及独立500题开发池已核查；QA适配与实际检索覆盖待完成，第三方全文不打包再发布 |
| 公平对照 | 在固定模型与版本、数据和输入协议下，全量运行无检索、基础 RAG、改进 RAG；基础 RAG 使用公开可复现的参考设置，明确它与 MedRAG 的关系 | 尚未运行 |
| 协议遵守 | 零样本；检索只使用问题，不使用选项；生成可接收选项；答案和给定 gold 支持上下文保留在评测侧 | 待实现 |
| 完整成绩 | 五个子任务分别报告准确率及其宏平均；同时报告实际调用数、tokens、费用、延迟与失败情况；失败题计入分母，不删除难题 | 尚无成绩 |
| 可复现交付 | 保存配置、源文件与题目 ID、检索结果、回答、评分和逐题 trace；提供运行入口、成本估算和最终报告 | 尚未实现 |
| 专项产品验证 | 报告指南匹配、用药与跨来源证据核对、多模态输入；分别验证引用、适用条件及必要澄清 | 匹配专项标注的公开benchmark待选，旧CT合成题记录仅保留历史 |

MIRAGE 测试题不用于反复调整提示词或检索规则；联调使用独立开发材料。预算估算和小规模联调不替代最终全量结果。只有下载题目、建立索引或完成抽样，都不能算完成该验收项。

验收要求可复现、公平且完整的实测比较；性能收益由实验决定，如实报告。采用不同语料或模型时准确标注设置，不以不相同条件下的分数宣称复现或超过原论文。原始论文的大量模型配置与本项目选定的一组主要对照实验分别描述。

## 原工作与本项目当前状态

[MIRAGE 官方仓库](https://github.com/gzxiong/MIRAGE) 和 [ACL 2024 原论文](https://aclanthology.org/2024.findings-acl.372/) 的 7,663 是评测问题数，来自五个医学问答数据集，不是文档或证据块数。它采用零样本、多选题、RAG 和 question-only retrieval；检索输入不包含选项。PubMedQA 与 BioASQ 的给定支持上下文在该基准中移除，不能再把这些 gold 直接送入检索或生成。

[MedRAG 官方仓库的语料统计](https://github.com/gzxiong/MedRAG#corpus) 将原始文档数与切块数分开报告。例如 Textbooks 为 18 份原始文档、约 125,800 个片段，四种来源组合 MedCorp 为约 54,200,000 个片段。这是原工作报告的统计，不是本项目已下载、可无条件复制或必须完整复现的规模。

此前 CT 阶段有 238 条检索输入、48 道 AI 初标题、24 个家族；其中 32 题开发、16 题留出。2026-11-18 已扩充并固定自定义 v3 主语料：10,840 来源、783,847 片段，包含 9,836 篇论文、998 份产品说明书及原 CT 238 条。数据位置与 token 完整性检查通过，但没有模型成绩。专项题仍是原 48 道，不能把新增文档或片段冒充新增病例，更不能用片段量对应 7,663 道问题。

48 题尚未经独立人工或医生复核；数据规模、覆盖范围和标注独立性都需继续建设。2026-11-16 的“整批完成”仅指本轮 CT v2 准备，不能写成整个项目最终数据建设或 MIRAGE 对标已经完成。

## 后续对标安排：待实现

1. 保留当前 CT v2 小规模基线，继续建设报告条件、药品说明书、医学文献和多模态的专项评测，独立复核标签与证据。这一组验证逐条引用、适用性和澄清，不能由通用选择题准确率代替。
2. 将 MIRAGE 全量对标列为最终必须完成的验收项。使用原始题目，而非由模型合成七千题充当同一基准；正式调用前先核对数据条件、语料覆盖及调用成本。联调与全量验收分开，不以小样本替代完整成绩。
3. 外部基准需要覆盖相应医学主题的检索语料。原 300–1000 个精核证据块的规划不能作为系统总索引规模的上限，也不证明大规模检索性能。另行核实公开医学语料的来源、授权和资源消耗，区分专项精核集与更大检索集合。
4. 同一模型、语料、题目和预算下比较无检索、基础 RAG 和改进 RAG；若只采用外部语料子集或不同模型，明确写为自定义设置，不能宣称复现原论文成绩。正式对标时遵守原始协议并报告各子任务成绩。

截至 2026-11-18，MIRAGE 原题及 LICENSE／README 已下载并完成 SHA-256、schema 与五任务 7,663 题检查；未展示题目答案，未运行模型。自定义医学主语料 v3 已冻结并通过完整性验证，完整评测适配及五套上游题库使用条件审计仍未完成，没有全量对标成绩。v3 是本项目自定义语料，不能称为原始 MedRAG／MedCorp 语料的严格复现。

历史记录（2026-11-17，当时未成功）：已编写 [原始数据准备脚本](../scripts/data/prepare_mirage_data.py)，包含固定快照、结构和数量检查及原始许可保留。运行时 GitHub API 域名解析失败，获准联网后的 API 和官方 raw 地址均出现 TLS unexpected EOF；原题尚未落盘，没有 source_manifest，状态保存在 [准备记录](../results/mirage_preparation_status.json)。不能将脚本存在写成基准接入完成。CT v2 的 [完整检索工作单元](ct_v2_baseline_task.md) 继续推进，评分核心由用户实现。

2026-11-18 重试成功：[来源与指纹](../data/external/mirage/source_manifest.json)已落盘，Git revision 未取得而明确留空，三个原始文件按 SHA-256 固定。自定义主语料现已选定、接入并冻结；五套题库使用条件、完整评测适配及对标实测尚未完成。接下来在 v3 同一输入上做向量／BM25／RRF 正式对照，详见[扩充节点](data_expansion_milestones.md)。

## 数据条件边界

[MIRAGE 仓库 LICENSE](https://raw.githubusercontent.com/gzxiong/MIRAGE/main/LICENSE) 提供 NCBI 公共领域声明及引用要求。五个组成数据集、外部医学语料及其上游材料的具体条件仍需分别核对，不能将仓库声明自动扩展为所有第三方文本的无条件分发许可。本轮仅核实官方说明，没有公开发布、调用付费模型或向论文作者发送消息。

# 对标范围与数据规模校准

原协议核对日期：2026-11-17；接入进度更新：2026-11-18。用户明确质疑几百条数据是否达到此前提及的七千余项对标规模。本记录纠正阶段交付与最终对标的混淆，不把新目标写成已实现。

**用户随后明确确认：最终项目必须完成对标。MIRAGE 全量外部评测是正式验收项；只有 CT 小库或少量抽样结果不能标记项目完成。**

## 2026-11-26：仅使用可核查的公开benchmark

用户明确要求评测只采用有公开依据、有说服力和可信度的公开benchmark。撤回刚提出的120道自建CT题运行计划；180道自建题及已完成的单例／检索记录仅留作历史，停止据其调参或证明效果。其来源是助手依据固定公开资料编写的病例／问题／行为初标，并非公开benchmark；复核表120行均pending、具名复核者0，来源真实不等于标注独立。未执行的120题准备记录保留其历史状态，不能再当成当前运行指令。

| 当前公开基准 | 可核查来源与实际版本 | 能评估的内容与进度 |
| --- | --- | --- |
| NFCorpus／BEIR | [原作者项目页](https://www.cl.uni-heidelberg.de/statnlpgroup/nfcorpus/)及[BEIR官方数据表](https://github.com/beir-cellar/beir#available-datasets)；本地固定镜像3633文档、324 dev／323 test | 检索相关性、排序及召回；已有dev完整对照，test未运行 |
| MIRAGE医学QA | [ACL 2024论文](https://aclanthology.org/2024.findings-acl.372/)及[官方仓库](https://github.com/gzxiong/MIRAGE)；本地原始快照7663题／五任务 | 医学选择题RAG准确率与成本；全量是既定目标，QA适配及上游使用条件核查待完成 |

以上官方来源已于2026-11-26重新浏览核实。NFCorpus原站明确相关性等级由网站引用／内部链接／主题关系构造，不能称医生逐题金标准；原站学术用途条件及镜像说明分别保存，不把BEIR软件许可套到数据。MIRAGE仓库有NCBI公共领域声明，但五个组成题库与检索语料仍需分别核查；保留原版本，不能因网页更新静默覆盖本地快照。

后续每个指标都应对应基准原有标注和官方评分协议。NFCorpus的qrels不是证据充分性标签；MIRAGE选择题准确率不能代替追问正确性、引用支持率、报告解析或临床有效性。这些专项能力应先寻找匹配的公开benchmark，核实原始标签、划分、版本与使用条件，覆盖不足就明确列为待评测；不再临时合成题目填补效果证明。无需将评测要求扩展为“检索库只能包含benchmark材料”：业务语料与评测题各自保留来源和许可，但检索基准必须使用配套corpus及ID。

当前已完成下段所列的五上游公开发布声明和MIRAGE角色核查；下一项由用户在已有benchmark_data.py增量实现离线读取，不重跑已完成的324 dev，也不对MIRAGE正式测试题反复调参。下面较早保留自建题作产品回归的安排已由本次用户要求取代，原实验历史不改写。

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

五部分在本项目均作最终评测，不因上游名叫dev就拿来调prompt。后续模型联调须另取官方train／dev材料，固定来源并与MIRAGE做题目重叠检查后使用；当前未下载或创建该开发包。只读格式核验不构成模型调参。保持零样本与question-only retrieval；options只用于生成，answer只用于评分。PubMedQA／BioASQ快照额外保存的PMID来自对应／参考文献，不能作为检索条件或直接补上下文。现有两套公开基准仍不能代证所有报告追问／引用／多模态能力。

助手只读复核三份原件SHA、五任务容器／字段／数量、选项与答案关系；未打印本地试题或答案、未运行模型、未下载新数据。审计保存在本地results/mirage_upstream_review_01.json，原source_manifest.json及其采集时pending状态不改写，Git revision未知仍为null，不把本次网页核查冒充重新固定提交。每任务排序对齐[官方QADataset](https://github.com/gzxiong/MIRAGE/blob/main/src/utils.py)的字符串题号排序。后续答题解析需另行声明失败处理；原工具解析失败回退A的行为不应无说明地沿用，失败计入分母，各方法同口径。

### 当前用户任务：在已有模块添加MIRAGE读取函数

文件benchmark_data.py，新增load_mirage_dataset(benchmark_path, *, task=None)，已有两个函数保持。使用标准库json、已有Path与pandas，不增加脚本或依赖。benchmark_path显式指向固定raw/sha256-snapshot/benchmark.json；task为None读取全部，或精确选择五个任务键之一；这是原始评测集合读取，不伪造split=dev。

输入结构是外层任务字典→任务内原题号字典→题目记录，不是JSONL。用json.load读一次；task为None选原任务顺序，否则只选该任务。每任务按sorted(任务内字典)遍历字符串题号，不能先转int；全局id取“任务名:原题号”，例如medqa:0000。每行只选id／task／query／options，query保持原question字符串、options保持原字典，不拼成检索表达；标准答案另存gold_answers[id]=原answer。PMID和其他gold材料不进入题目表，原始文件保持完整。

返回questions_df与gold_answers两个对象。前者四列按id、task、query、options排列，后者为id到选项键的字典，双方ID集合相同且唯一；它不是检索qrels，没有文档相关性分数。检查任务存在、问题非空、options为非空字典且键／文本有效、answer属于options；空白检查不改写原问题或选项。不强制某种异常名称，不把题数硬编码进业务读取器。原模型／凭证／缓存／检索与评分均不在本函数中。

验收只输出结构和计数：全量shape=(7663,4)，gold数7663，分任务数与上表一致；task=pubmedqa时500行；id唯一且双方集合相同，题目表无answer／PMID，原始文件字节未改。只看列名、数量和一致性，不head打印最终题干或答案。此函数尚未实现，用户贴代码和输出后再审；助手不提前代写核心或调用模型。

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
| 基准与语料接入 | 固定 MIRAGE 原始 7,663 题和五个子任务的版本；核实数据条件；准备医学检索语料并记录规模、来源与使用条件 | 原题、五上游公开声明及角色已核查；QA适配、独立开发包与实际检索覆盖待完成，第三方全文不打包再发布 |
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

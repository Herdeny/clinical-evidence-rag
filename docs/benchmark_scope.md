# 对标范围与数据规模校准

原协议核对日期：2026-11-17；接入进度更新：2026-11-18。用户明确质疑几百条数据是否达到此前提及的七千余项对标规模。本记录纠正阶段交付与最终对标的混淆，不把新目标写成已实现。

**用户随后明确确认：最终项目必须完成对标。MIRAGE 全量外部评测是正式验收项；只有 CT 小库或少量抽样结果不能标记项目完成。**

## 2026-11-26：仅使用可核查的公开benchmark

用户明确要求评测只采用有公开依据、有说服力和可信度的公开benchmark。撤回刚提出的120道自建CT题运行计划；180道自建题及已完成的单例／检索记录仅留作历史，停止据其调参或证明效果。其来源是助手依据固定公开资料编写的病例／问题／行为初标，并非公开benchmark；复核表120行均pending、具名复核者0，来源真实不等于标注独立。未执行的120题准备记录保留其历史状态，不能再当成当前运行指令。

| 当前公开基准 | 可核查来源与实际版本 | 能评估的内容与进度 |
| --- | --- | --- |
| NFCorpus／BEIR | [原作者项目页](https://www.cl.uni-heidelberg.de/statnlpgroup/nfcorpus/)及[BEIR官方数据表](https://github.com/beir-cellar/beir#available-datasets)；本地固定镜像3633文档、324 dev／323 test | 检索相关性、排序及召回；已有dev完整对照，test未运行 |
| MIRAGE医学QA | [ACL 2024论文](https://aclanthology.org/2024.findings-acl.372/)及[官方仓库](https://github.com/gzxiong/MIRAGE)；本地原始快照7663题／五任务 | 医学选择题RAG准确率与成本；五上游公开声明与读取已核查，完整QA适配及全量运行待完成 |

以上官方来源已于2026-11-26重新浏览核实。NFCorpus原站明确相关性等级由网站引用／内部链接／主题关系构造，不能称医生逐题金标准；原站学术用途条件及镜像说明分别保存，不把BEIR软件许可套到数据。MIRAGE仓库有NCBI公共领域声明，但五个组成题库与检索语料仍需分别核查；保留原版本，不能因网页更新静默覆盖本地快照。

后续每个指标都应对应基准原有标注和官方评分协议。NFCorpus的qrels不是证据充分性标签；MIRAGE选择题准确率不能代替追问正确性、引用支持率、报告解析或临床有效性。这些专项能力应先寻找匹配的公开benchmark，核实原始标签、划分、版本与使用条件，覆盖不足就明确列为待评测；不再临时合成题目填补效果证明。无需将评测要求扩展为“检索库只能包含benchmark材料”：业务语料与评测题各自保留来源和许可，但检索基准必须使用配套corpus及ID。

当前已完成下段所列的五上游公开发布声明、MIRAGE角色核查、用户离线读取验收及独立PubMedQA开发池准备；下一项由用户编写选择题生成核心。不重跑已完成的324 dev，也不对MIRAGE正式测试题反复调参。下面较早保留自建题作产品回归的安排已由本次用户要求取代，原实验历史不改写。

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

### 当前用户任务：离线QA评分

在已有benchmark_eval.py增量添加evaluate_multiple_choice(questions_df, gold_answers, answer_records)，不新增脚本、不改变原BEIR评分。只读取调用者传入的内存对象，不检索或调用模型。questions_df四列id／task／query／options；gold_answers为id到标准答案键；answer_records直接采用本次保存结构，外层query_id、内层result.status与result.answer.answer_choice。返回逐题eval_df和summary，后续无检索／BM25／Dense／RRF共用。

先检查题目表非空、ID唯一、gold键集合一致；逐条建立record_map并拒绝重复，最后要求记录题号集合与本次参评表完全一致。只保存一题的联调文件不能拿去当500题完整结果，API失败也需批量层保存错误行后计错。按questions_df.iterrows()遍历，核对result.original_query与该题query相同，状态只允许ok／error。ok取实际answer_choice并检查属于本题options，error的predicted_answer=None、correct=0；不删除失败行，不改成默认A，不重复检查reason或引用支持。逐题表六列query_id／task／gold_answer／predicted_answer／status／correct，其中correct是0或1。

summary为query_count、ok_count、error_count、accuracy、per_task、macro_accuracy。全局accuracy对所有行的correct求均值；按task分组保存每组题数和准确率，macro_accuracy对参评子任务准确率等权平均。全MIRAGE正式报告必须包含五个任务，不能将只包含一个任务的平均称全量成绩。

PubMedQA另报告macro_f1，依据[原作者评分脚本](https://github.com/pubmedqa/pubmedqa/blob/master/evaluation.py)；MIRAGE任务间准确率等权平均依据[作者评测代码](https://github.com/gzxiong/MIRAGE/blob/main/src/evaluate.py)，本轮于2026-11-27重核。使用已安装scikit-learn 1.9.1的f1_score，按该任务options键并集排序生成label_to_index；gold用映射转整数、失败预测用-1，labels显式只列合法非负编号，average="macro"、zero_division=0。失败仍记入相应真实类漏判，不把错误符号当第四类。此失败政策与结构化解析差异须说明，不能称原脚本原样复现。数学验收例真值0／1／2、预测0／0／-1：Accuracy=1/3、Macro-F1=2/9，仅软件算术例而非新增医学benchmark。

当前函数尚未实现，核心仍由用户写；聊天具体说明record_map构造、逐题字段／失败分支、groupby与F1参数。保存后先离线检查，再接用户批量生成，不提前运行500次API。

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

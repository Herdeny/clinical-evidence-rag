# 项目背景、进度与后续任务交接

最后核对：2026-11-24。本文用于在后续对话、上下文压缩或换助手时恢复项目。内容依据用户的项目要求、当前代码、保存的输出及结果文件整理。该日期是交接更新日，不覆盖来源此前的核验日期。

**接手时先读本文件，再检查当前代码和用户最新提交的输出。不要把规划当成实现，不要从 B0 重新教起。用户后续明确指令优先于本文，代码与输出的变化需要及时更新到本文。**

## 1. 当前应从哪里继续

**2026-11-24最新：NFCorpus BM25、Dense、RRF dev均已实测并核验，当前Dense四指标均值最高。** 最新run_name=nfcorpus_rrf_dev_01，用户终端执行提交3b51482dc73a600915d4ab59afe134579deeb1d1，3633文档／324题／每题100命中。RRF的nDCG@10=0.312468299806529、Recall@10=0.1406747396163073、nDCG@100=0.28137851892188376、Recall@100=0.3003347087049922，平均查询35.87232415430876ms、中位35.28364700105158ms；整进程16.10s、峰值进程RSS1431336KiB、退出0。Dense相应四指标0.32718602689711807／0.14901094123636222／0.2972834613889674／0.31508239684562706，平均23.261722024713375ms；BM25主指标0.2657379994665381／0.20567783238375933、平均2.839211916625011ms。完整报告docs/nfcorpus_retrieval_baselines.md，不把开发集成绩当临床结论或MIRAGE成绩。

**RRF核验与负结果：** 两路各Top100、常量60、最终100；从归档两路排名独立计算融合，324题全部ID／顺序／分数一致。原qrels四指标重评分、缓存及12个保护文件全部通过，run_audit为complete_integrity_validated。cache_hit=true、initial_completed_rows=3633，未重做文档编码；助手未加载模型或重新检索。相对Dense的nDCG@10逐题RRF高94／Dense高125／相同105；Recall@100高66／低105／相同153，均值分别下降0.014717727090589092、0.014747688140634832。RRF至少命中一篇的279题多于Dense的278题，不代表平均Recall更高，加入相关文档的收益小于移出文档的损失。详见ENG-022，保留全部原始负结果。

**Dense缓存与核验：** fingerprint=4aa389bc2d522a2fc285b6065a93e38de9516d6dfa7265c1e614a4761109c3f0，3633×384、float32只读矩阵，array SHA31c71ff295e2baba90d4ba5b0e334b9fa9d50a40bb445c63a0abc2e32d651f61，有序id/text SHAbcea3c417ac8c0535088df2a31f2c46020fb6fa36cdc69f25c15169d434c3f3e，全部有限且归一化。首次cache_hit=false／initial_completed_rows=0。离线核验工具已扩展为分块检查缓存文件、形状、源文本身份与范数，并检查此前基线产物保护；324题四指标重算一致，输入及9份源码与回执一致，BM25原5产物未变。Dense_validation.json通过、run_audit为complete_integrity_validated；助手没有重新检索、编码或加载模型。

**逐题比较：** nDCG@10 Dense高147／BM25高76／相同101；Recall@100 Dense高184／BM25高52／相同88。Top100两路均命中相关文档231题、仅BM25命中7、仅Dense命中47、两路均零39。均值绝对差分别0.06144802743057999和0.10940456446186769，保留results/nfcorpus_bm25_vs_dense_dev_01_comparison.json。候选互补只支持继续验证RRF，不是融合已取得收益。

**当前任务：用户编写rerank_core.py的rerank(query,hits,k,*,reranker,batch_size=16)。** RRF归档已推送cacf463。用户进一步明确正式项目不默认偏向轻量模型，具体长期约束见13.10。撤回MiniLM直接定为成品模型的决定；重新查阅官方来源后，Qwen3-Reranker-4B为优先效果候选（revision22e683669bc0f0bd69640a1354a6d0aebcfeede5），BGE-reranker-v2-m3为对照（revision953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e），均Apache-2.0。发布方同候选设置的英文汇总分数支持优先验证4B，不能当作本项目医学成绩。两者未下载、初始化或运行；本地sentence-transformers5.7.0／transformers4.57.6及CrossEncoder相关支持已检查。完整接口和来源见docs/reranking_task.md；本轮纯函数契约不变，模型注入、一次predict全部句对、复制元数据、原score留作retrieval_score、新score保留原始模型相关性分数、按(-score,id)排序。核心由用户写，助手随后用假打分器验收，不提前启动GPU。

**用户下一次返回代码或“好了”：** 重读rerank_core.py实际文件并检查上述完整契约；不能沿用旧版代码诊断，不代写核心。函数通过并提交推送后再接公开基准入口dense_rerank，助手先扩展保存辅助与配置支持，再交用户接线。固定Dense Top100→重排100→返回100，只改排序，Recall@100应不变；观察nDCG@10／Recall@10／成本，真实模型运行由用户终端执行。不重复运行三条旧基线，不同时调RRF，test与MIRAGE未运行，Notebook删除及.vscode继续保留本地。

**2026-11-24：benchmark_eval.py验收完成。** 实际验收源码SHAae8ba1240f9fcc9ca79dfbe029c2ecaa305c1887af7c7a8222aae67244254f6d，tests/test_benchmark_eval.py原7方法全部通过，pytrec-eval-terrier==0.5.11。覆盖原query不变、每题max(ks)只检索一次、结果行与真实float分数保留、空命中计0且保留分母、相关等级排序、自定义K、非法输入／命中拒绝及逐题异常定位。两题临时验收的四指标为[1,0]且均值0.5；这是可解释的小样本验收，绝非NFCorpus成绩。结果results/benchmark_eval_validation.json及2026-11-24_revision5，之前失败快照保留。核心由用户完成，助手未改。

**同步与接续：** 评测节点777d784及保存辅助b185eeb已推送origin/main。save_beir_results(result_df,run,*,config,run_name,result_dir)只校验／汇总／保存，不编码检索或重新逐题评分；新增6项和旧保存6项共12项通过，记录results/beir_results_io_validation.json。三类产物为_results.jsonl、_run.json、_summary.json，含全部题目的均值、耗时范围、方法层配置、评分包版本与三输入SHA；拒绝丢题、矛盾run、非法数值和同名覆盖。入口、BM25归档及Dense归档也已推送，最新已同步节点3b51482；本轮继续归档RRF，保持每个完成节点提交后再进入下一步的约定。

**已验收的运行入口：** run_benchmark_eval.py已完成main(method,data_dir,split,cache_dir,run_name)及CLI，复用load_beir_dataset／evaluate_beir_retrieval与已存在save_beir_results，不修改CT入口。三方法复用当前Dense、BM25、RRF；BM25仅CPU构建一次，Dense沿用冻结的LangChain模型和缓存，RRF每路100／常量60。common config提供dataset_name／data_dir／split／retrieval_method／ks=[10,100]，保留原query模板及标题拼接规则；模型参数保留在dense／bm25／rrf子配置。完整参数、各阶段调用和验收见docs/nfcorpus_benchmark_task.md。三种方法dev真实结果均已核验，入口尚未支持dense_rerank。核验辅助现在从历史源码快照严格验证执行身份，另报当前工作区是否仍一致，避免后续开发让历史运行无法复核。数据／缓存／本地结果与.vscode保持原策略。

**概念注释提醒：** from exc明确设置直接原因；省略它时Python也会保留隐式异常上下文。用户注释中“不写from就有两个异常”的表述需要按此理解，不作为功能验收的新阻断。RuntimeError与from exc此前已经解释，异常链已用真实用户函数验证。

**2026-11-23最新：NFCorpus读取适配验收完成。** benchmark_data.py源码SHA46419011dd285ad6eeaf3fd35481acc0a43e946c5c3ead15dd3922b9ffd18833，tests/test_benchmark_data.py原9方法全部通过。真实dev为3633文档、324查询、324个qrels查询键、11385标签，整数等级1／2、原正文和行序保留；通用目录、前导零、多对多标签、划分隔离、既定异常输入均通过。结果results/benchmark_data_validation.json及2026-11-23_revision6。有效any(布尔Series)写法保留，读取核心由用户完成；不继续要求改已验收代码。

**已完成的评测接口：** benchmark_eval.py实现evaluate_beir_retrieval(queries_df, qrels, retrieve_fn, ks=(10,100))，返回逐题eval_df与run（query→doc→真实float检索分数）。直接使用原query，每题调用一次retrieve_fn(query,max(ks))；perf_counter只计检索调用，支持tqdm进度。评分用BEIR同口径pytrec_eval.RelevanceEvaluator及ndcg_cut／recall，按全部输入查询保留行，空hits计0；不传qrels给检索器。完整列、输入约束和无模型验收例见docs/nfcorpus_benchmark_task.md。用户核心、保存辅助及三方法运行入口均已完成；下一步重排继续复用这些接口。

**依赖和边界：** 2026-11-23核查评分API时未安装；2026-11-24已确认用户安装pytrec-eval-terrier==0.5.11，导入名pytrec_eval，先用临时标签与run核验返回结构，再通过用户函数验收及三方法真实开发集实测。主库矩阵继续保留，NFCorpus使用自身文档缓存。当前test和MIRAGE不做模型调用。

### 以下为上一版真实dev已通过的历史结果

2026-11-23 revision3源码SHAcbd761aa89af69408a7f6ef22730f1b3bcf1a712e5e055e3153d03fb2317ac6b曾通过真实dev主流程：3633文档、324查询、324个qrels查询键、11385标签、整数等级1／2、原文与行序保留。当时其余8方法尚未通过；该结论只绑定上一版，不能冒充当前源码结果。

### 以下为之前字典键错误版本的检查

**2026-11-23最新读取复验：** 当前benchmark_data.py源码SHA86f38bc8ebf1fbda1ce018fe8f99de4bf4b8df29decb3872e878c5c849fc893c，语法通过且真实dev调用可以返回。查询字段text→query、isin(qrels)成员筛选和返回顺序corpus／queries／qrels均已按契约修正，不再要求改这些已正确的写法。实际数量3633文档／0查询／1个qrels外层键／1条标签，外层键恰为字面字符串query-id，原因是第29行两层赋值键与第31行外层赋值键写成列名字面量，而非当前qrel行的列值。if条件使用qrel['query-id']和else内层qrel['corpus-id']已经正确，可保留if／else组织，只修正取键；前面标签被反复覆盖，继而导致查询筛空。

**当前指导和验收：** 用小例子解释列名字符串与qrel['query-id']实际值的区别，可先取query_id和document_id局部变量，再让用户自行修订字典创建／更新，不代写整个循环。之前的CSV ID字符串／grade整数dtype、split／文件／重复／悬空／空输入校验及locator数据集身份仍未完成，不因概念解释跳过。原9方法契约检查复跑后尚未通过；结果results/benchmark_data_validation.json及2026-11-23_revision2快照绑定本次源码。多项失败受同一字典键问题影响，不宣称9个独立缺陷。无模型或检索，真实数据只用dev，用户核心未由助手修改。

### 以下为之前读取版本的检查

**2026-11-22最新读取适配检查：** benchmark_data.py已改为显式定位corpus、queries及单个split的qrels，语法通过；当前源码SHA63149fcb3ca842ee0e8c2acc2f9e650bcc2ac561cf205c530174f173f083dc2b。真实dev调用在第27行访问qrels['id']报KeyError，尚未得到返回结果。助手新增tests/test_benchmark_data.py，9个方法含多个子用例检查真实dev、通用小目录、前导零、多对多标签、等级、划分隔离、重复和悬空ID、空输入及缺文件；当前全部尚未通过，12条失败记录不代表12个独立代码问题，多项被同一个KeyError阻断。无模型或检索，用户核心未改。最新results/benchmark_data_validation.json；旧骨架诊断initial和当前源码版revision1记录均保留。

**本轮集中修订任务：** (1)qrels的官方列为query-id／corpus-id／score；筛选queries要用查询ID集合的isin成员判断，不能将3237条查询与11385条query-document标签逐行==，并把查询text改名query。(2)标签TSV按ID字符串／score整数读取，删除round，整理成query→doc→整数grade字典；源表可称qrels_df以区别最终qrels。(3)按既定顺序返回corpus_df、queries_df、qrels。(4)补split枚举、必需文件存在、空正文／空标签、重复ID／pair和悬空引用检查；locator的dataset根据输入数据集目录身份生成，避免换BEIR目录仍标nfcorpus。静态问题一次列齐，不让用户每次只修一个小错误；后续仍重读用户最新文件。

**代码注释中的dtype问题已本地验证：** 当前pandas对JSONL字符串ID“001”默认推断为数值1，dtype=False保留字符串“001”。该参数关闭按列自动推断转换，不是把全部列都转成字符串；TSV的两个ID列和score仍需在read_csv中显式指定dtype。本轮未把基础语法／字段错误加入工程面试记录。

### 以下为之前的骨架版本检查

**2026-11-22当前读取适配尚未完成：** 用户已创建benchmark_data.py，实际保存版本SHA为5fc118ace7def45cf22f145b0957d1bd2ab3d2ef7de90c45943bf6ba8cd17643。文件仅导入pandas／Path、定义函数并rglob扫描，末尾if／elif为空，没有读取、转换、qrels或return；ast语法检查在第9行失败（第7行if之后没有语句）。results/benchmark_data_validation.json明确记录incomplete_source_not_executable，没有动态验收、模型或检索。助手没有改用户核心。

**当前指导：** BEIR是固定目录约定，应直接定位corpus.jsonl、queries.jsonl和qrels/{split}.tsv，再分别读取与转换；rglob按后缀扫描不能区分两份JSONL用途，也会扫进其他划分。固定文件名属于格式契约，不牺牲换目录／换BEIR数据集的通用性。Path.suffix返回.tsv／.jsonl这种带点后缀，但当前不需要依赖后缀扫描。用户继续完成既定load_beir_dataset契约后再用真实dev和小目录验收。若用户再次说“好了”，必须重读最新文件，不能沿用本次未完成版本结论。不要将这些基础语法与读取问题记作工程面试案例。

**2026-11-21当前：公开检索基准NFCorpus已准备完成，等用户写读取适配。** BEIR官方HF镜像固定正文仓库提交b5026a0e96e8a7ac4f95f482a596389289d46269和标签仓库提交a451b3b26d3ae1358f259c1a3a4dd61fcea35a65。实际3633文档、3237查询，train2590／dev324／test323；qrels分别110575／11385／12334条，train等级1，dev／test等级1和2。原始Parquet／TSV／数据卡在data/external/nfcorpus/raw/huggingface，规范文件在prepared/nfcorpus；只转换容器，保留官方字段值、ID、划分和相关性等级，没有生成新题。原站ZIP请求超时或TLS中断，采用官方镜像；不能宣称原ZIP MD5已校验。来源source_manifest.json、数据说明DATA_CARD.md、独立核验results/nfcorpus_data_validation.json均已落盘。镜像数据卡CC BY-SA4.0与原站学术用途说明分别保存，当前本地学术实验，不推断统一商业再分发许可。

**当前唯一用户实现任务：** 项目根目录新建benchmark_data.py，实现load_beir_dataset(data_dir,*,split="dev")，返回corpus_df／queries_df／qrels；准确契约、库、API与验收见docs/nfcorpus_benchmark_task.md。corpus保留title和body，检索text拼标题与正文，补source_id／locator以兼容现有hit；queries只取所选划分且使用原query，不套CT模板；qrels保留query→doc→整数等级。dev验收3633／324／324及11385相关性记录，并查重和拒绝悬空ID。用户核心未由助手创建或改写；下一次“好了”重读实际benchmark_data.py后用真实dev及临时BEIR小目录验收，不替用户写核心，也不重复从B0教读一行。

**已经实测的数据边界和后续：** prepare_nfcorpus.py可下载／离线复验；validate_nfcorpus.py独立核验文件SHA、Parquet值保真、TSV字节一致、ID关系、官方划分及23份旧产物／核心模块保护，全部通过。仅本地tokenizer计数：完整标题＋正文最长2377，330篇超过512，dev查询含BGE前缀最长29；保留全文，后续BGE512截断要明确入配置。没有嵌入、检索或benchmark分数。NFCorpus需要自己3633文档的小缓存，不能复用医学主库矩阵；旧783847行矩阵保持。后续公开评测nDCG@10／Recall@100，RRF每路候选预设100和常量60；当前评分包未安装，等读取适配通过再接官方指标及运行入口。正式test留到方法固定后，MIRAGE7663仍为最终问答验收，自建CT仅作产品回归。

### 以下为公开基准接入前的决策记录

**最新来源澄清与评测优先级：** 用户询问为何不用现成benchmark及开发题是否都由助手生成。已逐条核对annotation：当前120开发／60留出全部为assistant_generated_synthetic、draft_requires_human_review，包括继承的48题；6份来源快照是真实材料，合成的是病例描述、问题、预期行为与gold标注。这套数据用于产品场景回归，不能作为独立外部评测或临床金标准；按家族留出也不能消除同一生成作者的偏差。停止继续扩充合成题作为主评测，公共基准接入应提前，原MIRAGE7663最终验收不变。

**公共基准核对结果：** MIRAGE官方是最终医学问答评测，包含question／options／answer，不提供本项目自定义v3片段的穷尽相关性gold，不能直接用选项答案算现有Recall。当前已下载原题，尚无完整问答适配／对标成绩。针对当前Dense／BM25／RRF的纯检索评测，已查BEIR官方与NFCorpus原站：BEIR NFCorpus列323测试查询、约3.6K文档，带train／dev／test及qrels；原始完整版统计不同，不能混用。原站说明相关性由网站链接自动构建，学术用途可用，不是医生逐条判断，也不能自动推断为任意商业使用授权。该基准只是经过来源核查的接入候选，本轮未下载、编码或跑分；采用时使用其配套语料／ID／划分，不能套到本项目783847片段上评分。官方入口https://github.com/beir-cellar/beir、https://www.cl.uni-heidelberg.de/statnlpgroup/nfcorpus/、https://github.com/gzxiong/MIRAGE。

**接续方向：** 优先接通公开基准的数据与评分接口，公开检索基准验证排序，MIRAGE验证最终问答，自建CT题保留作适用性／澄清／引用回归。用户继续实现核心，助手处理来源核验与辅助准备。已有代码、主库及向量全部保留；以下“先跑120合成题作为主要对照”的安排仅作为可选产品回归，不作为公开效果证明。正式MIRAGE测试集不转成日常调参开发集。

**当前推进与职责更正：** 用户询问为何被安排逐题复核；助手确认把用户填CSV设为继续开发的前置任务不合适。数据准备、来源回查及辅助核验继续由助手负责，用户主要编写和解释检索／生成／Agent核心代码。独立人工／医生复核是标注质量状态，用户勾选accepted不能自动构成临床金标准。撤销“用户先完成三题或整批复核才能继续”的教学任务，保留全部待复核标记，不降低医学有效性结论的证据要求。

**下一步实际任务：** 在固定的120道开发题草稿上做Dense／BM25／RRF探索性检索对照，明确标注AI初标、未经独立复核；用同一题集、语料、查询模板及既定参数，复用完整文档向量。由用户在可见终端运行run_retrieval_eval.py，分别指定--method、--cases data/evaluation/ct_v3/cases.dev.jsonl及独立--run-name medical_v3_{method}_ct_eval_v3_draft_dev。原32题成绩保持；60道留出和MIRAGE不参与这轮调试。助手核验逐题结果、区分漏检与参考标签问题，修订标签必须另记版本，不把改标签带来的分数变化算算法收益。正式结论另行核查标签质量，探索性分数不当作临床准确率。当前尚未运行这轮真实对照。

### 以下复核教学安排已被上述职责更正取代

**2026-11-21复核示范补记：** 用户贴出CT3-001至005原始CSV，末尾仍pending、reviewer／review_notes为空，不能据此登记人工复核完成。助手回查001／003／005的固定原文；001原预期行为额外写“测量缺失影响后续分类”，当前gold只直接支撑筛查框架范围，因此已收窄为“已明示筛查目的，可定位Lung-RADS；为回答报告体系名称，无需先补结节大小。本题不作具体结节分类或随访判断。” 仅修订此新增开发题的预期措辞，保留报告／问题／gold／动作及全部旧题；其他两题展示框架分流和缺目的澄清的复核思路。全部仍待人工复核，助手回查不计入human／clinician。当前向用户说明CSV末尾三个字段的用途，请其按原文写自己的核对理由，不把待复核草稿当作已通过标签。

**2026-11-21当前状态：CT专项扩题草稿已交付，下一步是开发题来源复核。** 在方法层配置验收通过后，助手完成132道新增题，连同逐字段保留的原48题，组成data/evaluation/ct_v3下120开发／60留出、30规则家族（20／10），每族6个相关条件变体。原24家族保持划分，另加6家族；新增开发88、留出44，不能把180题表述成180个独立临床场景。blueprints.json固定条款、变体与预定划分，sources.json继承6份原始来源身份，evidence_references.json保存79条参考的原文位置及指纹。新required_evidence_gaps与required_missing_fields分别表示检索缺规则和病例缺事实，不让Agent向医生追问本应补查的规则。原48记录及旧文件值未改。

**实际验收与边界：** scripts/data/build_ct_evaluation.py离线构建，scripts/data/validate_ct_evaluation.py独立读回并复验HTML DOM／锚点、PDF页／字符位置及数据保护。tests/test_ct_evaluation.py的4项行为检查通过，覆盖固定快照重建、gold选择漂移、旧家族边界和复核表保护。results/ct_eval_v3_validation.json结构检查通过：主库和完整向量SHA不变，17份历史产物及6个用户核心模块未变，实际查询含前缀和特殊token最长78。没有检索、LLM、新文档编码或RRF性能实验。构建manifest的pending指独立验证结果另存于results，并非已有人审标签。所有180题仍draft_requires_human_review，独立人工／医生均0；79条参考不是783847片段的穷尽相关性标注。旧留出在新增蓝本生成之后仅复制和结构检查，未显示正文、检索或用作参数调优；不要笼统说本轮“从未读取留出文件”。

**当前用户任务：** 打开data/evaluation/ct_v3/review.dev.csv，先核对CT3-001、CT3-003、CT3-005；检查问题范围、必需证据组是否支持预期行为、事实缺项与规则缺口是否分开，填写review_status accepted／needs_revision、reviewer和review_notes。只读开发题，可结合sources.json及现有证据定位回查，不能仅凭助手预期行为勾通过。初次3题用于校准复核方式，不等于全部题已通过。整批复核意见随后显式合并并固定可用版本；留出另审且不看方法输出调标签。再由用户在可见终端用同一开发集／独立run-name跑Dense、BM25、RRF，复用完整矩阵。详见data/evaluation/ct_v3/DATA_CARD.md。本轮只新增数据辅助与注释，没有代写用户检索核心，最终MIRAGE7663、用药／跨来源／多模态任务仍待完成。

### 以下为扩题前的阶段记录

**2026-11-21最新决定与完成：用户保留方法层model_name，助手已适配保存辅助，入口通过。** model_name不是必须顶层的业务／框架要求，之前强制复制到顶层只是助手旧I/O实现限制，已撤销该建议。公共cases_path、evidence_path、query_template、corpus_name和retrieval_method继续在顶层；dense／bm25各自保存model_name、device、query_prefix和实际参数；rrf只记录candidate_k、rrf_constant，组合方法不需要全局假模型名或设备／前缀副本。retrieval_results_io.py现在按当前方法验证子配置，直接原样保存，不扁平化或修改用户输入；旧平铺配置仍兼容，不改写历史产物。用户run_retrieval_eval.py保持原来的分组结构，RRF键名已修正，三个分支及CLI共5项入口检查全部通过；保存辅助新布局／旧布局／不变性／缺失字段路径／参数检查共6项通过。tests/test_retrieval_results_io.py为新增辅助测试；审计results/retrieval_config_layout_adaptation.json核对17个历史产物指纹未变，旧helper在Dense执行快照保留。没有真实模型／全库RRF／GPU／付费调用。当前功能接入完成，下一步转专项评测覆盖清单、扩题与原文标签回查，正式RRF效果对照等新版题集冻结；当前新增题数仍0。较早要求config.update或全局model_name／device／query_prefix的诊断与旧辅助契约有关，已被本次适配取代，不再让用户重复复制配置。

**2026-11-21当前入口只剩保存配置两项，资源和实际调用已修好。** 用户将elif改成独立if，partial现在正确传rrf_constant=60；五项复验中CLI两项通过，三种方法都完成小型真实检索／评分后到达保存，各资源初始化次数正确，RRF不再缺BM25，也无不支持关键字。失败只因顶层缺model_name／device／query_prefix；公共cases_path／evidence_path／query_template／corpus_name已正确平放。Dense／BM25可用config.update(config[method])将现有子配置补到顶层，RRF顶层补组合model_name、cuda+cpu、空query_prefix；子配置仍保留。另config['rrf']目前误写constant_k和rrf_candidate，须为candidate_k=20、rrf_constant=60，实际调用已经正确，勿再要求改已修好的partial。记录results/retrieval_entry_validation_2026-11-21_revision1.json，最新同名无日期报告也已更新。tests/test_retrieval_entry.py仍5项，新增检查既定RRF元数据字段以防实际参数与保存信息不一致；未改用户核心，没有GPU或正式语料运行。下一次重读最新入口并复跑5项，配置通过后转扩题／标签核验，不提前跑正式RRF。下方“资源elif／实际参数误拼”是首版历史状态。

**2026-11-21最新入口复验：CLI两项通过，Dense／BM25／RRF三个实际分支尚未通过，当前用户集中修三处。** 用户main已改为main(method,cache_dir,cases_path,evidence_path,run_name)，CLI调用与之自洽，按此实际接口核验，不为位置参数顺序强制改回；CLI新增--cache／--evidences也可正常传递。tests/test_retrieval_entry.py使用7条虚构证据／2题、假模型、真实小缓存／BM25／检索／评测／保存，并将输出重定向临时目录，5项中2个CLI通过、3个方法错误；报告results/retrieval_entry_validation.json，首版另存retrieval_entry_validation_2026-11-21_initial.json。三处为：(1)资源准备第二段仍是elif，rrf只建Dense，bm25_retrieve_fn未定义；改为独立if。(2)partial和config['rrf']误写rrf_candidate，已通过函数的参数名为rrf_constant，需统一。(3)公共配置全放config['general']、方法摘要全放子项，保存函数要求顶层cases_path／evidence_path／query_template／model_name／device／query_prefix；corpus_name也须顶层medical_v3，否则保存默认ct_v2。公共字段平放顶层，dense／bm25详细子配置保留，再为当前方法填顶层model_name／device／query_prefix；RRF用BM25+BGE RRF、cuda+cpu、空全局前缀，实际BGE前缀仍留dense子配置。助手未修用户核心、未用正式题／GPU／付费API，也未创建正式RRF成绩。未把这些基础入口问题加工程面试编号。下次“好了”先重读文件并复跑这5项，前面的12项融合编排已通过，不重做；入口通过后转专项扩题和标签核对，正式对照等待新版冻结。

**2026-11-21最新：RRF纯融合及查询编排12项合成检查全部通过，当前用户接CLI。** tests/test_rrf_fusion.py含原7项融合和新5项假检索编排，用Mock验证每路一次、相同原始query、候选数和常量传递、非法参数在检索前拒绝、候选不足／空路、上游异常传播及输入不变；记录results/rrf_retrieval_validation.json，旧7项记录和失败证据保留。用户retrieve_rrf.py未被助手改写，没有真实RRF检索／模型成绩。当前用户修改run_retrieval_eval.py：导入retrieve_rrf；main保留前4参数并增加可选关键字run_name=None；资源准备改为两个独立if（dense／rrf准备模型缓存，bm25／rrf准备词项索引），各资源一次初始化；方法分支只选最终partial，评分／保存统一一次。RRF固定每路Top20、最终评测Top5、常量60，记录公共路径／模板及dense／bm25实际子配置、完整缓存、候选预算；组合query_prefix为空，BGE前缀仍由dense模型配置处理。CLI --method增加rrf，增加--cases(type=Path,默认原32题)和--run-name(默认None)以支持新版题集独立结果名；默认运行名仍medical_v3_{method}_ct_dev。具体步骤docs/rrf_task.md。下次“好了”先读实际入口并用临时合成题／假模型／临时输出验收，不重新编码或开全库长跑。入口通过后先完成专项评测扩题与原文标签核对、冻结，再做正式RRF对照；MIRAGE仍为独立最终测试。较早“等待编排”均为历史。

**2026-11-21最新：fuse_rankings已通过7项手工验收，当前用户实现retrieve_rrf查询编排。** 返回list[dict]、跨路贡献、单路查重、参数、空排名、同分、截断与输入不变均正确。记录results/rrf_fusion_validation.json，测试tests/test_rrf_fusion.py（逐行中文注释），保留此前initial／revision1失败证据；助手未改用户核心，无模型／真实检索。用户在同一retrieve_rrf.py实现retrieve_rrf(query,k,*,dense_retrieve_fn,bm25_retrieve_fn,candidate_k=20,rrf_constant=60)：实际调用前检查3个正整数及candidate_k>=k，两路各接收相同原始query与candidate_k且各调用一次，合并交给已通过的fuse_rankings，返回统一hit列表。资源仍由入口一次准备并用partial绑定，函数不读数据或创建模型；BGE前缀留在模型查询配置。异常正常向外传播。本轮用可记录调用的假检索函数验收，再接CLI；正式Dense／BM25／RRF对照仍以扩充并核对新版评测题为前置。较早“融合还剩两处”为历史，不能再要求修已通过问题。

**2026-11-21最新复验：fuse_rankings还剩两处，不能进入查询编排。** 用户已修正正整数参数校验、hit.copy后改score、按输入名次累加；手工诊断中的[B,A,C]及B贡献计算正确，输入不变与全空等检查通过。当前保留items并用x[1]排序是可行写法，但返回值仍为[(id,hit),...]，应提取排序元组的hit部分，返回既定list[dict]。另一处为单路重复ID校验仍未实现：每份hits开始新建seen集合，遍历时查重并add，跨路new_hits继续累计。七类复验3项通过，其余由返回接口和缺少查重阻断；记录results/rrf_fusion_validation_2026-11-21_revision1.json，源码SHA86c29a6269ea31e27b81850d56e6c176cf845f4aee1fcedd2f77d7dfbc64a201，包含本次受测源码。助手未改核心，没有模型／全库运行。下方初版4处问题已部分解决，以本段两项为准；不要求用户必须改成values，只需返回接口正确。

**2026-11-21当前：用户已创建retrieve_rrf.py，但fuse_rankings尚未验收，先修该函数。** 七项手工排名检查仅全空通过，记录results/rrf_fusion_validation_2026-11-21_initial.json，受测源码SHA为af14c2965879a87dd11587630804b70114907f83d2303bf7bcbd40a4f52b52a4。正常输入在最终排序报tuple indices错误：new_hits.items()产生(id,hit)元组，排序键却按hit字典取score/id，应根据values中的hit排序。首次写入时直接hit['score']=...修改了输入，需要先复制hit再替换融合分。输入已经按检索名次排列，直接enumerate即可，不在融合函数中按原score重排。另外补齐既定正整数参数校验和每份排名内部的重复ID拒绝；跨排名同ID应累加。排序后可直接返回字典列表，不必再做元组转字典。助手没有修改用户核心源码，没有模型／语料检索或正式RRF成绩。这些基础实现问题不新增工程面试问题编号。下次“好了”重读实际文件并用手工排名复验，不跳过失败项。

**评测扩题的最新安排（依据11月20日讨论，本轮补记）：** 当前32题仅16场景家族、AI初标，足以排错但不承担最终效果结论。RRF纯融合函数继续写；第一次正式RRF方法对照前先补专项题覆盖、回查原文标签并冻结新版评测，再让Dense／BM25／RRF使用同一新版题集。近期CT开发100–150、独立留出50–80是建设预算建议，按可核实独立场景决定，不是统计充分性保证，也不算已生成或已复核。现有32／16及成绩保留，不能倒改旧标签或把旧开发题移成未见留出；报告多个模态版本属于同一病例家族。扩题仅改变查询／评测输入，主语料和完整文档向量继续复用，不重新编码；MIRAGE7663继续作为独立最终外部测试，未用于调参。详见docs/data_expansion_milestones.md；当前新增题数仍为0。

**2026-11-20最新完成：用户终端续跑已结束，医学v3 Dense全库与32题结果已独立核验通过，不再编码。** 矩阵(783847,384)、float32只读memmap，所有行数值有限且归一化，文件SHA-256为83d0ea30b5bc6588391a6f3cd13f012bbe9467e58c82402110148dacef339688；缓存fingerprint仍为03f83f8aee178e40b006d7b80f395c7f50cdbc6ef292ee190e00b8a423c60b34。Canonical与Group Recall@1／3／5均为0.1875／0.359375／0.421875；完整13／部分1／零18题，查询均值330.062ms、中位328.447ms。相同输入的BM25为0.28125／0.34375／0.453125、均值4332.917ms；Dense较高3题、BM25较高4题、相同25题，3题仅Dense有非零标注覆盖、4题仅BM25有、11题两路均有、14题均零。Top5并集最多10候选的需求组覆盖0.546875只用于观察互补性，绝不是RRF成绩。两段进程8:43.33和3:52.87，合计12:36.20，不含移交间隔但含重复加载，不称单次冷启动编码时间；较大峰值RSS约17.295GiB。用户新加tqdm／百分比输出，移除进度语句后AST与首段相同；续跑前未另存源码，当前版本以segment2_observed_after_run归档，不伪装事前固定。六指标、原题字段、所有命中／标注ID、矩阵／行序／文件指纹与旧v2／BM25成绩均核验通过。结果前缀results/medical_v3_dense_ct_dev，审计complete_integrity_validated；完整说明docs/medical_v3_dense_baseline.md。没有新生成、MIRAGE、留出或临床有效性成绩。

**当前下一任务：用户新建retrieve_rrf.py，先实现fuse_rankings(rankings,k,*,rrf_constant=60)，不代写核心。** 任务和参数依据见docs/rrf_task.md；Python内置dict／enumerate／sorted即可。输入为多份已有hit列表，名次从1开始，按id累加1/(60+rank)，未出现贡献0，输出字段沿用id／score／source_id／locator／text而score换为融合值；不改输入hit。融合分降序，同分id升序；单路重复ID抛错，两路同ID可累加。手工[A,B]与[B,C]应输出[B,A,C]。先用手工列表验收，再在同模块接查询编排及rrf入口；预设每路Top20、最终Top5、等权、常量60（原始论文参考值，不称医疗最优），复用完整Dense缓存。用户要求自己看终端跑，本次长任务已交由用户完成，后续真实长任务优先给终端命令，不未经要求另开后台长跑；助手可检查代码、小样本和保存结果。下方11月19日“等待续跑／运行中”均为历史状态。

**2026-11-19最新移交：用户要求在可见终端自己运行，助手已停止后台进程，不能再次自行启动。** 会话4565以KeyboardInterrupt／退出130正常结束，最后已提交529,408／783,847行，缓存状态building；已用非阻塞文件锁验证旧进程释放锁，断点完整。用户将用原CLI、原cache目录和离线开关从该断点继续，命令使用tee显示并保存第二段日志、GNU time记录第二段资源。第一段日志／资源已另存results/medical_v3_dense_ct_dev_encoding_part1.log及_encoding_part1_resources.txt；第二段预定为_encoding_part2.log及_encoding_part2_resources.txt。审计_run_audit.json状态interrupted_for_user_terminal_resume，execution_segments记录两段，不把第一段130当未知失败，也不能把第二段耗时叫完整冷启动编码耗时。当前无全库Dense成绩。下次用户“好了”先检查第二段、最终摘要、缓存清单，再独立核验与比较，不重复编码；/tmp/validate_medical_v3_dense_run.py是助手准备的未执行验证工具，使用前须确认适配分段资源记录。较早“正在后台运行”记录已被本次移交取代。

**2026-11-19 当前正在运行全库Dense，先检查会话4565，不要重复启动。** 用户已接通run_retrieval_eval.py，main(cases_path,evidence_path,cache_dir,method)，实际元数据键embeddings_cache；12项合成入口验收通过，记录results/embedding_entry_validation.json。RTX 4090真实8条文档／查询编码也通过，输出(8,384)、float32只读矩阵、归一化、复用零正文编码，记录results/dense_cuda_preflight.json（首次探测记录另存_initial.json）。默认工具环境没有/dev/nvidia0，但获准的隔离环境外GPU执行和模型实测正常，不要误判服务器驱动故障；实际GPU操作需要require_escalated访问，本轮执行已授权。底层曾在local_files_only=True时探测processor_config.json远端HEAD，正式命令增加HF_HUB_OFFLINE=1、TRANSFORMERS_OFFLINE=1，模型和权重版本未改。783,847条／32开发题的原样CLI已启动，日志results/medical_v3_dense_ct_dev_run.log，审计_run_audit.json状态running，资源_resources.txt，源码_code_snapshot；缓存cache/embeddings/03f83f8aee178e40b006d7b80f395c7f50cdbc6ef292ee190e00b8a423c60b34，每512条提交。完成后独立复算指标、核对输入／源码／历史成绩及缓存完整性，再教用户RRF。当前未有全库成绩，未修改用户核心模块，无付费模型、MIRAGE或留出评测；下方尚待实现／接入描述为历史状态。

**2026-11-19 最新进度：用户已完成 embedding_index.py，6项合成编排检查全部通过。** 首次分批／单条尾批／非连续DataFrame标签下的行位置、完整缓存零文档编码调用、第二批模拟模型失败后从前三行断点恢复、全部行已保存但未finish的恢复发布、单改查询前缀复用、非法chunk_size拒绝，均通过；返回为只读float32 np.memmap，矩阵和元数据一致。结果results/embedding_index_validation.json绑定实际用户源码和缓存源码SHA-256，测试tests/test_embedding_index.py已逐行中文注释。助手没有修改用户核心模块，没有真实模型／CUDA／全库编码。当前应由用户修改run_retrieval_eval.py：导入prepare_document_embeddings；模型kwargs保留cuda并固定提交5c38ec7c405ec4b44b94cc5a9bb96e735b38267a、local_files_only=True；用函数替代整库embed_documents和np.float32两行，传入当前evidence_df／embedding_model／evidence_path以及脚本根目录cache/embeddings，接收embeddings与cache_info；config增加embedding_cache=cache_info。入口目前尚未接入，下次“好了”先读实际入口验收，再做CUDA小批和全库。下方较早“用户待实现embedding_index.py”描述为历史状态，以上方最新验收为准。

**2026-11-19 维护任务：用户要求助手代码逐行中文注释，并允许清理无用一次性脚本但保留操作记录。** 已将10个仍用于数据复现／测试的根目录脚本移到scripts/data，包内导入和3个ROOT定位同步，构建清单的源代码路径也同步；未为凑数删除仍有依赖的下载、解析或验证能力。根目录保留用户5个核心模块与助手2个I/O模块，清理9个旧路径自动编译.pyc。助手的16个实际代码／测试文件已逐行补中文注释，多行字符串内容保留；包标记文件仅含说明注释。以迁移后、注释前版本为基准，语法树保持一致；26项测试通过，下载／构建未重跑。整理前源码与迁移／注释核验记录在results/source_maintenance_2026-11-19。下载来源、候选、参数、许可筛选、指纹、数量、失败原因与模块命令详见docs/data_acquisition_and_processing.md；文件导航docs/project_files.md。此前历史文档中根目录数据脚本名称是旧位置，现用python -m scripts.data.模块名；历史执行快照和冻结语料／成绩继续保留原样。当前研发任务仍为用户实现embedding_index.py和Dense入口接入，不将维护当成完成编码。 维护核验最终通过：16份助手源码／测试的2,514个代码行均有中文注释；注释相对迁移后原版的语法树一致，目录调整仅包含已记录的导入／ROOT／代码定位变更，26项测试通过，29个已跟踪数据／成绩文件指纹保持不变。embedding_index.py在共享工作期间检测到外部更新，本轮没有写入或回滚它，下一次检查必须读取最新内容；不要声称其字节与维护前相同。

**2026-11-19 当前具体任务：用户新增 embedding_index.py，实现 prepare_document_embeddings(evidences, embedding_model, *, evidence_path, cache_dir, chunk_size=512)，返回 (embeddings, cache_info)，再接入现有 dense 分支。** 缓存 I/O 由助手按已有保存授权实现于 embedding_cache_io.py，提供 DocumentEmbeddingCache：with 打开一次，is_complete／completed_rows／load／write_batch／finish／info；辅助模块不调用模型。8项合成测试通过，覆盖复用、断点、身份变化、非法批次、损坏、发布中断和排他写入，记录 results/embedding_cache_preparation_validation.json。用户负责分块、选择文本、embed_documents 调用和入口接入，不给完整核心函数。文档 docs/dense_cache_task.md 固定接口和验收：正式 cache/embeddings、384维float32、外层512条检查点／模型内部batch_size=8，归一化与前缀不变。模型 kwargs 保留cuda，并固定本机已核实的缓存提交5c38ec7c405ec4b44b94cc5a9bb96e735b38267a和local_files_only=True，库参数已核对。查询参数不使文档缓存失效；缓存绑定文件与实际id/text行序及模型／文档配置，当前不是逐文档增量索引。下一次“好了”先读新模块和入口，用合成可计数编码器检查零调用复用／恢复，再做真实CUDA小批和全库。当前没有真实Dense缓存或GPU模型运行，不能跳过用户核心代码。

**2026-11-19 最新完成：医学主语料 v3 的全库 CPU BM25 开发集基线已运行并独立核验通过。** 用户的三个核心函数和入口已完成；args.method、v3 数据路径、BM25 保存字段及 dense 版本名均已修正。783,847 片段／32 开发题，原样执行 --method bm25，结果 32×16；Canonical 与 Group Recall@1／3／5 均为 0.28125／0.34375／0.453125，Top-5 需求组完整14／部分1／零17题。每题检索均值4332.917ms、中位数4298.497ms；整进程2:56.53、峰值RSS约17.294GiB（不是单独索引大小），退出0。独立逐题复算全部指标、文件指纹、命中／标注ID有效性、代码及原v2成绩未改动，全部通过。结果前缀 results/medical_v3_bm25_ct_dev，含 results.jsonl、summary.json、validation.json、resources.txt、run_audit.json；审计为 complete_integrity_validated，执行源文件副本在对应 code_snapshot 目录。归档说明 docs/medical_v3_bm25_baseline.md。exec session61007已结束，不重复运行本轮基线。没有 v3 Dense、LLM生成、留出或MIRAGE成绩。

**最新教学粒度约定（2026-11-19）：直接说明当前步骤怎么做、引用哪些库、关键 API／正则及选择理由。** 用户不需要整套 Python 基础教程，也不希望只给函数名让自己猜用法。可以给具体正则、少量关键调用和输入输出示例；完整核心函数仍由用户组合实现。检查代码后集中说明问题并给出下一段实际任务，不逐行挤牙膏。

**2026-11-19 当前入口状态：run_retrieval_eval.py 的 main(cases_path,evidence_path,method)、__main__ 参数解析、脚本根目录 v3 路径、dense／bm25 分支、各自版本名及保存配置均已接通。** BM25 的命令行到保存已通过临时合成验收及上述真实全库运行，不再要求重复修正历史 Namespace／缺配置问题。Dense 分支仍每次直接 embed_documents 全库，尚无缓存；下一工作单元应先加可复用向量缓存和实际编码配置／输入指纹，再用既定 CUDA 编码建立 v3 Dense 基线。不要以无参数命令提前重复全库编码。

**2026-11-18 医学主语料 v3 已扩充、冻结并通过独立完整性校验：10,840 个入库来源、783,847 个片段，594,483 条不同正文。** 包括 9,836 篇 PMC CC BY／CC0 论文（480,538 片段）、998 份 DailyMed 产品说明书（303,071 片段），以及原 CT v2 的 6 来源／238 片段逐字保留。原始下载池分别为 10,000／1,000，进一步隔离 164 份非白名单论文类型和 2 份无可索引 SPL；不要把下载量当成入库量。NIH 两网页与三官方 PDF 本机均 403，新增 NIH 为 0，空输出不是成功入库。全部片段回溯、源文件／单元格位置、指纹和 token 检查通过，最高 480 tokens；原 v2 输入及开发题指纹未变。新增解析 6 项测试通过。入口为 data/v3/DATA_CARD.md，实际清单 data/v3/corpus_manifest.json，核验 results/medical_corpus_v3_validation.json；调研 docs/medical_corpus_v3_research.md。本轮是助手受托的辅助数据准备，没有运行嵌入模型／付费 API、读取 MIRAGE 测试内容或修改用户核心检索／评分／生成代码。

**当前下一工作单元：为 v3 Dense 基线接入可复用向量缓存，再用 CUDA 编码同一主语料并评测原 32 道 CT 开发题。** BM25 三函数、CLI、完整基线已完成，不再从 tokenize／build_bm25 重新教学。保持 LangChain HuggingFaceEmbeddings、BGE-small-en-v1.5、384维、既定归一化／文档和查询前缀配置；缓存需绑定证据内容及行序、模型和编码参数，不能仅按条数复用。向量基线另存 medical_v3_dense_ct_dev，与本轮同库 BM25 比较后再做 RRF。辅助缓存I/O已由助手准备并通过合成检查，核心编码和检索仍由用户实现；当前任务见docs/dense_cache_task.md。用户询问为什么不用GPU，已解释rank-bm25当前为Python字典＋NumPy CPU后端，该询问没有授权或要求迁移BM25后端；后续BGE编码仍使用CUDA。

**数据扩充的最新工作次序（2026-11-18）：先批量扩充并固定主要检索语料版本，再做向量／BM25／RRF 的正式对照。** 用户指出扩库后仍要重复构建和评测，助手据此纠正了先做完小库 BM25／RRF 再扩库的安排；此前顺序不再执行。扩库不要求重写已有代码，但正文编码、词项统计／索引及评测确实需要更新或重跑，不能承诺零重复计算。当前 CT v2 的 238 条／32 开发题及实测结果保留为回归基线，不要求再在小库完成 BM25／RRF 正式实验。当前工作是来源与使用条件、主题覆盖、磁盘内存编码资源审计及批量接入，实际规模已由 v3 清单核定；数据量不是任务覆盖或模型效果证明。详细安排见 docs/data_expansion_milestones.md。MIRAGE 原始 7,663 题已下载并核验，配套自定义主语料已接入并通过完整性校验，上游题库条件待审计，没有模型对标成绩。

**扩库后的检索工作单元：用户实现 BM25 单独基线，再做 RRF；当前优先数据接入。** 完整接口、分词、参数、运行及验收已固定在 [BM25 当前任务](docs/bm25_baseline_task.md)。新模块为 retrieve_bm25.py：tokenize(text)、build_bm25(evidences, *, k1=1.5, b=0.75, epsilon=0.25)、retrieve_bm25(query, k, *, bm25_index, evidences)。统一小写、英文片段和含小数数字为 token、连字符分隔，保留停用词、不词干化；语料与查询共用规则。按分数降序，同分按原始行顺序。用 rank-bm25 0.2.2 的公共 get_scores，已装入当前环境；已核验官方源码、默认参数与 Apache-2.0 许可，本地 LangChain BM25Retriever 也使用该后端。该实现作为最终项目的可复现参照基线保留；不因教学再迁移包装，不将小库运行能力当作已证明大语料扩展能力。

待主要数据版本固定后，复用 run_retrieval_eval.py，用户新增 --method dense|bm25（默认 dense 保持原行为），保留现有 main()，完成脚本目录路径收尾。BM25 分支仅构建 CPU 词项索引，partial 绑定同一五字段返回接口，继续用原 evaluate_retrieval。正式输入改为冻结后的 data/v3/evidence.jsonl 与 data/v3/cases.ct.dev.jsonl（原 32 道 CT 开发题原样保留），仍用报告加问题模板，英文 BGE 前缀不加入 BM25。独立保存 medical_v3_bm25_ct_dev，新版本向量结果另存 medical_v3_dense_ct_dev；不覆盖已有 ct_v2 基线，也不拿换库前后差异归因于算法。配置记录检索方法、参数、分词、同分规则及包版本。RRF 本轮尚不实现。

助手仅准备依赖、文档与保存辅助：retrieval_results_io.py 现读取 config.retrieval_method，旧配置默认 dense；省略 run_name 时按 ct_v2_<method>_dev 命名，stage 正确标注方法；计时范围明确排除索引构建和指标计算。legacy／dense／bm25 的合成 I/O 与读回均通过，临时文件删除，原始向量结果指纹保持一致。准备记录见 results/bm25_preparation_validation.json。截至2026-11-19，BM25核心模块与--method已由用户完成，真实32题基线及核验已完成；依赖／保存辅助与实际模型成绩分开记录。

**2026-11-18 最新结果：CT v2 纯向量开发集实测及保存已完成，独立核验通过。** 用户已用正式入口接通 238 条语料、32 道开发题，保存 results/ct_v2_dense_dev_results.jsonl（32×16）及 summary.json。Canonical Recall@1／3／5 为 0.21875／0.390625／0.484375；Group Recall@1／3／5 为 0.21875／0.421875／0.484375。Top-5 的需求完整／部分／零覆盖为 15／1／16 题。CUDA 单轮检索均值 4.0475 ms，中位数 3.1064 ms。助手逐题独立复算全部指标、汇总、输入指纹、题目与标注匹配及 Top-5 合法性，全部通过，未重新编码或调用 API；见 [实测归档](docs/ct_v2_dense_baseline.md) 与 [核验记录](results/ct_v2_dense_dev_validation.json)。题目为 AI 初标，指标不是医学回答正确率，留出题未用。

**2026-11-18 用户再次强调当前就是项目开发，质疑新增入口的 practice 命名。助手已纠正：本轮正式入口为 run_retrieval_eval.py，由用户实现；不再新建阶段练习 Notebook。** 此前该入口尚未创建，本次没有需要迁移的入口代码；现有 retrieve_core.py、retrieve_evalution.py 的职责、接口、算法、模型、数据、指标和验收均保持既定安排。已有 practice Notebook 仅为历史实验产物，不重做其中已验收的工作。当前任务文档与 README 已同步，不得下一轮又要求新建练习入口。

**全项目执行约束（用户于 2026-11-17 明确）：现在就在做正式项目，所有任务都按已确定的成品方向增量开发，不反复改变标准。** 这不局限于向量模型：数据结构、检索、生成、Agent、引用、评测和交付都遵守。阶段划分用于逐步增加功能和数据，不用于先做一套将来丢弃的教学接口。具体规则见第 13.8 节；已验收成果保持原有完成状态，不能因后来新增要求追溯改成未完成。

**当前操作顺序已由用户确认：先写两个 py 核心模块，再写正式基线运行脚本。** 实际文件名为 retrieve_core.py、retrieve_evalution.py，与最初规划名称不同；按实际文件检查和引用，不误判为没有保存，不要求为命名重新实现。最新合成检查中，检索、两类评分、两题批量评测及保存兼容性正常流程均通过；评分空标注和评测 ks 入口校验也通过。retrieve 的 k<=0 校验现已修正，-1、0、1.0 均在编码前以 ValueError 拒绝，遗留检查通过。两个核心模块合成验收及真实 CT 开发集结果核验现均通过；正式脚本已接通，另有 Notebook 保存的向量形状 (238, 384)。完整结果已保存，main() 和当前编码参数配置已写好；入口数据路径与方法分支待一并收尾。模型与数据由运行入口创建和传入；两个模块导入时不加载模型／文件，不反向依赖 Notebook。入口导入模块是正常单向调用，“不依赖”指不隐式读取 Notebook 全局变量，不是禁止入口 import。当前任务具体说明见 docs/ct_v2_baseline_task.md。

2026-11-17 用户表示 evaluate_retrieval 未理解，助手已读上述实际文件并仅用合成小样例检查：recall_at_k([B,X,C],[A,C],3)=0.5；group_recall_at_k 在分母位置提前读取循环变量 gold_ids，触发 UnboundLocalError；evaluate_retrieval 按 for case in cases 迭代 DataFrame 列名，触发字符串索引 TypeError；retrieve 的 evidences.iloc(top_indices) 取行方式触发 TypeError。evaluate 中查询组装、检索一次与计时框架已写；尚需按行遍历、每题同时算两类指标的全部 K、积累结果行并返回 DataFrame，不能用标注类型分支二选一。助手未修改核心源码、未加载真实模型或调用 API。这些是当前代码讲解与修正点，不记录成面试工程问题；用户修正后再复核。

2026-11-18 最新复核：此前取错证据行、iterrows 未解包、字段拼写、缺少 scores、循环内提前 return 五处均已由用户修正。助手以两个不同合成题、非默认 DataFrame 索引和固定二维向量联通真实 retrieve 与 evaluate_retrieval：结果为 2×16，六项逐题分数符合独立预期、每题只编码检索一次、查询只有报告和问题、ID 与得分顺序正确、来源定位返回、K 超过语料数返回全量，均通过；输出送入现有保存辅助，在临时目录保存读回成功，临时文件已自动删除。group 的 K=1／2／3 样例及同组不重复计数此前也已通过。

2026-11-18 最近一次复核（用户按片段补校验后）：评分空标注（包括空需求组）ValueError 通过；evaluate 的 ks 为空、含零、负数、1.0、1.5 时均在任何检索调用前拒绝，通过；retrieve 的 0、1.0 均在查询编码前拒绝，通过。该次检查仅遗留 retrieve 第 4 行 k==0 应改为 k<=0；随后用户已修正，助手于 2026-11-18 验证 -1、0、1.0 均在编码前以 ValueError 拒绝，此遗留已解决。正常两题 2×16、六项分数、有效 ID／得分及每题一次检索再次通过。用户修这一行后直接编写 run_retrieval_eval.py 入口，真实编码 238 条、评测 32 开发题并保存；下次统一检查该行、入口及真实输出。不再增加边界要求或安排单行验收轮次。助手未修改核心实现，合成结果不冒充模型能力或 CT 成绩，未加载真实模型或调用 API，不将基础错误加入面试工程复盘。

**用户已进一步确认：最终项目必须完成 MIRAGE 对标，这是硬性验收项。** 必须交付原始 7,663 题、五个子任务上的固定配置实测对照，覆盖无检索、基础 RAG、改进 RAG，报告分任务准确率、宏平均、成本与逐题记录。专项临床证据链和多模态验证也继续保留。仅有 CT 小库、下载基准或抽样结果不能标记项目完成；性能收益如实实测，不能预先保证。完整要求见 docs/benchmark_scope.md。MIRAGE 原始题库快照已取得；外部检索语料和完整评测适配尚未完成，没有对标成绩。

**2026-11-17 对标目标校准：用户要求保留此前七千余项的对标目标，不能以几百条收尾。** 已核实 MIRAGE 的 7,663 是题目数，对应本项目当前 48 题；238 是证据块数，两者不能混比。CT v2 本轮交付不等于全项目最终规模。后续明确加入 MIRAGE 外部基准接入与语料覆盖审计，不再将其仅作为可选项搁置；原题现已下载并核验；外部语料及模型对标仍未完成。专项精核集与总检索集合分别规划，原 300–1000 不作为总索引的上限。来源、原始协议、许可及实际状态详见 [对标范围校准](docs/benchmark_scope.md)。当前 CT 基线仍可做，但不能据此宣称完成通用医学 RAG 对标。

**CT v2 的数据准备已按用户“扩数据一次性搞完”的要求整批交付。接下来直接进行新数据上的检索基线复测，不再要求用户逐条整理 18 张候选或重写编号解析。** 本轮数据脚本、统一表示、来源位置验证、质量隔离和合成题初标由助手完成；检索、生成、评分及 Agent 核心代码仍由用户写。

- B0：原 15 张卡、8 道开发题的纯向量实现和结果已完成，历史指标保留。
- B1：DeepSeek 连通、上下文构建、DEV-01 Top-3／全量对照已完成；实时端到端、跨题生成评测仍待做。
- CT v2：6 份本地来源快照，241 条候选，**238 条本地检索输入**，另有 3 条隔离记录。最长正文 434 tokens，使用本地 BGE tokenizer 含特殊 token、无截断检查；数据构建阶段不做模型推理，随后用户已完成纯向量编码与开发集评测，尚无新增 LLM 生成评测。
- 合成题：**48 道、24 个场景家族**；开发 32 题／16 族，留出 16 题／8 族。均为助手生成的 AI 初标草稿，尚未经独立人工或医生复核。新留出题未用于算法调试；原 v1 留出未读入设计或改动。
- 12 项测试通过；全部网页块可回查原始 DOM，真实锚点存在，PDF 页文本与原文件一致，候选正文可由原始位置重建，表格行保留 Variant 条件，家族不跨集。已重复离线构建，数据文件 SHA-256 完全一致，原 v1 数据和 Notebook 前六个单元格一致。
- 入口是 [CT v2 数据说明](data/v2/DATA_CARD.md)、[批量交付记录](docs/ct_v2_delivery.md)、[数据验证](results/ct_v2_validation.json) 与 [复现记录](results/ct_v2_reproducibility.json)。Notebook 的旧空白 build_evidence_candidates 练习已由本轮授权下的整批构建入口取代，不伪造 Notebook 执行次数或输出。
- 代码：[ct_data_pipeline.py](scripts/data/ct_data_pipeline.py)、[ct_case_blueprints.py](scripts/data/ct_case_blueprints.py)、[validate_ct_data.py](scripts/data/validate_ct_data.py)。输出位于 data/v2，v1 文件继续保留。
- 范围：本轮为 CT 文字证据数据；未完成用药、原始论文、报告 OCR、多模态或 Agent。Fleischner 无本地全文、PDF 第一页复杂合并表格暂未自动恢复，均明确排除。注释 6 原文数值表达待复核、两条多癌种检测内容不在当前范围，保留候选及原因。
- 本地完整语料不代表全部可公开再分发。NCI 文字子集为 120 条；归属及 ACR／USPSTF 使用条件见 [USAGE.md](data/v2/USAGE.md)，来源原有决定未被自动改成开放许可。

**当前纯向量基线实测已完成；当前工作单元转为批量扩库，固定主要语料版本后再做 BM25／RRF 对照。** 原 CT 小库及结果用于回归与错误分析。检索、评分与保存接口不变，已实现模块不重写；扩充后更新索引和数据版本，再用相同程序评测。正式入口的脚本目录路径、main() 与完整配置记录按既定安排接入，不为这些组织调整重跑现有小库基线。

2026-11-17 用户追问以后扩数据是否又要重做。本轮任务已调整为一次必要的复用整理：用户待实现 retrieval_core.py（迁移原检索算法、显式模型／证据／向量／前缀依赖）与 retrieval_evaluation.py（复用评分并整理逐题评测），Notebook 只负责配置和运行。以后同结构数据替换路径和运行名称，不要求另复制一份 Notebook 或重学编码。238／32 仅是当前快照验收数，程序通过实际输入计算规模。当前尚无向量缓存／增量索引，不能声称已实现；数据扩充需更新向量、重新评测，新来源仍需解析和使用条件核验，新任务仍需查询及评测适配。该整理不更换算法；先在少量开发题检查前后结果等价，再跑全开发集，不读留出题。

2026-11-17 用户提出项目可以使用 OKF。已按 GoogleCloudPlatform 的 Open Knowledge Format 核验官方 v0.2 规范、参考 Agent、Apache-2.0 许可证及相关 Knowledge-as-Skill 预印本，评估见 [OKF 适配记录](docs/okf_assessment.md)。建议作为来源目录和知识组织层做小范围试验，先从现有 6 条来源记录导出只读目录，再于 Agent 适用性核验阶段比较是否使用目录路由；当前仅完成研究与建议，用户未明确确认具体 OKF 指代或要求全面迁移，未导出文件、安装参考 Agent、改动语料或产生性能结果。现有来源／证据溯源能力不是 OKF 新增贡献，格式不解决数据规模、医学正确性或原文使用条件。MIRAGE 全量目标及当前纯向量基线保留。

**2026-11-17 用户随后明确决定：先按原计划进行，后面扩充完整数据后再做 OKF 对照。此决定覆盖上段提前在 6 份来源上试验的建议。** 当前不实施 OKF 导出、工具、迁移或对照；继续 CT v2 纯向量基线及原检索改进路线。完整数据扩充并冻结对照版本后再讨论 OKF，不将其列为当前前置任务。已有调研文档仅保留候选方案和真实未实施状态。

**2026-11-17 用户要求“最终项目要用什么，现在就用什么，不要等以后再换”。向量模型接口已定为从当前 CT v2 起使用 langchain_huggingface.HuggingFaceEmbeddings，后续也沿用 LangChain 的 Embeddings 接口。** 底层仍是 Sentence Transformers 和 BAAI/bge-small-en-v1.5，不以 SentenceTransformer.encode 作为新核心组件的公开调用，也不再安排以后换封装。当前本地已安装 langchain-huggingface 0.3.1、langchain-core 0.3.71；已读本地封装及核对官方文档，无需升级。文档用 embed_documents、查询用 embed_query；文档参数 batch_size=8／normalize_embeddings=True／prompt=""，查询参数 batch_size=1／normalize_embeddings=True／prompt=prefix，前缀不再手工拼接。输出为列表，手写 NumPy 检索前转换 float32。新 retrieve 建议接口为 retrieve(query, k, *, embedding_model, evidences, embeddings)，模型只创建一次。该决定覆盖前文历史任务中的 model.encode 与显式 query_prefix 参数安排；原 B0 历史文件不改。该接口现已由用户实现并完成 CT v2 纯向量开发集实测，具体成绩见本节最新记录。0.3.1 封装实际会把换行替换为空格，需记录预处理，不能无实测宣称与旧编码逐位一致；细节见当前任务说明。

助手已实现 retrieval_results_io.py，只检查和保存 eval_df 与实际配置，不编码、检索或评分；临时目录合成 I/O 检查通过，未生成真实成绩。输出目标为 results/ct_v2_dense_dev_results.jsonl 和 ct_v2_dense_dev_summary.json。用户说“好了”后先检查运行脚本、六项指标及这些文件，不再重复教读文件／单条编码。新数据版本的指标不能直接归因于算法变化，留出题不用于调试。

历史记录：2026-11-17 编写 prepare_mirage_data.py 后，首次联网因 DNS／TLS 问题失败，未关闭证书校验。2026-11-18 重试已成功取得原题、LICENSE 和 README，并完成本地 SHA-256／schema 检查；最新状态见 results/mirage_preparation_status.json，保留了此前失败记录。下载与完整评测接入、广泛检索语料分别统计，当前没有模型对标成绩。

## 2. 用户背景与求职目标

用户是浙江大学人工智能硕士研一，本科为浙江理工大学计算机科学与技术。以前自己用 Transformer、GNN 等方法融合血液数据做过分类与预测。研究方向可能为显微操作视觉伺服，实验室 GPU 有限。本项目是独立选择的求职项目。早期希望CPU、小模型与API跑通；2026-11-24进一步明确以正式项目效果为先，不能把早期资源偏好当作成品轻量模型上限，具体选型约束见13.10。

用户学过 MiniMind、Hello-Agents，跑过 All-in-RAG 的 LangChain＋DeepSeek 示例，同时练习力扣。项目希望支持 Agent 开发／AI 应用开发实习求职，并形成本人能独立解释、复现和展示的贡献。先前表达的实习时间意向为最早寒假、最晚研一下学期，开学后可以全勤；具体日期以后按实际情况确认，不据此推断当前已经满足某一入职日期。

## 3. 项目定位与成品边界

暂定名：**基于多源循证检索与多模态报告解析的医疗辅助决策系统**。

面向临床人员，输入可以是医生的问题，也可以是病例描述、检查报告加问题。系统需要提取已知事实和影响当前任务的缺失条件，检索适用的临床指南、药品说明书和医学文献，逐条解释结论、证据位置、适用条件，以及仍需确认的内容。

项目使用公开资料和合成病例做离线验证。当前题目为人工初标，尚未经医生复核。当前没有临床验证结果，也没有真实患者部署结果。

### 3.1 至少两类任务与一组跨来源任务

| 任务 | 要证明的能力 | 当前状态 |
| --- | --- | --- |
| 检查报告与指南匹配 | 从胸部 CT 文字报告识别筛查、偶发发现、检查目的缺失等场景，检索正确范围的证据并说明分流依据 | 已有小规模基线和单题生成实验 |
| 用药证据核对 | 特殊人群或合并用药问题；识别正确产品的说明书及章节，匹配指南条件，区分论文发现与指南推荐 | 已调研并拟定美国 HIV ARV／他汀相互作用；已有相关 SPL 和论文，NIH 本地来源受 403 阻碍，专项题未完成 |
| 指南＋说明书＋论文共同查证 | 发现当前来源不能回答的部分，并定向补查；保留不同来源各自支持的命题与适用条件 | 待规划题组和实现 |

第二类任务不预先拍定疾病、药物或地区。增加大模块或选定具体主题前，先查同类 GitHub 项目、产品或论文，核实数据和使用条件，再判断差异、标注难度、数据量与技术栈价值。

### 3.2 引用与不确定性是主线

- 报告中的事实需能回到原句、页码或截图区域；报告事实与外部医学证据分别管理。
- 每条医学结论需对应证据，保留发布机构、文件名、章节／表格／页码和原文链接。
- 说明书需保留产品记录身份及章节；论文需保留论文标识及证据类型。
- 来源发布日期、更新日期、版本、核验日期与实际采集时间分别记录，不相互替代。
- 病例缺少影响当前问题的事实时，追问具体缺什么；检索缺少证据时，定向补查资料。两者不能混为一张泛化的缺项清单。
- 仍不足时说明当前证据只能支持到哪里；来源分歧时分别说明条件。
- 项目转述、原文摘录、模型生成的结论保持区别，不能因附有官网链接就将转述称为原文。

CPython 文档版本回归属于另一个项目，不并入本项目主线。

### 3.3 多模态成品范围

输入需要从纯文本扩展到电子 PDF、扫描 PDF 和截图，包括 CT 等影像检查的文字报告。通过 OCR 或视觉模型提取字段并保留位置，重点核对数字、单位、否定词和左右侧。

使用同一份报告的文本版与图片版做配对对照，分别评估字段提取与下游判断。同一报告的不同展示版本不计为独立病例。原始 CT 体数据的病灶识别、测量或诊断可以另立项目验证，不作为本项目当前必做模块。

## 4. 参考项目与自身贡献

原始参考为 [JEen-wang/Adaptive-rag](https://github.com/JEen-wang/Adaptive-rag)，此前参考的 [固定提交](https://github.com/JEen-wang/Adaptive-rag/tree/2a12a62382a8c3ec033fa9a5b19b9b23b8780ab8) 为 `2a12a62382a8c3ec033fa9a5b19b9b23b8780ab8`。

此前交流中介绍的参考仓库能力包括 Python、FastAPI、LangGraph、BM25、稠密检索、RRF、Cross-Encoder、改写、多轮检索、引用、评测与日志；也包括电商交易工具、权限审批、React＋TypeScript 工作台、SSE 及多种 Docker 部署。本交接记录保留该参考关系，没有重新审计该提交中的每项实现。

本项目当前在独立练习目录实现，借鉴检索分层、状态流、评测与交付方式。以后复用源码时记录来源、版本、许可证和自己的改造。客服交易、权限审批、完整聊天工作台、多实例运维不自动成为本项目必做项。

任何介绍或简历描述都分别说明：

1. 参考仓库已有且经核对的能力。
2. 本项目计划实现的能力。
3. 用户已经自己实现、运行和评测过的能力。

当前可解释的贡献主要是手写检索基线、评测口径、证据与来源关联、基础 RAG 及失败样例对照。多源任务、自动适用性核验、Agent 补查与多模态证据链是后续贡献目标，暂不能写成已完成。

## 5. 当前环境与文件

当前工作目录：`/home/wzh/clinical-evidence-rag`。

Python：`/home/wzh/miniforge3/envs/all-in-rag/bin/python`，环境名 `all-in-rag`。不要假设终端默认的 `python` 可用。原先用户提供的 Mac 路径 `/Users/herdeny/Documents/ChatGPT/大模型学习项目/clinical-evidence-rag` 是历史位置，当前操作以上述 Linux 工作目录为准。

截至本次核对，环境有 pandas 2.2.3、sentence-transformers 5.7.0、torch 2.6.0+cu126、langchain 0.3.26、langchain-core 0.3.71、langchain-deepseek 0.1.4、python-dotenv 1.2.4、requests 2.34.2、beautifulsoup4 4.13.5、lxml 5.4.0。这是当前环境快照，不代替后续交付时需要整理的依赖文件。

2026-11-14 另核对已安装 pypdf 5.9.0、pypdfium2 5.14.0，未安装 PyMuPDF、pdfplumber。先以 pypdf 作电子 PDF 读取基线，不代表最终表格／OCR 工具已选定。

用户实验实际使用CUDA，并在可见终端完成GPU编码。成品模型按任务效果、领域／语言适配、可复现性及实际成本选择，不默认CPU或小模型；不能把CUDA单轮耗时写成CPU性能结果。API凭证通过环境变量管理，不把密钥写入文档、日志、Notebook输出或提交记录。

| 文件 | 内容与用途 |
| --- | --- |
| [data/sources.json](data/sources.json) | v1 的 5 条来源元数据，字段含 id、publisher、title、url |
| [data/evidence.jsonl](data/evidence.jsonl) | v1 的 15 张英文项目转述证据卡，字段含 id、source_id、text、locator，部分含 page |
| [data/cases.jsonl](data/cases.jsonl) | 12 道合成题：8 开发、4 留出；含报告、问题、场景组和人工初标 |
| [b0_practice.ipynb](b0_practice.ipynb) | 用户的纯向量检索与开发集评测练习 |
| [b1_practice.ipynb](b1_practice.ipynb) | 用户的 DeepSeek、上下文构建和基础 RAG 对照练习 |
| [data_v2_practice.ipynb](data_v2_practice.ipynb) | 当前的原始资料采集练习 |
| [data/v2/parsed/nci-lung-screening-pdq-hp.risk-factors.json](data/v2/parsed/nci-lung-screening-pdq-hp.risk-factors.json) | 用户提取并组装的单章记录；助手提供保存与读回辅助代码，已核对一致，可作后续函数回归样本 |
| [data/v2/parsed/nci-screening-overview-pdq-hp.purpose-of-summary.json](data/v2/parsed/nci-screening-overview-pdq-hp.purpose-of-summary.json) | 同一用户函数在第二份 NCI 页面提取的章节记录，1 个段落，助手辅助保存并核对读回一致 |
| [data/v2/parsed/acr-lungrads-2022.pages.json](data/v2/parsed/acr-lungrads-2022.pages.json) | 用户现有逐页读取代码输出，助手辅助保存的两页原始文本；未通过整张表结构核验或入库 |
| [document_parsing.py](scripts/data/document_parsing.py) | 助手按用户本次授权实现的编号分段及 Lung-RADS 注释适配，未代写后续 RAG 核心逻辑 |
| [data/v2/parsed/acr-lungrads-2022.notes.json](data/v2/parsed/acr-lungrads-2022.notes.json) | 16 条中间注释记录，含来源、页码、编号、原文字符位置；未自动修复文本或入库 |
| [tests/test_document_parsing.py](tests/test_document_parsing.py) | 6 项分段及溯源检查，已通过；仅一个真实 PDF 指定页及合成格式 |
| [results/data_v2_lungrads_notes_validation.json](results/data_v2_lungrads_notes_validation.json) | 输入、实现及输出指纹，验收结果、独立执行输出与适用边界 |
| [docs/pdf_extraction_comparison.md](docs/pdf_extraction_comparison.md) | 助手按用户委托完成的局部 plain／layout 对照，链接两种原始输出及第 0 类三行人工参考；不是自动表格解析实现 |
| [results/b0_dev_results.jsonl](results/b0_dev_results.jsonl) | B0 逐题输入、检索结果与指标 |
| [results/b0_dev_summary.json](results/b0_dev_summary.json) | B0 模型、配置、平均指标和计时范围 |
| [results/b1_dev01_top3_vs_all.json](results/b1_dev01_top3_vs_all.json) | DEV-01 Top-3／全量对照文本、统计和评审 |
| [data/v2/source_candidates.json](data/v2/source_candidates.json) | 7 条候选来源的类型、使用条件、日期、核验与采集决定；不是已入库语料 |
| [data/v2/README.md](data/v2/README.md) | v2 数据目录说明 |
| [docs/data_v2_plan.md](docs/data_v2_plan.md) | 来源核验、覆盖维度、格式处理及数据扩充安排 |
| [docs/engineering_issues.md](docs/engineering_issues.md) | 有证据支撑的工程问题、处理状态与面试复盘 |

早期曾按说明准备新建 `b0_practice.py`，当前实际核心练习保存在 Notebook，不应因为找不到该脚本而判断 B0 未完成。

## 6. 已完成的 B0

### 6.1 实现与配置

| 小步 | 用户已经完成的内容 | 验证情况 |
| --- | --- | --- |
| 读数据 | 用 pandas 读取 JSONL，检查卡片数、首条 ID 与正文 | 15 张，首条 LR_SCOPE |
| 加载模型 | 使用 SentenceTransformer 加载 BAAI/bge-small-en-v1.5 | 保存代码使用 device="cuda" |
| 向量化 | 对证据正文编码并做 L2 归一化 | 向量维度 384 |
| 相似度与排序 | 自己做向量点积和 Top-K 排序，整理卡片及得分 | 有独立查询 Top-1／Top-3 输出 |
| 检索函数 | retrieve(query, k) | 已用于单题和开发集 |
| 评测 | recall_at_k(retrieved_ids, gold_ids, k)，逐题统计与按 K 聚合 | 8 道开发题已复算 |
| 保存 | 逐题 JSONL 和摘要 JSON | 已保存并读回核对；保存辅助代码由助手提供 |

证据编码批量为 8，查询编码批量为 1。查询侧前缀为 `Represent this sentence for searching relevant passages: `，文档正文不自动加查询前缀。报告与问题使用固定模板：`Report: {report}\nQuestion: {question}`。这里的 `\n` 表示换行。

**报告属于检索查询的输入信息，当前没有作为指南证据混入被检索库。** 向量库中的对象是证据卡；模型回答时再同时接收报告、问题和检索到的证据。

归一化向量的点积用于本次相似度计算。相似度得分不是医学结论正确概率，也不是指南适用性证明。当前 retrieve 仍依赖 Notebook 中的全局模型、证据表与向量，不是已模块化的服务组件。

### 6.2 实测结果及边界

| 指标 | 8 道开发题的逐题平均 |
| --- | ---: |
| Recall@1 | 0.5625 |
| Recall@3 | 0.6875 |
| Recall@5 | 0.6875 |

每题 Recall@K 为前 K 个检索 ID 与标注 ID 的交集数量除以标注数量，再对题目取平均。它不是“至少命中一张卡的题目比例”，也不是医学回答准确率。

同一轮 GPU 检索平均约 5.95 ms，中位数约 3.07 ms。计时包含 retrieve 内的查询编码、相似度、排序和返回结果组装，包含首题，不含模型加载、外部打印与评测整理。没有做 CPU、并发、吞吐或多轮稳定性测试。

典型失败：DEV-01 的目标卡 `LR_SCOPE` 排第 6，得分约 0.692640；Top-3 为 `F_SCOPE`、`AC_INCIDENTAL`、`AC_RADIOGRAPH`，所以本题 Recall@3 和 Recall@5 均为 0。开发集 Recall@5 不完整的题包括 DEV-01、DEV-03、DEV-04。未用这批开发结果证明泛化或临床效用。

## 7. 已完成的 B1 与仍待完成项

### 7.1 当前实现

- ChatDeepSeek 已取得文字回复、token 统计和结束原因。
- 当前保存的模型配置为 `deepseek-flash`，API 地址为 `https://api.deepseek.com`，temperature=0，max_tokens=2048，timeout=30，max_retries=0，thinking.type=disabled。
- `max_tokens` 是输出预算，不是输入长度上限；这些是已保存代码的实验配置，不保证以后模型名称与接口保持不变，后续变更时再核验。
- `build_context(evidence_ids, evidence_df, sources)` 根据卡片 ID 找正文，再通过 source_id 找来源元数据，拼出证据 ID、机构、标题、定位、URL 和项目转述。
- 使用 ChatPromptTemplate 的 system／human 模板并调用 invoke。角色与占位符管理有助于组织输入，不会自动完成证据核验。
- 输入规则已强调报告事实与医学判断区分、每条判断引用、材料不足与病例缺条件区分，以及转述不能冒充原文。
- 当前 B1 **读取 B0 保存的检索 ID 做离线回放**，尚未验证每个新问题都实时调用 retrieve 的完整链路。
- 当前回答仍主要是自然语言；结构化输出、自动逐条支持检查、Agent 状态流均未实现。部分卡片有 page，但上下文构建还未完整展示这一可选字段。

### 7.2 DEV-01 证据量对照

问题询问本报告应该查哪套指南，以及决定选择的事实。报告明确为肺癌筛查项目中的基线低剂量 CT。标注的关键证据为 LR_SCOPE。

对照中使用同一报告、问题、模型对象和提示词，只替换证据上下文。全量组保留原三张卡在前，再追加剩余卡片，共 15 个唯一 ID。

| 统计 | Top-3 | 全量 15 张 |
| --- | ---: | ---: |
| 输入 tokens | 674 | 2128 |
| 输出 tokens | 970 | 1550 |
| 总 tokens | 1644 | 3678 |
| 输入中的缓存读取 tokens | 512 | 640 |
| 结束原因 | stop | stop |

全量组总 tokens 约为 Top-3 的 2.24 倍。这不是费用比例，缓存读取已经包含在输入统计中。

实际观察：

1. 初版 Top-3 在没有对应证据时补出了具体指南名。后续主要结论更明确地承认材料缺口，单独标记候选线索。
2. 全量组拿到 LR_SCOPE 后能引用它给出具体框架名称，支持“本例关键证据缺口影响生成”的解释。
3. 两组仍扩展到具体分类、随访和风险信息，未解决围绕当前问题控制任务范围的问题。
4. 全量组出现条件转述偏移和证据范围串用：将“正在调取既往影像”放宽为“有对比影像”，将多发结节条款用于单发病例等。
5. 全量回答仍未完整展示所有原文链接等来源信息，不能算全部引用要求已满足。

这是单题、单次对照，不能推断所有错误都来自检索，也不能证明全量输入始终更好。小语料全量输入继续作为诊断对照，不算新增检索算法。

相关历史文件包括 [初版](results/b1_dev01_top3_initial.json)、[后续保存输出](results/b1_dev01_top3_followup_01.json)、[用户最新单次提交](results/b1_dev01_top3_user_reported_02.json) 和 [成对对照](results/b1_dev01_top3_vs_all.json)。不同输出不能混为一次调用。

### 7.3 B1 待办如何安排

DEV-01 最小闭环到此收尾，失败项保留。当前先扩 CT 数据，之后在同一数据版本上补批量生成评测、实时检索链路和必要的调用日志。不要继续反复调整 DEV-01 提示词，把一题改到完美作为扩数据的前置条件。

## 8. CT 数据 v2 的现状和格式方案

### 8.1 来源状态

现有 v1 来源涉及 ACR Lung-RADS、Fleischner、ACR 偶发结节影像适宜性标准和 USPSTF 筛查建议。v2 候选清单在原有 5 条基础上增加两份 NCI 专业人员版 PDQ 证据综述，共 7 条记录。两个 ACR Lung-RADS 记录分别为入口页与 PDF，不能仅按记录数推断独立指南数量。

第一轮核验已记录于 2026-11-12：

- ACR Lung-RADS 入口当时链接到 v2022 PDF；具体复用条件待继续核对。
- Fleischner 官方页当时可读，但免费可读不自动等于可打包再分发。
- ACR 偶发结节 Narrative 当次访问返回 403，动态页面版本未重核；ID 中的 2023 不证明当前页面版本。
- USPSTF 页面有带条件的复制说明，需按实际使用方式处理。
- NCI PDQ 有明确文字复用说明，例外、图像和标识另行处理；其类型是 evidence_summary，不能当正式临床指南。

首份计划采集样本为 `nci-lung-screening-pdq-hp`，作为采集解析练习和筛查背景证据。NCI 综述不会代替 ACR／Fleischner 原始条款。来源使用条件与访问结果是截至核验时的记录，不在每次代码练习中反复做无关核验。

### 8.2 当前采集练习的真实状态

保存的代码已读取清单、循环请求、读取 Content-Type、对 HTML 提取标题，并计算下载字节及保存文件的 SHA-256。当前源码已按 HTML／PDF 设置后缀，但未知类型以及 HTML 缺少 title 时的后缀分支尚未完善。请求阶段已捕获 RequestException，追加失败记录并 continue，保存输出显示后续来源仍被处理。

用户最新提交的失败记录含 id=fleischner-2017、数字 status=403 和可读 exception_message，失败记录验收通过。先前状态对象和错误方法对象的修正到此收尾。当前源码的汇总打印已移到循环外；Notebook 某些单元格可能仍留有更早展示，不以其否定用户最新明确提交。这里作为练习进度记录，不单独列为面试工程问题。

本次本地检查见到六个原始文件，其字节数和 SHA-256 与保存的成功输出一致：

| 本地文件 | 字节数 | 内容特征 |
| --- | ---: | --- |
| data/v2/raw/acr-lungrads-scope.html | 155519 | HTML，标题为 ACR Lung-RADS 入口 |
| data/v2/raw/acr-lungrads-2022.pdf | 665034 | 以 %PDF-1.7 开头，内容和保存后缀为 PDF |
| data/v2/raw/acr-incidental-2023.html | 275180 | HTML，title 为 Preview，h1 为 Incidentally Detected Indeterminate Pulmonary Nodule；版本仍待核对 |
| data/v2/raw/uspstf-screening-2021.html | 148549 | HTML，标题与肺癌筛查推荐相符 |
| data/v2/raw/nci-lung-screening-pdq-hp.html | 124323 | HTML，title 和 h1 与肺癌筛查专业人员版相符 |
| data/v2/raw/nci-screening-overview-pdq-hp.html | 91538 | HTML，title 和 h1 与筛查概述专业人员版相符 |

文件名与当前数量是交接时快照，用户后续可修改。NCI 肺癌筛查页已满足原始采集样本的 HTTP 200、正确标题、非空文件和保存前后指纹一致要求；用户随后已提取 Risk Factors 单章正文与锚点，尚未完成全页解析和统一证据输出。不是全部 7 条来源下载成功，也没有完成重试、断点续采或全部失败场景测试。

此前用户提交：requests 请求 `https://pubs.rsna.org/doi/full/10.1148/radiol.2017161659` 后，raise_for_status 抛出 HTTPError，状态为 403。它说明该次请求被拒绝，不能仅据此确定具体访问策略，也不等于此前其他客户端核验到的页面可读状态虚假。最新运行已经继续下载后续来源，失败列表详情已由用户提交并通过。不删除状态检查、不将错误响应当正文保存、不反复盲目重试 403。ACR 偶发结节页面此前核验返回 403，本轮用户实际请求成功返回 200；两次观察分别保留，版本和内容仍需正文核对。

Notebook 保存的旧输出仍有错误，而当前源码部分写法已变化；不能仅凭历史错误断定当前代码还会同样失败。来源文件已经采集到本地，也不等于已通过正文核对或加入检索索引。

### 8.3 多格式统一方案与此前小步记录

本节保留早期接口和解析练习的背景。现已由本轮批量准备实现 HTML／PDF 的共同证据输出，最新范围、数量及排除项见 8.4；OCR、通用站点适配及 PDF 复杂表格仍未完成。

采集阶段可共用请求、状态检查、字节保存和指纹计算。读取阶段按格式分支：

| 格式 | 解析结果 | 定位 |
| --- | --- | --- |
| HTML | 过滤导航等内容，提取正文和标题层级 | 章节路径、实际存在的锚点、本地段落标识 |
| 有文本层的 PDF | 按页提取正文，检查阅读顺序及表格关系 | 从 1 开始的文件页码，必要时为区域坐标 |
| 扫描 PDF／截图 | 后续 OCR 或视觉解析得到字段和文本 | 页码、图像坐标 |

不同解析器计划输出同类证据块，保留 `id`、`source_id`、`text`、结构化 `locator`。原始路径、内容指纹、最终 URL、Content-Type、实际采集时间等保存于采集记录中。完整字段在实现时逐步确定，不直接覆盖 v1 的字符串 locator。

source_type 表示指南、推荐声明、说明书、论文、证据综述等证据性质；Content-Type 表示 HTML、PDF 等文件格式，两者分别记录。

HTML 不编造页码或不存在的锚点。没有直接锚点时，用章节及本地段落标识辅助回查，不能冒充精准网页锚点。分段后继承原始位置，不只保存一大段丢失结构的纯文本。扫描件处理工具需经样本对比后选择，目前未定。

当前 NCI 样本的本地结构已由助手检查：唯一的 main 元素 id 为 main-content，其内有一个 article；h1 为 Lung Cancer Screening (PDQ®)–Health Professional Version；前三个 h2 为 Overview、Incidence and Mortality、Risk Factors。2026-11-13 用户代码已将 h1_text 和 section_titles 转为纯文字。助手只执行保存的本地解析单元格，确认主标题为 str、章节元素均为 str，前三个名称正确；保存的旧标签输出不再作为当前状态。

用户已完成结构较简单的 Risk Factors：h2 的外层 section id 为 _222，含 2 个 p 段落，无嵌套 section；已形成原始页面 URL 加 #_222 的章节链接。解析期间保留 h2 标签对象用于查父元素和属性，另存标题字符串用于展示和序列化。get_text 返回新的字符串，不修改原标签；不覆盖后续还要使用的标签列表。用户已将提取结果组装为含 source_id、section_title、section_id、paragraphs、section_url 的字典，section_url 也已校正为带锚点链接。

助手只追加了保存与读回辅助单元格，没有代写记录构造；实际保存验证在独立 Python 进程执行，新增 Notebook 单元格不伪造执行次数或输出。结果保存在 data/v2/parsed/nci-lung-screening-pdq-hp.risk-factors.json，读回与用户生成的记录完全一致。该文件是 1 条供后续分段和函数回归使用的中间章节记录，不是已加入检索库的新证据卡，也不代表全页正文、表格和参考文献均已处理。

用户已将现有代码封装为 parse_nci_section(html_path, source_record, target_title)。2026-11-14 助手以两份页面和两个失败分支完成独立调用核对，均通过。文件路径、来源字典和目标标题确实通过参数切换，未沿用旧来源；当前验证为 Path 输入、两个结构简单的 NCI 章节。全页中的嵌套、列表、表格和参考文献仍需后续处理。

电子 PDF 使用 pypdf 5.9.0 作读取基线。用户已构造逐页记录，实测为 2 页、普通模式 4322／7770 字符，第二页以 NOTES 开头。2026-11-16 当前源码来源 ID 已修正，助手执行用户现有本地 PDF 单元格并将页记录保存为 data/v2/parsed/acr-lungrads-2022.pages.json，读回一致。页文本仍是未经完整结构核验的中间产物。

助手已将原 PDF 第一页渲染为 [原页预览](data/v2/previews/acr-lungrads-2022.page-1.png)。用户于 2026-11-16 明确委托助手比较并给出正确参考，助手保存第一页 plain（4322 字符）和 layout（24744 字符）输出并对照原图：第 0 类三组内容在两种模式中均可人工对应；layout 仍有词语粘连，两种输出均有 3 处 /uni00B3，也均未显式输出第 1／2 类共用处理单元格的关系。因此保留普通模式作中间基线，未建立自动结构恢复、自动单位修复或下游收益结论。第 0 类三行人工参考另存，包含指向第二页注释 9／10 的关系；该参考及预览不算新增检索卡或报告多模态评测病例。详情见 [对照报告](docs/pdf_extraction_comparison.md)。原始 PDF 与两种提取均保留，不用归一化覆盖原文。随后用户授权助手实现编号注释步骤，现已保存第二页 16 条注释并通过分段和溯源验证；医学文本仍需逐条核对，下一步统一候选证据格式。第一页表格结构另行恢复，最终表格工具未选定。接口说明见 [pypdf 5.9.0 文字提取文档](https://pypdf.readthedocs.io/en/5.9.0/user/extract-text.html)。

2026-11-13 用户质疑“只能处理 NCI 的函数有何封装意义”。设计判断：站点专用解析可作为隔离结构差异的适配器，封装的收益应通过多个文档复用及统一输出验证，不能只把一次性脚本包成函数就算项目贡献。本地对比已确认两份 NCI 都有 main#main-content、article 和带 id 的 section；USPSTF 的正文主要用 h3 和表格，ACR 偶发结节页没有 article、含多张表格。不能把 NCI 的 h2／section 规则直接宣称为所有 HTML 的解析规则。

成品的统一边界仍是格式识别与外层解析入口、证据数据结构及下游检索引用。HTML 保留必要的站点规则，PDF 保留按页或区域定位；解析得到的正文、来源和位置再进入共同分段及检索流程。未来可设计 parse_document(path, source_record) 统一分派，当前未实现，也不先引入复杂注册框架。若来源规模扩大，再用多源样本比较通用抽取工具与规则适配的取舍。

### 8.4 本轮批量交付已取代上述小步待办

用户要求一次性完成扩数据后，助手基于现有 6 份本地快照完成批量适配、分块、统一结构、去重与溯源验证。NCI 和 USPSTF 提取正文与附属列表，ACR 偶发结节保留原表格行及完整 Variant 场景，PDF 注释完整保留子项。HTML、PDF 的位置含义分别记录，不把规范化文本偏移冒充图片坐标。

实际 241 条候选，238 条本地检索输入，最长 434 tokens；3 条隔离。原 v1 未混入。本轮数据快照版本为 ct-v2.0-draft，已记录所有数据文件指纹，重复离线构建一致。48 道 AI 初标题按 24 个家族划分为 32 开发／16 留出，没有用检索结果或模型答案反推标签。

这不代表全部医学文字已独立复核或原文可公开分发，也不代表复杂 PDF 表格、Fleischner 全文、用药与多模态已完成。下一步进入新语料的向量基线，详细结构、评分口径及边界见 data/v2/DATA_CARD.md；不要恢复到旧的 18 条候选练习。

## 9. 数据量规划与划分

| 阶段 | 累计证据目标 | 累计评测目标 |
| --- | --- | --- |
| v1 已有基线 | 15 张项目转述卡，5 条来源 | 12 道合成题：8 开发、4 留出 |
| CT v2 本轮实际交付 | 238 条本地检索输入、6 份来源快照；另有 3 条隔离候选 | 48 道 AI 初标题：32 开发、16 留出，24 个家族 |
| CT v2 | 约 100–300 个有定位的证据单元 | 约 40–60 道文本题 |
| 加入用药和论文任务后 | 约 300–1000 个证据单元 | 约 100–200 道题，含两类任务和三来源补查题组 |
| 多模态配对 | 约 20–30 份基础报告的多种展示版本 | 记录基础报告数和版本数，分别评估 |

表中本轮实际交付为已构建和检查的数量；其他目标仍为工作量规划，不是保证数量或临床验证门槛。不能把完整性依赖很强的条款任意拆成大量小块凑数。文档数、来源记录数、证据块数、题目数、病例家族数、图片版本数分别统计。

此前提及的 7663 项来自 [MIRAGE 外部问答基准](https://github.com/gzxiong/MIRAGE)，指评测问题规模，不是本项目文档数或需自行标注的卡片数。用户于 2026-11-17 再次明确对标预期：外部基准接入改为明确待办，全量 7,663 题作为外部评测目标；原始题库现已下载核验，尚未运行模型评测。其选择题准确率与本项目的报告条件、逐条引用和澄清指标分开报告。需要覆盖相应医学主题的更大检索语料，不能用 CT 的 238 条支撑全基准，也不能以自合成七千题替代它。原专项 300–1000 条目标不作为系统总索引上限，详见 docs/benchmark_scope.md。

### 9.1 数据覆盖

CT v2 按任务和关键条件构建覆盖：指南框架选择、条款解释、筛查资格与具体分类的区别；筛查／偶发／目的缺失；年龄、已知肿瘤、免疫抑制；胸部 CT／胸片／部分胸部成像；既往影像正在调取／已有可用影像／未说明；单发／多发等。

补充只有关键条件不同的成对样例，检查模型是否保留触发条件。每道题只要求来源真正支持的命题，不能凭一张卡推出整个临床管理流程。多模态阶段另测数字、单位、否定词和左右侧。

### 9.2 标注与划分

- 所有标准答案、证据 ID、适用条件和定位都需回到来源核对；允许先保留未知，不先生成肯定答案再找支持。
- 先登记病例家族与场景组，再整体划分开发和留出；关键条件变体、改写及图片版保持同组。
- 不把已经调试过的 v1 开发题重新算作未见过的留出题。
- 原 4 道留出题不用于提示词调整、改写设计或错误驱动开发；必要时只统计划分元数据，不展示题目内容用于调试。
- 人工初标状态明确保留；增加样本数不会自动得到医生复核或临床有效性。
- 标注答案与 gold_evidence_ids 留在评测侧，不进入检索、改写或模型生成的输入。

## 10. 分步路线与每步验收

推进主线为：**B0 → B1 最小闭环 → CT 数据 v2 及基线复测 → 广泛医学语料批量扩充与新版本基线 → BM25＋RRF → 重排 → 查询改写 → 证据核验与有限补查 → 用药、论文、多模态任务 → MIRAGE 全量对标及服务化交付。** 外部基准、检索语料、许可及评测协议提前准备，避免功能完成后才发现无法公平比较。最终项目必须同时交付专项产品验证与公开基准对照，核心实现继续由用户完成。

此处列的是总体任务清单。用户已要求将数据准备整批完成，该阶段不再拆成字段级练习；之后核心教学按完整、可验收的工作单元推进，等待用户代码与输出，不擅自代写检索或 Agent。

### 10.1 当前阶段：CT 数据 v2

| 顺序 | 用户自己实现或完成的任务 | 验收标准 | 状态 |
| --- | --- | --- | --- |
| 1 | 来源筛选、类型和使用条件核验 | 来源有官方入口、类型、核验日、使用条件和采集决定 | 第一轮 7 条记录已建立，仍有待核验来源 |
| 2 | 原始资料采集与格式识别 | 指定来源身份正确；HTTP 成功；Content-Type 与内容相符；按格式保存；读回字节一致 | 本轮 6 份成功、1 条失败已验收；未知类型等通用分支仍待补 |
| 3 | HTML 正文提取 | 检查标题和若干原文段落；排除导航页脚；保留章节与实际锚点 | 用户 NCI 单章函数验证通过；助手在批量阶段完成现有正文与列表及表格适配，原始元素定位已检查；不宣称支持所有网站结构 |
| 4 | 电子 PDF 按页解析 | 页数、页码和样本文本可核对；检查表格与脚注关系 | 用户逐页读取完成；助手保存两页结果、完成局部 plain／layout 对照，并按授权实现及保存 16 条编号注释，通过 6 项检查；第一页表格结构待恢复 |
| 5 | 输出统一证据块与采集记录 | source_id、正文、定位可回到原文件；日期和来源身份不混淆 | 助手按批量授权完成，238 条检索输入及来源快照记录已保存 |
| 6 | 按自然条款和段落分段、去重与核对 | 条件、否定、表格关系和定位未丢失；统计实际有效数据量 | 已完成机器溯源、长度、表格场景与隔离检查；医学内容仍非独立临床复核 |
| 7 | 构建病例题、标准证据与场景组 | 目标命题可被原文支持；正负或缺条件样例有明确预期 | 48 道助手初标草稿、24 个家族已交付，gold 均可回查；待独立人工复核 |
| 8 | 按家族划分开发／留出并固定数据版本 | 无改写、图片或条件变体跨集泄漏 | 草稿快照及指纹已固定，32／16 题、家族不跨集；正式标注复核后更新数据版本 |
| 9 | 重跑纯向量检索与基础 RAG | 新旧数据结果分开；保存逐题 trace、指标及失败类型 | **新语料纯向量检索已完成并核验；下一步固定数据 BM25／RRF；B1 批量生成与实时链路后续补齐** |

下载记录用于保证来源可回查，不把完善通用爬虫、登录绕过或浏览器自动化作为当前扩数据的前提。发生不可用来源时按任务价值选择公开可用的替代入口，并保留访问状态。

### 10.2 BM25＋RRF

当前具体实现约定及完整任务见 [BM25 单独基线](docs/bm25_baseline_task.md)。先完成该固定配置的 BM25 实测，再定义并实现 RRF 的候选预算；不同时调参、换数据或改写查询。

1. 在相同证据集合上建立 BM25 检索，输出统一的证据 ID、排名与得分。先单独评估 BM25。
2. 实现 RRF 融合稀疏与稠密结果，按排名融合并合并重复证据；不要直接把尺度不同的原始得分相加。
3. 固定最终 K 和候选预算，对比纯向量、BM25、RRF。逐题看漏检是否改善，以及是否引入新的错误。
4. 验收为结果可复现、实现可解释、指标口径一致；结果不提升也据实记录，不能为正向结论改题或改 gold。

### 10.3 重排

1. 先核对候选Cross-Encoder的任务适配、公开评测和许可，再以固定候选集做效果对照并记录GPU／API成本；不默认选择轻量模型，具体候选与进度见docs/reranking_task.md。
2. 对固定的候选前 N 条重排，再返回最终 K 条；保留重排前后排名。
3. 同时检查候选召回与最终 Top-K，区分“未进候选”和“进入后排错”。
4. 验收证据适用性、引用支持关系和延迟变化，不能仅看文本相似度或一题排序。

### 10.4 查询改写

1. 根据报告和当前问题生成检索表达，保留原查询和改写结果。
2. 不新增报告没有的人群、数值或检查目的，不把标注答案或未经核验的医学结论塞入查询。
3. 与原查询在相同数据和预算下对照，统计额外调用、tokens、延迟及逐题变化。
4. 验收既看召回，也看病例条件是否被改写丢失或改变。

### 10.5 借鉴 Self-RAG：核验与有限补查

这里借鉴“检查证据再决定继续”的思路，不等于训练或复现了 Self-RAG 模型。

1. 设计结构化结果：当前任务、已知事实、待确认条件、逐条结论、引用证据、适用条件、证据不足原因。
2. 分别检查引用是否存在、结论是否被引用支持、适用条件是否匹配；不能只做 ID 白名单检查。
3. 将病例缺条件分流到具体追问；证据缺口分流到定向补查；无关条件不作为当前任务前置要求。
4. 用 LangGraph 表达报告解析、检索、适用性核验、补查、追问和停止。业务工具围绕指南、说明书、论文和报告原文，不移植客服交易工具。
5. 限定补查轮次、调用数或预算，保存停止原因；具体阈值通过开发题确定。重复无增益或证据仍不足时，说明支持边界。
6. 用确实需要补查的题目验证，比较单次检索和有限补查，统计成功、失败及成本。

Agentic RAG 的预期价值是根据问题和证据缺口选择下一步，而不是增加一个框架名称。需通过“补哪类来源、补什么条件、为何停止”的 trace 证明其作用。当前尚无上述 Agent 实现或收益结果。

### 10.6 用药、论文与三来源任务

1. 研究同类项目、产品或论文，选定任务主题及目标地区。
2. 核实指南发布机构、说明书产品记录身份、论文可获取范围及逐篇使用条件。
3. 候选入口包括 [NIH 用药相互作用指南](https://clinicalinfo.hiv.gov/en/guidelines/hiv-clinical-guidelines-adult-and-adolescent-arv/drug-interactions)、[DailyMed API](https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm)、[PMC Open Access Subset](https://pmc.ncbi.nlm.nih.gov/tools/openftlist/)。找到入口不等于已采集到足够的可用文档。
4. 设计有明确产品、章节、人群或合并用药条件的题目，核对 gold 和标注成本。
5. 接入第二类任务，沿用共同检索与核验流程，用结果证明可复用。
6. 再构建需要指南、说明书和论文共同查证的题组，区分研究发现、产品说明与指南推荐，验证跨来源补查。

### 10.7 报告多模态输入

1. 准备可使用的合成或公开报告，保留对应的文本事实与区域标注。
2. 制作或收集同一基础报告的电子 PDF、扫描件、截图版本，保持同组。
3. 在样本上比较 PDF 提取、OCR 或视觉模型后选工具，保留失败和字段置信不足的状态。
4. 对关键字段保存原文位置，逐项检查数字、单位、否定词和左右侧。
5. 分别评估字段提取与下游任务；比较文本版／图片版，区分识别错误与推理错误。
6. 验收完整证据链：报告事实能回到原文位置，医学结论能回到外部来源。

### 10.8 服务与交付

1. 持续复用当前阶段开始建设的 Python 核心模块和正式基线运行脚本，脚本作为当前命令行入口；后续 FastAPI 调用相同核心模块，不再为服务化重新实现检索和评测。
2. 使用 Qdrant 保存索引及来源类型、地区、适用场景等元数据，验证过滤行为。当前尚未建立 Qdrant 索引。
3. 使用 FastAPI 暴露查询与报告处理能力，输出结构化结果及引用；接口细节在核心流程稳定后确定。
4. 使用 SQLite 保存题目、运行与评测记录，加入结构化日志及逐题 trace。
5. 保存实际消息、模型与检索配置、数据版本、响应、tokens、耗时和停止原因，保证对应同一次运行；不记录密钥。
6. 用 Docker 单实例交付，给出复现步骤、样例输入、评测报告、错误对照与明确限制。
7. 整理本人贡献、引用来源和面试说明。演示重点是医疗证据链及错误改进，而非电商工作台或多实例运维。

### 10.9 MIRAGE 全量对标：最终必做

1. 接入原始 7,663 题与五个子任务，保留版本、来源及使用条件；准备足够覆盖主题的检索语料，记录实际规模和数据指纹。
2. 使用独立开发材料联调，估算成本；不将基准测试题作为反复调参的开发集。检索只接收问题，选项可用于生成，答案及给定支持上下文只用于评测。
3. 固定一组主要实验配置，在同一模型、数据和输入协议下完整比较无检索、公开可复现的基础 RAG 设置及本项目改进 RAG；所有设置差异显式记录。
4. 报告五个子任务准确率及宏平均、延迟、tokens、调用数、费用和失败情况；保留逐题输入、检索、回答与评分记录。不能把只下载、建索引或部分题运行写成完成对标。
5. 提供复现入口与结果报告，解释实际改进和失败；不同模型或语料下与论文分数的比较需标注条件，不预先承诺超过原工作。

此验收项当前尚未实现。详细口径见 [对标范围与验收](docs/benchmark_scope.md)，不因当前 CT 阶段完成而删去或改成可选项。

## 11. 已定技术栈与尚待验证的工具

| 层面 | 当前实际状态 | 已定方向与后续增量 |
| --- | --- | --- |
| 数据 | Python、pandas、JSON／JSONL；CT v2 已有来源快照、证据及位置、场景家族划分 | 沿用统一证据结构，扩充来源与任务；新增字段兼容已有记录，正式标注复核另记版本 |
| 向量检索 | B0 已实测 SentenceTransformer＋BGE-small；HuggingFaceEmbeddings 接口及 CT v2 开发集新基线已实现并保存实测 | 现在与成品统一使用 LangChain Embeddings 接口；手写相似度／Top-K；后续增加 BM25、RRF、重排、改写、Qdrant 与元数据过滤 |
| LLM | LangChain＋ChatDeepSeek，提示模板和自然语言输出 | 结构化输出、逐条支持与适用性核验 |
| Agent | 尚未实现 | LangGraph 状态流、有限补查、追问与停止 |
| 解析 | 用户采集／局部解析，助手获授权实现当前来源批量处理、统一证据与位置验证；复杂 PDF 表格及 OCR 未完成 | 保持统一证据输出；站点与格式适配可增量加入；尚未确定的表格／OCR 工具需真实样本验证后选择 |
| 交付 | 已有 Notebook、结果 JSON／JSONL、Markdown；新核心模块已有用户初稿，待修正与验收 | 复用核心模块增加 CLI、FastAPI、SQLite、结构化日志、Docker 单实例、可复现报告 |

B0 直接调用 SentenceTransformer 是已完成的历史实现；新代码从当前阶段起统一使用 langchain_huggingface.HuggingFaceEmbeddings 的 embed_documents／embed_query，后续沿用相同接口。没有换用 LlamaIndex 的要求，不为了框架数量更换已定方案。这里列为后续的组件是尚未实现的增量功能，不是允许以后随意更换现有实现标准。

当前没有必做的微调环节。先建立可评测的检索、证据核验与任务闭环；以后若真实失败样例表明需要，再研究 embedding／reranker 或模型微调，先确认训练数据、独立评测与资源。现有 15 张卡、12 道题不作为足够的训练集。

[RAG_Techniques](https://github.com/NirDiamant/RAG_Techniques) 中的 Contextual Chunk Headers、HyPE、ColPali 等已被讨论过，留到主线完成后考虑，不提前加模块。

## 12. 评测规则与证据边界

每次只改一个因素，在相同数据版本、题目、输入模板、模型配置和最终 K 下做比较。扩大语料后先重跑基线，再比较算法；不能把 v1 和 v2 的差异直接归因于算法。

需要逐步覆盖的指标包括：Recall@K、指南选择、引用定位、逐条结论支持、缺条件时的澄清表现，以及延迟、调用次数、tokens 和费用。当前已完成 v1 B0 与 CT v2 开发集召回率及单轮检索计时；B1 有单题输出及 tokens，不存在完整的自动医学判断评分体系。

每个新增指标都要先写清计分单位、分母和适用题目。例如“缺条件时的澄清率”需在确实缺必要条件的题上统计，并同时观察不必要追问；“引用 ID 合法”不能代替“结论受到支持”。支持率的人工判断与自动评分要分别标明。

逐题至少区分：

- 漏检：目标证据未进入候选或最终上下文。
- 用错证据：来源或条款被检索到，但人群、场景、触发条件或任务不匹配。
- 无依据生成：出现上下文不能支持的名称、结论或建议。
- 任务范围错误：回答或追问扩展到当前问题不需要的事项。
- 解析错误：报告或来源文字、数字、单位、否定、左右侧被误读，原文位置丢失。

保留全量小语料输入作为诊断对照。日志对实际输入与响应的绑定、运行次数和来源格式需诚实标记，用户粘贴的展示文本不冒充原始 API JSON，当前源码也不冒充历史请求时消息。

## 13. 我们的合作方式：后续必须遵守

### 13.1 用户写核心代码

用户希望自己理解并实现核心逻辑。助手可以解释概念、函数接口、参数含义、选择理由、少量用法示例和验收标准；不要给出能直接填满练习的整段核心答案，也不要直接改写用户的检索、评测、上下文构建、解析或 Agent 主逻辑。

用户明确反馈过：提示若太接近完整答案，就失去练习价值。解释要能帮助用户自己推导；打印语句几乎不影响练习，助手可以直接提供。

### 13.2 助手可直接处理的辅助工作

用户于2026-11-19补充要求：助手编写的项目代码逐行提供中文解释；可删除无用的一次性.py，但应先记录输入来源、操作步骤、命令／参数、验证和产物。已有下载／重建／核验脚本仍有复现用途，应集中管理而不是盲删；历史快照不改写。核心逻辑继续由用户实现，注释或清理不代表助手可以代写核心函数。

用户已授权助手提供输出语句、结果保存辅助代码、文档与工程复盘记录，并要求持续检查代码。用户曾明确说“保存这步你来写吧”。这不代表授权代写后续所有核心模块。

章节记录的字段组装、来源关联与位置对应属于用户练习的核心逻辑；助手可以辅助其后的写文件和读回核对。用户说“继续”时，先给一个目标、必要接口及验收标准，不能直接修改核心代码来完成练习。

本文件及其他交接文档由助手维护。新的核心任务仍由用户写，除非用户明确改变合作方式。

2026-11-16 用户明确委托“这个你来比较吧，然后给我正确的”。该次授权用于助手完成 plain／layout 对照、保存输出与正确的局部人工参考；不推定用户将后续解析器、分段、检索等核心代码一并交给助手。

同日用户进一步明确“你来写这一步吧，感觉跟 rag 关系不大”，授权助手完成当前编号注释的分段、来源位置继承、保存和验证。该步骤已实现并标注为助手贡献。后续教学重心回到证据构建、检索、评测与 Agent；不将本次授权扩大为代写这些核心模块，也不再要求用户重写已经由助手完成的编号分段。

用户随后要求“扩数据一次性搞完，不要挤牙膏”。本轮明确按整批数据准备执行：助手完成现有资料批量解析、统一证据、质量检查、场景划分与 AI 初标题；撤销旧的 18 条候选构造练习。本次不替用户编写向量检索、评分或 Agent，不将 AI 初标写成人工或医生复核。后续不要重复要求用户重做这批准备工作。

### 13.3 按完整工作单元推进

用户已明确反对数据扩充挤牙膏式推进；数据准备阶段本轮已整批交付，不再让用户逐张拼记录或反复做格式小步。核心教学说明完整工作单元的目标、接口、理由和验收，等用户代码与输出后检查。用户说“好了”“写完了”“ok”时，结合上下文去查看对应文件和结果，不因没有粘贴完整代码而直接跳到下一阶段，也不反复让用户重发本地已有内容。

检查顺序为：当前代码做了什么、最新输出显示什么、是否达到本小步验收；有问题先解释原因，让用户自己修正。用中文、完整段落，避免几个字就换一行。

拆步之前先明确当前产物会如何接入随后步骤。至少说明本步用途、要保留的信息和验收结果，避免只为打印设计变量、下一步又重新推翻。小的输出或字段修正随当前任务处理，不机械地把每一行修改都拆成新阶段；仍遵守用户写核心代码的要求。

### 13.4 尊重输出时点，避免重复消耗

用户明确提交的当次输出作为本次运行的证据；Notebook 的保存输出和当前可编辑源码可能来自不同执行状态。发现不一致时先核对对应关系，不把旧错误直接归到当前代码，不单凭 token 数相同认定提示词没有运行。

此前助手把历史输入 token 数当作主要排障依据，造成了不必要的检查；已纠正。用户随后提交的 674 输入／922 输出／1596 总 tokens 是另一份有效单次结果，不能与成对实验 Top-3 的 674／970／1644 混淆。不要为追查助手自己的错误反复要求用户调用 API。

### 13.5 哪些问题记录到面试复盘

只记录涉及系统设计、证据质量、任务边界、评测可信度和可复现性且有实际依据的问题。例如：引用存在却不支持结论、条件串用、缺信息与缺证据分流、证据预算变化的利弊、实验比较是否可信。

语法、索引、切片、DataFrame 用法、基本类型和单行拼接等练习错误，现场讲解并修正，不包装成工程案例。用户已明确纠正过这一点；此前对应的基础错误条目已从工程记录删除。编号空缺不表示遗漏必做任务。

复盘记录区分现象、原因假设、已做修正、未做方案及复测结果。尚未实现或测过的解决方法不能写成自己的成功经验。

### 13.6 调研、决策与范围控制

新方向或大模块前先核对同类工作、数据、使用条件和差异。常规小步不反复打断询问权限，不为了增加技术名词扩大项目。对已有授权范围内的文档、检查和辅助工作继续完成。

当前目标是完成有独立贡献、可复现、有错误分析的项目。遇到真实限制时说明限制和可执行的下一步，不用无法兑现的数据规模、模型微调或 Agent 名称替代实测。

### 13.7 导师职责与前后步骤的衔接

用户在 2026-11-13 明确要求：每一步指令都要考虑后续用途；助手作为导师独立判断，不是用户提出什么就附和什么。

助手需从最终任务与证据链倒推当前设计，提前检查接下来几个步骤的依赖。例如 HTML 解析既需要标签结构取得章节位置，也需要字符串用于 JSON、向量化和回答；合理做法是同时保留对象与字段值。不能为了一个输出验收覆盖结构，又让用户下一步重新查找。此前标题练习在这点上说明不足，后续按这一规则纠正。

对用户提出的技术改动，先核对其前提、收益、代价及对整个流程的影响，再给明确建议。不合理时说明原因和可验证的替代方案；证据不足时说明需要验证什么，不用无依据的赞同或反对代替判断。用户偏好与授权予以尊重，技术事实和方案选择仍需保持独立判断。

用户再次质疑专用解析函数的泛化性后，后续明确区分：输入参数可替换、某类结构的规则可复用，以及已在其他真实文档验证，是三种不同程度。站点或文档适配器可以存在；可复用机制与统一输出应有清晰边界，不能仅通过增加参数宣称已具备泛化能力。当前编号分段工具只面向阅读顺序可用、按行编号的文本，不扩称为表格、扫描件或所有 PDF 的统一解析器。

教学任务要形成可复用的产物，例如带来源和位置的章节记录，而不是停留在打印结果。提前设计范围以支撑已确定的后续步骤为限，不为假想需求扩建大框架，也不跳过必要的学习和验收。

### 13.8 全部任务按成品方向增量开发，保持标准连续

用户于 2026-11-17 明确强调：“其他任务也是一样，我们现在就在做项目，不要总是改标准。” 这是全项目约束，覆盖模型接口之外的全部任务，不能只记录成一次库选择偏好。

- 每次布置任务前，依据现有成品架构确定它所在的模块、输入输出、后续调用方式和验收。使用已定的库、接口及证据结构，不安排教学专用的临时实现再要求重写成正式版本。
- 分阶段增加功能与数据，复用已实现的核心逻辑；新增交付流程采用按职责命名的 Python 模块与运行脚本，Notebook 保留为历史实验记录或可选排查工具。数据扩充更新数据、向量和运行结果，不因条数变化重写检索与评测。
- 开始一个工作单元时给出完整且明确的验收口径，执行中不无依据追加要求；发现真实正确性、兼容性或任务覆盖问题时，说明证据、影响和必要修正，并保留旧版配置及结果。不以助手临时想到的“更工程化”要求反复推翻前一步。
- 区分已确定与确实待选的事项。HTML／PDF／OCR 的具体工具仍需样本验证，不能假称早已选定；验证后通过既定统一输出接入，不牵连重写下游。已决定的 LangChain Embeddings、ChatDeepSeek、LangGraph、Qdrant、FastAPI、SQLite、Docker 方向保持连续，不因教学便利更换。
- 既有 B0、B1 与数据准备的验收结论保留。新功能或新数据版本有自己的任务与结果，不将新增标准追溯成用户旧任务没完成；规划和接口决定不能冒充已实现或实测。
- 核心代码仍由用户写，助手给接口、参数、理由和验收并检查实际代码／输出；辅助数据准备、保存与文档按已有授权完成。不因“成品标准”扩大代写范围或增加无必要的基础设施任务。

### 13.9 验收后先提交并同步 GitHub，再进入下一步

用户于2026-11-23明确要求：“每次要进行下一步前，请你将现有成果提交并同步到github，改错阶段不需要。” 这是后续持续生效的合作约定。

- 一个完整工作单元验收通过后，先更新必要的进度与说明，检查相关改动，创建Git提交并推送到当前项目的GitHub远端；确认远端已同步后，再布置或开始下一工作单元。修订中的小错误不逐次提交，汇入该工作单元最终验收的提交。
- 当前仓库为https://github.com/Herdeny/clinical-evidence-rag，分支main，远端origin。用户已授权日常阶段提交和正常推送，不再每次重复询问。遇到远端更新先检查并正常整合，不擅自强制推送、覆盖他人提交或改写历史。
- 提交范围是本阶段已验收的代码、相关测试和必要文档。尚未验收的新模块及无关改动保留本地。沿用.gitignore，原始语料、模型／向量缓存、环境凭证和本地生成结果不强制加入Git；验收规模与可复现步骤留在受版本管理的文档中。
- 同步失败时如实说明已经完成本地提交还是尚未提交，以及失败原因；不能把仅本地commit称为已同步，也不能默认越过用户要求继续下一步。正常纠错与重试沿用本次授权。
- 本次读取适配已在此前通过9项检查，现补做该验收节点的提交与同步；benchmark_eval.py仍是下一项待验收任务。

### 13.10 模型按正式项目的任务效果选择，不默认偏向轻量

用户于2026-11-24明确：“模型你都可以选性能好的，不要老往轻量上靠。” 适用于向量、重排、生成和多模态等所有模块，优先于早期CPU／小模型起步的资源偏好，不授权助手代写核心或擅自启动长任务／付费运行。

- 先明确模型承担的任务、语言、输入长度、证据类型与失败风险，查官方论文／模型卡、许可、公开结果和可复现接口，给出有依据的候选；不能只因快、能跑或教程常用就定为成品模型。
- 以固定语料、题目和候选预算的开发集对照评价效果及逐题失败，再结合延迟、吞吐、显存和API费用作决定。模型规模和排行榜均不替代本任务实测；成本是有证据的权衡，不能凭假想资源限制排除强模型。
- 区分官方结果、待验证候选与本项目已实现／实测。面试选型理由应能回到候选比较、实测增益与失败边界；未做的对照不能写成自己的实验结论。检索相关性模型不自动等于医学适用性判断或临床决策能力。
- 既有BGE-small、DeepSeek及缓存保留为已有基线；成品模型没有因此被永久锁定。模型配置通过已定接口接入，升级向量模型确需新编码与索引，但不让用户重写核心，也不与新检索模块同时改动。
- 本轮撤回未经效果对照的MiniLM成品选型，优先验证Qwen3-Reranker-4B，并与BGE-reranker-v2-m3对照；当前rerank纯函数及验收不变。模型权重、dtype、输入模板、长度和batch在真实运行前核定并冻结，尚无重排模型成绩。

## 14. 恢复工作与维护本文

后续接手按以下顺序恢复：

1. 先读本文第 1 节、当前任务和第 13 节合作约定，特别是导师职责与步骤衔接。
2. 检查用户最新消息是否改变任务、范围或合作方式。
3. 打开当前核心模块、正式运行脚本及必要输出，区分历史输出和本次提交；仅在需要回查历史实验时读取旧 Notebook，不读取或展示密钥。
4. 对照已保存的结果及数据版本，确定本小步是否验收。
5. 验收后先按13.9提交并同步GitHub，确认成功后再给下一个完整工作单元的目标、接口、理由和验收；未通过时解释并让用户修改，不代写核心逻辑，不拆成逐行练习。
6. 有实质进展、实验结果、路线变化或新合作约定时更新本文，避免只更新零散笔记。

维护时优先更新：当前阶段与下一步、已完成及未完成状态、实际结果和对应文件、数据规模与版本、待决定事项。更新不能删除失败证据或将规划改写成已完成。细节文件与本文冲突时，以用户最新指令、可核实代码和当次运行证据为依据修正记录。

**截至2026-11-24，v3主语料及其BM25／Dense旧32题基线已完成，NFCorpus公开开发集BM25／Dense／RRF三条基线也均实测核验。当前Dense在该开发集四指标均值最高，下一步用户实现重排纯函数，固定Dense候选再检验排序。核心继续由用户写，长任务由用户可见终端执行；用药专项、多模态、Agent与MIRAGE全量对标仍未完成。**

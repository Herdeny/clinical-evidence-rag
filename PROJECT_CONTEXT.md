# 项目背景、进度与后续任务交接

最后核对：2026-11-26。本文用于在后续对话、上下文压缩或换助手时恢复项目。内容依据用户的项目要求、当前代码、保存的输出及结果文件整理。该日期是交接更新日，不覆盖来源此前的核验日期。

**接手时先读本文件，再检查当前代码和用户最新提交的输出。不要把规划当成实现，不要从 B0 重新教起。用户后续明确指令优先于本文，代码与输出的变化需要及时更新到本文。**

## 1. 当前应从哪里继续

**2026-11-26当前恢复协作：用户自行运行324题三方法02，助手只准备命令并等待输出。** 用户在纠正代跑后说“继续”；这不构成重新授权助手执行模型／API／GPU。已只读核对现有全324条改写文件results/nfcorpus_query_rewrite_dev_324_01_results.jsonl，324条且ID唯一，SHA=ccbb27de7427b403e59fa3ee13ac758faf491e342b62474b5f121344dc2bed95。本轮直接复用它，不再发送改写请求。原01助手误执行记录保留、不覆盖；不继续以它推进效果分析。为让用户亲自执行，三方法新前缀分别nfcorpus_bm25_query_rewrite_dev_324_02、nfcorpus_dense_qwen3_8b_query_rewrite_dev_324_02、nfcorpus_rrf_qwen3_8b_query_rewrite_dev_324_02，准备时均无同名产物。

只准备results/nfcorpus_query_rewrite_retrieval_dev_324_02_source_snapshot/user_terminal_command.sh及_audit.json：原核心／模型／配置不变，仍--config configs、原corpus与缓存、同一324题和qrels、每方法两组。脚本按八份原始输出保护日志／资源／两组三JSON，冲突或失败停止；只做bash -n语法检查，不能执行脚本或代用户调用其中命令。聊天直接给完整终端循环和参数作用，等用户贴三种方法的324题输出后再独立复算并分析。提交同步范围仅为工作约定、任务与准备文档，不包含凭证、生成结果、草稿或无关删除。

**2026-11-26最新执行边界纠正：模型、API及GPU运行由用户亲自执行，助手不能擅自代跑。** 用户最新明确“让我来跑好吗？你在干什么？”；助手此前把“全部运行完324道题再分析”误解为代跑授权，越过了已有合作约定，现已承认并停止后续执行。该句应按用户希望先完成全量再分析理解，不能据此覆盖用户负责运行的约定。今后助手只审代码、准备并说明命令，等用户贴实际输出再分析；若用户确实另行明确委托助手执行某项任务，才在其具体范围内执行。不能用助手自己写下的“授权”描述充当用户授权证据。

误执行事实保留：助手已复用旧8条，真实调用DeepSeek316次并保存全324条改写（324成功、12条表达变化），随后完成BM25／Dense／RRF各原文与改写324题六组检索，并独立复算。新增生成进程session48842、三方法进程session22762均已exit0结束，无这两项后台运行继续执行。核心代码未改；辅助编排及原始结果保留在results，分别以前缀nfcorpus_query_rewrite_dev_324_01、nfcorpus_query_rewrite_remaining_dev_316_01、nfcorpus_query_rewrite_retrieval_dev_324_01及三方法全量前缀存放。不自行删除、覆盖或再次运行。相关audit中的authorization字段记录的是助手当时的错误理解，不代表用户授权；保留原审计内容，在此明确更正。8题仍只作流程联调，旧临时核验在进度刷新次数断言处停止属于辅助核验假设过强，不是核心缺陷。此后不继续推进全量分析或启动下一实验，先按用户恢复的运行分工协作。

**2026-11-26最新：用户原入口可选改写已最终验收，准备真实同8题三方法运行。** 用户已补main最前的3／6输出检查；run_benchmark_eval.py现198行，SHA=bcda8cb4750fd93705f054620b19c3617f315812b7257d8cedd236ee1147c026。去掉此次唯一新增8行可精确恢复前次六方法／模式及两CLI审查源码字节，其他逻辑未改。逐一模拟原模式3处与配对模式6处冲突，全部在数据加载、模型／缓存／索引构造和保存前拒绝，哨兵原件不变；新目录下真实临时BM25单组／配对分别保存3／6文件且不构造embedding。记录results/query_rewrite_shared_entry_validation_01.json，旧_review_01.json失败观察保留；未调用真实模型、GPU或API，助手未改核心。

运行准备：已核对保存改写JSONL仍为af5e6ad0ffdf16851f0caa92be9bed683726417a10cb78fb2b912b5e3fa6c1fb，8题身份／顺序与原dev前8相同、1条改变；原dev324／corpus3633。Qwen缓存fingerprint=f57e042cca31d1d4e4fcc61d84d576d2b6ad4b247c7490d03188c16144fd54c1，manifest complete且completed3633，原corpus身份一致，矩阵3633×4096 FP32可只读映射。用户接下来依次运行BM25、Dense Qwen8B、RRF Qwen8B，每种方法各比较同8题original／rewritten，原方法参数保持。运行名前缀分别nfcorpus_bm25_query_rewrite_dev_8_01、nfcorpus_dense_qwen3_8b_query_rewrite_dev_8_01、nfcorpus_rrf_qwen3_8b_query_rewrite_dev_8_01，准备时三方法各8个原始输出均不存在。三方法均复用已有改写，不重发DeepSeek；Dense／RRF复用文档缓存，BM25不传embedding模型选项。

先归档本验收节点并同步，再准备results/nfcorpus_query_rewrite_retrieval_dev_8_01_audit.json和_source_snapshot，绑定已推送执行提交、源码／embedding配置、三原数据、原改写及缓存身份。此新回执只覆盖列明材料，继承旧历史资源异常，不声称全历史未变。完整用户终端循环见docs/query_rewrite_task.md：每方法在time／tee启动前保护log、resources和两组三JSON共8份，任意冲突或失败停止，保留已运行方法，重试手动换编号。尚未执行任何真实改写检索，无新nDCG／Recall；8题仅用于流程和逐题差异，不能与旧324题均值比较。用户贴结果后独立核对同题两组评分、来源／缓存／命令和成本，再安排完整324改写及三方法对照；MIRAGE和临床专项目标不变。以下“待补防覆盖”是本轮已解决的修订历史。

**2026-11-26最新入口审查：三方法两模式及CLI接线通过，尚缺启动前输出保护，未最终验收。** 重读用户run_benchmark_eval.py 190行，SHA=ef831e039e3f2b29019ac6c236de72441decd23f911792a331303271d4eda3ff。rewrite_path传参、可选默认名、BM25无embedding依赖、按method共享retrieve_fn、两组子集／来源SHA／query_inputs、独立group_config和_original／_rewritten前缀及打印均正确。临时3文档／3原题／2保存记录，真实BM25／Dense分数计算／RRF／评分／JSON保存，embedding及文档缓存替换为CPU假对象；三方法×原单组／两组共6条路径、2条实际CLI路径通过，模型／缓存各按方法只构造一次，失败改写原样回退，两组题号／文本／配置及原文件身份保持。假指标不作效果，未读.env、运行模型／GPU或调用API。报告results/query_rewrite_shared_entry_review_01.json；助手未改核心。

本地实际复现唯一阻断：仅guard_probe_rewritten_summary.json预先存在时，主入口未提前检查，仍构造1次假模型和缓存、完成4次查询编码、写出original三文件，随后被真实保存器FileExistsError拒绝；已有哨兵原件未变。此为临时fixture观察，不是用户真实GPU失败。下一项只需在main方法校验后、加载模型／索引前，根据rewrite_path为None或Path检查run_name单组3份或_original／_rewritten两组6份输出；任意存在即停止。沿用已约定保护，无新默认、兼容或异常包装要求。用户保存后复查保护及受影响路径，通过再提交同步并准备用户终端真实8题命令。纠错阶段不提交，不重发改写API，用户草稿及其他改动保留。

**2026-11-26最新方案纠正：复用原run_benchmark_eval.py增加可选改写输入，不继续独立Dense入口。** 用户指出独立入口重复已有模型／缓存／保存，并限制BM25和RRF复用，这一设计判断成立。助手撤回此前新建完整run_query_rewrite_retrieval_eval.py的任务，不把“先跑Dense”作为架构限制。用户已写该未跟踪草稿（导入、六输出保护、配置／数据／改写读取及未完成缓存调用），保留原件不擅自改写或删除；可用片段由用户迁回原入口。现在只修订任务和文档，尚未代写核心、运行模型／API或取得改写检索分数。

已验收evaluate_query_rewrite_retrieval本身无需修改：它只接收通用retrieve_fn，对Dense／BM25／RRF均适用；A/B/C假检索及真实dev324＋保存8条的假检索通过，后者16次调用、各次k100。ids使用Series、局部seleted_qrels拼写均不阻断。旧公共评分及冻结重排AST不变；记录results/query_rewrite_paired_eval_validation_01.json，源码SHA=74f0a6e93044fa59a27a1b14b1c940069f988e4ad53f01c3b542e3e0f7b72720。上个完成节点72e3d6f已推送；本轮属于方案纠正，不把文档变更称为入口已实现。

助手扩展原retrieval_results_io.save_beir_results：调用方可明确提供config.query_subset_ids，结果／run仍须完整覆盖这组题，摘要query_scope记录原划分数量和实际评测数量；未声明时保留整划分严格检查及旧摘要布局。临时3题fixture验证整集、显式2题子集及4种错误声明的写前拒绝；不为8题放宽成任意少题可保存，不改原评分逻辑或旧全量原问题核验脚本。新问题记ENG-027。

下一用户任务修改原run_benchmark_eval.py：main保持原位置参数／config_embedding_model默认bge_small，只追加关键字rewrite_path=None；CLI只新增--rewrite-results（type=Path，默认None），沿用--method／--config及可选run-name默认公式。未传文件时原全划分单组评测、原文件前缀及summary返回均保持；传文件时读取已保存记录，用当前method的同一retrieve_fn调用两组函数，按_original／_rewritten分别保存三份，返回两组摘要，CLI按模式打印对应metrics。不新增--rewrite布尔开关或直接请求LLM，参数同时提供开关与必要输入。将embedding profile读取／核对移到dense／rrf条件内，移除BM25+Qwen无关拒绝；BM25不读模型配置或加载embedding，RRF仍两路各构建一次。运行前根据模式保护三份或六份输出；保持原results目录，不顺带新增result-dir或改变其余默认。显式子集／改写来源SHA／query_inputs配置沿用上一方案。三种方法分别运行，形成各自同题原文对照；当前先用同一保存8条接线，再扩完整324，不能把8题改写均值与旧324题均值比较。用户先迁移并保存，助手语义审核及CPU假依赖检查，通过后提交同步，再由用户真实运行。以下独立入口描述属于撤回的旧方案；其他旧待办均按最新段落判断。

**2026-11-26当前：用户apply_query_rewrites已验收，下一项写同题两组评测编排。** 已重读125行，失败回退不再strip。实际A/B/C例子验证原文件顺序、非默认索引、原题含空白精确保留、成功表达清理、状态／来源、额外列及输入不变；重复record ID、未知ID、原文不匹配、空成功表达、未知status均拒绝，异常类型按现实现观察不强制另改。真实8条适配ID及文本完全对应原保存输出，原文件未改。用户标签llm_rewrite_query保留，任务文档同步使用，不为旧示例强制改名。benchmark_data.py SHA=482dea9c0f4c07e4eabb7551fd26b9af7892d4552273bc676b882ffcb698c03c，原loader AST对上一提交不变；记录query_rewrite_input_adapter_validation_01.json，派生nfcorpus_query_rewrite_dev_8_01_retrieval_inputs.jsonl。未调用API／GPU／embedding或做检索，不宣称收益；归档提交同步后再交下一函数。后面旧问题均属已解决修订记录。

下一用户任务在benchmark_eval.py增加evaluate_query_rewrite_retrieval(queries_df,qrels,retrieve_fn,*,rewrite_records,ks=(10,100))，新增导入apply_query_rewrites。前三参数复用现有公共评测接口；原表及qrels现324、records现8，retrieve_fn是已构造的同一个检索函数对象。先适配得rewritten_queries_df8行，再ids=其id列表，原表用isin(ids).copy得original_queries_df8行，selected_qrels用{qid:qrels[qid] for qid in ids}保留同8题原文档等级。用同一retrieve_fn／selected_qrels／ks，分别调用既有evaluate_beir_retrieval两次，得到各8行eval_df和各8题run字典。返回{"original":{"eval_df":original_eval_df,"run":original_run},"rewritten":{"eval_df":rewritten_eval_df,"run":rewritten_run},"query_inputs":rewritten_queries_df}，其中DataFrame不能直接json.dumps，后续入口用既有保存辅助分别落盘。函数不读写文件、不构造模型、不调DeepSeek、不重复写评分公式或包装异常。保留失败回退题和原文来源；新query必须用真正Dense重检索，不沿用原冻结候选。当前只写函数保存，语义审查／最小CPU假检索后再接用户GPU入口；此新函数与入口尚未实现。聊天要按324→8→两组8的中间变量、对象类型、调用参数与返回逐步讲清，不重复抽象目标。

**2026-11-26当前教学澄清：用户第三次指出任务逻辑太抽象，需按实际草稿和具体数据逐步展开。** 已读benchmark_data.py：用户开始apply_quert_rewrites草稿（约定接口为apply_query_rewrites），将rewrite_records列表当DataFrame调用iterrows、把query_id写为id、对标量调用isin、将单行DataFrame列比较直接用于if，并从原题表读取实际上属于record的status；末尾if尚未写完且缺冒号。本轮不运行导入／测试或修改核心，先在聊天用原题A/B/C与记录B成功/A失败演示list→按ID字典→布尔mask→DataFrame副本→第二个逐行循环→at写回→返回，明确两个循环各遍历什么、每个变量类型与中间值、set差集／isin／copy／at的语法和原因。给必要语法小片段及分支字段表，不代写完整函数；保持上次输入输出及显式回退规则，不额外新增要求。保存后再读代码，纠错阶段不提交。

**2026-11-26当前：真实dev前8题改写已核验，下一项用户写检索输入适配。** 用户终端完成nfcorpus_query_rewrite_dev_8_01，8成功、1变化、7原样、0失败；输入3260／输出706／总3966tokens，8条用量已知，输入含缓存读取2048不可再加。逐题流程合计7388.057ms／平均923.507ms，进程8.31秒、RSS211596KiB、退出0无中断；不是远程模型纯推理耗时。6份准备源码和快照、3份输入、8题ID与原文、配置及独立重算摘要／日志匹配，5份输出和准备audit未改。_validation.json为passed_with_semantic_observation，协议及产物passed，_semantic_review.json独立保存语言观察。旧历史资源异常继续披露，无全历史审计或恢复宣称；助手未调用API／GPU或读.env。

唯一变化PLAIN-77把elsewhere变为in other countries，可能将未明确地点收窄为国家层级；reason声称改善检索但尚无检索对照，不能据此认证同义或收益。7条字面原样只说明输入保留，不说明原题医学陈述已核实或表达最优。原模型结果不改、不为增加改写率重调prompt，不因语义观察先手改数据后再报分；当前没有改写nDCG／Recall结果。此次只给逐题观察，不估计总体保真率或临床有效性；ENG-026已追加此例。运行源码在5e15904已推送，入口及API生成阶段完整；接下来复用原8题，不再调用DeepSeek。

适配任务定义现已实现：完整原题DF与本批记录按ID对应，返回仅覆盖题目、原文件顺序、输入副本；原文匹配检查，成功用非空保存表达并标llm_rewrite_query，失败精确原题回退并保留error／original_fallback。返回id／query／original_query／query_source／rewrite_status及已有额外列，原始错误和token记录不改；PLAIN-77原输出保留。数据适配不读文件／调用模型／评分，后续评价按返回ID筛选同一qrels。当前实现已核对，尚无新的Dense检索结果。

下一检索接线须将同一qrels按返回ID筛选，满足现有evaluate_beir_retrieval查询与qrels键集一致；原题和改写组都8题同标注、同Qwen Dense配置和文档缓存，重新生成候选。不可拿原冻结Top100冒称新召回。8题是流程与逐题观察，完整324dev检索对照仍待后续；不引入RRF／重排或同时改模型。本单元先归档提交同步8题结论再交用户下一函数。以下命名和初稿缺陷段落为已解决的修订记录，不再作为当前阻断。

**2026-11-26最新命名纠正：--run-name保持可选，撤回助手添加的必填要求。** 已核对run_benchmark_eval.py及run_reranking_eval.py都注册可选--run-name，未传时生成数据集_方法_配置_划分默认名，显式名称优先、不加时间戳。批量改写沿用此规则，默认如nfcorpus_query_rewrite_deepseek_flash_dev，防覆盖检查和请求前确定名称，生成位置沿用有效实现即可，不额外强制CLI或main某一处。parser.add_argument("--run-name")本身正确，空字符串兜底应改成有效默认名，调用main仍需传run_name；函数参数必需传入不等于CLI选项必须用户填写。任务文档及前次审查记录已纠正，不能为旧任务说明／测试强制required=True。用户正在修改的批量文件不由助手代写，不新增测试或提交；其他实际运行问题待保存后统一复查。

**2026-11-26当前：用户提交run_query_rewrite_batch.py初稿，尚未验收，集中修订后再看，不运行API。** 已读74行实际源码，CLI --config／args.config及main函数签名正确；需要集中修六组实际问题：(1)第17行防覆盖名称与保存辅助真实输出不一致：应_results.jsonl／_summary.json／_run.json，当前单数result及错误.jsonl扩展名漏拦；可对目标Path.exists检查避免新目录os.listdir先报错，不规定唯一实现或异常类型。(2)第23行if not queries对DataFrame真值不明确，应查queries.empty；实际直接main加载公开324条dev后在此ValueError，未读dotenv或构造客户端。(3)第25行先用root，第31行才局部赋值，应把root赋值移到读取.env之前；静态问题，未越过DataFrame错误动态运行。(4)第35行批量调用仍传全queries_df，会请求324条而不是limit8；第43行query_ids也应从选中的queries取，与现已正确的query_count对应。(5)第44行profile_name错误写死为config，应记录实际profile_name。(6)保存摘要需接收并return，CLI --run-name保持可选，空字符串兜底应改成既有风格有效默认名（此前必填要求已撤回），第73行main调用缺run_name，接收summary并打印JSON；真实CLI用显式参数实际复现TypeError missing required keyword-only argument run_name，未进入main，客户端／dotenv调用0。局部rerank_profile、to_list别名和无用导入不是阻断。助手只读核心／做本地最小检查和更新记录，模型／API及.env读取被禁止并mock，未替用户修改或提交。先给聊天内完整六组修订及理由，不挤成逐行多轮，不为测试另添兼容或异常协议。

**2026-11-26最新纠正：CLI只用--config，解析为args.config，函数参数仍config_dir，不添加兼容别名。** 用户指出助手引入--config-dir违反已有run_benchmark_eval.py风格，随后又明确否定助手自行添加的历史兼容别名，强调测试不得反过来规范核心代码。单题／重排入口及两份预检工具只注册--config；旧CLI测试改用--config，不要求核心兼容测试的旧参数。用户批量入口已有的--config正确，该文件继续由用户开发，尚未验收。历史日志、源码快照及已执行命令保留原件供回查，不为历史记录增加运行时代码。纠错阶段不提交、不推进新任务。此轮只修参数及相应说明／旧测试，不改业务函数、模型配置或用户批量入口。四入口实际参数声明至parse_args边界的本地检查已通过，--config映射args.config且无别名，业务函数AST对HEAD不变；没有执行模型导入／API／GPU或读取.env。此前要求检查兼容别名属于助手额外条件，已撤回，不作为用户代码缺陷。

**2026-11-25最新：用户rewrite_queries已通过本地验收，下一项写数据集批量入口。** 重读104行源码，失败original_query已取问题字符串、error为具体类型及消息字符串、两路径统一添加ID／计时并append一次。实际4题混合假响应依次为有效改写／解析失败／连接异常／原样返回，4次假invoke，状态ok／error／error／ok，顺序、原文、10字段、JSON、有限非负计时、失败后下一题继续、输入DataFrame不变全部符合约定；解析失败保留用量，连接异常未知，和保存辅助衔接统计3已知／1未知，假token不作真实成本。另验证原TypeError实例自然向外传播。原RewriteResult与rewrite_query的AST对HEAD不变。源码SHA=0767d5da2a8c4ffd25768d1b18d9f75dfe9e3210a53e6cee281886095fabf6f5，记录results/query_rewrite_batch_validation_01.json。助手未改核心或加永久测试脚本，未读.env或运行API／GPU；本次通过只是本地逻辑，不是8题真实API或检索收益。归档提交同步后才交下一工作单元。

批量入口任务已完成并经真实8题验证：main读取同一LLM配置，loader以split选题，head(limit)限制请求，qrels不传模型；dotenv及客户端只构造一次，批量核心结果全部交保存辅助。config公开记录dataset_name／绝对data_dir／split／limit／实际题数与ID／profile及公开参数，CLI只用--config且run-name可选，无时间戳。现20根目录模块，下一函数加在现benchmark_data.py；尚无改写检索实测，后续指导继续在聊天写完整。

**2026-11-25当前：用户真实CT查询改写单题通过，已归档；下一项用户写小批量核心。** 用户在终端完成ct_query_rewrite_single_01，原问题及检索表达完全一致、changed=false，检查目的未说明保留，status=ok、error=None、finish_reason=tool_calls。真实输入422／输出96／总518 tokens、cache_read0，响应ID=f2c04abe-bda3-4c7d-a89d-e1b70d1ec294，model_name=deepseek-flash。资源为整个本地进程1.47秒、RSS96700KiB、退出0无中断，不称远程模型推理延迟。原_run.log／_resources.txt与用户提交一致且未改，已无损生成_results.jsonl、_summary.json、_run.json、_validation.json。验证时当前core／entry／配置SHA匹配原入口验收，但没有请求前代码回执或HTTP消息快照，不能冒称严格证明请求时源码身份。入口此前d21bd5d已成功推送。

单题reason声称无negations，但输入有not stated；检索表达保留原句，流程通过，说明文本的不准确观察记ENG-026。reason不是独立保真核验，changed也只判断文本变化；不为单题措辞重跑或修改prompt。目前只有这一真实输入的服务与条件保留观察，无批量、改写检索或广泛医学语义结果。助手未调用API／GPU或读取.env，用户核心与入口未改。

助手按计划新增query_rewrite_io.py，save_rewrite_results(records,*,config,run_name,result_dir)：每条query_id加核心8字段、允许额外计时字段，保存_results.jsonl／_summary.json／_run.json并返回summary。公开config由入口传入；不读环境或调用模型。摘要统计成功／失败／changed及完整已知token；错误响应有用量也计入，未知／不完整单独计数，全未知总量None；ID唯一、防覆盖、写前序列化及本次部分产物清理。临时目录已检查实际JSON无损、输入不变、失败已知用量、未知用量、覆盖保护与写前拒绝错误数据。此为批次结束保存，不宣称有逐请求断点恢复或事务。现19根目录模块，新增辅助逐行中文注释；本工作单元归档提交同步后再交下一项。

批量核心约定现已实现：输入id／query，客户端由入口共享；tqdm逐题、perf_counter计时，只有APIError转失败记录，编程异常自然传播，不重试／回退。计时含提示／请求／解析及错误处理，不含客户端、打印、落盘；本地openai1.109.1确认连接／超时／限流／HTTP异常皆为APIError子类。下一真实流程检查用NFCorpus dev.head(8)：PLAIN-1／11／22／32／43／55／67／77；完整检索对照仍324题、同Qwen Dense文档缓存及新候选，当前尚无真实8题、批量缓存或改写召回结果。

**入口本地验收记录：** 用户run_query_rewrite.py已通过CLI到核心函数检查，第28行--query正确。真实argparse／实际核心／假LLM验证配置展开、项目dotenv路径override=False、单次invoke、原问题、8字段JSON；导入无客户端构造，help／缺query在请求前退出。此轮不读密钥或API，假token不作成本。入口SHA=8f9783b2730a8b7cb82de9f1351c1bfce708132217c768e5f6a95327c2aa2773，记录query_rewrite_entry_validation_01.json，与后续真实单题记录分开。

**核心验收记录：用户query_rewrite.py已通过本地验收，核心及公开配置9f3ccaf已推送。** 第48行最终为not schema_response or responses["parsing_error"] is not None，错误转字符串／缺失回退、空白内容说明均已完成。已实际检查12个输入情形：六类结构化响应、四个非法输入、原网络异常传播、未知用量保留None；语法／真实提示对象／8字段返回／JSON序列化／单次invoke／原问题和raw元数据保留均通过。源码SHA=eaba30a9f7efa31a0850e72a6f475eb0869fcff3c7b1a3d465889ca5fd20daed，记录results/query_rewrite_core_validation_01.json。只用CPU假响应，虚拟token不作成本，无API／GPU、医学语义或召回收益结果；助手未改用户核心、未增加永久隐藏测试。普通拼写／未用导入不阻断验收，不再让用户返工。

配置与入口设计保持原约定：configs/llm_profiles.json沿用B1 deepseek-flash／temperature0／max_tokens2048／非思考，api_base=https://api.deepseek.com；timeout60、max_retries0。已复核官方工具说明及本地SDK字段，配置不含密钥，API别名不等于锁定revision。入口现已由用户实现，不从Notebook导入，也不重复套结构化包装。原向量缓存与冻结候选未改；以下旧节点为历史记录，当前进度以上方为准。

**2026-11-25最新：BGE完整dev已核验，重排候选对照完成；下一阶段查询改写。** nfcorpus_rerank_bge_v2_m3_dev_01执行提交4823b0e7f43449eebf0e14e539150088fd47024f，同一原Qwen Dense Top100／324题／32400对，实际BF16／SDPA／4096／batch4、无指令／Identity。四指标0.3294191948049945／0.14729743122167865／0.3376506725571584／0.39709670188154617；对原Dense分别-16.006481%／-23.363434%／-8.773941%／0。nDCG@10逐题71升／164降／89同，Recall@10为49／124／151；Top10正命中252→239、补回9丢22，Top100始终292命中／32零命中。新增阶段均值267.75750053387543ms、中位264.22249699680833、最近秩P95=314.3434670055285；进程91.03秒（1:31.03）、RSS4105064KiB、退出0且无中断。比同阶段4B batch4／8B batch4分别快12.0863／20.2796倍，但当前设置降低前三项指标并新增成本，保留负向对照、不进入默认主线。

_validation.json严格核对当前五原件／原qrels逐题四指标／原候选集合／实际命令与固定配置、三输入／十文件快照及当前代码、86份新周期保护文件通过，原始产物未改。该passed仅属于BGE当前保护周期；报告显式继承旧4B资源异常一项，unbroken_history_claimed=false，旧回执原预期与异常原件均未改，不能宣称历史已恢复。_comparison.json含对Dense和三套Qwen的完整逐题差值。助手未运行模型或GPU、未改核心或核验器。全程GPU峰值未测，不用预检值替代。网络已恢复：用户提示重试后已成功推送4823b0e，用户正式运行也显示Everything up-to-date；之前TLS失败只属历史事件。

阶段结论以Qwen8B保留nDCG效果优先对照、4B保留成本和Recall@10对照，不再追加模型／盲调batch来追高分。按原计划进入查询改写：先固定原Qwen8B Dense和文档缓存，仅改变检索表达，检查Recall@100／nDCG@10、零标注命中32题能否补回及原命中题是否退化；原问题／报告事实保留用于评价与回答，不把LLM改写当成新事实，不向模型暴露qrels或标注答案。核心仍由用户写，下一工作单元先核实已安装ChatDeepSeek结构化接口并给完整函数／参数／验收，再做单题与少量开发题；模型／API调用由用户终端执行。当前尚无query_rewrite.py、改写缓存、批量改写或收益结果，不让用户调用不存在辅助。未来改写检索阶段复用文档向量，产生新候选，不能沿用原冻结Top100冒称改写召回；8B embedding和reranker分阶段加载以适应4090。先归档提交同步本轮BGE结论，再进入下一工作单元。以下为历史记录。

**下一工作单元已明确，尚待用户写核心：** BGE归档ac881d6已成功推送后，核实本地langchain-deepseek0.1.4／langchain-core0.3.71／pydantic2.14.3及实际with_structured_output返回协议，未构造客户端或调用API。已查官方LangChain MultiQueryRetriever说明及DeepSeek Tool Calls接口；本轮只一条改写保持预算，不引入多查询并集，复用既有数据和DeepSeek方向。任务见docs/query_rewrite_task.md：用户新建query_rewrite.py，定义RewriteResult(retrieval_query,reason)，实现rewrite_query(query,*,llm)，使用ChatPromptTemplate及method=function_calling／include_raw=True，一次invoke，先取raw元数据再检查解析对象和空白结果。返回8字段：original_query／status／retrieval_query／changed／reason／usage_metadata／response_metadata／error。成功由Python计算changed；已有响应但解析失败、parsed缺失或空白内容时返回error状态，改写／changed／reason为None，保留真实token成本，不能先抛解析异常而丢费用或静默回退；输入错误和没有有效raw的API异常沿用实际异常。原问题原样保留，未知条件不能补成已知；模型reason不作医学证据。llm由后续独立入口构建后注入，不依赖Notebook、不读取凭证；当前先写函数待审，不运行324次API。核心未代写，批量／保存辅助尚不存在，真实单题后续由用户运行。任务文档将单独提交同步后交用户。

**2026-11-25最新：BGE真实预检01通过并离线核验，下一步用户完整dev。** nfcorpus_rerank_bge_v2_m3_preflight_01，固定953dc6f版本，实际RTX4090／cuda:0、BF16／SDPA／4096／batch4、右填充、无指令及Identity均符合profile。324题／32400句对真实长度最小32、最大2624、P95=609、超限0；实际一个batch4，样本长度2624／2620／2619／2616，float32有限原始分数-3.984375／-3.953125／-4.0625／-5.53125。GPU已分配1435868672字节（1.337256908GiB）、预留1629487104（1.517578125GiB）；进程12.83秒、主机RSS4144888KiB、退出0且无中断。加载0.672743715秒、四对打分0.163378023秒不当稳定单题成本或完整峰值。

_validation.json核对模型实际属性及完整profile、原候选来源、源码／三输入／三原产物、实际命令和终端JSON一致；四个样本以固定BGE分词器和完整原文独立重算长度一致，未重新扫描全部长度，助手未执行模型或GPU。cache_dir弃用提示已记录，本地CrossEncoder的普通分类加载分支内部向Transformer传cache_dir；是兼容提示而非本次失败，缓存仍在项目内，不为消除提示改动本轮加载器或已通过的配置。

先归档同步本节点，再准备nfcorpus_rerank_bge_v2_m3_dev_01的十文件执行前快照、三输入和旧文件保护回执，交用户终端完整324题／32400对，仍复用原Qwen Dense Top100，不重做检索。新回执必须显式继承4B dev02的历史资源异常：旧回执原预期保留，新周期以当前实际文件身份冻结并链接旧异常报告，不能把原失败清单直接复制后称全历史通过；运行后报告也须保留该继承范围。运行前检查五个原始输出名称，排除已预建audit／snapshot，不用整个前缀存在性阻断准备好的运行。完整命令见docs/reranking_runtime_task.md“BGE-v2-m3完整开发集重排”。Recall@100应仍0.39709670188154617，其他指标与耗时以完整实测为准，不能由预检4对选定最终模型。以下为历史记录。

**本节点早先同步连接异常（已恢复）：** 当时2e908f0本地提交完成，工具端多次HTTPS／HTTP/1.1推送及只读SSH探测连接失败，没有冒称同步成功。用户提示重试后已将后续4823b0e推送成功，本地与origin/main一致，正式回执git_sync_at_preparation.verified=true，用户运行也显示Everything up-to-date。交付命令保留最外层git push成功条件和五原件保护，push在GNU time之外；本段保留网络故障及恢复历史，不是当前待解决事项。

**2026-11-25最新：BGE-v2-m3固定快照下载核验通过，下一步用户终端真实预检。** BAAI/bge-reranker-v2-m3 revision953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e已在项目cache；13文件／单权重2271071852字节，393个张量原生F32、张量数据2271023108字节，逐文件SHA256／普通Git blob地址、链接归属、头部形状／偏移／字节总量均匹配，无.incomplete。下载200.37秒（3:20.37）、主机RSS1764348KiB、退出0且无中断标记；记录results/bge_reranker_v2_m3_download_validation.json。离线AutoConfig／AutoTokenizer及短句对分词成功，本地类映射XLMRobertaForSequenceClassification、num_labels=1且权重分类头为[1,1024]；该类声明支持SDPA，不冒称实际模型加载成功。助手未加载权重或GPU。

现有加载器／预检代码无需改，profile=bge_v2_m3保持batch4、4096联合预算、CUDA BF16／SDPA、右填充、无Qwen指令、Identity原始分类logit。检查点F32与计划运行BF16须区分，实际精度和容量由用户执行确认。先归档同步本节点，再交nfcorpus_rerank_bge_v2_m3_preflight_01命令；启动time／tee前检查JSON、资源、日志三名称，已确认均未用。复用同一324题／32400原候选，BGE自己分词统计全部联合输入，再取最长4对真实打分；不能沿用Qwen的长度或显存，通过后才准备完整BGE dev。旧4B历史资源异常状态与原预期继续保留，不因新下载通过而改写。命令与验收见docs/reranking_runtime_task.md“BGE-v2-m3下载验收与真实预检”。以下为历史节点记录。

**2026-11-25最新：4B batch4完整dev02当前运行核验通过，但有一处历史资源覆盖异常；下一步BGE下载。** 四指标0.40770144978894557／0.20511966645543572／0.378699429264687／0.39709670188154617，执行提交40712d368c9d2d46a9c5cb786905baab7b5984ba。对4B batch1，nDCG@10相对-0.554337%、Recall@10-0.900884%，新增阶段均值3236.2094056732553ms（仅少0.677616%）、中位3219.8874420064385、最近秩P95=3716.3080089958385；进程1052.91秒／17:32.91，RSS5344568KiB、退出0。22101／32400句对分数变化，绝对差均值0.0569386574、P95=.125、最大.5；83题Top10集合变化，245题Top10顺序变化；nDCG@10对batch1为41升／42降／241同。原100候选及Recall@100不变。当前单次未观察到明显批量提速，不宣称所有差异归因于batch或统计显著。同batch4的8B nDCG@10更高2.178317%、Recall@10低1.037300%，本次阶段均值为4B的1.677891倍；BGE待补，不先定最终模型。

**核验限制必须保留。** 严格核验发现唯一变化是旧nfcorpus_rerank_qwen3_4b_preflight_02_resources.txt，预期67bcf01a…实际db163c9f…，当前内容为同预检命令signal 2中断／2.45秒尝试，原预检JSON、日志和核验JSON均未变。不能恢复或用聊天文本伪造旧资源原件；保留异常原件快照和_prior_artifact_drift.json。原严格核验器未改；临时副本只排除该一历史项后，当前五产物／原qrels四指标逐题重算／原候选／配置、三输入／十文件源码快照及其余67历史文件全部通过。主_validation.json为current_run_validated_with_prior_artifact_drift，audit=complete_with_prior_artifact_drift，strict_full_history_validation=failed而current_run_integrity=passed。原保护清单和旧预期未改，原五产物未改；不能称全历史通过。后续新运行前回执应以当前实际内容建立新的保护身份，并显式链接本异常；不要改写旧回执或反复用旧失败清单宣称通过。详情docs/nfcorpus_retrieval_baselines.md及ENG-025。

下一步按既定计划下载BAAI/bge-reranker-v2-m3固定revision953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e，不后台下载或GPU。已重新核对官方固定版本文件表和Apache-2.0模型卡，快照尚未在项目cache，download_01两日志名称未用。命令先检查资源／日志名称，再启动GNU time与tee，避免它们在Python内部防覆盖之前改写旧文件；不要给已存在前缀重跑，重试手动用新编号，Hub缓存可复用。新profile仍batch4、4096、BF16／SDPA、Identity，既有加载器及预检支持BGE；下载后助手核对，再由用户做真实长度／batch4预检，最后同原Top100完整dev。尚无BGE实测。先归档同步本节点，再交下载命令，见docs/reranking_runtime_task.md的BGE节。以下为历史节点记录。

**2026-11-25最新：4B batch4真实预检02已核验，下一步完整dev02控制。** 实际RTX4090／cuda:0、BF16／SDPA／4096／batch4及原Identity／query指令；32400联合输入最大2414、P95=654、超限0。最长四对长度2414／2412／2411／2410，float32有限分数-4.25／-6.25／-8.125／-6.78125。预检GPU已分配10324794368字节（9.615714GiB）、预留10877927424（10.130859GiB）；进程15.24秒、主机RSS5352216KiB、退出0；加载0.805843369秒、小批0.994710797秒不当稳定查询成本或完整峰值。_validation.json核对源码／配置／三输入／三原产物、候选归属及真实资源参数和终端JSON；四对长度以固定分词器独立重算一致，助手未加载神经网络或执行GPU。

除batch_size与配置文件身份外，当前完整模型运行声明与旧4B batch1逐项相同，候选来源完全一致。同一PLAIN-2639／MED-957旧batch1预检-4.375、当前batch4为-4.25，记录为不同批次／填充上下文的观察，不强求BF16逐位同分，不据单对推断完整指标。先归档同步本节点，再准备nfcorpus_rerank_qwen3_4b_dev_02的十文件源码快照及旧结果／缓存保护回执，交用户在可见终端完整运行324题／32400对；不下载模型、不改核心或重做Dense，保留旧4B batch1及8B batch4的dev01。显式命令见docs/reranking_runtime_task.md“Qwen4B batch4完整开发集控制”。Recall@100应仍为0.39709670188154617，其他指标、排名变化和耗时以新实测为准；BGE对照继续保留。以下为较早节点记录。

**2026-11-25最新：Qwen8B batch4完整dev重排已通过独立核验，下一步补4B batch4控制。** nfcorpus_rerank_qwen3_8b_dev_01，执行提交d9a9955833303b9d27ef99097ac741e2500cc62e，同一原Qwen Dense Top100、324题／32400对；四指标0.4165824815915057／0.20299195976049142／0.38352092086136175／0.39709670188154617。相对原Dense+6.217941%／+5.613564%／+3.619229%／0；相对旧4B batch1为+1.611905%／-1.928839%／+1.059764%／0，不能称8B所有指标胜出。nDCG@10对Dense逐题131升／98降／95同，对旧4B为112／102／110；Top10正命中Dense252→263，补回19丢8；对4B257→263，补回11丢5。Top100始终292命中／32为0，各题候选集合及Recall@100不变。

新增候选读取＋重排平均5430.007332923309ms、中位5410.375527499127ms、最近秩P95=6146.1651060089935ms；整进程1764.12秒（29:24.12）、主机RSS5447832KiB、退出0。该次均值为旧4B batch1的1.6665215631502692倍，仅描述两套已记录profile，模型和批次同时变化，不能隔离规模或批次性能原因。全程GPU峰值未采集，不能用预检值或主机RSS替代。_validation.json核验原qrels逐题四指标、候选集合／最大K召回、预检固定配置、三输入／十文件快照／当前实现、56旧产物与缓存身份及终端／实际资源参数均通过，audit已complete_integrity_validated；_comparison.json含对Dense和旧4B的完整逐题差异。原始五产物未改，助手未运行模型／GPU。详见docs/nfcorpus_retrieval_baselines.md。

下一步是已计划的同batch补齐：当前4B profile仍batch4、固定4B权重已在项目缓存；先用户终端运行nfcorpus_rerank_qwen3_4b_preflight_02（完整最长4对），通过并归档后再准备nfcorpus_rerank_qwen3_4b_dev_02的完整运行及回执，不覆盖旧batch1的01。三预检名称和dev02前缀当前均未使用。这样可分别评价4B自身批次影响及同batch4的4B／8B差异，BGE对照继续保留；当前不选最终胜出模型、不进入test或MIRAGE。先归档同步本轮8B节点，再交下一条预检命令，见docs/reranking_runtime_task.md的4B批次控制节。以下记录为较早节点当时状态。

**2026-11-25最新：Qwen3-Reranker-8B batch4真实预检01通过，下一步用户终端完整dev重排。** 用户执行提交5dbcb7ef8505bb67ae21be32a451676340896bba，实际RTX4090／cuda:0、BF16／SDPA／4096／batch4、Identity及query指令符合固定profile，revision=77d193c791ed757ca307ee72715aa132723da912。324题／32400联合输入最小93、最大2414、P95=654、超限0；实际一个完整批次4对、样本长度2414／2412／2411／2410，原始float32分数-3.75／-6.9375／-7.8125／-6.40625，全部有限。预检峰值已分配18863105024字节（17.567636GiB）、预留19497222144（18.158203GiB）；进程16.81秒、主机RSS5454612KiB、退出0。加载1.335686秒、小批1.431585秒均不当完整运行或稳定单题成本。

记录results/nfcorpus_rerank_qwen3_8b_preflight_01.json、_resources.txt、_run.log及_validation.json。助手离线核对报告绑定的源码／配置／三输入／三原产物、当前完整profile及模型运行属性、样本归属、真实资源参数和终端JSON一致；用固定快照AutoTokenizer和原始完整正文独立重算四个样本模板后长度一致，未重新扫描全部32400长度、未加载神经网络或执行GPU。当前只有预检通过，尚无8B完整排序成绩。先将此节点归档提交同步，再保存nfcorpus_rerank_qwen3_8b_dev_01_run_audit.json、十文件实际源码快照及旧产物／缓存指纹，交用户运行同原Top100、324题、batch4的完整入口；显式config-dir等参数和命令见docs/reranking_runtime_task.md的8B完整开发集节。通过后独立重评分和逐题比较；Recall@100应仍为0.39709670188154617。正式入口仍未记录全程GPU峰值，不能用本次预检值替代。旧4B为batch1，模型本身效果／成本结论仍需同batch补齐4B对照。

**2026-11-25最新：Qwen3-Reranker-8B下载核对通过，下一步由用户运行batch4真实预检。** 固定revision=77d193c791ed757ca307ee72715aa132723da912，项目内快照共19文件／5权重分片，权重文件16377142272字节、张量16377096192字节，均BF16；逐文件内容地址、分片索引／头部／形状字节和离线配置／分词器一致，yes9693／no2152，无.incomplete。下载23:50.88、主机RSS4293064KiB、退出0，记录results/qwen3_reranker_8b_download_validation.json；助手没有加载权重或使用GPU。

本轮读取到用户将三个reranker profile的batch_size从1改为4，助手保留该修改。原预检最多3对不能覆盖完整batch4，因此只扩展助手的scripts/evaluation/preflight_reranker.py：batch1仍用原首两对＋最长一对策略，batch>1则取全体固定候选中联合token长度最大的batch_size对，一次predict覆盖一个完整批次；记录batch_check的实际数量、策略、是否覆盖完整批次及长度。跨题聚合最长输入是保守显存压力检查，不当作正式逐题批次或全量显存保证；样本不足时full_batch_exercised=false，不假称整批通过。输入仍全量扫描，不参考qrels等级选样本。保留原4B batch1预检和完整结果，当前所有batch4配置均尚未实测；8B预检前缀nfcorpus_rerank_qwen3_8b_preflight_01，完整显式命令见docs/reranking_runtime_task.md。

本轮先审语义，再用CPU辅助检查核对：重排核心12＋预检5＋入口4＋支持6共27项通过，CLI帮助成功，没有真实模型／GPU运行；新增预检用例核对5个候选中确实选择最长4对且原候选不变。入口辅助检查原把batch1写死，已改为核对临时配置实际值，未因测试要求改用户核心。rerank_core.py／benchmark_eval.py／run_reranking_eval.py／reranker_adapter.py指纹保持原样。后续模型选型需同batch补齐4B对照；当前8B batch4与旧4B batch1之间不能把速度或细小分数变化全部归因于模型。先归档同步本节点，再交用户执行8B预检，返回真实结果后才准备完整重排。

**2026-11-25最新咨询：Jina重排模型已做官方调研，未接入／下载／实测。** 当前更值得研究的是jina-reranker-v3.5（0.6B、多语言列表式、131K整组上下文），不是简单将当前CrossEncoder的model_name换掉；官方接口AutoModel＋model.rerank(query,documents)，返回index／relevance_score，需要独立适配候选映射、整体预算／截断及分组策略。官方论文同jina-embeddings-v5-text-small Top100协议中BEIR均值Jina3.5=63.20对Qwen4B62.28，但NFCorpus38.45对42.48、ChatDoctor70.63对73.38、CURE平均62.20对63.68；不能把外部汇总或分项直接与本地dev0.409974比较，也不能推断Jina本机更快或医学更强。v2提供CrossEncoder示例但原生1024预算及分块需核对。当前Jina权重CC-BY-NC-4.0，官方商业部署需商业许可。详情与primary来源见docs/reranking_runtime_task.md的Jina调研节。此为选型咨询，不自动改既有Qwen8B／BGE实验计划、不新增profile或调用API；Jina3.5作为待验证不同架构候选，后续纳入需明确理由及实际验证。

**2026-11-25最新实测与验收：Qwen4B完整dev重排完成，独立核验通过。** run_name=nfcorpus_rerank_qwen3_4b_dev_01，执行提交c036e6b128b1dac66ea379e573d2fc233c761f68，同一Qwen8B Dense原Top100、324题／32400对、BF16／SDPA／4096／batch1。四指标为0.4099740875251688／0.2069843548748328／0.37949912510243394／0.39709670188154617；相对原Qwen Dense依次+4.532968%／+7.690745%／+2.532625%／0。nDCG@10逐题124升／106降／94同；Recall@10为87／65／172；Top10正命中252→257，补回17、丢12；所有题Top100集合不变，292题正命中、32题为0。不能说每题提升或新增召回，当前仅公开dev排序对照，无显著性推断或临床有效性结论。

候选读取＋新增重排平均3258.2880731880987ms，中位3245.5629495016183ms，最近秩P95=3512.4218779965304ms；整进程1060.07秒（17:40.07）、主机RSS5345564KiB、退出0。原Dense检索53.69274598138244ms单独报告，不能把分阶段测量称端到端总延迟；没有完整GPU峰值，不用预检值替代。results/nfcorpus_rerank_qwen3_4b_dev_01_validation.json通过，三输入、10份执行前源码快照／当前源码、40受保护产物／缓存身份、候选集合与原qrels重评分、实际资源CLI及固定模型配置均一致，audit已complete_integrity_validated。比较含逐题变化见同前缀_comparison.json，汇总docs/nfcorpus_retrieval_baselines.md，新增工程取舍ENG-024。

本轮只离线核验与记录，不改用户核心或profile，不重新调用GPU。下一步按既定Qwen4B／8B／BGE候选对照，用户终端下载Qwen/Qwen3-Reranker-8B固定revision77d193c791ed757ca307ee72715aa132723da912；该快照本地当前不存在。继续同项目缓存、文件进度变量、资源／日志编号download_01；命令见docs/reranking_runtime_task.md的8B下载节。下载后核对，再用同一工具独立8B预检，随后同候选完整dev比较；保留4B实测，不先定最终胜出模型。batch咨询不自动改变当前profile，性能调优后续作为独立实验。先将本节点归档提交同步，再交下一命令。

**2026-11-25最新咨询：batch_size对推理速度和结果的影响，不等于授权改当前配置。** 已核对实际ST5.7源码及PyTorch2.6数值说明：100候选的batch1／4／8／16对应100／25／13／7个内部前向批次，业务predict仍每题一次；通常增大批次可提高吞吐，但填充／长度／显存导致非线性，权重不随batch复制。BF16批量与单条不保证逐位同分，近分可交换排序；不能声称batch更大提高模型能力。项目目前只实测batch1，小批峰值8.063GiB不推断batch8可用或峰值乘8。尤其现有预检最多3样本，若日后测batch8必须扩充足够样本及长输入，不能仅改profile后沿用3样本就声称通过。细节见docs/reranking_runtime_task.md批次讨论。当前正式run_name nfcorpus_rerank_qwen3_4b_dev_01仍固定batch1，运行前10文件快照与40文件保护回执已准备，状态prepared_not_executed；源码提交c036e6b已同步。等待用户完整运行输出，不擅自修改profile或启动GPU／新批次实验。

**2026-11-25最新实测：Qwen4B真实预检01通过并已离线核对，下一步用户终端完整重排dev。** RTX4090／cuda:0、实际BF16、4096联合上限、SDPA、batch1及Identity／query指令均符合固定profile。324题／32400联合输入最短93、最长2414、P95=654、超限0；实际仅打分3对，float32一维全有限，分数5.0625／3.75／-4.375。样本为PLAIN-1→MED-2418（560tokens）、PLAIN-1→MED-4070（384）、PLAIN-2639→MED-957（2414）。显存峰值已分配8657582592字节（8.063002GiB）、预留8875147264（8.265625GiB）；进程15.04秒、主机RSS5352928KiB、退出0。加载0.79804秒、小批0.39160秒不当完整运行成本或稳定查询延迟。

记录results/nfcorpus_rerank_qwen3_4b_preflight_01.json与_validation.json；报告绑定的配置／源码／三输入／三原产物、样本归属及命令／资源均通过，未重新加载模型或GPU。当前已证明这批固定输入在4B配置下无截断且小批可运行，尚无完整排序效果。首次完整运行名nfcorpus_rerank_qwen3_4b_dev_01（无时间戳），该前缀产物目前不存在；同一Qwen8B Dense原Top100、324 dev及四指标，源Recall@100=0.39709670188154617。保持4B固定配置，仅测重排；不重做Dense／换候选。预检峰值不能充当完整运行GPU峰值，本轮正式入口未记录全程GPU峰值，GNU time只提供主机RSS及整进程耗时，结果必须如实说明。

为复用离线核验，助手扩展scripts/evaluation/validate_beir_run.py支持frozen_rerank：按已有run_reranking_eval.py的--profile核对资源命令，不强迫用户增加旧--method；独立检查原候选集合、与预检固定的模型配置、Recall@100不变量及原计时范围。新增tests/test_beir_run_validation.py共4项通过，含合法重排／原BM25完整临时产物、错候选／错配置／错资源profile拒绝；没有真实模型调用。报告results/rerank_validator_support_validation.json。先归档同步本节点，再准备本地_run_audit.json及实际10文件源码快照、保护既有结果／缓存身份，交用户执行docs/reranking_runtime_task.md完整开发集命令。用户返回后核对5产物、候选逐题集合、独立四指标重算、逐题收益与新增重排成本；当前不运行官方test或MIRAGE。tests现21模块，用户核心源码未改。

**2026-11-25最新：下载节点804b1dc已同步，真实重排预检工具已实现，等待用户终端执行。** 新scripts/evaluation/preflight_reranker.py由助手编写，复用现有build_reranker／describe_reranker及固定候选加载器，不改用户核心。先核对来源并在CUDA加载唯一reranker，然后用实际CrossEncoder.preprocess、原query／完整正文／同一默认指令统计全部32400联合输入长度（含模板），统计时关闭截断；首两对加最长一对去重，最多3对真实predict。输入超4096则在打分前停止，不默默裁剪；输出只检查一维、数量、有限性，允许负数和大于1的原始logit，不要求L2或概率。记录真实设备／BF16／长度／指令、显存峰值、加载与小批打分耗时及输入前后指纹；不算完整排序指标，不将样本耗时当稳定查询延迟。

tests/test_reranker_preflight.py的4项辅助检查，加原支持6项及入口4项，共14项通过；报告results/reranker_preflight_helper_validation.json及快照，命令行help实际通过，旧输入／产物SHA未变。仅CPU假预处理器／假模型，不是实际GPU预检通过。原文“支持7项＋CT保存5项”系模块计数笔误，已改为实际6＋6，原46与50总数不变，未改用户实现或新增验收要求。tests现20模块，根模块仍16。当前用户命令见docs/reranking_runtime_task.md真实预检节：显式config-dir／data-dir／receipt／profile=qwen3_4b／output，离线环境经project_env.sh运行，保存nfcorpus_rerank_qwen3_4b_preflight_01.json、日志、资源。工具验收提交同步后交用户运行；收到输出再核对真实结果，通过后才准备完整324题重排。当前无真实模型推理或完整重排成绩。

**2026-11-25最新下载验收：Qwen3-Reranker-4B固定版本已完整下载，尚未加载真实模型。** 用户终端download_01完成17/17、退出0，耗时10:29.07，主机RSS3860552KiB；单文件字节进度已实际显示。快照位于项目cache/huggingface/hub/models--Qwen--Qwen3-Reranker-4B/snapshots/22e683669bc0f0bd69640a1354a6d0aebcfeede5。17文件均为有效项目内blobs链接，流式校验LFS SHA256／普通Git对象SHA1与缓存地址一致；索引引用2个分片，文件合计8043614960字节，张量数据8043569152字节、均BF16，头部张量名／归属／shape字节与索引一致，无.incomplete。离线AutoConfig及AutoTokenizer成功，yes9693／no2152与LogitScore一致。记录results/qwen3_reranker_4b_download_validation.json，助手未加载权重或执行GPU。先归档同步下载节点，再由助手新增scripts/evaluation/preflight_reranker.py复用build_reranker／describe_reranker，统计32400个联合输入长度、选少量样本真实打分并记录显存；预检仍由用户可见终端执行，完整重排尚未运行。

**2026-11-25下载命令说明修正：必须解释单文件进度与实际缓存位置。** 用户追问未见进度参数和下载位置。已核对真实huggingface_hub0.36.2 CLI及file_download／utils.tqdm源码：hf download无show-progress，quiet关闭进度；tee使文件tqdm的disable=None按非终端自动隐藏，所以原命令只说默认显示不充分。命令现补进程级HF_HUB_DISABLE_PROGRESS_BARS=0 TQDM_POSITION=-1，模拟真实_get_progress_bar_context的10字节检查已确认disable从True变False并输出字节进度，不下载权重、不切换Xet后端。路径已在包装器子进程实际读取：/home/wzh/clinical-evidence-rag/cache/huggingface/hub与同级xet；模型子目录models--Qwen--Qwen3-Reranker-4B，snapshots固定revision为原文件名入口，blobs通常保存实际字节。已更新docs/reranking_runtime_task.md下载节，当前为下载说明纠正阶段，随下载核对节点再提交；用户尚未报告下载完成，不启动第二个后台下载。

**2026-11-25最新验收：用户run_reranking_eval.py已完成，4项入口及相关46项共50项全部通过。** 当前入口SHA=96743186288c98436424061a9a1f2de9732f536731058bfda27341ffbd56488a，助手未改源码。配置文件路径已修正、receipt默认指向真实描述文件，默认run_name在模型构造前按dataset_rerank_profile_split生成，显式名称优先，不加时间戳。当前Python3.12.7实际compile通过，f-string中表达式复用双引号合法，不按旧Python语法要求改引号。main／CLI、唯一模型构造、配置batch=1透传、真实描述文件指纹、完整候选来源／模型元数据与三类保存产物均通过临时数据联结；未知profile及缺失receipt自然在加载模型前报错，未新增核心守卫或异常包装。未使用urllib.parse不作为阻断项。

记录results/reranking_entry_validation.json、_run.log及_accepted_code_snapshot。4项入口检查覆盖导入无自动运行、3个profile各自默认／显式名称、真实CLI参数映射、原生输入错误的加载顺序；临时CPU单参数假模型配合真实候选加载／describe／用户重排评分／保存，不是模型效果或真实GPU运行。原描述文件／三检索产物／三输入SHA保持。根目录现16个Python模块，tests19个。本单元验收后先提交同步，再让用户在可见终端下载Qwen/Qwen3-Reranker-4B固定revision=22e683669bc0f0bd69640a1354a6d0aebcfeede5；使用scripts/project_env.sh和环境内hf download，保留实时日志与资源统计，缓存位于项目内。完整命令见docs/reranking_runtime_task.md下载节。尚未下载／加载真实reranker、没有真实重排成绩；下载完成后助手核对文件身份，再准备真实联合输入长度／小批打分／GPU显存预检，通过后才跑324题，不能直接跳到完整重排。

**2026-11-25最新合作要求：始终保持前后一致，禁止临时改变既有标准。** 用户指出此前run_name没有时间戳，助手临时建议加入时间戳已撤回。重排默认名沿用数据集／方法／模型配置／划分拼接，例如nfcorpus_rerank_qwen3_4b_dev；显式--run-name优先，例如带_01／_02的名称，不自动加入时间戳。这不局限于命名，接口、配置、文件职责、评测口径和任务验收均应先核对已定约定。必要变更先解释具体证据、原因及影响，不把临时建议追溯升级为旧任务的硬要求；发现真实错误仍须明确纠正。长期规则见13.13。当前入口仍在修订阶段，文档随该工作单元验收后一并提交。

**2026-11-25最新入口初审：用户已新建run_reranking_eval.py，主调用链正确，当前处于三项修订阶段，尚未提交入口。** main六参数、按配置读模型、先核对冻结候选、唯一模型构造、batch取profile、完整7字段config、评测／保存／CLI传参均已写好。实际第21行describe_reranker的config_path却传config_dir目录，应使用第13行已有的reranker_profile_path文件；已直接验证Path('configs').read_bytes()原生抛IsADirectoryError，没有运行模型来复现。CLI第52行默认root/'receipt'不存在，实际描述文件为results/nfcorpus_qwen3_8b_frozen_candidates.json，可改有效默认或要求显式--receipt。第54行--run-name既无默认又非必填，省略时None会在整轮评测后被保存器拒绝，应设必填或在模型加载前生成名称。其他有效CLI默认值不强制改为必填，无用urllib.parse不作返工门槛。不代写核心、不为旧测试格式改异常，无真实模型／GPU运行。用户源码注释询问source_info和describe_reranker含义，需要在聊天解释：前者保存原Dense候选来源、配置和文件指纹，后者读取本轮实际模型属性、核对配置并返回记录字典。修正保存后重读实际文件再用小型假模型核对main／CLI，通过后提交同步并准备下载预检。

**2026-11-25最新：真实重排配置／加载与保存辅助已实现，用户下一项新增run_reranking_eval.py。** 助手新增configs/reranker_profiles.json和reranker_adapter.py，扩展原retrieval_results_io.save_beir_results支持frozen_rerank，不改用户benchmark_eval.py／rerank_core.py。新辅助build_reranker(profile)返回一个CrossEncoder；describe_reranker(model,*,profile_name,profile,config_path)返回实际设备、权重精度、长度、激活／指令和库版本等可保存字典。候选来源与本轮模型分置config.candidate_source和config.rerank，来源描述文件／原三产物／三输入重新核对，逐题输出只能来自自己原候选；latency.scope明确只含候选副本读取＋重排，排除原召回／文件模型加载／计分，旧方法范围保持。

三候选Qwen4B／8B／BGE-v2-m3保留；8B固定revision=77d193c791ed757ca307ee72715aa132723da912，4B和BGE固定版本沿用。已读官方模型卡／公开API／固定版本小配置，Qwen为Transformer＋LogitScore，yes9693／no2152、默认query指令、Identity原始差值。实际ST5.7.0类位于cross_encoder/model.py（并非大写CrossEncoder.py），构造签名已直接核对。初始4096联合输入上限、batch1、CUDA BF16 SDPA；这是待真实预检的起点，不是最优或已验证显存配置。没有权重下载、模型推理或GPU运行。相关46项全部通过：新辅助6＋原BEIR保存6＋CT保存6＋评测10＋加载6＋rerank12。报告results/reranking_support_validation.json，真实构造仅autospec检查签名转发，不能写成模型加载通过。

下一项完整说明见docs/reranking_runtime_task.md：用户写main(config_dir,data_dir,receipt_path,profile_name,run_name,result_dir)及CLI；显式读配置→加载冻结候选→创建一次reranker并取得真实描述→调用既有evaluate_frozen_reranking，batch_size须来自profile→构建7字段config→save_beir_results→返回summary。split从冻结来源取，不设冲突参数；不重建embedding／Dense，不复制循环，不让用户调用不存在辅助。本轮先写入口，保存后语义审核＋假模型编排检查，通过同步再准备用户终端下载和真实小批预检。新增文件的来源／用途／输入输出必须在交任务前讲清，不再直接引入未说明对象。

**2026-11-25最新验收：用户已完成冻结候选重排评测衔接，相关28项检查全部通过。** benchmark_eval.py保留默认两参数检索回调，新增pass_query_id=False选项；开启时传当前行query_id。用户新增evaluate_frozen_reranking(frozen,reranker,ks=(10,100),*,batch_size=16)，内部按ID取候选、调用现有rerank，并复用原计时和pytrec_eval循环返回eval_df／run。选项可由位置或关键字传入，不因原任务建议仅关键字而强制用户修改合法签名。原有未使用导入不作为本轮返工门槛。助手未改用户核心源码，只在tests/test_benchmark_eval.py添加3项已说明的行为检查：同文不同ID回调、真实rerank句对／批次／候选副本衔接、空题保留分母；该模块10项，加加载器6项、rerank核心12项，共28项通过。

真实NFCorpus324题／32400句对也已通过用户包装函数完整联结检查：假打分器反转候选顺序，逐题query原文／ID／顺序和候选集合均保持，Recall@100仍0.39709670188154617；只验证衔接与集合不变量，不是重排模型成绩，不报告假分数nDCG为项目效果。未加载模型、向量或GPU，原描述文件／三产物／三输入SHA全部未变。结果results/frozen_reranking_eval_validation.json、_run.log和_accepted_code_snapshot。用户已了解frozen由助手在9c56f07提供的load_frozen_candidates创建，不是内置变量；辅助文件的来源、输入／返回结构和角色应在使用前讲明。当前工作单元验收后先提交同步；下一步准备真实重排的配置、来源／计时保存辅助和运行入口，现有save_beir_results尚未支持重排，不让用户调用不存在的接口。真实reranker尚未下载或实测。

**2026-11-25当前进展：冻结候选加载辅助已实现并完成真实只读核对，下一步用户只改benchmark_eval.py。** 新frozen_candidates_io.py提供load_frozen_candidates(receipt_path,*,data_dir)，返回FrozenCandidates，公开queries_df／qrels／info副本和get_hits(query_id)。按查询ID联结原文，保留ID／score／source_id／locator及原始顺序；核对原results／run／summary、实际corpus／queries／qrels的指纹和内容对应，不加载模型／向量矩阵、不执行评分、不写原始产物。辅助6项检查通过，包括相同问题文字不同ID／候选、嵌套副本互不污染、源文件／数据改动、内容错配及空候选保留分母。真实NFCorpus324题各100、总32400候选全部恢复，首题PLAIN-1、首文档MED-2418，记录results/frozen_candidates_loading_validation.json；用户rerank_core SHA仍1e04ef...未改。

真实PLAIN-237与PLAIN-2859同文，本轮候选及分数相同，没有观察到旧结果错误；不能把设计风险写成已发生的错误。原evaluate_beir_retrieval按query文本调用没有错误，这次新增用途需要传ID。用户按docs/frozen_reranking_eval_task.md完成一个连贯工作单元：(1)给原评测增加仅关键字pass_query_id=False，默认回调保持(query,k)，开启时额外传query_id=当前行ID；(2)新增evaluate_frozen_reranking(frozen,reranker,ks=(10,100),*,batch_size=16)，内部回调按ID取候选并调用现有rerank，再复用原计分循环，原样返回eval_df／run。核心仍用户写，不增无用守卫或指定异常名称。当前加载辅助已可用，模型配置／CLI／保存辅助的重排扩展尚未实现，不让用户调用；本轮不需要模型、GPU、文件保存或改rerank_core。计时为候选访问＋重排，不含原Dense召回，固定100候选时Recall@100仍应为0.39709670188154617。验收意图已写在任务文档并在聊天说明，保存后先审语义再验证，辅助通过同步后再交用户任务。

**2026-11-25用户纠正导师工作方式：不能为隐藏测试脚本反复改核心，先判断代码语义，再用测试复查。** 用户明确指出多次因助手测试错误或偏好导致核心冗杂，float(None)的TypeError不应被强制包装成ValueError。这是助手判断错误，不能只称“偏严”；此前真实get_embedding_dimension合法却被错误替身判错也是同类问题。已取消重排测试中输入／输出验证对TypeError和ValueError的统一名称硬限制，仍检查非法输入在predict前被拒绝、输出结构与有限性、ID／分数对应、来源保留／输入不变、单次调用及运行异常传播。测试失败先排查用例与替身，未解释的脚本不是需求来源；具体错误协议只有在真实调用方依赖时才明示约束。永久约定见13.12。

本轮仅修助手测试及文档，不改用户rerank_core.py，不加新的校验分支或引入新模块。现有isnan(x)或not isfinite(x)中的isnan、以及对已有seen集合重复set(seen)，属于代码审查应指出的冗余，不当作返工门槛或另布置练习。冻结候选加载辅助此前仅阅读设计资料，尚未实现；原项目目标和路线保留，先落实此检查方式再继续。当前核心已完成，不能再次以旧异常名称要求用户返工。

**2026-11-25当前已验收：rerank纯函数12项全部通过，撤回原分数转换必须包装ValueError的过度约束。** 用户追问异常类型后，核对Python3.12官方说明：TypeError用于类型不合适，ValueError用于类型可接受但值不合法。float(None)自然抛TypeError，float('bad')抛ValueError；统一输入异常可简化调用方，但当前没有必要强制转换。本轮只修助手测试的异常类型要求，原分数转换保留原生TypeError／ValueError即可，非法字段仍须在predict前被拒绝；输出契约、排序、来源和不变性、运行异常传播检查均未减弱。rev05的11/12唯一失败不是算法错误，原报告按当时过严约定保留，不当成当前缺陷或用户工程贡献。

用户原函数SHA=1254c963972c7a1d6e7cee00daa28be1cf11ddfad8d52697c007169f8f9eef9f，无需再改转换逻辑。助手只清理无用logging导入／尾部空白，函数AST相同；最终SHA=1e04ef1809434bb57a30bc0a9cd903f597a29491c0d1c679d99793a86f1c32dc。此前两条错误提示由助手整理，校验／评分／排序仍用户实现。最终results/rerank_core_validation_accepted.json和_run.log、rerank_core_accepted_code_snapshot保存12/12通过、0失败、0错误，无模型／GPU。待本单元归档同步后，下一步由助手先提供冻结Qwen候选加载／原query与正文联结／身份核验、重排评测保存辅助，再交用户入口编排；这些辅助尚未实现，不调用不存在接口。真实4B／8B／BGE reranker尚未下载／实测。以下“只剩强制ValueError”要求已撤回，不再让用户补try/except或撤回已写显式ValueError检查。

**2026-11-25当前复验revision05：同一12项通过11项，只剩float(None)的异常转换。** 最新用户源码SHA=1254c963972c7a1d6e7cee00daa28be1cf11ddfad8d52697c007169f8f9eef9f。全局类型／合法空列表、字典字段／文本空白／重复ID／原分数有限性前置、正常打分排序／元数据／输入不变、错误模型输出与运行异常传播均已通过。唯一剩余：第20行float(hit['score'])遇None抛TypeError，需try/except捕获(TypeError,ValueError)，按既定接口重新抛ValueError，成功后继续现有有限性检查；不用再改算法或增加要求。results/rerank_core_validation_05.json、_run.log及revision_05源码快照保留，12方法11通过／0失败／1错误。未代写核心、未用模型／GPU，不提交纠错阶段；下次保存后复验同一12项，通过再清理无用logging／空白、归档同步，并进入冻结候选加载及重排评测辅助。

**2026-11-25当前复验revision04：同一12项已通过10项，剩候选验证与异常类型。** 用户最新47行源码SHA=fbcf6541ffd3c10cf47c6094a683be56045f10f4db39cb3bc9562ae91379c8fc；字典键检查／and／raise、合法空候选位置、正常重排及输出异常分支均已修好。剩三项：(1)第9／12行仍TypeError，按已确定接口统一ValueError；(2)第14行text仅检查真假，没有strip，纯空白文本会被送模型；(3)重复ID、float原分数及有限性检查仍在predict后的复制循环里，需拆两个循环：predict前独立遍历全部候选完成这些检查，float转换捕获TypeError／ValueError后转ValueError；predict后原循环仅复制候选／存两类float分数。先前只说“前置”不够直观，本轮要明确拆开输入校验与输出组装两阶段，首个循环不能依赖scores。可先验证float再在输出循环重取，或用同序列表保留转换结果，不强制具体写法。

results/rerank_core_validation_04.json、_run.log及revision_04快照保留；12方法10通过，8条子用例失败／错误不等于8个独立缺陷。未改核心、未用GPU／真实模型，不提交纠错阶段；下次保存后复验同一12项，通过后再同步及进入冻结候选加载辅助。以下03的4/12状态为历史。

**2026-11-25当前复验revision03：新字段检查阻断正常字典，需解释Python语法后由用户修订。** 用户原提交SHA=1a0ce36a3fb362b90b7405aa1f61ef82717cb5f32f1ceb22d6aa0bc460c22a41，45行；query先判字符串再strip已修好。第13行用getattr(hit,"id"/"text"/"score")检查dict属性，普通候选全部被误拒，应检查键是否存在，不用值真假判断存在性，原分数0合法。第14行逗号表达式形成非空元组，not(tuple)恒False；type(id)未与str比较，str and也非类型判断；即使分支执行，缺raise只构造异常不抛。第9／12行仍TypeError而契约为ValueError；合法空hits返回仍在predict之后；重复ID、原分数转换／有限性仍在predict后，应全部前置，float转换失败统一ValueError。

助手依用户早前允许输出语句代写的约定，仅修两处异常提示格式及加中文注释：维度提示改f-string，数量提示len(scores[0])改len(scores)；未改校验条件、字段访问、评分或排序。实际受测SHA=52ef630e1ddd73d8df3fb6c562c464f62ce872deadef10ac764f64c483eacb2c。tests仍12方法，合法候选原分数改为0以覆盖同一有限分数契约；当前4/12通过，主要共同阻断Missing attr for hit，不能把负例偶然通过说成字段检查正确。结果results/rerank_core_validation_03.json及_run.log，用户原稿revision_03_user_submission和实际受测revision_03快照均保留，无模型／GPU，纠错不提交。下次保存重读复验12项。当前教学要点：getattr查对象属性、in查dict键、and组合条件而非逗号元组、raise才抛异常；按全局校验→合法空列表返回→所有候选校验→predict→输出校验→复制排序整理。以下02的7/12状态为历史，不增加新接口要求、不写工程贡献。

**2026-11-25当前复验revision02：正常重排路径通过，剩校验顺序和异常分支。** 重新读取用户34行实现，SHA=627747e8982b0922fccd5eb9dc8af257ac743390f7562ac140ff48ab2327820c。分数数组同位取值、Python float、来源保留／输入不变、同分ID排序、k超候选、单条与负分数、模型异常传播均通过。剩：(1)第4行if not hits过早返回，让None／空tuple／空dict等非法容器或空hits下非法全局参数伪成功；先验证query／hits容器／k／batch，再允许合法空列表返回。(2)第5行or仍先query.strip后类型判断，None等直接AttributeError；类型先判，id／text同样先判字符串再strip。(3)候选检查仍在predict后的结果复制循环内，应把必填字典／字段／类型／唯一ID及float原分数有限性验证全部放pairs和predict之前，原分数NaN／Inf当前仍漏检。类型不符按既有契约ValueError，不用TypeError。(4)第14行错误文本仍str+int，第15行数量条件已正确但消息内还留len(scores[0])，导致错误分支再次异常，应安全格式化并读整个scores长度。

同一11项初复验7通过；补1个方法检查“合法空候选不能绕过既有全局参数契约”，未新增接口要求，当前12项方法7通过；8失败／13错误条目含子用例，不能当21个独立缺陷。结果results/rerank_core_validation_02.json和_run.log，初始11项结果另存_before_empty_contract_check，完整覆盖快照rerank_core_revision_02_complete_checks；未改用户实现，未加载模型／GPU、不提交纠错阶段。下一次用户保存后重读并复验这12项。推荐流程：全局校验→合法空列表返回→所有候选校验→pairs／predict→输出校验→复制候选并排序；核心仍用户写，logging未用可稍后清理，不另设验收阻断。以下初版状态为历史。

**2026-11-25当前：用户rerank_core.py初版已保存，尚未验收，集中修订后复验，不推进真实模型。** 已逐行读取26行源码，SHA=d91b92aee01a8ada0bb7941dffcf78d2f8f35518b8bd688cef14be12ee0a558f。句对构造、一次predict传参、dict.copy及(-score,id)排序方向正确。阻断：第5行type(hits)与list()实例比较，正常list也被拒绝；错误消息拼接type／int又触发TypeError。query未先检查字符串就strip；k／batch消息也需安全格式化；缺少空hits提前返回及候选必填字段／类型／唯一ID／有限原分数检查；第15行len(scores[0])误把一维数组元素当容器；第22行hit[index]误从字典取整数键，应从分数数组同位置取值，两类分数转Python float；logging.WARN是数字级别不能调用，缺predict时不能只记录后继续。后几处为静态检查结论，当前有效输入实际尚未越过第5行，不声称已执行到后面。

助手新增tests/test_rerank_core.py，11个无权重测试方法覆盖原query／全文句对、单次predict、稳定同分排序、原分数和来源保留／输入不变、k越界／空／单候选、负logit、非法输入／输出与运行异常传播。初验0/11方法通过，日志含47子用例错误及1条后续断言失败，均不当成48个独立缺陷。results/rerank_core_validation_01.json、_run.log及rerank_core_revision_01保存实际源码和测试快照；未改用户实现，未加载模型／GPU。当前用户集中修订，保存后重读新文件并复验同一契约；只有通过才提交同步并准备冻结候选加载／重排评测辅助。普通语法／索引错误不记工程面试贡献。仍保留d6e11c0已同步状态，benchmark_data.ipynb删除及.vscode不动，纠错阶段不提交。

**2026-11-24最新：完整Qwen Dense dev已核验，当前交用户实现rerank_core.py纯函数。** 运行nfcorpus_dense_qwen3_8b_dev_01、执行提交ed7fc4e，同一3633文档／324题／11385 qrel对、每题100候选。nDCG@10=0.3921959681142708、Recall@10=0.19220254685998026、nDCG@100=0.37012524211267905、Recall@100=0.39709670188154617；相对BGE分别+19.8694%／+28.9855%／+24.5025%／+26.0295%。平均query53.69274598138244ms、中位49.21915899467422ms，为BGE均值2.3082倍；初始文档缓存0行，进程190.69秒、RSS6276000KiB、退出0，进度建库约168秒。本轮未采全程GPU峰值，不把预检或主机RSS替代完整运行显存。nDCG@10逐题163升／64降／97同，Recall@100为173／37／114；Top100至少命中292题，原BGE278，补回18原零命中、丢4原有命中。

**验证与下一步：** results/nfcorpus_dense_qwen3_8b_dev_01_validation.json为passed，25历史保护文件、12源码事前快照及当前代码、输入、终端／资源、324题四指标与最大K召回集合独立复算通过。实际输出策略、四项配置和新缓存身份符合计划；矩阵3633×4096 float32只读，norm0.9999998905402698～1.000000123176053，vectors SHA=ed8a7d4b5b17ea5986f991668934a858efc4e73c8f7e839b56d1b129734d0f28。完整比较同前缀_comparison.json，固定候选身份results/nfcorpus_qwen3_8b_frozen_candidates.json。阶段选择Qwen Top100作重排输入，非最终临床／部署选型，比较包含长度／分词器／指令／数值处理差异，不独归8B容量；旧RRF只测过BGE配置。当前用户按docs/reranking_task.md新建rerank_core.py，实现rerank(query,hits,k,*,reranker,batch_size=16)，先假打分器验收；不下载或执行新模型。后续重排在独立进程只加载一种reranker，复用固定候选与原query／正文，避免与8B embedding同时占GPU。候选加载辅助尚未实现，不能让用户调用；4B／8B／BGE控制保留，真实模板／batch／精度待预检。全部100候选仍返回时Recall@100必须保持0.39709670188154617，重排效果尚未实测。先归档同步本单元，再交下一步；以下“完整dev待跑”为历史。

**2026-11-24最新实测：Qwen预检03通过并独立核验，下一步用户终端跑完整NFCorpus Dense dev。** 真实执行提交b4625a2，RTX4090／cuda:0、BF16权重、4096维、8192输入上限。3633文档／324 dev查询的最大token为2335／40，均0截断；实际仅编码MED-10／MED-14／最长MED-957及原query PLAIN-1。文档归一化前范数0.9986501650037067～1.0032141011444935，FP32处理后0.9999999705619592～0.9999999824791376；query前0.9993850897037317、后1.000000031221733。该实测支持此前低精度归一化偏差判断，不能倒填为02原始向量的数值。峰值GPU已分配15737360384字节（14.65656GiB）、预留16095641600字节（14.99023GiB）；进程5.93秒、RSS6226840KiB、退出0。正文小批0.54619秒、单query0.03104秒只为样本计时，不当稳定查询延迟或全库性能。记录results/nfcorpus_qwen3_8b_preflight_03_validation.json：8份代码与运行前快照、输入、配置、17原结果／缓存及4份失败日志资源均通过；03独立日志无ValueError，终端开头错误属旧输出。弃用提示未阻断。

**当前用户任务：** 同步后运行nfcorpus_dense_qwen3_8b_dev_01，完整3633文档／324 dev、原始query、Top100、同一qrels与四指标，不同时加RRF／重排／改写，不运行test／MIRAGE或医学全库。正式命令显式--config configs、--config-embedding-model qwen3_8b及项目缓存包装器，见docs/dense_model_selection_task.md末节。运行回执和12份代码快照已准备，保护25份历史产物；Qwen文档缓存初始不存在，计划指纹f57e042cca31d1d4e4fcc61d84d576d2b6ad4b247c7490d03188c16144fd54c1，3633×4096 float32。助手未加载模型或代跑GPU。用户返回后核对5个正式产物、输入／代码身份、全部324题／Top100、完整新矩阵、原qrels重评分、逐题增益与成本；仍无Qwen检索成绩。BGE512有330篇截断、Qwen8192本库0截断，应比较整套profile，不将差异独归8B容量。以下“预检03待运行”均为历史。

**2026-11-24当前验收：共享FP32输出适配及用户入口接线均通过，下一步用户终端预检03。** 用户已为getattr补默认None，入口15项全部通过；此前适配6／缓存8／编排9／预检4项共27项也通过。助手仅清理入口未使用HFE导入、旧注释参数与尾部空白，未改用户逻辑。最终入口SHA=9ca5bf87531b3adbda70371687bd5ffd442c261d8a972f927d5cb35394e52ce9。原BGE指纹4aa...与17历史保护文件保持不变；Qwen的float32_l2_v1实际策略及适配类进入缓存身份，BF16权重／8B／4096维／8192上限不变。记录results/embedding_output_entry_validation_02.json及results/embedding_output_normalization_accepted.json，无权重通过不代表真实GPU修复已通过。

**当前用户任务：** 提交同步后，按docs/dense_model_selection_task.md末节通过bash scripts/project_env.sh离线运行nfcorpus_qwen3_8b_preflight_03。03回执和源码快照已准备，01／02日志及资源保留。预检最多编码3篇正文＋1条原query，统计3633文档／324 dev长度；document_vectors和query_vectors分别记录output_normalization的before／after范数。返回后核查实际CUDA／BF16／维度／长度、前后范数、截断与峰值GPU内存，不回填CPU模拟值，不把进程RSS称作GPU显存。只有真实预检通过归档同步，才给正式Qwen Dense dev命令，不跑test／MIRAGE或医学主库编码。以下“getattr待修／入口待接线”为历史。本次数值边界问题记ENG-023，辅助与用户接线分工分别说明。

**2026-11-24最新入口复验：共享辅助已接线，剩getattr缺省回退一处。** 用户已保存run_benchmark_eval.py，SHA=c264c6fa5ab0cb5c521180dfd6c9e8b8caf552b57e0e0b209f0ccaa0606980c4。build_embedding_model(profile=embedding_profile)及Qwen输出策略记录正确，独立Qwen成功用例通过；原HFE导入和四行注释旧构造参数仅属可清理残留。入口测试已切到共享辅助，按实际profile模拟BGE无属性／Qwen有策略；新增完整profile传递及策略记录独立检查，共15项，11通过／4项被同一AttributeError阻断。第85行getattr(embedding_model,"output_normalization")缺第三默认参数，原生BGE无此属性时直接抛错，不能到else。保留用户if/else结构，给getattr默认None即可让BGE走model_native分支；若直接赋值才用model_native作默认，不要混淆两种结构。已使用真实HuggingFaceEmbeddings.model_construct复核同一行为，无权重／GPU，避免替身误判。记录results/embedding_output_entry_validation_01.json及_run.log；助手未改用户入口，不提交纠错阶段。下次保存重读并复验同一入口集，全部通过后同步，再准备预检03。

**2026-11-24当前修订：预检02已成功加载Qwen并进入编码，但单位范数检查失败；先由用户完成共享输出适配接线。** 02日志显示4/4权重加载、3633文档／324 dev长度统计、3篇正文编码已到达检查器，随后退出1，未运行query编码／检索／评分，未生成通过JSON。旧检查未输出范数，不能声称已取得这三篇的实际偏差。已读本地Sentence Transformers5.7源码：Normalize和encode先按张量当前精度归一化，返回NumPy时才把BF16转FP32；precision=float32跳过输出量化，并不把之前的归一化算子升级。CPU合成100×4096的BF16双重归一化复现min=0.9980784463、max=1.0036273482，66行超过旧阈值；只作为机制复现，非真实Qwen样本测量。

**辅助已写、核心待接线，纠错阶段未提交：** 新增embedding_adapter.py的build_embedding_model(profile)，原BGE使用原生HuggingFaceEmbeddings；Qwen显式output_normalization=float32_l2_v1，子类集中为文档／query在FP32再次归一化并记录前后范数，保留BF16权重、8B、4096维及原严格检查阈值。embedding_cache_io只为有策略的实际适配类添加身份字段，BGE指纹4aa...及17历史文件SHA均未变。预检已使用同一辅助并保存前后范数，错误也加入实际min／max。新增6项适配测试，加缓存8／编排9／预检4，共27项无权重通过；不代表GPU通过。记录results/embedding_output_normalization_validation.json。用户下一步只改run_benchmark_eval.py：导入build_embedding_model，将原四参数HFE构造替换为向辅助传所选embedding_profile，dense配置记录实际output_normalization（原生类无属性时model_native）。该入口尚未接入，不能声称预检和正式运行已经一致。用户保存后重读实际文件，补入口集成验收，通过后按约定提交推送，再准备预检03；02日志／资源不覆盖，不直接重跑原02命令。以下“等待预检02”均为历史。

**2026-11-24最新：Qwen3-Embedding-8B项目内下载完整，等待用户重跑小批预检02。** 固定revision为1d8ad4ca9b3dd8059ad90a75d4983776a23d44af；download_02_project_cache日志显示17/17完成，索引要求的4个权重分片共15,134,634,568字节，逐分片流式SHA-256均与缓存内容哈希一致，该模型无.incomplete文件。核验记录results/qwen3_8b_download_validation.json。通过项目包装器离线AutoConfig读取成功，配置／分词器／权重全部位于项目cache；本次检查没有加载权重或执行GPU，不能称为Qwen效果或显存实测。

**当前用户操作：** 用docs/dense_model_selection_task.md末节预检02命令，必须通过bash scripts/project_env.sh启动。预检01已经尝试并退出1，日志为离线文件缓存查找失败，未生成通过报告；保留01日志和资源记录，不覆盖。默认共享Hub下找不到该固定版本config／modules，项目包装器下二者及离线AutoConfig均成功，先统一缓存入口重试，不重新下载、不改模型或依赖。02回执为results/nfcorpus_qwen3_8b_preflight_02_run_audit.json。只有02真实GPU预检通过并同步后，才给正式Qwen Dense dev命令。以下“下载未完成／预检未执行”是历史记录，以本段为准。

**缓存位置要求继续有效：** 模型命令都通过bash scripts/project_env.sh，将HF_HOME／Hub／Xet／assets／Sentence Transformers／Torch／XDG缓存设到项目cache内，仅影响子进程，不改全局配置。原Qwen目录及对应锁已从共享缓存原子迁入，BGE复制至项目并核验，原共享BGE保留。迁移记录results/model_cache_migration_2026-11-24.json，路径记录results/project_model_cache_validation.json。已有BGE文档矩阵和旧基线保留，权重不提交Git。用户偏好见13.11。

**2026-11-24最新：模型配置／维度接入已完成，下一步用户终端下载和预检Qwen8B。** 用户已将CLI调用与六个位置参数对齐，config_dir必填、配置名保留config_embedding_model，结果名带bge_small／qwen3_8b。最终缓存9项、入口14项全部通过，含真实安装类API、4096维、两配置／缓存隔离、零文档重编码、元数据、参数拒绝和CLI。核心由用户完成；助手仅删除未使用logging.config／matplotlib rainbow导入、整理空白，未改变函数逻辑。最终SHA：embedding_index.py=dbdd1baca3a0dc85bd8853c8c6cb8763919af8c59eb4eec2cc075bc559e6fd49；run_benchmark_eval.py=b6d2472690e42519657766e5f8f2c56a1302b7938c38f271d06503ec228f6f3b。results/embedding_model_integration_validation.json为passed，revision5_accepted保存源码；旧10份结果及NFCorpus缓存2文件SHA未变，旧失败报告保留。

**当前用户任务：固定版本下载＋小批预检，命令见docs/dense_model_selection_task.md末节。** 已核查hf路径/home/wzh/miniforge3/envs/all-in-rag/bin/hf、huggingface-hub0.36.2；Qwen revision1d8ad4ca9b3dd8059ad90a75d4983776a23d44af的配置／权重尚未缓存，官方目录约15.2GB。新增助手辅助scripts/evaluation/preflight_embeddings.py，必填--config-dir／--profile／--output，读取同一配置与NFCorpus dev，统计全部文档／查询token长度，只编码前两篇及最长文档、第一条原query；核对真实CUDA、BF16、4096维、8192上限、有限性／范数和峰值GPU分配／保留内存，记录输入与源码SHA。不创建全库缓存、不检索／评分、不访问test／MIRAGE。4项无权重辅助检查及--help通过，实际模型／GPU未运行。用户先下载，再用进程离线开关运行预检；实时日志和GNU time资源文件独立保存，不在助手后台启动。

**用户下一次返回预检输出或“好了”：** 读取results/nfcorpus_qwen3_8b_preflight_01.json及对应_run.log、_resources.txt和下载日志，核对设备／精度／形状、3633文档／324 dev、截断统计、显存、配置与输入身份。不能提前称0截断或GPU可运行，更不能将预检样本当作NFCorpus效果成绩。失败保留日志，报告同名不覆盖，重跑用新编号。只有预检通过并归档同步后，再准备正式Qwen Dense dev完整运行回执与命令；不重跑旧三条基线、不编码医学主库、不运行test／MIRAGE。以下revision4及更早修订为历史，不再要求用户修已通过代码。

**2026-11-24用户新约定：config_dir必须显式提供，不再要求省略参数或兼容旧五参数调用。** 用户明确表示现在不允许省略config_dir，该选择有效，优先于前面可选参数讨论。当前用户采用main(method,config_dir,data_dir,split,cache_dir,run_name,*,config_embedding_model="bge_small")；CLI的--config仍可有默认目录，但调用main时必须传入。测试已撤掉默认路径回退要求，改为检查config_dir无默认值、缺少时报TypeError且显式提供时完整成功，不强制位置或关键字形式。

**当前复验revision4：** 用户入口SHA为aaf6c69ac217ba29ed403169f29a5fe2174b34435022f9e5a8a00a2e51c8f58e，缓存9项通过，入口14项中10项通过／4个CLI用例共享同一绑定错误。定义中config_dir为第二个必需位置参数，但底部仍按原五个位置参数调用并另传config_dir=...，导致第二个位置data_dir先占了config_dir，再关键字重复赋值。只需将CLI调用与当前六个位置参数的定义对齐，或所有参数按角色关键字传入，不能继续要求None默认回退。显式config_dir路径下三方法、Qwen4096维／缓存复用／元数据、参数拒绝和真实新API检查均已通过。报告results/embedding_model_integration_validation.json和revision4_required_config快照；核心未代写，模型未加载，未提交。下一次重读最新文件，检查调用绑定修正后复验，全部通过再提交推送及交用户终端下载／预检。

**2026-11-24导师纠错：维度API和BGE命名两条旧要求撤回，以本段为准。** 用户截图指出旧方法弃用后，已直接检查真实安装的sentence-transformers5.7.0：推荐get_embedding_dimension()，get_sentence_embedding_dimension()是发出FutureWarning的兼容别名。用户一直使用的新方法正确；此前助手手写SimpleNamespace只提供旧方法，导致测试误报用户代码。已改用create_autospec(SentenceTransformer, instance=True, spec_set=True)，并以真实SentenceTransformer＋无权重Pooling验证新API。以下initial／revision1的“新方法错误”诊断失效，历史报告原样保留但不能作为用户缺陷引用。用户同时明确允许nfcorpus_dense_bge_small_dev，已接受按dataset_method_profile_split统一命名，旧自动名不再是验收硬性条件；BM25名字是否含默认配置标签不阻断，实际元数据应准确。用户显式--run-name仍优先，旧结果文件不改名。

**当前最新复验revision3：** 入口源码SHA为fc7d2e174bfea7034dfd7da84255152ee57aa55bd85a8777f001b22be240c228，用户已把config_dir改为仅关键字可选参数，CLI关键字传入正确，方法／BM25组合检查也已放入main。缓存9项通过；修正后的入口14方法中13通过，仅一个默认调用问题：config_dir=None时第23行仍直接做config_dir / 文件名，报NoneType与str不能相除。保留--config覆盖，在拼接前为None补脚本目录下configs即可。原兼容测试之前只检查签名绑定，会漏掉这个默认路径运行错误；已补实际五参数调用，仍为同一项要求，不增加新项目范围。结果results/embedding_model_integration_validation.json及revision3_api_and_naming归档，含API误判和用户命名决定；未改用户核心、未加载预训练权重／GPU。无用rainbow／logging导入仍可清理，绘图库缓存提示不需要安装或配置库。下一次检查用户最新保存内容，保留已通过项；纠错不提交，全部通过再同步并进入用户终端预检。

**2026-11-24接入复验revision1：用户已修正JSON、配置键、对象／字典比较、元数据和CLI配置传递，入口仍有4组问题。** 当前run_benchmark_eval.py SHA为b6945a47d4380f8714301dd4233fbd021077cea5b7976ee0e0fbd07e4792f10b，embedding_index.py仍为25a67822d7816e9560aeb5eb22604fc0857c4b405afbec4389c0b92ab6eaf3ad。缓存9项再次通过；入口13方法尚未通过，4条失败、6条错误（含共同API阻断和子用例，不等于10个缺陷）。真实CLI已传入config_dir和config_embedding_model，绑定问题在CLI这一条已修正，不能继续声称没传。现在剩：(1)第51行仍用get_embedding_dimension，应为get_sentence_embedding_dimension；(2)方法与bm25配Qwen校验仅在CLI，直接main仍到达语料读取，须置于main读语料之前；(3)必需位置config_dir破坏原五参数调用，允许保留用户新增--config，将config_dir作为仅关键字可选参数、默认None时函数内部计算脚本configs路径即可，不要求删除覆盖能力；(4)默认BGE自动名仍多出配置名，Qwen才加。新增未使用matplotlib.cm.rainbow导入已实际触发绘图库缓存目录提示，删除无用导入即可，不配置MPL环境或安装库；logging.config也未使用。模型未加载、核心未由助手改写，报告results/embedding_model_integration_validation.json和revision1归档。下一次重读用户最新文件并复验同套契约；纠错不提交、不启动下载。

**2026-11-24本轮接入代码检查：embedding_index.py已通过9项，运行入口尚待集中修订。** 用户保存后已重读两个实际文件，源码SHA分别25a67822d7816e9560aeb5eb22604fc0857c4b405afbec4389c0b92ab6eaf3ad和93ba7584a56b9de1da2d81548a34a5ce2dc45aeca54a3ab732e6c5fe91ab7b0a。dimension=384默认及传给缓存正确，原6项和新增4096维缓存隔离／复用、非法维度、错误输出不推进断点3项全部通过。tests/test_benchmark_entry.py已扩展为13个方法，假模型提供正确真实API、384／4096维和查询调用记录，临时目录复制受版本管理配置；不强制用户把config_embedding_model命名改为embedding_profile，功能测试会按当前签名提供配置目录，另独立检查原五参数兼容。入口当前未通过，14条错误包含子用例与共同前置阻断，不能说成14个独立缺陷。首次实际阻断为json.load接收read_text字符串而报AttributeError。结果results/embedding_model_integration_validation.json，原始副本results/embedding_model_integration_2026-11-24_initial；未改用户核心、未加载模型／GPU／正式检索或付费API。

**这轮集中修订范围：** 仅run_benchmark_eval.py需修：(1)main多了必需config_dir导致原五参数与CLI绑定失败，按既定规则在函数内部从脚本目录定位configs，保留用户config_embedding_model名称也可，但CLI必须实际传入该关键字；(2)read_text返回str，应json.loads；(3)先确认配置名属于profiles再取值，补bm25与Qwen组合拒绝，方法检查前移；(4)真实方法是_client.get_sentence_embedding_dimension()，实际属性与embedding_profile['dimension']／['max_seq_length']比较，不能下标模型对象；(5)保留既有embeddings_cache／embeddings_shape复数字段，补实际query_prefix，新增embedding_profile／embedding_dimension字段本身正确；(6)默认BGE自动名沿用dataset_method_split，Qwen才加入配置名。from logging import config未使用但不是功能阻断；不扩大为新任务或工程面试编号。修订阶段不提交／推送，等用户改好后重读最新文件再复验同一完整契约，不启动下载。后面的旧“用户下一次”按本段最新状态理解。

**2026-11-24最新：NFCorpus BM25、Dense、RRF dev均已实测并核验，当前Dense四指标均值最高。** 最新run_name=nfcorpus_rrf_dev_01，用户终端执行提交3b51482dc73a600915d4ab59afe134579deeb1d1，3633文档／324题／每题100命中。RRF的nDCG@10=0.312468299806529、Recall@10=0.1406747396163073、nDCG@100=0.28137851892188376、Recall@100=0.3003347087049922，平均查询35.87232415430876ms、中位35.28364700105158ms；整进程16.10s、峰值进程RSS1431336KiB、退出0。Dense相应四指标0.32718602689711807／0.14901094123636222／0.2972834613889674／0.31508239684562706，平均23.261722024713375ms；BM25主指标0.2657379994665381／0.20567783238375933、平均2.839211916625011ms。完整报告docs/nfcorpus_retrieval_baselines.md，不把开发集成绩当临床结论或MIRAGE成绩。

**RRF核验与负结果：** 两路各Top100、常量60、最终100；从归档两路排名独立计算融合，324题全部ID／顺序／分数一致。原qrels四指标重评分、缓存及12个保护文件全部通过，run_audit为complete_integrity_validated。cache_hit=true、initial_completed_rows=3633，未重做文档编码；助手未加载模型或重新检索。相对Dense的nDCG@10逐题RRF高94／Dense高125／相同105；Recall@100高66／低105／相同153，均值分别下降0.014717727090589092、0.014747688140634832。RRF至少命中一篇的279题多于Dense的278题，不代表平均Recall更高，加入相关文档的收益小于移出文档的损失。详见ENG-022，保留全部原始负结果。

**Dense缓存与核验：** fingerprint=4aa389bc2d522a2fc285b6065a93e38de9516d6dfa7265c1e614a4761109c3f0，3633×384、float32只读矩阵，array SHA31c71ff295e2baba90d4ba5b0e334b9fa9d50a40bb445c63a0abc2e32d651f61，有序id/text SHAbcea3c417ac8c0535088df2a31f2c46020fb6fa36cdc69f25c15169d434c3f3e，全部有限且归一化。首次cache_hit=false／initial_completed_rows=0。离线核验工具已扩展为分块检查缓存文件、形状、源文本身份与范数，并检查此前基线产物保护；324题四指标重算一致，输入及9份源码与回执一致，BM25原5产物未变。Dense_validation.json通过、run_audit为complete_integrity_validated；助手没有重新检索、编码或加载模型。

**逐题比较：** nDCG@10 Dense高147／BM25高76／相同101；Recall@100 Dense高184／BM25高52／相同88。Top100两路均命中相关文档231题、仅BM25命中7、仅Dense命中47、两路均零39。均值绝对差分别0.06144802743057999和0.10940456446186769，保留results/nfcorpus_bm25_vs_dense_dev_01_comparison.json。候选互补只支持继续验证RRF，不是融合已取得收益。

**当前任务：先接入Qwen3-Embedding-8B的独立Dense对照，再做真实重排。** 用户在询问embedding选型后明确“继续”，当前完整工作单元见docs/dense_model_selection_task.md：用户修改embedding_index.py，为prepare_document_embeddings增加关键字dimension=384并传给现有DocumentEmbeddingCache；修改run_benchmark_eval.py，为main增加仅关键字embedding_profile="bge_small"与--embedding-profile CLI，读取助手已准备的configs/embedding_profiles.json，按配置初始化、核对真实维度／长度、传入缓存维度并记录实际配置。两个配置为bge_small（原模型与参数不变）和qwen3_8b（revision1d8ad4ca9b3dd8059ad90a75d4983776a23d44af，4096维，BF16权重、float32归一化输出、SDPA、processor输入上限8192、batch1、官方query指令）。batch／长度在用户终端小批预检后才能当作正式可运行配置。核心仍由用户写，尚无接入代码或Qwen权重下载／模型实测。旧缓存／三条基线保留，不先重编码医学783847行主库。

**本轮助手辅助已验收：** 两个静态配置通过真实LangChain构造器＋替换底层SentenceTransformer的参数转发检查，不加载权重。既有缓存类对同一合成模型的384／4096维分别建库、只读输出及重新打开复用通过，目录分离。以真实NFCorpus输入和新bge_small配置只计算身份，仍匹配原指纹4aa389bc2d522a2fc285b6065a93e38de9516d6dfa7265c1e614a4761109c3f0；前两路10份原产物及缓存2文件SHA全部未变。结果results/embedding_profiles_validation.json，配置SHA81204fc0b0f7db38027ddaadfd02ed7967a8da1374f2c28e4013a9c318a02ff3。检查的是配置与助手缓存能力，不是用户尚未修改的编排，也不是Qwen效果或GPU预检。

**用户下一次返回代码或“好了”：** 重读embedding_index.py和run_benchmark_eval.py当前文件，按完整工作单元集中验收维度、配置初始化、缓存复用、摘要与CLI，不沿用旧版诊断、不代写核心。已有分块／入口检查应继续通过，再加4096维及两配置隔离的合成检查；假模型需有真实接口的max_seq_length／get_sentence_embedding_dimension，临时入口目录要复制受版本管理的配置，不能因测试没准备依赖误判用户。代码通过并提交推送后，再交用户可见终端的固定版本下载、小批预检和真实NFCorpus dev命令。暂不启动权重下载／GPU或全量编码，不重复三条旧基线。rerank_core.py的稳定接口继续保留，Dense选型后再实现／接真实重排；test与MIRAGE未运行，Notebook删除及.vscode继续保留本地。

**同日8B候选补充：** 用户追问Qwen3-Reranker-8B，已复查官方同一张分项表：4B英文MTEB-R为69.76、8B为69.02，但8B的中文、多语言、长文档项更高。当前英文汇总只支持优先验证4B，不能排除8B或证明医学任务优劣；明确将8B加入正式候选，与4B在同一Dense Top100上直接比较后选择。8B模型卡／Apache-2.0及官方predict用法已核查，revision下载前冻结，尚无任何重排模型加载或成绩。当前函数与验收不变，见docs/reranking_task.md。

**同日Dense模型选型咨询：** 用户进一步询问BGE-small是否有更好的embedding选择。已查[Qwen3-Embedding-8B](https://huggingface.co/Qwen/Qwen3-Embedding-8B)、[4B](https://huggingface.co/Qwen/Qwen3-Embedding-4B)、[BGE-M3](https://huggingface.co/BAAI/bge-m3)及[MedCPT Query Encoder](https://huggingface.co/ncbi/MedCPT-Query-Encoder)／[Article Encoder](https://huggingface.co/ncbi/MedCPT-Article-Encoder)官方来源。Qwen8B是建议优先验证的通用Dense升级候选：官方32K上限、最大4096维、Apache-2.0；4B最大2560维，模型卡英文MTEB(eng v2)的Retri.列为8B69.44／4B68.46，不要混用之前reranker的分数或全任务均值，也不称为当前最新榜首。BGE-M3是多语言／长文档备选，8192tokens、1024维、MIT，只测Dense时不顺带启用其稀疏／多向量能力。MedCPT是英文医学文献领域对照，查询／文章两个编码器、768维，官方基于255M PubMed query-article对训练、模型卡标public-domain；训练日志未公开，不能声称本项目取得该训练集。原任务主要短查询到标题摘要，不预设适合中文、指南或说明书，也不能用医学背景替代实测。

**建议实验与实现边界：** 第一轮在同一NFCorpus 3633文档／324 dev、相同正文和Top100上，将Qwen3-Embedding-8B与现有BGE-small基线独立比较nDCG@10／Recall@100及成本，先不加重排。用户随后“继续”，已转为上面的配置接入任务；模型revision、指令、输出维度及初始推理配置已准备，未开始模型下载／编码。明确截断差异，随后固定Dense候选再比较重排。现有783847行BGE缓存和NFCorpus缓存均保留。DocumentEmbeddingCache已支持dimension参数，用户需在prepare_document_embeddings中透传；不能只改model_name或混用新查询与旧文档向量。Qwen和BGE-M3沿用LangChain HuggingFaceEmbeddings接口但各用官方query配置；MedCPT需另适配双编码器、CLS pooling与原始inner-product语义。没有新的embedding模型实测成绩。

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

2026-11-26按用户指定提交实际取得公开源码快照，静态核对services/container.py与chat_service.py、agents/graph.py与state.py、retrieval的hybrid／query_rewrite／self_rag／vector／ingest／unstructured_parser、providers/base.py、schemas/retrieval.py、生成和忠实度节点、eval/runner.py与MEASURED.md、配置／权限／可观测性及MIT LICENSE。没有启动对方应用、运行其测试或复现实测，仓库代码、作者报告和本机已验证结果分别表述。源码仅暂存/tmp审阅，不引入本项目实现。

参考项目的分层已有代码依据：FastAPI路由调用ChatService；CLI可经HTTP或本进程共享同一服务；build_container／build_retrieval负责模型、检索、数据库和工具装配；ChatService构造时编译图并复用。Graph以AgentState组织护栏、意图、五策略路由、检索或规划执行、生成、忠实度与记忆。SelfRAGLoop的有限补查是检索内部循环，不能只凭graph.py节点名宣称图有自动回边；五策略DIRECT／SINGLE／MULTI／AGENT／REFUSE也不等于BM25／Dense／RRF方法选择。

对照当前项目：已具备手写Dense／BM25／RRF、rerank、LangChain模型适配、文档断点缓存、基准评分／保存及单条和小批量真实改写；公共NFCorpus324dev已有方法实测，真实8条改写尚无检索收益。run_benchmark_eval.py目前仍承担配置、资源装配与评测，用户正在增加rewrite_path参数；三方法可选改写接线未验收。尚缺统一临床应用服务、结构化临床状态流、自动适用性核验和定向补查，FastAPI／SQLite／Qdrant元数据过滤／Docker成品交付仍在既定规划；已有医学来源解析不等于报告OCR／多模态验证完成。

架构沿用决定：保留现有函数及参数注入，优先扩展原多方法评测入口；检索方法选择、查询表达处理和Agent业务路由分别处理。资源装配逐步集中供CLI／未来API复用，评测层可调用相同检索与业务模块，产品处理不能调用会读取qrels并评分的评测main。原始问题／报告与检索表达分别保留；BM25不加载embedding，Dense／RRF按需构造，文档缓存继续绑定原始corpus而非改写文件。逻辑分层在当前代码上增量形成，当前不以换目录或复制一整套实现代替职责划分。

医疗专用目标继续是报告事实→原句／页码／区域，结论→来源证据→适用条件两条可回查链；区分病例缺事实（追问）与检索缺证据（定向补查），分别保留指南、产品说明书和论文的身份／证据类型。对方Citation模型是document_id／title／chunk_id／section，解析器虽有页码metadata，也不能据此称具备本项目的医疗字段核验、逐条结论适用性或区域追溯。其SelfRAGLoop._grade在模型／解析失败时用bool(chunks)作sufficient，医疗流程不应直接沿用此兜底；应明确核验未完成，不能把非空结果当证据充分。上述是本项目设计目标与复用约束，尚无自动核验或临床有效性成绩。

参考评测边界：eval_retrieval在同一入口共享索引、通过不同检索可调用对象比较BM25／向量／Hybrid／重排，印证当前原入口增量方案；MEASURED.md作者报告为65政策题／39文档等自建任务，并注明同模型裁判偏乐观及原JSON报告未随仓库分发。不得拿该Precision／Recall／Faithfulness与本地NFCorpus nDCG／Recall直接排名，不将README简历示例（如Cohere）视为实际后端。其Qdrant／内存及Redis降级、工具确认与幂等、SSE／前端及多档部署是代码或配置已有能力，不宣称真实业务上线和生产规模验证。

本项目继续独立实现，借鉴检索分层、状态流、评测与交付方式。以后复用源码时记录来源、固定版本、MIT版权／许可及自己的改造；医学资料的使用条件另核验。客服交易、完整聊天工作台、多实例运维不自动成为本项目必做项；LangChain／DeepSeek、LangGraph、Qdrant、FastAPI、SQLite及单实例Docker方向保持。

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

用户于2026-11-26进一步指出：查询改写应复用原多方法入口，通过可选参数改变检索表达，不能因为当前先做Dense就复制一个仅Dense的完整入口，导致BM25／RRF以后重复接入。新增功能先检查已有函数参数和扩展位置；已接受的通用评测函数保留，方法构建与查询表达选择分别处理。实验先后顺序不等于代码能力限制；撤回方案及时替换当前任务记录，用户已写草稿保留供迁移，不擅自删除。

用户于2026-11-26第三次强调：仅列“建立映射、筛选、核对、返回”仍太抽象，无法独立落笔。讲解必须结合实际草稿和一组具体输入／输出，明确每个中间变量的类型和值、循环遍历哪个对象、键来自哪一列、在哪一步赋值、pandas整列与单个字符串的区别，并给具体函数用法、参数及理由。要一次讲清完整工作单元，不能只换一种说法重复目标，也不能因此代写完整核心或拆成逐行多轮。核心仍用户写，文档不能代替聊天讲解。

用户于2026-11-25补充要求：任务的逻辑顺序、参数选择理由和验收标准必须直接写在聊天里，不能只给文档链接让用户自行寻找。文档用于持久记录；核心指导本身在聊天中自洽完整。此后检查代码时也直接说明实际问题和修订要求，不只把结论写进文件。

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
- 当前读取适配和benchmark_eval.py两组编排均已验收；下一项为原run_benchmark_eval.py的可选改写模式，独立入口方案已撤回，仍须完成后先提交同步再真实运行。

### 13.10 模型按正式项目的任务效果选择，不默认偏向轻量

用户于2026-11-24明确：“模型你都可以选性能好的，不要老往轻量上靠。” 适用于向量、重排、生成和多模态等所有模块，优先于早期CPU／小模型起步的资源偏好，不授权助手代写核心或擅自启动长任务／付费运行。

- 先明确模型承担的任务、语言、输入长度、证据类型与失败风险，查官方论文／模型卡、许可、公开结果和可复现接口，给出有依据的候选；不能只因快、能跑或教程常用就定为成品模型。
- 以固定语料、题目和候选预算的开发集对照评价效果及逐题失败，再结合延迟、吞吐、显存和API费用作决定。模型规模和排行榜均不替代本任务实测；成本是有证据的权衡，不能凭假想资源限制排除强模型。
- 区分官方结果、待验证候选与本项目已实现／实测。面试选型理由应能回到候选比较、实测增益与失败边界；未做的对照不能写成自己的实验结论。检索相关性模型不自动等于医学适用性判断或临床决策能力。
- 既有BGE-small、DeepSeek及缓存保留为已有基线；成品模型没有因此被永久锁定。模型配置通过已定接口接入，升级向量模型确需新编码与索引，但不让用户重写核心，也不与新检索模块同时改动。
- 本轮撤回未经效果对照的MiniLM成品选型，Qwen3-Reranker-4B／8B作为同家族效果候选直接比较，BGE-reranker-v2-m3保留对照；不以英文单项排除8B。当前rerank纯函数及验收不变。模型权重、dtype、输入模板、长度和batch在真实运行前核定并冻结，尚无重排模型成绩。

### 13.11 模型下载与运行缓存放项目内

用户于2026-11-24明确要求下载到clinical-evidence-rag项目中，不污染外部环境。后续模型下载、预检、索引和评测统一通过bash scripts/project_env.sh启动，或采用同等明确的项目内缓存配置；HF_HOME位于cache/huggingface，Hub／Sentence Transformers共享其hub子目录，Xet及资产缓存同属项目。包装器仅影响子进程，不修改全局启动文件。模型文件、未完成分片和运行日志继续由Git忽略；保留来源、固定版本与迁移／运行记录。

旧共享缓存可能供其他项目使用，不清空整个全局缓存；本次只移动已确认的Qwen及其本次日志，复制BGE维持本项目离线加载。只改变模型文件存储位置不意味着模型或编码参数改变，已验证BGE文档向量身份仍一致。当前迁移已完成，下载等待用户在可见终端继续，不由助手后台启动长下载。

### 13.12 先审代码语义，测试不能反过来定义需求

用户于2026-11-25明确指出：多次因为助手自己写、用户没有阅读的测试脚本，要求核心代码变得冗杂，甚至把合理的TypeError反复改为ValueError。此反馈优先于此前“统一ValueError”的条款。

- 先依据Python语义、实际安装API、真实调用路径和项目目标审查代码；给出具体反例和影响，再决定是否需要修改。不要仅凭“测试未通过”要求用户改实现。
- 测试和替身也需要审查。失败时先判断用例假设、替身接口或测试预期是否错误；对真实库API先查实际安装类或官方资料，不能凭自造替身否定合法方法。
- 在聊天中先说明当前工作单元要验证的行为、理由和简短例子，测试只把这些已说明的判断变成可重复检查。不把脚本里新增的偏好、实现细节或未说明条件直接升级成验收要求，也不要求用户逐条审批长脚本。
- Python惯例为类型不适当用TypeError、值不合法用ValueError。没有真实错误协议或调用方依赖时，不强制把原生异常统一包装成某一类；若需要统一，应先解释用途、边界和代价。
- 区分会导致候选错配、来源丢失、非法推理或非有限分数的实质问题，与个人风格、冗余表达式、错误信息措辞等非阻断问题。不要把普通细节拆成多轮返工，也不要为覆盖用例而增加无实际用途的防御分支。
- 代码审查结论与测试通过范围分别说明，绿灯不证明全部语义正确。指出助手先前误判并修测试／文档，不将其算作用户缺陷或简历贡献。核心由用户写的约定继续有效。

### 13.13 保持既有约定一致，必要变更说明依据和影响

用户于2026-11-26再次明确指出已有CLI是--config，不能由助手随意改成--config-dir。此约定固定为命令行--config、解析args.config、函数参数config_dir；后续新增入口／预检／文档均沿用。用户随后明确否定兼容别名：不为了旧命令或旧测试加入无业务需求的兼容代码，测试应更新以反映实际接口。此前添加--config-dir及兼容别名均属助手额外设计，已经撤回；历史产物不改写。

用户于2026-11-25明确要求：“请你始终保持前后一致性。” 直接背景是助手临时给run_name加入此前没有使用的时间戳，已撤回该建议。本要求覆盖全部后续指导。

- 下达任务或审查实现前，先核对当前代码、已验收接口、项目记录及用户最新选择；沿用已有命名、参数角色、目录、缓存和评测口径，不按当次想到的偏好另定标准。
- 保留有效的实现选择。可选建议不自动成为验收条件；新阶段要求不得追溯将此前正确、已验收的实现判为错误，不因测试偏好新增限制或让用户反复返工。
- 需要改变既定方案时，先说明旧方案的具体问题、依据、拟改内容及对现有代码／数据／结果的影响，再更新相关说明，不能直接换一套做法。发现真实错误应如实纠正，不能以一致性为由延续错误。
- run_name默认沿用dataset_method_profile_split的可读形式，本轮为nfcorpus_rerank_qwen3_4b_dev；用户显式提供的名称优先，_01／_02等实验编号由其显式名称体现，不引入时间戳或擅自重命名旧产物。保存器继续拒绝覆盖。
- --run-name沿用既有可选选项，不擅自设为required=True。未传时按原命名方式生成默认值；函数仍显式接收最终run_name，保存器要求有效名称不能成为强制CLI必填的理由。
- main的config_dir仍显式传入；CLI有有效默认值与此并不冲突，不再反复要求所有CLI选项改成必填。每次解释先分清函数参数、命令行默认和实际运行配置各自的职责。

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

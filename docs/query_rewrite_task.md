# 单题查询改写：保留原问题，生成检索表达

2026-11-26接口纠正：命令行只用已有基准入口的--config，解析属性为args.config，Python函数参数仍叫config_dir。助手引入--config-dir及随后添加兼容别名均未遵守用户要求，现已撤回，不为旧测试保留额外接口；测试改用实际的--config。下文首次真实单题原命令仅作已执行历史记录，原日志、源码快照和验证摘要不改，不作为当前运行命令。

同日命名约定纠正：--run-name沿用已有入口的可选方式，不设required=True。传入时使用用户名称，省略时按数据集_方法_配置_划分生成有效默认名，如nfcorpus_query_rewrite_deepseek_flash_dev，不加时间戳。默认名在防覆盖检查及请求之前确定；保存器需要有效名称，不意味着CLI必须强制用户填写。助手此前的必填要求撤回，不能作为验收条件。

2026-11-25。重排候选对照已完成并在ac881d6归档同步。本工作单元由用户新建根目录query_rewrite.py，先完成结构化改写模型和单题函数；助手没有代写该核心文件。模型及API调用仍由用户在自己的终端执行。

## 为什么现在做

原Qwen8B Dense Top100中，32道dev题没有命中任何已标注相关文档。固定候选后的所有重排都保持Recall@100=0.39709670188154617，说明重排不能补入候选之外的文档。改写的目标是生成更适合检索的表达，后续用相同Dense配置、Top100预算和原始qrels比较召回及退化，不预设一定有效。

已核查[LangChain MultiQueryRetriever官方说明](https://reference.langchain.com/python/langchain-classic/retrievers/multi_query/MultiQueryRetriever)：它生成多条查询并合并结果。本轮先输出一条检索表达，保持候选预算，不引入多查询并集或同时调整RRF；不复制该实现，也不为参考最新文档而升级当前依赖。语料、查询和dev划分仍沿用现有NFCorpus，未新增数据来源。

已核查[DeepSeek Tool Calls官方说明](https://api-docs.deepseek.com/guides/tool_calls/)与本地已安装SDK实际实现。这里借助tool-calling格式取得结构化字段，不执行外部业务工具。模型返回的reason是改写说明，不是医学证据或条件核验结论。

## 当前进度：原多方法入口已验收，待用户运行同8题三方法对照

2026-11-26最终验收：用户已补main前置输出检查，现198行run_benchmark_eval.py SHA=bcda8cb4750fd93705f054620b19c3617f315812b7257d8cedd236ee1147c026。唯一新增8行移除后精确匹配前次审查源码，继承六方法／模式及两CLI接线结果；本轮逐一验证原模式3处和两组模式6处文件冲突，均在数据／模型／索引／缓存／保存前拒绝，旧文件不变。新临时目录实际BM25单组／两组保存3／6文件且零embedding构造。记录results/query_rewrite_shared_entry_validation_01.json；旧审查报告保留缺陷观察。无模型／GPU／API调用，核心未由助手改写。下面两段“唯一待补”属于已解决的历史记录。

2026-11-26，重读用户190行run_benchmark_eval.py，SHA=ef831e039e3f2b29019ac6c236de72441decd23f911792a331303271d4eda3ff。临时3文档／3原题／2保存记录搭配CPU假embedding及文档缓存，通过三方法×两模式6路径和真实CLI的可选默认名／显式配对名2路径：同题子集、表达／失败回退、独立组配置、来源身份及打印均正确，BM25不依赖模型配置，资源按方法构造一次。使用实际检索计算／公共评分／保存辅助，所有输出重定向临时目录，输入不变；未加载真实模型、GPU或请求API，不是检索成绩。报告results/query_rewrite_shared_entry_review_01.json。

唯一待补为原任务已约定的启动前防覆盖。临时目录仅预放改写组摘要，入口仍构造假模型／缓存、完成两组4次查询并写出原问题组三文件，直到保存改写组才被FileExistsError拒绝；原哨兵未变。当前保存器已能保护自己的既有文件，但入口须提前检查本轮所有输出，避免浪费计算和留下半套新产物。main方法检查后按模式确定一个或两个前缀，遍历三个既有后缀，任一存在先停止；不改变主业务、参数默认值或评分。用户补好保存后复核，通过再提交同步并准备真实8题运行。以下旧段落按各自日期理解，不能把当前入口仍称未接入，也不提前称最终验收通过。

2026-11-26，用户evaluate_query_rewrite_retrieval已通过语义审查和CPU假检索核对，benchmark_eval.py SHA-256为74f0a6e93044fa59a27a1b14b1c940069f988e4ad53f01c3b542e3e0f7b72720。A/B/C例子验证同一子集／标签／函数／ks、成功表达与失败回退、两次公共评分及输入不变；真实dev324＋保存8条通过16次假检索接线，各次k100。ids为Series可正常迭代及供isin使用，局部变量拼写不影响结果，不修改正确核心迎合示例。旧公共评分和冻结重排AST未变。记录results/query_rewrite_paired_eval_validation_01.json；未加载Dense模型／GPU或调用API，不是检索效果结果。

助手将save_beir_results扩展为支持明确的config.query_subset_ids。声明必须是非空、唯一且属于当前划分的题号列表；逐题表及run必须恰好覆盖该集合。摘要query_scope注明原划分数量与本次数量，原三份输入SHA仍保留；未声明仍要求整划分，不将漏题视为合法子集。临时fixture核对旧整集行为、显式子集及错误声明写前拒绝。该辅助改动不改变用户评分、错误类型或旧完整划分核验脚本；后者不应用于此次改写文本／子集实验。

用户apply_query_rewrites已通过CPU数据检查，benchmark_data.py当前SHA-256为482dea9c0f4c07e4eabb7551fd26b9af7892d4552273bc676b882ffcb698c03c，原load_beir_dataset的AST对上一提交不变。A/B/C例子验证原表顺序和非默认索引、成功表达清理、失败原题精确保留（含首尾空白）、来源及状态、额外列和输入对象不变；重复记录ID、未知ID、原文不匹配、空成功表达和未知状态均拒绝。来源标签保留用户实现llm_rewrite_query（成功）／original_fallback（失败），不因此前示例叫llm_output要求返工。真实8条ID／原文／保存表达适配一致，原JSONL未改；记录results/query_rewrite_input_adapter_validation_01.json，派生输入nfcorpus_query_rewrite_dev_8_01_retrieval_inputs.jsonl。未调用API、模型或检索，没有新的Recall／nDCG结果。

2026-11-26用户完成nfcorpus_query_rewrite_dev_8_01，8题均status=ok，1改写／7原样，0失败，已知用量8条。逐题独立汇总3260输入／706输出／3966总tokens；输入中cache_read=2048已包含在3260内，不能再加到总量。单题改写流程耗时合计7388.057ms、平均923.507ms；整个本地进程8.31秒、主机RSS峰值211596KiB、退出0且无中断，不称远程模型推理耗时。6份准备源码与快照／3份输入身份／8条题号和原文／公开配置／5份原始输出一致，原件及准备audit未改。结果_validation.json状态passed_with_semantic_observation，协议与产物核验passed；_semantic_review.json单独保存语言层面的观察，不作临床事实或总体保真率验证。

唯一变化为PLAIN-77：Phosphate Additives in Chicken Banned Elsewhere → phosphate additives in chicken banned in other countries。elsewhere没有明确是其他国家还是其他地点，输出具体化为其他国家，标为可能地域范围收窄，不能直接认证同义。reason声称改善检索但目前未测检索；7条字面未变也不等于原问题医学陈述已经核实或表达已最优。保留全部模型原输出，不为提高改写率重调提示词，也不先手工修正后再比较收益。当前只完成8题真实改写链路及逐条观察，没有nDCG／Recall收益；下一步直接复用保存结果与同一Dense配置比较。

2026-11-26，用户完成run_query_rewrite_batch.py，源码SHA-256为456a055983d902b2713e7f2de0bb19445bb9731c45edd235009323d2962d79a7。使用真实公共dev文件、真实CLI／单题和批量核心／保存辅助，只有dotenv读取及真实客户端被替换：默认命名8题和显式命名3题均按序处理、客户端只构造一次、记录及config只包含选中题目、三份产物与打印摘要一致；解析失败的已知用量、连接异常的未知用量均保留。重复运行在客户端构造前被已有文件拦住，原文件不变；非正limit在请求前拒绝。记录results/query_rewrite_batch_entry_validation_01.json。假调用及token不是实际成本，未由助手发起API或读取.env；用户原入口代码未被助手修改，尚无真实8题或改写检索成绩。

此前CLI命名纠正也在本轮归档：四入口只用--config／args.config，业务函数AST未变；旧重排CLI检查改用实际接口后通过。第一次用包名启动该检查因既有平级fixture导入路径失败，只调整进程PYTHONPATH后通过，没有为测试修改核心或异常协议。

用户完成rewrite_queries，当前query_rewrite.py的SHA-256为0767d5da2a8c4ffd25768d1b18d9f75dfe9e3210a53e6cee281886095fabf6f5。已通过四行真实DataFrame搭配假LLM的本地检查：有效改写、解析失败、连接异常、原样返回依次得到ok／error／error／ok，四题四次假invoke、顺序及原文保持、每条10字段／非负有限计时／JSON可保存；解析失败保留用量，连接异常用量未知，后续题继续，输入DataFrame不改。和save_rewrite_results实际衔接后3条已知用量／1条未知，失败的已知用量未漏计；另验证原TypeError实例向外传播。原RewriteResult和rewrite_query相对上一提交AST不变，未重新跑单题API。记录results/query_rewrite_batch_validation_01.json；假用量不是实际成本，助手未改核心或运行API，批量入口及真实8题仍未完成。

2026-11-25，用户终端完成ct_query_rewrite_single_01：status=ok，检索表达与原问题完全相同，changed=false，保留检查目的未说明；模型deepseek-flash，finish_reason=tool_calls，422输入／96输出／518总tokens，缓存读取0。本地整个进程1.47秒、主机RSS峰值96700KiB、退出0且无中断标记，不称远程模型推理延迟。日志及资源原件未改；8字段无损归档results/ct_query_rewrite_single_01_results.jsonl、_summary.json、_run.json，核验_validation.json。原始日志与用户提交内容一致，当前三份源码／配置SHA匹配入口本地验收；本次未在请求前创建代码回执或抓取原始HTTP消息，不能冒称已严格绑定请求时源码。

该次reason声称没有否定表达，原问题却有not stated；实际检索表达完整保留该条件，单题流程通过，解释文本的这个概括不准确另记ENG-026。不因此重复调用或修改提示词追单题措辞。真实单题只证明这个输入的服务链路和保留情况，没有测NFCorpus召回、指南选择或更广泛的语义忠实性。

2026-11-25，用户完成query_rewrite.py，本轮审阅源码SHA-256为eaba30a9f7efa31a0850e72a6f475eb0869fcff3c7b1a3d465889ca5fd20daed。以真实ChatPromptTemplate、RewriteResult及AIMessage搭配最小FakeLLM检查六类响应：有效改写、仅首尾空白差异、空白查询、空白原因、解析异常、parsed缺失，均符合本文返回协议；另检查四个非法输入零模型调用、网络异常原样传播及未知用量保留None。成功／失败返回均可JSON序列化，已有响应保留原问题及两类元数据，每次模型invoke一次。假响应中的token值只是检查数据，不是实际用量，助手未调用API或GPU；这不证明真实服务兼容性、医学语义保真或检索收益。原用户核心未修改，未新增隐藏测试脚本。离线观察归档results/query_rewrite_core_validation_01.json。

助手补充configs/llm_profiles.json作为公开配置；用户已实现run_query_rewrite.py，不从Notebook导入对象，核心rewrite_query的接口和8字段返回不变。入口38行源码SHA-256为8f9783b2730a8b7cb82de9f1351c1bfce708132217c768e5f6a95327c2aa2773，记录results/query_rewrite_entry_validation_01.json。修正--query后，真实argparse到实际核心的CPU假响应链路通过，配置／项目dotenv路径／单次invoke／原问题／JSON输出正确；导入及help无客户端构造，缺query在调用前拒绝。该轮dotenv及真实客户端被mock，未读密钥或发起API，假token不是成本；随后用户真实单题结果已单独记录于上文。没有修改用户实现，也未把局部变量名作为阻断。

## 已补的保存辅助：query_rewrite_io.py

助手提供save_rewrite_results(records, *, config, run_name, result_dir)。records为按输入顺序排列的字典列表，每条有query_id及核心返回的8字段，允许附加rewrite_elapsed_ms等字段，原样写入；config只传公开运行配置，不传密钥或环境内容。函数不调用模型、不改写查询、不读取环境。输出为手动run_name前缀的_results.jsonl（逐题）、_summary.json（数量和已知token）、_run.json（公开配置），返回summary字典。

逐题保留原始metadata，解析失败但有用量时仍计入已知token；缺失或不完整用量单独计数，全部未知时三项总量为None，不能假设为0。query_id要求非空字符串且同一批不重复；status沿用ok/error。写前检查字段及JSON可序列化，任意一份输出已存在即拒绝覆盖，并使用x模式创建；普通写入失败只清理本次已创建文件，原异常继续抛出。这是批次结束后的保存，不宣称具备逐请求断点恢复、跨进程锁或断电事务保证。临时目录检查已覆盖无损往返、输入不变、已知错误用量、未知用量、覆盖保护、重复ID及不可序列化配置；未为此改用户核心。

## 已完成：rewrite_queries的任务约定

现有query_rewrite.py中rewrite_queries(queries_df, *, llm)已由用户完成并通过上文本地检查，复用单题函数及其8字段协议。以下保留任务定义供后续核对。数据集入口完成后用现有load_beir_dataset(...,split="dev")得到的queries_df.head(8)作流程检查，完整评测仍用同一324道dev题。已核对前8题为PLAIN-1、PLAIN-11、PLAIN-22、PLAIN-32、PLAIN-43、PLAIN-55、PLAIN-67、PLAIN-77；按原文件顺序选取，不依检索分数或标签挑题。

输入queries_df是上游加载器已经检查的DataFrame，列为id和query；不在该函数里重新读取数据或重复整套标注验证。llm是入口创建的一份共享客户端。需要time.perf_counter计时、tqdm显示进度，以及openai.APIError处理请求本身失败；本地openai1.109.1已核实连接／超时／限流／HTTP错误类都继承APIError，无需新安装。

完整逻辑顺序：

1. 建立结果列表，用tqdm包住queries_df.iterrows()，total=len(queries_df)，desc="改写查询"，保证输入顺序。row["id"]只用于记录query_id，模型只接收row["query"]，不传qrels或标注答案。
2. 对每题在调用前取perf_counter，执行一次rewrite_query(row["query"],llm=llm)，不在循环中创建客户端或再次结构化包装。
3. 核心正常返回时，不论status为ok还是error，都原样保留8字段；已有响应的解析失败不是抛出的API异常，用量仍保留。
4. 仅捕获APIError，为这一题构造相同8字段的失败结果：original_query原样、status=error，retrieval_query／changed／reason／usage_metadata／response_metadata均None，error为含异常类型及具体消息的字符串。此时没有有效原始响应，用量未知；不自动重试、回退或丢弃该题。数据／编程异常自然抛出，不用except Exception把它们伪装成API失败。
5. 单题处理后停止计时，将差值乘1000作为rewrite_elapsed_ms。它包含单题提示构造、请求、解析及失败处理，不含客户端创建、进度输出或文件保存；不直接称远程推理时间。
6. 每条结果加query_id=row["id"]及rewrite_elapsed_ms，追加到列表，结束后返回列表。它共10字段，不改核心函数返回；函数不调用保存辅助，输出落盘由后续入口统一执行。

验收看正常／原样／解析失败／请求异常均每输入一条就有一条记录，ID顺序一致；有有效输入的请求每题最多调用一次；失败不伪造changed或token，编程错误不吞掉，计时非负。先审实际代码再做最小CPU假调用检查，真实8题仍由用户终端执行。保存辅助已能接收这批记录，接入入口后复用同一模型配置和原文档向量；当前尚无8题API输出、批量缓存、改写检索或收益结果。

## 已完成：run_query_rewrite_batch.py任务及接口

用户已完成独立批量入口run_query_rewrite_batch.py，单题入口继续保留。main(config_dir, data_dir, *, profile_name, split, limit, run_name, result_dir)串起配置、数据读取、一份客户端、批量核心和保存辅助；上述本地检查通过，归档同步后由用户执行真实8题。以下保留已完成的任务和接口，未改变核心／模型配置或标注。

除已有argparse／json／Path／load_dotenv／ChatDeepSeek，导入benchmark_data.load_beir_dataset、query_rewrite.rewrite_queries和query_rewrite_io.save_rewrite_results；无需新安装。参数职责：config_dir是公开配置目录，data_dir是准备好的BEIR数据集目录，profile_name选择deepseek_flash，split本轮dev，limit本轮8，run_name可由用户指定如nfcorpus_query_rewrite_dev_8_01，省略时沿用既有规则生成默认名，result_dir保存本次三份JSON产物。

main顺序固定为：

1. 拒绝非正limit；先沿用既有规则确定有效run_name：显式名称优先，省略时按数据集_方法_配置_划分生成默认名，不使用空字符串。按确定的名称检查result_dir内_results.jsonl、_summary.json、_run.json是否任一已存在；已有时在请求前报错，避免付费后才发现不能保存。不要调用保存辅助生成空文件来做预检查。最终保存辅助仍保留独占创建保护。
2. 按已完成单题入口的方式读取llm_profiles.json并选当前profile；使用load_beir_dataset(data_dir,split=split)，忽略本阶段不用的corpus_df与qrels，只使用返回的queries_df。qrels仅由现有加载器确定split成员，不传给模型。
3. selected=queries_df.head(limit)，保留原文件顺序，空选择在请求前报错。limit超过总题数时自然选到全部，元数据分别记录请求limit和实际query_count，不伪称选满。模型只会接收选出的query文本。
4. 在main内按原入口显式加载项目.env，override=False；用同一profile构造一次ChatDeepSeek，调用一次rewrite_queries(selected,llm=llm)，不在外层再逐题调用或添加重试／回退。
5. 构建公开config字典，至少包含dataset_name=data_dir.resolve().name、data_dir的绝对路径字符串、split、limit、query_count=len(selected)、query_ids=selected["id"].tolist()、profile_name、llm_profile=当前profile。不要把DataFrame、客户端、异常对象或密钥放入config。
6. 调用save_rewrite_results(records,config=config,run_name=run_name,result_dir=result_dir)，main返回它的summary。保留失败记录，不只保存status=ok。它生成三份原件，外层终端命令后续另保护run.log与resources.txt，二者分层防覆盖。

CLI位于if __name__ == "__main__"，Path默认值沿用项目目录：--config（Path，configs）、--data-dir（Path，data/external/nfcorpus/prepared/nfcorpus）、--profile（deepseek_flash）、--split（dev，choices沿用train/dev/test）、--limit（int，8）、--run-name（可选，显式名称优先，省略时生成既有风格默认名，不加时间戳）、--result-dir（Path，results）。正式运行命令仍可显式指定实验编号名称；args.config传给main的config_dir，不改既有函数参数。解析后按上述main签名传参，run_name无论来自显式值或默认生成都要传入，打印json.dumps(summary,ensure_ascii=False,indent=2)。导入与--help不读.env、不创建客户端或请求。

验收先看原数据前8题按序交给批量核心、客户端构造一次、批量调用一次、配置为可JSON保存的公开值、既有输出或无效limit在请求前拒绝、成功／失败记录都交给保存辅助。之后才由用户跑真实8题并复查改写忠实性与成本；完整召回比较仍为同一324条dev和原Qwen Dense文档缓存，产生新候选，当前不执行或声称该结果。

### 已执行：NFCorpus dev前8题命令（历史记录）

本地检查、归档提交并同步后执行。run-name在本命令中显式指定编号便于保留这次实验，CLI选项仍可省略。运行前检查5份原始输出，避免外层time／tee先覆盖；代码与输入准备记录为results/nfcorpus_query_rewrite_dev_8_01_audit.json及_source_snapshot目录，不列入这5个原始输出保护项。助手只准备材料，真实API仍由用户执行。

```bash
# 进入项目目录。
cd /home/wzh/clinical-evidence-rag
# 保留Python失败时的管道退出状态。
set -o pipefail
# 在启动计时和日志写入前，保护本轮五份原始输出。
if [[ -e results/nfcorpus_query_rewrite_dev_8_01_results.jsonl || -e results/nfcorpus_query_rewrite_dev_8_01_summary.json || -e results/nfcorpus_query_rewrite_dev_8_01_run.json || -e results/nfcorpus_query_rewrite_dev_8_01_run.log || -e results/nfcorpus_query_rewrite_dev_8_01_resources.txt ]]; then
  printf '%s\n' '本轮记录已存在，请改用新的运行编号。'
else
  # 复用同一配置运行前8道dev题，保存实时输出和资源统计。
  bash scripts/project_env.sh \
    /usr/bin/time -v \
    -o results/nfcorpus_query_rewrite_dev_8_01_resources.txt \
    /home/wzh/miniforge3/envs/all-in-rag/bin/python -u run_query_rewrite_batch.py \
    --config configs \
    --data-dir data/external/nfcorpus/prepared/nfcorpus \
    --profile deepseek_flash \
    --split dev \
    --limit 8 \
    --run-name nfcorpus_query_rewrite_dev_8_01 \
    --result-dir results \
    2>&1 | tee results/nfcorpus_query_rewrite_dev_8_01_run.log
fi
```

运行后先贴终端摘要或错误。助手再读取逐题JSONL，检查8条题号和原文、改写是否篡改语义、失败处理、实际用量及耗时。单题与整个进程计时按各自范围报告；changed多或少都不直接说明质量。此轮不运行Dense或重排、不改文档缓存，也不将它当作324题检索评测；通过后再推进已保存改写与同一Dense配置的对照。

## 已完成：apply_query_rewrites任务及接口

用户在现有benchmark_data.py中新增apply_query_rewrites(queries_df, rewrite_records)，它只把已保存改写适配成检索输入，不读文件、不请求模型、不检索或保存。原有load_beir_dataset及查询改写核心不改，无新依赖；输入queries_df是加载器返回的完整原问题表（当前324条，id／query），rewrite_records是本批JSONL读取的字典列表（当前8条）。函数仅返回这批记录覆盖的题目，按原问题表顺序排列；不把其余316题混入8题对照。后续完整324条复用同一接口。

逻辑和字段约定：

1. 用record["query_id"]建立映射，重复ID先报错，避免字典静默覆盖。同原问题id列比较，改写记录中的未知ID拒绝，不能悄悄丢弃。原问题ID唯一性已由现有加载器检查，无需再重复整套数据校验。缺失字段等保留自然异常，不强制包装统一类型。
2. 使用queries_df["id"].isin(...)选出映射覆盖的行，并.copy()取得副本，保持原文件顺序。将副本的原query保存在original_query列。对每题检查record["original_query"]与当前原问题一致，避免把另一版问题的改写挂到同ID。
3. status=ok时，使用保存的retrieval_query作为新query；清理后须非空。不重新让模型改写，不依据人工语义观察手工更正PLAIN-77。用户实现采用query_source="llm_rewrite_query"，rewrite_status="ok"；即使changed=false，也表示采用了这次LLM输出，不等于文字发生变化。保留此有效命名，后续记录一致。
4. status=error时，检索输入显式使用该题原问题，记录query_source="original_fallback"、rewrite_status="error"。这是本阶段公开定义的检索层失败回退，为全题对照保留失败题；原始改写记录的error、未知或已有token均不修改，原单题函数仍返回error而不回退。未知status拒绝。不能把失败题从评测中剔除后只报成功题收益。
5. 返回DataFrame，保留id以及供检索的query，新增original_query／query_source／rewrite_status；输入表和rewrite_records都不修改。常见当前输入2列时输出为5列，其他已有列不需要丢掉。函数不接收qrels，标注留在评测层。

本轮只写函数保存，助手审核后用最小CPU例子核对。验收例：原问题A／B／C，改写记录顺序B成功／A失败，返回顺序A／B，C不进入此次比较；A保留原题且明确error／fallback，B使用保存表达，两个原问题仍可回查，输入不变；重复ID、未知ID、原题不匹配不能静默通过。不要为样例增加无业务用途的兼容或异常分支。

接线时还要按返回ID筛选同一份qrels，满足现有evaluate_beir_retrieval对查询与qrels键集合一致的要求；原题组与改写组用相同8题、相同qrels和Qwen Dense配置，复用原文档向量，重新生成检索候选。已有原冻结Top100只作基线记录，不能当新表达已完成检索。apply_query_rewrites已实现并核对，仍无新Dense结果；324题完整比较待后续，8题只用于流程和逐题观察。

## 已完成：evaluate_query_rewrite_retrieval

在现有benchmark_eval.py增加evaluate_query_rewrite_retrieval(queries_df, qrels, retrieve_fn, *, rewrite_records, ks=(10,100))，前三参数沿用evaluate_beir_retrieval；新增导入benchmark_data.apply_query_rewrites。它编排同题原问题与保存表达两组评价，不构造模型、不读取或保存文件、不调用DeepSeek，实际检索由传入的retrieve_fn完成。先写函数保存、CPU假检索核对，之后才由用户入口加载同一Qwen模型／文档缓存真实运行。

输入queries_df为原始324条表、qrels为324个题号映射到文档等级字典、rewrite_records为当前保存8条，retrieve_fn是已有可调用对象（接收query字符串与k，返回含id／score的候选列表），ks默认(10,100)。流程只有数据对齐与两次复用现有评分：

1. rewritten_queries_df=apply_query_rewrites(queries_df,rewrite_records)，当前得到8行带original_query／query_source／rewrite_status的表。用户ids=rewritten_queries_df["id"]为包含8个字符串题号的Series，供isin和后续迭代正常使用，无须改成tolist；并非按range(8)取qrels，也不更改问题ID。
2. original_queries_df用queries_df["id"].isin(ids)筛选并.copy()，仍保留原query；与rewritten_queries_df对应同一8题和顺序。不能把整张324题原表同8题改写表比较均值。
3. selected_qrels用{query_id:qrels[query_id] for query_id in ids}得到8个外层键；每题内层文档ID和相关等级原样保留。例如原qrels有A/B/C，ids为A/B，就只取qrels[A]和qrels[B]，不重新标注。现有公共评分函数要求这8键与查询ID集相同。
4. 用同一个retrieve_fn和同一个selected_qrels／ks，分别调用evaluate_beir_retrieval(original_queries_df,...)与evaluate_beir_retrieval(rewritten_queries_df,...)。每次返回(eval_df,run)：eval_df为逐题指标／耗时表，run为题号→文档ID→检索分数字典。这里不另写检索循环或评分公式，不额外过滤失败回退题。
5. 返回普通字典，键original对应{"eval_df":original_eval_df,"run":original_run}，键rewritten对应相同结构的新表达结果，键query_inputs对应rewritten_queries_df，留存原问题与来源以便后续保存和逐题分析。这是内存中的对象集合，其中有DataFrame，不能直接json.dumps整个字典；后续入口分别交已有保存辅助，不在本函数里写文件或打印。

完整中间规模为原表324／原qrels324→适配表8／ids8→原题子表8／qrels子集8→两份各8行eval_df及两份各8个题号的run。相同检索器使两组使用同一模型／正文缓存／候选预算；8条未证明统计收益，仅用于接线和逐题差异。ks原样传给两组。原题数据／qrels／改写记录不修改，结果来源标签沿用用户已有llm_rewrite_query，不追溯改前一步实现；不新增异常包装或用旧测试限定风格。

验收按实际语义看：同一批题、相同标签和检索函数、各调用公共评测一次；原题组收到原query，新表达组收到保存query；query_inputs保留原文及失败回退状态，完整返回两组表与run。此函数已通过上文本地检查；原运行入口的可选改写模式仍待用户实现，没有真实改写召回结果。

## 已完成：原run_benchmark_eval.py支持三方法可选改写

2026-11-26方案纠正：用户指出独立Dense入口重复原有模型／缓存／保存，且后续BM25／RRF仍需接入。助手核对后撤回独立入口任务，改为原入口增量扩展；“先做Dense实验”不应变成架构限制。已验收evaluate_query_rewrite_retrieval接收通用retrieve_fn，无须改动，三方法均可复用。用户已开始未跟踪run_query_rewrite_retrieval_eval.py草稿，助手不修改或删除，可用片段由用户迁回原入口。原入口现已完成并通过上文本地验收；以下保留任务定义，真实分数待下方用户执行。

本轮只修改run_benchmark_eval.py，沿用原method、位置参数和默认值。main接口变为main(method, config_dir, data_dir, split, cache_dir, run_name, *, config_embedding_model="bge_small", rewrite_path=None)，CLI新增--rewrite-results（type=Path，默认None），将args.rewrite_results传给rewrite_path。保留--config／args.config、--method及现有可选run-name默认公式f"{data_dir.name}_{method}_{config_embedding_model}_{split}"，不加时间戳或兼容别名，不顺带新增result-dir等参数。

参数本身同时提供开关和所需输入：未传时rewrite_path是None，执行原全划分单组评测；传入时是Path，读取保存的改写记录，以同一method比较原问题／检索表达两组。判断用is None／is not None，无需另增--rewrite布尔值，也不在入口重新请求DeepSeek。改写记录生成仍由既有独立生成入口负责，三种检索方法共享同一份记录，避免重生成而同时改变输入与成本。

完整修改位置与控制流：

1. 新增标准库hashlib及evaluate_query_rewrite_retrieval导入；不另加LLM依赖。项目results路径保留为原目录，提为局部result_dir供检查和保存复用。模型／索引构造前，根据模式选择输出前缀：未传文件为run_name，传文件为run_name加_original和_rewritten。每个前缀检查_results.jsonl／_run.json／_summary.json，分别保护三份或六份输出；已有即停止。外层log／resources由后续用户运行命令保护。
2. 原load_beir_dataset仍调用一次，返回完整corpus_df（3633）、queries_df（324）及qrels（324键）。若rewrite_path非None，rewrite_bytes=rewrite_path.read_bytes()是bytes，decode("utf-8").splitlines()得到行字符串，再逐非空行json.loads组成rewrite_records（当前8个dict）。rewrite_sha256用hashlib.sha256(rewrite_bytes).hexdigest()计算同一读取内容的指纹，不在检索后重新读取另一份字节。无需head(8)或新增limit，子集由记录中的题号决定。
3. 原embedding_profiles.json的读取、profile选择及维度／长度检查移到if method in ("dense","rrf")内，模型构造和prepare_document_embeddings也保留在这里。移除旧的BM25+Qwen拒绝，因为BM25根本不使用此模型配置；不虚构dense元数据。纯BM25路径只需原数据和BM25索引，不依赖embedding配置文件存在。Dense／RRF继续固定原profile、corpus.jsonl、cache_dir、chunk_size=512及profile dimension，复用原文档缓存。原model profile选项／默认值不变。
4. 原BM25构建仍在if method in ("bm25","rrf")内，k1=1.5、b=0.75、epsilon=.25不变。原method选择retrieve_fn的三分支保留：dense_retrieve_fn、bm25_retrieve_fn或RRF的partial，RRF每路candidate_k100、rrf_constant60不变。无论表达是否改写，方法配置完全相同；原dense／bm25／rrf子配置及公共字段布局沿用。
5. 三方法选出retrieve_fn后，才按rewrite_path分叉。None时沿用evaluate_beir_retrieval及原单组save_beir_results，保留原run_name、整集覆盖和summary返回。非None时调用evaluate_query_rewrite_retrieval(queries_df,qrels,retrieve_fn,rewrite_records=rewrite_records,ks=(10,100))，注意传已有当前方法retrieve_fn，而非写死dense_retrieve_fn；其内部自动得到两组同8题和原qrels，不修改公共评分。
6. 改写模式得到paired字典，original／rewritten各含eval_df（8行）和run（8题排名字典），query_inputs为带原题及来源的DataFrame。公共config增加query_subset_ids=paired["query_inputs"]["id"].tolist()及rewrite_source={"path":str(rewrite_path.resolve()),"sha256":rewrite_sha256,"query_inputs":paired["query_inputs"].to_dict(orient="records")}。retrieval_method仍为当前method，改写是查询输入选择，不能把它写成dense或新方法枚举；标注和数据文件保持原件。
7. 仅改写分支建立summaries={}，for variant in ("original","rewritten")两轮：group=paired[variant]，group_config={**config,"query_variant":variant}，调用save_beir_results(group["eval_df"],group["run"],config=group_config,run_name=f"{run_name}_{variant}",result_dir=result_dir)，将返回值放summaries[variant]，最后返回两组摘要。不能直接json.dumps含DataFrame的paired，也不在保存层重新评分或改写文本。
8. CLI将新参数传给main，并按相同模式处理返回值：None时沿用summary["metrics"]打印；传文件时从两个组摘要各取metrics后打印。不要只改main返回结构却保留单组打印，导致执行成功后取不到metrics。旧调用未传新参数时返回协议不变；新增模式的两组结构明确记录，不为统一返回结构追溯改旧调用。

功能与资源矩阵：

| method | 不传--rewrite-results | 传保存JSONL | 只构造一次的资源 |
| --- | --- | --- | --- |
| bm25 | 原全划分单组 | 同题原文／保存表达两组 | BM25索引，不加载embedding |
| dense | 原全划分单组 | 同题原文／保存表达两组 | embedding模型＋文档向量缓存 |
| rrf | 原全划分单组 | 同题原文／保存表达两组 | BM25索引＋embedding模型／向量，两组共享 |

本轮先由用户修改保存，助手重读实际代码，再用CPU假模型／缓存检查原无改写路径及三方法改写接线、资源构造次数、两组标签／题号／表达、原配置保持、JSON可保存和模型前防覆盖。语义正确性优先，不为测试改变异常类型或变量名，不加载GPU／模型或请求API。草稿暂不自动删除；完成迁移后再按用户授权整理。

实验先复用同一8条验证流程，三方法分别运行；每次在方法内只改变检索表达。完整324条改写准备后使用同一入口，无需新函数。比较BM25原文vs BM25改写、Dense原文vs Dense改写、RRF原文vs RRF改写，之后可横向比较共同题集上的方法差异；不能直接拿8题改写均值与旧324题均值相比。此时不接重排、不改变RRF预算或提示词，保存表达中的PLAIN-77语义观察仍保留。运行前先提交同步，再给用户终端命令；检索计时不含此前改写API耗时，不宣称端到端成本或临床效果。

## 待用户执行：同8题三方法检索对照

本地验收后先提交同步，再准备results/nfcorpus_query_rewrite_retrieval_dev_8_01_audit.json及_source_snapshot。回执绑定执行提交、已验收源码／embedding配置、三原数据、已保存改写及原Qwen文档缓存身份；其核验范围仅为列明材料，旧历史资源异常继续披露，不声称全历史未变。助手只做准备，不运行下列真实实验。

输入已核对：NFCorpus3633文档／324dev，保存改写8条与原dev前8题相同，其中1条文字变化；原JSONL SHA仍为af5e6ad0ffdf16851f0caa92be9bed683726417a10cb78fb2b912b5e3fa6c1fb。Qwen文档缓存f57e042cca31d1d4e4fcc61d84d576d2b6ad4b247c7490d03188c16144fd54c1已完整，3633×4096 FP32、原corpus身份一致；准备时三方法各8份原始输出均不存在。不会重新请求DeepSeek，Dense／RRF复用文档缓存。BM25不传embedding模型选项；两方法明确指定qwen3_8b，原batch／prompt／RRF预算不变。

以下终端循环依次运行BM25、Dense、RRF；每种方法两组各8题。各运行前缀分别为nfcorpus_bm25_query_rewrite_dev_8_01、nfcorpus_dense_qwen3_8b_query_rewrite_dev_8_01、nfcorpus_rrf_qwen3_8b_query_rewrite_dev_8_01。每方法检查8个原始输出，外层time／tee也受保护；遇冲突或运行失败即停止，不自动覆盖或生成时间戳。已完成方法的记录保留，重试手动换编号并按实际尚未运行的方法执行。

```bash
# 进入项目目录。
cd /home/wzh/clinical-evidence-rag
# 保留Python失败时的管道退出状态。
set -o pipefail
# 三种方法依次运行，各自比较同8题的原问题与保存表达。
for clinical_method in bm25 dense rrf; do
  # BM25使用自己的名称，不传不需要的embedding配置。
  if [[ "$clinical_method" == bm25 ]]; then
    clinical_run_name="nfcorpus_bm25_query_rewrite_dev_8_01"
    clinical_embedding_args=()
  else
    # Dense和RRF固定使用原Qwen8B配置及文档缓存。
    clinical_run_name="nfcorpus_${clinical_method}_qwen3_8b_query_rewrite_dev_8_01"
    clinical_embedding_args=(--config-embedding-model qwen3_8b)
  fi
  # 启动time和tee前，检查两份外层记录及两组三份JSON。
  clinical_conflict=""
  for clinical_suffix in run.log resources.txt original_results.jsonl original_run.json original_summary.json rewritten_results.jsonl rewritten_run.json rewritten_summary.json; do
    if [[ -e "results/${clinical_run_name}_${clinical_suffix}" ]]; then
      clinical_conflict="results/${clinical_run_name}_${clinical_suffix}"
      break
    fi
  done
  # 发现旧文件时停止，保留原件，重试时手动更换本轮编号。
  if [[ -n "$clinical_conflict" ]]; then
    printf '已有记录，停止运行：%s\n' "$clinical_conflict"
    break
  fi
  # 说明当前运行的方法；Python中会显示两组评测进度。
  printf '开始运行：%s\n' "$clinical_run_name"
  # 离线复用本地模型及已保存改写，保留资源统计和实时日志。
  if ! HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 bash scripts/project_env.sh \
    /usr/bin/time -v \
    -o "results/${clinical_run_name}_resources.txt" \
    /home/wzh/miniforge3/envs/all-in-rag/bin/python -u run_benchmark_eval.py \
    --method "$clinical_method" \
    --config configs \
    --data-dir data/external/nfcorpus/prepared/nfcorpus \
    --split dev \
    --cache cache/embeddings \
    "${clinical_embedding_args[@]}" \
    --rewrite-results results/nfcorpus_query_rewrite_dev_8_01_results.jsonl \
    --run-name "$clinical_run_name" \
    2>&1 | tee "results/${clinical_run_name}_run.log"; then
    # 任意方法失败后停止，不继续启动后续方法。
    printf '运行失败，已停止：%s\n' "$clinical_run_name"
    break
  fi
done
```

验收看三种方法各有original／rewritten摘要、两组各8条记录、相同题号／原qrels、缓存身份与预期配置；两组进度各到8/8，原问题与保存表达逐题对应。7条字面原样用于一致性观察，不预先保证浮点数逐位相同；唯一变化PLAIN-77的地域范围疑点仍保留，不能只看收益判同义。原问题／改写均值只在同8题内比较，不同旧324题均值直接相减。检索阶段耗时不包括先前DeepSeek改写，整进程资源另列，不拼成未经测量的端到端延迟。该8题是流程及个案验证，后续完整324题三方法对照仍须完成；当前未产生真实改写检索成绩。

用户运行后贴终端三组指标或错误；助手再只读独立复算两组原qrels指标、核验文件／配置／来源与缓存，保存逐题差异及限制，通过后先归档同步再进入下一单元。

## 已完成的单题入口任务（历史定义）

实现main(config_dir, *, profile_name, query)，其中config_dir使用Path，profile_name指定配置名，query是单条原问题。按以下顺序完成：

1. 使用json.loads和Path.read_text(encoding="utf-8")读取config_dir / "llm_profiles.json"，按profile_name选择配置。
2. 用Path(__file__).resolve().parent定位项目根目录；在main内调用load_dotenv(root / ".env", override=False)，供SDK读取DEEPSEEK_API_KEY。不要打印密钥、环境内容或完整客户端对象，配置文件也不存密钥。助手未读取.env。
3. 从langchain_deepseek导入ChatDeepSeek，以ChatDeepSeek(**profile)构造客户端。**把字典键值展开为关键字参数；本地0.1.4已核实接受这些参数，api_base是本安装类实际使用的地址字段。不要再套一层with_structured_output，核心已经负责包装。
4. 从query_rewrite导入rewrite_query，只调用一次rewrite_query(query, llm=llm)，main返回其字典，不增加重试、检索、循环或回退。
5. 在if __name__ == "__main__"里用argparse接收--config（type=Path）、--profile（默认deepseek_flash）、--query（required=True），将args.config传给main的config_dir，使用json.dumps(result, ensure_ascii=False, indent=2)输出。允许配置目录默认项目configs，但实际运行命令必须显式传--config。不在导入模块时构造客户端或调用API。

所需库：标准库argparse／json／pathlib.Path，已安装的dotenv.load_dotenv及langchain_deepseek.ChatDeepSeek，加上自己的query_rewrite.rewrite_query。不需要SentenceTransformer、LangGraph或新依赖。

### 参数理由与真实调用验收

公开配置沿用早先B1的deepseek-flash、temperature=0、max_tokens=2048、非思考模式，并使用官方api_base。2026-11-25再次核对[模型说明](https://api-docs.deepseek.com/quick_start/pricing/)及[工具调用说明](https://api-docs.deepseek.com/guides/tool_calls/)，当前接口支持该模型及非思考工具格式。temperature=0用于减少采样变化，不承诺完全确定；2048是输出上限而非每次实际消耗；extra_body显式禁用思考。入口操作参数timeout=60限制等待，max_retries=0禁用SDK自动重试，以免一次函数invoke背后出现额外自动请求。服务端模型名称是API别名，不等同固定开源模型revision，保留真实响应metadata，不虚构锁定版本。配置不含密钥。

用户先写入口并保存，助手审核且同步后再给终端执行命令；助手不发起真实请求。首个输入固定为：Which reporting framework applies to a chest CT report with a pulmonary nodule when the examination purpose is not stated? 它只用于验证缺失条件是否保留，不是新增人工标注或检索成绩。

真实单题验收看status=ok、两个非空字段、Python计算的changed、真实usage_metadata及response_metadata，确认检查目的缺失仍然缺失，没有被改成筛查或偶发发现，也没有生成医学回答。changed=False合法，具体措辞不设标准答案；finish_reason若为tool_calls可能是结构化工具格式的正常结束，不强求stop。若失败，保留本次真实错误和用量再排查。成功后才做保存辅助和少量开发题，后续批量编排仍由用户完成。当前不加载向量或运行324次API，执行命令继续通过bash scripts/project_env.sh。

### 首次真实单题命令：已由用户执行，保留供回查

入口本地验收、归档并同步GitHub后执行。准备时确认下列两个01文件尚不存在；每次启动time和tee前仍检查，重复运行手动改02等编号。日志保存终端输出，资源文件记录整个本地进程，不当远程模型推理耗时；结构化JSON保存辅助尚未加入。此次只有一条query、不加载本地模型或文档向量，SDK max_retries=0。

```bash
# 进入项目目录。
cd /home/wzh/clinical-evidence-rag
# 保留Python失败时的管道退出状态。
set -o pipefail
# 在启动计时和日志写入前，保护已有记录。
if [[ -e results/ct_query_rewrite_single_01_run.log || -e results/ct_query_rewrite_single_01_resources.txt ]]; then
  printf '%s\n' '本轮记录已存在，请改用新的运行编号。'
else
  # 通过项目环境执行一条真实请求，同时保存实时输出和资源统计。
  bash scripts/project_env.sh \
    /usr/bin/time -v \
    -o results/ct_query_rewrite_single_01_resources.txt \
    /home/wzh/miniforge3/envs/all-in-rag/bin/python -u run_query_rewrite.py \
    --config-dir configs \
    --profile deepseek_flash \
    --query 'Which reporting framework applies to a chest CT report with a pulmonary nodule when the examination purpose is not stated?' \
    2>&1 | tee results/ct_query_rewrite_single_01_run.log
fi
```

用户提交本次完整JSON或错误后再检查，不用旧Notebook输出推断新入口成功，也不能把本地假响应写成真实服务结果。

## 文件和库

用户写query_rewrite.py；本轮不读取数据文件、不保存JSONL，也不从Notebook导入。现有检索／重排模块不改。后续运行入口负责构造ChatDeepSeek客户端并作为llm参数传入，与已有reranker参数的依赖注入方式相同；本函数不读取密钥、不在导入时创建客户端。

已实查当前环境：langchain-deepseek=0.1.4、langchain-core=0.3.71、pydantic=2.14.3，无需安装或升级。需要了解的对象如下：

| 对象 | 导入位置 | 用途 |
| --- | --- | --- |
| BaseModel、Field | pydantic | 描述模型必须返回的字段及最小长度 |
| ChatPromptTemplate | langchain_core.prompts | 将固定指令和原问题组成消息 |
| ChatDeepSeek | langchain_deepseek | 由后续入口创建的llm类型；核心函数接收对象即可 |

## 一、用户定义RewriteResult

它继承BaseModel，只定义两个模型生成字段：retrieval_query是非空字符串，表示单条检索表达；reason是非空字符串，简短解释为何改写或保留原文。Field可使用min_length=1和description，description应解释字段用途。min_length=1本身不能拒绝全空格，因此仍需在处理结果时检查strip后的文本。

不要让模型生成original_query、changed或token数量。原问题和改写是否变化可以由Python确定，token数量必须从真实响应元数据取得。

## 二、用户实现rewrite_query(query, *, llm)

query是原始问题字符串。当前先处理NFCorpus的单条英文问题；未来报告加问题可以由上游组合成同一输入字符串，原报告事实仍需保留。llm是后续入口已经创建的ChatDeepSeek对象。本轮不另定模型名称／端点，不用占位凭证或从Notebook取得对象。

函数按下列顺序完成一个完整工作单元：

1. 在调用前拒绝非字符串和空白query。原query原样保留供返回，避免改写覆盖评价／回答使用的原文。
2. 用ChatPromptTemplate.from_messages组成system指令与human问题。system要求只改写检索表达、不回答；可整理措辞和关键词；保留原意及已给的人群、数值／单位、否定和检查目的；未知条件仍未知；不得猜测诊断、药物、指南名或把缺失条件改成已知。语言与输入保持一致；无必要改写时可原样返回。
3. 通过llm.with_structured_output包装RewriteResult，显式method="function_calling"和include_raw=True。schema使用刚定义的Pydantic类；不传strict。method使用已安装SDK实际支持的接口，include_raw保留响应元数据和解析错误。本轮先固定普通结构化工具格式，不切换服务端beta端点或另接模型服务。
4. 进行一次invoke。可以先用prompt.invoke得到消息再调用结构化模型，也可以用prompt与结构化模型的管道；选可解释的写法，不强制两种风格之一。human模板变量名需与invoke输入字典一致，例如使用{query}时传对应query键。
5. 收到结构化返回值后，先从raw取得usage_metadata和response_metadata。即使输出解析失败，这次调用也可能已产生token成本，不能先抛出解析错误而丢掉这些信息。
6. 没有parsing_error且parsed存在时，才读取字段。retrieval_query和reason去首尾空白后均须非空。成功时status="ok"、error=None，由Python比较最终检索表达与query.strip()得到changed；大小写、标点等变化不额外忽略。
7. 已有raw响应但解析失败、parsed缺失或结果全空白时，返回status="error"及清楚的error说明，保留原问题和两类响应元数据，retrieval_query／changed／reason设为None。不自动重试或悄悄用原问题兜底，批量运行的回退策略在后续单元明示。
8. 返回下表中的普通字典。输入错误仍在调用前报错，invoke本身的网络／API异常没有有效raw响应时沿用原异常向上传递，不强行包装。不要在函数里打印、调用检索或保存文件。

异常类型按实际语义使用，不为了测试将TypeError／ValueError等一律包装成同一种异常。本轮验收先审用户代码与真实SDK语义，再检查调用和数据边界。

| 返回字段 | 来源及含义 |
| --- | --- |
| original_query | 输入query原样保存 |
| status | Python生成的ok或error，不让模型自己决定是否成功 |
| retrieval_query | 成功时为去首尾空白的单条检索表达，输出失败时None |
| changed | 成功时为Python比较后的布尔值，输出失败时None |
| reason | 成功时模型生成的改写说明，不能作为医学依据；输出失败时None |
| usage_metadata | 原始AIMessage.usage_metadata，原样保留；未知时保留None，不伪造为0 |
| response_metadata | 原始AIMessage.response_metadata，保留模型／结束原因等真实响应信息 |
| error | 成功时None；响应解析／内容失败时清楚说明原因，不返回不可JSON序列化的异常对象 |

## 三、已核实的SDK返回结构

本地ChatDeepSeek.with_structured_output支持schema、method、include_raw、strict等参数；method="json_schema"在这个安装版本内会转为function_calling，因此本轮直接写明function_calling。include_raw=True时返回普通字典，其raw为原始消息，parsed在成功时为RewriteResult实例，parsing_error在无解析错误时为None。原始AIMessage包含usage_metadata与response_metadata字段。

结构概念为raw／parsed／parsing_error三个槽位，解析失败或模型没有返回目标结构时不能只访问parsed.retrieval_query继续。Pydantic对象的字段使用属性访问，与外层字典键访问区分。保存整个raw对象不是本函数任务，先返回上述可回查的两类元数据。这里区分“请求本身失败”和“已有响应但不能作为成功改写”：后者明确返回错误状态并保留成本，方便后续批量运行记入全部题目，不遗漏失败调用。

## 四、验收与本轮结束位置

用户先写类和函数，保存后贴代码；这一轮先审代码，不直接跑324次API。检查意图提前固定：

- 正常路径只调用模型一次，原问题完整进入提示并原样返回，输出8字段齐全且status=ok。
- 无须改写时允许retrieval_query等于原问题、changed=False；是否相同由Python计算。
- 有效新表达时changed=True；空白输入在调用前报错；已有响应的空白改写、解析错误或parsed缺失返回status=error而非成功，不能伪造changed=False或默默回退。
- usage_metadata和response_metadata来自raw，不能使用模型自己生成的token数字。
- 解析失败仍保留真实元数据，API调用本身抛错时保留原异常；不是把所有错误统一为某一种异常类型。
- 提示中有事实保留及不补未知条件的约束，但不能因此宣称已经自动验证所有改写的医学语义；语义保真要随后用开发样本检查。

验收后再由用户用入口创建的真实ChatDeepSeek对象跑一题，核对字段、token用量、结束原因和原意；后续助手补保存辅助，用户写批量编排。单题调用不会重建文档向量。批量改写会生成新的检索候选，不能把原冻结Top100继续当作改写后的召回结果；先测Dense召回变化，再接已经固定的重排，避免同时改变多个因素。当前这些后续辅助和收益都尚未实现。

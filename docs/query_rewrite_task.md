# 单题查询改写：保留原问题，生成检索表达

2026-11-25。重排候选对照已完成并在ac881d6归档同步。本工作单元由用户新建根目录query_rewrite.py，先完成结构化改写模型和单题函数；助手没有代写该核心文件。模型及API调用仍由用户在自己的终端执行。

## 为什么现在做

原Qwen8B Dense Top100中，32道dev题没有命中任何已标注相关文档。固定候选后的所有重排都保持Recall@100=0.39709670188154617，说明重排不能补入候选之外的文档。改写的目标是生成更适合检索的表达，后续用相同Dense配置、Top100预算和原始qrels比较召回及退化，不预设一定有效。

已核查[LangChain MultiQueryRetriever官方说明](https://reference.langchain.com/python/langchain-classic/retrievers/multi_query/MultiQueryRetriever)：它生成多条查询并合并结果。本轮先输出一条检索表达，保持候选预算，不引入多查询并集或同时调整RRF；不复制该实现，也不为参考最新文档而升级当前依赖。语料、查询和dev划分仍沿用现有NFCorpus，未新增数据来源。

已核查[DeepSeek Tool Calls官方说明](https://api-docs.deepseek.com/guides/tool_calls/)与本地已安装SDK实际实现。这里借助tool-calling格式取得结构化字段，不执行外部业务工具。模型返回的reason是改写说明，不是医学证据或条件核验结论。

## 当前进度：真实单题通过，下一步小批量核心

2026-11-25，用户终端完成ct_query_rewrite_single_01：status=ok，检索表达与原问题完全相同，changed=false，保留检查目的未说明；模型deepseek-flash，finish_reason=tool_calls，422输入／96输出／518总tokens，缓存读取0。本地整个进程1.47秒、主机RSS峰值96700KiB、退出0且无中断标记，不称远程模型推理延迟。日志及资源原件未改；8字段无损归档results/ct_query_rewrite_single_01_results.jsonl、_summary.json、_run.json，核验_validation.json。原始日志与用户提交内容一致，当前三份源码／配置SHA匹配入口本地验收；本次未在请求前创建代码回执或抓取原始HTTP消息，不能冒称已严格绑定请求时源码。

该次reason声称没有否定表达，原问题却有not stated；实际检索表达完整保留该条件，单题流程通过，解释文本的这个概括不准确另记ENG-026。不因此重复调用或修改提示词追单题措辞。真实单题只证明这个输入的服务链路和保留情况，没有测NFCorpus召回、指南选择或更广泛的语义忠实性。

2026-11-25，用户完成query_rewrite.py，本轮审阅源码SHA-256为eaba30a9f7efa31a0850e72a6f475eb0869fcff3c7b1a3d465889ca5fd20daed。以真实ChatPromptTemplate、RewriteResult及AIMessage搭配最小FakeLLM检查六类响应：有效改写、仅首尾空白差异、空白查询、空白原因、解析异常、parsed缺失，均符合本文返回协议；另检查四个非法输入零模型调用、网络异常原样传播及未知用量保留None。成功／失败返回均可JSON序列化，已有响应保留原问题及两类元数据，每次模型invoke一次。假响应中的token值只是检查数据，不是实际用量，助手未调用API或GPU；这不证明真实服务兼容性、医学语义保真或检索收益。原用户核心未修改，未新增隐藏测试脚本。离线观察归档results/query_rewrite_core_validation_01.json。

助手补充configs/llm_profiles.json作为公开配置；用户已实现run_query_rewrite.py，不从Notebook导入对象，核心rewrite_query的接口和8字段返回不变。入口38行源码SHA-256为8f9783b2730a8b7cb82de9f1351c1bfce708132217c768e5f6a95327c2aa2773，记录results/query_rewrite_entry_validation_01.json。修正--query后，真实argparse到实际核心的CPU假响应链路通过，配置／项目dotenv路径／单次invoke／原问题／JSON输出正确；导入及help无客户端构造，缺query在调用前拒绝。该轮dotenv及真实客户端被mock，未读密钥或发起API，假token不是成本；随后用户真实单题结果已单独记录于上文。没有修改用户实现，也未把局部变量名作为阻断。

## 已补的保存辅助：query_rewrite_io.py

助手提供save_rewrite_results(records, *, config, run_name, result_dir)。records为按输入顺序排列的字典列表，每条有query_id及核心返回的8字段，允许附加rewrite_elapsed_ms等字段，原样写入；config只传公开运行配置，不传密钥或环境内容。函数不调用模型、不改写查询、不读取环境。输出为手动run_name前缀的_results.jsonl（逐题）、_summary.json（数量和已知token）、_run.json（公开配置），返回summary字典。

逐题保留原始metadata，解析失败但有用量时仍计入已知token；缺失或不完整用量单独计数，全部未知时三项总量为None，不能假设为0。query_id要求非空字符串且同一批不重复；status沿用ok/error。写前检查字段及JSON可序列化，任意一份输出已存在即拒绝覆盖，并使用x模式创建；普通写入失败只清理本次已创建文件，原异常继续抛出。这是批次结束后的保存，不宣称具备逐请求断点恢复、跨进程锁或断电事务保证。临时目录检查已覆盖无损往返、输入不变、已知错误用量、未知用量、覆盖保护、重复ID及不可序列化配置；未为此改用户核心。

## 下一项用户任务：rewrite_queries

在现有query_rewrite.py中增加rewrite_queries(queries_df, *, llm)，复用已完成的rewrite_query，不改它的8字段协议。当前只写该函数，保存后由助手审阅；不直接调用8次API或修改入口。下一次接线后用现有load_beir_dataset(...,split="dev")得到的queries_df.head(8)作流程检查，完整评测仍用同一324道dev题。已核对前8题为PLAIN-1、PLAIN-11、PLAIN-22、PLAIN-32、PLAIN-43、PLAIN-55、PLAIN-67、PLAIN-77；按原文件顺序选取，不依检索分数或标签挑题。

输入queries_df是上游加载器已经检查的DataFrame，列为id和query；不在该函数里重新读取数据或重复整套标注验证。llm是入口创建的一份共享客户端。需要time.perf_counter计时、tqdm显示进度，以及openai.APIError处理请求本身失败；本地openai1.109.1已核实连接／超时／限流／HTTP错误类都继承APIError，无需新安装。

完整逻辑顺序：

1. 建立结果列表，用tqdm包住queries_df.iterrows()，total=len(queries_df)，desc="改写查询"，保证输入顺序。row["id"]只用于记录query_id，模型只接收row["query"]，不传qrels或标注答案。
2. 对每题在调用前取perf_counter，执行一次rewrite_query(row["query"],llm=llm)，不在循环中创建客户端或再次结构化包装。
3. 核心正常返回时，不论status为ok还是error，都原样保留8字段；已有响应的解析失败不是抛出的API异常，用量仍保留。
4. 仅捕获APIError，为这一题构造相同8字段的失败结果：original_query原样、status=error，retrieval_query／changed／reason／usage_metadata／response_metadata均None，error为含异常类型及具体消息的字符串。此时没有有效原始响应，用量未知；不自动重试、回退或丢弃该题。数据／编程异常自然抛出，不用except Exception把它们伪装成API失败。
5. 单题处理后停止计时，将差值乘1000作为rewrite_elapsed_ms。它包含单题提示构造、请求、解析及失败处理，不含客户端创建、进度输出或文件保存；不直接称远程推理时间。
6. 每条结果加query_id=row["id"]及rewrite_elapsed_ms，追加到列表，结束后返回列表。它共10字段，不改核心函数返回；函数不调用保存辅助，输出落盘由后续入口统一执行。

验收看正常／原样／解析失败／请求异常均每输入一条就有一条记录，ID顺序一致；有有效输入的请求每题最多调用一次；失败不伪造changed或token，编程错误不吞掉，计时非负。先审实际代码再做最小CPU假调用检查，真实8题仍由用户终端执行。保存辅助已能接收这批记录，接入入口后复用同一模型配置和原文档向量；当前尚无8题API输出、批量缓存、改写检索或收益结果。

### 独立入口的完整任务

实现main(config_dir, *, profile_name, query)，其中config_dir使用Path，profile_name指定配置名，query是单条原问题。按以下顺序完成：

1. 使用json.loads和Path.read_text(encoding="utf-8")读取config_dir / "llm_profiles.json"，按profile_name选择配置。
2. 用Path(__file__).resolve().parent定位项目根目录；在main内调用load_dotenv(root / ".env", override=False)，供SDK读取DEEPSEEK_API_KEY。不要打印密钥、环境内容或完整客户端对象，配置文件也不存密钥。助手未读取.env。
3. 从langchain_deepseek导入ChatDeepSeek，以ChatDeepSeek(**profile)构造客户端。**把字典键值展开为关键字参数；本地0.1.4已核实接受这些参数，api_base是本安装类实际使用的地址字段。不要再套一层with_structured_output，核心已经负责包装。
4. 从query_rewrite导入rewrite_query，只调用一次rewrite_query(query, llm=llm)，main返回其字典，不增加重试、检索、循环或回退。
5. 在if __name__ == "__main__"里用argparse接收--config-dir（type=Path）、--profile（默认deepseek_flash）、--query（required=True），传给main，使用json.dumps(result, ensure_ascii=False, indent=2)输出。允许配置目录默认项目configs，但实际运行命令必须显式传--config-dir。不在导入模块时构造客户端或调用API。

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

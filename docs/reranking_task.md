# Cross-Encoder重排任务

**2026-11-25当前进度：4B batch4完整控制已完成，下一步BGE下载。** 同一原Top100／324题，4B batch4的nDCG@10=0.407701、Recall@10=0.205120，新增3.236秒/题；对batch1仅少0.68%耗时、两指标略降。同batch4的8B nDCG@10高2.18%、Recall@10低1.04%、阶段均值约1.678倍，尚不选最终模型。当前指标／来源／代码核对通过，一份旧预检资源覆盖导致严格全历史检查失败，限定状态和异常原件均保留，见[当前实测归档](nfcorpus_retrieval_baselines.md#qwen4b-batch4控制与历史记录异常)。用户核心与核验器未改，不重做Dense；下一步[下载固定BGE](reranking_runtime_task.md#bge-v2-m3同候选对照下载)，先核对再真实预检／完整dev，启动前检查记录名称。以下保留较早节点的任务设计与历史状态。

**2026-11-25首个完整重排结果已核验：** Qwen4B在同一Qwen8B Dense Top100／324 dev上的nDCG@10=0.409974、Recall@10=0.206984，相对+4.53%／+7.69%，Recall@100保持0.397097。batch1新增重排平均3.258秒/题、整轮17:40.07；逐题存在下降，当前不是最终模型结论。详见[实测归档](nfcorpus_retrieval_baselines.md#qwen3-reranker-4b实测收益与代价)。下一步按原计划[下载8B](reranking_runtime_task.md#qwen8b同候选对照先下载)，独立预检后同候选比较，BGE对照保留。

**2026-11-25真实预检通过，待完整dev运行：** Qwen4B在4090实际CUDA BF16／4096／batch1下完成32400联合长度扫描（最大2414，0超限）及3对真实打分，预检峰值已分配8.063GiB。报告及输入／源码身份核对通过，不能把样本结果当排序效果。下一步在同一Qwen8B Dense Top100上完整重排324道dev，运行名nfcorpus_rerank_qwen3_4b_dev_01，见[完整命令](reranking_runtime_task.md#完整开发集重排)。离线核验工具已适配profile入口，4项新检查通过，用户核心未修改。

**2026-11-25模型已下载，预检待用户运行：** 固定Qwen4B的17文件／2个BF16分片已核对完整，索引、内容哈希和离线分词器通过。助手新增scripts/evaluation/preflight_reranker.py，4项工具＋支持6项＋入口4项共14项辅助检查通过；实际模型、联合输入长度与显存仍需用户终端预检。工具先扫描32400联合长度，再对最多3对样本真实打分，命令见[真实预检](reranking_runtime_task.md#真实预检)。当前没有真实重排效果。

**2026-11-25运行入口已验收：** 用户run_reranking_eval.py的4项编排检查及相关46项共50项全部通过，模型只构造一次、默认命名不含时间戳，原始候选来源和本轮模型属性完整进入保存结果。当前没有真实模型或GPU运行；下一步用户在可见终端下载固定Qwen4B，命令与后续预检顺序见[运行任务下载节](reranking_runtime_task.md#用户终端下载)。下载完成核对后再准备真实小批预检，不直接完整重排。

**2026-11-25运行辅助已提供：** configs/reranker_profiles.json固定Qwen4B／8B与BGE配置，8B revision=77d193c791ed757ca307ee72715aa132723da912；reranker_adapter.py提供build_reranker和describe_reranker，save_beir_results已支持frozen_rerank、候选来源核对和独立重排计时。相关46项检查通过，未下载或加载真实模型。4096联合长度／batch1待预检。用户下一项新增运行入口，完整接口、参数理由和配置对应见[运行任务](reranking_runtime_task.md)。以下待实现描述属于此前阶段。

**当前衔接已验收，2026-11-25：** 用户已完成benchmark_eval.py的可选query_id传递及evaluate_frozen_reranking包装函数，复用原评分循环，相关28项检查全部通过。真实324题／32400候选以假打分反转顺序核对了查询身份、候选集合及Recall@100保持0.39709670188154617；未加载模型、向量或GPU。详见[冻结重排评测任务](frozen_reranking_eval_task.md)，记录results/frozen_reranking_eval_validation.json。模型／CLI／重排保存扩展待后续，暂无真实重排成绩。

**导师检查方式修正，2026-11-25。** 用户明确反对由不可见测试要求核心迁就错误异常约定。TypeError／ValueError按语义使用，不强制统一名称；本轮测试只核对非法输入／输出确实被拒绝、候选与分数对应、来源／输入不变、模型调用次数和运行异常传播。先审实际代码与API，再验证；若测试假设错，修测试，不反复改正确实现。用户无需再加异常包装，核心本轮不修改。此原则覆盖下文旧的强制ValueError要求，详见PROJECT_CONTEXT第13.12节。

**2026-11-25最终验收：纯函数12项全部通过，真实重排模型尚未接入。** 原分数转换可保留Python原生TypeError／ValueError，撤回此前强制统一ValueError的验收要求；这是助手测试过严，不是重排算法错误。[Python异常说明](https://docs.python.org/3.12/library/exceptions.html#TypeError)区分类型不适当与值不合法。非法字段仍需在predict前拒绝，其他语义／调用次数／输入不变性要求不变。用户函数原逻辑未改，助手仅清理无用logging／空白，函数AST一致；最终SHA=1e04ef1809434bb57a30bc0a9cd903f597a29491c0d1c679d99793a86f1c32dc。记录results/rerank_core_validation_accepted.json和最终源码快照。当前完成归档同步，下一步先补冻结候选加载与评测辅助，再交入口接线；暂无真实重排效果。下文失败修订均为历史，旧“必须包装ValueError”条款失效。

**2026-11-25最新复验revision05：12项通过11项。** 唯一剩余为第20行原score为None时float抛TypeError；转换周围捕获(TypeError,ValueError)，统一重新抛ValueError即可，成功后保留有限性检查。其他校验顺序、正常路径与错误输出均已通过。不增加接口要求或改算法，结果results/rerank_core_validation_05.json；当前纠错不提交／不加载真实模型，下次保存复验同一12项。

**2026-11-25最新复验revision04：12项通过10项。** 正常重排和输出检查已恢复，剩第9／12行异常类型统一ValueError、第14行text增加纯空白检查，以及把重复ID／float原分数转换和有限性检查移到predict前。这里要拆两个循环：先完整验证输入候选，再打分，最后原循环只负责输出复制和分数保存；转换失败也按既定契约ValueError。结果results/rerank_core_validation_04.json，核心未代写，当前不提交、不加载模型，复验要求仍为同一12项。

**2026-11-25最新复验revision03：** query类型顺序已修，但getattr检查dict属性误拒正常候选；应用字典键存在性检查，0分合法。复合条件被逗号构成tuple且少raise；应使用and组合独立布尔比较。空候选仍在predict后返回，重复ID／原分数转换与有限性仍需前置，类型错误统一ValueError。助手仅整理两条异常提示及注释，未代写校验／排序。12方法当前4通过，多条失败来自同一字段检查阻断；结果results/rerank_core_validation_03.json，用户原稿与受测快照均保留。仍在纠错阶段，不提交，不加载模型。原分数0的合法样例未改变契约。

**2026-11-25最新复验revision02：** 正常打分、稳定排序、原分数／来源保留、单条／负分数和模型异常传播已通过。当前需先完成全局类型／值检查再返回合法空候选；query及id／text先检查字符串再strip；候选字段／唯一ID／有限原分数应全部在pairs和predict之前验证；输出维度和长度错误消息仍有str+int及len(scores[0])残留。本轮针对既有空候选约定补一项组合检查，共12方法7通过，未新增接口要求。记录results/rerank_core_validation_02.json及完整覆盖快照；当前用户修订，核心未由助手改写，不提交或加载真实模型。下面初版11项结果保留作历史。

**2026-11-25当前验收：用户初版已存在，尚未通过。** 11个无权重测试方法初验未通过，results/rerank_core_validation_01.json及源码快照保留。正常输入首先被type(hits)与list()实例的比较阻断，错误消息又拼接非字符串；静态检查另见query类型、空候选／字段验证缺失、len(scores[0])及hit[index]误取值、两类分数未转float、logging.WARN误调用。以上普通代码错误不列工程贡献，助手不代写核心。当前用户集中修订后复验，不下载模型、不提交纠错阶段。后文“尚未创建”是旧阶段记录，以本段为准。

任务确定与来源核查：2026-11-24。BM25、BGE Dense／RRF及Qwen3-Embedding-8B Dense均已实测核验，当前固定Qwen本轮Top100。其nDCG@10=0.3921959681142708、Recall@100=0.39709670188154617，平均query53.69274598138244ms。本步只改候选排序，核心由用户编写；rerank_core.py尚未创建，无重排成绩，官方test及MIRAGE未运行。

**当前工作单元：** [Dense独立对照](dense_model_selection_task.md)已完成，现在用户新建rerank_core.py，实现以下纯函数，先假打分器验收。固定候选身份results/nfcorpus_qwen3_8b_frozen_candidates.json引用本轮原始results／run／summary及SHA；尚未实现候选加载辅助，不要求调用不存在的函数。真实推理后续用原query与候选ID联结原文，在独立进程只加载一个reranker，复用Top100，无需8B embedding与reranker同时占GPU或重复query编码。分别报告既有召回与新增重排耗时，不将分阶段数据相加冒充单进程端到端实测。

## 参考实现、模型与使用条件

[Sentence Transformers官方两阶段说明](https://www.sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html)及其[固定提交示例](https://github.com/huggingface/sentence-transformers/blob/cddcaee3405a5efde83c1d98f89c6ebd6733dab6/examples/sentence_transformer/applications/retrieve_rerank/retrieve_rerank_simple_wikipedia.ipynb)使用检索候选再交叉编码重排。已查阅该示例，不能将示例输出当成本项目的分数；本项目不复制其Wikipedia数据管线。

**2026-11-24选型修正。** 用户明确要求按正式项目的任务效果选模型，不默认偏向轻量。撤回此前将MiniLM-L6-v2直接确定为成品重排模型的决定：此前只核对了模型条件和API，没有医学任务效果对照，选型依据不足。MiniLM未下载或实测，无相关代码需要重写；以下候选通过同一接口接入。

| 已核查候选 | 任务能力与使用条件 | 本轮定位 |
| --- | --- | --- |
| [Qwen/Qwen3-Reranker-4B](https://huggingface.co/Qwen/Qwen3-Reranker-4B) | 4B，多语言、指令感知，官方报告32K上下文，Apache-2.0；revision=22e683669bc0f0bd69640a1354a6d0aebcfeede5 | 优先验证的效果候选，尚未下载／运行，不能称为最终胜出模型 |
| [Qwen/Qwen3-Reranker-8B](https://huggingface.co/Qwen/Qwen3-Reranker-8B) | 8B，多语言、指令感知，官方报告32K上下文，Apache-2.0；revision=77d193c791ed757ca307ee72715aa132723da912 | 与4B做同家族直接对照，官方中文／多语言／长文档项更高；尚未下载／运行 |
| [BAAI/bge-reranker-v2-m3](https://huggingface.co/BAAI/bge-reranker-v2-m3) | 多语言联合编码相关性打分，Apache-2.0；revision=953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e | 效果与成本对照，尚未下载／运行，不因规模较小预设为最终模型 |

候选依据：[Qwen官方同一评测表](https://huggingface.co/Qwen/Qwen3-Reranker-4B#evaluation)中，Qwen3-Reranker-4B的MTEB-R为69.76，BGE-reranker-v2-m3为57.03，Qwen3-Reranker-8B为69.02；该表均由发布方在Qwen3-Embedding-0.6B检索的Top100上运行。当前英文任务支持先验证4B，但不足以排除8B。8B在CMTEB-R（77.45对75.94）、MMTEB-R（72.94对72.74）、MLDR（70.19对69.97）更高，4B在FollowIR（14.84对8.05）更高；汇总项不能代替医学专项，未提供误差范围也不宣称差异显著。用户追问8B后，明确将其加入正式候选，在相同Dense Top100、相同实际输入内容／预算与任务指令下与4B直接比较，记录截断和显存／延迟；模型格式差异必须如实配置。先验候选顺序不是最终胜出结论。这些模型都是通用模型，不能当作医学专用或已具备指南适用性判断能力。

选型按任务适配、同候选集实测、长文本／语言覆盖、许可与可复现性作判断，同时报告延迟、吞吐和显存；资源成本是实际约束，不能替代效果证据。NFCorpus用于公共排序对照，临床专项仍要检验适用条件、否定、数字、来源与定位；后续以留出集核验已固定方案，不用官方test反复选模型。现有BGE-small成绩保留为基线，不等于它已经通过成品选型；更换向量模型须作为独立实验，不能与本次重排同时改动。

本地sentence-transformers==5.7.0、transformers==4.57.6已安装；本地CrossEncoder包含因果模型及LogitScore处理，Qwen官方模型卡也提供CrossEncoder.predict句对接口及默认原始logit差值用法。模型输入模板、prompt和实际返回结构仍需在真实小批中核对，目前仅完成文档／源码检查，不是模型加载验收。这个库与现有LangChain HuggingFaceEmbeddings分别承担重排打分与向量编码，向量部分继续沿用现有接口。见[官方CrossEncoder用法](https://www.sbert.net/docs/cross_encoder/usage/usage.html)。

## 本轮完整工作单元

项目根目录rerank_core.py已实现并通过验收，接口保持：

    rerank(query, hits, k, *, reranker, batch_size=16)

本函数只对传入候选打分与排序，不创建模型、下载权重、调用检索器或读取qrels。未来CT、NFCorpus及主库共用此接口；不依赖Notebook。

| 参数 | 内容与原因 |
| --- | --- |
| query | 非空原始问题字符串；不添加BGE向量检索前缀 |
| hits | 现有检索器返回的列表，每条含id、text、score及原有来源定位元数据 |
| k | 正整数，重排后保留数量；超过候选数时返回全部候选 |
| reranker | 已初始化的CrossEncoder对象；由运行入口创建一次并注入 |
| batch_size | 正整数，函数默认16；只是可覆盖的接口默认值，4B模型的实际运行批次须小批预检后单独冻结 |

构造与候选同序的(query, hit["text"])句对列表，对整个列表调用一次reranker.predict，参数batch_size=batch_size、show_progress_bar=False、convert_to_numpy=True。一次调用由库内部按batch处理，不是把所有100对同时塞进显存，也不要逐条调用100次。

用numpy.asarray整理返回值，要求一维、长度等于候选数、全部有限。每个输出对应同位置输入句对。复制每个候选字典，把原score保存为float类型retrieval_score，把模型相关性分数保存为float类型score，保留id、text、source_id、locator等字段。按(-score, id)排序后取前k条，不原地改hits。

按已核查模型的官方CrossEncoder用法保留原始打分：分类模型logit或Qwen的logit差值，允许负数和大于1，不是概率；不做归一化或强制裁剪。候选模型不同，分数不直接跨模型比较；原Dense分数与重排分数也不相加。只在后续明确设计消融时才引入混合权重。

输入检查集中在函数入口：query有效；k与batch_size为非bool正整数；hits中id为非空且唯一字符串、text为非空且非纯空白字符串、原score可转有限float。类型或值错误可按实际语义抛TypeError／ValueError，不强制包装或仅为测试改写异常类。合法空列表返回[]，不调用predict；非法字段须在模型调用前失败。模型输出长度／维度错误或NaN／Inf必须拒绝，不丢候选掩盖失败。真正模型运行异常向上传递，不吞掉后继续给出答案。

## 所需库与API

本函数只需numpy与Python内置功能，不必在模块顶层导入CrossEncoder或初始化GPU。numpy.asarray接收模型返回值；.ndim／.shape检查结构，numpy.isfinite(...).all()检查数值。dict.copy()复制候选字典，本函数只改顶层分数字段；zip对应候选与分数，sorted(..., key=...)指定排序，列表切片保留前k条。字典复制不会递归复制嵌套对象，因此不要修改locator等嵌套元数据。

模型类在后续运行入口使用sentence_transformers.CrossEncoder，固定模型revision并用CUDA。实际dtype、batch、联合输入长度、官方输入模板／指令与打分模块，在真实开发集运行前结合官方配置、样本长度和可见GPU做一次预检并冻结；不把MiniLM的512-token限制机械套给新模型，也不默认启用完整32K输入。下载后启用local_files_only=True与进程级离线模式。原始完整正文继续保留；函数只接收已初始化打分器，模型运行配置的核定不改变其接口或排序逻辑。现在先完成并验收纯函数，不提前下载权重或启动GPU。

## 函数验收

用一个仅提供predict方法的假打分器，无需模型权重或GPU。三个候选按A、B、C输入，原检索分数任意且保留；假输出为[0.2,0.8,0.8]，k=3时输出B、C、A，k=2时只返回B、C。同分按ID升序，不沿用偶然的输入顺序。

检查predict恰好调用一次，收到原query与对应完整text、指定batch参数；输入hits不变，来源定位字段保留，retrieval_score等于原分数，score为新的float。空候选不调用模型，k超过条数不补候选，负logit正常保留，重复ID、非正k、错误长度／维度和非有限分数被拒绝。用户保存后助手重读当前代码，并提供必要的独立测试；不代写核心函数。

## 函数通过后的实验

在已有公开基准流程接入冻结候选的重排评测：本轮Qwen Dense Top100→重排全部100→返回100，真实重排进程只加载一个打分模型。候选加载、原query／正文联结及身份核验、保存与配置辅助由助手先补齐，再交用户入口接线；不能调用尚未实现的辅助。保留旧方法及原始产物，记录模型版本、句对长度、batch、候选数与新增重排计时。产品在线组合另行验证资源与延迟，不由本轮离线分阶段数据推断。

先用相同324条dev原query比较nDCG@10、Recall@10和新增重排延迟；最终Top100集合相同，因此Recall@100应保持0.39709670188154617。324×100=32,400个推理句对，不是新增题目或训练样本。旧文档矩阵继续保留，离线重排直接复用保存的候选，不重复query编码；重排需要联合处理query原文和候选正文，不能用已有文档向量代替。

真实模型下载、预检和开发集运行稍后由用户在可见终端执行，当前不启动。通过、归档、提交并同步GitHub后继续下一项。开发集方法固定再运行官方test；本步不扩充语料、不调整RRF、不宣称Agent或医学适用性核验已完成。

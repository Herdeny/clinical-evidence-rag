# 当前任务：实现RRF排名融合

日期：2026-11-20。医学v3的Dense和BM25基线均已完成并独立核验。原32道开发题中3题仅Dense的Top-5有标注需求覆盖、4题仅BM25有，足以提出融合实验；尚未实现RRF，不承诺融合后一定提高。核心代码继续由用户编写。

## 2026-11-21当前状态

**公开评测接续：** NFCorpus已经实际下载、固定并核验，当前用户实现[benchmark_data.py读取适配](nfcorpus_benchmark_task.md)，随后用官方相关性标签比较现有Dense／BM25／RRF。原代码验收保留，尚无公开基准跑分。下面针对120合成题的安排只作可选产品回归，不再充当主要外部效果证明。

CT专项评测草稿现已扩至120开发／60留出、30家族，详见[题集说明](../data/evaluation/ct_v3/DATA_CARD.md)。原48题和旧成绩保留，主库及完整向量未变。当前直接准备在固定120题开发草稿上做三方法探索性对照，由用户在终端执行；数据仍明确标为AI初标，不要求用户先逐题填写复核表。以下融合／入口验收结果仍有效，医学标签质量另行核查，探索性成绩不能当作临床准确率。较早强制先由用户复核的安排不再适用。

**最新决定：保留方法层配置，入口5项与保存辅助6项检查全部通过。** 用户希望model_name留在dense／bm25方法层，这种布局合理。助手旧保存函数曾强制顶层元数据，现已修改该辅助代码按方法读取和校验；配置原样持久化，旧平铺布局继续兼容。无需添加此前建议的config.update或组合方法的全局模型名。当前三种方法及CLI均已通过小样本检索／评分／保存；没有真实全库RRF成绩。审计results/retrieval_config_layout_adaptation.json，入口results/retrieval_entry_validation.json；下一步专项评测覆盖、扩题及标签核对。以下旧配置阻断记录留作历史，不再要求用户按旧限制改布局。

**最新修订：资源准备和RRF实际调用均已修好，只剩保存配置。** 三种方法的小型检索与评分均执行完成，资源初始化次数正确，统一在保存处因顶层缺model_name／device／query_prefix报错。公共路径／模板／corpus_name已正确顶层。Dense和BM25可从已有子配置update到顶层；RRF顶层补组合方法标识、cuda+cpu、空全局前缀，同时保留两路详细配置。config['rrf']的constant_k和rrf_candidate分别改成candidate_k和rrf_constant，值仍20与60。实际partial已正确，勿重复修改。修订记录results/retrieval_entry_validation_2026-11-21_revision1.json；初版三处诊断留作历史。

**最新入口检查：CLI解析／传参两项通过，三个方法执行仍需修正。** 用户已完成main重组，但资源准备用了if/elif，使RRF没有BM25函数；RRF partial及配置键误写rrf_candidate；保存所需公共／方法摘要字段都嵌套了，原保存契约读取顶层字段。具体修正：第二资源段改独立if；统一rrf_constant；公共cases_path、evidence_path、query_template、corpus_name平放顶层，当前方法的model_name、device、query_prefix也放顶层，dense／bm25详细配置保留。见results/retrieval_entry_validation_2026-11-21_initial.json。测试tests/test_retrieval_entry.py用临时合成数据、假模型和真实小型检索／评分／保存，未接触正式数据或GPU。

实际main签名为main(method,cache_dir,cases_path,evidence_path,run_name)，当前CLI与之对应且已通过测试，可保留；下文先前“保留前四参数／可选关键字”是设计建议，不为此单独要求重排。新增--cache和--evidences也已通过传参测试。

**最新：retrieve_rrf查询编排也已通过小样本验收。** tests/test_rrf_fusion.py现包含7项融合检查和5项假检索编排检查，共12项通过；结果results/rrf_retrieval_validation.json。两路各调用一次，原始查询／候选数／常量正确传递，返回融合hit；非法参数在调用前拒绝，空路／候选不足和上游异常传播符合约定。没有真实模型、全库检索或RRF效果成绩。当前由用户修改运行入口，任务如下；早先“待实现查询编排”为历史。

**最新：fuse_rankings七项手工检查全部通过。** 已验证手算[B,A,C]及分数、返回list[dict]、保留证据信息、k截断、全空／单路空、同分规则、输入不变、单路重复拒绝和正整数参数边界。可复用测试为tests/test_rrf_fusion.py，最新结果results/rrf_fusion_validation.json；初版和revision1失败证据保留。没有调用模型或运行真实RRF检索。当前用户继续同一模块实现下方retrieve_rrf查询编排；更早“剩两处”属于历史状态。

最新修订复验：参数检查、输入复制、输入名次和贡献累计已修正。用户改用items配合x[1]排序，内部[B,A,C]及得分正确，但返回值仍为(id,hit)元组列表，需要提取hit返回list[dict]；可以保留当前items排序，不强制替换values。另须补上每份排名各自seen集合的重复ID检查。七类检查当前3项通过，另外4项受上述两处阻断，记录results/rrf_fusion_validation_2026-11-21_revision1.json。下面初版诊断留作历史，不重复要求修已通过的内容。

retrieve_rrf.py已由用户创建，fuse_rankings尚未验收。七项手工检查仅全空返回通过，其余检查中多个被同一处items元组排序错误阻断；此外确认输入分数被修改、非法参数未拒绝。初版证据results/rrf_fusion_validation_2026-11-21_initial.json绑定实际源码指纹。当前由用户集中修正：按values中的hit排序、先复制hit再替换score、直接使用输入名次，以及补齐下文既定的参数和单路重复ID检查。助手未代写或改动核心，不将基础Python错误计作工程复盘案例。

正式RRF方法对照前先扩充并核对专项评测题，见[data_expansion_milestones.md](data_expansion_milestones.md)。当前先完成纯函数和手工验收，后续查询编排可继续按接口开发；不直接拿32题的小幅差距宣称方法优势，不提前启动全库RRF实验。

## 方法和参数来源

RRF按名次累加倒数，不直接相加两路原始分数。对证据d，每个返回它的排名贡献1/(rrf_constant+rank)，rank从1开始；没有返回该证据的排名贡献0。

先固定rrf_constant=60。原始论文在早期实验确定60，后续验证保持不变；本项目沿用该参考设置，不把它称为医疗场景最优参数。来源：[Cormack、Clarke和Büttcher，SIGIR 2009原始论文](https://cormack.uwaterloo.ca/cormack/cormacksigir09-rrf.pdf)，已于2026-11-20读取方法和参数说明。这里参考算法与公式，没有复制第三方仓库源码。

## 本次用户实现

新建根目录retrieve_rrf.py，先实现接口fuse_rankings(rankings, k, *, rrf_constant=60)。模块导入时不读取数据、不创建模型、不建索引。无需新增库；Python内置dict、enumerate、sorted即可。

rankings是多份已有检索结果组成的列表，例如[dense_hits,bm25_hits]。每份hits的输入顺序就是检索名次，融合函数直接枚举，不再按原score重排；每个hit沿用id、score、source_id、locator、text。这里的多份排名指检索方法，不是指南／说明书／论文来源类型。

返回最多k个不同ID的hit，字段兼容现有retrieve／evaluate_retrieval。score改为融合得分，其他证据信息保留；复制原hit后修改，不改写输入hit或原始分数。融合分数只是排序依据，不是临床置信度或正确概率。

流程：

1. 检查k与rrf_constant均为正整数，排除布尔值。空排名不贡献分数，所有排名为空时返回空列表。
2. 遍历每份排名，使用enumerate(hits,start=1)取得名次。
3. 按id累计1/(rrf_constant+rank)，同时保留该id的证据信息。跨排名重复ID应累加；单份排名中重复ID属于非法输入，抛ValueError，避免一份排名重复投票。
4. 所有候选按融合分数降序，同分按id字符串升序，保证可复现；截取前k条。k大于候选数时返回全部候选。

可以用dict.get(identifier,0.0)取得当前累计值；使用hit.copy()复制原hit再替换score。sorted返回新列表，排序键包含负的融合分和id。上述是所需API提示，完整函数由用户组合。

## 验收样例

两份排名分别为[A,B]和[B,C]，rrf_constant=60。B为1/62+1/61，A为1/61，C为1/62，因此k=3输出[B,A,C]。输入hit需要提供真实接口要求的字段，但原始score数值不参与融合。

还需通过：两路同一ID只输出一次；单一路空时保留另一路顺序；全部空时返回空；同分按ID；k超过总候选数；输入字典不被修改；单路重复ID抛错；非法参数在计算前拒绝。助手用手工排名验收，不启动模型或真实全库任务。

## 本函数通过后的接入安排

### 当前用户实现的查询接口

继续在retrieve_rrf.py中定义retrieve_rrf(query,k,*,dense_retrieve_fn,bm25_retrieve_fn,candidate_k=20,rrf_constant=60)。无需新增库，同模块可直接调用已通过的fuse_rankings。

两个retrieve_fn都是已经由入口绑定资源的可调用函数，调用形式均为retrieve_fn(query,k)，返回当前统一hit列表。Dense的模型／证据／向量、BM25的索引／证据继续在入口创建一次并绑定，查询编排只传查询和候选条数。这样evaluate_retrieval仍可使用统一(query,k)接口，以后更换检索存储也保留此边界。

实现流程：

1. 在实际调用前检查k、candidate_k、rrf_constant是正整数且candidate_k>=k，排除布尔值。
2. 将原始query和candidate_k交给dense_retrieve_fn，取得dense_hits。
3. 将同一个原始query和candidate_k交给bm25_retrieve_fn，取得bm25_hits。BGE前缀已经由Dense模型配置处理，编排不再拼接。
4. 把这两份排名、最终k和平滑常量交给fuse_rankings，直接返回融合hit列表。输入证据不足时只返回实际候选；某一路抛异常时正常向外传播，不把错误伪装成空命中。

本次验收只使用两个可记录调用的假检索函数：每路恰好调用一次、查询原样一致、每路候选数20而最终k为3；[A,B]和[B,C]仍输出[B,A,C]；候选不足和空路行为正确；非法参数在任何检索调用前拒绝；两路输入不被改写。助手检查后再接CLI，不加载模型或重建索引来验证这几行编排。

仍在同一模块增加retrieve_rrf查询编排，调用已初始化的两路检索函数，然后调用fuse_rankings。首轮固定每路Top-20候选、最终Top-5、rrf_constant=60、两路等权。20是本项目预先选定的候选预算，提供超过最终5条的融合空间，不称为已调优或最优。候选数影响覆盖与成本，后续单独做消融时保持其他设置一致。

入口新增rrf方法，一次读取证据／模型／缓存并构建BM25，不能在每道题重建；复用当前完整文档向量。原始查询分别交给两路：查询前缀由Dense模型配置处理，不传给BM25。沿用同一评测和保存辅助，独立运行名medical_v3_rrf_ct_dev，配置记录两路参数、候选数、常量、缓存与计时范围。

后续真实长任务优先给用户终端命令，由用户可见执行；助手核验代码、小样本与保存结果。本轮只交付融合函数，不代写核心，不提前运行融合全库评测。下一步仍是RRF，不跳到重排、换模型或重新扩库。

## 当前用户任务：一次接通CLI与可配置评测输入

入口接入现已完成，保留既定模型、参数、语料、查询模板、检索和评测实现。实际main接口为main(method,cache_dir,cases_path,evidence_path,run_name)，已验证CLI与调用一致；默认运行名由CLI计算为medical_v3_{method}_ct_dev，显式传入时使用指定名称。

### main的三个阶段

第一阶段只准备资源。证据和题目各读取一次；method属于dense或rrf时创建一次现有HuggingFaceEmbeddings、读取完整文档缓存并用partial绑定dense_retrieve_fn；method属于bm25或rrf时建一次BM25并绑定bm25_retrieve_fn。这是两个独立if，RRF要同时执行两段，不能用if/elif只准备其中一个。模型revision、local_files_only、batch_size、归一化、前缀与BM25参数保持原值。

第二阶段选择最终retrieve_fn。dense直接选dense_retrieve_fn，bm25选bm25_retrieve_fn，rrf用partial绑定retrieve_rrf的两路函数、candidate_k=20、rrf_constant=60，留下query和k由evaluate_retrieval调用。每道题不重复创建模型、读文件、编码文档或建BM25。

第三阶段统一evaluate_retrieval和save_retrieval_results，避免复制三套评分／保存逻辑。原Dense与BM25配置内容继续保留；每轮只执行所选方法。

### RRF运行配置

沿用顶层公共evidence_path、cases_path、query_template、corpus_name及retrieval_method。模型或检索实现名称、设备和前缀属于各自方法层：config['dense']与config['bm25']分别保存model_name、device、query_prefix及实际参数；config['rrf']保存candidate_k和rrf_constant。RRF没有单一模型，无需额外合成全局model_name／device／query_prefix。组合接口传递原始query，BGE查询前缀由Dense模型配置处理。

当前rrf子配置记录candidate_k=20与rrf_constant=60；dense子配置保留实际模型名、设备、编码参数和embeddings_cache，固定revision等加载身份同时可由缓存清单回查；bm25子配置保留实现名、设备、空查询前缀、k1、b、epsilon。保存辅助兼容旧平铺布局，但新分组结构不需要复制字段到顶层。配置值来自实际运行，保留原始布局供回查。

### CLI参数

argparse的--method选项增加rrf，默认dense保留。增加--cases，type=Path，默认仍是项目根目录data/v3/cases.ct.dev.jsonl；增加--run-name，默认None。先计算脚本root再设置依赖root的参数默认值。解析后将args.cases和args.run_name传给main；evidence_path和cache_dir继续使用当前脚本根目录固定路径。

可配置题集和运行名是为了即将扩充评测后复用同一入口，给新版结果独立命名，不覆盖原32题基线。扩题只改查询与标签，原783,847条文档向量继续复用。当前新增题尚未生成，不提前提供指向不存在文件的正式运行命令。

入口现已用临时合成数据、假模型与临时输出目录通过三个分支、CLI传参、一次初始化和配置／保存兼容检查。当前进入评测题覆盖、原文回查与新版冻结；真实RRF正式对照等待该前置完成，长任务由用户在可见终端执行。

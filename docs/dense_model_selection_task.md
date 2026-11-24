# Dense模型选型：接入可切换的固定配置

2026-11-24，用户在查询模型候选后要求继续。当前工作单元改为先接入Qwen3-Embedding-8B的独立Dense对照，再固定候选测试重排。核心由用户编写；助手提供已核查的静态配置、测试与结果辅助。现有BM25／Dense／RRF成绩和两份BGE文档缓存均保留。本轮尚未加载、下载或运行Qwen模型，也没有新模型成绩。

**代码验收revision5已通过。** 用户已将CLI调用与必填config_dir的六参数接口对齐，缓存编排9项、入口14项全部通过；包括Qwen4096维、两配置缓存隔离、再次零文档编码、实际元数据、参数拒绝和CLI转发。核心由用户完成，助手仅移除未使用的logging.config／matplotlib rainbow导入并清理行尾空白。源码SHA：embedding_index.py为dbdd1baca3a0dc85bd8853c8c6cb8763919af8c59eb4eec2cc075bc559e6fd49，run_benchmark_eval.py为b6d2472690e42519657766e5f8f2c56a1302b7938c38f271d06503ec228f6f3b。两路旧结果10文件及NFCorpus缓存2文件SHA未变。记录results/embedding_model_integration_validation.json及revision5_accepted快照；假模型通过不表示Qwen已下载或实测。

**已纠正的旧指导：** 用户使用get_embedding_dimension()正确；5.7.0旧名称get_sentence_embedding_dimension已弃用。旧测试替身遗漏新方法导致助手误判，现以真实类规格和无权重Pooling检查验证。BGE自动名nfcorpus_dense_bge_small_dev已认可；旧命名和旧五参数调用都不再是必须保留的验收条件。历史报告保留并明确其失效范围。

## 已准备的资料与选择依据

静态参数在configs/embedding_profiles.json，两个键分别为bge_small与qwen3_8b。bge_small四项模型构造配置逐值保留现有入口的设置，目标是复用既有缓存和命令。Qwen使用[官方模型及Apache-2.0许可](https://huggingface.co/Qwen/Qwen3-Embedding-8B)，冻结[revision 1d8ad4ca9b3dd8059ad90a75d4983776a23d44af](https://huggingface.co/Qwen/Qwen3-Embedding-8B/tree/1d8ad4ca9b3dd8059ad90a75d4983776a23d44af)。官方目录的权重约15.2GB，不能把它当作显存测量。

官方[pooling配置](https://huggingface.co/Qwen/Qwen3-Embedding-8B/blob/1d8ad4ca9b3dd8059ad90a75d4983776a23d44af/1_Pooling/config.json)使用last-token、4096维；[查询配置](https://huggingface.co/Qwen/Qwen3-Embedding-8B/blob/1d8ad4ca9b3dd8059ad90a75d4983776a23d44af/config_sentence_transformers.json)提供Instruct／Query格式，正文不加指令。模型卡的英文MTEB(eng v2)检索列为8B69.44、4B68.46，仅作为候选依据，不能当成本项目或当前最新榜首成绩。医学专用候选MedCPT和多语言BGE-M3保留在交接记录，本轮先比较Qwen8B与BGE-small。

使用现有langchain_huggingface.HuggingFaceEmbeddings，向量编码仍由Sentence Transformers执行。本地5.7.0的真实构造签名接受processor_kwargs，底层Transformers4.57.6支持Qwen3；本轮不升级依赖。Qwen的嵌套model_kwargs用于底层权重精度和SDPA，processor_kwargs用于左填充与输入上限。配置中的字符串均可JSON序列化，不将torch.dtype对象放进缓存身份。

Qwen配置说明：4096维保留完整输出；权重bfloat16、不量化；输出precision=float32并归一化，缓存仍float32。长度先定8192而非直接使用模型的32K上限；实际截断比例和GPU可运行性要在全量评测前以用户终端预检确认。batch1是控制推理批次的起点，不减少模型规模、题目或候选数；外层chunk_size仍512，负责保存检查点。若预检需要改长度或批次，先更新配置及回执再正式运行，不覆盖旧结果。

准备验收已通过，记录results/embedding_profiles_validation.json：实际LangChain构造器在替换底层模型后原样转发两套参数；现有缓存辅助保存／复用两行384维和4096维合成向量且目录隔离；新bge_small配置与真实NFCorpus输入仍得到原缓存指纹4aa389bc2d522a2fc285b6065a93e38de9516d6dfa7265c1e614a4761109c3f0。两路原10份结果及NFCorpus缓存2文件摘要未变。配置SHA为81204fc0b0f7db38027ddaadfd02ed7967a8da1374f2c28e4013a9c318a02ff3。该检查没有验收尚未修改的用户接线，没有加载权重或运行GPU。

本轮比较的是采用各自输入配置的检索器：BGE512与Qwen8192、分词器和指令不同，保持同一原文与query，明确记录截断差异。只能把结果归于这套整体设置，不将差异单独归因于参数量；需要归因长度时另做独立消融。

## 用户修改两个现有文件

### 1. embedding_index.py：把维度传给缓存

prepare_document_embeddings的现有关键字参数末尾增加dimension=384，保留默认兼容已有调用。将该值传给已经存在的DocumentEmbeddingCache(..., dimension=dimension)。辅助类已经支持任意正整数维度，并把维度放入缓存身份，不需要重写它。现有分块、断点、编码与返回逻辑继续复用；非法维度由辅助类在模型调用前拒绝。

### 2. run_benchmark_eval.py：读配置并接入入口

main按用户当前接口为main(method,config_dir,data_dir,split,cache_dir,run_name,*,config_embedding_model="bge_small")，config_dir必填。CLI使用--config（默认脚本下configs目录）和--config-embedding-model（choices为bge_small／qwen3_8b，默认bge_small），将目录和配置名实际传入main；具体参数名称按用户保存的接口，不为命名重写。现有method仍为dense／bm25／rrf，不增加名为qwen的检索算法。

使用json和pathlib.Path读取显式config_dir下的embedding_profiles.json，不在main内部补默认目录。校验配置名有效，method=bm25时只允许默认bge_small（BM25本身不加载向量模型），不静默接受无效模型选择。只在dense／rrf分支初始化HuggingFaceEmbeddings，并从选中的配置传入model_name、model_kwargs、encode_kwargs、query_encode_kwargs四项；dimension与max_seq_length是项目元数据，不能将整个配置直接展开给模型构造器。

构造模型后核对embedding_model._client.max_seq_length和embedding_model._client.get_embedding_dimension()与所选配置一致；不一致抛ValueError，避免摘要与真正编码不同。这里_client是当前LangChain封装持有的SentenceTransformer对象，该访问只用于运行入口检查，检索核心继续使用embed_query／embed_documents接口。此前要求旧名称是助手的错误，当前采用已核查安装版本的推荐API。

调用prepare_document_embeddings时传实际dimension，evidence_path继续为data_dir/corpus.jsonl，cache_dir与chunk_size不改。模型对象与文档矩阵仍在查询循环外创建一次，Dense／BM25／RRF的检索编排与评分不改。

config["dense"]保留现有字段，新增embedding_profile与embedding_dimension；max_seq_length使用已核对的真实值，query_prefix取实际query_encode_kwargs["prompt"]，不再写死BGE前缀。模型／编码参数继续保存实际对象持有的字典，嵌套精度／长度也因此进入缓存身份和摘要。

自动run_name按用户最新决定可以统一包含profile，例如nfcorpus_dense_bge_small_dev和nfcorpus_dense_qwen3_8b_dev，RRF也标所用embedding配置。BM25实际不使用embedding，结果元数据应如实记录；文件名是否带默认配置标签不作为正确性阻断。显式--run-name优先，同名覆盖仍由现有保存辅助拒绝。三条旧基线原文件名与旧缓存保留，不为命名重跑。

## 需要的API和参数位置

只新增标准库json。Path(__file__).resolve().parent定位脚本目录；Path.read_text(encoding="utf-8")读取文本；json.loads转换为字典；profiles[embedding_profile]取得对应配置。模型初始化参数与项目元数据分别取用，不改已有LangChain接口。

HuggingFaceEmbeddings.model_kwargs传给SentenceTransformer构造器，所以Qwen配置中内层同名model_kwargs继续传给Transformers权重加载器，processor_kwargs传给分词器。encode_kwargs只用于文档，query_encode_kwargs只用于问题。padding_side与model_max_length不放入encode_kwargs，bfloat16权重精度也不与float32输出向量精度混淆。

## 一次验收完整工作单元

用户保存后助手重读两个当前文件，先用假模型与临时数据验收，不让用户提前消耗GPU或下载失败排错：

- 原384维缓存分批、恢复及完整缓存零调用仍通过；新增4096维缓存，形状正确，与384维缓存目录分离，第二次编码调用为0。
- 三种既有方法默认行为保留，Qwen通过同一Dense接口运行；四项构造参数、长度／维度、实际前缀和嵌套配置记录完整。
- 查询原文、K、corpus文件及评分口径不变；模型只初始化一次，Qwen第二轮只复用文档缓存，查询仍编码。
- CLI默认／显式配置和自动名称正确；非法profile、bm25配Qwen、实际模型维度／长度不符时在评测前拒绝。
- 输入／代码／旧结果及真实BGE矩阵身份保留。假模型验收不是Qwen性能或GPU可运行性证明。

代码通过后先提交同步GitHub，再提供用户可见终端的固定版本下载、小批预检和正式dev命令；预检记录模型设备、dtype、维度、归一化、长度／截断和GPU内存。正式使用新run_name与新文档缓存，先NFCorpus，不直接重编码783847行医学主库。官方test和MIRAGE仍不运行；rerank函数接口继续保留，真实重排等待Dense选型结果。

## 当前下一步：用户终端小批预检02

**2026-11-24下载验收完成。** 固定版本已下载至项目cache，下载日志17/17完成，索引要求的4个权重分片共15,134,634,568字节，逐个SHA-256匹配内容寻址文件名，未完成分片为0；results/qwen3_8b_download_validation.json保存核验结果。通过项目包装器离线读取AutoConfig成功，配置和全部权重均在项目内。本次只检查文件和配置，没有加载权重，不能作为显存或效果成绩。

预检01实际已运行并以退出码1结束：离线查找模型文件失败，没有生成通过JSON。默认共享Hub下确实找不到该固定版本config／modules，项目包装器下均可解析；先统一入口重试，不重下模型或升级依赖。原01日志和资源保留，新运行使用02编号，results/nfcorpus_qwen3_8b_preflight_02_run_audit.json记录代码、配置及历史保护文件身份。以下下载迁移经过仅作过程记录，不要求再次下载。

**缓存位置修正，2026-11-24。** 用户要求模型文件只放clinical-evidence-rag项目内。此前共享Hub目录的这次Qwen下载已精确中断，模型目录及锁文件原子迁至cache/huggingface/hub，本次Xet日志迁至cache/huggingface/xet/logs；完整文件、未完成分片及快照相对链接均保留，旧Qwen目录已移走。原BGE缓存复制到项目内并逐实体文件核对SHA，原共享BGE保留。操作记录results/model_cache_migration_2026-11-24.json，路径验证results/project_model_cache_validation.json；旧文档矩阵指纹和17个历史保护文件均未变。迁移不表示下载完成，未完成分片的复用由下载后端决定。

后续模型相关命令统一通过bash scripts/project_env.sh启动。它只为子进程设置项目内HF_HOME、Hub、Xet、assets、Sentence Transformers、Torch及XDG缓存，不改全局shell配置或父进程环境。实际Hub／Xet常量、Qwen和BGE本地配置解析、异目录调用与参数保真检查均通过。/cache/已被Git忽略，权重和下载日志不提交。模型存储位置不是编码语义变化，固定模型与参数不变时无需重做已有BGE文档向量。

辅助scripts/evaluation/preflight_embeddings.py已准备。它使用与入口相同的四项模型配置，只统计配套语料／dev查询的输入长度，实际编码前两篇及最长文档（最多三篇）、第一条原query；检查真实设备、权重BF16、4096维、归一化、输入上限及峰值GPU分配／保留内存。完整参数、输入和辅助源码指纹写入独立JSON。它不调用检索、不计算效果分数、不创建文档向量缓存，也不访问test／MIRAGE。

4项无权重检查已通过：换行／prompt／分词批次、向量异常拒绝、替换CUDA和模型后的完整报告／样本范围、无GPU时初始化前失败。--help也已检查。本轮工具没有加载预训练权重或运行真实GPU；显存和性能只在用户执行后报告。huggingface-hub0.36.2的hf入口存在，下载参数已核查，下载现已核验完成。

下面保留已完成的下载命令，后续重新准备环境时可复现；当前直接执行其后的预检02命令。下载量与实际显存分开记录。原download_01日志保留为迁移前记录，完成日志使用02_project_cache；TQDM_POSITION=-1确保经tee时也显示单文件进度。

```bash
# 从项目目录保存本轮下载日志。
cd /home/wzh/clinical-evidence-rag
# 保留下载失败时的退出状态。
set -o pipefail
# 在项目缓存继续固定版本下载，强制显示单文件进度并另存新日志。
HF_HUB_OFFLINE=0 TRANSFORMERS_OFFLINE=0 HF_HUB_DISABLE_PROGRESS_BARS=0 TQDM_POSITION=-1 bash scripts/project_env.sh /home/wzh/miniforge3/envs/all-in-rag/bin/hf download Qwen/Qwen3-Embedding-8B --revision 1d8ad4ca9b3dd8059ad90a75d4983776a23d44af --max-workers 4 2>&1 | tee results/qwen3_8b_download_02_project_cache.log
```

```bash
# 从项目目录运行，防止相对配置和输出路径指向其他位置。
cd /home/wzh/clinical-evidence-rag
# 保留Python失败时的管道退出状态。
set -o pipefail
# 预检使用已下载的固定权重，禁止依赖链再联网探测。
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 bash scripts/project_env.sh /usr/bin/time -v -o results/nfcorpus_qwen3_8b_preflight_02_resources.txt /home/wzh/miniforge3/envs/all-in-rag/bin/python -u -m scripts.evaluation.preflight_embeddings --config-dir configs --data-dir data/external/nfcorpus/prepared/nfcorpus --profile qwen3_8b --output results/nfcorpus_qwen3_8b_preflight_02.json 2>&1 | tee results/nfcorpus_qwen3_8b_preflight_02_run.log
```

验收观察：status=passed、实际CUDA设备、torch.bfloat16权重、4096维、实际输入上限8192、3633文档／324 dev查询，文档样本形状最多3×4096、query为1×4096，数值有限且L2范数接近1。长度统计中的超限文档／查询数按真实分词器结果核查，不提前填写0；峰值GPU字节不能称为整进程RSS。失败保留终端日志，不改成CPU或缩小模型冒充通过。同名预检报告拒绝覆盖，重跑用新的后缀。

用户返回输出或“好了”后，助手先读实际报告、日志和资源，检查配置与输入身份、样本和显存；只有通过并同步后，再给完整3633文档／324题的Qwen Dense dev运行命令。当前不自动执行正式开发集，更不先重编码医学主库。

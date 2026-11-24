# Dense模型选型：接入可切换的固定配置

2026-11-24，用户在查询模型候选后要求继续。当前工作单元改为先接入Qwen3-Embedding-8B的独立Dense对照，再固定候选测试重排。核心由用户编写；助手提供已核查的静态配置、测试与结果辅助。现有BM25／Dense／RRF成绩和两份BGE文档缓存均保留。本轮尚未加载、下载或运行Qwen模型，也没有新模型成绩。

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

main保留原五个位置参数，新增仅关键字参数embedding_profile="bge_small"。CLI新增--embedding-profile，choices为bge_small／qwen3_8b，默认bge_small；传给main。现有method仍为dense／bm25／rrf，不增加名为qwen的检索算法。

使用json和pathlib.Path读取脚本目录下configs/embedding_profiles.json。校验配置名有效，method=bm25时只允许默认bge_small（BM25本身不加载向量模型），不静默接受无效模型选择。只在dense／rrf分支初始化HuggingFaceEmbeddings，并从选中的配置传入model_name、model_kwargs、encode_kwargs、query_encode_kwargs四项；dimension与max_seq_length是项目元数据，不能将整个配置直接展开给模型构造器。

构造模型后核对embedding_model._client.max_seq_length和embedding_model._client.get_sentence_embedding_dimension()与所选配置一致；不一致抛ValueError，避免摘要与真正编码不同。这里_client是当前LangChain封装持有的SentenceTransformer对象，该访问只用于运行入口检查，检索核心继续使用embed_query／embed_documents接口。

调用prepare_document_embeddings时传实际dimension，evidence_path继续为data_dir/corpus.jsonl，cache_dir与chunk_size不改。模型对象与文档矩阵仍在查询循环外创建一次，Dense／BM25／RRF的检索编排与评分不改。

config["dense"]保留现有字段，新增embedding_profile与embedding_dimension；max_seq_length使用已核对的真实值，query_prefix取实际query_encode_kwargs["prompt"]，不再写死BGE前缀。模型／编码参数继续保存实际对象持有的字典，嵌套精度／长度也因此进入缓存身份和摘要。

自动run_name保持默认bge_small时的原规则dataset_method_split；Qwen自动名增加profile，例如nfcorpus_dense_qwen3_8b_dev。显式--run-name优先，同名覆盖仍由现有保存辅助拒绝。bm25不会在配置中冒充使用Qwen；三条旧基线和旧缓存不重新运行。

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

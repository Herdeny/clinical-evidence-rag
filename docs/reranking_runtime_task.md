# 真实重排运行入口

**2026-11-25预检工具已实现。** 助手新增scripts/evaluation/preflight_reranker.py，4项新辅助检查与支持6项／入口4项共14项通过，CLI帮助可运行，尚未执行真实GPU预检。工具沿用同一配置、加载及候选来源；统计全部联合长度后，只打分最多3对样本。完整用户命令见文末“真实预检”。根目录核心保持原样。

**2026-11-25下载已核对。** 固定Qwen4B快照17文件全部齐全，2权重分片8043614960字节，内容哈希与项目blobs地址一致；索引、BF16头部及张量总字节核对通过，无未完成分片。离线配置／分词器与yes/no ID检查成功，未加载真实权重。用户终端下载10:29.07、退出0，记录results/qwen3_reranker_4b_download_validation.json。下一项是小批真实预检，下载成功不等于模型推理通过。

**2026-11-25入口已验收。** 用户已完成run_reranking_eval.py，助手未改核心源码，4项入口检查及原相关46项共50项全部通过；记录results/reranking_entry_validation.json及源码快照。实际Python3.12.7接受当前f-string复用引号语法，不要求改写。三种profile的默认／显式名称、只加载一次模型、config_path指向文件、batch透传、真实临时加载／描述／评分／保存及CLI参数映射均通过。假模型只含CPU单参数，不是GPU或模型效果验收。下一步用户终端下载，命令见文末。以下任务说明保留本工作单元的设计与接口。

2026-11-25。本轮助手辅助已完成并通过相关46项检查；尚未下载任何reranker权重，没有真实模型效果或显存结论。用户下一项只新增根目录run_reranking_eval.py，把已有模块串起来。核心算法和评测已经实现，不重写。

## 新辅助的来源和职责

| 文件 | 由谁实现 | 本轮作用 |
| --- | --- | --- |
| configs/reranker_profiles.json | 助手 | 保存三种候选的固定版本、精度、输入长度、批次、指令和打分含义 |
| reranker_adapter.py | 助手 | build_reranker按配置创建一次CrossEncoder；describe_reranker读取真实设备／精度／长度等属性，返回可保存的元数据 |
| retrieval_results_io.py | 助手扩展原文件 | 现有save_beir_results新增frozen_rerank方法，保留候选来源、核对原候选集合并记录正确计时范围 |
| tests/test_reranking_support.py | 助手 | 6项辅助检查；不进入正式运行入口，不运行真实模型 |

原有frozen_candidates_io.py负责读旧候选，用户rerank_core.py负责重排，benchmark_eval.py负责逐题调用和评分。上述辅助不重新实现这些核心算法。

## 模型及参数依据

继续保留Qwen4B、Qwen8B及BGE-v2-m3三种候选，先运行Qwen4B，再在同一批候选上比较8B及BGE。先后顺序不是最终选型结论。4B是此前基于官方英文汇总提出的优先验证候选，不能据此宣称医学任务胜出。

| profile | 模型 | 固定revision |
| --- | --- | --- |
| qwen3_4b | Qwen/Qwen3-Reranker-4B | 22e683669bc0f0bd69640a1354a6d0aebcfeede5 |
| qwen3_8b | Qwen/Qwen3-Reranker-8B | 77d193c791ed757ca307ee72715aa132723da912 |
| bge_v2_m3 | BAAI/bge-reranker-v2-m3 | 953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e |

本轮重新核对[4B模型卡](https://huggingface.co/Qwen/Qwen3-Reranker-4B)、[8B模型卡](https://huggingface.co/Qwen/Qwen3-Reranker-8B)、官方公开API及固定版本小型配置，未下载权重。Qwen固定版本的modules.json明确为Transformer加LogitScore，true_token_id=9693、false_token_id=2152；默认query指令与Identity激活见其config_sentence_transformers.json。官方模型卡明确CrossEncoder.predict返回原始logit差值，可出现负数。BGE许可沿用此前官方模型卡核验的Apache-2.0。

本地sentence-transformers5.7.0真实类位于sentence_transformers/cross_encoder/model.py，构造器支持revision、local_files_only、max_length、prompts、model_kwargs和processor_kwargs；其内部自行加载Qwen模块和模板。不要在业务入口手写聊天模板或重复添加BGE embedding前缀。查询仍用原文，模型指令由CrossEncoder模板插入。

| 当前值 | 原因与状态 |
| --- | --- |
| device=cuda | 使用现有4090；describe_reranker核对实际设备，不自动回退CPU |
| dtype=bfloat16 | 保留未量化模型的精度与显存记录，实际值从模型权重读取 |
| attn_implementation=sdpa | 使用当前PyTorch注意力实现，不新安装FlashAttention；真实运行仍待预检 |
| max_length=4096 | 这是问题、正文和模板合计的运行上限；现有Qwen embedding最长正文2335、查询40只提供起点依据，不能替代reranker的联合分词统计；下载后必须检查真实截断情况 |
| batch_size=1 | 首轮显存预检的起点，避免把函数默认16误当4090已验证批次；不会减少每题100候选 |
| local_files_only=true | 权重先由用户终端下载到项目缓存，正式入口离线加载 |
| Identity激活 | 保存原始logit或yes/no logit差值，不转概率，不与Dense分数相加 |

4096与batch1不是最终最优配置，也尚未实测。之后真实预检与正式运行必须使用同一个build_reranker构造入口；若长度或批次因实测调整，记录新配置和运行名称，不改当前核心函数契约。模型命令继续经bash scripts/project_env.sh启动，所有缓存位于项目cache。

## 用户编写的入口

建议main接口：main(config_dir, data_dir, receipt_path, profile_name, run_name, result_dir)。六项显式传入，不给config_dir增加省略逻辑。路径由CLI的type=Path提供；若另行支持字符串，可自行转换，不要求为了测试加入额外守卫。

所需库：argparse负责CLI，json负责json.loads读取配置文本，pathlib.Path负责路径。业务导入是：frozen_candidates_io.load_frozen_candidates、reranker_adapter.build_reranker／describe_reranker、benchmark_eval.evaluate_frozen_reranking、retrieval_results_io.save_beir_results。

main内部依次完成以下工作。调用必须发生在main里或其调用链内，导入模块时不加载权重。

1. 从显式config_dir拼出reranker_profiles.json，read_text后用json.loads读取profiles，再按profile_name取一个profile。直接下标未知名称自然报KeyError即可，不强制增加异常包装。
2. load_frozen_candidates(receipt_path,data_dir=data_dir)取得frozen，并读取frozen.info保存为source_info。此步骤在模型加载前核对来源，避免先占GPU再发现输入错误。
3. build_reranker(profile)创建唯一的reranker。紧接着调用describe_reranker(reranker,profile_name=profile_name,profile=profile,config_path=profile_path)，保存为rerank_info。它返回字典，不是另一个模型。
4. evaluate_frozen_reranking(frozen,reranker,ks=(10,100),batch_size=profile['batch_size'])得到eval_df和run。batch_size来自配置，不能漏传后使用函数默认16。一次评测会逐题处理100候选。
5. 构建下面的config字典，再把eval_df／run／config／run_name／result_dir交给save_beir_results。该函数已经支持frozen_rerank，不另建保存循环。
6. 返回保存函数给出的summary，CLI打印summary['metrics']即可。

| config字段 | 值从哪里来 |
| --- | --- |
| dataset_name | source_info['dataset_name'] |
| data_dir | source_info['data_dir']，已解析的绝对路径 |
| split | source_info['split']；不额外提供一个可能冲突的split参数 |
| retrieval_method | 字符串frozen_rerank |
| ks | [10,100] |
| candidate_source | 整个source_info字典，保留原Dense配置、原产物、输入指纹与基线指标 |
| rerank | 整个rerank_info字典，保留本轮模型配置和实际运行属性 |

describe_reranker的返回内容包含profile_name、model_name、revision、max_length、batch_size、score_type，以及actual_device／actual_weight_dtype／actual_max_length、实际指令和库版本。保存模块不需要也不能接收模型对象。

CLI选项建议为--config-dir、--data-dir、--receipt、--profile、--run-name、--result-dir。前后路径参数type=Path，--profile可choices设为qwen3_4b／qwen3_8b／bge_v2_m3。main六参数显式传入，CLI本身可以保留有效默认值；args.receipt要对应main的receipt_path，不按变量名猜位置。使用if __name__ == '__main__'保护解析与调用。CLI命名只要一致即可，不按命名偏好验收。

run_name沿用既有命名方式：用户传--run-name时优先使用；未传时，在取得source_info之后、加载模型之前，用数据集、rerank、profile_name和split拼接默认名，例如nfcorpus_rerank_qwen3_4b_dev。独立实验可显式传入nfcorpus_rerank_qwen3_4b_dev_01或_02，不引入时间戳。已有同名结果仍由保存器拒绝覆盖。用户于2026-11-25重申保持前后一致，助手此前临时时间戳建议已撤回，不作为验收要求。

真实后续输入是项目results/nfcorpus_qwen3_8b_frozen_candidates.json及data/external/nfcorpus/prepared/nfcorpus；第一轮profile为qwen3_4b。此时用户只写入口，不启动下载或完整运行。保存后先审实际语义，以假模型核对编排，再提交同步；之后准备用户终端下载与真实小批预检。

## 验收和计时边界

- 读取同一描述文件和原查询，不重新创建embedding模型、向量矩阵或Dense检索，不读取标签给模型打分。
- 模型只初始化一次；实际配置、批次和运行属性能完整进入config.rerank；候选来源完整进入config.candidate_source。
- 对已有evaluate_frozen_reranking和save_beir_results各调用一次，返回summary；路径、profile和名称从CLI正确传入。
- 检查导入入口不会调用模型或自动运行评测，使用小型假模型即可，不用真实GPU验收编排。
- 真实模型预检后才能运行324题。固定100候选、返回全部100时Recall@100应保持原值；nDCG@10／Recall@10能否提高由真实模型成绩决定。
- 逐题latency_ms覆盖候选副本读取和重排，排除原Dense检索、文件／模型加载和指标计算；这不是单进程端到端延迟。正式运行的整进程时间和资源由终端另行记录。

当前辅助验收记录results/reranking_support_validation.json及_run.log：新辅助6项、原BEIR保存6项、CT保存6项、评测10项、加载6项、rerank12项，共46项通过。构造器检查使用真实类签名的autospec；运行属性检查用小型CPU参数；保存用合成冻结文件和假打分，不是下载或模型推理验收。

## 用户终端下载

入口验收并提交同步后，由用户在自己的终端执行以下命令。固定版本来自当前qwen3_4b配置；环境内hf download --help已实际核对支持revision参数。包装器设置项目内Hub／Xet等缓存，不改全局环境。命令只下载，不加载模型或运行评测。

```bash
# 进入项目目录，使日志路径指向项目results。
cd /home/wzh/clinical-evidence-rag
# 即使经过tee，也保留下载命令失败时的退出状态。
set -o pipefail
# 下载固定模型，终端显示进度，同时保存资源统计和运行日志。
HF_HUB_DISABLE_PROGRESS_BARS=0 TQDM_POSITION=-1 bash scripts/project_env.sh /usr/bin/time -v -o results/qwen3_reranker_4b_download_01_resources.txt /home/wzh/miniforge3/envs/all-in-rag/bin/hf download Qwen/Qwen3-Reranker-4B --revision 22e683669bc0f0bd69640a1354a6d0aebcfeede5 2>&1 | tee results/qwen3_reranker_4b_download_01_run.log
```

本轮日志名称固定为download_01，若单独重试且需要保留失败日志，使用download_02等新编号；Hub缓存会复用已经完整下载的文件，无需force-download。下载完成应显示项目cache/huggingface/hub/models--Qwen--Qwen3-Reranker-4B/snapshots/固定revision路径。用户贴出末尾输出后，助手只读核对文件及权重身份，再准备真实预检。此时不运行完整run_reranking_eval.py，也没有真实重排成绩。

单文件进度说明：本地huggingface_hub0.36.2的hf download没有show-progress参数，quiet用于关闭进度；文件进度的tqdm会在输出经过tee等非终端场景时自动隐藏。此处显式设置HF_HUB_DISABLE_PROGRESS_BARS=0，并用该版本实际支持的TQDM_POSITION=-1使文件字节进度在管道输出下保持显示。已用真实_get_progress_bar_context模拟10字节进度核对：普通非终端disable=True，加这两个变量后disable=False并实际输出字节进度；未下载权重。不要为了显示进度切换模型、缓存布局或下载后端。

实际缓存路径已通过包装器启动的子进程读取确认：HF_HUB_CACHE=/home/wzh/clinical-evidence-rag/cache/huggingface/hub，HF_XET_CACHE=/home/wzh/clinical-evidence-rag/cache/huggingface/xet。模型目录是hub/models--Qwen--Qwen3-Reranker-4B；snapshots/22e683669bc0f0bd69640a1354a6d0aebcfeede5提供原始文件名入口，Linux默认通常通过链接指向同模型目录下blobs中的实际文件。路径由scripts/project_env.sh设置，无需再增加local-dir或另放全局缓存。

## 真实预检

新增scripts/evaluation/preflight_reranker.py是助手编写的运行检查工具，复用正式build_reranker和describe_reranker；不是用户需要重写的核心，也不是新模型封装。工具验收并提交同步后，由用户在可见4090终端执行。

工具分三个阶段：先加载唯一重排模型并检查实际设备／精度／长度／指令；再用真实preprocess统计全部32400句对的联合长度，包含原query、完整文档、指令与模板；最后选原首两对和最长一对去重，最多3个句对使用真实predict打分。长度统计仅分词，不对32400句对做模型推理；内部CPU分词批次32不改变GPU配置batch_size=1。

统计时明确关闭截断，若任何输入超过当前4096，先显示超限数量与最长值，再停止，依据输出调整配置，不擅自切短正文。真实打分沿用正常模型输入处理，保留原始logit，一维、数量一致、有限即可，负数／大于1均合法，不做向量L2范数检查。

```bash
# 进入项目目录，保持结果路径与此前一致。
cd /home/wzh/clinical-evidence-rag
# 保留Python失败时的管道退出状态。
set -o pipefail
# 离线加载固定模型，保存真实预检结果、日志与资源统计。
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 bash scripts/project_env.sh /usr/bin/time -v -o results/nfcorpus_rerank_qwen3_4b_preflight_01_resources.txt /home/wzh/miniforge3/envs/all-in-rag/bin/python -u -m scripts.evaluation.preflight_reranker --config-dir configs --data-dir data/external/nfcorpus/prepared/nfcorpus --receipt results/nfcorpus_qwen3_8b_frozen_candidates.json --profile qwen3_4b --output results/nfcorpus_rerank_qwen3_4b_preflight_01.json 2>&1 | tee results/nfcorpus_rerank_qwen3_4b_preflight_01_run.log
```

预期通过范围：status=passed，query_count=324、length_check.pair_count=32400、pairs_over_limit=0，实际CUDA／BF16／4096与配置一致，score_check形状为样本数量的一维数组且全部有限。显存峰值属于本次模型加载＋少量样本打分，不能替代完整运行峰值；sample_predict_seconds也不是稳定查询延迟。报告绑定配置、代码、原描述文件、三输入和三产物身份，不修改旧检索结果或向量缓存。

当前辅助验证报告results/reranker_preflight_helper_validation.json：新4项＋模型支持6项＋用户入口4项，共14项通过，均未加载真实模型。真实预检结果只有用户执行上述命令后才能确认。报告拒绝覆盖，失败日志保留，必要重跑改成preflight_02等独立编号。通过并归档后，再准备完整324题重排命令。

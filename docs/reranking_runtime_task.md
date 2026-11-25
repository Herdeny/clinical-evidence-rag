# 真实重排运行入口

**2026-11-25当前节点：8B batch4真实预检01已通过并离线核对，下一步完整324题重排。** RTX4090／cuda:0、BF16／SDPA／4096，全部32400联合输入无超限；4个最长样本2414／2412／2411／2410 tokens，实际一个完整batch4，float32有限分数-3.75／-6.9375／-7.8125／-6.40625。峰值已分配17.567636GiB、预留18.158203GiB，整进程16.81秒、退出0；4个样本已用固定分词器独立重算长度，源码／输入／候选／配置／日志身份一致。记录results/nfcorpus_rerank_qwen3_8b_preflight_01_validation.json，尚无8B完整排序成绩。下一命令见“Qwen8B完整开发集重排”，不重新跑Dense，旧4B batch1结果保留；预检峰值不是全程峰值。

**2026-11-25当前节点：8B下载核对通过，等待用户运行batch4预检。** 19个文件／5权重分片16377142272字节，固定版本、内容哈希、索引与BF16头部和离线分词器均一致，无未完成分片；下载23:50.88、退出0，记录results/qwen3_reranker_8b_download_validation.json。助手只做文件和CPU检查，没有加载8B权重。读取到用户把三个profile的batch_size改为4，已保留；预检辅助现在可实际覆盖完整配置批次，命令和验收范围见“Qwen8B下载验收与完整批次预检”。原4B batch1成绩保持，当前batch4尚无真实预检或完整结果。以下较早的节点记录保留其当时状态。

**2026-11-25Qwen4B完整dev已验收。** 同候选324题四指标0.4099740875251688／0.2069843548748328／0.37949912510243394／0.39709670188154617，原Recall@100保持；nDCG@10相对+4.53%、Recall@10+7.69%。新增重排均值3.258秒/题，整轮17:40.07，nDCG@10有124升／106降／94同，独立核验通过。详见nfcorpus_retrieval_baselines.md，原结果保留。下一步按既定候选对照先下载8B，见文末；不因批次咨询擅自改配置。

**2026-11-25真实预检01通过。** 4090／cuda:0、BF16／4096／batch1及原始logit配置与实际模型一致；32400联合输入最小93、最大2414、P95=654、超限0。3对实际分数5.0625／3.75／-4.375，显存峰值已分配8.063002GiB、预留8.265625GiB。报告与源码／输入／命令／资源身份核对通过，进程15.04秒、退出0。记录results/nfcorpus_rerank_qwen3_4b_preflight_01_validation.json。下一步运行文末“完整开发集重排”；小批显存和耗时不代表完整运行成本。

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

## 完整开发集重排

本次只对既有Qwen3-Embedding-8B Dense的Top100进行Qwen3-Reranker-4B重排；使用相同324道dev原问题、文档正文、标签和四项指标。固定候选来源nfcorpus_dense_qwen3_8b_dev_01，模型仍为22e683...固定版本、BF16／4096／SDPA／batch1，不加入其他检索改动，也不选择test或MIRAGE。

正式run_name为nfcorpus_rerank_qwen3_4b_dev_01，显式名称沿用既有规则，不添加时间戳。助手在交运行命令前保存_run_audit.json、实际源码快照与三输入指纹，保护既有基线、预检及BGE／Qwen文档缓存；运行本身只读原候选并加载一个重排模型。用户在可见终端执行：

```bash
# 进入项目目录。
cd /home/wzh/clinical-evidence-rag
# 保留Python失败时的管道退出状态。
set -o pipefail
# 离线使用已通过预检的固定配置，保存结果、日志和整进程资源。
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 bash scripts/project_env.sh /usr/bin/time -v -o results/nfcorpus_rerank_qwen3_4b_dev_01_resources.txt /home/wzh/miniforge3/envs/all-in-rag/bin/python -u run_reranking_eval.py --config-dir configs --data-dir data/external/nfcorpus/prepared/nfcorpus --receipt results/nfcorpus_qwen3_8b_frozen_candidates.json --profile qwen3_4b --run-name nfcorpus_rerank_qwen3_4b_dev_01 --result-dir results 2>&1 | tee results/nfcorpus_rerank_qwen3_4b_dev_01_run.log
```

终端进度以324道题为单位，每题内部处理100个句对；本次合计32400对都将真实打分。最后打印四项指标字典，保存_results.jsonl、_run.json和_summary.json，加日志／资源共5个正式产物。

| 相同候选的原Dense基线 | 数值 |
| --- | --- |
| nDCG@10 | 0.3921959681142708 |
| Recall@10 | 0.19220254685998026 |
| nDCG@100 | 0.37012524211267905 |
| Recall@100 | 0.39709670188154617 |

本轮主要看前部排序质量、逐题变化与新增重排延迟。由于返回全部原100候选，Recall@100应保持0.39709670188154617；其他指标是否提升以实测为准。当前没有完整重排成绩，不由3对预检推断收益或运行时间。

逐题latency_ms覆盖候选副本读取＋重排，原Dense召回均值53.69274598138244ms单独报告；这不是完整两阶段端到端实测。GNU time提供整进程时间和主机RSS，本次正式入口没有采集全程GPU峰值，不拿预检显存或主机RSS代替。模型4B／8B／BGE后续同候选对照可沿用该入口，每套配置先独立预检。

结果返回后，由助手使用已适配新入口的scripts/evaluation/validate_beir_run.py独立重新评分、核对候选集合与预检固定配置、输入／源码／旧产物身份及实际资源命令。核验工具按--profile识别重排入口，旧BM25／Dense／RRF仍按--method，不让用户为旧脚本新增无意义参数。新增4项临时核验检查通过，结果results/rerank_validator_support_validation.json；不是完整真实运行的提前验收。

## batch_size影响与后续性能对照

2026-11-25用户询问提高batch_size对速度与结果的影响，属于概念与实验设计咨询，未授权修改当前固定运行配置。当前nfcorpus_rerank_qwen3_4b_dev_01仍使用已通过预检的batch1；配置和已准备回执保持原样。

当前ST5.7.0的predict先按输入长度估计排序，再每batch_size个句对执行一次前向，最后恢复原输入顺序；每题业务层predict仍调用一次。100候选时batch1／4／8／16分别需要100／25／13／7个前向批次。较大批次通常有利于吞吐与摊薄调度开销，但不会按倍数线性提速；批内按最长输入填充，长短混合可能增加无效计算。模型权重不会随批次复制，额外显存主要受激活、注意力与临时计算空间及长度影响，不能把8.06GiB峰值直接乘以batch倍数。

理论上推理批次不改变单个句对的任务或模型权重；实际BF16批处理的算子、填充及浮点归约可能产生分数差异，接近分数可能交换名次。因此不能承诺结果逐位相同，批次增大也不是排序质量提升方法。依据[PyTorch2.6批量数值精度说明](https://docs.pytorch.org/docs/2.6/notes/numerical_accuracy.html#batched-computations-or-slice-computations)及[HF填充说明](https://huggingface.co/docs/transformers/main/pad_truncation)。

后续若做批次性能对照，固定模型版本、指令、正文、长度和候选，仅调整batch，记录暖机后耗时／吞吐／显存以及分数差、排名和指标变化，独立命名并保留原batch1结果。当前预检最多3个打分样本，即使把profile批次改成8也只实际跑3个样本，不能由此声称验证过完整batch8；测试更大批次必须扩大样本，覆盖足够数量的较长输入，并在同一批句对上比较。相关加速与数值差异尚未在本项目实测。

## Qwen8B同候选对照：先下载

按已经确定的Qwen4B／8B／BGE对照继续。4B当前取得的是公开dev平均收益，尚不足以选定最终重排模型；8B需要在相同候选、正文与评分协议下实测。8B配置已经存在，用户核心入口共用，不改4B配置或旧结果。当前固定8B快照尚未下载，先由用户终端执行：

```bash
# 进入项目目录，保持缓存和结果位置一致。
cd /home/wzh/clinical-evidence-rag
# 保留下载失败时的管道退出状态。
set -o pipefail
# 下载既定8B重排候选，显示单文件进度并保留日志和资源。
HF_HUB_DISABLE_PROGRESS_BARS=0 TQDM_POSITION=-1 bash scripts/project_env.sh /usr/bin/time -v -o results/qwen3_reranker_8b_download_01_resources.txt /home/wzh/miniforge3/envs/all-in-rag/bin/hf download Qwen/Qwen3-Reranker-8B --revision 77d193c791ed757ca307ee72715aa132723da912 2>&1 | tee results/qwen3_reranker_8b_download_01_run.log
```

快照会进入项目cache/huggingface/hub/models--Qwen--Qwen3-Reranker-8B/snapshots/77d193c791ed757ca307ee72715aa132723da912。下载后先检查分片和固定版本，再以profile=qwen3_8b独立做真实预检；不能把4B的长度／显存值写成8B实测。随后用同一份冻结候选完整重排，比较收益与成本，原4B数据和batch1基线始终保留。

## Qwen8B下载验收与完整批次预检

2026-11-25用户报告下载完成。已流式重算19个文件的SHA256，普通Git对象使用带blob头部的SHA1核对缓存地址；快照链接均指向该模型的项目内blobs。索引要求5个分片，逐张量核对分片归属、BF16、形状字节、数据偏移连续性和文件总长，张量总字节16377096192与索引一致。离线AutoConfig／AutoTokenizer与LogitScore的yes9693／no2152一致，未构造神经网络。资源记录23:50.88、主机RSS4293064KiB、退出0。明细在results/qwen3_reranker_8b_download_validation.json，下载成功还不代表显存或排序效果通过。

本轮实际配置已由用户改为三个profile均batch4，助手未回改成1。原辅助最多3对的策略不能验证完整batch4，因此扩展scan_candidate_lengths(...,batch_size=...)：batch1保持原首两对＋最长一对；batch>1保留联合token长度最大的batch_size对，凑成一个完整批次再predict。用有界最小堆保留少量样本，不复制全体正文；长度相同时按原出现次序选择，不参考相关性标签。完整长度统计仍覆盖32400对。报告新增batch_check，明确实际打分数量、配置批次、样本策略和full_batch_exercised；如果候选不足则不宣称覆盖整批。

跨题选出的最长4对构成保守的显存压力样本；它不代表正式每题的批次，也不能保证所有其他输入形态都不溢出。此次只改助手的预检及辅助检查，用户核心不变。tests/test_reranking_entry.py原硬编码batch=1的断言已改为读取临时配置核对透传，避免测试反过来强迫修改有效实现。相关27项CPU检查通过（核心12、预检5、入口4、支持6），CLI帮助通过，未执行真实GPU；记录results/qwen3_reranker_8b_preflight_helper_validation.json。

用户终端下一步执行以下命令；config-dir／data-dir／receipt／profile／output均显式传入，仍复用原候选，不重新运行Dense或生成向量：

```bash
# 进入项目目录，统一缓存和结果路径。
cd /home/wzh/clinical-evidence-rag
# 保留Python失败时的管道退出状态。
set -o pipefail
# 离线预检8B，读取当前batch4配置并保存报告、资源与实时日志。
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 bash scripts/project_env.sh \
  /usr/bin/time -v \
  -o results/nfcorpus_rerank_qwen3_8b_preflight_01_resources.txt \
  /home/wzh/miniforge3/envs/all-in-rag/bin/python -u \
  -m scripts.evaluation.preflight_reranker \
  --config-dir configs \
  --data-dir data/external/nfcorpus/prepared/nfcorpus \
  --receipt results/nfcorpus_qwen3_8b_frozen_candidates.json \
  --profile qwen3_8b \
  --output results/nfcorpus_rerank_qwen3_8b_preflight_01.json \
  2>&1 | tee results/nfcorpus_rerank_qwen3_8b_preflight_01_run.log
```

验收看status=passed、actual_device=cuda:0、实际BF16、4096联合预算、32400对无超限，以及batch_check里configured_batch_size=4、scored_pair_count=4、full_batch_exercised=true和4个有限原始logit。真实GPU峰值以这次报告为准，不能复制4B值。若显存不足，保留本轮失败日志后判断实际原因和批次；不静默回退CPU或改配置续跑。

通过后才准备完整8B重排。由于旧4B结果是batch1，后续作模型本身效果／成本对照时应同batch补齐4B；当前不同模型且不同批次的运行可分别展示，但不能把差异全归因于参数规模或模型。原batch1产物和当时的执行快照继续保留，不覆盖旧结果或改写旧指标。

## Qwen8B完整开发集重排

2026-11-25真实预检01已通过。独立核对当前profile、固定源码／输入指纹、原候选归属、实际设备／精度／激活／指令，以及终端JSON和资源中的全部显式参数。四个样本均为原候选中的MED-957，查询ID分别PLAIN-2639／3371／3381／770；用已下载固定快照AutoTokenizer的模型模板对原query和完整正文重算长度，得到2414／2412／2411／2410，与报告一致。核验没有加载神经网络／执行GPU，也没有重新扫描全部32400对长度。

预检已分配18863105024字节（17.567635536193848GiB）、预留19497222144（18.158203125GiB）；整进程16.81秒、主机RSS5454612KiB、退出0。加载1.335685963秒、四对样本1.431585001秒只属于本次预检，不推断全量速度、模型收益或全程显存。负分是合法raw_yes_minus_no_logit，不要求概率范围、非负或L2。

本轮正式名称nfcorpus_rerank_qwen3_8b_dev_01，模型／版本／batch4／指令／4096预算保持刚通过的配置。继续读取同一份Qwen Dense原Top100，324题／32400对，只运行一个8B重排模型；不重新构造embedding／Dense。交命令前，助手先提交同步节点，再在已忽略的results中保存实际十文件源码快照、三输入身份及旧结果／缓存内容指纹的_run_audit.json，供运行后核对，不要求用户新增核心代码。

```bash
# 进入项目目录。
cd /home/wzh/clinical-evidence-rag
# 保留Python失败时的管道退出状态。
set -o pipefail
# 复用原候选与当前8B batch4配置，记录完整结果、资源和实时日志。
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 bash scripts/project_env.sh \
  /usr/bin/time -v \
  -o results/nfcorpus_rerank_qwen3_8b_dev_01_resources.txt \
  /home/wzh/miniforge3/envs/all-in-rag/bin/python -u run_reranking_eval.py \
  --config-dir configs \
  --data-dir data/external/nfcorpus/prepared/nfcorpus \
  --receipt results/nfcorpus_qwen3_8b_frozen_candidates.json \
  --profile qwen3_8b \
  --run-name nfcorpus_rerank_qwen3_8b_dev_01 \
  --result-dir results \
  2>&1 | tee results/nfcorpus_rerank_qwen3_8b_dev_01_run.log
```

验收要求进程正常完成、324题各返回原100候选、summary／results.jsonl／run.json／resources.txt／run.log五产物齐全且有限，独立用原dev qrels重算四项指标并与逐题及均值对应。返回全部原100候选时Recall@100应保持0.39709670188154617；nDCG@10／Recall@10是否提升看实际输出，不预设8B胜出。记录逐题升降、均值／中位数／P95重排延迟和整进程成本。候选读取＋重排计时排除原Dense检索、模型／文件加载及评分；正式入口未采集全程GPU峰值，不拿预检值或主机RSS代替。8B batch4与旧4B batch1先分别报告，最终模型对照需同batch补齐4B，不能把两种变化合称模型规模带来的提升。

## Jina候选调研：尚未接入或实测

2026-11-25用户询问Jina重排模型。已查官方模型卡、服务说明和技术报告，属于选型咨询，不自动替换当前Qwen／BGE对照，也未添加profile、下载权重或调用API。

[jina-reranker-v3.5模型卡](https://huggingface.co/jinaai/jina-reranker-v3.5)描述0.6B多语言列表式重排，以Qwen3-0.6B为基座，混合滑动窗口与全局注意力，131K是问题与整组文档共享的上下文预算。接口为AutoModel加model.rerank(query,documents)，返回index与relevance_score；当前项目是CrossEncoder.predict独立句对打分，不能只换model_name就假装完成接入。若后续适配，应固定版本与其自定义实现、核对候选index映射、整组长度和截断、候选顺序／分组策略及显存。列表式的候选间交互不同于当前batch_size作为独立句对的并行批次；拆组可能改变上下文，不能仅按硬件参数处理。

[v3.5论文](https://arxiv.org/html/2607.18152v1)在相同jina-embeddings-v5-text-small Top100协议下报告nDCG@10百分数：BEIR平均Jina3.5=63.20、Qwen4B=62.28；NFCorpus分项Jina3.5=38.45、Qwen4B=42.48，医疗ChatDoctor为70.63与73.38、CURE平均62.20与63.68。外部结果只说明该评测中Jina有竞争力且并非每类任务领先，不能与我们不同召回来源／本地dev的0.409974直接比较，也不构成本项目Jina实测。官方效率数据使用A100和FlashAttention-2，不能用来声称本机4090快于当前4B。

[v2-base-multilingual模型卡](https://huggingface.co/jinaai/jina-reranker-v2-base-multilingual)提供CrossEncoder.predict示例，属于更接近当前调用形式的逐对打分，但原生1024上下文及长文分块策略与当前4096预算不同，接入前仍需核对。v3.5是当前更值得研究的不同架构候选，模型小不等于所有任务效果弱，也不保证整组长输入显存低。

[官方许可说明](https://jina.ai/reranker/)列当前v2／v3／v3.5等权重为CC-BY-NC-4.0，商业生产部署需要商业许可；应与项目中Apache-2.0候选区分。API服务另按服务条件评估。本次建议将v3.5保留为待验证候选，后续如纳入应做同一原Top100的独立架构对照，既有数据、原始结果和当前实验顺序保持，不能因一次咨询直接更改标准。

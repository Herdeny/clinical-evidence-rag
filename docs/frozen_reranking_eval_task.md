# 冻结候选与重排评测衔接

2026-11-25。用户的rerank纯函数已完成。本轮先由助手提供只读候选加载辅助，用户再复用现有评分循环接入重排。没有真实reranker成绩，不下载或加载模型。

## 已提供的辅助

frozen_candidates_io.py提供load_frozen_candidates(receipt_path, *, data_dir)，读取现有冻结回执中的results／run／summary，核对文件内容及corpus／queries／当前qrels身份，按query_id和文档ID恢复候选。它不读取向量矩阵，不调用embedding、重排模型或评分器，也不改写原始产物。

返回FrozenCandidates对象：

| 属性或方法 | 内容 |
| --- | --- |
| queries_df | 原始划分的查询表副本，仍为id、query字段，顺序不变 |
| qrels | 供既有评分器使用的标签副本，不传给重排模型 |
| get_hits(query_id) | 按ID取得该题候选副本，保留原始顺序、检索分数、完整正文与来源元数据 |
| info | 原运行、模型配置、输入／产物指纹、候选预算、原指标与原检索计时范围 |

当前真实入口是results/nfcorpus_qwen3_8b_frozen_candidates.json，数据目录data/external/nfcorpus/prepared/nfcorpus。已实际恢复324题各100候选、共32400句对所需的文档；该数量不是新增题目或训练样本。首题PLAIN-1、首候选MED-2418，原Recall@100为0.39709670188154617。记录results/frozen_candidates_loading_validation.json。

真实查询PLAIN-237和PLAIN-2859文字相同（Pollutants in Californian Breast Tissue），本轮候选ID和分数也相同，没有观察到旧结果混淆。两个ID和两行查询仍须独立保留。合成样本使用相同文字、不同候选，检验加载器确实按ID关联，不依赖当前候选碰巧相同。

辅助的6项检查对应：正确关联及与用户rerank衔接、返回副本与源文件不变、源产物改动、语料／查询／标签改动、内容关联错误、合法空候选不丢题。检查目的先说明，再验证；不根据测试偏好增加用户核心分支，不规定统一异常名称。

## 用户本轮只修改benchmark_eval.py

原evaluate_beir_retrieval没有错误。BM25／Dense／RRF按问题文字检索，原回调接口足够；读取已保存候选这个新增用途需要query_id。保留原有计时、run构造、pytrec_eval和返回结构，不复制一份评分算法。

第一处改动：在evaluate_beir_retrieval现有参数后增加仅关键字选项pass_query_id=False。默认调用仍为retrieve_fn(query_text, max(ks))。开启时仍保留这两个位置参数，额外传query_id=query_id，ID来自当前查询行。该选项用于给回调提供查询身份，不参与文本改写、模型编码或评分。

第二处改动：新增evaluate_frozen_reranking(frozen, reranker, ks=(10,100), *, batch_size=16)。frozen就是上述辅助返回的对象，reranker由外部初始化后注入，函数内不创建或下载模型。batch_size只是传给已完成的rerank接口，真实模型运行批次稍后预检确定。

该函数内部定义一个接收(query, k, *, query_id)的回调：通过frozen.get_hits(query_id)取得原候选，把原query、候选、k以及外部reranker／batch_size交给用户已实现的rerank，返回新的候选列表。然后用frozen.queries_df、frozen.qrels、这个回调及ks调用既有evaluate_beir_retrieval，并开启ID传递。原样返回eval_df、run。新增导入只需from rerank_core import rerank，其他评分库沿用现有模块。

本轮不需要新增CLI、初始化CrossEncoder或修改rerank_core；也不调用尚未扩展的保存方法。后续保存辅助需要为重排记录正确的来源和计时范围，助手先提供后再交入口接线，不能将本轮结果冒写成原Dense方法。

## 可见的验证目标

- 原调用不传新选项，仍只调用两参数检索函数，原评分行为保持；不是让用户重做旧实验。
- 开启后，回调得到当前行的query_id和原query。相同文字的两个ID仍能读取不同候选，不删除或合并查询。
- 冻结重排只把query和候选正文送模型；qrels只进入既有评分器，空候选仍保留在评分分母中。
- 本轮默认100候选全部返回时，Recall@100应保持原值；前部排序能否提升需之后真实模型实测。计时包含回调中的候选副本读取和重排，不包含原Dense召回、文件加载或模型初始化，不能称端到端两阶段实测延迟。

用户保存后先审实际代码与上述行为，再用小型假打分器检查，无需真实模型或GPU。通过后先提交同步，再准备真实重排配置、下载及预检。

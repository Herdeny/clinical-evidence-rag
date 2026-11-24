# NFCorpus 检索评测接入任务

当前数据已准备：3,633篇文档，2,590 train／324 dev／323 test查询。来源版本、原始文件、转换记录和校验见[数据说明](../data/external/nfcorpus/DATA_CARD.md)。数据读取与公共评测已验收，结果保存辅助已提供；当前由用户实现独立运行入口。核心仍由用户编写。

## 已验收：数据读取函数

2026-11-23最新检查：原9方法全部通过。真实dev返回3633文档、324查询、324个qrels查询键、11385标签，原等级1／2、正文与行序保留；通用目录／前导零／划分隔离及既定异常输入检查均通过。源码SHA46419011dd285ad6eeaf3fd35481acc0a43e946c5c3ead15dd3922b9ffd18833，诊断见results/benchmark_data_validation.json及revision6。用户核心未由助手修改，无模型／检索。读取环节结束，保留有效的any(布尔Series)写法。

项目根目录 benchmark_data.py 已实现：

    load_beir_dataset(data_dir, *, split="dev")

data_dir 是任意符合 corpus.jsonl／queries.jsonl／qrels/{split}.tsv 约定的BEIR数据目录，不把本机绝对路径或nfcorpus文件名写死进函数。当前调用目录为 /home/wzh/clinical-evidence-rag/data/external/nfcorpus/prepared/nfcorpus。split只允许train、dev、test，非法值抛ValueError；本轮调用dev。模块导入时不读取数据或创建模型。

返回 (corpus_df, queries_df, qrels)：

| 返回对象 | 字段或结构 | 用途 |
| --- | --- | --- |
| corpus_df | id、title、body、text、source_id、locator | 兼容当前Dense／BM25使用的文档字段 |
| queries_df | id、query | 仅保留当前划分中的查询，不加病例模板 |
| qrels | dict[str, dict[str, int]] | 查询ID → 文档ID → 原始相关性等级 |

corpus_df 的 id 原样来自 _id；body保留原text，text为标题加一个空格加正文并去首尾空白。标题允许为空，按空字符串处理；正文不允许为空。source_id沿用文档ID；locator记录dataset名称和document_id，表达基准文档身份，不伪造医学原文页码或URL。保留官方文档次序，不按qrels过滤语料。

queries_df将_id改为id、text改为query，仅依据当前split的qrels题号过滤查询。qrels必须保留整数等级，不展开成“每条都必须命中的证据组”，也不能只留第一个相关文档。不要把qrels的score误当检索得分。

## 库和必要用法

只需pandas、pathlib.Path和Python的dict／set。JSONL可用pd.read_json(path, lines=True, dtype=False)，TSV可用pd.read_csv(path, sep="\t", dtype={"query-id": str, "corpus-id": str, "score": int})。ID按字符串保留，不能丢前导零。

Path可用斜杠组合子路径；rename(columns=...)统一字段名；Series.str.cat(..., sep=" ")拼接标题和正文，str.strip()去首尾空白；isin(...)按题号集合过滤查询。TSV含连字符列名，itertuples(index=False, name=None)可按普通三元组遍历，避免错误地当Python属性名访问。setdefault(key, {})用于建立两层qrels字典。

应拒绝重复文档／查询ID、重复query-document对，以及qrels引用不存在的query或document。不要用drop_duplicates或丢行来掩盖无效输入。对查询过滤后再检查非空；文件不存在可保留FileNotFoundError。适配器不编码、不检索、不计算Recall或nDCG。

## 验收

对官方dev目录调用后：len(corpus_df)=3633，len(queries_df)=324，len(qrels)=324；sum(len(items) for items in qrels.values())=11385。所有qrels查询属于queries_df，相关文档属于corpus_df，等级保持整数1／2。官方文件指纹不变，语料次序、标题及原正文保留。

助手还会用小型临时BEIR目录检查路径可配置、标签多对多、无关查询过滤、重复及悬空ID拒绝，确保不是只能读取一份nfcorpus。用户贴代码或保存后说“好了”，助手重读实际文件再验收，不代写核心。

## 已验收：公共检索评测函数

2026-11-24最新检查：原7方法全部通过，实际源码SHAae8ba1240f9fcc9ca79dfbe029c2ecaa305c1887af7c7a8222aae67244254f6d。验证每题一次检索、原查询与分数保真、空命中保留及分母、等级排序、自定义K、输入／命中校验与异常定位。结果见results/benchmark_eval_validation.json及revision5；两题均值0.5仅为临时验收期望，不是公开基准分数。用户核心未由助手修改，无公开题库或模型运行；按约定先提交推送，再接运行入口与保存。

用户已完成 /home/wzh/clinical-evidence-rag/benchmark_eval.py，实现 evaluate_beir_retrieval(queries_df, qrels, retrieve_fn, ks=(10, 100))，返回 (eval_df, run)。本步不创建模型、构建索引或保存文件，已有读取模块与Dense／BM25／RRF接口继续复用。

依赖：pandas、time、math、tqdm以及pytrec_eval。2026-11-24已确认用户安装pytrec-eval-terrier==0.5.11，tqdm可用；安装名与import名不同。该依赖与[BEIR pyproject](https://github.com/beir-cellar/beir/blob/main/pyproject.toml)一致；接口见[BEIR官方评分实现](https://github.com/beir-cellar/beir/blob/main/beir/retrieval/evaluation.py)，版本文件见[PyPI](https://pypi.org/project/pytrec-eval-terrier/0.5.11/)。真实依赖的临时两题探针通过，正确排序题四项指标1、空命中题四项0；仅属依赖核验，不是用户函数验收或公开基准成绩。

输入queries_df使用读取器返回的id、query两列，qrels保持原等级字典。每条原query只调用一次retrieve_fn(query, max(ks))；检索调用不接收qrels，不加CT模板。time.perf_counter()仅计量retrieve_fn调用，换算ms；索引初始化与指标计算不计入该列。循环可用tqdm，给出total=len(queries_df)。

run结构为query_id → {document_id: float(retrieval_score)}；与qrels的相关性等级严格区分。保留真实检索分数，不改成标签或排序行号。每次hits的id应唯一、score可转换为有限浮点数，不接受NaN／Infinity；异常直接抛出并标识query_id，不通过字典覆盖或丢题掩盖。

评分器可用pytrec_eval.RelevanceEvaluator(qrels, {"ndcg_cut.10,100", "recall.10,100"})，再evaluate(run)取得逐题指标，返回键如ndcg_cut_10、recall_100。ks可配置时相应生成指标字符串。主报告是nDCG@10及Recall@100，额外保留两种指标在两个K的值便于核查。直接使用库的等级与排序语义，不另写gain公式。

eval_df每查询一行，列为query_id、query、retrieved_ids、scores、latency_ms，以及每个k对应的ndcg_at_{k}、recall_at_{k}。按queries_df原顺序返回。空hits也保留run[qid]={}与结果行，四项指标记0；若评分库不返回该qid，不能因此丢行。汇总将对全部行做算术平均，当前函数不额外返回summary。

既定输入约束一次说明：ks是非空、不重复的正整数序列；queries_df非空且id唯一，查询ID集合与qrels的键一致；任何单次hits不能含重复id、非有限分数或超过max(ks)条。空hits有效；检索异常使本次运行失败，不静默跳题。有效但少于K的命中按实际返回评估，不人工补齐文档。

验收先用临时查询、标签和假retrieve_fn，无模型运行：两查询中一条按等级正确排序检出全部相关文档，另一条返回空；结果恰两行，前者四指标为1、后者为0，各指标均值0.5；每题调用一次、原query不变、K=max(ks)，run保留实际float分数。交换不同相关等级文档顺序应降低nDCG而不改变召回；重复ID及非有限分数应明确拒绝。用户保存后助手检查实际源码并验证，再接真实BM25开发集、Dense与RRF入口及保存，不直接消耗test。

## 已验收：公开基准运行入口

2026-11-24复验：既有6方法全部通过，源码SHA61477fca26a322e10aa30dcbff649d12390204e46f133013f9fc3a43355ed87e。覆盖三方法索引一次初始化、Dense第二轮文档缓存复用、当前corpus路径、元数据、默认与显式CLI参数及无效方法拒绝。诊断results/benchmark_entry_validation.json及revision1。所有输入为临时材料，模型是假向量编码器；无真实权重／GPU或公开查询运行。按约定先提交推送后交用户在终端跑BM25 dev。

评测节点777d784已同步GitHub。保存辅助已在retrieval_results_io.py中实现save_beir_results(result_df,run,*,config,run_name,result_dir)，6项新检查及6项旧保存检查全部通过；不调用模型或检索器，不重新计算逐题指标。助手准备好该辅助后再交接用户入口，避免引用尚不存在的函数。

用户已完成 /home/wzh/clinical-evidence-rag/run_benchmark_eval.py，接口为main(method,data_dir,split,cache_dir,run_name)，返回保存辅助的summary，再添加__main__参数解析。使用argparse、pathlib.Path、functools.partial及现有项目模块；Dense继续使用langchain_huggingface.HuggingFaceEmbeddings。不要从Notebook导入。

执行顺序：校验method为dense／bm25／rrf；load_beir_dataset(data_dir,split=split)读取配套语料与当前查询；在查询循环外构建所需索引并用partial得到retrieve_fn；evaluate_beir_retrieval(queries_df,qrels,retrieve_fn,ks=(10,100))；调用save_beir_results(eval_df,run,config=config,run_name=...,result_dir=root/results)，最后返回summary。

BM25与RRF分支调用build_bm25(corpus_df,k1=1.5,b=0.75,epsilon=0.25)，partial绑定retrieve_bm25的bm25_index和evidences。Dense与RRF沿用run_retrieval_eval.py内的固定模型设置：BAAI/bge-small-en-v1.5、revision=5c38ec7c405ec4b44b94cc5a9bb96e735b38267a、cuda、local_files_only=True，文档batch8／normalize_embeddings=True／prompt为空，查询batch1／normalize_embeddings=True／prompt为既有检索前缀。调用prepare_document_embeddings时evidences=corpus_df、evidence_path=data_dir/corpus.jsonl、cache_dir为CLI参数、chunk_size=512；源文件SHA及实际标题拼接后的id/text共同确定缓存身份，因此NFCorpus获得自身3633文档矩阵，医学主库783847行矩阵不重做。记录模型512-token输入限制和330篇超过长度的事实，不声称全部正文已编码。

RRF使用partial绑定retrieve_rrf：两路闭包、candidate_k=100、rrf_constant=60。最终评估预算max(ks)=100，不沿用CT入口的20候选。每个索引只初始化一次。

config公共字段为dataset_name=data_dir.name、data_dir绝对路径字符串、split、retrieval_method、ks=[10,100]、query_template="{query}"、corpus_text="title + space + body; strip"。BM25子配置保存model_name="rank_bm25.BM25Okapi"、device="cpu"、query_prefix=""及k1／b／epsilon。Dense子配置保存实际model_name、model_kwargs、encode_kwargs、query_encode_kwargs、query_prefix、device、embeddings_cache与矩阵shape及最大输入长度；RRF另记candidate_k／rrf_constant。配置放在方法层，不强制复制模型信息到顶层。

CLI提供--method（默认bm25）、--data-dir（Path，默认root/data/external/nfcorpus/prepared/nfcorpus）、--split（默认dev）、--cache（Path，默认root/cache/embeddings）和--run-name。后者默认dataset_method_split，复跑同名会被保存辅助拒绝覆盖，应显式给新名称。summary.metrics供终端展示。

验收先用临时BEIR目录、真实小型BM25和假Dense模型检查参数到结果的完整链路，确认配置、文件、预算与索引只建一次；用户先写完整入口，不由助手代写。通过并同步后再给用户可见终端命令跑真实BM25 dev，继而Dense与RRF。test与MIRAGE当前不运行。

保存辅助写入三个文件：{run_name}_results.jsonl保留全部逐题字段；{run_name}_run.json保留题号到文档和检索分数；{run_name}_summary.json保存全部查询的指标均值、耗时、方法配置、评分包版本、输入文件SHA。当前没有任何真实NFCorpus模型成绩；辅助测试的0.5仍是临时验收值。

## 已完成：BM25 dev 首轮运行

2026-11-24用户执行完成并核验：nDCG@10=0.2657379994665381、Recall@100=0.20567783238375933，平均检索2.839ms，整进程1.99s，324题均返回100条。逐题重评分、输入／源码及产物身份均通过，审计complete_integrity_validated。完整四指标与边界见[开发集对照报告](nfcorpus_retrieval_baselines.md)。

入口验收后先提交并同步GitHub，再执行下面命令。该轮使用配套3633篇文档、324条dev查询和11385条标注，CPU BM25一次建索引，每题返回最多100条；指标由已验收函数和真实pytrec_eval计算。当前没有预设分数，也不以临时两题的0.5作为真实期望。

输入已按固定清单验证SHA，9份执行源码已快照。运行回执results/nfcorpus_bm25_dev_01_run_audit.json已更新为complete_integrity_validated。由用户在可见终端执行，助手不另开后台任务。

```bash
# 从项目目录运行，让日志路径对应本轮身份。
cd /home/wzh/clinical-evidence-rag
# 保留管道前方Python运行失败的退出状态。
set -o pipefail
# 运行完整dev，保存进程资源统计与实时终端输出。
/usr/bin/time -v -o results/nfcorpus_bm25_dev_01_resources.txt /home/wzh/miniforge3/envs/all-in-rag/bin/python -u run_benchmark_eval.py --method bm25 --data-dir data/external/nfcorpus/prepared/nfcorpus --split dev --run-name nfcorpus_bm25_dev_01 2>&1 | tee results/nfcorpus_bm25_dev_01_run.log
```

成功后results下生成同前缀的_results.jsonl、_run.json、_summary.json，以及上面保存的_run.log、_resources.txt。返回终端打印的指标或说明运行结束，助手读取本地文件核验；如失败，保留日志并按本轮运行记录排错，不静默删除失败题或覆盖旧结果。正式数据第一次运行在此时才开始，test与MIRAGE仍未参与。

## 当前任务：用户终端运行 Dense dev

BM25已核验，先提交同步其报告和核验工具，再执行本轮。使用同一配套文档、原query、dev标注与Top-100预算，独立结果名nfcorpus_dense_dev_01；固定模型配置沿用已验收入口，文档与查询编码用CUDA，相似度及Top-K仍是NumPy。

本地固定revision的模型权重和所需配置已检查存在，但准备阶段未加载模型或检测GPU。设置两个离线开关，避免模型封装探测未缓存的远端元数据。首次将生成NFCorpus的3633×384文档向量，外层512条保存检查点、模型batch8；后续复用。固定模型输入上限512，330篇长文档将按既定模型规则截断，完整原文保持。医学主库向量与BM25基线均保留。

```bash
# 使用项目目录定位本轮日志和结果。
cd /home/wzh/clinical-evidence-rag
# 保留Python失败时的管道退出状态。
set -o pipefail
# 离线使用已缓存模型，在GPU编码，并保存资源统计和终端输出。
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 /usr/bin/time -v -o results/nfcorpus_dense_dev_01_resources.txt /home/wzh/miniforge3/envs/all-in-rag/bin/python -u run_benchmark_eval.py --method dense --data-dir data/external/nfcorpus/prepared/nfcorpus --split dev --run-name nfcorpus_dense_dev_01 2>&1 | tee results/nfcorpus_dense_dev_01_run.log
```

启动回执results/nfcorpus_dense_dev_01_run_audit.json状态prepared_for_user_terminal_not_started，包含9份源码指纹、相同输入、模型版本和5份BM25原产物保护指纹。用户运行结束或遇到错误后保留输出，助手检查实际文件，不能把准备状态或临时验收值写成Dense成绩，也不擅自后台启动或重新跑BM25。通过Dense核验和同步后再做RRF；test和MIRAGE当前不运行。

## 后续接入保持同一接口

数据适配通过后，查询循环直接将query传给统一retrieve_fn(query,k)，复用现有Dense／BM25／RRF与文档缓存；不经过CT的Report/Question模板。公开基准新增评测函数，不伪造report、gold_evidence_groups来迎合旧保存接口。

之后以BEIR使用的pytrec_eval指标实现核对nDCG@10、Recall@100，用户已完成查询编排和评分，助手已提供保存辅助；当前继续接运行入口。当前评分包已安装，评测函数已通过7项临时数据验收。RRF基准候选预算每路100、常量60，默认CT设置不改。

运行入口与结果按数据集／方法／划分命名，dev用于调试，test等方法固定后再完整评测。模型版本、原始语料、标题拼接、512-token截断、候选预算和计时范围均入配置。MIRAGE依然负责最终问答，CT合成题只作产品场景回归，三类评测分别报告。

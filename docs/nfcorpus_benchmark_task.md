# NFCorpus 检索评测接入任务

当前数据已准备：3,633篇文档，2,590 train／324 dev／323 test查询。来源版本、原始文件、转换记录和校验见[数据说明](../data/external/nfcorpus/DATA_CARD.md)。数据读取适配已验收；当前接入现有检索与官方排序指标，随后提供独立运行入口和结果保存。核心仍由用户编写。

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

## 当前任务：公共检索评测函数

由用户新建 /home/wzh/clinical-evidence-rag/benchmark_eval.py，实现 evaluate_beir_retrieval(queries_df, qrels, retrieve_fn, ks=(10, 100))，返回 (eval_df, run)。本步不创建模型、构建索引或保存文件，已有读取模块与Dense／BM25／RRF接口继续复用。

依赖：pandas、time、math、tqdm以及pytrec_eval。2026-11-23检查发现tqdm已安装，pytrec_eval／ir_measures／beir未安装。用户在all-in-rag环境安装 pytrec-eval-terrier==0.5.11；安装名与import名不同。该依赖与[BEIR pyproject](https://github.com/beir-cellar/beir/blob/main/pyproject.toml)一致；接口见[BEIR官方评分实现](https://github.com/beir-cellar/beir/blob/main/beir/retrieval/evaluation.py)，版本文件见[PyPI](https://pypi.org/project/pytrec-eval-terrier/0.5.11/)。本轮仅核查，尚未安装或运行评分库。

输入queries_df使用读取器返回的id、query两列，qrels保持原等级字典。每条原query只调用一次retrieve_fn(query, max(ks))；检索调用不接收qrels，不加CT模板。time.perf_counter()仅计量retrieve_fn调用，换算ms；索引初始化与指标计算不计入该列。循环可用tqdm，给出total=len(queries_df)。

run结构为query_id → {document_id: float(retrieval_score)}；与qrels的相关性等级严格区分。保留真实检索分数，不改成标签或排序行号。每次hits的id应唯一、score可转换为有限浮点数，不接受NaN／Infinity；异常直接抛出并标识query_id，不通过字典覆盖或丢题掩盖。

评分器可用pytrec_eval.RelevanceEvaluator(qrels, {"ndcg_cut.10,100", "recall.10,100"})，再evaluate(run)取得逐题指标，返回键如ndcg_cut_10、recall_100。ks可配置时相应生成指标字符串。主报告是nDCG@10及Recall@100，额外保留两种指标在两个K的值便于核查。直接使用库的等级与排序语义，不另写gain公式。

eval_df每查询一行，列为query_id、query、retrieved_ids、scores、latency_ms，以及每个k对应的ndcg_at_{k}、recall_at_{k}。按queries_df原顺序返回。空hits也保留run[qid]={}与结果行，四项指标记0；若评分库不返回该qid，不能因此丢行。汇总将对全部行做算术平均，当前函数不额外返回summary。

既定输入约束一次说明：ks是非空、不重复的正整数序列；queries_df非空且id唯一，查询ID集合与qrels的键一致；任何单次hits不能含重复id、非有限分数或超过max(ks)条。空hits有效；检索异常使本次运行失败，不静默跳题。有效但少于K的命中按实际返回评估，不人工补齐文档。

验收先用临时查询、标签和假retrieve_fn，无模型运行：两查询中一条按等级正确排序检出全部相关文档，另一条返回空；结果恰两行，前者四指标为1、后者为0，各指标均值0.5；每题调用一次、原query不变、K=max(ks)，run保留实际float分数。交换不同相关等级文档顺序应降低nDCG而不改变召回；重复ID及非有限分数应明确拒绝。用户保存后助手检查实际源码并验证，再接真实BM25开发集、Dense与RRF入口及保存，不直接消耗test。

## 后续接入保持同一接口

数据适配通过后，查询循环直接将query传给统一retrieve_fn(query,k)，复用现有Dense／BM25／RRF与文档缓存；不经过CT的Report/Question模板。公开基准新增评测函数，不伪造report、gold_evidence_groups来迎合旧保存接口。

之后以BEIR使用的pytrec_eval指标实现核对nDCG@10、Recall@100，用户实现查询编排和评分调用，助手提供保存辅助。当前评分包未安装，不在数据读取任务中引入额外依赖。RRF基准候选预算每路100、常量60，默认CT设置不改。

运行入口与结果按数据集／方法／划分命名，dev用于调试，test等方法固定后再完整评测。模型版本、原始语料、标题拼接、512-token截断、候选预算和计时范围均入配置。MIRAGE依然负责最终问答，CT合成题只作产品场景回归，三类评测分别报告。

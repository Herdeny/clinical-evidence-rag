# NFCorpus 检索评测接入任务

当前数据已准备：3,633篇文档，2,590 train／324 dev／323 test查询。来源版本、原始文件、转换记录和校验见[数据说明](../data/external/nfcorpus/DATA_CARD.md)。本次用户任务是完整实现数据读取适配；之后再接现有检索、官方排序指标及独立结果保存。核心仍由用户编写。

## 当前实现一个完整读取函数

2026-11-23最新检查：真实dev读取主流程通过，返回3633文档／324查询／324个qrels查询键／11385标签，等级与正文保真检查通过。字典键、查询字段、isin和返回顺序都已正确。剩余收尾是TSV显式ID字符串／grade整数dtype、通用locator和此前列明的输入校验；9方法中真实dev一项通过，其余8方法仍待完成。最新诊断见results/benchmark_data_validation.json及revision3，用户实现未由助手修改。

在项目根目录新建 benchmark_data.py，实现：

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

## 后续接入保持同一接口

数据适配通过后，查询循环直接将query传给统一retrieve_fn(query,k)，复用现有Dense／BM25／RRF与文档缓存；不经过CT的Report/Question模板。公开基准新增评测函数，不伪造report、gold_evidence_groups来迎合旧保存接口。

之后以BEIR使用的pytrec_eval指标实现核对nDCG@10、Recall@100，用户实现查询编排和评分调用，助手提供保存辅助。当前评分包未安装，不在数据读取任务中引入额外依赖。RRF基准候选预算每路100、常量60，默认CT设置不改。

运行入口与结果按数据集／方法／划分命名，dev用于调试，test等方法固定后再完整评测。模型版本、原始语料、标题拼接、512-token截断、候选预算和计时范围均入配置。MIRAGE依然负责最终问答，CT合成题只作产品场景回归，三类评测分别报告。

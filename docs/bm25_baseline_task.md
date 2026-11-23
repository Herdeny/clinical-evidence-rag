# 当前工作单元：BM25 单独检索基线

日期：2026-11-18。核心实现由用户完成。本轮只加入 BM25，复用现有评测、证据格式与运行入口；后续再做 RRF。

**执行顺序更新：当前先批量扩库并固定主要数据版本，再执行本任务的正式对照。** 下文的函数接口、分词及参数约定继续保留；238 条／32 题是现有回归集，不是要求先完成的另一轮正式实验。扩库后按实际输入规模验收，不写死数量。已写的代码、已安装依赖与保存辅助继续使用，不要求重写。具体节点以 [数据扩充安排](data_expansion_milestones.md) 为准。

**2026-11-19 本任务已完成并实测。** 用户实现三个函数和CLI入口，所有遗留参数／配置问题已修正。全库783,847条、32道开发题，Canonical／Group Recall@1、3、5均为0.28125、0.34375、0.453125；独立核验通过。详见 [真实基线归档](medical_v3_bm25_baseline.md)，不重复运行。下一步先接Dense向量缓存并完成同库向量对照，再做RRF。

## 固定输入与已有结果

- 语料：冻结后的 data/v3/evidence.jsonl，数量与 SHA-256 取 corpus_manifest.json，不能写死 238。
- 题目：data/v3/cases.ct.dev.jsonl，原 32 道 CT 开发题原样保留；不读留出题或 MIRAGE 测试题调参。
- 查询：原有 Report 加 Question 模板。英文 BGE 前缀是向量编码配置，不拼进 BM25 查询。
- 本轮仍每题一次 Top-5，计算两类 Recall@1／3／5。
- 同库对照：medical_v3_dense_ct_dev，尚待为新语料编码并运行。原 [CT v2 向量实测归档](ct_v2_dense_baseline.md)保留作回归，不能作为换库后 BM25 的直接公平对照。

## 技术选择与状态

使用 rank-bm25==0.2.2 的 BM25Okapi 公共接口。该版本已安装到当前 all-in-rag 环境，安装不升级已有依赖；API 及参数将以本地实际安装内容核对。BM25 分词、索引组织、返回结构和评测接入由用户实现，助手不代写核心函数。

参考基线作为最终项目的可复现比较实现保留，不以教学为由迁移框架。后续扩大医学语料时需另测构建成本、内存及检索耗时；小库可运行不能当作已经证明全量 MIRAGE 语料上的扩展能力。Qdrant 的存储与服务集成仍按既定路线验证，不将更换 BM25 公式或后端混作本次检索算法收益。

核验的主要来源：[官方仓库及用法](https://github.com/dorianbrown/rank_bm25)、[计分源码](https://github.com/dorianbrown/rank_bm25/blob/master/rank_bm25.py)、[固定版本](https://pypi.org/project/rank-bm25/0.2.2/)、[Apache-2.0 许可证](https://github.com/dorianbrown/rank_bm25/blob/master/LICENSE)。本地 langchain-community 0.3.27 的 BM25Retriever 也使用此后端，但标准检索结果只返回 Document；本项目使用公开 get_scores 接口以保留原始分数和统一五字段结构，不依赖其私有方法。

## 用户新增文件：retrieve_bm25.py

定义下面三个函数，不在模块导入时读取文件或构建索引。

### tokenize(text)

返回字符串 token 列表。规则在本轮固定：

- 转小写，英文片段与数字分别作为 token，数字保留小数点。
- 连字符和其他标点作为分隔；保留 no、not 等所有词，不做停用词删除或词干化。
- 文档与查询使用同一函数；不修改原始 evidence.text 或报告正文。
- 例：Lung-RADS 6.0 mm, no growth. 应得到 [lung, rads, 6.0, mm, no, growth] 六个字符串。

可使用 re.findall；匹配规则由用户编写。

### build_bm25(evidences, *, k1=1.5, b=0.75, epsilon=0.25)

输入当前证据 DataFrame。按其行顺序对 text 分词，将二维 token 列表传给 BM25Okapi，返回索引对象。空语料或所有正文均无 token 时明确报 ValueError。

- k1：词频饱和参数，先固定 1.5。
- b：文档长度归一化强度，先固定 0.75。
- epsilon：此实现对负 IDF 的平滑系数，固定 0.25，不宣称它使所有可能语料的得分都非负。

索引在运行入口构建一次，不放进逐题 retrieve 或评测计时中；构建后不重排证据表。

### retrieve_bm25(query, k, *, bm25_index, evidences)

验证 k 为正整数；使用 tokenize 处理原始查询，调用 bm25_index.get_scores(query_tokens) 取得与证据行对应的一维分数。自行取 Top-K 并组装与向量检索相同的 id、score、source_id、locator、text 五字段列表。

返回分数降序；同分按证据表原始行顺序，明确采用稳定排序。K 超过语料量时返回现有全部证据。索引与证据表需来自同一次构建，不能只因条数相同就交换另一个顺序的表。

本轮不增加分数阈值，未匹配词项时的零分也按上述固定 K 和同分规则处理；零分结果不代表证据支持。BM25 原始分数不是概率，也不与向量相似度直接相加；后续 RRF 融合排名。

## 用户修改文件：run_retrieval_eval.py

复用当前脚本，不另复制运行程序。

1. 保留已经写好的 main() 和编码参数配置；将 cases_path／evidence_path 改为基于脚本目录的 v3 路径，不依赖从项目父目录启动。
2. 用 argparse 增加 --method，选项为 dense、bm25，默认 dense，保持原来的无参数行为。
3. dense 分支保留现有编码对象及 retrieve；bm25 分支只构建 BM25 索引，通过 partial 绑定 retrieve_bm25。只有 dense 分支初始化 HuggingFaceEmbeddings。
4. 两分支得到相同调用接口的 retrieve_fn，继续调用现有 evaluate_retrieval，不改其公式和逐题字段。
5. config 记录 retrieval_method。BM25 使用 model_name=rank_bm25.BM25Okapi、device=cpu、query_prefix 为空；另记包版本、k1／b／epsilon、分词规则、同分规则、K 和同一批数据路径。
6. config 增加 corpus_name=medical_v3，run_name 使用 medical_v3_bm25_ct_dev，生成独立逐题结果和摘要。v3 向量对照另存 medical_v3_dense_ct_dev；保留原始 v2 向量结果，不为补写历史配置而重跑或覆盖原摘要。

保存辅助已由助手扩展：读取 config.retrieval_method 和 corpus_name 标记方法与数据版本；旧配置仍默认 dense／ct_v2。证据 ID 与文件指纹按流读取，避免保存时再把整库加载成另一张 DataFrame。每题字段与评分校验保持原约定。BM25 的计时包括查询分词、计分、排序和结果组装，不含一次性索引构建。

运行命令：

```bash
/home/wzh/miniforge3/envs/all-in-rag/bin/python /home/wzh/clinical-evidence-rag/run_retrieval_eval.py --method bm25
```

## 一次验收

- 分词例子符合规则，构建索引的 corpus_size 与冻结的 v3 chunk_count 相等。
- --help 可显示选项，导入脚本不加载模型或读数据；BM25 模式不初始化 BGE。
- 32×16 逐题结果，每题五个有效唯一 ID、对应得分降序；六项指标均合法，输入指纹与 v3 新库向量对照相同。
- 独立保存 results/medical_v3_bm25_ct_dev_results.jsonl 与 medical_v3_bm25_ct_dev_summary.json，方法为 bm25、corpus_name 为 medical_v3。
- 对比两种检索的六项均值及逐题得失，检查向量漏检题有无被 BM25 补到；不要求 BM25 总分一定更高。

用户保存代码与输出后，助手检查实现和实际结果。当前BM25函数、CLI及真实全库基线均已完成并核验；Dense同库对照待完成，不能直接比较旧小库Dense成绩。

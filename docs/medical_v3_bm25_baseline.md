# 医学主语料 v3 的 BM25 开发集基线

运行与核验日期：2026-11-19。核心实现和入口由用户编写；助手执行原样 CLI、保存资源记录并独立核验。没有改写用户核心代码。

## 输入与方法

- 输入：data/v3/evidence.jsonl，783,847 条；data/v3/cases.ct.dev.jsonl，32 道原 CT 开发题。未使用留出题或 MIRAGE。
- 证据 SHA-256：d120657651a681df56b29353fe69da5cabe8dff0c94bad55f673e99145c0bbd5。
- 开发题 SHA-256：f13291a4718866e06701370a0a6b1622bbf329f1514faac2885105f0fdc6f786。
- rank-bm25 0.2.2 / BM25Okapi，k1=1.5、b=0.75、epsilon=0.25，CPU。依赖版本和代码指纹另见运行审计。
- 查询是原 Report 加 Question 模板，不附加 BGE 前缀。统一小写，正则 `[a-z]+|\d+(?:\.\d+)?`，保留停用词，不词干化。
- 每题检索一次 Top-5；分数降序，同分保持语料原行顺序。三个核心函数、非默认行索引、参数与无效输入、稳定排序此前已用合成样例检查。

命令：

```bash
/home/wzh/miniforge3/envs/all-in-rag/bin/python /home/wzh/clinical-evidence-rag/run_retrieval_eval.py --method bm25
```

## 实际成绩

| 指标 | @1 | @3 | @5 |
| --- | ---: | ---: | ---: |
| Canonical Recall | 0.28125 | 0.34375 | 0.453125 |
| Group Recall | 0.28125 | 0.34375 | 0.453125 |

Top-5 需求组完整覆盖 14 题、部分覆盖 1 题、零覆盖 17 题。这里的 0.453125 是逐题需求组覆盖率的均值，不能解释成回答正确率，也不能直接说 45.31% 的题全部答对。题目仍是 AI 初标，未经独立医生复核。

Top-5 共 160 次命中，来源类型计数为 paper 43、evidence_summary 24、recommendation_statement 55、guideline 37、source_landing_page 1。命中来源不等于已经证明某个医学命题受支持；未进行生成或引用支持率评测。

## 实际资源消耗

- 每题检索平均 4332.917 ms，中位数 4298.497 ms；32 次检索合计 138.653 秒。
- 整个 CLI 进程耗时 2:56.53，峰值 RSS 18,133,656 KiB，约 17.294 GiB，退出状态 0。
- 查询计时包括分词、BM25 全库计分、稳定排序和命中结果组装；不包括读文件、建索引和保存。整进程计时则包括这些阶段及模块导入。
- 峰值内存是整个进程的峰值，不是单独 BM25 索引的大小；本轮未单独测量索引构建时间，不能从总耗时中直接推算为建索引耗时。
- 本实现由 Python 词频字典和 NumPy 在 CPU 上执行；config.device 是运行记录，不是可让 rank-bm25 自动使用 CUDA 的开关。用户询问 GPU 后已解释此区别，没有要求切换 BM25 后端。后续 BGE 文档编码仍计划使用 CUDA。

本轮证明了当前实现可以完成该规模的开发集评测，同时也暴露了全库逐词计分的成本。没有据此证明其满足最终在线服务延迟或全量 MIRAGE 的运行预算；生产后端的扩展性需要另测，参考基线保留。

## 独立核验与复现材料

- [逐题结果](../results/medical_v3_bm25_ct_dev_results.jsonl)：32×16，每题 5 个有效唯一 ID，分数有限且降序。
- [原始运行摘要](../results/medical_v3_bm25_ct_dev_summary.json)：实际参数、输入指纹、指标与计时范围。
- [独立核验](../results/medical_v3_bm25_ct_dev_validation.json)：按原题逐项复算六个指标、需求组覆盖、摘要和延迟；扫描全部证据确认所有命中与标注 ID 有效。
- [资源原始输出](../results/medical_v3_bm25_ct_dev_resources.txt)：GNU time 的进程耗时与峰值内存。
- [运行审计](../results/medical_v3_bm25_ct_dev_run_audit.json)：代码／输入／结果指纹、依赖版本及原 v2 成绩未改动的检查。
- results/medical_v3_bm25_ct_dev_code_snapshot 保存核验时与执行前指纹一致的源文件副本，供以后回查；不是新的生产入口。

输入、执行前后代码及旧 CT v2 结果指纹均通过核验。本轮无新增 LLM、嵌入模型或付费 API 调用，无留出／MIRAGE 评测。

## 接下来

2026-11-20后续更新：同一v3输入的[Dense基线与缓存](medical_v3_dense_baseline.md)已完成并核验，Group Recall@5=0.421875，查询均值330.062ms；当前由用户实现RRF。CT-v2 Dense的0.484375使用238条小库，与本轮783,847条不同，不能直接归因为算法优劣。

## 2026-11-26：原入口接入证据评估的三题联调

用户亲自执行medical_v3_bm25_ct_review_smoke_3_01，使用同一783,847片段与CT2-001／002／003，开启DeepSeek单轮评估。助手只读核验，没有重跑检索、调用API或修改核心。三题的Top-5 ID及分数均与上方原32题基线中对应结果完全一致；按冻结ID标注的六项Recall均为0，不能据三题替代32题或120题的整体成绩。

三次结构化响应均成功返回，模型均自评证据不足；ok=3仅表示返回结构与当前校验有效。输入6,333、输出1,194、共7,527 tokens；768个缓存读取tokens已包含在输入中，不重复相加。检索均值4,428.608 ms，评估均值2,900.038 ms，分别计时；整进程56.91秒、峰值RSS18,115,052 KiB（约17.276 GiB）、退出0，不将分阶段均值叫端到端延迟。

| 题目 | 给模型的实际材料 | 观察到的评估问题 |
| --- | --- | --- |
| CT2-001 | 多个病例影像片段与戒烟研究，无筛查报告框架说明 | 发现证据缺口，但把未给出的结节尺寸当作选择框架的必要事实 |
| CT2-002 | 筛查资格、吸烟史及其他学会建议等内容 | 混同筛查资格与已完成筛查的框架命名，要求补吸烟暴露 |
| CT2-003 | 论文引言与ACR偶发结节Variant 2／3表格行 | 识别检查目的未知，但列出已知年龄及超出当前任务的缺项，并将偶发路径称为最可能适用 |

以上是针对题目范围、报告明示事实和实际输入的定性复核，不是医生复核后的临床准确率。ACR入口说明Lung-RADS的筛查报告用途；USPSTF原文分别讨论筛查资格与LDCT报告标准化，评估需要保留这一区别。[ACR范围说明](https://www.acr.org/clinical-resources/clinical-tools-and-reference/reporting-and-data-systems/lung-rads) · [USPSTF声明](https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/lung-cancer-screening)

标签口径也有待复核：CT2-003检到的acr-incidental-2023::b0029正文包含标注b0021的完整范围句，精确ID计分未计算这部分等价证据。它仍缺少另一需求组的筛查依据，不能改判整题充分；冻结标签本轮不修改，保留这一潜在漏标观察。

原始两份JSON、日志和资源文件保持原样，验证报告位于本地results/medical_v3_bm25_ct_review_smoke_3_01_validation.json。核验覆盖逐题字段、六项指标、用量、均值／中位数、输入指纹、原BM25对应排名与实际资源命令，不宣称完整历史所有产物均未变。

下一步固定同三题、模型、提示词与核心，通过原--evidences参数做受控上下文对照。scope_context_control_5.jsonl只含从v3原样选出的5个片段：筛查范围、Lung-RADS说明、两个偶发范围和一段筛查资格干扰项；每题Top-5都会得到这5条。运行名medical_v3_bm25_ct_review_scope_control_3_01，准备状态未执行。其corpus_name=medical_v3表达来源，实际索引只有5条，evidence_path／evidence_count明确记录子集。该人工选定上下文只诊断核验器，Recall不能被用作检索改进成绩；全库与MIRAGE验收要求不变。助手未改提示词或代码，真实调用仍由用户执行。

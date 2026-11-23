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

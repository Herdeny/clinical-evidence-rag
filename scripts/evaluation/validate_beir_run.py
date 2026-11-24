# 从已保存产物重新评分并核对运行身份，不重新检索或加载模型。
import argparse
# 解析终端打印的Python指标字典。
import ast
# 读取标准BEIR标签。
import csv
# 为输入、源码和产物计算内容指纹。
import hashlib
# 读取和保存审计记录。
import json
# 验证有限值和浮点数误差。
import math
# 独立核对逐题延迟的中位数。
from statistics import median
# 核对实际评分库与运行时记录一致。
from importlib.metadata import version
# 处理源码与结果路径。
from pathlib import Path
# 使用与BEIR协议一致的真实评分器。
import pytrec_eval

# 项目根目录位于本模块上方两层。
ROOT = Path(__file__).resolve().parents[2]


# 按块计算文件指纹，不把大文件复制到内存。
def file_sha(path):
    # 为当前文件创建摘要器。
    digest = hashlib.sha256()
    # 只读真实文件。
    with Path(path).open("rb") as stream:
        # 读取到文件末尾即停止。
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            # 累加当前块。
            digest.update(block)
    # 返回可复查的内容身份。
    return digest.hexdigest()


# 比较评分或汇总浮点数，明确拒绝NaN和Infinity。
def same_number(actual, expected):
    # JSON里的数值转为标准浮点数。
    actual, expected = float(actual), float(expected)
    # 重算使用同一评分协议，允许极小的浮点误差。
    return math.isfinite(actual) and math.isfinite(expected) and math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-12)


# 核验保存结果；checked_on由调用方传客户端日期。
def validate_run(run_name, *, checked_on, result_dir=ROOT / "results"):
    # 限定到当前结果目录的单个文件名前缀。
    if not run_name or Path(run_name).name != run_name:
        # 不接受目录跳转。
        raise ValueError("run_name必须是文件名前缀")
    # 按运行身份定位固定文件。
    result_dir = Path(result_dir).resolve()
    # 运行前回执保留原始输入和源码身份。
    audit_path = result_dir / f"{run_name}_run_audit.json"
    # 读取回执，不推断未记录的运行设置。
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    # 只接受本次准备的运行名。
    assert audit["run_name"] == run_name
    # 当前保存的摘要、逐题结果、run、日志和资源文件必须齐全。
    paths = {suffix: result_dir / f"{run_name}_{suffix}" for suffix in ("summary.json", "results.jsonl", "run.json", "run.log", "resources.txt")}
    # 文件缺失不登记为完成。
    assert all(path.is_file() for path in paths.values()), "missing output artifacts"
    # 摘要只作为待核对结果，不作为评分依据。
    summary = json.loads(paths["summary.json"].read_text(encoding="utf-8"))
    # 逐题结果保持原始行序。
    rows = [json.loads(line) for line in paths["results.jsonl"].read_text(encoding="utf-8").splitlines() if line.strip()]
    # run保留真实文档得分，供评分器重新排序。
    run = json.loads(paths["run.json"].read_text(encoding="utf-8"))
    # 输入指纹必须仍匹配执行前回执。
    for metadata in audit["input_sha256"].values():
        # 任何输入变化都需要单独说明，不能沿用旧分数。
        assert file_sha(metadata["path"]) == metadata["sha256"], metadata["path"]
    # 核对执行前源码副本及当前工作区身份。
    for name, expected in audit["code_sha256"].items():
        # 快照必须完整且未被改写。
        assert file_sha(Path(audit["code_snapshot"]) / name) == expected, name
        # 当前首次核验要求工作区也仍为同一版本。
        assert file_sha(ROOT / name) == expected, name
    # 确认摘要声明的数据集、划分和方法与启动回执一致。
    assert (summary["dataset_name"], summary["split"], summary["retrieval_method"]) == (audit["dataset_name"], audit["split"], audit["method"])
    # 摘要的三个输入身份必须各自与运行前回执相符。
    expected_inputs = {metadata["path"]: metadata["sha256"] for metadata in audit["input_sha256"].values()}
    # 不能把其他语料或划分的结果贴到本运行名下。
    assert {metadata["path"]: metadata["sha256"] for metadata in summary["input_sha256"].values()} == expected_inputs
    # 从摘要定位原始标准BEIR文件。
    data_dir = Path(summary["config"]["data_dir"])
    # 语料只需保留文档ID集合。
    with (data_dir / "corpus.jsonl").open(encoding="utf-8") as stream:
        # 按原始_id核验命中来源。
        document_ids = {json.loads(line)["_id"] for line in stream if line.strip()}
    # 从当前划分原始标签独立构造评分器输入。
    with (data_dir / "qrels" / f"{audit['split']}.tsv").open(encoding="utf-8", newline="") as stream:
        # 保留所有等级和多对多标签。
        labels = list(csv.DictReader(stream, delimiter="\t"))
    # 保留完整query到doc的相关性映射。
    qrels = {}
    # 显式拒绝重复标签，不允许字典覆盖掩盖它们。
    for label in labels:
        # 当前查询、文档和整数等级。
        query_id, document_id, grade = label["query-id"], label["corpus-id"], int(label["score"])
        # 每个query-document对只能有一个标注。
        assert document_id not in qrels.setdefault(query_id, {}), "duplicate qrel"
        # 保存原始相关性等级。
        qrels[query_id][document_id] = grade
    # 从原始查询文件检查实际检索文本和次序。
    with (data_dir / "queries.jsonl").open(encoding="utf-8") as stream:
        # 仅将当前划分送入验证，不展示任何其他划分题面。
        queries = [item for line in stream if line.strip() for item in [json.loads(line)] if item["_id"] in qrels]
    # 输入规模与执行前回执保持一致。
    assert (len(document_ids), len(qrels), len(labels)) == (audit["document_count"], audit["query_count"], audit["qrel_pairs"])
    # 摘要不能改变分母或语料规模。
    assert (summary["document_count"], summary["query_count"]) == (len(document_ids), len(qrels))
    # 行数、题号、原问题与原始dev顺序逐项一致。
    assert [(row["query_id"], row["query"]) for row in rows] == [(query["_id"], query["text"]) for query in queries]
    # run也必须覆盖全部当前划分查询。
    assert set(run) == set(qrels)
    # 实际评分预算与启动回执一致。
    ks = audit["ks"]
    # 摘要不能误报另一个K集合。
    assert list(summary["config"]["ks"]) == ks
    # 重新计分使用相同的评分包版本。
    assert summary["scorer"]["version"] == audit["packages"]["pytrec-eval-terrier"] == version("pytrec-eval-terrier")
    # 使用原始标注和已保存run独立重新调用评分器。
    rescored = pytrec_eval.RelevanceEvaluator(qrels, {"ndcg_cut." + ",".join(map(str, ks)), "recall." + ",".join(map(str, ks))}).evaluate(run)
    # 所有查询都要计入指标。
    assert set(rescored) == set(qrels)
    # 保存观察到的返回数量分布和有相关命中的题数。
    hit_counts, positive_queries = {}, 0
    # 对每条查询核对命中、分数和四种指标。
    for row in rows:
        # 用题号对应原始标注和评分输入。
        query_id, ids, scores = row["query_id"], row["retrieved_ids"], row["scores"]
        # 不重复、不超预算，所有文档来自配套语料。
        assert len(ids) == len(scores) == len(set(ids)) <= max(ks) and set(ids) <= document_ids
        # JSON中保存的分数应全部有限。
        assert all(math.isfinite(value) for value in scores)
        # 逐题列表的分数保持降序。
        assert all(first >= second for first, second in zip(scores, scores[1:]))
        # 评分输入与逐题结果必须为同一组文档与分数。
        assert dict(zip(ids, scores)) == run[query_id]
        # 耗时应为非负有限数。
        assert math.isfinite(row["latency_ms"]) and row["latency_ms"] >= 0
        # 保存逐题候选数量分布。
        hit_counts[str(len(ids))] = hit_counts.get(str(len(ids)), 0) + 1
        # 独立用集合交集核对最大K召回，不依赖评分器公式。
        relevant = {identifier for identifier, grade in qrels[query_id].items() if grade > 0}
        # 当前语料的标注均应存在正相关文档。
        assert relevant
        # 最大K下全部返回文档均参与召回，与并列排序规则无关。
        assert same_number(row[f"recall_at_{max(ks)}"], len(set(ids) & relevant) / len(relevant))
        # 统计至少命中一篇相关文档的查询数。
        positive_queries += bool(set(ids) & relevant)
        # 将评分器返回键映射到已约定的结果列。
        for k in ks:
            # 两种指标逐题对照，不只看整体均值。
            assert same_number(row[f"ndcg_at_{k}"], rescored[query_id][f"ndcg_cut_{k}"])
            # 召回也逐题核对。
            assert same_number(row[f"recall_at_{k}"], rescored[query_id][f"recall_{k}"])
    # 对全部题目重新汇总指标。
    means = {f"{metric}_at_{k}": sum(row[f"{metric}_at_{k}"] for row in rows) / len(rows) for k in ks for metric in ("ndcg", "recall")}
    # 所有均值必须与摘要一致。
    assert all(same_number(summary["metrics"][name], value) for name, value in means.items())
    # 终端打印结果也应来自同一份汇总。
    printed = ast.literal_eval(paths["run.log"].read_text(encoding="utf-8").strip().splitlines()[-1])
    # 对照终端指标，避免混入另一轮输出。
    assert all(same_number(printed[name], value) for name, value in means.items())
    # 从GNU time中读取进程级资源，和逐题检索耗时分别报告。
    resources = dict(line.strip().rsplit(": ", 1) for line in paths["resources.txt"].read_text(encoding="utf-8").splitlines() if ": " in line)
    # 非零退出码不得登记为成功运行。
    assert resources["Exit status"] == "0"
    # 核对资源统计属于当前运行。
    assert f"--run-name {run_name}" in resources["Command being timed"]
    # 资源统计中的实际方法也必须与回执一致。
    assert f"--method {audit['method']}" in resources["Command being timed"]
    # 提取时间字符串，支持时分秒或分秒。
    elapsed = next(value for name, value in resources.items() if name.startswith("Elapsed (wall clock)"))
    # 将不同长度的时间表示统一为秒。
    elapsed_seconds = sum(float(part) * 60 ** index for index, part in enumerate(reversed(elapsed.split(":"))))
    # 重新核对逐题平均耗时。
    mean_latency = sum(row["latency_ms"] for row in rows) / len(rows)
    # 摘要中的检索延迟不能被进程总耗时替代。
    assert same_number(summary["latency_ms"]["mean"], mean_latency)
    # 中位数也应由同一批逐题耗时计算。
    assert same_number(summary["latency_ms"]["median"], median(row["latency_ms"] for row in rows))
    # 全部检查通过后才创建验证结果。
    validation = {"checked_on": checked_on, "status": "passed", "run_name": run_name, "dataset_name": audit["dataset_name"], "method": audit["method"], "split": audit["split"], "document_count": len(document_ids), "query_count": len(rows), "qrel_pairs": len(labels), "metrics": means, "mean_query_latency_ms": mean_latency, "process_wall_seconds": elapsed_seconds, "maximum_process_rss_kib": int(resources["Maximum resident set size (kbytes)"]), "exit_status": 0, "returned_count_distribution": hit_counts, "queries_with_positive_hit_at_max_k": positive_queries, "queries_without_positive_hit_at_max_k": len(rows) - positive_queries, "per_query_metrics_match_rescoring": True, "max_k_recall_matches_set_intersection": True, "inputs_and_snapshot_and_current_code_match_receipt": True, "output_sha256": {name: file_sha(path) for name, path in paths.items()}, "validator_sha256": file_sha(Path(__file__)), "validator_retrieval_or_model_calls": False, "scorer": summary["scorer"], "execution_git_commit": audit.get("git_commit")}
    # 诊断留在本地结果目录，报告可以引用其指纹与结论。
    validation_path = result_dir / f"{run_name}_validation.json"
    # 保存完整验证结论。
    validation_path.write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # 运行前回执更新为真正完成，保留原始输入和准备信息。
    audit.update(status="complete_integrity_validated", validated_on=checked_on, validation_file=str(validation_path), validation_sha256=file_sha(validation_path))
    # 原始产物本身不改写。
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # 返回已核验的事实供报告生成使用。
    return validation


# 允许显式离线调用，不在检索运行时隐式执行。
if __name__ == "__main__":
    # 简单CLI只接收已保存运行名和核验日期。
    parser = argparse.ArgumentParser()
    # 运行名称对应既有本地文件前缀。
    parser.add_argument("run_name")
    # 日期由当前客户端上下文提供。
    parser.add_argument("--checked-on", required=True)
    # 可在独立副本目录核验，不固定写正式结果目录。
    parser.add_argument("--result-dir", type=Path, default=ROOT / "results")
    # 解析调用参数。
    args = parser.parse_args()
    # 仅在实际检查通过后打印结果。
    print(json.dumps(validate_run(args.run_name, checked_on=args.checked_on, result_dir=args.result_dir), ensure_ascii=False, indent=2))

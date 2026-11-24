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


# 只读核对Dense文档缓存，既不创建模型也不重新生成向量。
def validate_dense_cache(summary, audit, data_dir):
    # 数组只以内存映射方式读取。
    import numpy as np
    # 实际模型和编码配置来自本轮摘要。
    dense = summary["config"]["dense"]
    # 缓存路径和使用状态来自真实prepare返回值。
    cache = dense["embeddings_cache"]
    # 读取当前已发布的缓存清单。
    manifest_path = Path(cache["manifest_path"])
    # 不打开写锁或改变清单内容。
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    # 所有文档都应已经成功发布。
    assert manifest["status"] == cache["status"] == "complete"
    # 固定每行对应的语料身份和编码设置。
    identity = manifest["identity"]
    # 检查预期矩阵规模。
    expected_shape = tuple(audit.get("expected_vector_shape", [audit["document_count"], 384]))
    # 清单、摘要和执行前预期必须一致。
    assert (identity["rows"], identity["dimension"]) == expected_shape == tuple(dense["embeddings_shape"])
    # 全部行已经保存，不能拿部分缓存评估。
    assert manifest["completed_rows"] == cache["rows"] == expected_shape[0]
    # 模型最大长度保持实际记录的固定值。
    assert dense["max_seq_length"] == audit.get("max_seq_length", 512)
    # 缓存输入必须是当前BEIR原始语料文件。
    assert identity["evidence_sha256"] == file_sha(data_dir / "corpus.jsonl")
    # 重建缓存实际编码的有序ID与标题加正文身份。
    ordered = hashlib.sha256()
    # 只读取当前语料，不改写原始文件。
    with (data_dir / "corpus.jsonl").open(encoding="utf-8") as stream:
        # 保留原始文档行顺序。
        for line in stream:
            # 忽略容器空行。
            if not line.strip():
                # 空行不是文档记录。
                continue
            # 正文和标题来自固定原始记录。
            record = json.loads(line)
            # 与读取器保持同一标题拼接规则。
            text = ((record.get("title") or "") + " " + record["text"]).strip()
            # 使用缓存层相同的规范JSON序列化规则。
            serialized = json.dumps([record["_id"], text], ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
            # 逐行累加有序身份。
            ordered.update(serialized.encode("utf-8"))
    # 缓存行与本轮真正使用的文本必须一致。
    assert ordered.hexdigest() == identity["ordered_id_text_sha256"]
    # 模型名、固定版本和文档编码设置逐项匹配。
    document_config = identity["document_config"]
    # 不把另一种模型的向量当作本轮结果。
    assert document_config["model_name"] == dense["model_name"] == audit["model_id"]
    # 初始化设置保留实际CUDA和固定revision。
    assert document_config["model_kwargs"] == dense["model_kwargs"]
    # 本轮预先固定模型版本与设备。
    assert dense["model_kwargs"]["revision"] == audit["model_revision"] and dense["device"] == audit["expected_device"]
    # 文档编码设置与摘要一致。
    assert document_config["encode_kwargs"] == dense["encode_kwargs"]
    # 固定规范身份计算出的目录名必须匹配。
    serialized = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    # 摘要中的缓存指纹也来自相同身份。
    assert hashlib.sha256(serialized.encode("utf-8")).hexdigest() == cache["fingerprint"] == manifest_path.parent.name
    # 向量文件必须属于同一个缓存目录。
    vectors_path = Path(cache["vectors_path"])
    # 拒绝把语料清单与另一份向量矩阵组合。
    assert vectors_path.parent == manifest_path.parent
    # 文件字节身份必须匹配发布时保存的摘要。
    assert file_sha(vectors_path) == manifest["array_sha256"]
    # 只读内存映射，禁止修改已完成向量。
    vectors = np.load(vectors_path, mmap_mode="r", allow_pickle=False)
    # 形状、精度和只读属性逐项检查。
    assert isinstance(vectors, np.memmap) and vectors.shape == expected_shape and vectors.dtype == np.float32 and not vectors.flags.writeable
    # 分块检查，避免将后续大语料的完整矩阵复制成float64。
    norm_min, norm_max = float("inf"), float("-inf")
    # 每次最多检查4096行，保持额外内存有界。
    for start in range(0, len(vectors), 4096):
        # 只复制当前块用于高精度范数检查。
        block = np.asarray(vectors[start:start + 4096], dtype=np.float64)
        # 全部向量元素必须有限。
        assert np.isfinite(block).all()
        # 计算当前块每行的L2范数。
        norms = np.linalg.norm(block, axis=1)
        # 当前块应符合已固定的归一化设置。
        assert np.allclose(norms, 1.0, rtol=1e-3, atol=1e-5)
        # 累加全矩阵的最小与最大范数。
        norm_min, norm_max = min(norm_min, float(norms.min())), max(norm_max, float(norms.max()))
    # RRF等后续运行应复用事先固定的完整缓存。
    if "expected_cache_fingerprint" in audit:
        # 指纹不变且实际cache_hit，不能悄悄重编码。
        assert cache["fingerprint"] == audit["expected_cache_fingerprint"] and cache["cache_hit"] and cache["initial_completed_rows"] == expected_shape[0]
    # 保存可复查的缓存检查结果，不输出整个矩阵。
    return {"fingerprint": cache["fingerprint"], "manifest_path": str(manifest_path), "manifest_sha256": file_sha(manifest_path), "vectors_path": str(vectors_path), "vectors_sha256": manifest["array_sha256"], "shape": list(vectors.shape), "dtype": str(vectors.dtype), "read_only": True, "status": "complete", "all_finite": True, "norm_min": norm_min, "norm_max": norm_max, "ordered_id_text_sha256": ordered.hexdigest(), "cache_hit": cache["cache_hit"], "initial_completed_rows": cache["initial_completed_rows"]}


# 用已经归档的两路排名重算RRF，独立核对实际融合而不调用原融合函数。
def validate_rrf_reference(rows, audit, config):
    # 只有RRF且已准备参考排名的运行才做此核对。
    if audit["method"] != "rrf" or not audit.get("reference_rankings"):
        # 其他方法没有RRF检查结果。
        return None
    # 读取固定的两路既有排名，不执行检索。
    references = {method: {row["query_id"]: row for line in Path(path).read_text(encoding="utf-8").splitlines() for row in [json.loads(line)]} for method, path in audit["reference_rankings"].items()}
    # 各路题号必须与当前运行一致。
    assert all(set(items) == {row["query_id"] for row in rows} for items in references.values())
    # 融合参数来自本轮实际配置和执行前回执。
    candidate_k, constant = config["rrf"]["candidate_k"], config["rrf"]["rrf_constant"]
    # 逐题比较实际融合后的顺序和分数。
    for row in rows:
        # 每题单独累加文档贡献。
        fused = {}
        # 与在线实现使用相同两路顺序。
        for method in ("dense", "bm25"):
            # 名次从1开始，不使用原检索分数。
            for rank, identifier in enumerate(references[method][row["query_id"]]["retrieved_ids"][:candidate_k], start=1):
                # 每一路出现的文档增加固定名次贡献。
                fused[identifier] = fused.get(identifier, 0.0) + 1.0 / (constant + rank)
        # 同分按ID升序，与已固定的融合排序规则一致。
        expected = sorted(fused, key=lambda identifier: (-fused[identifier], identifier))[:max(audit["ks"])]
        # 不一致时保留题号，不自动改动原始结果。
        assert expected == row["retrieved_ids"], f"RRF reference ranking mismatch: {row['query_id']}"
        # 分数也逐个核对，防止只验证排序而漏掉错误公式。
        assert all(same_number(score, fused[identifier]) for identifier, score in zip(row["retrieved_ids"], row["scores"])), row["query_id"]
    # 保存真正完成的检查范围。
    return {"query_count": len(rows), "all_rankings_and_scores_match": True, "candidate_k": candidate_k, "rrf_constant": constant, "final_k": max(audit["ks"]), "references": audit["reference_rankings"]}


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
    # 先前基线的原始产物不能被本轮对照覆盖或改写。
    for name, expected in audit.get("protected_prior_outputs", {}).items():
        # 只比较指纹，不重新运行旧基线。
        assert file_sha(name) == expected, name
    # 核对执行前源码副本，并单独记录当前工作区是否仍相同。
    current_code_matches = True
    # 历史运行以后续开发为背景，原始执行快照必须永久可核验。
    for name, expected in audit["code_sha256"].items():
        # 快照必须完整且未被改写。
        assert file_sha(Path(audit["code_snapshot"]) / name) == expected, name
        # 后续新增功能可以改变工作区，不能因此否定完整的历史快照。
        current_code_matches = current_code_matches and (ROOT / name).is_file() and file_sha(ROOT / name) == expected
    # 确认摘要声明的数据集、划分和方法与启动回执一致。
    assert (summary["dataset_name"], summary["split"], summary["retrieval_method"]) == (audit["dataset_name"], audit["split"], audit["method"])
    # 融合运行的实际参数必须与启动前固定值一致。
    if audit["method"] == "rrf":
        # 不允许运行后再更改候选预算或平滑常量。
        assert summary["config"]["rrf"] == audit["expected_rrf"]
    # 摘要的三个输入身份必须各自与运行前回执相符。
    expected_inputs = {metadata["path"]: metadata["sha256"] for metadata in audit["input_sha256"].values()}
    # 不能把其他语料或划分的结果贴到本运行名下。
    assert {metadata["path"]: metadata["sha256"] for metadata in summary["input_sha256"].values()} == expected_inputs
    # 从摘要定位原始标准BEIR文件。
    data_dir = Path(summary["config"]["data_dir"])
    # 仅Dense或RRF核对实际文档缓存，不启动任何编码。
    dense_cache = validate_dense_cache(summary, audit, data_dir) if audit["method"] in {"dense", "rrf"} else None
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
    # 融合正确性独立于效果优劣，使用已有两路排名核对。
    fusion_check = validate_rrf_reference(rows, audit, summary["config"])
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
    # 补充缓存与已有基线保护的实际检查结果。
    validation.update(dense_cache=dense_cache, protected_prior_output_count=len(audit.get("protected_prior_outputs", {})), rrf_reference_check=fusion_check, inputs_and_snapshot_match_receipt=True, current_code_matches_receipt=current_code_matches, inputs_and_snapshot_and_current_code_match_receipt=current_code_matches)
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

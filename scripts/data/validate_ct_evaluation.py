# 独立读回扩充后的题集，核对划分、引用和原实验保护。
"""Validate CT evaluation artifacts without retrieval or model inference."""

# 统计规则家族和复核状态。
from collections import Counter, defaultdict
# 记录实际校验时间，与客户端日期分开。
from datetime import datetime, timezone
# 校验文件指纹与精确重复查询。
import hashlib
# 读取草稿清单和来源引用。
import json
# 读取人工复核表。
import csv
# 根据模块位置定位项目。
from pathlib import Path
# 临时目录隔离旧验证器的报告输出。
import tempfile

# 复用已经存在的来源位置验证器，不重新提取或改写数据。
from scripts.data.validate_ct_data import validate as validate_ct_sources

# 当前文件位于scripts/data。
ROOT = Path(__file__).resolve().parents[2]


# 流式核验原文和完整向量，不将大文件加载到内存。
def sha256(path):
    # 创建本文件的摘要状态。
    digest = hashlib.sha256()
    # 按真实字节检查。
    with Path(path).open("rb") as stream:
        # 单次读取一MiB。
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            # 累加本块。
            digest.update(block)
    # 返回可保存的指纹。
    return digest.hexdigest()


# 读回小型评测文件。
def read_jsonl(path):
    # 不展示题目，只供结构验证。
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


# 本验证仅证明数据完整性，不能判定医学标签正确。
def validate(root=ROOT):
    # 固定当前项目根目录。
    root = Path(root)
    # 题集与主检索语料分目录保存。
    folder = root / "data/evaluation/ct_v3"
    # 构建清单提供待验证的内容指纹。
    manifest = json.loads((folder / "manifest.json").read_text())
    # 分别读回两个划分，不把留出正文打印出来。
    dev, holdout = read_jsonl(folder / "cases.dev.jsonl"), read_jsonl(folder / "cases.holdout.jsonl")
    # 总表只能用于结构核对。
    cases = dev + holdout
    # 新增132题另行核对，避免把继承题当作新增。
    new_cases = read_jsonl(folder / "cases.new.jsonl")
    # 原始48题必须保持字段值和次序。
    old_dev, old_holdout = read_jsonl(root / "data/v2/cases.dev.jsonl"), read_jsonl(root / "data/v2/cases.holdout.jsonl")
    # 根据题目本身计算家族划分与数量。
    families = defaultdict(set)
    # 保留独立检查结果，失败时不生成通过报告。
    checks = {}
    # 核对每个文件真实字节是否与构建清单一致。
    checks["generated_file_hashes_match"] = all(sha256(folder / name) == info["sha256"] for name, info in manifest["files"].items())
    # 来源蓝本或构建代码变化后，不能沿用旧构建收据。
    checks["blueprint_and_builder_receipts_match"] = sha256(folder / "blueprints.json") == manifest["blueprints_sha256"] and sha256(root / "scripts/data/build_ct_evaluation.py") == manifest["builder_sha256"]
    # 继承内容不能根据新实验结果倒改。
    checks["original_48_records_preserved"] = dev[:len(old_dev)] == old_dev and holdout[:len(old_holdout)] == old_holdout
    # 两份划分和总表必须完全一致。
    checks["master_and_new_files_consistent"] = cases == read_jsonl(folder / "cases.jsonl") and {case["id"] for case in new_cases} == {case["id"] for case in cases if case["id"].startswith("CT3-")}
    # 固定原始输入的真实字节。
    checks["old_inputs_unchanged"] = all(sha256(root / name) == digest for name, digest in manifest["old_inputs_sha256"].items())
    # 验证分集标签不被文件名掩盖。
    checks["split_labels_match_files"] = all(case["split"] == "dev" for case in dev) and all(case["split"] == "holdout" for case in holdout)
    # 根据全部题目收集所属划分。
    for case in cases:
        # 同一家族不能跨集。
        families[case["group"]].add(case["split"])
    # 报告真实覆盖规模，而不是只报告题目数。
    checks["family_split_and_counts"] = len(dev) == 120 and len(holdout) == 60 and len(new_cases) == 132 and len(families) == 30 and all(len(values) == 1 for values in families.values()) and set(Counter(case["group"] for case in cases).values()) == {6}
    # 按实际报告和问题查重，统一空白与大小写。
    query_keys = [" ".join((case["report"] + "\n" + case["question"]).split()).casefold() for case in cases]
    # 改写变体仍按同一家族统计，不能把精确重复计数。
    checks["unique_ids_and_exact_queries"] = len({case["id"] for case in cases}) == 180 and len(set(query_keys)) == 180
    # 读回固定CT证据，不加载全医学语料到内存。
    cards = {card["id"]: card for card in read_jsonl(root / "data/v2/evidence.jsonl")}
    # 引用索引不包含全文，但须能核对全部来源位置。
    references = json.loads((folder / "evidence_references.json").read_text())
    # 每个参考必须与已准入证据的原始字段一致。
    checks["all_reference_locations_and_text_hashes_match"] = all(key in cards and all(cards[key][name] == reference[name] for name in ("source_id", "source_type", "locator", "raw_path", "raw_sha256")) and hashlib.sha256(cards[key]["text"].encode()).hexdigest() == reference["text_sha256"] for key, reference in references.items())
    # 所有需求组必须非空，规范参考必须属于对应需求组。
    checks["gold_groups_and_canonical_references_valid"] = all(len(case["gold_evidence_ids"]) == len(case["gold_evidence_groups"]) and bool(case["gold_evidence_groups"]) and all(bool(group) and canonical in group and all(key in references for key in group) for canonical, group in zip(case["gold_evidence_ids"], case["gold_evidence_groups"])) for case in cases)
    # 重新验证HTML DOM、锚点、PDF页及字符切片，输出隔离到临时目录。
    with tempfile.TemporaryDirectory() as directory:
        # 用只读操作访问现有data，报告写到独立临时results。
        temporary_root = Path(directory)
        # 数据链接不复制大库，也不触碰历史报告。
        (temporary_root / "data").symlink_to(root / "data", target_is_directory=True)
        # 旧验证器的任何报告写入均落在临时目录。
        source_report = validate_ct_sources(temporary_root)
    # 保存这次真实复验的结果，不仅依赖旧报告。
    checks["raw_dom_pdf_and_character_positions_revalidated"] = all(source_report["checks"].values())
    # 新题的事实缺失和规则缺失必须分别驱动不同动作。
    actions = {(False, False): "answer_with_evidence_and_limits", (True, False): "clarify", (False, True): "retrieve_more_or_state_evidence_limit", (True, True): "clarify_and_retrieve_more"}
    # 只要求新题采用新增的缺证据字段，保持继承题完全原值。
    checks["fact_and_rule_gaps_remain_distinct"] = all(case["expected_action"] == actions[(bool(case["required_missing_fields"]), bool(case["required_evidence_gaps"]))] for case in new_cases)
    # 所有题目仍是待人工复核草稿。
    checks["no_clinical_or_human_review_falsely_claimed"] = all(case["annotation"]["status"] == "draft_requires_human_review" and not case["annotation"]["clinician_reviewed"] and not case["annotation"].get("independent_human_reviewed", False) for case in cases)
    # 只读开发集复核表，不导出留出题。
    with (folder / "review.dev.csv").open(encoding="utf-8-sig", newline="") as stream:
        # CSV转义由标准库处理。
        reviews = list(csv.DictReader(stream))
    # 不能将空复核表写成已审核标注。
    checks["all_dev_reviews_pending"] = len(reviews) == 120 and all(row["review_status"] == "pending" and not row["reviewer"] for row in reviews)
    # 保护之前的成绩和用户实现。
    protected = json.loads((root / "results/ct_eval_v3_input_receipt.json").read_text())["protected_sha256"]
    # 检查本轮记录的23份受保护文件。
    checks["historical_results_and_learner_code_unchanged"] = all(sha256(root / name) == digest for name, digest in protected.items())
    # 独立校验主语料字节，与题集清单一致才允许复用。
    checks["frozen_corpus_unchanged"] = sha256(root / "data/v3/evidence.jsonl") == manifest["corpus_sha256"]
    # 完整向量的身份由原Dense验证记录提供。
    dense_report = json.loads((root / "results/medical_v3_dense_ct_dev_validation.json").read_text())
    # 只核对字节，不加载模型或执行矩阵检索。
    cache_path = root / "cache/embeddings" / dense_report["cache"]["fingerprint"] / "vectors.npy"
    # 扩充题目不会使已编码正文变化。
    checks["complete_document_vectors_unchanged"] = sha256(cache_path) == dense_report["cache"]["array_sha256"]
    # 所有失败项都应显式报出，不能记录成通过。
    if not all(checks.values()):
        # 失败信息只列检查名称，不泄露留出正文。
        raise ValueError(f"Evaluation validation failed: {[key for key, value in checks.items() if not value]}")
    # 保存独立验证结果和医学边界。
    report = {"status": "passed_structural_validation_human_review_pending", "client_date": "2026-11-21", "validated_at_utc": datetime.now(timezone.utc).isoformat(), "counts": manifest["counts"], "families_by_split": dict(Counter(next(iter(values)) for values in families.values())), "checks": checks, "manifest_sha256": sha256(folder / "manifest.json"), "source_position_checks": source_report["checks"], "dev_review_status_counts": dict(Counter(row["review_status"] for row in reviews)), "reference_count": len(references), "max_query_tokens": manifest["max_query_tokens_including_prefix_and_specials"], "protected_file_count": len(protected), "complete_vector_sha256": dense_report["cache"]["array_sha256"], "human_reviewed_cases": 0, "clinician_reviewed_cases": 0, "clinical_correctness_validated": False, "formal_method_comparison_ready": False, "validation_calls_models_or_retrieval": False, "limits": ["Six variants within each family are correlated; report 30 families separately from 180 cases.", "Gold references are not exhaustive relevance judgments of all 783847 chunks.", "Existing holdout was copied and checked structurally; no question text was displayed and no retrieval was run.", "Structural validation is independent of construction; both code and medical drafts were authored by the same assistant, not an independent clinical reviewer."]}
    # 固定本次验证器实现，便于后续复核。
    report["validator_sha256"] = sha256(Path(__file__))
    # 本轮只新增报告，不覆盖旧CT、BM25或Dense实验结果。
    destination = root / "results/ct_eval_v3_validation.json"
    # 保留中文和检查明细。
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # 返回便于命令行报告的摘要。
    return report


# 独立命令用于重现结构验证，不运行检索或生成。
if __name__ == "__main__":
    # 执行所有完整性检查。
    result = validate()
    # 终端只显示聚合规模与状态。
    print(json.dumps({key: result[key] for key in ("status", "counts", "families_by_split", "reference_count", "formal_method_comparison_ready")}, ensure_ascii=False, indent=2))

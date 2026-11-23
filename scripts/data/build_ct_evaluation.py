# 从显式条件蓝本构建评测草稿，不检索、不调用模型。
"""Build source-bound CT evaluation drafts while preserving the old cases."""

# 提供可复现的数据构建命令。
import argparse
# 汇总题数、规则家族和动作覆盖。
from collections import Counter, defaultdict
# 为人工复核导出表格。
import csv
# 计算输入、来源和输出的内容指纹。
import hashlib
# 读取蓝本与保存结构化记录。
import json
# 按脚本位置确定项目根目录。
from pathlib import Path
# 对精确重复检查统一空白。
import re

# 只运行本地分词器检查长度，不加载Transformer权重。
from tokenizers import Tokenizer

# 数据工具位于scripts/data，向上两级是项目根目录。
ROOT = Path(__file__).resolve().parents[2]
# 固定与现有Dense查询配置相同的前缀。
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
# 固定已经使用的模型缓存提交。
MODEL_REVISION = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
# 使用已核实存在的本地tokenizer文件。
TOKENIZER_PATH = Path("/home/herdeny/.cache/huggingface/hub/models--BAAI--bge-small-en-v1.5/snapshots") / MODEL_REVISION / "tokenizer.json"
# 这些文件由构建器管理，人工复核变更必须先保护。
OUTPUT_NAMES = ("cases.dev.jsonl", "cases.holdout.jsonl", "cases.jsonl", "cases.new.jsonl", "evidence_sets.resolved.json", "evidence_references.json", "sources.json", "splits.json", "review.dev.csv")


# 流式计算文件SHA，避免将整个医学主库复制到内存。
def file_sha256(path):
    # 初始化当前文件的摘要。
    digest = hashlib.sha256()
    # 使用二进制读取真实字节。
    with Path(path).open("rb") as stream:
        # 一次读取一MiB。
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            # 将当前块加入摘要。
            digest.update(block)
    # 返回十六进制指纹。
    return digest.hexdigest()


# 读取小型JSONL输入，只用于CT子集与评测题。
def read_jsonl(path):
    # 按UTF-8读取原始记录。
    with Path(path).open(encoding="utf-8") as stream:
        # 跳过空行并保持原有顺序。
        return [json.loads(line) for line in stream if line.strip()]


# 保存可回查的小型JSON记录。
def write_json(path, value):
    # 创建所需目录。
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    # 保留中文并格式化，方便人工检查。
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# 保存兼容现有pandas读取接口的逐行JSON。
def write_jsonl(path, rows):
    # 每条题目独占一行。
    with Path(path).open("w", encoding="utf-8") as stream:
        # 保持输入记录和字段的原始值。
        for row in rows:
            # 序列化不会修改调用者字典。
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")


# 防止重建时覆盖已经填写的复核意见或手工修订。
def guard_existing_output(output_dir):
    # 以旧清单中的字节指纹判断文件是否已被人工改变。
    manifest_path = output_dir / "manifest.json"
    # 新输出目录不需要已有清单。
    if not manifest_path.exists():
        # 存在同名文件却没有清单时，无法确认可以安全重建。
        if any((output_dir / name).exists() for name in OUTPUT_NAMES):
            # 要求改用新目录，保留现有内容。
            raise ValueError("Existing evaluation files have no manifest; use a new output directory")
        # 空目录或只有蓝本等辅助文件可继续。
        return
    # 读取上一次构建的指纹。
    previous = json.loads(manifest_path.read_text(encoding="utf-8"))
    # 检查已有生成文件，尤其是人工复核表。
    for name in OUTPUT_NAMES:
        # 只处理目前仍存在的文件，缺失文件可从蓝本重建。
        path = output_dir / name
        # 清单缺项或内容变化时不能覆盖。
        if path.exists() and (name not in previous["files"] or file_sha256(path) != previous["files"][name]["sha256"]):
            # 仅报告文件名，不输出留出正文或复核内容。
            raise ValueError(f"Modified evaluation output: {name}; use a new output directory")


# 将具名证据需求解析成确定的可替代ID集合。
def resolve_evidence_sets(spec, cards):
    # 保存每个需求集合的实际ID。
    resolved = {}
    # 按蓝本定义顺序解析，规范ID由集合第一项给出。
    for name, selection in spec["evidence_sets"].items():
        # ACR Variant行都完整重复适用条件，可按已核对前缀选取。
        if isinstance(selection, dict):
            # 只在固定来源中使用明确文字前缀，不做模型相关性检索。
            identifiers = [key for key, card in cards.items() if card["source_id"] == selection["source_id"] and card["text"].startswith(selection["text_startswith"])]
            # 数量变化表示源结构或选择条件改变，不能静默沿用标签。
            if len(identifiers) != selection["expected_count"]:
                # 保留具体证据集合名称。
                raise ValueError(f"Evidence selection changed: {name}")
        # 其他集合使用逐项回查过的显式ID。
        else:
            # 复制列表，避免改变蓝本对象。
            identifiers = list(selection)
        # 每个需求至少有一个候选，且不能重复计数。
        if not identifiers or len(identifiers) != len(set(identifiers)):
            # 输入错误必须在生成题目之前暴露。
            raise ValueError(f"Empty or repeated evidence IDs: {name}")
        # 所有ID必须来自已准入CT证据，不能使用隔离条目。
        if any(identifier not in cards for identifier in identifiers):
            # 不把未入库的指南或表格伪装为已有证据。
            raise ValueError(f"Unknown or quarantined evidence: {name}")
        # 保存实际可替代集合。
        resolved[name] = identifiers
    # 返回固定、可审阅的需求组。
    return resolved


# 从显式条件蓝本创建新增草稿，不读取旧题文本来改写。
def make_new_cases(spec, evidence_sets, cards, sources, base_splits):
    # 收集新增题目，ID顺序由蓝本固定。
    rows = []
    # 遍历预先指定划分的规则家族。
    for family in spec["families"]:
        # 保留已有家族的开发／留出边界。
        if family["group"] in base_splits and family["split"] != base_splits[family["group"]]:
            # 不允许把已开发规则挪成未见留出。
            raise ValueError(f"Existing family split changed: {family['group']}")
        # 同一家族内的变体必须具有不同标识。
        variants = set()
        # 展开逐条明确编写的条件变体，不以模型批量改写充数。
        for item in family["cases"]:
            # 四个必需字段由蓝本明确给出。
            variant, report, question, expected = item[:4]
            # 可选项只覆盖本题实际不同的条件。
            options = item[4] if len(item) == 5 else {}
            # 不接受多余列或重复变体。
            if len(item) not in (4, 5) or variant in variants:
                # 出错时报告规则家族。
                raise ValueError(f"Invalid case blueprint: {family['group']}")
            # 记录已使用的变体名。
            variants.add(variant)
            # 每题引用实际需要的证据需求组。
            group_names = options.get("evidence_groups", family["evidence_groups"])
            # 保存允许替代的来源ID，不按检索得分决定gold。
            groups = [list(evidence_sets[name]) for name in group_names]
            # 规范参考从每个需求组取一项，旧评分仍可使用。
            canonical = [group[0] for group in groups]
            # 事实缺失与证据缺失分开标注。
            missing = list(options.get("missing", []))
            # 未入库的具体表格不能伪装成病人缺失字段。
            evidence_gaps = list(options.get("evidence_gaps", []))
            # 同时缺事实和规则时分别保留两个补全动作。
            if missing and evidence_gaps:
                # 后续Agent可分别追问事实与补查证据。
                action = "clarify_and_retrieve_more"
            # 只缺病例事实时应提出具体澄清。
            elif missing:
                # 保持与现有题目动作名兼容。
                action = "clarify"
            # 只缺规则时说明支持边界或定向补查。
            elif evidence_gaps:
                # 不向医生追问本应由检索取得的规则。
                action = "retrieve_more_or_state_evidence_limit"
            # 已有证据可以支持本题范围内的判断。
            else:
                # 与旧数据的回答动作名保持一致。
                action = "answer_with_evidence_and_limits"
            # 记录全部允许替代证据的来源，而不只记录规范参考。
            source_ids = sorted({cards[key]["source_id"] for group in groups for key in group})
            # 为新增题分配与旧CT2不冲突的稳定ID。
            case_id = f"CT3-{len(rows) + 1:03d}"
            # 所有参考标注都留在评测侧，查询仍只包含报告和问题。
            row = {"id": case_id, "split": family["split"], "group": family["group"], "pair_id": family["group"], "variant": variant, "task": family["task"], "report": report, "question": question, "expected_behavior": expected, "required_missing_fields": missing, "required_evidence_gaps": evidence_gaps, "expected_action": action, "gold_evidence_ids": canonical, "gold_evidence_groups": groups, "gold_source_ids": source_ids, "forbidden_claims": family.get("forbidden_claims", [])}
            # 如实标记这是生成作者回查过来源的草稿，尚非独立人工或医生标注。
            row["annotation"] = {"origin": "assistant_generated_synthetic", "status": "draft_requires_human_review", "clinician_reviewed": False, "independent_human_reviewed": False, "created_at": spec["authored_at_client_date"], "grounding": "Drafting assistant checked the cited frozen source clauses; no independent human or clinical review.", "source_snapshot_sha256": {key: sources[key]["snapshot_sha256"] for key in source_ids}, "evidence_set_names": group_names, "retrieval_scores_used": False, "model_answers_used": False}
            # 保存完整新增记录。
            rows.append(row)
    # 返回新增题，不改写继承的原题。
    return rows


# 构建可复核但尚未批准正式评测的新题集。
def build(output_dir=None, root=ROOT, tokenizer_path=TOKENIZER_PATH):
    # 允许测试使用隔离项目根目录。
    root = Path(root)
    # 固定默认输出到独立评测版本，而不是覆盖语料目录。
    output_dir = Path(output_dir) if output_dir else root / "data/evaluation/ct_v3"
    # 任何重建都先保护已有人工修改。
    guard_existing_output(output_dir)
    # 读取助手显式编写、仍待独立人工复核的条件蓝本。
    blueprint_path = root / "data/evaluation/ct_v3/blueprints.json"
    # 蓝本是数据输入，不执行任意Python。
    spec = json.loads(blueprint_path.read_text())
    # 读取6份已存在的来源身份。
    sources = {source["id"]: source for source in json.loads((root / "data/v2/sources.json").read_text())}
    # 来源集合必须与标注时固定的身份相同。
    if {key: value["snapshot_sha256"] for key, value in sources.items()} != spec["source_snapshot_sha256"]:
        # 不能把新网页的相同块号当作旧证据。
        raise ValueError("Source snapshot identities changed")
    # 核对每份本地原始快照，不重新下载或替换。
    for source in sources.values():
        # 真实字节必须等于标签所依据的原始版本。
        if file_sha256(root / source["snapshot_path"]) != source["snapshot_sha256"]:
            # 保留需要重新回查的来源。
            raise ValueError(f"Raw source changed: {source['id']}")
    # 保存原输入文件指纹以验证构建不改动旧数据。
    protected_paths = ["data/v2/evidence.jsonl", "data/v2/sources.json", "data/v2/splits.json", "data/v2/cases.dev.jsonl", "data/v2/cases.holdout.jsonl", "data/v3/cases.ct.dev.jsonl"]
    # 读取前保存实际原始字节指纹。
    protected = {name: file_sha256(root / name) for name in protected_paths}
    # CT子集仅238条，可以直接读取进行标注检查。
    ct_rows = read_jsonl(root / "data/v2/evidence.jsonl")
    # 建立ID索引，保留原始行序。
    cards = {card["id"]: card for card in ct_rows}
    # 任何重复ID都属于输入损坏。
    if len(cards) != len(ct_rows):
        # 防止字典覆盖掩盖重复来源。
        raise ValueError("Duplicate CT evidence IDs")
    # 验证主库仍是冻结输入，正文向量无需重建。
    corpus = json.loads((root / "data/v3/corpus_manifest.json").read_text())
    # 只流式校验，不将783847条再读入DataFrame。
    corpus_sha = file_sha256(root / "data/v3/evidence.jsonl")
    # 主库变化意味着后续方法比较需要新的语料版本。
    if corpus_sha != corpus["files"]["evidence.jsonl"]["sha256"]:
        # 不让评测扩题悄悄更换检索语料。
        raise ValueError("Frozen medical corpus changed")
    # 主库保留的CT前缀必须与原CT证据完全一致。
    with (root / "data/v3/evidence.jsonl").open(encoding="utf-8") as stream:
        # 只核对已经保留的CT前缀，不加载其他医学文档。
        for card in ct_rows:
            # 对比所有原始字段，而不只核对ID。
            if json.loads(next(stream)) != card:
                # 同一证据号不能指向被修改的文本。
                raise ValueError(f"Retained CT evidence changed: {card['id']}")
    # 只用旧划分元数据来保留家族边界。
    split_metadata = json.loads((root / "data/v2/splits.json").read_text())
    # 不以旧留出题内容设计新题。
    base_splits = {family["group"]: family["split"] for family in split_metadata["families"]}
    # 解析所有明确回查过的参考证据集合。
    evidence_sets = resolve_evidence_sets(spec, cards)
    # 先从独立蓝本生成新增题，再复制旧题。
    new_cases = make_new_cases(spec, evidence_sets, cards, sources, base_splits)
    # 旧开发题按原始记录保留。
    base_dev = read_jsonl(root / "data/v2/cases.dev.jsonl")
    # 旧留出仅复制与结构验证，不作为改写或调参输入。
    base_holdout = read_jsonl(root / "data/v2/cases.holdout.jsonl")
    # 两个划分分别组合，保持原始继承部分完整。
    dev = base_dev + [case for case in new_cases if case["split"] == "dev"]
    # 留出文件单独保存，不导出到默认人工开发复核表。
    holdout = base_holdout + [case for case in new_cases if case["split"] == "holdout"]
    # 完整列表用于机器结构验证，不运行检索。
    cases = dev + holdout
    # 题号必须全局唯一。
    if len({case["id"] for case in cases}) != len(cases):
        # 不允许新版本覆盖已有题号。
        raise ValueError("Duplicate case IDs")
    # 精确重复仅按报告与问题组合判断，不把文本改写当独立家族。
    query_hashes = set()
    # 为每个家族记录唯一所属划分。
    family_splits = defaultdict(set)
    # 只加载固定tokenizer，始终关闭截断与填充。
    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    # 长输入不能通过自动截断假装合格。
    tokenizer.no_truncation()
    # 去掉可能的固定长度填充，计数只反映真实输入。
    tokenizer.no_padding()
    # 保存实际查询长度。
    query_token_counts = {}
    # 验证全部记录，不读取模型输出或检索得分。
    for case in cases:
        # 按家族记录划分。
        family_splits[case["group"]].add(case["split"])
        # 归一化空白，只用于完全重复检查。
        normalized_query = re.sub(r"\s+", " ", case["report"] + "\n" + case["question"]).strip().casefold()
        # 重复问答输入会不必要地放大题数。
        query_digest = hashlib.sha256(normalized_query.encode()).hexdigest()
        # 既有与新增之间也检查完全重复。
        if query_digest in query_hashes:
            # 不输出留出正文，只报告题号。
            raise ValueError(f"Exact duplicate query: {case['id']}")
        # 保存已经见过的输入指纹。
        query_hashes.add(query_digest)
        # 参考证据组必须非空且全部能回查。
        if not case["gold_evidence_groups"] or any(not group or any(key not in cards for key in group) for group in case["gold_evidence_groups"]):
            # 不把隔离条款放进gold。
            raise ValueError(f"Invalid evidence group: {case['id']}")
        # 规范参考必须是对应需求组中的一项。
        if len(case["gold_evidence_ids"]) != len(case["gold_evidence_groups"]) or any(key not in group for key, group in zip(case["gold_evidence_ids"], case["gold_evidence_groups"])):
            # 评分的两个口径应保持可解释对应。
            raise ValueError(f"Canonical/group mismatch: {case['id']}")
        # 跟随现有封装的换行预处理，再加查询前缀和特殊token。
        query = QUERY_PREFIX + f"Report: {case['report']}\nQuestion: {case['question']}".replace("\n", " ")
        # 只计算查询输入，不把gold或预期行为编码。
        query_token_counts[case["id"]] = len(tokenizer.encode(query, add_special_tokens=True).ids)
    # 每个规则家族只能属于一个划分。
    if any(len(values) != 1 for values in family_splits.values()):
        # 条件变体不能跨开发与留出。
        raise ValueError("Family leakage across splits")
    # 记录真实题数和新增数。
    counts = {"dev": len(dev), "holdout": len(holdout), "families": len(family_splits), "new_dev": sum(case["split"] == "dev" for case in new_cases), "new_holdout": sum(case["split"] == "holdout" for case in new_cases)}
    # 与已经声明的建设预算核对，避免静默漏题。
    if counts != spec["expected_counts"]:
        # 真实数量不合格时不发布数据文件。
        raise ValueError(f"Unexpected counts: {counts}")
    # 不允许超过当前模型的查询长度上限。
    if max(query_token_counts.values()) > 512:
        # 不开启静默截断，也不自动删除报告事实。
        raise ValueError("A query exceeds the model input limit")
    # 每个家族的实际题数单独报告，不能用180当180个独立场景。
    family_counts = Counter(case["group"] for case in cases)
    # 本批每个家族是六个条件变体。
    if set(family_counts.values()) != {6}:
        # 家族缺题或重复需要回查蓝本。
        raise ValueError("Unexpected number of variants per family")
    # 创建独立输出版本目录。
    output_dir.mkdir(parents=True, exist_ok=True)
    # 保存开发集，不覆盖旧32题。
    write_jsonl(output_dir / "cases.dev.jsonl", dev)
    # 保存独立留出，不混入开发集。
    write_jsonl(output_dir / "cases.holdout.jsonl", holdout)
    # 总表仅用于审计，不作为调参输入。
    write_jsonl(output_dir / "cases.jsonl", cases)
    # 保存新增题本身，清楚区分新增132与总题数180。
    write_jsonl(output_dir / "cases.new.jsonl", new_cases)
    # 建立最小可回查证据索引，不重复打包原文全文。
    all_evidence_ids = sorted({key for case in cases for group in case["gold_evidence_groups"] for key in group})
    # 保留每条参考的原文身份和位置。
    references = {key: {name: cards[key][name] for name in ("source_id", "source_type", "locator", "raw_path", "raw_sha256")} for key in all_evidence_ids}
    # 每条参考再记录正文指纹以防同号换文。
    for key in references:
        # 引用定位与正文身份共同保存。
        references[key]["text_sha256"] = hashlib.sha256(cards[key]["text"].encode()).hexdigest()
    # 保存可替代集合解析结果，方便人工检查是否真可替代。
    write_json(output_dir / "evidence_sets.resolved.json", evidence_sets)
    # 保存去重后的引用索引。
    write_json(output_dir / "evidence_references.json", references)
    # 来源清单保留原始版本，不把本次核验日期充当发布日期。
    write_json(output_dir / "sources.json", list(sources.values()))
    # 只为开发集导出人工复核表，留出保持独立。
    with (output_dir / "review.dev.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        # 复核结果与原始草稿分开，避免直接覆盖标签。
        fields = ["case_id", "group", "origin", "report", "question", "expected_behavior", "required_missing_fields", "required_evidence_gaps", "gold_evidence_groups", "source_references", "review_status", "reviewer", "review_notes"]
        # 使用标准CSV写入，避免逗号与换行破坏列。
        writer = csv.DictWriter(stream, fieldnames=fields)
        # 输出固定表头。
        writer.writeheader()
        # 只输出开发题的复核材料。
        for case in dev:
            # 为每个规范参考保留标题和精确位置。
            source_refs = [{"evidence_id": key, "publisher": sources[cards[key]["source_id"]]["publisher"], "title": sources[cards[key]["source_id"]]["title"], "locator": cards[key]["locator"]} for key in case["gold_evidence_ids"]]
            # 真实人工复核字段为空，不能默认通过。
            writer.writerow({"case_id": case["id"], "group": case["group"], "origin": "inherited_CT2" if case["id"].startswith("CT2-") else "new_CT3", "report": case["report"], "question": case["question"], "expected_behavior": case["expected_behavior"], "required_missing_fields": json.dumps(case["required_missing_fields"], ensure_ascii=False), "required_evidence_gaps": json.dumps(case.get("required_evidence_gaps", []), ensure_ascii=False), "gold_evidence_groups": json.dumps(case["gold_evidence_groups"], ensure_ascii=False), "source_references": json.dumps(source_refs, ensure_ascii=False), "review_status": "pending", "reviewer": "", "review_notes": ""})
    # 所有旧输入在构建后必须保持原字节。
    if any(file_sha256(root / name) != digest for name, digest in protected.items()):
        # 不允许扩题隐式改写已有成绩的输入。
        raise ValueError("A protected input changed")
    # 记录每个家族的真实划分和变体数量，不输出留出题正文。
    families = [{"group": group, "split": next(iter(family_splits[group])), "case_count": family_counts[group], "new": group not in base_splits} for group in family_counts]
    # 保存预先划分元数据。
    write_json(output_dir / "splits.json", {"method": "rule_family_assigned_before_new_retrieval_runs", "families": families})
    # 统计生成文件的内容身份。
    output_names = OUTPUT_NAMES
    # 只有结构校验完成，不伪装成医学标签已经独立复核。
    manifest = {"evaluation_version": spec["evaluation_version"], "client_date": spec["authored_at_client_date"], "status": "draft_built_structural_validation_pending", "counts": counts, "inherited_cases": len(base_dev) + len(base_holdout), "new_cases": len(new_cases), "families_by_split": dict(Counter(family["split"] for family in families)), "cases_per_family": 6, "task_counts": dict(Counter(case["task"] for case in cases)), "action_counts": dict(Counter(case["expected_action"] for case in cases)), "max_query_tokens_including_prefix_and_specials": max(query_token_counts.values()), "query_token_counts": query_token_counts, "tokenizer_revision": MODEL_REVISION, "tokenizer_sha256": file_sha256(tokenizer_path), "corpus_sha256": corpus_sha, "corpus_changed": False, "document_embeddings_recomputed": False, "old_inputs_sha256": protected, "blueprints_sha256": file_sha256(blueprint_path), "source_snapshot_sha256": spec["source_snapshot_sha256"], "files": {name: {"sha256": file_sha256(output_dir / name), "bytes": (output_dir / name).stat().st_size} for name in output_names}, "builder_sha256": file_sha256(Path(__file__)), "independent_human_reviewed_cases": 0, "clinician_reviewed_cases": 0, "existing_holdout_access": "copied and structurally validated; not used for question authoring, retrieval or parameter tuning; no question text displayed", "reference_exhaustiveness": "selected source-grounded references; not an exhaustive relevance judgment of 783847 chunks", "retrieval_or_model_answers_used": False, "ready_for_formal_comparison": False}
    # 保存草稿状态及全部输入输出指纹。
    write_json(output_dir / "manifest.json", manifest)
    # 返回聚合元数据，不向终端打印留出题。
    return manifest


# 命令行仅构建数据草稿，不运行系统评测。
if __name__ == "__main__":
    # 创建可复现的构建入口。
    parser = argparse.ArgumentParser(description="Build source-bound CT evaluation drafts without model inference")
    # 允许输出至新的目录进行重建比对。
    parser.add_argument("--output", type=Path)
    # 分词器使用已存在的固定本地文件。
    parser.add_argument("--tokenizer", type=Path, default=TOKENIZER_PATH)
    # 解析数据准备参数。
    args = parser.parse_args()
    # 执行离线构建。
    result = build(args.output, tokenizer_path=args.tokenizer)
    # 只报告真实数量和审核状态。
    print(json.dumps({key: result[key] for key in ("status", "counts", "inherited_cases", "new_cases", "max_query_tokens_including_prefix_and_specials", "ready_for_formal_comparison")}, ensure_ascii=False, indent=2))

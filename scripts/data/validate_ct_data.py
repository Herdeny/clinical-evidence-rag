# 下面的文档字符串说明本模块、类或函数的用途和适用边界。
"""Check provenance and split integrity, without calling a model or retrieval code."""

# 从 collections 中的指定接口导入 Counter。
from collections import Counter
# 导入JSON 编解码工具。
import json
# 导入路径对象 Path，便于定位脚本、组合目录并读写文件。
from pathlib import Path

# 从 bs4 中的指定接口导入 BeautifulSoup。
from bs4 import BeautifulSoup
# 从 pypdf 中的指定接口导入 PdfReader。
from pypdf import PdfReader

# 从 数据准备包中的公共工具导入 ROOT、BUILD_DATE、clean、digest、write_json。
from scripts.data.ct_data_pipeline import ROOT, BUILD_DATE, clean, digest, write_json


# 定义 load_lines：读取非空 JSONL 行并解析为记录列表。
def load_lines(path):
    # 返回按遍历顺序筛选并整理 path.read_text(encoding='utf-8').splitlines() 中的数据，结束本次函数调用。
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


# 定义 validate：独立核对数据来源、位置、长度和划分；不验证医学正确性或运行生成模型。
def validate(root=ROOT):
    # 设置root：创建文件路径对象，便于跨目录组合与读写。
    root = Path(root)
    # 设置cards：读取非空 JSONL 行并解析为记录列表。
    cards = load_lines(root / "data/v2/evidence.jsonl")
    # 设置candidates：读取非空 JSONL 行并解析为记录列表。
    candidates = load_lines(root / "data/v2/evidence_candidates.jsonl")
    # 设置题目列表：读取非空 JSONL 行并解析为记录列表。
    cases = load_lines(root / "data/v2/cases.jsonl")
    # 设置inventory：解析 JSON 文本或字节，恢复为 Python 对象。
    inventory = json.loads((root / "data/v2/sources.json").read_text())
    # 设置来源清单：按遍历顺序筛选并整理 inventory 中的数据。
    sources = {s["id"]: s for s in inventory}
    # 设置card_map：按遍历顺序筛选并整理 cards 中的数据。
    card_map = {card["id"]: card for card in cards}
    # 当 len(card_map) != len(cards) 成立时，执行下面的分支。
    if len(card_map) != len(cards):
        # 抛出 AssertionError 并停止当前操作：Duplicate evidence IDs。
        raise AssertionError("Duplicate evidence IDs")
    # 当 len({(c['source_id'], clean(c['text'])) for c in cards}) != len(cards) 成立时，执行下面的分支。
    if len({(c["source_id"], clean(c["text"])) for c in cards}) != len(cards):
        # 抛出 AssertionError 并停止当前操作：Exact normalized duplicate evidence。
        raise AssertionError("Exact normalized duplicate evidence")

    # 设置(documents, soups)：元组。
    documents, soups = {}, {}
    # 设置verified_blocks：常量 0。
    verified_blocks = 0
    # 按顺序遍历inventory，本轮元素记作 source。
    for source in inventory:
        # 设置原始字节内容：将目录与右侧子路径组合，得到完整输出位置。
        raw = root / source["snapshot_path"]
        # 校验 digest(raw.read_bytes()) == source['snapshot_sha256']；不满足时抛出 AssertionError，使核验失败。
        assert digest(raw.read_bytes()) == source["snapshot_sha256"], source["id"]
        # 当 raw.suffix != '.html' 成立时，执行下面的分支。
        if raw.suffix != ".html":
            # 跳过当前项，继续检查本层循环中的下一项。
            continue
        # 设置soup：将原始 HTML 解析为可查找的 DOM 树。
        soup = BeautifulSoup(raw.read_bytes(), "lxml")
        # 设置soups[source['id']]：soup。
        soups[source["id"]] = soup
        # 设置doc：解析 JSON 文本或字节，恢复为 Python 对象。
        doc = json.loads((root / f"data/v2/parsed/documents/{source['id']}.json").read_text())
        # 校验 doc['raw_sha256'] == source['snapshot_sha256']；不满足时抛出 AssertionError，使核验失败。
        assert doc["raw_sha256"] == source["snapshot_sha256"]
        # 设置documents[source['id']]：按遍历顺序筛选并整理 doc['blocks'] 中的数据。
        documents[source["id"]] = {b["id"]: b for b in doc["blocks"]}
        # 按顺序遍历doc['blocks']，本轮元素记作 block。
        for block in doc["blocks"]:
            # 设置loc：按键或位置读取 当前正文块 中的对应内容。
            loc = block["locator"]
            # 设置node：按键或位置读取 soup.find_all(loc['selector']) 中的对应内容。
            node = soup.find_all(loc["selector"])[loc["element_index"]]
            # 当 loc['selector'] == 'tr' 成立时，执行下面的分支。
            if loc["selector"] == "tr":
                # 设置raw_cells：按遍历顺序筛选并整理 node.find_all(['td', 'th'], recursive=False) 中的数据。
                raw_cells = [clean(cell.get_text(" ", strip=True)) for cell in node.find_all(["td", "th"], recursive=False)]
                # 校验 raw_cells == loc['table_cells']；不满足时抛出 AssertionError，使核验失败。
                assert raw_cells == loc["table_cells"], block["id"]
                # 设置headers：按键读取字段，缺失时使用指定默认值或 None。
                headers = loc.get("table_headers", ["Procedure", "Appropriateness", "Relative radiation level"])
                # 设置reconstructed：用指定分隔符连接各段文字。
                reconstructed = "\n".join(f"{heading}: {cell}" for heading, cell in zip(headers, raw_cells))
            # 前面的条件都不满足时，执行这一分支。
            else:
                # 设置reconstructed：只合并空白字符，保留医学数字、单位、否定词和符号。
                reconstructed = clean(node.get_text(" ", strip=True))
            # 校验 block['text'] == reconstructed；不满足时抛出 AssertionError，使核验失败。
            assert block["text"] == reconstructed, (source["id"], block["id"])
            # 当 loc['anchor'] 成立时，执行下面的分支。
            if loc["anchor"]:
                # 校验 soup.find(id=loc['anchor']) is not None；不满足时抛出 AssertionError，使核验失败。
                assert soup.find(id=loc["anchor"]) is not None, loc["anchor"]
            # 更新verified_blocks，累计本轮处理量或内容。
            verified_blocks += 1

    # 设置pages_path：将目录与右侧子路径组合，得到完整输出位置。
    pages_path = root / "data/v2/parsed/acr-lungrads-2022.pages.json"
    # 设置pages：解析 JSON 文本或字节，恢复为 Python 对象。
    pages = json.loads(pages_path.read_text())
    # 设置reader：打开本地 PDF，供逐页文本一致性检查。
    reader = PdfReader(root / "data/v2/raw/acr-lungrads-2022.pdf")
    # 校验 all((record['text'] == reader.pages[record['page'] - 1].extract_text() for record in pages))；不满足时抛出 AssertionError，使核验失败。
    assert all(record["text"] == reader.pages[record["page"] - 1].extract_text() for record in pages)
    # 按顺序遍历candidates，本轮元素记作 card。
    for card in candidates:
        # 校验 card['source_id'] in sources；不满足时抛出 AssertionError，使核验失败。
        assert card["source_id"] in sources
        # 设置当前来源：按键或位置读取 来源清单 中的对应内容。
        source = sources[card["source_id"]]
        # 校验 card['raw_sha256'] == source['snapshot_sha256']；不满足时抛出 AssertionError，使核验失败。
        assert card["raw_sha256"] == source["snapshot_sha256"]
        # 校验 card['source_type'] == source['source_type']；不满足时抛出 AssertionError，使核验失败。
        assert card["source_type"] == source["source_type"]
        # 设置loc：按键或位置读取 card 中的对应内容。
        loc = card["locator"]
        # 当 loc['type'] == 'pdf_note' 成立时，执行下面的分支。
        if loc["type"] == "pdf_note":
            # 设置page_text：按键或位置读取 pages[loc['page'] - 1] 中的对应内容。
            page_text = pages[loc["page"] - 1]["text"]
            # 校验 page_text[loc['char_start']:loc['char_end']] == card['text']；不满足时抛出 AssertionError，使核验失败。
            assert page_text[loc["char_start"]:loc["char_end"]] == card["text"]
        # 前面的条件都不满足时，执行这一分支。
        else:
            # 设置原始正文块：按键或位置读取 documents 中的对应内容。
            blocks = documents[card["source_id"]]
            # 设置pieces：按遍历顺序筛选并整理 loc['parts'] 中的数据。
            pieces = [blocks[p["block_id"]]["text"][p["char_start"]:p["char_end"]] for p in loc["parts"]]
            # 校验 card['text'] == '\n\n'.join(pieces)；不满足时抛出 AssertionError，使核验失败。
            assert card["text"] == "\n\n".join(pieces), card["id"]
            # 校验 all((key in blocks for key in loc['context_block_ids']))；不满足时抛出 AssertionError，使核验失败。
            assert all(key in blocks for key in loc["context_block_ids"])
        # 当 card['retrieval_ready'] 成立时，执行下面的分支。
        if card["retrieval_ready"]:
            # 校验 card['embedding_token_count'] <= 512；不满足时抛出 AssertionError，使核验失败。
            assert card["embedding_token_count"] <= 512
        # 校验 'PUBMED Abstract' not in card['text']；不满足时抛出 AssertionError，使核验失败。
        assert "PUBMED Abstract" not in card["text"]
        # 校验 card['review_status'] == 'source_span_verified_not_clinician_reviewed'；不满足时抛出 AssertionError，使核验失败。
        assert card["review_status"] == "source_span_verified_not_clinician_reviewed"
    # 校验 len(cards) == sum((c['retrieval_ready'] for c in candidates))；不满足时抛出 AssertionError，使核验失败。
    assert len(cards) == sum(c["retrieval_ready"] for c in candidates)

    # 设置(group_splits, inputs)：元组。
    group_splits, inputs = {}, set()
    # 按顺序遍历题目列表，本轮元素记作 case。
    for case in cases:
        # 将 HTML 节点保存为带章节、锚点和原元素位置的正文块。
        group_splits.setdefault(case["group"], set()).add(case["split"])
        # 设置key：元组。
        key = (case["report"], case["question"])
        # 校验 key not in inputs；不满足时抛出 AssertionError，使核验失败。
        assert key not in inputs, case["id"]
        # 将 HTML 节点保存为带章节、锚点和原元素位置的正文块。
        inputs.add(key)
        # 校验 case['gold_evidence_ids'] == [g[0] for g in case['gold_evidence_groups']]；不满足时抛出 AssertionError，使核验失败。
        assert case["gold_evidence_ids"] == [g[0] for g in case["gold_evidence_groups"]]
        # 校验 all((group and all((key in card_map for key in group)) for group in case['gold_evidence_groups']))；不满足时抛出 AssertionError，使核验失败。
        assert all(group and all(key in card_map for key in group) for group in case["gold_evidence_groups"])
        # 校验 not case['annotation']['clinician_reviewed']；不满足时抛出 AssertionError，使核验失败。
        assert not case["annotation"]["clinician_reviewed"]
        # 校验 not case['annotation']['model_answers_used']；不满足时抛出 AssertionError，使核验失败。
        assert not case["annotation"]["model_answers_used"]
        # 校验 not case['annotation']['retrieval_scores_used']；不满足时抛出 AssertionError，使核验失败。
        assert not case["annotation"]["retrieval_scores_used"]
        # 按顺序遍历case['annotation']['source_snapshot_sha256'].items()，本轮元素记作 (source_id, fingerprint)。
        for source_id, fingerprint in case["annotation"]["source_snapshot_sha256"].items():
            # 校验 fingerprint == sources[source_id]['snapshot_sha256']；不满足时抛出 AssertionError，使核验失败。
            assert fingerprint == sources[source_id]["snapshot_sha256"]
    # 校验 all((len(splits) == 1 for splits in group_splits.values()))；不满足时抛出 AssertionError，使核验失败。
    assert all(len(splits) == 1 for splits in group_splits.values()), "Scenario-family split leakage"
    # 按顺序遍历('dev', 'holdout')，本轮元素记作 split。
    for split in ("dev", "holdout"):
        # 设置actual：读取非空 JSONL 行并解析为记录列表。
        actual = load_lines(root / f"data/v2/cases.{split}.jsonl")
        # 校验 actual == [case for case in cases if case['split'] == split]；不满足时抛出 AssertionError，使核验失败。
        assert actual == [case for case in cases if case["split"] == split]

    # 设置files：列表。
    files = ["evidence.jsonl", "evidence_candidates.jsonl", "evidence_nci_text.jsonl", "sources.json", "cases.jsonl",
             # 继续组装上方容器中的本行元素，保持其原始顺序和取值。
             "cases.dev.jsonl", "cases.holdout.jsonl", "splits.json", "exclusions.json"]
    # 设置report：字典，保存validated_at、dataset_version、implementation_owner、source_files、canonical_html_blocks_checked_against_dom等信息。
    report = {
        # 写入字段 validated_at（本份数据检查记录所用的日期）；字段 dataset_version（数据集版本标签）；字段 implementation_owner（代码实现者及授权范围的记录）。
        "validated_at": BUILD_DATE, "dataset_version": "ct-v2.0-draft", "implementation_owner": "assistant_at_user_request",
        # 写入字段 source_files（取得的原始来源文件数量）；字段 canonical_html_blocks_checked_against_dom（已经与原始DOM逐一核对的正文块数量）。
        "source_files": len(sources), "canonical_html_blocks_checked_against_dom": verified_blocks,
        # 写入字段 candidate_evidence（原始候选证据数量）；字段 index_input_evidence（真正准入索引的证据条数）。
        "candidate_evidence": len(candidates), "index_input_evidence": len(cards),
        # 写入字段 quarantined_evidence（被隔离而未进入检索的证据数量）。
        "quarantined_evidence": len(candidates) - len(cards),
        # 写入字段 nci_attributed_text_subset（当前记录中名为 nci_attributed_text_subset 的来源信息或统计值）。
        "nci_attributed_text_subset": len(load_lines(root / "data/v2/evidence_nci_text.jsonl")),
        # 写入字段 case_count（题目总数）；字段 scenario_families（合成题所属的不同场景家族数）。
        "case_count": len(cases), "scenario_families": len(group_splits),
        # 写入字段 case_splits（各题目划分的数量统计）。
        "case_splits": dict(Counter(case["split"] for case in cases)),
        # 写入字段 family_splits（各划分包含的场景家族数量）。
        "family_splits": dict(Counter(next(iter(v)) for v in group_splits.values())),
        # 写入字段 checks（各项完整性检查的结果）；字段 all_source_fingerprints_match（来源文件指纹是否全部匹配）；字段 all_html_blocks_match_raw_dom（正文块是否与原始DOM内容一致）。
        "checks": {"all_source_fingerprints_match": True, "all_html_blocks_match_raw_dom": True,
                   # 写入字段 all_candidate_text_reconstructs_from_source_parts（全部候选正文能否由原始切片重建）；字段 all_html_anchors_exist（所有网页章节锚点是否真实存在）。
                   "all_candidate_text_reconstructs_from_source_parts": True, "all_html_anchors_exist": True,
                   # 写入字段 pdf_page_text_matches_original_pdf（逐页文字记录是否与原PDF提取一致）；字段 pdf_character_slices_match（PDF证据能否由对应页字符切片还原）。
                   "pdf_page_text_matches_original_pdf": True, "pdf_character_slices_match": True,
                   # 写入字段 no_duplicate_ids_or_exact_passages_within_source（是否没有重复ID或同源重复正文）；字段 no_reference_list_leak（正文中是否没有混入参考文献列表）。
                   "no_duplicate_ids_or_exact_passages_within_source": True, "no_reference_list_leak": True,
                   # 写入字段 ready_token_counts_fit_512（已准入片段是否满足模型长度上限）；字段 no_family_crosses_dev_holdout（同一场景家族是否没有跨开发和留出）。
                   "ready_token_counts_fit_512": True, "no_family_crosses_dev_holdout": True,
                   # 写入字段 all_gold_references_exist_in_index_input（所有标准证据ID是否都在准入语料中）；字段 no_duplicate_report_question_pairs（是否没有完全相同的报告问题对）。
                   "all_gold_references_exist_in_index_input": True, "no_duplicate_report_question_pairs": True,
                   # 写入字段 split_files_equal_master_assignments（分集文件是否与主表的预先划分一致）。
                   "split_files_equal_master_assignments": True},
        # 写入字段 files（需要固定版本的文件清单）；字段 sha256（文件或响应的 SHA-256）。
        "files": {name: {"sha256": digest((root / "data/v2" / name).read_bytes()),
                         # 写入字段 bytes（文件原始字节数）。
                         "bytes": (root / "data/v2" / name).stat().st_size} for name in files},
        # 写入字段 v1_file_fingerprints_unchanged_by_pipeline（旧v1文件的内容指纹，供确认原资料未被改写）。
        "v1_file_fingerprints_unchanged_by_pipeline": {name: digest((root / "data" / name).read_bytes()) for name in ["sources.json", "evidence.jsonl", "cases.jsonl"]},
        # 写入字段 limits（验证不能覆盖的范围和限制）。
        "limits": ["Checks validate source preservation and split integrity, not medical correctness.",
                   # 继续组装上方容器中的本行元素，保持其原始顺序和取值。
                   "Questions and expected behavior are assistant-generated drafts requiring human review.",
                   # 继续组装上方容器中的本行元素，保持其原始顺序和取值。
                   "No retrieval, LLM generation, clinical validation or performance claims are included.",
                   # 继续组装上方容器中的本行元素，保持其原始顺序和取值。
                   "ACR and USPSTF extracts remain local-only pending a use-specific redistribution review; NCI text subset carries attribution.",
                   # 继续组装上方容器中的本行元素，保持其原始顺序和取值。
                   "Fleischner full text and Lung-RADS first-page table are excluded with reasons, not replaced by invented source text."],
    # 结束上方的字典或集合。
    }
    # 创建父目录并以 UTF-8 保存格式化 JSON。
    write_json(root / "results/ct_v2_validation.json", report)
    # 返回report，结束本次函数调用。
    return report


# 当 __name__ == '__main__' 成立时，执行下面的分支。
if __name__ == "__main__":
    # 设置处理结果：调用 validate，取得该步骤的处理结果。
    result = validate()
    # 打印当前进度、输出文件位置或核验结果，方便观察执行状态。
    print(json.dumps({key: result[key] for key in ["dataset_version", "source_files", "candidate_evidence", "index_input_evidence", "quarantined_evidence", "case_count", "scenario_families", "case_splits", "checks"]}, ensure_ascii=False, indent=2))

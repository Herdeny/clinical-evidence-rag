# 下面的文档字符串说明本模块、类或函数的用途和适用边界。
"""Source preservation checks for the batch corpus and synthetic evaluation set."""

# 导入JSON 编解码工具。
import json
# 导入路径对象 Path，便于定位脚本、组合目录并读写文件。
from pathlib import Path
# 导入测试框架。
import unittest
# 导入自动清理的临时目录工具。
import tempfile

# 从 数据准备包中的公共工具导入 validate。
from scripts.data.validate_ct_data import validate
# 从 数据准备包中的公共工具导入 build_cases。
from scripts.data.ct_data_pipeline import build_cases


# 设置项目根目录：按键或位置读取 Path(__file__).resolve().parents 中的对应内容。
ROOT = Path(__file__).resolve().parents[1]


# 定义这一组数据完整性测试用例。
class CtDataTests(unittest.TestCase):
    # 将下方方法绑定到类，使用 cls 访问类级共享数据。
    @classmethod
    # 定义 setUpClass：在这一组测试开始前准备共享的本地测试材料。
    def setUpClass(cls):
        # 设置cls.cards：按遍历顺序筛选并整理 (ROOT / 'data/v2/evidence.jsonl').read_text().splitlines() 中的数据。
        cls.cards = [json.loads(line) for line in (ROOT / "data/v2/evidence.jsonl").read_text().splitlines()]
        # 设置cls.by_id：按遍历顺序筛选并整理 cls.cards 中的数据。
        cls.by_id = {card["id"]: card for card in cls.cards}

    # 定义 test_all_source_positions_and_split_assignments：验证来源位置与场景划分完整性。
    def test_all_source_positions_and_split_assignments(self):
        # 设置处理结果：调用 validate，取得该步骤的处理结果。
        result = validate(ROOT)
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertTrue(all(result["checks"].values()))
        # A changed source must not silently inherit labels tied to old block IDs.
        # 进入受管理的上下文：创建测试专用临时目录并在结束后清理。
        with tempfile.TemporaryDirectory() as directory:
            # 设置root：创建文件路径对象，便于跨目录组合与读写。
            root = Path(directory)
            # 创建输出目录，按参数允许补建父目录或复用已有目录。
            (root / "data/v2").mkdir(parents=True)
            # 设置来源清单：解析 JSON 文本或字节，恢复为 Python 对象。
            sources = json.loads((ROOT / "data/v2/sources.json").read_text())
            # 设置sources[0]['snapshot_sha256']：字符串 'changed'。
            sources[0]["snapshot_sha256"] = "changed"
            # 将给定文本写入指定文件。
            (root / "data/v2/sources.json").write_text(json.dumps(sources))
            # 要求下方操作抛出指定异常；没有抛出或类型不符时测试失败。
            with self.assertRaisesRegex(ValueError, "Source snapshots changed"):
                # 从固定蓝本创建合成题及场景家族划分，并核对引用的证据 ID。
                build_cases(root)

    # 定义 test_variants_keep_imaging_context_with_procedure_rating：验证表格行仍与所属检查场景和适宜性评价对应。
    def test_variants_keep_imaging_context_with_procedure_rating(self):
        # 按顺序遍历[(1, 'b0002'), (2, 'b0012'), (3, 'b0022'), (4, 'b0032')]，本轮元素记作 (number, suffix)。
        for number, suffix in [(1, "b0002"), (2, "b0012"), (3, "b0022"), (4, "b0032")]:
            # 设置card：按键或位置读取 self.by_id 中的对应内容。
            card = self.by_id["acr-incidental-2023::" + suffix]
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            self.assertIn(f"Variant: {number}", card["text"])
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            self.assertIn("CT chest without IV contrast", card["text"])
            # 设置expected：根据 number == 2 选择两种结果中的一种。
            expected = "May Be Appropriate" if number == 2 else "Usually Appropriate"
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            self.assertIn("Appropriateness: " + expected, card["text"])
            # 当 number == 4 成立时，执行下面的分支。
            if number == 4:
                # 断言指定结果符合测试预期，不符合则使本项测试失败。
                self.assertIn("incomplete thoracic CT", card["text"])

    # 定义 test_source_type_does_not_promote_nci_summary_to_guideline：验证 NCI 证据综述没有被改标为正式指南。
    def test_source_type_does_not_promote_nci_summary_to_guideline(self):
        # 按顺序遍历self.cards，本轮元素记作 card。
        for card in self.cards:
            # 当 card['source_id'].startswith('nci-') 成立时，执行下面的分支。
            if card["source_id"].startswith("nci-"):
                # 断言指定结果符合测试预期，不符合则使本项测试失败。
                self.assertEqual(card["source_type"], "evidence_summary")
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertIn("does not provide formal guidelines", self.by_id["nci-lung-screening-pdq-hp::b0070"]["text"])

    # 定义 test_original_units_and_trigger_state_are_preserved：验证原文单位和条件触发状态没有被改写。
    def test_original_units_and_trigger_state_are_preserved(self):
        # 设置measurement：按键或位置读取 self.by_id['acr-lungrads-2022::p2::note4'] 中的对应内容。
        measurement = self.by_id["acr-lungrads-2022::p2::note4"]["text"]
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertIn("mm³", measurement)
        # 设置prior：按键或位置读取 self.by_id['acr-lungrads-2022::p2::note9'] 中的对应内容。
        prior = self.by_id["acr-lungrads-2022::p2::note9"]["text"]
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertIn("If waiting on prior exams", prior)
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertIn("temporary until", prior)

    # 定义 test_ambiguous_or_out_of_scope_records_are_quarantined：验证含混或超出范围的候选被隔离。
    def test_ambiguous_or_out_of_scope_records_are_quarantined(self):
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertNotIn("acr-lungrads-2022::p2::note6", self.by_id)
        # 设置candidates：按遍历顺序筛选并整理 (ROOT / 'data/v2/evidence_candidates.jsonl').read_text().splitlines() 中的数据。
        candidates = [json.loads(x) for x in (ROOT / "data/v2/evidence_candidates.jsonl").read_text().splitlines()]
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertTrue(any(c["id"].endswith("::note6") and not c["retrieval_ready"] for c in candidates))
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertFalse(any("Multi-Cancer Detection" in c["locator"].get("heading_path", []) for c in self.cards))

    # 定义 test_distribution_subset_contains_attributed_nci_text_only：验证可分发子集仅含带来源归属的 NCI 文字。
    def test_distribution_subset_contains_attributed_nci_text_only(self):
        # 设置subset：按遍历顺序筛选并整理 (ROOT / 'data/v2/evidence_nci_text.jsonl').read_text().splitlines() 中的数据。
        subset = [json.loads(x) for x in (ROOT / "data/v2/evidence_nci_text.jsonl").read_text().splitlines()]
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertTrue(subset)
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertTrue(all(c["source_id"].startswith("nci-") and c["distribution"] == "nci_text_with_attribution" for c in subset))


# 当 __name__ == '__main__' 成立时，执行下面的分支。
if __name__ == "__main__":
    # 以测试入口运行本文件中的测试用例。
    unittest.main()

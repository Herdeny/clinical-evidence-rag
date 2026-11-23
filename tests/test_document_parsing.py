# 下面的文档字符串说明本模块、类或函数的用途和适用边界。
"""验证来源切片、编号边界和子项保留；不评估医学内容正确性。"""

# 导入JSON 编解码工具。
import json
# 导入路径对象 Path，便于定位脚本、组合目录并读写文件。
from pathlib import Path
# 导入测试框架。
import unittest

# 从 数据准备包中的公共工具导入 parse_lungrads_notes、split_numbered_sections。
from scripts.data.document_parsing import parse_lungrads_notes, split_numbered_sections


# 定义这一组数据完整性测试用例。
class NumberedSectionsTests(unittest.TestCase):
    # 定义 test_lungrads_real_page_preserves_notes_and_provenance：验证真实 PDF 页的编号、原文切片、子项和页脚边界均被保留。
    def test_lungrads_real_page_preserves_notes_and_provenance(self):
        # 设置文件路径：将目录与右侧子路径组合，得到完整输出位置。
        path = Path(__file__).resolve().parents[1] / "data/v2/parsed/acr-lungrads-2022.pages.json"
        # 设置page：按键或位置读取 json.loads(path.read_text(encoding='utf-8')) 中的对应内容。
        page = json.loads(path.read_text(encoding="utf-8"))[1]
        # 设置notes：定位 Lung-RADS 页内 NOTES 范围，再复用通用编号分段器。
        notes = parse_lungrads_notes(page)
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertEqual([note["note_number"] for note in notes], list(range(1, 17)))
        # 按顺序遍历notes，本轮元素记作 note。
        for note in notes:
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            self.assertEqual(note["source_id"], page["source_id"])
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            self.assertEqual(note["page"], 2)
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            self.assertEqual(note["text"], page["text"][note["char_start"]:note["char_end"]])
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertIn("If waiting on prior exams", notes[8]["text"])
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertIn("a. Lung-RADS 0", notes[9]["text"])
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertIn("b. New solid or part solid nodules", notes[9]["text"])
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertIn("c. Some findings", notes[9]["text"])
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertNotIn("11. Airway", notes[9]["text"])
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertIn("no longer considered screening", notes[-1]["text"])
        # 按顺序遍历('Abbreviations:', 'Additional resources', 'All rights reserved')，本轮元素记作 footer。
        for footer in ("Abbreviations:", "Additional resources", "All rights reserved"):
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            self.assertNotIn(footer, notes[-1]["text"])

    # 定义 test_other_numbering_format_and_nonconsecutive_numbers：验证分段器可处理另一种编号样式和不连续编号。
    def test_other_numbering_format_and_nonconsecutive_numbers(self):
        # 设置当前文本：字符串 '1) First\ncontinued\n4) Second\na. nested condition\n'。
        text = "1) First\ncontinued\n4) Second\na. nested condition\n"
        # 设置sections：按编号标题切分文本，同时保留相对完整原文的字符范围。
        sections = split_numbered_sections(text, r"^(\d+)\)[ \t]*")
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertEqual([section["number"] for section in sections], [1, 4])
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertEqual(sections[0]["text"], "1) First\ncontinued\n")
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertIn("a. nested condition", sections[1]["text"])

    # 定义 test_absolute_offsets_with_bounded_range_and_decimals：验证有界分段使用原文绝对位置，且不误切小数。
    def test_absolute_offsets_with_bounded_range_and_decimals(self):
        # 设置prefix：字符串 '简介\n1. Outside the selected range\nBEGIN\n'。
        prefix = "简介\n1. Outside the selected range\nBEGIN\n"
        # 设置body：字符串 '2.First\na. Nested\n1.5 mm\n7. Second\n'。
        body = "2.First\na. Nested\n1.5 mm\n7. Second\n"
        # 设置当前文本：prefix + body + 'END\n9. Footer\n'。
        text = prefix + body + "END\n9. Footer\n"
        # 设置sections：按编号标题切分文本，同时保留相对完整原文的字符范围。
        sections = split_numbered_sections(
            # 继续为 split_numbered_sections 提供本行的参数或输入片段。
            text, r"^[ \t]*(\d+)\.[ \t]*(?=[A-Z])", len(prefix), len(prefix) + len(body)
        # 结束上方的函数调用、元组或分组表达式。
        )
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertEqual([section["number"] for section in sections], [2, 7])
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertEqual(sections[0]["char_start"], len(prefix))
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertEqual(sections[0]["text"], "2.First\na. Nested\n1.5 mm\n")
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertEqual(sections[-1]["char_end"], len(prefix) + len(body))

    # 定义 test_adapter_does_not_hardcode_sixteen_notes_or_source：验证适配器没有写死来源、页码或十六条注释的数量。
    def test_adapter_does_not_hardcode_sixteen_notes_or_source(self):
        # 设置page：字典，保存来源唯一标识，用于反查原始文件、从 1 开始的原文页码、本条正文或题目报告文字。
        page = {
            # 写入字段 source_id（来源唯一标识，用于反查原始文件）。
            "source_id": "synthetic-layout-check",
            # 写入字段 page（从 1 开始的原文页码）。
            "page": 5,
            # 写入字段 text（本条正文或题目报告文字）。
            "text": "NOTES\n1. First\n2.Second\nAbbreviations: XYZ\n",
        # 结束上方的字典或集合。
        }
        # 设置notes：定位 Lung-RADS 页内 NOTES 范围，再复用通用编号分段器。
        notes = parse_lungrads_notes(page)
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertEqual([note["note_number"] for note in notes], [1, 2])
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertTrue(all(note["source_id"] == page["source_id"] and note["page"] == 5 for note in notes))

    # 定义 test_missing_document_boundaries_fail_instead_of_ingesting_footer：验证缺少正文边界时明确失败，避免混入页脚。
    def test_missing_document_boundaries_fail_instead_of_ingesting_footer(self):
        # 按顺序遍历('1. First\nAbbreviations: X', 'NOTES\n1. First\nCopyright')，本轮元素记作 text。
        for text in ("1. First\nAbbreviations: X", "NOTES\n1. First\nCopyright"):
            # 要求下方操作抛出指定异常；没有抛出或类型不符时测试失败。
            with self.subTest(text=text), self.assertRaises(ValueError):
                # 定位 Lung-RADS 页内 NOTES 范围，再复用通用编号分段器。
                parse_lungrads_notes({"source_id": "example", "page": 1, "text": text})

    # 定义 test_no_matching_headings_are_reported：验证没有编号标题时给出错误。
    def test_no_matching_headings_are_reported(self):
        # 要求下方操作抛出指定异常；没有抛出或类型不符时测试失败。
        with self.assertRaisesRegex(ValueError, "未找到编号标题"):
            # 按编号标题切分文本，同时保留相对完整原文的字符范围。
            split_numbered_sections("Unnumbered content\n", r"^(\d+)\.")


# 当 __name__ == '__main__' 成立时，执行下面的分支。
if __name__ == "__main__":
    # 以测试入口运行本文件中的测试用例。
    unittest.main()

# 下面的文档字符串说明本模块、类或函数的用途和适用边界。
"""Check medically meaningful structure loss, not clinical recommendation accuracy."""

# 导入路径对象 Path，便于定位脚本、组合目录并读写文件。
from pathlib import Path
# 导入正则表达式工具，用于匹配标题或规范化空白。
import re
# 导入测试框架。
import unittest

# 从 lxml 中的指定接口导入 etree。
from lxml import etree
# 从 transformers 中的指定接口导入 AutoTokenizer。
from transformers import AutoTokenizer

# 从 数据准备包中的公共工具导入 clean、render、split_unit、table_units、xml_units。
from scripts.data.medical_corpus_parsing import clean, render, split_unit, table_units, xml_units
# 从 数据准备包中的公共工具导入 parse_identity。
from scripts.data.prepare_drug_sources import parse_identity


# 定义这一组数据完整性测试用例。
class MedicalParsingTests(unittest.TestCase):
    # 定义 test_negation_units_and_exponents_survive：验证否定、左右侧、小数、单位与上下标在提取后仍保留。
    def test_negation_units_and_exponents_survive(self):
        # 设置node：将原始 XML 字节解析成元素树。
        node = etree.fromstring('<p>No left-sided lesion. 1.5 mg/m<sup>2</sup>; H<sub>2</sub>O. See <xref ref-type="bibr">12</xref>.</p>')
        # 设置当前文本：只合并空白字符，保留医学数字、单位、否定词和符号。
        text = clean(render(node))
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertIn('No left-sided lesion.', text)
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertIn('1.5 mg/m^{2}', text)
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertIn('H_{2}O', text)
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertIn('[ref:12]', text)

    # 定义 test_unreadable_math_is_quarantined_and_sections_preserved：验证不可读数学标记被隔离，同时保留可用段落的章节。
    def test_unreadable_math_is_quarantined_and_sections_preserved(self):
        # 设置root：将原始 XML 字节解析成元素树。
        root = etree.fromstring('<article><body><sec><title>Contraindications</title><p>'
                                # 继续为 etree.fromstring 提供本行的参数或输入片段。
                                + 'Do not use this drug in the stated population. ' * 3
                                # 继续为 etree.fromstring 提供本行的参数或输入片段。
                                + '</p><p>Risk <inline-formula><math><mi>x</mi><mn>2</mn></math></inline-formula>'
                                # 继续为 etree.fromstring 提供本行的参数或输入片段。
                                + 'is not reliably readable here. ' * 5 + '</p></sec></body></article>')
        # 设置(units, excluded)：从论文或 SPL 的约定结构提取文本单元，隔离不可靠内容。
        units, excluded = xml_units(root, 'paper')
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertEqual(len(units), 1)
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertEqual(units[0]['section_path'], ['Contraindications'])
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertEqual(excluded[0]['reason'], 'unparsed_math')

    # 定义 test_formula_image_is_not_silently_deleted_and_spl_superscript_survives：验证公式图片不被静默删除，且 SPL 样式上标可保留。
    def test_formula_image_is_not_silently_deleted_and_spl_superscript_survives(self):
        # 从 数据准备包中的公共工具导入 UnparsedMath。
        from scripts.data.medical_corpus_parsing import UnparsedMath
        # 设置node：将原始 XML 字节解析成元素树。
        node = etree.fromstring('<p>Risk is <inline-formula><inline-graphic href="equation.png"/></inline-formula>.</p>')
        # 要求下方操作抛出指定异常；没有抛出或类型不符时测试失败。
        with self.assertRaises(UnparsedMath):
            # 将结构化节点转成可追溯文字，显式保留上下标并拒绝不可读公式。
            render(node)
        # 设置node：将原始 XML 字节解析成元素树。
        node = etree.fromstring('<paragraph>Dose 2 mg/m<content styleCode="Sup">2</content>.</paragraph>')
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertEqual(clean(render(node)), 'Dose 2 mg/m^{2}.')

    # 定义 test_table_carries_drug_across_rowspan_with_cell_origin：验证跨行表格能继承药名并定位到原单元格。
    def test_table_carries_drug_across_rowspan_with_cell_origin(self):
        # 设置root：将原始 XML 字节解析成元素树。
        root = etree.fromstring('<table><thead><tr><th>Drug</th><th>Condition</th><th>Recommendation</th></tr></thead><tbody>'
                                # 继续为 etree.fromstring 提供本行的参数或输入片段。
                                '<tr><td rowspan="2">Drug A</td><td>No renal impairment</td><td>Monitor symptoms</td></tr>'
                                # 继续为 etree.fromstring 提供本行的参数或输入片段。
                                '<tr><td>Severe renal impairment</td><td>Do not coadminister</td></tr></tbody></table>')
        # 设置rows：将可迭代结果按顺序收集为列表。
        rows = list(table_units(root, root.getroottree(), ['Interactions']))
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertEqual(len(rows), 2)
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertIn('Drug: Drug A', rows[1]['text'])
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertIn('Severe renal impairment', rows[1]['text'])
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertIn('Do not coadminister', rows[1]['text'])
        # 设置inherited：按键或位置读取 rows[1]['locator']['cells'] 中的对应内容。
        inherited = rows[1]['locator']['cells'][0]
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertEqual(inherited['xpath'], '/table/tbody/tr[1]/td[1]')

    # 定义 test_real_spl_identity_strength_and_narrative：验证本地真实 SPL 样本的产品身份、强度及章节位置。
    def test_real_spl_identity_strength_and_narrative(self):
        # 设置文件路径：将目录与右侧子路径组合，得到完整输出位置。
        path = Path(__file__).resolve().parents[1] / 'data/v3/research/spl_schema_example.xml'
        # 当 not path.exists() 成立时，执行下面的分支。
        if not path.exists():
            # 在本地缺少对应受限样本时明确跳过这项测试。
            self.skipTest('downloaded SPL fixture is local-only')
        # 设置原始字节内容：读取指定文件的原始字节。
        raw = path.read_bytes()
        # 设置value：从 SPL 核对 setID、版本、产品类别、成分、剂型和产品代码。
        value = parse_identity(raw, '5fec8de8-e409-4cf6-e063-6294a90af9c2')
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertIn('ANDA', value['marketing_category_reported'])
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertTrue(value['active_ingredients'])
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertEqual(value['products'][0]['ingredients'][0]['quantity'][0]['value'], '40')
        # 设置(units, _)：从论文或 SPL 的约定结构提取文本单元，隔离不可靠内容。
        units, _ = xml_units(etree.fromstring(raw), 'drug_label')
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertGreater(len(units), 20)
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertTrue(any('CONTRAINDICATION' in ' '.join(unit['section_path']).upper() for unit in units))
        # 按顺序遍历规范化文本单元，本轮元素记作 unit。
        for unit in units:
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            self.assertEqual(len(etree.ElementTree(etree.fromstring(raw)).xpath(unit['locator']['xpath'])), 1)

    # 定义 test_long_paragraph_has_no_lost_words_or_hidden_truncation：验证长段落分块没有丢词，所有块都符合实际 token 上限。
    def test_long_paragraph_has_no_lost_words_or_hidden_truncation(self):
        # 设置tokenizer：按参数加载 tokenizer；这里用于长度检查，不运行嵌入模型。
        tokenizer = AutoTokenizer.from_pretrained('BAAI/bge-small-en-v1.5', local_files_only=True)
        # 设置当前文本：用指定分隔符连接各段文字。
        text = ' '.join(f'Case {i}: no right-sided nodule; dose 1.5 mg daily.' for i in range(180))
        # 设置spans：按 tokenizer 的真实字符偏移切分长段落，确保不丢词且不隐藏截断。
        spans = split_unit(text, tokenizer, max_tokens=128)
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertGreater(len(spans), 2)
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertEqual(re.sub(r'\s+', '', ''.join(text[a:b] for a, b, _ in spans)), re.sub(r'\s+', '', text))
        # 按顺序遍历spans，本轮元素记作 (a, b, count)。
        for a, b, count in spans:
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            self.assertLessEqual(count, 128)
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            self.assertEqual(count, len(tokenizer.encode(text[a:b], truncation=False)))


# 当 __name__ == '__main__' 成立时，执行下面的分支。
if __name__ == '__main__':
    # 以测试入口运行本文件中的测试用例。
    unittest.main()

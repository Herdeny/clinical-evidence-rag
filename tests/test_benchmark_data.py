# 验证用户的BEIR读取接口，不实现该接口或运行检索。
"""Contract checks for the learner-owned BEIR dataset adapter."""

# 生成临时的标准TSV文件。
import csv
# 记录和比较结构化测试材料。
import json
# 使用真实和临时目录检验路径通用性。
from pathlib import Path
# 自动清理测试用数据。
import tempfile
# 沿用项目测试框架。
import unittest
# 用哨兵确认参数错误发生在数据读取之前。
from unittest.mock import patch

# 表格输出属于既定读取契约。
import pandas as pd
# 导入用户已保存的实际实现。
from benchmark_data import load_beir_dataset

# 测试代码位于根目录tests下。
ROOT = Path(__file__).resolve().parents[1]


# 每次返回新记录，避免不同失败用例互相污染。
def fixture_rows():
    # 纯数字字符串ID用于检验前导零是否保留。
    corpus = [{"_id": "007", "title": "Alpha", "text": "Body one"}, {"_id": "008", "title": "", "text": "Body two"}, {"_id": "009", "title": None, "text": "Body three"}]
    # 第三条查询不属于当前开发划分，应被筛掉。
    queries = [{"_id": "001", "text": "First query"}, {"_id": "002", "text": "Second query"}, {"_id": "003", "text": "Other split"}]
    # 同一查询的两篇相关文档及不同等级必须同时保留。
    qrels = [("001", "007", 2), ("001", "008", 1), ("002", "009", 1)]
    # 保留三种数据的原始角色。
    return corpus, queries, qrels


# 在隔离目录生成微型BEIR格式，不触碰公开基准文件。
def write_fixture(folder, corpus, queries, qrels):
    # 临时目录的名称故意与nfcorpus不同。
    folder = Path(folder)
    # 创建当前划分标签目录。
    (folder / "qrels").mkdir(parents=True)
    # 文档和查询分别序列化。
    for name, rows in (("corpus", corpus), ("queries", queries)):
        # 保持官方JSONL约定。
        (folder / f"{name}.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    # 标签文件必须包含标准列头。
    with (folder / "qrels/dev.tsv").open("w", encoding="utf-8", newline="") as stream:
        # 使用标准库正确输出制表符。
        writer = csv.writer(stream, delimiter="\t")
        # 明确每一列的角色。
        writer.writerow(["query-id", "corpus-id", "score"])
        # 保留等级与ID原值。
        writer.writerows(qrels)
    # 其他划分故意不可解析，dev读取不应接触它们。
    (folder / "qrels/train.tsv").write_text("not the requested split\n")
    # 同样放置测试划分隔离哨兵。
    (folder / "qrels/test.tsv").write_text("not the requested split\n")


# 同时检查真实开发数据与可控的小型边界输入。
class BenchmarkDataTests(unittest.TestCase):
    # 验证公开dev规模、字段、原值及返回顺序。
    def test_real_dev_contract(self):
        # 只使用真实开发划分。
        folder = ROOT / "data/external/nfcorpus/prepared/nfcorpus"
        # 返回顺序属于固定契约。
        corpus, queries, qrels = load_beir_dataset(folder, split="dev")
        # 先确认对象类型，避免把标签表当最终字典。
        self.assertIsInstance(corpus, pd.DataFrame)
        # 查询也应为表格。
        self.assertIsInstance(queries, pd.DataFrame)
        # 等级标签保持双层字典。
        self.assertIsInstance(qrels, dict)
        # 真实数量必须保持一致。
        self.assertEqual((len(corpus), len(queries), len(qrels)), (3633, 324, 324))
        # 多篇相关文档不能被覆盖成单个gold。
        self.assertEqual(sum(len(items) for items in qrels.values()), 11385)
        # 字段应兼容当前检索函数。
        self.assertTrue({"id", "title", "body", "text", "source_id", "locator"} <= set(corpus.columns))
        # 查询字段名保持统一。
        self.assertTrue({"id", "query"} <= set(queries.columns))
        # 对比官方原文，保证没有缩小文档库或重排正文。
        raw = pd.read_json(folder / "corpus.jsonl", lines=True, dtype=False)
        # ID保持原始行序。
        self.assertEqual(corpus["id"].tolist(), raw["_id"].tolist())
        # 原文保存在独立body列。
        self.assertEqual(corpus["body"].tolist(), raw["text"].tolist())
        # 标签保留原整数等级。
        self.assertEqual({grade for items in qrels.values() for grade in items.values()}, {1, 2})
        # 逐条类型也应是整数而非舍入后的浮点数。
        self.assertTrue(all(type(grade) is int for items in qrels.values() for grade in items.values()))
        # 返回的查询与当前标签恰好对应。
        self.assertEqual(set(queries["id"]), set(qrels))

    # 检查非默认目录、前导零、多对多标签和空标题。
    def test_generic_directory_ids_and_many_to_many_labels(self):
        # 所有文件仅存在于临时目录。
        with tempfile.TemporaryDirectory() as directory:
            # 名称明确不叫nfcorpus。
            folder = Path(directory) / "another_beir_dataset"
            # 每轮获取新测试记录。
            corpus_rows, query_rows, qrel_rows = fixture_rows()
            # 生成完整微型输入。
            write_fixture(folder, corpus_rows, query_rows, qrel_rows)
            # 字符串路径也应可以正常使用。
            corpus, queries, qrels = load_beir_dataset(str(folder), split="dev")
            # 检索库包含全部三篇，不按标签删文档。
            self.assertEqual(corpus["id"].tolist(), ["007", "008", "009"])
            # 当前划分只包含两条查询。
            self.assertEqual(set(queries["id"]), {"001", "002"})
            # 查询文本保持原值。
            self.assertEqual(dict(zip(queries["id"], queries["query"])), {"001": "First query", "002": "Second query"})
            # 两层ID及相关性等级必须完整保留。
            self.assertEqual(qrels, {"001": {"007": 2, "008": 1}, "002": {"009": 1}})
            # 标题加正文仅去掉首尾空白。
            self.assertEqual(corpus["text"].tolist(), ["Alpha Body one", "Body two", "Body three"])
            # 来源标识使用原始基准文档身份。
            self.assertEqual(corpus["source_id"].tolist(), corpus["id"].tolist())
            # 定位信息随数据集目录变化，而非写死nfcorpus。
            self.assertEqual(corpus["locator"].tolist(), [{"dataset": folder.name, "document_id": key} for key in ["007", "008", "009"]])

    # split错误应先于文件访问被明确拒绝。
    def test_invalid_split_rejected_before_file_access(self):
        # 明确阻止数据读取，避免pandas的其他ValueError造成假通过。
        with patch("benchmark_data.pd.read_json", side_effect=AssertionError("read_json called before split validation")), patch("benchmark_data.pd.read_csv", side_effect=AssertionError("read_csv called before split validation")):
            # 函数自身应在任何读取前拒绝参数。
            with self.assertRaises(ValueError):
                # 不应把无效split当成待创建文件名。
                load_beir_dataset("/nonexistent/beir_fixture", split="validation")

    # 重复ID不能通过字典覆盖或静默去重消失。
    def test_duplicate_document_or_query_ids_rejected(self):
        # 分别检查两种原始ID集合。
        for duplicate_kind in ("corpus", "queries"):
            # 子用例保留具体出错角色。
            with self.subTest(kind=duplicate_kind), tempfile.TemporaryDirectory() as directory:
                # 准备全新记录。
                corpus, queries, qrels = fixture_rows()
                # 在选定角色加入重复ID。
                (corpus if duplicate_kind == "corpus" else queries).append(dict((corpus if duplicate_kind == "corpus" else queries)[0]))
                # 保存异常输入。
                write_fixture(directory, corpus, queries, qrels)
                # 不接受静默覆盖。
                with self.assertRaises(ValueError):
                    # 用户函数负责完整性检查。
                    load_beir_dataset(directory)

    # 相同查询与文档不应出现两个相互覆盖的等级。
    def test_duplicate_qrel_pair_rejected(self):
        # 当前目录只用于此用例。
        with tempfile.TemporaryDirectory() as directory:
            # 获取新记录。
            corpus, queries, qrels = fixture_rows()
            # 故意给相同pair添加另一个等级。
            qrels.append(("001", "007", 1))
            # 保存冲突标签。
            write_fixture(directory, corpus, queries, qrels)
            # 应报告输入错误而不是保留最后一次赋值。
            with self.assertRaises(ValueError):
                # 执行实际用户实现。
                load_beir_dataset(directory)

    # 相关性等级应按原整数解析，不能把无效小数舍入成有效标签。
    def test_fractional_grade_rejected(self):
        # 在隔离数据中制造无效等级。
        with tempfile.TemporaryDirectory() as directory:
            # 保留正常的查询和文档。
            corpus, queries, qrels = fixture_rows()
            # 小数不符合当前整数qrels契约。
            qrels[0] = ("001", "007", 1.5)
            # 写入待检验标签。
            write_fixture(directory, corpus, queries, qrels)
            # 不接受round或直接截断标签。
            with self.assertRaises(ValueError):
                # 只读取，不调用任何模型。
                load_beir_dataset(directory)

    # 标签不能指向不存在的查询或文档。
    def test_dangling_reference_rejected(self):
        # 分别检查标签两端。
        for kind in ("query", "document"):
            # 各种异常相互隔离。
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                # 获取正常小型数据。
                corpus, queries, qrels = fixture_rows()
                # 插入没有对应原文的一条标签。
                qrels.append(("missing" if kind == "query" else "001", "missing" if kind == "document" else "007", 1))
                # 保存异常引用。
                write_fixture(directory, corpus, queries, qrels)
                # 不得通过过滤丢掉错误记录。
                with self.assertRaises(ValueError):
                    # 保留定位输入错误的机会。
                    load_beir_dataset(directory)

    # 正文缺失或当前划分为空时不能返回看似成功的结果。
    def test_empty_body_or_qrels_rejected(self):
        # 两种空输入分别检查。
        for kind in ("body", "qrels"):
            # 建立隔离子用例。
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                # 新建正常数据。
                corpus, queries, qrels = fixture_rows()
                # 标题存在不能掩盖正文为空。
                if kind == "body":
                    # 空白正文不算有效文本。
                    corpus[0]["text"] = " "
                # 另一种情形仅保留标签表头。
                else:
                    # 空划分应该被明确拒绝。
                    qrels = []
                # 保存边界输入。
                write_fixture(directory, corpus, queries, qrels)
                # 不应返回空查询当作完成了评测准备。
                with self.assertRaises(ValueError):
                    # 使用真实函数检查。
                    load_beir_dataset(directory)

    # 有效split但缺文件时保留清楚的文件缺失异常。
    def test_missing_file_preserves_file_not_found_error(self):
        # 临时目录内不创建任何数据。
        with tempfile.TemporaryDirectory() as directory:
            # 文件缺失不等于参数非法。
            with self.assertRaises(FileNotFoundError):
                # 不生成空的默认数据。
                load_beir_dataset(directory)


# 允许独立运行本组契约检查。
if __name__ == "__main__":
    # 不触发模型或全库评测。
    unittest.main()

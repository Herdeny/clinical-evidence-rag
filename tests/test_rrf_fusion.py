# 用手工排名和假检索函数验证融合与查询编排，不调用模型。
"""Public-contract checks for RRF fusion and query orchestration."""

# 保存输入的独立副本，检查原始命中是否被修改。
from copy import deepcopy
# 为测试时间记录使用明确的UTC时区。
from datetime import datetime, timezone
# 将验收结果绑定实际源码版本。
import hashlib
# 保存结构化验收记录。
import json
# 定位受测模块与输出目录。
from pathlib import Path
# 使用标准库测试框架。
import unittest
# 创建可记录调用参数和模拟错误的假检索函数。
from unittest.mock import Mock

# 导入用户实现的纯融合函数与查询编排。
from retrieve_rrf import fuse_rankings, retrieve_rrf


# 构造字段与现有检索接口一致的虚构命中。
def make_hit(identifier, score):
    # 使用嵌套定位字段，同时检查证据信息是否保留。
    return {"id": identifier, "score": score, "source_id": "synthetic", "locator": {"row": identifier}, "text": f"synthetic {identifier}"}


# 定义七类手工验收，不依赖临床数据或检索索引。
class RRFFusionTests(unittest.TestCase):
    # 为各项检查提供互不共享的输入。
    def example(self):
        # 两路原始得分量级不同，输入顺序表示已经确定的名次。
        return [[make_hit("A", .9), make_hit("B", .8)], [make_hit("B", 11), make_hit("C", 10)]]

    # 检查融合名次、手算分数和公共返回格式。
    def test_manual_two_rankings(self):
        # 执行约定的最小例子。
        result = fuse_rankings(self.example(), 3)
        # 返回值必须是列表。
        self.assertIsInstance(result, list)
        # 每个元素必须是可直接按字段读取的hit字典。
        self.assertTrue(all(isinstance(item, dict) for item in result))
        # 跨路重复的B只输出一次，并排在最前。
        self.assertEqual([item["id"] for item in result], ["B", "A", "C"])
        # B同时取得第二名和第一名的贡献。
        self.assertAlmostEqual(result[0]["score"], 1 / 62 + 1 / 61, places=12)
        # A只有一路的第一名贡献。
        self.assertAlmostEqual(result[1]["score"], 1 / 61, places=12)
        # C只有另一路的第二名贡献。
        self.assertAlmostEqual(result[2]["score"], 1 / 62, places=12)
        # 其余证据信息必须保留。
        self.assertEqual(result[0]["locator"], {"row": "B"})
        # 检查最终返回数量受k控制。
        self.assertEqual(fuse_rankings(self.example(), 2), result[:2])

    # 检查全空排名不产生虚构候选。
    def test_all_empty(self):
        # 无检索路时返回空列表。
        self.assertEqual(fuse_rankings([], 3), [])
        # 两路均空也返回空列表。
        self.assertEqual(fuse_rankings([[], []], 3), [])

    # 检查输入分数与证据字段保持原样。
    def test_input_unchanged(self):
        # 取得独立输入。
        rankings = self.example()
        # 保存原始值。
        original = deepcopy(rankings)
        # 运行实际函数。
        fuse_rankings(rankings, 3)
        # 所有输入字典和嵌套字段都不能被改写。
        self.assertEqual(rankings, original)

    # 检查单路重复ID被拒绝，跨路同ID则由正常例子验证累加。
    def test_duplicate_within_one_ranking(self):
        # 同一份排名出现两次A应当明确报错。
        with self.assertRaises(ValueError):
            # 不允许同一路重复投票。
            fuse_rankings([[make_hit("A", 2), make_hit("A", 1)]], 3)

    # 检查同分规则和k大于候选总数的情况。
    def test_ties_and_k_above_count(self):
        # 两路各第一名的RRF贡献相同。
        result = fuse_rankings([[make_hit("Z", 200)], [make_hit("A", .1)]], 5)
        # 同分按ID升序，而且只返回实际存在的两条。
        self.assertEqual([item["id"] for item in result], ["A", "Z"])

    # 检查某一路为空不影响另一条有效排名。
    def test_one_empty_ranking(self):
        # 两条实际证据来自第二路。
        result = fuse_rankings([[], [make_hit("A", 2), make_hit("B", 1)]], 5)
        # 应完整保留两条候选的顺序。
        self.assertEqual([item["id"] for item in result], ["A", "B"])

    # 检查参数必须为正整数，并排除布尔值。
    def test_positive_integer_parameters(self):
        # 分别检查非法k和非法平滑常量。
        invalid = [(0, 60), (-1, 60), (True, 60), (1.5, 60), ("3", 60), (3, 0), (3, -1), (3, True), (3, 1.5), (3, "60")]
        # 各组边界独立展示，便于定位回归。
        for k, constant in invalid:
            # 保存当前被测参数。
            with self.subTest(k=k, rrf_constant=constant):
                # 参数应在处理排名前被拒绝。
                with self.assertRaises(ValueError):
                    # 空排名可以隔离参数校验，避免其他错误掩盖它。
                    fuse_rankings([], k, rrf_constant=constant)


# 检查查询编排的调用边界，实际融合仍使用用户函数。
class RRFRetrievalTests(unittest.TestCase):
    # 验证同一原始查询、每路候选数、调用次数和融合结果。
    def test_calls_and_fusion(self):
        # 构造两份独立手工排名。
        rankings = RRFFusionTests().example()
        # 保留原始检索结果，检查编排不污染输入。
        original = deepcopy(rankings)
        # 创建第一路可计数的假检索函数。
        dense = Mock(return_value=rankings[0])
        # 创建第二路可计数的假检索函数。
        bm25 = Mock(return_value=rankings[1])
        # 查询含换行，检查包装函数是否原样传递。
        query = "Report: synthetic report\nQuestion: synthetic question"
        # 最终只取三条，每路仍应使用默认候选数二十。
        result = retrieve_rrf(query, 3, dense_retrieve_fn=dense, bm25_retrieve_fn=bm25)
        # Dense必须恰好调用一次，并收到原始查询。
        dense.assert_called_once_with(query, 20)
        # BM25同样必须恰好调用一次。
        bm25.assert_called_once_with(query, 20)
        # 验证最终返回统一的hit字典列表。
        self.assertEqual([item["id"] for item in result], ["B", "A", "C"])
        # 验证默认平滑常量被正确传给融合函数。
        self.assertAlmostEqual(result[0]["score"], 1 / 62 + 1 / 61, places=12)
        # 两路原始结果都不能被改写。
        self.assertEqual(rankings, original)

    # 验证非默认候选数、最终数量和常量能够正确传递。
    def test_custom_candidate_budget_and_constant(self):
        # 取得与默认用例相同的手工排名。
        rankings = RRFFusionTests().example()
        # 构造两路假检索函数。
        dense, bm25 = Mock(return_value=rankings[0]), Mock(return_value=rankings[1])
        # 候选五条、最终两条，常量改为十以检查参数传递。
        result = retrieve_rrf("custom query", 2, dense_retrieve_fn=dense, bm25_retrieve_fn=bm25, candidate_k=5, rrf_constant=10)
        # 每路应收到五而不是最终的二。
        dense.assert_called_once_with("custom query", 5)
        # 第二路应收到同一候选预算。
        bm25.assert_called_once_with("custom query", 5)
        # 最终数量受k控制。
        self.assertEqual([item["id"] for item in result], ["B", "A"])
        # 常量应沿用本次显式设置，不能被内部默认值覆盖。
        self.assertAlmostEqual(result[0]["score"], 1 / 12 + 1 / 11, places=12)

    # 验证参数不合法时不能发生任何真实检索调用。
    def test_invalid_parameters_before_retrieval(self):
        # 依次检查最终数量、候选数、常量及候选预算不足。
        invalid = [(0, 20, 60), (-1, 20, 60), (True, 20, 60), (1.5, 20, 60), (3, 0, 60), (3, -1, 60), (3, True, 60), (3, 20.0, 60), (3, "20", 60), (3, 20, 0), (3, 20, -1), (3, 20, True), (3, 20, 60.0), (21, 20, 60)]
        # 每个边界用全新的假函数独立检查。
        for k, candidate_k, constant in invalid:
            # 在失败报告中保留当前参数组合。
            with self.subTest(k=k, candidate_k=candidate_k, rrf_constant=constant):
                # 两路调用次数都从零开始。
                dense, bm25 = Mock(), Mock()
                # 非法参数应由入口明确拒绝。
                with self.assertRaises(ValueError):
                    # 运行用户编排，禁止调用任何真实模型。
                    retrieve_rrf("query", k, dense_retrieve_fn=dense, bm25_retrieve_fn=bm25, candidate_k=candidate_k, rrf_constant=constant)
                # Dense不得在校验失败后被调用。
                dense.assert_not_called()
                # BM25也不得被调用。
                bm25.assert_not_called()

    # 验证空路和实际候选不足时的返回值。
    def test_empty_routes_and_fewer_candidates(self):
        # 显式列出期望结果，避免补造不存在的证据。
        examples = [([], [], []), ([], [make_hit("A", 2)], ["A"]), ([make_hit("A", .9)], [], ["A"])]
        # 每种空路情况独立检查。
        for dense_hits, bm25_hits, expected in examples:
            # 记录当前期待的ID列表。
            with self.subTest(expected=expected):
                # 用固定返回值模拟候选不足。
                dense, bm25 = Mock(return_value=dense_hits), Mock(return_value=bm25_hits)
                # 即使最终要求三条，也只返回实际候选。
                result = retrieve_rrf("query", 3, dense_retrieve_fn=dense, bm25_retrieve_fn=bm25)
                # 检查没有虚构或重复填充候选。
                self.assertEqual([item["id"] for item in result], expected)

    # 验证上游错误正常传播，不被伪装为空命中。
    def test_upstream_errors_propagate(self):
        # 首路模拟检索失败。
        dense = Mock(side_effect=RuntimeError("synthetic dense failure"))
        # 第二路在首路失败时尚不应执行。
        bm25 = Mock()
        # 应保留原始错误。
        with self.assertRaisesRegex(RuntimeError, "synthetic dense failure"):
            # 检查顺序调用的失败路径。
            retrieve_rrf("query", 3, dense_retrieve_fn=dense, bm25_retrieve_fn=bm25)
        # 第一条路线只尝试一次。
        dense.assert_called_once_with("query", 20)
        # 不应在失败后悄悄变成另一条路线的单独检索。
        bm25.assert_not_called()
        # 另一个用例让Dense成功但BM25失败。
        dense = Mock(return_value=[])
        # 保留第二条路线的具体错误。
        bm25 = Mock(side_effect=RuntimeError("synthetic bm25 failure"))
        # 第二路异常同样需要传播。
        with self.assertRaisesRegex(RuntimeError, "synthetic bm25 failure"):
            # 不将错误改写成空列表。
            retrieve_rrf("query", 3, dense_retrieve_fn=dense, bm25_retrieve_fn=bm25)
        # 两条路线在这次调用中分别执行一次。
        dense.assert_called_once_with("query", 20)
        # 第二条路线也只尝试一次。
        bm25.assert_called_once_with("query", 20)


# 直接运行时保存验收报告，普通测试发现模式不额外写结果文件。
if __name__ == "__main__":
    # 从测试文件位置确定项目根目录。
    root = Path(__file__).resolve().parents[1]
    # 记录开始前受测源码。
    source = (root / "retrieve_rrf.py").read_bytes()
    # 同时执行七项融合检查与五项查询编排检查。
    suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(RRFFusionTests), unittest.defaultTestLoader.loadTestsFromTestCase(RRFRetrievalTests)])
    # 打印精简且可定位的逐项测试结果。
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    # 核对测试期间用户源码未发生变化。
    unchanged = source == (root / "retrieve_rrf.py").read_bytes()
    # 取得真实手工样例输出，不调用模型。
    sample = fuse_rankings(RRFFusionTests().example(), 3) if result.wasSuccessful() else None
    # 将结果绑定源码、测试版本与实际时间。
    report = {"validated_at_utc": datetime.now(timezone.utc).isoformat(), "scope": "manual RRF fusion and mocked retrieval orchestration; no models, corpus or benchmark questions", "test_classes": ["RRFFusionTests", "RRFRetrievalTests"], "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors), "passed": result.wasSuccessful() and unchanged, "source_unchanged": unchanged, "source_sha256": hashlib.sha256(source).hexdigest(), "source_text": source.decode(), "test_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "sample": sample}
    # 将最新验收另存，不覆盖此前两份失败证据。
    path = root / "results" / "rrf_retrieval_validation.json"
    # 保存完整记录。
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # 测试失败或源码并发变化时返回非零状态。
    raise SystemExit(0 if report["passed"] else 1)

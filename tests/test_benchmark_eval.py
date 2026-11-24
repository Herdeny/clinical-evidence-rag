# 用临时查询和真实评分包验证用户评测编排，不运行模型或公开基准。
import unittest
# 用表格表达与读取器一致的查询接口。
import pandas as pd
# 测试时关闭进度条显示，保留实际循环逻辑。
from unittest.mock import patch
# 只调用用户实际保存的评测函数。
from benchmark_eval import evaluate_beir_retrieval


# 每次生成独立输入，避免不同用例互相影响。
def make_inputs():
    # 非连续行标签用于检验按查询身份和原顺序处理。
    queries = pd.DataFrame([{"id": "q-full", "query": "Original FULL query?"}, {"id": "q-empty", "query": "Original EMPTY query?"}], index=[7, 2])
    # 第一题有两个不同等级的相关文档，第二题有一个。
    qrels = {"q-full": {"A": 2, "B": 1}, "q-empty": {"C": 1}}
    # 两种对象保持独立角色。
    return queries, qrels


# 检查既定的查询编排、评分与输入错误处理契约。
class BenchmarkEvalTests(unittest.TestCase):
    # 关闭终端进度显示，使检查输出只包含测试结果。
    def setUp(self):
        # 对输入迭代器原样返回，保留用户的遍历过程。
        progress = patch("benchmark_eval.tqdm", side_effect=lambda iterable, **kwargs: iterable)
        # 在本用例内启用显示替代。
        progress.start()
        # 用例结束时自动恢复真实进度条。
        self.addCleanup(progress.stop)

    # 正常题和空命中题应各占一行，且检索预算只使用一次。
    def test_perfect_and_empty_results_preserve_rows_scores_and_single_calls(self):
        # 获取原始查询及等级标签。
        queries, qrels = make_inputs()
        # 记录实际调用，检验原查询和每题次数。
        calls = []
        # 这个检索替身只依赖查询内容，不接收标注。
        def retrieve(query, k):
            # 原样记录检索输入和预算。
            calls.append((query, k))
            # 混合数值表示检验输出转换为Python浮点数。
            return [{"id": "A", "score": "0.9"}, {"id": "B", "score": 0.8}] if query == "Original FULL query?" else []
        # 调用实际用户实现与真实评分包。
        frame, run = evaluate_beir_retrieval(queries, qrels, retrieve)
        # 每题仅一次检索，使用默认最大K。
        self.assertEqual(calls, [(query, 100) for query in queries["query"]])
        # 返回顺序由输入查询决定。
        self.assertEqual(frame["query_id"].tolist(), queries["id"].tolist())
        # 检索字符串应原样保存。
        self.assertEqual(frame["query"].tolist(), queries["query"].tolist())
        # 空命中也必须有对应键，数值保持实际检索分数。
        self.assertEqual(run, {"q-full": {"A": 0.9, "B": 0.8}, "q-empty": {}})
        # 保持评分库要求的Python浮点类型。
        self.assertTrue(all(type(value) is float for hits in run.values() for value in hits.values()))
        # 命中列表与分数列表保持对齐。
        self.assertEqual(frame["retrieved_ids"].tolist(), [["A", "B"], []])
        # 保存结果使用转换后的分数。
        self.assertEqual(frame["scores"].tolist(), [[0.9, 0.8], []])
        # 两个K下的两种指标都必须保留空题分母。
        for column in ("ndcg_at_10", "ndcg_at_100", "recall_at_10", "recall_at_100"):
            # 完全命中与空命中的可解释期望分别为1和0。
            self.assertEqual(frame[column].tolist(), [1.0, 0.0])
            # 两题汇总不能把空题删掉。
            self.assertEqual(frame[column].mean(), 0.5)
        # 耗时应为每题检索的非负毫秒数。
        self.assertTrue(frame["latency_ms"].ge(0).all())

    # 不同等级的顺序影响nDCG，同时验证自定义K不被写死。
    def test_grade_order_affects_ndcg_not_recall_and_custom_ks(self):
        # 单查询便于隔离排序效应。
        queries = pd.DataFrame([{"id": "grade-query", "query": "Grade order"}])
        # 两篇文档的相关性等级不同。
        qrels = {"grade-query": {"A": 2, "B": 1}}
        # 按等级正确排序的替身。
        good = lambda query, k: [{"id": "A", "score": 0.9}, {"id": "B", "score": 0.8}][:k]
        # 交换文档顺序而不改变命中的文档集合。
        reversed_order = lambda query, k: [{"id": "B", "score": 0.9}, {"id": "A", "score": 0.8}][:k]
        # 非默认且非升序的K应仍可正确计算。
        correct, _ = evaluate_beir_retrieval(queries, qrels, good, ks=(3, 1))
        # 同一参数下只改变排名。
        reversed_frame, _ = evaluate_beir_retrieval(queries, qrels, reversed_order, ks=(3, 1))
        # 全部相关文档按等级正确排序时nDCG为1。
        self.assertEqual(correct.loc[0, "ndcg_at_3"], 1.0)
        # 把较低等级排前面应降低排序质量。
        self.assertLess(reversed_frame.loc[0, "ndcg_at_3"], 1.0)
        # 两篇都命中时召回不受顺序影响。
        self.assertEqual(correct.loc[0, "recall_at_3"], reversed_frame.loc[0, "recall_at_3"])
        # K为1时只命中两篇中的一篇。
        self.assertEqual(correct.loc[0, "recall_at_1"], 0.5)

    # 空结果不能使任何查询从评测中消失。
    def test_all_empty_results_keep_all_queries(self):
        # 使用同样的两题标注。
        queries, qrels = make_inputs()
        # 模拟两条查询均未找到候选。
        frame, run = evaluate_beir_retrieval(queries, qrels, lambda query, k: [])
        # 所有原始题目都必须保留。
        self.assertEqual(frame["query_id"].tolist(), queries["id"].tolist())
        # 每题在评分输入中也保留空字典。
        self.assertEqual(run, {key: {} for key in queries["id"]})
        # 所有指标为数值0，不能是缺失值。
        self.assertTrue(frame[["ndcg_at_10", "ndcg_at_100", "recall_at_10", "recall_at_100"]].eq(0).all().all())

    # 无效的查询集合应在任何检索调用前被拒绝。
    def test_invalid_query_inputs_rejected_before_retrieval(self):
        # 准备正常输入用于局部制造异常。
        queries, qrels = make_inputs()
        # 以不同正文保留重复ID，避免只检查重复整行。
        duplicate = pd.DataFrame([{"id": "q-full", "query": "One"}, {"id": "q-full", "query": "Other"}])
        # 包括空表、重复ID、标注缺查询与查询缺标注两种方向。
        cases = [(queries.iloc[:0], {}), (duplicate, {"q-full": {"A": 1}}), (queries, {"q-full": {"A": 1}}), (queries.iloc[:1], qrels)]
        # 各种无效输入都必须被拒绝。
        for query_frame, labels in cases:
            # 子用例便于区分失败输入。
            with self.subTest(ids=query_frame["id"].tolist(), qrel_ids=list(labels)):
                # 检索哨兵可发现“先检索再检查”的错误。
                with self.assertRaises(ValueError):
                    # 检索被调用时抛不同异常，避免假通过。
                    evaluate_beir_retrieval(query_frame, labels, lambda query, k: self.fail("invalid query inputs reached retrieval"))

    # K的异常必须明确来自参数校验，不能误借其他ValueError通过。
    def test_invalid_ks_rejected_before_retrieval(self):
        # 标签与查询保持匹配，只改变K。
        queries, qrels = make_inputs()
        # 包含空、非正数、布尔值、小数以及重复K。
        for ks in ((), (0,), (-1,), (True,), (1.5,), (10, 10)):
            # 记录当前参数组合。
            with self.subTest(ks=ks):
                # 异常信息必须能定位到ks参数。
                with self.assertRaisesRegex(ValueError, "ks"):
                    # 无效K不应触发任何检索。
                    evaluate_beir_retrieval(queries, qrels, lambda query, k: self.fail("invalid ks reached retrieval"), ks=ks)

    # 无效命中应被拒绝，异常需要标明是哪一条查询。
    def test_invalid_hits_rejected_with_query_id(self):
        # 为异常定位设置容易识别的查询ID。
        query_id = "query-bad-hits"
        # 单条查询只用于无效命中的边界输入。
        queries = pd.DataFrame([{"id": query_id, "query": "Bad hits"}])
        # 标注本身完全有效。
        qrels = {query_id: {"A": 1}}
        # 检查重复ID、三种非有限值、超预算和不可转换分数。
        cases = [([{"id": "A", "score": 0.9}, {"id": "A", "score": 0.8}], (2,)), ([{"id": "A", "score": float("nan")}], (1,)), ([{"id": "A", "score": float("inf")}], (1,)), ([{"id": "A", "score": -float("inf")}], (1,)), ([{"id": "A", "score": 0.9}, {"id": "B", "score": 0.8}], (1,)), ([{"id": "A", "score": "invalid"}], (1,))]
        # 各类错误都应提供题号，避免无法追查逐题失败。
        for hits, ks in cases:
            # 保存子用例身份。
            with self.subTest(hits=hits, ks=ks):
                # 接受直接输入错误或附上下文的运行错误。
                with self.assertRaisesRegex((ValueError, RuntimeError), query_id):
                    # 每次返回当前无效命中。
                    evaluate_beir_retrieval(queries, qrels, lambda query, k: hits, ks=ks)

    # 检索自身失败时仍应在异常中保留查询身份。
    def test_retrieval_failure_identifies_query(self):
        # 独立题号便于确认错误来自实际检索。
        query_id = "query-retrieval-failure"
        # 创建一条合法查询。
        queries = pd.DataFrame([{"id": query_id, "query": "Fail upstream"}])
        # 记录是否实际到达检索调用。
        calls = []
        # 模拟上游检索故障。
        def broken(query, k):
            # 记录原始输入。
            calls.append((query, k))
            # 原始故障不包含题号，由编排层补充上下文。
            raise RuntimeError("upstream failed")
        # 用户函数应抛出可定位题号的错误。
        with self.assertRaisesRegex((ValueError, RuntimeError), query_id):
            # 标签有效，故障仅来自检索。
            evaluate_beir_retrieval(queries, {query_id: {"A": 1}}, broken)
        # 确认调用确实进入上游检索。
        self.assertEqual(calls, [("Fail upstream", 100)])


# 支持从项目根目录单独运行这组检查。
if __name__ == "__main__":
    # 不构建索引、不运行公开题库或模型。
    unittest.main()

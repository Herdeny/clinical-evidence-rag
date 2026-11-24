# 检查公开基准保存辅助的文件保真、分母、配置及覆盖保护。
import copy
# 比较输入文件指纹。
import hashlib
# 读回JSON与JSONL。
import json
# 每个用例使用独立临时目录。
import tempfile
# 沿用项目测试框架。
import unittest
# 使用可配置路径。
from pathlib import Path
# 构造已经计算好的逐题结果，不运行检索或评分。
import pandas as pd
# 只测试保存辅助，不接触模型。
from retrieval_results_io import save_beir_results


# 创建微型BEIR输入和具有明确期望的已算结果。
def fixture(root):
    # 使用标准数据目录。
    data_dir = Path(root) / "fixture"
    # 仅当前dev划分有标签。
    (data_dir / "qrels").mkdir(parents=True)
    # 保留数字字符串ID以防序列化时丢前导零。
    corpus = [{"_id": key, "title": "Title", "text": "Body"} for key in ("007", "008", "009")]
    # 两条查询都必须出现在最后结果中。
    queries = [{"_id": "001", "text": "First question"}, {"_id": "002", "text": "Empty hits"}]
    # 保存标准JSONL原始输入。
    for name, rows in (("corpus", corpus), ("queries", queries)):
        # 每条记录独立一行。
        (data_dir / f"{name}.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    # 标签覆盖两题，其中一题在本次检索中没有命中。
    (data_dir / "qrels/dev.tsv").write_text("query-id\tcorpus-id\tscore\n001\t007\t2\n001\t008\t1\n002\t009\t1\n", encoding="utf-8")
    # 构造已算好的逐题指标，不让保存模块重新评分。
    rows = [{"query_id": "001", "query": "First question", "retrieved_ids": ["007", "008"], "scores": [0.9, 0.8], "latency_ms": 10.0}, {"query_id": "002", "query": "Empty hits", "retrieved_ids": [], "scores": [], "latency_ms": 20.0}]
    # 所有K下第一题完全正确，第二题为0。
    for index, row in enumerate(rows):
        # 逐列设置易于核对的既算指标。
        row.update({f"{name}_at_{k}": float(index == 0) for k in (10, 100) for name in ("ndcg", "recall")})
    # 评分输入保留检索分数而非相关等级。
    run = {"001": {"007": 0.9, "008": 0.8}, "002": {}}
    # 真实方法配置放在方法层。
    config = {"dataset_name": "fixture", "data_dir": str(data_dir), "split": "dev", "retrieval_method": "bm25", "ks": [10, 100], "query_template": "{query}", "corpus_text": "title + space + body; strip", "bm25": {"model_name": "rank_bm25.BM25Okapi", "device": "cpu", "query_prefix": "", "k1": 1.5, "b": 0.75, "epsilon": 0.25}}
    # 统一返回辅助测试需要的对象。
    return pd.DataFrame(rows), run, config


# 测试保存后的实际文件，而不只检查函数返回值。
class BeirResultsIOTests(unittest.TestCase):
    # 验证三类产物、空题分母、输入指纹和方法配置不变。
    def test_roundtrip_counts_metrics_hashes_and_config(self):
        # 使用隔离目录。
        with tempfile.TemporaryDirectory() as directory:
            # 获取合法小型输入。
            frame, run, config = fixture(directory)
            # 保存原配置以检查辅助函数不改写它。
            before = copy.deepcopy(config)
            # 导出已经算好的结果。
            summary = save_beir_results(frame, run, config=config, run_name="fixture_bm25_dev", result_dir=Path(directory) / "out")
            # 方法层配置必须原样保留。
            self.assertEqual(config, before)
            # 摘要不丢空题，文档数来自配套语料。
            self.assertEqual((summary["document_count"], summary["query_count"]), (3, 2))
            # 指标在全部两行上平均。
            self.assertEqual(set(summary["metrics"].values()), {0.5})
            # 耗时仅汇总既有逐题测量。
            self.assertEqual(summary["latency_ms"]["mean"], 15.0)
            # 读回真正落盘的逐题文件。
            loaded = [json.loads(line) for line in Path(summary["files"]["results"]).read_text(encoding="utf-8").splitlines()]
            # 数字字符串查询ID保留前导零和次序。
            self.assertEqual([row["query_id"] for row in loaded], ["001", "002"])
            # 空命中列表必须保留。
            self.assertEqual(loaded[1]["retrieved_ids"], [])
            # 评分输入与原run逐项一致。
            self.assertEqual(json.loads(Path(summary["files"]["run"]).read_text()), run)
            # 落盘摘要与返回摘要一致。
            self.assertEqual(json.loads(Path(summary["files"]["summary"]).read_text()), summary)
            # 三个输入都按实际字节计算指纹。
            for metadata in summary["input_sha256"].values():
                # 独立计算并核对。
                self.assertEqual(metadata["sha256"], hashlib.sha256(Path(metadata["path"]).read_bytes()).hexdigest())

    # 删除空题也会改变分母，保存时应拒绝。
    def test_missing_query_rejected_before_writing(self):
        # 本用例不触碰其他结果。
        with tempfile.TemporaryDirectory() as directory:
            # 从完整输入开始。
            frame, run, config = fixture(directory)
            # 明确输出目录初始不存在。
            output = Path(directory) / "out"
            # 逐题结果和run同时丢题也不能通过。
            with self.assertRaises(ValueError):
                # 所选qrels仍有两题。
                save_beir_results(frame.iloc[:1], {"001": run["001"]}, config=config, run_name="missing", result_dir=output)
            # 失败时不留下看似成功的文件。
            self.assertFalse(output.exists())

    # 逐题列表和评分输入不能保存不同分数。
    def test_conflicting_run_rejected_before_writing(self):
        # 创建隔离输入。
        with tempfile.TemporaryDirectory() as directory:
            # 仅修改run中的一个分数。
            frame, run, config = fixture(directory)
            # 模拟错误地保存另一轮检索分数。
            run["001"]["007"] = 0.1
            # 检查具体题号是否保留。
            with self.assertRaisesRegex(ValueError, "001"):
                # 不允许覆盖逐题结果来掩盖矛盾。
                save_beir_results(frame, run, config=config, run_name="conflict", result_dir=Path(directory) / "out")

    # NaN指标和负耗时不能写入有效摘要。
    def test_invalid_metric_or_latency_rejected(self):
        # 两种异常分别检查。
        for column, value in (("ndcg_at_10", float("nan")), ("latency_ms", -1.0)):
            # 子用例使用独立目录。
            with self.subTest(column=column), tempfile.TemporaryDirectory() as directory:
                # 每轮取得新输入。
                frame, run, config = fixture(directory)
                # 制造一个非法既算值。
                frame.loc[0, column] = value
                # 保存层应明确拒绝。
                with self.assertRaises(ValueError):
                    # 不重新评分或偷偷改成0。
                    save_beir_results(frame, run, config=config, run_name="invalid", result_dir=Path(directory) / "out")

    # 同名结果再次导出时必须保留旧产物。
    def test_existing_run_not_overwritten(self):
        # 使用临时结果目录。
        with tempfile.TemporaryDirectory() as directory:
            # 创建一轮合法输入。
            frame, run, config = fixture(directory)
            # 首次保存应正常完成。
            summary = save_beir_results(frame, run, config=config, run_name="existing", result_dir=Path(directory) / "out")
            # 固定旧产物字节以便核对。
            before = {name: Path(path).read_bytes() for name, path in summary["files"].items()}
            # 第二次明确拒绝同名写入。
            with self.assertRaises(FileExistsError):
                # 保持相同名称模拟误运行。
                save_beir_results(frame, run, config=config, run_name="existing", result_dir=Path(directory) / "out")
            # 全部旧文件都必须原样保留。
            self.assertEqual(before, {name: Path(path).read_bytes() for name, path in summary["files"].items()})

    # RRF两路配置保持各自身份，不要求虚构全局模型。
    def test_grouped_rrf_metadata_preserved(self):
        # 仅验证保存配置，不执行组合检索。
        with tempfile.TemporaryDirectory() as directory:
            # 从已有逐题表开始。
            frame, run, config = fixture(directory)
            # 方法改为RRF并保留两路配置。
            config.update({"retrieval_method": "rrf", "dense": {"model_name": "test-embedding", "device": "cpu", "query_prefix": "test prefix"}, "rrf": {"candidate_k": 100, "rrf_constant": 60}})
            # 原配置应保持不变。
            before = copy.deepcopy(config)
            # 保存同一结构的已算结果。
            summary = save_beir_results(frame, run, config=config, run_name="rrf", result_dir=Path(directory) / "out")
            # 确认两路和融合参数都原样进入摘要。
            self.assertEqual(summary["config"], before)
            # 不在顶层新增虚构模型字段。
            self.assertNotIn("model_name", config)


# 允许独立执行保存辅助检查。
if __name__ == "__main__":
    # 不运行真实语料索引、检索或模型。
    unittest.main()

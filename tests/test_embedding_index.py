# 验证用户的分批编码编排；仅使用合成证据和向量，不加载真实模型。
"""Synthetic integration checks for document encoding and cache reuse."""

# 捕获被测函数的进度输出，保持测试结果简洁。
from contextlib import redirect_stdout
# 计算当前受测源码的指纹，让验证结果绑定实际代码。
import hashlib
# 提供捕获输出使用的内存缓冲。
from io import StringIO
# 保存机器可读的验收结果。
import json
# 组合临时目录和项目内结果路径。
from pathlib import Path
# 创建测试结束后自动清理的合成数据目录。
import tempfile
# 使用标准库测试框架。
import unittest

# 生成可核对证据行序的合成向量。
import numpy as np
# 构造带有非连续索引标签的证据表。
import pandas as pd

# 直接准备缓存状态，独立验证用户编排函数的各个入口分支。
from embedding_cache_io import DocumentEmbeddingCache
# 导入用户已经实现的函数，不改写它的核心逻辑。
from embedding_index import prepare_document_embeddings


# 定义可计数、可模拟失败的编码器，公开配置与现有模型接口一致。
class CountingEncoder:
    # 初始化合成配置；可指定在哪一次调用中模拟模型失败。
    def __init__(self, fail_on_call=None):
        # 虚构模型名称只用于缓存身份，不下载模型。
        self.model_name = "test/synthetic-encoder"
        # 固定虚构版本，满足缓存的可复现配置要求。
        self.model_kwargs = {"device": "cpu", "revision": "fixed-test-revision"}
        # 保留正文归一化和批次配置，供缓存校验使用。
        self.encode_kwargs = {"batch_size": 8, "normalize_embeddings": True, "prompt": ""}
        # 查询参数与文档向量身份分开处理。
        self.query_encode_kwargs = {"prompt": "query-only"}
        # 记录每次实际接收到的正文列表。
        self.calls = []
        # 保存本次测试指定的失败调用序号。
        self.fail_on_call = fail_on_call

    # 为每条合成正文生成不同的单位向量，便于核对输出行序。
    def embed_documents(self, texts):
        # 复制本次输入，避免后续修改影响调用记录。
        self.calls.append(list(texts))
        # 在指定批次模拟推理异常，检查此前断点是否可恢复。
        if len(self.calls) == self.fail_on_call:
            # 模型失败正常向调用者传播，不冒充成功保存。
            raise RuntimeError("simulated encoder failure")
        # 从正文中的编号取得对应向量位置。
        positions = [int(text.split()[-1]) for text in texts]
        # 返回与真实接口相同的二维浮点列表，每行维度固定为 384。
        return np.eye(384, dtype=np.float32)[positions].tolist()


# 定义编码编排与缓存持久化之间的集成测试。
class EmbeddingIndexTests(unittest.TestCase):
    # 为每个测试单独准备输入与缓存目录，避免测试之间互相复用。
    def setUp(self):
        # 创建自动清理的临时目录。
        self.temporary = tempfile.TemporaryDirectory(prefix="embedding-index-check-")
        # 注册清理动作，即使测试失败也会删除合成文件。
        self.addCleanup(self.temporary.cleanup)
        # 将临时目录转换为路径对象。
        self.root = Path(self.temporary.name)
        # 七条证据便于验证三条一批时的单条尾批。
        rows = {"id": [f"T{i}" for i in range(7)], "text": [f"text {i}" for i in range(7)]}
        # 非连续且无序的索引能检查程序是否正确使用 iloc 的行位置。
        self.frame = pd.DataFrame(rows, index=[20, 4, 80, 9, 60, 12, 1])
        # 指定仅包含虚构材料的 JSONL 文件。
        self.evidence_path = self.root / "evidence.jsonl"
        # 为缓存身份提供真实但很小的文件输入。
        self.frame.to_json(self.evidence_path, orient="records", lines=True)
        # 指定本项测试专用缓存根目录。
        self.cache_dir = self.root / "cache"
        # 每条证据的预期向量占用不同维度，且已经 L2 归一化。
        self.expected = np.eye(384, dtype=np.float32)[:7]

    # 使用同一组输入调用用户函数，并捕获进度输出。
    def prepare(self, encoder, chunk_size=3):
        # 进度内容不是这里的验收对象，因此只捕获而不输出。
        with redirect_stdout(StringIO()):
            # 传入真实辅助缓存路径，但编码器只返回合成向量。
            return prepare_document_embeddings(self.frame, encoder, evidence_path=self.evidence_path, cache_dir=self.cache_dir, chunk_size=chunk_size)

    # 独立打开缓存，用于制造部分完成或尚未发布的状态。
    def open_cache(self, encoder):
        # 默认维度为 384，与合成编码器和当前真实模型一致。
        return DocumentEmbeddingCache(self.frame, encoder, evidence_path=self.evidence_path, cache_dir=self.cache_dir)

    # 集中验证完整输出，确保退出 with 后返回的矩阵依然可读。
    def assert_complete_matrix(self, matrix):
        # 输出必须直接使用内存映射，避免额外复制全库矩阵。
        self.assertIsInstance(matrix, np.memmap)
        # 保存数值类型应为既定的 float32。
        self.assertEqual(matrix.dtype, np.dtype("float32"))
        # 完整缓存只允许读取，防止下游误改向量。
        self.assertFalse(matrix.flags.writeable)
        # 逐行核对向量内容，同时检查尾行和证据位置。
        np.testing.assert_array_equal(matrix, self.expected)

    # 验证首次编码的批次边界、尾批及顺序。
    def test_new_cache_batches_tail_and_row_order(self):
        # 创建不会失败的合成编码器。
        encoder = CountingEncoder()
        # 七条输入按三、三、一条分批编码。
        matrix, info = self.prepare(encoder)
        # 核对完整输出的类型、只读性和内容。
        self.assert_complete_matrix(matrix)
        # 每条证据只在正确批次出现一次。
        self.assertEqual(encoder.calls, [["text 0", "text 1", "text 2"], ["text 3", "text 4", "text 5"], ["text 6"]])
        # 首次构建不能被误记为进入时命中完整缓存。
        self.assertFalse(info["cache_hit"])
        # 初始断点应从零开始。
        self.assertEqual(info["initial_completed_rows"], 0)
        # 最终清单必须标记为完整。
        self.assertEqual(info["status"], "complete")

    # 验证完整缓存分支完全跳过正文编码。
    def test_complete_cache_skips_model(self):
        # 先独立建立完整缓存，不依赖被测函数的首次编码分支。
        with self.open_cache(CountingEncoder()) as cache:
            # 保存所有七行正确向量。
            cache.write_batch(0, self.expected)
            # 发布已经完整的缓存。
            cache.finish()
        # 换一个同配置编码器，用空调用记录判断是否重新推理。
        encoder = CountingEncoder()
        # 即使换了外层分块大小，也应复用既有文档向量。
        matrix, info = self.prepare(encoder, chunk_size=2)
        # 读取后的矩阵应与原始数据完全一致。
        self.assert_complete_matrix(matrix)
        # 完整缓存读取时文档模型调用必须为零。
        self.assertEqual(encoder.calls, [])
        # 运行信息应明确标记缓存命中。
        self.assertTrue(info["cache_hit"])

    # 验证中途失败保留成功批次，并只重试未提交的行。
    def test_failed_batch_keeps_checkpoint_and_resumes(self):
        # 在第二批模拟模型失败，第一批应已成功保存。
        failing_encoder = CountingEncoder(fail_on_call=2)
        # 模型异常必须继续抛出，不能伪装成完整矩阵。
        with self.assertRaisesRegex(RuntimeError, "simulated encoder failure"):
            # 触发第一批成功、第二批失败的情况。
            self.prepare(failing_encoder)
        # 直接检查磁盘断点，不只依赖进度打印。
        with self.open_cache(CountingEncoder()) as cache:
            # 只有前三行可以被算作已完成。
            self.assertEqual(cache.completed_rows, 3)
            # 半成品不能被标为完整缓存。
            self.assertFalse(cache.is_complete)
        # 使用相同配置的新编码器恢复。
        resumed_encoder = CountingEncoder()
        # 用户函数应自动从保存的第三行位置继续。
        matrix, info = self.prepare(resumed_encoder)
        # 完成后的七行必须仍然全部正确。
        self.assert_complete_matrix(matrix)
        # 已提交的前三行不能再次编码；失败批次允许重试。
        self.assertEqual(resumed_encoder.calls, [["text 3", "text 4", "text 5"], ["text 6"]])
        # 运行元数据应保留恢复前的真实断点。
        self.assertEqual(info["initial_completed_rows"], 3)
        # 从半成品恢复不算进入时命中完整缓存。
        self.assertFalse(info["cache_hit"])

    # 验证最后一批保存成功但 finish 尚未执行时的恢复。
    def test_all_rows_checkpoint_only_finalizes(self):
        # 制造所有向量都已提交但仍未正式发布的状态。
        with self.open_cache(CountingEncoder()) as cache:
            # 保存全部向量，退出时故意不调用 finish。
            cache.write_batch(0, self.expected)
        # 新编码器用于检查恢复时是否发生多余推理。
        encoder = CountingEncoder()
        # 此时循环应为空，但仍须正常执行 finish。
        matrix, info = self.prepare(encoder)
        # 恢复发布后返回正确的完整矩阵。
        self.assert_complete_matrix(matrix)
        # 全部行已经保存，因此不应再调用模型。
        self.assertEqual(encoder.calls, [])
        # 进入时的断点已经等于总行数。
        self.assertEqual(info["initial_completed_rows"], 7)
        # 最终应发布为完整状态。
        self.assertEqual(info["status"], "complete")

    # 验证查询前缀变化不会触发文档重新编码。
    def test_query_prompt_change_reuses_document_cache(self):
        # 首次构建合成缓存并保存其身份。
        _, first_info = self.prepare(CountingEncoder())
        # 准备相同文档模型配置的新编码器。
        encoder = CountingEncoder()
        # 仅修改查询前缀，不改变文档编码参数。
        encoder.query_encode_kwargs["prompt"] = "a different query prefix"
        # 再次调用用户函数。
        matrix, info = self.prepare(encoder)
        # 文档向量应保持一致。
        self.assert_complete_matrix(matrix)
        # 不应重新编码文档。
        self.assertEqual(encoder.calls, [])
        # 缓存身份必须与首次构建一致。
        self.assertEqual(info["fingerprint"], first_info["fingerprint"])
        # 此次应命中完整缓存。
        self.assertTrue(info["cache_hit"])

    # 验证非法分块参数在建立缓存前被拒绝。
    def test_invalid_chunk_sizes_rejected(self):
        # 零、负数、布尔、小数和字符串都不是合法的正整数配置。
        for value in [0, -1, True, 1.5, "3"]:
            # 分别显示各个参数的失败信息，便于定位回归。
            with self.subTest(value=value):
                # 预期用户函数抛出参数错误。
                with self.assertRaises(ValueError):
                    # 传入不合法的分块大小。
                    self.prepare(CountingEncoder(), chunk_size=value)
        # 参数不合法时不应创建任何向量缓存目录。
        self.assertFalse(self.cache_dir.exists())


# 仅在直接执行测试模块时运行测试并保存本轮验收结果。
if __name__ == "__main__":
    # 根据测试文件位置找到项目根目录，不依赖启动目录。
    project_root = Path(__file__).resolve().parents[1]
    # 指定要绑定指纹的用户核心模块和助手缓存模块。
    checked_paths = [project_root / "embedding_index.py", project_root / "embedding_cache_io.py"]
    # 记录测试开始前的源码指纹。
    before = {str(path.relative_to(project_root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in checked_paths}
    # 只加载本文件定义的六项集成检查。
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(EmbeddingIndexTests)
    # 执行合成测试，不运行真实模型或临床评测。
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    # 复核测试期间受测源码没有被修改。
    after = {str(path.relative_to(project_root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in checked_paths}
    # 保存本次验收的范围、结果和源码指纹，避免误记为 GPU 检索成绩。
    report = {"date": "2026-11-19", "scope": "synthetic embedding orchestration; no real model, CUDA or corpus encoding", "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors), "passed": result.wasSuccessful(), "source_sha256": before, "source_unchanged_during_tests": before == after, "test_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    # 指定独立验证结果，不覆盖此前缓存辅助层测试或检索成绩。
    report_path = project_root / "results" / "embedding_index_validation.json"
    # 确保结果目录存在。
    report_path.parent.mkdir(parents=True, exist_ok=True)
    # 将验收记录保存为 UTF-8 JSON。
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # 失败或测试期间源码变化时返回非零状态，防止误报通过。
    raise SystemExit(0 if result.wasSuccessful() and before == after else 1)

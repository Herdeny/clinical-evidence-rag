# 下面的文档字符串说明本模块、类或函数的用途和适用边界。
"""Meaningful persistence checks; synthetic vectors, no model execution."""

# 导入测试配置的深复制工具。
import copy
# 导入JSON 编解码工具。
import json
# 导入路径对象 Path，便于定位脚本、组合目录并读写文件。
from pathlib import Path
# 导入自动清理的临时目录工具。
import tempfile
# 导入测试框架。
import unittest
# 从 unittest.mock 中的指定接口导入 patch。
from unittest.mock import patch

# 导入数值数组和内存映射工具。
import numpy as np
# 导入表格及 JSONL 读写工具。
import pandas as pd

# 从 embedding_cache_io 中的指定接口导入 DocumentEmbeddingCache。
from embedding_cache_io import DocumentEmbeddingCache


# 定义只提供模型配置的合成编码器，测试时不执行推理。
class ToyEncoder:
    # 定义 __init__：只设置合成模型的公开配置，供缓存测试使用。
    def __init__(self):
        # 设置self.model_name：字符串 'test/synthetic-encoder'。
        self.model_name = 'test/synthetic-encoder'
        # 设置self.model_kwargs：字典，保存device、revision。
        self.model_kwargs = {'device': 'cpu', 'revision': 'fixed-test-revision'}
        # 设置self.encode_kwargs：字典，保存batch_size、normalize_embeddings、prompt。
        self.encode_kwargs = {'batch_size': 8, 'normalize_embeddings': True, 'prompt': ''}
        # 设置self.query_encode_kwargs：字典，保存prompt。
        self.query_encode_kwargs = {'prompt': 'query-only'}

    # 定义 embed_documents：在合成编码器中主动报错，确保纯缓存测试没有调用模型。
    def embed_documents(self, texts):
        # 抛出 AssertionError 并停止当前操作：Persistence must never call the encoder。
        raise AssertionError('Persistence must never call the encoder')


# 定义这一组数据完整性测试用例。
class EmbeddingCacheTests(unittest.TestCase):
    # 定义 setUp：为当前测试创建独立的临时目录和合成材料。
    def setUp(self):
        # 设置self.tmp：创建测试专用临时目录并在结束后清理。
        self.tmp = tempfile.TemporaryDirectory(prefix='embedding-cache-check-')
        # 设置self.root：创建文件路径对象，便于跨目录组合与读写。
        self.root = Path(self.tmp.name)
        # 设置self.frame：调用 pd.DataFrame，取得该步骤的处理结果。
        self.frame = pd.DataFrame({'id': ['A', 'B', 'C'], 'text': ['first', 'second', 'third']}, index=[7, 4, 10])
        # 设置self.path：将目录与右侧子路径组合，得到完整输出位置。
        self.path = self.root / 'evidence.jsonl'
        # 调用 self.frame.to_json，取得该步骤的处理结果。
        self.frame.to_json(self.path, orient='records', lines=True)
        # 设置self.encoder：调用 ToyEncoder，取得该步骤的处理结果。
        self.encoder = ToyEncoder()
        # 设置self.vectors：创建 NumPy 数值数组。
        self.vectors = np.array([[1, 0], [0, 1], [2**-0.5, 2**-0.5]], dtype=np.float32)

    # 定义 tearDown：测试结束后自动清理临时目录。
    def tearDown(self):
        # 调用 self.tmp.cleanup，取得该步骤的处理结果。
        self.tmp.cleanup()

    # 定义 cache：按当前合成语料和编码配置创建待测试的缓存对象。
    def cache(self, frame=None, encoder=None):
        # 返回调用 DocumentEmbeddingCache，取得该步骤的处理结果，结束本次函数调用。
        return DocumentEmbeddingCache(
            # 继续为 DocumentEmbeddingCache 提供本行的参数或输入片段。
            self.frame if frame is None else frame,
            # 继续为 DocumentEmbeddingCache 提供本行的参数或输入片段。
            self.encoder if encoder is None else encoder,
            # 为上方调用传入 evidence_path、cache_dir、dimension 参数；取值按本行指定。
            evidence_path=self.path, cache_dir=self.root / 'cache', dimension=2,
        # 结束上方的函数调用、元组或分组表达式。
        )

    # 定义 test_batch_roundtrip_readonly_mmap_and_reuse：验证分批保存、只读矩阵读取和完整缓存复用。
    def test_batch_roundtrip_readonly_mmap_and_reuse(self):
        # 进入受管理的上下文：按当前合成语料和编码配置创建待测试的缓存对象。
        with self.cache() as cache:
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            self.assertFalse(cache.is_complete)
            # 校验并保存下一段连续向量，落盘成功后更新断点。
            cache.write_batch(0, self.vectors[:2])
            # 校验并保存下一段连续向量，落盘成功后更新断点。
            cache.write_batch(2, self.vectors[2:])
            # 设置处理结果：仅在全部行已保存后发布完整缓存，并返回只读矩阵。
            result = cache.finish()
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            self.assertFalse(cache.info['cache_hit'])
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            self.assertEqual(cache.info['initial_completed_rows'], 0)
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            self.assertIsInstance(result, np.memmap)
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            self.assertEqual(result.dtype, np.dtype('float32'))
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            self.assertFalse(result.flags.writeable)
            # 设置fingerprint：cache.fingerprint。
            fingerprint = cache.fingerprint
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        np.testing.assert_array_equal(result, self.vectors)
        # 进入受管理的上下文：按当前合成语料和编码配置创建待测试的缓存对象。
        with self.cache() as cache:
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            self.assertTrue(cache.is_complete)
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            self.assertTrue(cache.info['cache_hit'])
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            self.assertEqual(cache.completed_rows, 3)
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            self.assertEqual(cache.fingerprint, fingerprint)
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            np.testing.assert_array_equal(cache.load(), self.vectors)
            # 要求下方操作抛出指定异常；没有抛出或类型不符时测试失败。
            with self.assertRaises(RuntimeError):
                # 校验并保存下一段连续向量，落盘成功后更新断点。
                cache.write_batch(0, self.vectors)

    # 定义 test_resume_after_interruption_without_exposing_partial_array：验证编码中断后按断点续写，半成品不能冒充完整缓存。
    def test_resume_after_interruption_without_exposing_partial_array(self):
        # 要求下方操作抛出指定异常；没有抛出或类型不符时测试失败。
        with self.assertRaisesRegex(RuntimeError, 'simulated interruption'):
            # 进入受管理的上下文：按当前合成语料和编码配置创建待测试的缓存对象。
            with self.cache() as cache:
                # 校验并保存下一段连续向量，落盘成功后更新断点。
                cache.write_batch(0, self.vectors[:2])
                # 要求下方操作抛出指定异常；没有抛出或类型不符时测试失败。
                with self.assertRaises(ValueError):
                    # 读取完整且通过校验的向量文件，返回只读内存映射。
                    cache.load()
                # 抛出 RuntimeError 并停止当前操作：simulated interruption。
                raise RuntimeError('simulated interruption')
        # 进入受管理的上下文：按当前合成语料和编码配置创建待测试的缓存对象。
        with self.cache() as cache:
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            self.assertEqual(cache.completed_rows, 2)
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            self.assertEqual(cache.info['initial_completed_rows'], 2)
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            self.assertFalse(cache.info['cache_hit'])
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            self.assertFalse(cache.is_complete)
            # 校验并保存下一段连续向量，落盘成功后更新断点。
            cache.write_batch(2, self.vectors[2:])
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            np.testing.assert_array_equal(cache.finish(), self.vectors)

    # 定义 test_row_order_text_model_and_encoding_settings_invalidate_cache：验证证据与文档配置变化使缓存失效，查询前缀变化则不会。
    def test_row_order_text_model_and_encoding_settings_invalidate_cache(self):
        # 设置original：self.cache().fingerprint。
        original = self.cache().fingerprint
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertNotEqual(original, self.cache(frame=self.frame.iloc[[2, 0, 1]]).fingerprint)
        # 设置changed：调用 self.frame.copy，取得该步骤的处理结果。
        changed = self.frame.copy()
        # 设置changed.loc[7, 'text']：字符串 'changed text'。
        changed.loc[7, 'text'] = 'changed text'
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertNotEqual(original, self.cache(frame=changed).fingerprint)
        # 设置encoder：深复制测试配置，避免修改原对象。
        encoder = copy.deepcopy(self.encoder)
        # 设置encoder.model_kwargs['revision']：字符串 'different-revision'。
        encoder.model_kwargs['revision'] = 'different-revision'
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertNotEqual(original, self.cache(encoder=encoder).fingerprint)
        # 设置encoder：深复制测试配置，避免修改原对象。
        encoder = copy.deepcopy(self.encoder)
        # 设置encoder.encode_kwargs['normalize_embeddings']：常量 False。
        encoder.encode_kwargs['normalize_embeddings'] = False
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertNotEqual(original, self.cache(encoder=encoder).fingerprint)
        # 设置encoder：深复制测试配置，避免修改原对象。
        encoder = copy.deepcopy(self.encoder)
        # 设置encoder.query_encode_kwargs['prompt']：字符串 'new query-only prefix'。
        encoder.query_encode_kwargs['prompt'] = 'new query-only prefix'
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertEqual(original, self.cache(encoder=encoder).fingerprint)

    # 定义 test_input_snapshot_change_is_part_of_identity：验证输入文件字节变化也属于缓存身份变化。
    def test_input_snapshot_change_is_part_of_identity(self):
        # 设置original：self.cache().fingerprint。
        original = self.cache().fingerprint
        # 将给定文本写入指定文件。
        self.path.write_text(self.path.read_text() + '\n')
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertNotEqual(original, self.cache().fingerprint)

    # 定义 test_invalid_batch_does_not_advance_checkpoint：验证非法批次不会更新已完成进度。
    def test_invalid_batch_does_not_advance_checkpoint(self):
        # 进入受管理的上下文：按当前合成语料和编码配置创建待测试的缓存对象。
        with self.cache() as cache:
            # 按顺序遍历[(1, self.vectors[:1]), (0, [[1, 0, 0]]), (0, [[np.nan, 0]]), (0, [[2, 0]]), (0, np.tile([1, 0], (4, 1))…，本轮元素记作 (start, vectors)。
            for start, vectors in [(1, self.vectors[:1]), (0, [[1, 0, 0]]), (0, [[np.nan, 0]]),
                                   # 继续组装上方容器中的本行元素，保持其原始顺序和取值。
                                   (0, [[2, 0]]), (0, np.tile([1, 0], (4, 1)))]:
                # 要求下方操作抛出指定异常；没有抛出或类型不符时测试失败。
                with self.subTest(start=start, vectors=str(vectors)), self.assertRaises(ValueError):
                    # 校验并保存下一段连续向量，落盘成功后更新断点。
                    cache.write_batch(start, vectors)
                # 断言指定结果符合测试预期，不符合则使本项测试失败。
                self.assertEqual(cache.completed_rows, 0)
            # 要求下方操作抛出指定异常；没有抛出或类型不符时测试失败。
            with self.assertRaises(ValueError):
                # 仅在全部行已保存后发布完整缓存，并返回只读矩阵。
                cache.finish()
            # 校验并保存下一段连续向量，落盘成功后更新断点。
            cache.write_batch(0, self.vectors)
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            np.testing.assert_array_equal(cache.finish(), self.vectors)

    # 定义 test_corrupted_complete_file_rejected_without_overwrite：验证完整缓存被损坏后明确拒绝读取且不覆盖证据。
    def test_corrupted_complete_file_rejected_without_overwrite(self):
        # 进入受管理的上下文：按当前合成语料和编码配置创建待测试的缓存对象。
        with self.cache() as cache:
            # 校验并保存下一段连续向量，落盘成功后更新断点。
            cache.write_batch(0, self.vectors)
            # 仅在全部行已保存后发布完整缓存，并返回只读矩阵。
            cache.finish()
            # 设置文件路径：cache.array_path。
            path = cache.array_path
        # 进入受管理的上下文：按指定读写模式打开文件，并在 with 退出时关闭句柄。
        with path.open('r+b') as stream:
            # 调用 stream.seek，取得该步骤的处理结果。
            stream.seek(-1, 2)
            # 设置value：调用 stream.read，取得该步骤的处理结果。
            value = stream.read(1)
            # 调用 stream.seek，取得该步骤的处理结果。
            stream.seek(-1, 2)
            # 将本行给出的完整文本或字节写入已打开的文件，保留指定的分行格式。
            stream.write(bytes([value[0] ^ 1]))
        # 设置damaged：读取指定文件的原始字节。
        damaged = path.read_bytes()
        # 要求下方操作抛出指定异常；没有抛出或类型不符时测试失败。
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            # 进入受管理的上下文：按当前合成语料和编码配置创建待测试的缓存对象。
            with self.cache():
                # 占位语句，不执行额外操作。
                pass
        # 断言指定结果符合测试预期，不符合则使本项测试失败。
        self.assertEqual(path.read_bytes(), damaged)

    # 定义 test_interrupted_publication_recovers_using_recorded_digest：验证发布阶段中断后可依据已保存指纹恢复。
    def test_interrupted_publication_recovers_using_recorded_digest(self):
        # 导入embedding_cache_io 模块。
        import embedding_cache_io
        # 设置original_replace：embedding_cache_io.os.replace。
        original_replace = embedding_cache_io.os.replace
        # 进入受管理的上下文：按当前合成语料和编码配置创建待测试的缓存对象。
        with self.cache() as cache:
            # 校验并保存下一段连续向量，落盘成功后更新断点。
            cache.write_batch(0, self.vectors)
            # 定义 interrupt：模拟向量文件发布时发生中断，以验证之后能够恢复。
            def interrupt(source, destination):
                # 当 Path(destination) == cache.array_path 成立时，执行下面的分支。
                if Path(destination) == cache.array_path:
                    # 抛出 OSError 并停止当前操作：simulated interruption before publication。
                    raise OSError('simulated interruption before publication')
                # 返回调用 original_replace，取得该步骤的处理结果，结束本次函数调用。
                return original_replace(source, destination)
            # 进入受管理的上下文：临时替换被测试的函数，模拟中断或阻止真实外部操作。
            with patch('embedding_cache_io.os.replace', side_effect=interrupt):
                # 要求下方操作抛出指定异常；没有抛出或类型不符时测试失败。
                with self.assertRaises(OSError):
                    # 仅在全部行已保存后发布完整缓存，并返回只读矩阵。
                    cache.finish()
        # 进入受管理的上下文：按当前合成语料和编码配置创建待测试的缓存对象。
        with self.cache() as cache:
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            self.assertTrue(cache.is_complete)
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            np.testing.assert_array_equal(cache.load(), self.vectors)

    # 定义 test_second_writer_is_rejected_and_lock_released：验证并发写入被拒绝，退出后文件锁正常释放。
    def test_second_writer_is_rejected_and_lock_released(self):
        # 进入受管理的上下文：按当前合成语料和编码配置创建待测试的缓存对象。
        with self.cache() as first:
            # 要求下方操作抛出指定异常；没有抛出或类型不符时测试失败。
            with self.assertRaisesRegex(RuntimeError, 'already in use'):
                # 进入受管理的上下文：按当前合成语料和编码配置创建待测试的缓存对象。
                with self.cache():
                    # 占位语句，不执行额外操作。
                    pass
            # 校验并保存下一段连续向量，落盘成功后更新断点。
            first.write_batch(0, self.vectors)
            # 仅在全部行已保存后发布完整缓存，并返回只读矩阵。
            first.finish()
        # 进入受管理的上下文：按当前合成语料和编码配置创建待测试的缓存对象。
        with self.cache() as second:
            # 断言指定结果符合测试预期，不符合则使本项测试失败。
            self.assertTrue(second.is_complete)


# 当 __name__ == '__main__' 成立时，执行下面的分支。
if __name__ == '__main__':
    # 以测试入口运行本文件中的测试用例。
    unittest.main()

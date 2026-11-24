# 检查共享模型输出适配，不加载真实权重或执行GPU推理。
import json
# 为缓存身份检查创建自动清理的目录。
import tempfile
# 使用项目已有的测试框架。
import unittest
# 定位真实静态配置和临时输入文件。
from pathlib import Path
# 替换父类编码结果，保留实际LangChain文档／查询调用路径。
from unittest.mock import patch
# 检查输出矩阵与范数。
import numpy as np
# 构造最小缓存输入表。
import pandas as pd
# 仅用CPU合成张量复现BF16归一化误差。
import torch
# 读取实际父类，避免测试替身改变接口规格。
from langchain_huggingface import HuggingFaceEmbeddings
# 检查缓存是否记录实际输出策略。
from embedding_cache_io import DocumentEmbeddingCache
# 测试本次新增的模型适配辅助。
import embedding_adapter as adapter


# 覆盖数值误差、两种编码入口、策略选择及缓存隔离。
class EmbeddingAdapterTests(unittest.TestCase):
    # 每个测试读取当前受版本管理的模型配置。
    def setUp(self):
        # 仅读取JSON，不调用模型初始化。
        self.profiles = json.loads((Path(__file__).resolve().parents[1] / 'configs/embedding_profiles.json').read_text())

    # 使用真实子类和父类接口，跳过需要下载权重的初始化。
    def make_adapter(self):
        # model_construct创建实际Pydantic对象，不调用模型加载构造逻辑。
        return adapter.Float32L2HuggingFaceEmbeddings.model_construct(**{key: self.profiles['qwen3_8b'][key] for key in ('model_name', 'model_kwargs', 'encode_kwargs', 'query_encode_kwargs')})

    # 正文和查询必须同时修复BF16舍入后的范数偏差。
    def test_bf16_outputs_are_normalized_for_documents_and_query(self):
        # 固定随机种子，以稳定复现先低精度归一化的路径。
        generator = torch.Generator().manual_seed(42)
        # 维度与Qwen一致，样本仅在CPU生成。
        raw = torch.randn(100, 4096, generator=generator).to(torch.bfloat16)
        # 模拟官方Normalize模块及encode各归一化一次。
        rounded = torch.nn.functional.normalize(torch.nn.functional.normalize(raw, dim=1), dim=1).float().numpy()
        # 确认这组样本能触发旧阈值，避免测试只覆盖理想单位向量。
        self.assertFalse(np.allclose(np.linalg.norm(rounded.astype(np.float64), axis=1), 1, rtol=1e-3, atol=1e-5))
        # 保留真实适配器和继承的两个公开编码方法。
        model = self.make_adapter()
        # 仅用合成矩阵替换底层昂贵编码。
        with patch.object(HuggingFaceEmbeddings, '_embed', return_value=rounded.tolist()) as base:
            # 正文公开接口必须经过FP32适配。
            documents = np.asarray(model.embed_documents(['document'] * 100), dtype=np.float32)
            # 独立保存正文摘要，后续query不应改变已取出的字典。
            document_stats = model.last_output_normalization
            # 查询编码返回一行；选择旧范数偏差最大的一行。
            base.return_value = [rounded[np.argmax(np.abs(np.linalg.norm(rounded.astype(np.float64), axis=1) - 1))].tolist()]
            # 通过实际父类embed_query验证同一适配路径。
            query = np.asarray(model.embed_query('original question'), dtype=np.float32)
        # 结果保持完整4096维，不改变批量行序。
        self.assertEqual((documents.shape, query.shape), ((100, 4096), (4096,)))
        # 两类输出均满足原检查器的阈值。
        np.testing.assert_allclose(np.linalg.norm(documents.astype(np.float64), axis=1), 1, rtol=1e-3, atol=1e-5)
        # 查询也必须是单位向量。
        self.assertAlmostEqual(float(np.linalg.norm(query.astype(np.float64))), 1, places=6)
        # 输出摘要保留修复前的真实偏差。
        self.assertGreater(document_stats['before_norm_max'] - document_stats['before_norm_min'], 0.001)
        # 对外记录的策略与缓存策略一致。
        self.assertEqual(document_stats['policy'], 'float32_l2_v1')

    # 数值修复不能把异常模型输出掩盖成合法结果。
    def test_invalid_outputs_still_fail(self):
        # 使用不加载权重的实际适配器。
        model = self.make_adapter()
        # 分别覆盖零向量、NaN、空维度和行数不符。
        for values in ([[0, 0]], [[float('nan'), 1]], [[]], [[1, 0], [0, 1]]):
            # 每种异常必须在进入缓存之前失败。
            with self.subTest(values=values), patch.object(HuggingFaceEmbeddings, '_embed', return_value=values), self.assertRaises(ValueError):
                # 一条输入只允许一行非零有限向量。
                model.embed_documents(['document'])

    # 没有要求归一化时，不改变父类结果。
    def test_unnormalized_call_preserves_parent_output(self):
        # 使用合成对象以跳过模型初始化。
        model = self.make_adapter()
        # 明确设置该次文档调用不归一化。
        model.encode_kwargs = {'normalize_embeddings': False}
        # 非单位向量应原样返回。
        values = [[3.0, 4.0]]
        # 保留真实父子调用链，仅替换推理结果。
        with patch.object(HuggingFaceEmbeddings, '_embed', return_value=values):
            # 未开启归一化的调用不会被策略擅自改变。
            self.assertEqual(model.embed_documents(['document']), values)

    # BGE保留原类，Qwen才使用新的输出策略。
    def test_factory_selects_class_and_preserves_constructor_arguments(self):
        # 分别观察两个构造器的调用。
        with patch.object(adapter, 'HuggingFaceEmbeddings') as native, patch.object(adapter, 'Float32L2HuggingFaceEmbeddings') as normalized:
            # 旧BGE默认使用原生类。
            self.assertIs(adapter.build_embedding_model(self.profiles['bge_small']), native.return_value)
            # Qwen按显式配置使用FP32适配类。
            self.assertIs(adapter.build_embedding_model(self.profiles['qwen3_8b']), normalized.return_value)
            # 项目元数据不应混入真实模型构造参数。
            normalized.assert_called_once_with(**{key: self.profiles['qwen3_8b'][key] for key in ('model_name', 'model_kwargs', 'encode_kwargs', 'query_encode_kwargs')})

    # 无效策略应在占用模型资源前失败。
    def test_unknown_or_asymmetric_policy_fails_before_initialization(self):
        # 从真实Qwen配置复制出测试输入。
        profile = json.loads(json.dumps(self.profiles['qwen3_8b']))
        # 替换两个可能的构造器，确认失败发生在模型加载之前。
        with patch.object(adapter, 'HuggingFaceEmbeddings') as native, patch.object(adapter, 'Float32L2HuggingFaceEmbeddings') as normalized:
            # 策略拼写错误不能静默回退。
            profile['output_normalization'] = 'typo'
            # 拒绝错误策略。
            with self.assertRaises(ValueError):
                # 不调用模型初始化。
                adapter.build_embedding_model(profile)
            # 恢复策略但故意让查询不归一化。
            profile['output_normalization'] = 'float32_l2_v1'
            # 构造两类编码不一致的配置。
            profile['query_encode_kwargs']['normalize_embeddings'] = False
            # 文档和查询必须遵守同一约定。
            with self.assertRaises(ValueError):
                # 不允许只修正文的输出。
                adapter.build_embedding_model(profile)
            # 所有错误都应发生在构造器之前。
            native.assert_not_called()
            # 不占用GPU或读取真实权重。
            normalized.assert_not_called()

    # 适配后的向量不得与原生Qwen向量使用同一缓存身份。
    def test_cache_identity_records_policy_and_isolates_native_outputs(self):
        # 使用会自动清理的小型输入目录。
        with tempfile.TemporaryDirectory(prefix='embedding-adapter-cache-') as directory:
            # 构造一条足够计算有序内容摘要的记录。
            corpus = pd.DataFrame([{'id': 'A', 'text': 'evidence'}])
            # 缓存身份需要绑定原始输入文件。
            evidence_path = Path(directory) / 'corpus.jsonl'
            # 保存微型原始输入，不触碰真实语料。
            evidence_path.write_text('{"id":"A","text":"evidence"}\n')
            # 创建适配后的实际对象，不调用加载器。
            normalized = self.make_adapter()
            # 同一组初始化参数下构造原生对象。
            native = HuggingFaceEmbeddings.model_construct(**{key: self.profiles['qwen3_8b'][key] for key in ('model_name', 'model_kwargs', 'encode_kwargs', 'query_encode_kwargs')})
            # 只计算缓存身份，不打开写入事务。
            normalized_cache = DocumentEmbeddingCache(corpus, normalized, evidence_path=evidence_path, cache_dir=Path(directory) / 'cache', dimension=4096)
            # 计算原生模型输出的身份供对照。
            native_cache = DocumentEmbeddingCache(corpus, native, evidence_path=evidence_path, cache_dir=Path(directory) / 'cache', dimension=4096)
            # 显式保存实际数值策略，便于复核。
            self.assertEqual(normalized_cache.identity['document_config']['output_normalization'], 'float32_l2_v1')
            # 原生配置保持原有字段集合。
            self.assertNotIn('output_normalization', native_cache.identity['document_config'])
            # 两种向量语义不能复用同一目录。
            self.assertNotEqual(normalized_cache.fingerprint, native_cache.fingerprint)


# 单独运行时只做上述无权重验证。
if __name__ == '__main__':
    # 不运行预检、正式基准或任何下载。
    unittest.main()

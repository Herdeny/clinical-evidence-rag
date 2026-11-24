# 验证预检辅助的输入与结果检查，不使用真实GPU或权重。
import json
# 创建自动清理的临时输入。
import tempfile
# 复用标准测试框架。
import unittest
# 捕获正常进度输出。
from contextlib import redirect_stdout
# 存放捕获内容。
from io import StringIO
# 定位项目配置与临时目录。
from pathlib import Path
# 只提供参数元数据，不分配GPU张量。
from types import SimpleNamespace
# 替换模型和CUDA查询。
from unittest.mock import patch
# 生成小型归一化假向量。
import numpy as np
# 构造设备与精度标识不会初始化CUDA。
import torch
# 导入辅助工具，模块导入不得执行预检。
from scripts.evaluation import preflight_embeddings as preflight


# 用字符长度充当可解释的合成分词长度，记录真实调用参数。
class FakeTokenizer:
    # 初始化调用记录。
    def __init__(self):
        # 不加载任何分词器文件。
        self.calls = []
    # 提供与预检实际需要的分词接口一致的返回格式。
    def __call__(self, texts, **kwargs):
        # 复制原输入以便核对换行处理和prompt。
        self.calls.append((list(texts), dict(kwargs)))
        # 字符长度仅用于本测试，不作为真实token统计。
        return {'length': [len(text) for text in texts]}


# 假模型只在CPU生成两三行数组，参数沿用真实配置。
class FakeEmbeddings:
    # 记录预检实际传入的构造参数。
    def __init__(self, **kwargs):
        # 保存文档编码配置。
        self.encode_kwargs = kwargs['encode_kwargs']
        # 保存独立的查询配置。
        self.query_encode_kwargs = kwargs['query_encode_kwargs']
        # 创建无网络分词器替身。
        self.tokenizer = FakeTokenizer()
        # 参数元数据不涉及真实GPU内存。
        parameter = SimpleNamespace(device=torch.device('cuda:0'), dtype=torch.bfloat16)
        # 提供已核查的新API，输出维度对应Qwen静态配置。
        self._client = SimpleNamespace(get_embedding_dimension=lambda: 4096, max_seq_length=8192, tokenizer=self.tokenizer, parameters=lambda: iter([parameter]))
        # 记录实际编码范围。
        self.document_calls, self.query_calls = [], []
    # 为少量正文生成对应维度的单位向量。
    def embed_documents(self, texts):
        # 记录辅助是否只编码样本。
        self.document_calls.append(list(texts))
        # 每个样本对应不同的单位向量。
        return np.eye(len(texts), 4096, dtype=np.float32).tolist()
    # 生成一条查询单位向量。
    def embed_query(self, query):
        # 保留原查询，不能偷偷送入标签。
        self.query_calls.append(query)
        # 使用与文档相同的维度。
        return np.eye(1, 4096, dtype=np.float32)[0].tolist()


# 验证预检报告、样本边界和失败处理。
class EmbeddingPreflightTests(unittest.TestCase):
    # 每个测试独立准备小型输入。
    def setUp(self):
        # 临时目录结束后自动清理。
        temporary = tempfile.TemporaryDirectory(prefix='embedding-preflight-check-')
        # 即使断言失败也清理文件。
        self.addCleanup(temporary.cleanup)
        # 当前测试的工作目录。
        self.root = Path(temporary.name)
        # 配置复制项目真实静态文件。
        self.config_dir = self.root / 'configs'
        # 创建配置目录。
        self.config_dir.mkdir()
        # 原样复制已固定的模型参数。
        (self.config_dir / 'embedding_profiles.json').write_bytes((preflight.ROOT / 'configs/embedding_profiles.json').read_bytes())
        # 建立最小标准BEIR容器。
        self.data_dir = self.root / 'tiny_beir'
        # 标签目录只有当前开发划分。
        (self.data_dir / 'qrels').mkdir(parents=True)
        # 第三篇刻意最长，以证明预检没有只选前两篇。
        corpus = [{'_id': 'A', 'title': '', 'text': 'first'}, {'_id': 'B', 'title': '', 'text': 'second'}, {'_id': 'C', 'title': 'long title', 'text': 'long evidence ' * 20}, {'_id': 'D', 'title': '', 'text': 'unused'}]
        # 两条原始查询都必须参与长度统计。
        queries = [{'_id': 'q1', 'text': 'first question'}, {'_id': 'q2', 'text': 'second question'}]
        # 规范文件按原始容器格式写入。
        for name, rows in [('corpus', corpus), ('queries', queries)]:
            # 每行一条记录。
            (self.data_dir / f'{name}.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
        # 标签只用于读取器筛选当前查询，不传入模型。
        (self.data_dir / 'qrels/dev.tsv').write_text('query-id\tcorpus-id\tscore\nq1\tA\t1\nq2\tB\t1\n', encoding='utf-8')

    # 输入换行、prompt和批次边界必须符合实际封装流程。
    def test_token_lengths_keep_prompt_and_disable_truncation(self):
        # 使用可观察的无网络分词器。
        tokenizer = FakeTokenizer()
        # 65条数据恰好跨越两批。
        lengths = preflight.token_lengths(tokenizer, ['alpha\nbeta'] * 65, 'query\n')
        # prompt里的换行保留，原文里的换行换为空格。
        self.assertEqual(tokenizer.calls[0][0][0], 'query\nalpha beta')
        # 两次调用对应64条及尾部1条。
        self.assertEqual([len(texts) for texts, _ in tokenizer.calls], [64, 1])
        # 测试替身返回可独立计算的字符数。
        self.assertEqual(lengths, [16] * 65)
        # 必须关闭截断和填充，不能把长度上限当作原长度。
        self.assertEqual(tokenizer.calls[0][1], {'padding': False, 'truncation': False, 'return_length': True})

    # 形状、有限性和单位范数均应检查。
    def test_vectors_reject_wrong_shape_nonfinite_or_norm(self):
        # 正确单位向量返回有效摘要。
        self.assertEqual(preflight.check_vectors([[1, 0]], 1, 2)['shape'], [1, 2])
        # 分别检查维度错误、非有限元素和未归一化结果。
        for values in ([[1, 0, 0]], [[float('nan'), 0]], [[2, 0]]):
            # 每个非法输入都必须明确失败。
            with self.subTest(values=values), self.assertRaises(ValueError):
                # 不静默修复模型异常输出。
                preflight.check_vectors(values, 1, 2)

    # 整个辅助流程只编码三篇样本和一条原query，报告范围明确。
    def test_report_uses_real_inputs_and_small_sample_only(self):
        # 创建可观察的假模型工厂。
        models = []
        # 保存真实收到的构造参数。
        def factory(profile):
            # 不下载或加载权重。
            model = FakeEmbeddings(**{key: profile[key] for key in ('model_name', 'model_kwargs', 'encode_kwargs', 'query_encode_kwargs')})
            # 供后续检查编码范围。
            models.append(model)
            # 返回合成接口。
            return model
        # CUDA元数据全部由测试提供，不探测真实设备。
        cuda = {'is_available': lambda: True, 'current_device': lambda: 0, 'reset_peak_memory_stats': lambda device: None, 'synchronize': lambda device: None, 'get_device_name': lambda device: 'synthetic GPU', 'get_device_properties': lambda device: SimpleNamespace(total_memory=1000), 'max_memory_allocated': lambda device: 500, 'max_memory_reserved': lambda device: 600}
        # 同时替换模型构造和所有CUDA调用。
        with patch.object(preflight, 'build_embedding_model', side_effect=factory), patch.multiple(torch.cuda, **cuda), redirect_stdout(StringIO()):
            # 使用真实读取器、静态配置及数值检查。
            report = preflight.run_preflight(self.config_dir, self.data_dir, 'qwen3_8b')
        # 运行状态和实际报告设备均来自本次测试输入。
        self.assertEqual((report['status'], report['actual_device'], report['actual_weight_dtype']), ('passed', 'cuda:0', 'torch.bfloat16'))
        # 所有输入参与长度统计，但只编码最长文档与前两篇。
        self.assertEqual((report['document_count'], report['dev_query_count'], report['sample_document_ids']), (4, 2, ['A', 'B', 'C']))
        # 不构建全库向量，只调用一次正文样本编码。
        self.assertEqual([len(texts) for texts in models[0].document_calls], [3])
        # 查询采用原题第一条。
        self.assertEqual(models[0].query_calls, ['first question'])
        # 样本矩阵和查询维度都必须贯通4096。
        self.assertEqual((report['document_vectors']['shape'], report['query_vectors']['shape']), ([3, 4096], [1, 4096]))
        # 所有参与回查的文件都有对应指纹。
        self.assertEqual(set(report['input_sha256']), {'profiles', 'corpus', 'queries', 'qrels_dev', 'preflight_code'})

    # 没有CUDA时在模型初始化前明确失败。
    def test_missing_gpu_fails_before_model_initialization(self):
        # GPU不可见由测试模拟，避免读取真实环境状态。
        with patch.object(torch.cuda, 'is_available', return_value=False), patch.object(preflight, 'build_embedding_model') as factory:
            # 不允许静默回退CPU运行。
            with self.assertRaisesRegex(RuntimeError, 'GPU terminal'):
                # 只读取当前静态配置。
                preflight.run_preflight(self.config_dir, self.data_dir, 'qwen3_8b')
        # 失败之前不应占用模型加载资源。
        factory.assert_not_called()


# 单独运行时仅执行无权重测试。
if __name__ == '__main__':
    # 标准测试入口不运行任何正式基准。
    unittest.main()

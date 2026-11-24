# 只检查预检工具的数据和调用边界，不加载真实模型或使用GPU。
from copy import deepcopy
# 读取正式静态配置用于构造独立用例。
import json
# 单独核对模块导入保护。
import importlib.util
# 组合临时路径和源码路径。
from pathlib import Path
# 临时配置在用例结束后清理。
import tempfile
# 用属性容器提供已核对的预处理接口。
from types import SimpleNamespace
# 沿用标准测试框架。
import unittest
# 替换GPU可用性和模型构造哨兵。
from unittest.mock import Mock, patch
# 构造真实CPU注意力掩码。
import torch
# 样本查询表与实际容器接口一致。
import pandas as pd
# 使用已实现的冻结候选容器。
from frozen_candidates_io import FrozenCandidates
# 调用本轮实际辅助代码。
from scripts.evaluation import preflight_reranker as preflight


# 检查已说明的联合长度、原始logit与运行边界。
class RerankerPreflightTests(unittest.TestCase):
    # 准备同文不同ID但候选不同的小型输入。
    def make_inputs(self):
        # 两题保留各自ID。
        queries = pd.DataFrame([{'id': '01', 'query': 'same original query'}, {'id': '02', 'query': 'same original query'}])
        # 标签不应进入预处理器。
        qrels = {'01': {'A': 1}, '02': {'C': 1}}
        # 完整正文包含换行，检验不擅自清洗或截断。
        documents = {name: {'id': name, 'text': text} for name, text in {'A': 'short\nbody', 'B': 'middle body', 'C': 'longest body'}.items()}
        # 以问题ID分别关联候选。
        rows = {'01': {'retrieved_ids': ['B', 'A'], 'scores': [0.8, 0.7]}, '02': {'retrieved_ids': ['C', 'B'], 'scores': [0.9, 0.1]}}
        # 直接返回容器，文件核对已由加载器检查覆盖。
        return FrozenCandidates(queries, qrels, documents, rows, {})

    # 长度统计使用真实预处理接口，保留全体句对并选择最长样本。
    def test_scan_preserves_pairs_prompt_and_untruncated_lengths(self):
        # 获取独立的候选输入。
        frozen = self.make_inputs()
        # 人为给出三种长度，避免依赖未运行的真实分词器。
        sizes = {'short\nbody': 10, 'middle body': 20, 'longest body': 45}
        # 记录每次实际输入。
        calls = []
        # 与真实preprocess相同的已核对参数形式。
        def preprocess(pairs, prompt=None, **kwargs):
            # 保存原问题、正文、指令和截断设置。
            calls.append((deepcopy(pairs), prompt, kwargs))
            # 真实接口通过attention_mask表达去除填充后的长度。
            counts = [sizes[text] for _, text in pairs]
            # 当前用例使用CPU张量模拟左填充掩码。
            return {'attention_mask': torch.tensor([[0] * (max(counts) - count) + [1] * count for count in counts])}
        # 该假预处理器明确没有模型权重。
        model = SimpleNamespace(prompts={'query': 'instruction'}, default_prompt_name='query', max_seq_length=40, preprocess=preprocess)
        # 关闭进度显示，保留实际遍历和预处理调用。
        with patch.object(preflight, 'tqdm', side_effect=lambda iterable, **kwargs: iterable):
            # 运行本轮实际长度统计。
            report, samples = preflight.scan_candidate_lengths(model, frozen)
        # 四个句对全部进入分布，最长一对超过当前预算。
        self.assertEqual((report['pair_count'], report['joint_token_min'], report['joint_token_max'], report['pairs_over_limit']), (4, 10, 45, 1))
        # 前两对和真正最长的一对均被选中。
        self.assertEqual([(sample['query_id'], sample['document_id']) for sample in samples], [('01', 'B'), ('01', 'A'), ('02', 'C')])
        # 查询文本相同也不会混淆候选池。
        self.assertEqual([pair for pairs, _, _ in calls for pair in pairs], [('same original query', 'middle body'), ('same original query', 'short\nbody'), ('same original query', 'longest body'), ('same original query', 'middle body')])
        # 指令单独交给预处理器，关闭截断而非先切短正文。
        self.assertTrue(all(prompt == 'instruction' and not kwargs['processing_kwargs']['text']['truncation'] and not kwargs['processing_kwargs']['chat_template']['truncation'] for _, prompt, kwargs in calls))

    # 原始logit允许负数和大于1，结构或有限性错误必须被发现。
    def test_score_check_accepts_raw_logits_and_rejects_bad_arrays(self):
        # 这是可解释假分数，不是模型推理结果。
        report = preflight.check_scores([-14.0, 6.5], 2)
        # 原始值直接保留。
        self.assertEqual(report['scores'], [-14.0, 6.5])
        # 长度、维度与非有限值分别验证。
        for values in ([1.0], [[1.0, 2.0]], [float('nan'), 2.0], [float('inf'), 2.0]):
            # 不根据概率范围限制合法logit。
            with self.subTest(values=values), self.assertRaises(ValueError):
                # 本例预期两项一维有限输出。
                preflight.check_scores(values, 2)

    # 不具备CUDA时应在权重构造前失败，不能偷偷回退CPU。
    def test_missing_cuda_does_not_build_model(self):
        # 仅配置读取需要临时文件。
        with tempfile.TemporaryDirectory() as directory:
            # 定位本项目模型配置。
            profiles = json.loads((Path(__file__).resolve().parents[1] / 'configs/reranker_profiles.json').read_text())
            # 将配置副本写入隔离目录。
            (Path(directory) / 'reranker_profiles.json').write_text(json.dumps(profiles))
            # 来源加载只返回已核对的小型容器，不涉及真实文件。
            with patch.object(preflight, 'load_frozen_candidates', return_value=self.make_inputs()), patch.object(preflight.torch.cuda, 'is_available', return_value=False), patch.object(preflight, 'build_reranker') as build:
                # 不允许宣称CPU运行是CUDA预检通过。
                with self.assertRaises(RuntimeError):
                    # 在模型构造前即会因缺少GPU终止。
                    preflight.run_preflight(Path(directory), Path(directory), Path(directory) / 'receipt.json', 'qwen3_4b')
            # 模型权重构造从未发生。
            self.assertEqual(build.call_count, 0)

    # 导入预检模块不会触发GPU或模型构造。
    def test_import_does_not_start_preflight(self):
        # 使用独立的非__main__模块名。
        specification = importlib.util.spec_from_file_location('reranker_preflight_import_check', Path(preflight.__file__))
        # 为导入创建模块容器。
        module = importlib.util.module_from_spec(specification)
        # 模型构造与GPU调用在导入阶段都不应发生。
        with patch('reranker_adapter.build_reranker') as build, patch.object(torch.cuda, 'set_device') as select_device:
            # 执行真实导入代码。
            specification.loader.exec_module(module)
        # 仅定义函数和导入依赖。
        self.assertEqual((build.call_count, select_device.call_count), (0, 0))


# 本文件可通过标准测试发现方式执行。
if __name__ == '__main__':
    # 所有用例均为CPU辅助检查。
    unittest.main()

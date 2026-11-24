# 验证模型构造参数和重排保存来源，不下载或加载模型权重。
from copy import deepcopy
# 核对落盘结果与配置。
import json
# 为测试提供真实路径与隔离目录。
from pathlib import Path
# 临时文件会在用例结束后自动清理。
import tempfile
# 假打分器只提供已核对的predict接口。
from types import SimpleNamespace
# 沿用标准测试框架。
import unittest
# 仅替换模型构造或打分，不替换用户评分逻辑。
from unittest.mock import Mock, patch
# 用小型真实CPU参数验证实际精度记录。
import torch
# 检查适配器绑定到的真实库签名。
from sentence_transformers import CrossEncoder
# 测试本轮辅助公开接口。
from reranker_adapter import build_reranker, describe_reranker
# 加载真实结构的小型冻结候选。
from frozen_candidates_io import load_frozen_candidates
# 重排与评分仍由用户函数执行。
from benchmark_eval import evaluate_frozen_reranking
# 保存实际三类结果文件。
from retrieval_results_io import save_beir_results
# 复用已有小型文件样本，避免复制另一套输入格式。
from test_frozen_candidates_io import fixture


# 辅助检查只覆盖本轮新增能力。
class RerankingSupportTests(unittest.TestCase):
    # 每次使用同一份受版本管理的模型配置。
    def setUp(self):
        # 通过测试文件位置定位项目。
        self.root = Path(__file__).resolve().parents[1]
        # 明确本轮配置文件位置。
        self.profile_path = self.root / 'configs/reranker_profiles.json'
        # 读取三种正式候选的静态配置。
        self.profiles = json.loads(self.profile_path.read_text())

    # 真实库的构造签名应接受各候选的参数，且配置不被原地修改。
    def test_builder_binds_real_constructor_and_preserves_profile(self):
        # 三个候选都走同一个构造入口。
        for name, profile in self.profiles.items():
            # 显示当前正在核对的模型配置。
            with self.subTest(profile=name):
                # 保留原始嵌套配置。
                before = deepcopy(profile)
                # autospec来自真实CrossEncoder，防止假造不存在的参数。
                with patch('reranker_adapter.CrossEncoder', autospec=CrossEncoder) as constructor:
                    # 不进入真实加载过程。
                    model = build_reranker(profile)
                # 公开函数返回构造器创建的同一模型对象。
                self.assertIs(model, constructor.return_value)
                # 实验配置不应被构造器准备过程改写。
                self.assertEqual(profile, before)
                # 固定版本与离线约定确实传入。
                self.assertEqual(constructor.call_args.kwargs['revision'], profile['revision'])
                # 模型缓存明确位于项目。
                self.assertEqual(Path(constructor.call_args.kwargs['cache_folder']), self.root / 'cache/huggingface/hub')
                # 返回原始分数，不悄悄套用Sigmoid。
                self.assertIsInstance(constructor.call_args.kwargs['activation_fn'], torch.nn.Identity)
                # 参数字典使用副本。
                self.assertIsNot(constructor.call_args.kwargs['model_kwargs'], profile['model_kwargs'])

    # 使用真实小型CPU参数提供可观察属性，不声称加载过候选模型。
    def make_runtime(self):
        # 从正式配置复制，只为元数据用例改成CPU。
        profile = deepcopy(self.profiles['qwen3_4b'])
        # 当前用例明确没有GPU模型。
        profile['device'] = 'cpu'
        # 单参数张量用于核对dtype与device。
        parameter = torch.nn.Parameter(torch.zeros(1, dtype=torch.bfloat16))
        # 属性与真实CrossEncoder公开接口一致。
        model = SimpleNamespace(parameters=lambda: iter([parameter]), max_seq_length=profile['max_length'], activation_fn=torch.nn.Identity(), prompts=deepcopy(profile['prompts']), default_prompt_name=profile['default_prompt_name'])
        # 返回独立的运行描述样本。
        return model, profile

    # 元数据同时保留配置声明与可实际观察的运行属性。
    def test_metadata_records_actual_runtime_and_config_identity(self):
        # 创建没有模型权重的CPU样本。
        model, profile = self.make_runtime()
        # 读取公开元数据接口。
        metadata = describe_reranker(model, profile_name='synthetic-runtime', profile=profile, config_path=self.profile_path)
        # 实际设备与精度由参数得出。
        self.assertEqual((metadata['actual_device'], metadata['actual_weight_dtype']), ('cpu', 'torch.bfloat16'))
        # 保留配置文件与库版本来源。
        self.assertEqual(metadata['profile_file']['path'], str(self.profile_path))
        # 配置中的嵌套内容不会被返回值修改。
        metadata['prompts']['query'] = 'changed output'
        # 原始配置仍是原指令。
        self.assertNotEqual(profile['prompts']['query'], metadata['prompts']['query'])

    # 运行属性与声明不同会改变实验含义，必须如实发现。
    def test_metadata_rejects_runtime_mismatch(self):
        # 只改变当前元数据样本的输入长度。
        model, profile = self.make_runtime()
        # 模拟构造时长度配置没有生效。
        model.max_seq_length = 512
        # 不依赖真实模型或GPU。
        with self.assertRaises(ValueError):
            # 不能把512误写成配置里的4096。
            describe_reranker(model, profile_name='synthetic-runtime', profile=profile, config_path=self.profile_path)

    # 创建完整的小型重排输出及可回查来源。
    def make_result(self, directory):
        # 复用原有同文不同ID文件样本。
        receipt, data, paths = fixture(Path(directory) / 'source')
        # 真正经过加载器恢复正文和候选身份。
        frozen = load_frozen_candidates(receipt, data_dir=data)
        # 每题用同一组可解释假分数反转顺序。
        scorer = SimpleNamespace(predict=Mock(return_value=[-2.0, 3.0]))
        # 关闭输出进度，保留实际评测循环。
        with patch('benchmark_eval.tqdm', side_effect=lambda iterable, **kwargs: iterable):
            # 用户函数计算逐题指标。
            frame, run = evaluate_frozen_reranking(frozen, scorer, ks=(1, 2))
        # 运行元数据明确标记为合成样本。
        model, profile = self.make_runtime()
        # 按后续正式入口同样的层次组织配置。
        config = {'dataset_name': data.name, 'data_dir': str(data), 'split': 'dev', 'retrieval_method': 'frozen_rerank', 'ks': [1, 2], 'candidate_source': frozen.info, 'rerank': describe_reranker(model, profile_name='synthetic-runtime', profile=profile, config_path=self.profile_path)}
        # 输出与源文件同时返回，便于制造来源错误。
        return frame, run, config, paths

    # 保存后能回查原检索来源，计时范围不会冒充端到端。
    def test_rerank_save_roundtrip_preserves_source_and_latency_scope(self):
        # 所有写入都在临时目录。
        with tempfile.TemporaryDirectory() as directory:
            # 得到用户实际计算的临时结果。
            frame, run, config, paths = self.make_result(directory)
            # 保存前记录原检索产物。
            original = {key: path.read_bytes() for key, path in paths.items()}
            # 保存本轮新增方法。
            summary = save_beir_results(frame, run, config=config, run_name='synthetic-rerank', result_dir=Path(directory) / 'out')
            # 结果明确属于冻结候选重排。
            self.assertEqual(summary['retrieval_method'], 'frozen_rerank')
            # 原始来源配置完整保留。
            self.assertEqual(summary['config']['candidate_source'], config['candidate_source'])
            # 计时范围明确排除原Dense检索。
            self.assertIn('excludes source retrieval', summary['latency_ms']['scope'])
            # 标准评分输入与实际输出完全一致。
            self.assertEqual(json.loads(Path(summary['files']['run']).read_text()), run)
            # 原始检索产物未被改写。
            self.assertEqual(original, {key: path.read_bytes() for key, path in paths.items()})

    # 文档即使存在于语料中，也不能被换进另一题的冻结候选。
    def test_save_rejects_document_from_another_query_pool(self):
        # 隔离当前错误样本。
        with tempfile.TemporaryDirectory() as directory:
            # 01题候选为A与B，C只属于另一题。
            frame, run, config, _ = self.make_result(directory)
            # 换入同库但不属于该题的文档C。
            frame.at[0, 'retrieved_ids'] = ['C', 'B']
            # 同步run以避免依赖其他一致性错误触发拒绝。
            run['01'] = dict(zip(frame.at[0, 'retrieved_ids'], frame.at[0, 'scores']))
            # 保存层必须拒绝候选集合变化。
            with self.assertRaises(ValueError):
                # 不保存伪装成重排的新增召回结果。
                save_beir_results(frame, run, config=config, run_name='wrong-pool', result_dir=Path(directory) / 'out')
            # 校验失败前没有输出产物。
            self.assertFalse((Path(directory) / 'out').exists())

    # 加载后源文件变化也不能沿用旧的来源身份保存。
    def test_save_rejects_source_modified_after_loading(self):
        # 模拟并行任务修改原产物。
        with tempfile.TemporaryDirectory() as directory:
            # 先完成合法加载与假重排。
            frame, run, config, paths = self.make_result(directory)
            # 只添加合法空白，保持JSON可解析但改变原始字节。
            paths['run.json'].write_text(paths['run.json'].read_text() + '\n')
            # 保存时仍须重新核对来源。
            with self.assertRaises(ValueError):
                # 不把变化后的文件指向旧哈希。
                save_beir_results(frame, run, config=config, run_name='changed-source', result_dir=Path(directory) / 'out')


# 可从项目测试发现入口独立执行，不接触真实模型。
if __name__ == '__main__':
    # 使用本文件说明的小型输入。
    unittest.main()

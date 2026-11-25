# 检查用户运行入口的实际编排，不下载或加载真实模型。
from contextlib import redirect_stdout
# 复制正式配置到临时测试目录。
from copy import deepcopy
# 单独执行入口以核对导入保护。
import importlib.util
# 捕获CLI输出，不把合成指标当成真实成绩。
import io
# 读取与保存配置及结果。
import json
# 处理实际文件路径。
from pathlib import Path
# 在当前进程执行CLI，保留可观察的调用。
import runpy
# 临时数据随用例结束自动清理。
import tempfile
# 假打分器使用与真实接口一致的属性。
from types import SimpleNamespace
# 使用项目已有测试框架。
import unittest
# 只替换模型加载和输出显示。
from unittest.mock import Mock, patch
# 真实CPU张量用于元数据读取，不代表加载过模型。
import torch
# 读取用户已经保存的运行入口。
import run_reranking_eval as entry
# 复用同文不同ID的既有文件样本。
from test_frozen_candidates_io import fixture


# 所有检查对应本轮已说明的入口行为。
class RerankingEntryTests(unittest.TestCase):
    # 每项检查创建独立输入，避免覆盖真实实验。
    def setUp(self):
        # 当前项目根目录。
        self.root = Path(__file__).resolve().parents[1]
        # 创建可自动清理的测试空间。
        temporary = tempfile.TemporaryDirectory(prefix='reranking-entry-')
        # 测试结束时清理临时文件。
        self.addCleanup(temporary.cleanup)
        # 保存临时目录路径。
        self.directory = Path(temporary.name)
        # 真实格式的小型候选描述文件、语料与检索产物。
        self.receipt, self.data, _ = fixture(self.directory / 'source')
        # 临时模型配置位于另一个明确的目录。
        self.config_dir = self.directory / 'configs'
        # 创建测试配置目录。
        self.config_dir.mkdir()
        # 沿用正式配置的所有字段。
        profiles = json.loads((self.root / 'configs/reranker_profiles.json').read_text())
        # 本用例的实际权重只是CPU单参数，不伪装成CUDA加载。
        for profile in profiles.values():
            # 只在临时配置中明确改为CPU。
            profile['device'] = 'cpu'
        # 写入临时配置文件，describe_reranker实际读取该文件。
        (self.config_dir / 'reranker_profiles.json').write_text(json.dumps(profiles), encoding='utf-8')
        # 保存模型构造器实际创建的假打分器。
        self.scorers = []
        # 隐藏进度条但保留真实评分循环。
        progress = patch('benchmark_eval.tqdm', side_effect=lambda iterable, **kwargs: iterable)
        # 本用例启用显示替代。
        progress.start()
        # 用例结束恢复原进度条。
        self.addCleanup(progress.stop)

    # 假打分器仅替代真实权重，其他加载／描述／评分／保存均使用项目代码。
    def build_scorer(self, profile):
        # 单参数精度与临时配置一致。
        weight = torch.nn.Parameter(torch.zeros(1, dtype=torch.bfloat16))
        # 每题候选两条，假分数用于核对完整链路。
        predict = Mock(side_effect=lambda pairs, **kwargs: [float(index) for index in range(len(pairs))])
        # 提供describe_reranker与rerank真正使用的属性。
        scorer = SimpleNamespace(parameters=lambda: iter([weight]), max_seq_length=profile['max_length'], activation_fn=torch.nn.Identity(), prompts=deepcopy(profile['prompts']), default_prompt_name=profile['default_prompt_name'], predict=predict)
        # 保存实际创建对象供检查调用次数。
        self.scorers.append(scorer)
        # 返回无真实模型权重的打分器。
        return scorer

    # 导入入口模块不应创建模型或自动运行评测。
    def test_import_does_not_start_work(self):
        # 使用非__main__名称执行用户原文件。
        specification = importlib.util.spec_from_file_location('reranking_entry_import_check', self.root / 'run_reranking_eval.py')
        # 创建独立模块对象。
        module = importlib.util.module_from_spec(specification)
        # 哨兵对应入口可能调用的实际依赖。
        with patch('reranker_adapter.build_reranker') as build, patch('frozen_candidates_io.load_frozen_candidates') as load, patch('benchmark_eval.evaluate_frozen_reranking') as evaluate, patch('retrieval_results_io.save_beir_results') as save:
            # 执行顶层导入与函数定义。
            specification.loader.exec_module(module)
        # 四个运行步骤均不应在导入时发生。
        self.assertEqual([build.call_count, load.call_count, evaluate.call_count, save.call_count], [0, 0, 0, 0])

    # 三种profile都能共用入口，显式名称覆盖默认名称。
    def test_main_roundtrip_default_and_explicit_names(self):
        # 每种候选分别检查默认名与用户指定名。
        for profile_name in ('qwen3_4b', 'qwen3_8b', 'bge_v2_m3'):
            # 名称不引入时间戳或自动编号规则。
            for supplied_name in (None, 'chosen_experiment_02'):
                # 不同调用使用不同结果目录。
                output = self.directory / f'out-{profile_name}-{supplied_name}'
                # 仅替换权重加载；describe、用户评测和保存都实际执行。
                with self.subTest(profile=profile_name, run_name=supplied_name), patch.object(entry, 'build_reranker', side_effect=self.build_scorer) as build:
                    # 显式传入六项运行参数。
                    summary = entry.main(self.config_dir, self.data, self.receipt, profile_name, supplied_name, output)
                # 每轮只创建一次模型。
                self.assertEqual(build.call_count, 1)
                # 当前两道题各调用一次predict。
                self.assertEqual(self.scorers[-1].predict.call_count, 2)
                # 直接读取用例配置，核对批次透传，不把过去的batch1写死。
                expected_batch_size = json.loads((self.config_dir / 'reranker_profiles.json').read_text())[profile_name]['batch_size']
                # 实际predict参数应来自配置，而非函数默认16或测试偏好的常量。
                self.assertTrue(all(call.kwargs['batch_size'] == expected_batch_size for call in self.scorers[-1].predict.call_args_list))
                # 查询和候选预算保持当前样本的真实规模。
                self.assertEqual(summary['query_count'], 2)
                # 模型profile被完整带入记录。
                self.assertEqual(summary['config']['rerank']['profile_name'], profile_name)
                # 指纹来自配置文件而不是配置目录。
                self.assertEqual(summary['config']['rerank']['profile_file']['path'], str(self.config_dir / 'reranker_profiles.json'))
                # 原候选来源保持可回查。
                self.assertEqual(summary['config']['candidate_source']['source_run_name'], 'synthetic-source')
                # 原数据的划分决定本轮划分。
                self.assertEqual(summary['split'], 'dev')
                # 默认命名只拼接原有字段，显式名称优先。
                expected_name = supplied_name or f'tiny_beir_rerank_{profile_name}_dev'
                # 保存器实际使用了正确名称和结果目录。
                self.assertEqual(Path(summary['files']['summary']), output / f'{expected_name}_summary.json')
                # 实际写出的摘要与返回值一致。
                self.assertEqual(json.loads(Path(summary['files']['summary']).read_text()), summary)

    # 终端六个参数能够传到对应main参数，而非依赖默认值碰巧正确。
    def test_cli_maps_explicit_paths_profile_and_name(self):
        # 特意选择非默认模型、名称和带空格的输出路径。
        output = self.directory / 'cli output'
        # 按真实CLI选项准备参数列表。
        arguments = ['run_reranking_eval.py', '--config', str(self.config_dir), '--data-dir', str(self.data), '--receipt', str(self.receipt), '--profile', 'qwen3_8b', '--run-name', 'cli_experiment_03', '--result-dir', str(output)]
        # 捕获最终打印的合成指标。
        printed = io.StringIO()
        # 模型构造替身位于入口真正导入的模块，其他步骤仍实际执行。
        with patch('sys.argv', arguments), patch('reranker_adapter.build_reranker', side_effect=self.build_scorer) as build, redirect_stdout(printed):
            # 执行真实命令行分支。
            namespace = runpy.run_path(str(self.root / 'run_reranking_eval.py'), run_name='__main__')
        # CLI只创建一个模型。
        self.assertEqual(build.call_count, 1)
        # 显式profile覆盖默认4B。
        self.assertEqual(namespace['summary']['config']['rerank']['profile_name'], 'qwen3_8b')
        # 显式结果目录和实验名都生效。
        self.assertTrue((output / 'cli_experiment_03_summary.json').is_file())
        # CLI打印指标而非模型对象。
        self.assertIn('ndcg_at_10', printed.getvalue())

    # 原输入错误应在模型构造前暴露，无需新增核心校验分支。
    def test_invalid_source_or_profile_does_not_load_model(self):
        # 未知配置和缺失描述文件分别依赖原生错误。
        cases = [('unknown-profile', self.receipt, KeyError), ('qwen3_4b', self.directory / 'missing.json', FileNotFoundError)]
        # 每次只破坏一种输入。
        for profile_name, receipt, expected_error in cases:
            # 不规定统一异常名称，保留实际语义。
            with self.subTest(profile=profile_name), patch.object(entry, 'build_reranker') as build, self.assertRaises(expected_error):
                # 调用用户原有读取流程。
                entry.main(self.config_dir, self.data, receipt, profile_name, 'invalid-input', self.directory / 'unused')
            # 无效输入没有进入GPU模型加载。
            self.assertEqual(build.call_count, 0)


# 支持项目标准的测试发现方式。
if __name__ == '__main__':
    # 本文件全部使用临时数据及假打分器。
    unittest.main()

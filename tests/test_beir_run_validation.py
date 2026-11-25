# 检查离线核验能适配已有入口，不执行真实模型。
from copy import deepcopy
# 写入临时结果和资源记录。
import json
# 记录评分包的真实版本。
from importlib.metadata import version
# 处理临时文件路径。
from pathlib import Path
# 每项检查隔离结果目录。
import tempfile
# 假打分器只提供predict接口。
from types import SimpleNamespace
# 使用标准测试框架。
import unittest
# 关闭进度条，不替换实际评测或评分器。
from unittest.mock import Mock, patch
# 加载标准格式的临时冻结候选。
from frozen_candidates_io import load_frozen_candidates
# 调用用户已有评测函数。
from benchmark_eval import evaluate_frozen_reranking
# 保存真实结构的三类结果。
from retrieval_results_io import save_beir_results
# 核对本轮实际修改的离线工具。
from scripts.evaluation.validate_beir_run import validate_run, validate_rerank_reference, file_sha
# 复用既有临时数据文件结构。
from test_frozen_candidates_io import fixture


# 所有检查只涉及记录和重新评分。
class BeirRunValidationTests(unittest.TestCase):
    # 创建合法小型结果和对应运行前回执。
    def prepare_run(self, directory, method='frozen_rerank'):
        # 当前用例的根目录。
        directory = Path(directory)
        # 源文件与结果文件使用不同目录。
        receipt, data, _ = fixture(directory / 'source')
        # 实际加载原文与候选关联。
        frozen = load_frozen_candidates(receipt, data_dir=data)
        # 假分数用于产生可回查的排序输入。
        scorer = SimpleNamespace(predict=Mock(return_value=[0.0, 1.0]))
        # 逐题评分仍由用户函数和真实pytrec_eval执行。
        with patch('benchmark_eval.tqdm', side_effect=lambda iterable, **kwargs: iterable):
            # 保留两题全部候选。
            frame, run = evaluate_frozen_reranking(frozen, scorer)
        # 本用例的模型身份明确为合成记录。
        model_info = {'model_name': 'synthetic-scorer', 'revision': 'synthetic-fixed', 'device': 'cpu', 'max_length': 4096, 'batch_size': 1, 'score_type': 'synthetic', 'actual_device': 'cpu', 'actual_weight_dtype': 'float32', 'actual_max_length': 4096}
        # 方法布局与项目保存接口一致。
        config = {'dataset_name': data.name, 'data_dir': str(data), 'split': 'dev', 'retrieval_method': method, 'ks': [10, 100], 'candidate_source': frozen.info, 'rerank': model_info, 'bm25': {'model_name': 'synthetic-bm25', 'device': 'cpu', 'query_prefix': ''}}
        # 区分各个临时实验名称。
        name = f'synthetic-{method}'
        # 保存待核验的真实格式产物。
        summary = save_beir_results(frame, run, config=config, run_name=name, result_dir=directory / 'output')
        # 以实际结果路径定位资源与审计文件。
        output = Path(summary['files']['summary']).parent
        # 新旧入口各有自己的合法CLI协议。
        command = f'python run_reranking_eval.py --profile qwen3_4b --run-name {name}' if method == 'frozen_rerank' else f'python run_benchmark_eval.py --method {method} --run-name {name}'
        # 资源文件只模拟已知结构，不声称做过模型运行。
        (output / f'{name}_resources.txt').write_text(f'Command being timed: "{command}"\nElapsed (wall clock) time (h:mm:ss or m:ss): 0:01.00\nMaximum resident set size (kbytes): 1024\nExit status: 0\n')
        # 用户入口最终打印的是摘要指标字典。
        (output / f'{name}_run.log').write_text(str(summary['metrics']) + '\n')
        # 用当前真实用户入口作为独立源码快照。
        snapshot = directory / 'snapshot'
        # 创建临时快照目录。
        snapshot.mkdir()
        # 当前核验工具的项目根目录可由测试文件位置确定。
        entry_path = Path(__file__).resolve().parents[1] / 'run_reranking_eval.py'
        # 保留实际源码内容。
        (snapshot / entry_path.name).write_bytes(entry_path.read_bytes())
        # 回执在核验前固定，模型元数据与候选来源均使用副本。
        audit = {'run_name': name, 'method': method, 'dataset_name': data.name, 'split': 'dev', 'document_count': 3, 'query_count': 2, 'qrel_pairs': 2, 'ks': [10, 100], 'packages': {'pytrec-eval-terrier': version('pytrec-eval-terrier')}, 'input_sha256': summary['input_sha256'], 'code_snapshot': str(snapshot), 'code_sha256': {entry_path.name: file_sha(entry_path)}, 'expected_candidate_source': deepcopy(frozen.info), 'expected_rerank': deepcopy(model_info), 'reranker_profile': 'qwen3_4b', 'expected_latency_scope': summary['latency_ms']['scope']}
        # 保存与正式运行相同的审计文件名。
        (output / f'{name}_run_audit.json').write_text(json.dumps(audit))
        # 返回直接或整体核验所需对象。
        return name, output, frame.to_dict(orient='records'), audit, config

    # 新入口按profile核对，旧BM25按method核对，均使用同一评分器。
    def test_rerank_and_legacy_run_artifacts_validate(self):
        # 每种方法独立保存，避免互相覆盖。
        for method in ('frozen_rerank', 'bm25'):
            # 当前测试仍不执行任何真实检索模型。
            with self.subTest(method=method), tempfile.TemporaryDirectory() as directory:
                # 生成完整的微型结果集。
                name, output, _, _, _ = self.prepare_run(directory, method)
                # 调用完整离线核验，包括独立重新评分。
                validation = validate_run(name, checked_on='2026-11-25', result_dir=output)
                # 两个入口的合法命令都能通过。
                self.assertEqual(validation['status'], 'passed')
                # 只有冻结重排应产生候选集合检查结果。
                self.assertEqual(validation['frozen_rerank_reference_check'] is not None, method == 'frozen_rerank')

    # 同语料中的另一篇文档仍不能冒充该题原候选。
    def test_changed_candidate_pool_is_rejected(self):
        # 不修改真实实验。
        with tempfile.TemporaryDirectory() as directory:
            # 原01题只有A和B。
            _, _, rows, audit, config = self.prepare_run(directory)
            # 替换成同库另一题的C。
            rows[0]['retrieved_ids'] = ['C', 'B']
            # 核验来源集合，不能只检查文档在语料中存在。
            with self.assertRaises(AssertionError):
                # 不调用任何模型重算分数。
                validate_rerank_reference(rows, audit, config)

    # 完整运行的模型配置必须与预检固定版本一致。
    def test_changed_model_recipe_is_rejected(self):
        # 使用临时来源和结果。
        with tempfile.TemporaryDirectory() as directory:
            # 获得启动前独立元数据副本。
            _, _, rows, audit, config = self.prepare_run(directory)
            # 模拟运行后改成不同输入预算。
            config['rerank']['max_length'] = 512
            # 拒绝把另一套配置写成本轮实验。
            with self.assertRaises(AssertionError):
                # 只核对实际记录。
                validate_rerank_reference(rows, audit, config)

    # 资源文件中的模型选择也须对应当前实验。
    def test_wrong_profile_in_resource_command_is_rejected(self):
        # 所有写入都位于临时目录。
        with tempfile.TemporaryDirectory() as directory:
            # 原回执固定的是4B配置。
            name, output, _, _, _ = self.prepare_run(directory)
            # 只改变资源命令，其他结果仍自洽。
            path = output / f'{name}_resources.txt'
            # 模拟贴错另一个模型的资源文件。
            path.write_text(path.read_text().replace('--profile qwen3_4b', '--profile qwen3_8b'))
            # 整体核验应发现这一次实际命令身份不匹配。
            with self.assertRaises(AssertionError):
                # 不让用户修改CLI去迎合旧核验参数。
                validate_run(name, checked_on='2026-11-25', result_dir=output)


# 可通过项目标准测试发现命令运行。
if __name__ == '__main__':
    # 不读取真实完整运行结果，不使用GPU。
    unittest.main()

# 验证运行配置分组保存、旧布局兼容和输入不变，不运行检索。
"""Persistence checks for grouped and legacy retrieval metadata."""

# 检查保存函数是否改变调用者配置。
from copy import deepcopy
# 捕获测试输出的临时文件位置。
from contextlib import redirect_stdout
# 提供输出缓冲。
from io import StringIO
# 读取真正保存到磁盘的配置。
import json
# 组合测试专用路径。
from pathlib import Path
# 测试后自动清理数据和输出。
import tempfile
# 使用标准库测试框架。
import unittest

# 创建已经计算好的虚构评测表。
import pandas as pd

# 仅测试助手提供的保存辅助，不调用模型或评分函数。
from retrieval_results_io import save_retrieval_results


# 定义分组布局与旧平铺布局的持久化检查。
class RetrievalResultsIOTests(unittest.TestCase):
    # 每个测试使用独立临时目录。
    def setUp(self):
        # 创建仅含虚构材料的临时工作目录。
        temporary = tempfile.TemporaryDirectory(prefix='retrieval-io-check-')
        # 测试失败也会执行清理。
        self.addCleanup(temporary.cleanup)
        # 保存路径对象。
        self.root = Path(temporary.name)
        # 指定五条合成证据的文件。
        self.evidence_path = self.root / 'evidence.jsonl'
        # 指定一条合成开发题的文件。
        self.cases_path = self.root / 'cases.jsonl'
        # 生成满足Top-5保存约定的五个不同ID。
        self.identifiers = list('ABCDE')
        # 保存只供输入指纹和ID验证使用的材料。
        pd.DataFrame([{'id': identifier, 'text': f'synthetic {identifier}'} for identifier in self.identifiers]).to_json(self.evidence_path, orient='records', lines=True)
        # 构造标准字段齐全的虚构开发题。
        case = {'id': 'CASE-1', 'split': 'dev', 'group': 'synthetic', 'report': 'synthetic report', 'question': 'synthetic question', 'gold_evidence_ids': ['A'], 'gold_evidence_groups': [['A']]}
        # 保存用于核对题号的输入文件。
        pd.DataFrame([case]).to_json(self.cases_path, orient='records', lines=True)
        # 评测结果中的题号字段名与原题不同。
        row = {key: value for key, value in case.items() if key != 'id'}
        # 给出已经计算好的合成命中和计时，不在I/O测试中重新评分。
        row.update(case_id='CASE-1', retrieved_ids=self.identifiers, scores=[.9, .8, .7, .6, .5], latency_ms=1.0)
        # 六个合成指标均为一，A始终位于第一条。
        row.update({f'{kind}_at_{k}': 1.0 for kind in ('canonical_recall', 'group_recall') for k in (1, 3, 5)})
        # 转换为保存接口所需的结果表。
        self.frame = pd.DataFrame([row])

    # 创建与模型无关的公共配置。
    def common(self, method):
        # 顶层只保存输入、模板、语料与方法选择。
        return {'cases_path': str(self.cases_path), 'evidence_path': str(self.evidence_path), 'query_template': 'Report: {report}\nQuestion: {question}', 'corpus_name': 'synthetic', 'retrieval_method': method}

    # 每次返回新对象，防止测试之间共享元数据。
    def metadata(self, name):
        # 模型或检索实现信息可以属于自己的方法层。
        return {'model_name': name, 'device': 'cpu', 'query_prefix': ''}

    # 创建两路完整分组配置。
    def grouped_rrf(self):
        # 先创建公共输入配置。
        config = self.common('rrf')
        # 为两路分别保存模型或实现信息。
        config.update(dense=self.metadata('synthetic-encoder'), bm25=self.metadata('synthetic-bm25'), rrf={'candidate_k': 20, 'rrf_constant': 60})
        # 返回尚未保存的调用者配置。
        return config

    # 统一保存并验证配置原样保留。
    def save_and_check(self, config, run_name):
        # 保存输入配置的独立副本。
        original = deepcopy(config)
        # 捕获临时文件位置打印。
        with redirect_stdout(StringIO()):
            # 真实验证并保存，不通过适配器伪造结果。
            summary = save_retrieval_results(self.frame, config, run_name=run_name, result_dir=self.root / 'results')
        # 保存操作不能修改调用者对象。
        self.assertEqual(config, original)
        # 返回摘要应保留原布局。
        self.assertEqual(summary['config'], original)
        # 从真正的磁盘文件回读。
        saved = json.loads((self.root / 'results' / f'{run_name}_summary.json').read_text())
        # 磁盘布局也必须完全一致，不能偷偷扁平化或补假字段。
        self.assertEqual(saved['config'], original)
        # 证据与题目计数仍应正确。
        self.assertEqual((saved['evidence_count'], saved['case_count']), (5, 1))

    # 验证既有的三种平铺配置仍可保存。
    def test_legacy_flat_layout(self):
        # 保留对既有接口支持的方法范围。
        for method in ('dense', 'bm25', 'rrf'):
            # 各方法单独展示结果。
            with self.subTest(method=method):
                # 模拟历史调用者的顶层模型字段。
                config = self.common(method)
                # 历史字段仍保持原位置。
                config.update(self.metadata(f'legacy-{method}'))
                # 不要求重写旧调用者或旧产物。
                self.save_and_check(config, f'legacy_{method}')

    # 验证单路方法自己的分组配置。
    def test_grouped_single_method_layout(self):
        # 两种单路方法使用相同的结构原则。
        for method in ('dense', 'bm25'):
            # 各分支独立检查。
            with self.subTest(method=method):
                # 顶层只含公共信息。
                config = self.common(method)
                # 模型名和设备放在方法子项中。
                config[method] = self.metadata(f'grouped-{method}')
                # 新布局不需要冗余全局模型名。
                self.assertNotIn('model_name', config)
                # 验证该结构可原样持久化。
                self.save_and_check(config, f'grouped_{method}')

    # 验证RRF分别保存两路元数据和融合参数。
    def test_grouped_rrf_layout(self):
        # 使用完整两路分组结构。
        config = self.grouped_rrf()
        # 组合方法不要求一个全局模型名。
        self.assertNotIn('model_name', config)
        # 两路各自保留原始字段。
        self.save_and_check(config, 'grouped_rrf')

    # 验证缺失方法信息时错误能定位到具体层。
    def test_missing_method_metadata_reports_section(self):
        # 构造Dense缺少模型名的输入。
        config = self.common('dense')
        # 其余两个字段存在，避免错误含糊。
        config['dense'] = {'device': 'cpu', 'query_prefix': ''}
        # 报错应指出Dense分组及模型名。
        with self.assertRaisesRegex(ValueError, r'config\.dense.*model_name'):
            # 验证发生在写文件前。
            self.save_and_check(config, 'missing_dense_name')
        # 构造RRF缺少BM25分组的输入。
        config = self.grouped_rrf()
        # 只移除一条路线。
        del config['bm25']
        # 不能把不完整分组静默当成其他方法。
        with self.assertRaisesRegex(ValueError, r'config\.bm25'):
            # 报错必须指向缺失的实际路线。
            self.save_and_check(config, 'missing_bm25')

    # 验证新布局记录的融合参数仍有基本有效性约束。
    def test_invalid_grouped_rrf_parameters(self):
        # 保持与查询函数一致的正整数约定。
        for value in (0, -1, True, 1.5):
            # 每个参数独立核对。
            for name in ('candidate_k', 'rrf_constant'):
                # 为失败信息保留具体键和值。
                with self.subTest(name=name, value=value):
                    # 每组使用独立输入。
                    config = self.grouped_rrf()
                    # 只修改一个字段。
                    config['rrf'][name] = value
                    # 错误应保留融合参数路径。
                    with self.assertRaisesRegex(ValueError, f'config.rrf.{name}'):
                        # 不允许把无效值作为可信运行记录。
                        self.save_and_check(config, 'invalid_rrf')

    # 验证方法分组不会放松公共输入信息要求。
    def test_missing_common_input_field(self):
        # 取得方法信息齐全的配置。
        config = self.grouped_rrf()
        # 缺少输入路径仍然无法形成可回查结果。
        del config['cases_path']
        # 应在打开文件前给出缺失字段。
        with self.assertRaisesRegex(ValueError, 'cases_path'):
            # 新结构仍须具有公共输入来源。
            self.save_and_check(config, 'missing_cases')

# 用临时数据检验三个入口分支和CLI传参，不加载真实模型。
"""Entry integration checks with real retrieval/evaluation/I/O and a fake model."""

# 提取实际CLI代码块，只替换最终main调用以检验参数传递。
import ast
# 捕获合成缓存和保存函数的终端输出。
from contextlib import redirect_stdout
# 记录本轮验收的实际UTC时间。
from datetime import datetime, timezone
# 保存受测代码指纹。
import hashlib
# 按实际main签名核对CLI调用，不强制用户采用某种位置参数顺序。
import inspect
# 为捕获输出提供内存缓冲。
from io import StringIO
# 保存结构化验收记录。
import json
# 处理临时数据与项目路径。
from pathlib import Path
# 读取CLI参数解析所用的原始标准库。
import argparse
# 自动清理合成证据、缓存和结果。
import tempfile
# 使用标准库测试框架。
import unittest
# 替换模型加载并统计资源初始化次数。
from unittest.mock import Mock, patch

# 生成可核对的单位向量，不使用GPU。
import numpy as np
# 构造实际入口会读取的JSONL数据。
import pandas as pd

# 导入用户入口；导入本身不读取正式语料。
import run_retrieval_eval as entry

# 定位项目根目录。
ROOT = Path(__file__).resolve().parents[1]
# 收集各方法实际初始化次数和保存配置，用于诊断失败。
OBSERVATIONS = []


# 定义与真实封装具有相同公开属性的合成模型。
class SyntheticModel:
    # 接收入口实际传入的全部模型配置。
    def __init__(self, **kwargs):
        # 保留模型标识，用于真实缓存身份计算。
        self.model_name = kwargs['model_name']
        # 保留设备和固定版本，但不实际加载任何权重。
        self.model_kwargs = kwargs['model_kwargs']
        # 保留文档编码参数。
        self.encode_kwargs = kwargs['encode_kwargs']
        # 保留查询编码参数。
        self.query_encode_kwargs = kwargs['query_encode_kwargs']

    # 根据合成正文编号返回不同的384维单位向量。
    def embed_documents(self, texts):
        # 与真实接口一样返回二维浮点列表。
        return np.eye(384, dtype=np.float32)[[int(text.split()[-1]) for text in texts]].tolist()

    # 两道虚构查询都与第零条证据匹配。
    def embed_query(self, text):
        # 只返回合成向量，不访问模型API。
        return np.eye(384, dtype=np.float32)[0].tolist()


# 检验真实入口的资源选择、评分、保存与CLI边界。
class RetrievalEntryTests(unittest.TestCase):
    # 每个测试使用独立临时目录，避免覆盖原始成绩。
    def setUp(self):
        # 创建自动清理的合成数据目录。
        temporary = tempfile.TemporaryDirectory(prefix='retrieval-entry-check-')
        # 即使测试失败也执行清理。
        self.addCleanup(temporary.cleanup)
        # 保存本项测试的临时根目录。
        self.root = Path(temporary.name)
        # 指定合成证据路径。
        self.evidence_path = self.root / 'evidence.jsonl'
        # 指定合成题路径。
        self.cases_path = self.root / 'cases.dev.jsonl'
        # 七条证据足够支持Top-5及候选不足的实际检索。
        evidence = pd.DataFrame([{'id': f'T{i}', 'text': f'text {i}', 'source_id': 'synthetic', 'locator': f'row {i}'} for i in range(7)])
        # 保存小型JSONL，供用户main实际读取。
        evidence.to_json(self.evidence_path, orient='records', lines=True)
        # 查询使用字母后缀，避免题号数字意外成为BM25匹配词。
        reports = ['synthetic report alpha', 'synthetic report beta']
        # 构造两道虚构开发题，与真实留出和MIRAGE无关。
        cases = pd.DataFrame([{'id': f'TEST-{i}', 'split': 'dev', 'group': 'synthetic', 'report': reports[i], 'question': 'synthetic question', 'gold_evidence_ids': ['T0'], 'gold_evidence_groups': [['T0']]} for i in range(2)])
        # 保存合成题目。
        cases.to_json(self.cases_path, orient='records', lines=True)
        # 保留真实保存函数，只重定向输出目录。
        real_save = entry.save_retrieval_results
        # 将临时输出目录保存在闭包中。
        output = self.root / 'results'
        # 不修正配置内容，让真实保存契约检查用户传入的数据。
        def save_temporary(result_df, config, *, run_name=None, result_dir=None):
            # 真实验证并保存到临时目录，禁止覆盖正式成绩。
            return real_save(result_df, config, run_name=run_name, result_dir=output)
        # 仅替换真实模型工厂，其他主要实现均保留。
        self.model = self.start_patch('HuggingFaceEmbeddings', side_effect=SyntheticModel)
        # 保留真实缓存I/O，同时统计入口调用次数。
        self.prepare = self.start_patch('prepare_document_embeddings', wraps=entry.prepare_document_embeddings)
        # 保留小语料真实BM25，同时统计建索引次数。
        self.build = self.start_patch('build_bm25', wraps=entry.build_bm25)
        # 使用真实评分函数，并核对仅执行一次。
        self.evaluate = self.start_patch('evaluate_retrieval', wraps=entry.evaluate_retrieval)
        # 使用真实保存校验，只改变输出位置。
        self.save = self.start_patch('save_retrieval_results', side_effect=save_temporary)

    # 统一启动测试替换，并确保结束后恢复原对象。
    def start_patch(self, name, **kwargs):
        # 创建针对入口命名空间的替换。
        patcher = patch.object(entry, name, **kwargs)
        # 启动替换并取得可计数对象。
        value = patcher.start()
        # 注册恢复操作，避免测试之间互相影响。
        self.addCleanup(patcher.stop)
        # 返回包装后的调用对象。
        return value

    # 对指定方法走完整main，不跳过实际错误。
    def check_method(self, method):
        # 为每种方法使用独立且明确的合成运行名。
        run_name = f'synthetic_{method}'
        # 无论成功还是失败，都保存真实初始化与配置观测。
        try:
            # 捕获进度与临时路径输出。
            with redirect_stdout(StringIO()):
                # 按名称传参，接受用户自洽的main参数顺序。
                summary = entry.main(method=method, cache_dir=self.root / 'cache', cases_path=self.cases_path, evidence_path=self.evidence_path, run_name=run_name)
        # 记录事实不吞掉异常，测试框架仍会报告失败。
        finally:
            # 读取实际传给保存函数的配置；未到保存阶段时记为空。
            config = self.save.call_args.kwargs['config'] if self.save.call_args else {}
            # 公共输入信息放在顶层，模型和设备信息保留在实际方法层。
            required = {'evidence_path', 'cases_path', 'query_template'}
            # 保存实际分支执行情况，便于定位首个错误阻断后的状态。
            OBSERVATIONS.append({'method': method, 'model_factory_calls': self.model.call_count, 'cache_prepare_calls': self.prepare.call_count, 'bm25_build_calls': self.build.call_count, 'evaluate_calls': self.evaluate.call_count, 'save_calls': self.save.call_count, 'top_level_config_keys': sorted(config), 'missing_required_top_level_fields': sorted(required - config.keys())})
        # 成功返回后核对初始化数量。
        self.assertEqual(self.model.call_count, int(method in ('dense', 'rrf')))
        # 文档缓存只在有Dense的分支中准备一次。
        self.assertEqual(self.prepare.call_count, int(method in ('dense', 'rrf')))
        # BM25仅在需要的分支构建一次。
        self.assertEqual(self.build.call_count, int(method in ('bm25', 'rrf')))
        # 每轮只评测一次。
        self.assertEqual(self.evaluate.call_count, 1)
        # 每轮只保存一次。
        self.assertEqual(self.save.call_count, 1)
        # 实际题目与证据数量应来自临时输入。
        self.assertEqual((summary['case_count'], summary['evidence_count']), (2, 7))
        # 三种方法都应保留真实方法标识。
        self.assertEqual(summary['retrieval_method'], method)
        # 语料身份必须留在顶层，不能触发保存函数默认的ct_v2名称。
        self.assertEqual(summary['config']['corpus_name'], 'medical_v3')
        # 摘要所属阶段也必须对应真实语料与方法。
        self.assertEqual(summary['stage'], f'medical_v3-{method}-baseline')
        # RRF记录必须使用与实际调用一致的候选数和平滑常量名称。
        if method == 'rrf':
            # 接受独立rrf子配置，也兼容直接保存在顶层的布局。
            rrf_config = summary['config'].get('rrf', summary['config'])
            # 本轮预先固定每路二十条候选。
            self.assertEqual(rrf_config['candidate_k'], 20)
            # 本轮预先固定平滑常量六十。
            self.assertEqual(rrf_config['rrf_constant'], 60)
        # 所有合成查询都有同一个明确的第一名标注。
        self.assertTrue(all(value == 1.0 for value in summary['metrics'].values()))
        # 必须实际生成本次指定名称的结果文件。
        self.assertTrue((self.root / 'results' / f'{run_name}_results.jsonl').is_file())
        # 同时必须生成可回读的摘要。
        self.assertTrue((self.root / 'results' / f'{run_name}_summary.json').is_file())

    # 检验Dense独立分支。
    def test_dense_entry(self):
        # 不创建真实GPU模型。
        self.check_method('dense')

    # 检验BM25独立分支。
    def test_bm25_entry(self):
        # 仅索引七条虚构证据。
        self.check_method('bm25')

    # 检验两路资源同时存在的RRF分支。
    def test_rrf_entry(self):
        # 使用真实融合和评分，不修改用户入口。
        self.check_method('rrf')

    # 执行实际CLI代码块，但用假main阻止读取正式数据。
    def run_cli(self, arguments):
        # 读取当前实际入口语法树。
        tree = ast.parse((ROOT / 'run_retrieval_eval.py').read_text())
        # 取最后一个顶层if，即__main__入口块。
        guard = next(node for node in reversed(tree.body) if isinstance(node, ast.If))
        # 只编译CLI代码，不重新定义或执行main本体。
        launcher = compile(ast.Module(body=guard.body, type_ignores=[]), str(ROOT / 'run_retrieval_eval.py'), 'exec')
        # 假main返回CLI所需的最小摘要。
        fake_main = Mock(return_value={'metrics': {'synthetic': 0}})
        # 提供CLI实际使用的名称。
        namespace = {'__file__': str(ROOT / 'run_retrieval_eval.py'), 'argparse': argparse, 'Path': Path, 'main': fake_main}
        # 替换参数并捕获最后的打印。
        with patch('sys.argv', ['run_retrieval_eval.py', *arguments]), redirect_stdout(StringIO()):
            # 执行原始CLI参数解析与传递。
            exec(launcher, namespace)
        # 最终main应只调用一次。
        fake_main.assert_called_once()
        # 按用户实际函数签名还原位置参数的意义。
        return inspect.signature(entry.main).bind(*fake_main.call_args.args, **fake_main.call_args.kwargs).arguments

    # 检验默认路径、方法与结果名称。
    def test_cli_defaults(self):
        # 不传参数，读取当前实际默认值。
        bound = self.run_cli([])
        # 维持默认Dense行为。
        self.assertEqual(bound['method'], 'dense')
        # 默认题集应从脚本根目录定位。
        self.assertEqual(bound['cases_path'], ROOT / 'data/v3/cases.ct.dev.jsonl')
        # 默认证据应指向冻结v3输入。
        self.assertEqual(bound['evidence_path'], ROOT / 'data/v3/evidence.jsonl')
        # 默认缓存路径应保持现有位置。
        self.assertEqual(bound['cache_dir'], ROOT / 'cache/embeddings')
        # 默认结果名延续已约定格式。
        self.assertEqual(bound['run_name'], 'medical_v3_dense_ct_dev')

    # 检验自定义评测路径和RRF运行名传递。
    def test_cli_custom_paths_and_name(self):
        # 这些路径只用于参数解析，不会读取正式数据。
        cache = self.root / 'custom-cache'
        # 指定用户实现的全部可配置路径。
        arguments = ['--method', 'rrf', '--cache', str(cache), '--cases', str(self.cases_path), '--evidences', str(self.evidence_path), '--run-name', 'synthetic_cli']
        # 解析并还原真实main参数映射。
        bound = self.run_cli(arguments)
        # 检查方法、路径类型与运行名全部一致。
        self.assertEqual(dict(bound), {'method': 'rrf', 'cache_dir': cache, 'cases_path': self.cases_path, 'evidence_path': self.evidence_path, 'run_name': 'synthetic_cli'})


# 直接运行时保存验收结果，普通测试发现模式不额外写文件。
if __name__ == '__main__':
    # 保存运行前入口源码字节。
    source = (ROOT / 'run_retrieval_eval.py').read_bytes()
    # 加载本文件的五项集成检查。
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(RetrievalEntryTests)
    # 输出每项检查的实际状态。
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    # 核对没有改写或混入并发更新的用户代码。
    unchanged = source == (ROOT / 'run_retrieval_eval.py').read_bytes()
    # 单独检查RRF参数绑定，避免资源错误掩盖参数拼写问题。
    tree = ast.parse(source.decode())
    # 取得入口实际创建RRF partial的表达式。
    rrf_partial = next(node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'partial' and node.args and isinstance(node.args[0], ast.Name) and node.args[0].id == 'retrieve_rrf')
    # 根据真实retrieve_rrf签名找出不支持的关键字。
    unsupported = [keyword.arg for keyword in rrf_partial.keywords if keyword.arg not in inspect.signature(entry.retrieve_rrf).parameters]
    # 保存失败和成功事实，不把诊断误写成真实模型成绩。
    report = {'validated_at_utc': datetime.now(timezone.utc).isoformat(), 'scope': 'temporary synthetic data; fake model; real cache/BM25/retrieval/evaluation/saving; CLI launcher uses fake main; no production data or GPU', 'tests_run': result.testsRun, 'failure_count': len(result.failures), 'error_count': len(result.errors), 'passed': result.wasSuccessful() and unchanged and not unsupported, 'source_unchanged': unchanged, 'source_sha256': hashlib.sha256(source).hexdigest(), 'source_text': source.decode(), 'observations': OBSERVATIONS, 'unsupported_rrf_partial_keywords': unsupported, 'failures': [{'test': test.id(), 'traceback': details} for test, details in result.failures], 'errors': [{'test': test.id(), 'traceback': details} for test, details in result.errors], 'test_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    # 保存到独立记录，不覆盖历史Dense或RRF函数验收。
    path = ROOT / 'results' / 'retrieval_entry_validation.json'
    # 留存当前入口实际代码和核验范围。
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    # 输出精简的诊断，完整追踪保存在JSON中。
    print(json.dumps({'passed': report['passed'], 'observations': OBSERVATIONS, 'unsupported_rrf_partial_keywords': unsupported}, ensure_ascii=False, indent=2))
    # 失败时返回非零退出状态。
    raise SystemExit(0 if report['passed'] else 1)

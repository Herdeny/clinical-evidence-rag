# 验证已说明的文件身份、查询ID关联和候选副本，不加载模型。
from copy import deepcopy
# 保存微型JSON输入和冻结回执。
import json
# 使用真实有限值和NaN构造关联检查。
import hashlib
# 定位自动清理的测试输入。
from pathlib import Path
# 每个用例独立准备文件，不触碰真实基线。
import tempfile
# 沿用标准库测试框架。
import unittest
# 假打分器只提供predict接口。
from types import SimpleNamespace
# 记录真实rerank接收的句对。
from unittest.mock import Mock
# 测试本轮辅助和用户已实现的重排函数之间的衔接。
from frozen_candidates_io import load_frozen_candidates
# 不创建真实CrossEncoder，只使用用户的纯函数。
from rerank_core import rerank


# 保存JSON文件，便于制造独立的关联错误。
def write_json(path, value):
    # 测试只在临时目录中写入。
    path.write_text(json.dumps(value, ensure_ascii=False) + '\n', encoding='utf-8')


# 根据当前三个原始产物更新测试回执，用于区分哈希错误和内容关联错误。
def refresh_receipt(path):
    # 保留回执的查询数和候选预算。
    receipt = json.loads(path.read_text())
    # 只有测试主动修改产物时才刷新其摘要。
    for metadata in receipt['files'].values():
        # 测试回执故意采用相对路径，验证便携读取。
        source = path.parent / metadata['path']
        # 记录当前实际内容。
        metadata['sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    # 保存重新绑定的测试回执。
    write_json(path, receipt)


# 两条文字相同、ID不同的查询必须取回各自候选。
def fixture(directory):
    # 文档和标注使用标准BEIR容器。
    data = Path(directory) / 'tiny_beir'
    # 创建标签目录。
    (data / 'qrels').mkdir(parents=True)
    # 文档正文含换行，确认加载器不擅自改写原文。
    corpus = [{'_id': 'A', 'title': 'alpha title', 'text': 'alpha\nbody'}, {'_id': 'B', 'title': '', 'text': 'beta body'}, {'_id': 'C', 'title': 'Gamma', 'text': 'gamma body'}]
    # 无标签查询放在前面，检验非连续行标签和正确ID关联。
    queries = [{'_id': 'unused', 'text': 'unused'}, {'_id': '01', 'text': 'same original query?'}, {'_id': '02', 'text': 'same original query?'}]
    # 写入原始JSONL。
    for name, records in (('corpus', corpus), ('queries', queries)):
        # 保持每行一条记录。
        (data / f'{name}.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in records))
    # 标签只用于评测查询筛选，不进入候选内容。
    (data / 'qrels/dev.tsv').write_text('query-id\tcorpus-id\tscore\n01\tA\t1\n02\tC\t2\n')
    # 逐题文件刻意与查询表顺序相反。
    rows = [{'query_id': '02', 'query': 'same original query?', 'retrieved_ids': ['C', 'B'], 'scores': [0.8, -0.2]}, {'query_id': '01', 'query': 'same original query?', 'retrieved_ids': ['B', 'A'], 'scores': [0.9, 0.0]}]
    # 三个冻结产物放在回执旁边。
    paths = {name: Path(directory) / name for name in ('results.jsonl', 'run.json', 'summary.json')}
    # 保存原先顺序和原检索分数。
    paths['results.jsonl'].write_text(''.join(json.dumps(row) + '\n' for row in rows))
    # 标准run按查询ID组织。
    write_json(paths['run.json'], {row['query_id']: dict(zip(row['retrieved_ids'], row['scores'])) for row in rows})
    # 摘要记录本测试输入身份，未宣称真实模型成绩。
    summary = {'dataset_name': data.name, 'split': 'dev', 'retrieval_method': 'dense', 'document_count': 3, 'query_count': 2, 'config': {'model_name': 'synthetic-source'}, 'metrics': {'recall_at_100': 1.0}, 'latency_ms': {'mean': 2.0, 'median': 2.0, 'scope': 'synthetic fixture'}, 'input_sha256': {key: {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for key, path in {'corpus': data / 'corpus.jsonl', 'queries': data / 'queries.jsonl', 'qrels': data / 'qrels/dev.tsv'}.items()}}
    # 保存摘要。
    write_json(paths['summary.json'], summary)
    # 冻结预算为最多两条，后续也检验合法空候选。
    receipt = {'source_run_name': 'synthetic-source', 'query_count': 2, 'candidates_per_query': 2, 'total_pairs': 4, 'same_candidate_set_requires_recall_at_100': 1.0, 'files': {name: {'path': name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for name, path in paths.items()}}
    # 返回实际加载入口。
    receipt_path = Path(directory) / 'frozen.json'
    # 保存回执。
    write_json(receipt_path, receipt)
    # 用普通字典返回测试路径，方便各个用例独立修改。
    return receipt_path, data, paths


# 所有检查对应文件冻结、关联准确和实验输入独立这三个目的。
class FrozenCandidatesTests(unittest.TestCase):
    # 初始化相同格式的微型冻结输入。
    def setUp(self):
        # 不读取或修改真实基线。
        temporary = tempfile.TemporaryDirectory(prefix='frozen-candidate-check-')
        # 用例结束自动删除临时文件。
        self.addCleanup(temporary.cleanup)
        # 保存可重复创建独立案例的根目录。
        self.root = Path(temporary.name)
        # 当前测试的合法输入。
        self.receipt, self.data, self.paths = fixture(self.root / 'base')

    # 相同问题文字必须依靠query_id区分，正文和分数按文档ID对应。
    def test_id_association_full_text_and_rerank_integration(self):
        # 只读加载。
        frozen = load_frozen_candidates(self.receipt, data_dir=self.data)
        # ID保留前导零，顺序来自原始查询表。
        self.assertEqual(frozen.queries_df['id'].tolist(), ['01', '02'])
        # 两道查询文字完全相同，候选却不能混用。
        self.assertEqual([hit['id'] for hit in frozen.get_hits('01')], ['B', 'A'])
        # 第二题保留独立候选顺序。
        self.assertEqual([hit['id'] for hit in frozen.get_hits('02')], ['C', 'B'])
        # 原始0分及负分均合法。
        self.assertEqual([hit['score'] for hit in frozen.get_hits('01')], [0.9, 0.0])
        # 原文标题拼接和换行沿用原读取器。
        self.assertEqual(frozen.get_hits('01')[1]['text'], 'alpha title alpha\nbody')
        # 保留源文档和定位元数据。
        self.assertEqual(frozen.get_hits('01')[1]['locator'], {'dataset': 'tiny_beir', 'document_id': 'A'})
        # 同一对象可直接给用户的rerank纯函数使用。
        model = SimpleNamespace(predict=Mock(return_value=[0.1, 0.8]))
        # 不使用任何标签或真实模型决定假分数。
        ranked = rerank('same original query?', frozen.get_hits('01'), 2, reranker=model)
        # 原始零分正确保存在重排结果里。
        self.assertEqual((ranked[0]['id'], ranked[0]['retrieval_score']), ('A', 0.0))
        # 调用模型时只有原query和候选正文。
        model.predict.assert_called_once_with([('same original query?', 'beta body'), ('same original query?', 'alpha title alpha\nbody')], batch_size=16, show_progress_bar=False, convert_to_numpy=True)

    # 结果及元数据副本不能污染下一轮模型实验。
    def test_returned_copies_and_source_files_stay_independent(self):
        # 保存加载前的所有测试文件字节。
        before = {str(path): path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        # 加载同一冻结输入。
        frozen = load_frozen_candidates(self.receipt, data_dir=self.data)
        # 修改返回的嵌套来源对象。
        frozen.get_hits('01')[0]['locator']['document_id'] = 'wrong'
        # 修改返回的独立查询表。
        queries = frozen.queries_df
        # 不能改变内部原query。
        queries.loc[queries.index[0], 'query'] = 'changed'
        # 修改返回的标签副本。
        labels = frozen.qrels
        # 不应污染内部标签。
        labels['01'].clear()
        # 修改返回元数据同样不得改变冻结预算。
        frozen.info['candidate_k'] = 999
        # 后续读取仍恢复原始文档定位。
        self.assertEqual(frozen.get_hits('01')[0]['locator']['document_id'], 'B')
        # 查询、标签和预算仍为原值。
        self.assertEqual((frozen.queries_df.iloc[0]['query'], frozen.qrels['01'], frozen.info['candidate_k']), ('same original query?', {'A': 1}, 2))
        # 辅助没有改写任何文件。
        self.assertEqual(before, {str(path): path.read_bytes() for path in self.root.rglob('*') if path.is_file()})

    # 产物仍是合法JSON，仅字节改变也必须报告冻结身份不符。
    def test_changed_source_artifacts_are_rejected(self):
        # 三种源产物分别检查。
        for name in self.paths:
            # 每种场景使用独立输入。
            receipt, data, paths = fixture(self.root / name)
            # 添加合法空白，不依赖JSON解析失败碰巧拒绝。
            paths[name].write_text(paths[name].read_text() + '\n')
            # 必须由内容身份检查拒绝。
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Frozen source changed'):
                # 不刷新回执，模拟文件被改动。
                load_frozen_candidates(receipt, data_dir=data)

    # 文档、查询或当前qrels改变时，不继续沿用旧候选。
    def test_changed_dataset_inputs_are_rejected(self):
        # 独立验证三类输入身份。
        for name in ('corpus.jsonl', 'queries.jsonl', 'qrels/dev.tsv'):
            # 每种场景创建完整输入。
            receipt, data, _ = fixture(self.root / name.replace('/', '-'))
            # 添加空白以保留原语义，检验实际字节冻结约定。
            (data / name).write_text((data / name).read_text() + '\n')
            # 由数据身份检查拒绝，而非后续评分报错。
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Frozen dataset input changed'):
                # 不启动模型或读取向量。
                load_frozen_candidates(receipt, data_dir=data)

    # 即使哈希重新绑定，题目、候选和run的内容关联也必须一致。
    def test_inconsistent_associations_are_rejected(self):
        # 每种改动只破坏一个已说明的关联条件。
        for case in ('query_text', 'duplicate_query', 'missing_query', 'unknown_document', 'duplicate_document', 'score_count', 'run_score', 'nonfinite_score'):
            # 使用独立输入，避免前一个错误掩盖下一个。
            receipt, data, paths = fixture(self.root / case)
            # 解析测试数据。
            rows = [json.loads(line) for line in paths['results.jsonl'].read_text().splitlines()]
            # 解析独立标准run。
            run = json.loads(paths['run.json'].read_text())
            # 改变query文字会破坏原查询身份。
            if case == 'query_text':
                # 不允许把改写后的query称为同一冻结问题。
                rows[0]['query'] = 'rewritten'
            # 重复题号不能冒充完整覆盖。
            elif case == 'duplicate_query':
                # 复制整行，保留结构合法性。
                rows.append(deepcopy(rows[0]))
            # 丢题也不可改变分母。
            elif case == 'missing_query':
                # 删掉一题但不修改真实queries。
                rows.pop()
            # 候选ID必须存在于原始语料。
            elif case == 'unknown_document':
                # 未知文档仍是合法字符串。
                rows[0]['retrieved_ids'][0] = 'UNKNOWN'
            # 一个查询内的候选不可重复。
            elif case == 'duplicate_document':
                # 两条分数对应了同一个文档ID。
                rows[0]['retrieved_ids'][1] = rows[0]['retrieved_ids'][0]
            # 候选与分数必须等长。
            elif case == 'score_count':
                # 删掉一项分数。
                rows[0]['scores'].pop()
            # 独立run必须指向相同分数。
            elif case == 'run_score':
                # 保留逐题记录，只改标准run。
                run['02']['C'] = 99.0
            # JSON允许的NaN仍不能成为模型分数。
            else:
                # 测试有限性检查。
                rows[0]['scores'][0] = float('nan')
            # 保存修改后的合法结构。
            paths['results.jsonl'].write_text(''.join(json.dumps(row) + '\n' for row in rows))
            # 同步写入独立run。
            write_json(paths['run.json'], run)
            # 主动更新产物哈希，确保这次验证的是内容关联。
            refresh_receipt(receipt)
            # 任一种关联错误都应拒绝加载。
            with self.subTest(case=case), self.assertRaises(ValueError):
                # 不依赖真实模型或文件哈希旧值触发错误。
                load_frozen_candidates(receipt, data_dir=data)

    # 合法空候选仍保留对应查询和标签。
    def test_empty_candidates_keep_query_and_denominator(self):
        # 修改其中一题为空候选。
        rows = [json.loads(line) for line in self.paths['results.jsonl'].read_text().splitlines()]
        # 第一行是02题，将其候选清空。
        rows[0].update(retrieved_ids=[], scores=[])
        # 保存空候选记录。
        self.paths['results.jsonl'].write_text(''.join(json.dumps(row) + '\n' for row in rows))
        # 标准run保留空查询键。
        write_json(self.paths['run.json'], {row['query_id']: dict(zip(row['retrieved_ids'], row['scores'])) for row in rows})
        # 摘要基线召回率随空题变为0.5。
        summary = json.loads(self.paths['summary.json'].read_text())
        # 两题仍都计入分母。
        summary['metrics']['recall_at_100'] = 0.5
        # 保存测试摘要。
        write_json(self.paths['summary.json'], summary)
        # 总候选数减少，但查询数不变。
        receipt = json.loads(self.receipt.read_text())
        # 两条候选只来自另一题。
        receipt.update(total_pairs=2, same_candidate_set_requires_recall_at_100=0.5)
        # 保存更新后的测试回执。
        write_json(self.receipt, receipt)
        # 绑定当前测试产物。
        refresh_receipt(self.receipt)
        # 加载合法空候选。
        frozen = load_frozen_candidates(self.receipt, data_dir=self.data)
        # 不丢题、不丢标签。
        self.assertEqual((frozen.get_hits('02'), len(frozen.queries_df), len(frozen.qrels)), ([], 2, 2))
        # 明确记录实际候选分布。
        self.assertEqual(frozen.info['candidate_count_distribution'], {'0': 1, '2': 1})


# 独立执行时仅测试上述文件关联行为。
if __name__ == '__main__':
    # 不加载模型或运行公开基准评分。
    unittest.main()

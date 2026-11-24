# 只读取已保存的候选及原文，不加载模型、向量矩阵或执行检索。
from collections import Counter
# 返回候选副本，避免一次重排改变下一次实验的输入。
from copy import deepcopy
# 核对实际使用的源文件内容。
import hashlib
# 解析冻结回执、摘要、逐题结果和标准run。
import json
# 检查原始相关性分数是否有限。
from math import isfinite
# 解析显式传入的数据和回执路径。
from pathlib import Path
# 复用用户已实现的BEIR读取和标题拼接规则。
from benchmark_data import load_beir_dataset


# 流式读取内容指纹，不复制大型输入文件。
def _sha256(path):
    # 每个文件独立计算摘要。
    digest = hashlib.sha256()
    # 原始产物只读打开。
    with Path(path).open('rb') as stream:
        # 每批最多读取1MiB。
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            # 累加本批实际字节。
            digest.update(block)
    # 返回可回查的摘要。
    return digest.hexdigest()


# 保存一次已核对的冻结输入，对外按查询ID提供候选副本。
class FrozenCandidates:
    # 初始化只接受加载器已核对的数据，不执行任何模型调用。
    def __init__(self, queries, qrels, documents, rows, info):
        # 私有保存原始查询顺序。
        self._queries = queries
        # 标签只供评测，不混入候选文本或打分输入。
        self._qrels = qrels
        # 文档按ID保存一次，各题不重复存储正文。
        self._documents = documents
        # 每题仅保存原始候选顺序和原始分数。
        self._rows = rows
        # 保存模型来源、数据指纹及冻结身份。
        self._info = info

    # 对外返回独立查询表，调用方不会修改内部原始输入。
    @property
    # 查询表沿用现有评测所需的id和query字段。
    def queries_df(self):
        # 非连续行标签和原始顺序均保留。
        return self._queries.copy(deep=True)

    # 标签仅由评测函数接收。
    @property
    # 不把可变标签字典直接暴露给调用方。
    def qrels(self):
        # 每次提供独立副本。
        return deepcopy(self._qrels)

    # 元数据用于后续保存和复核来源。
    @property
    # 返回JSON可保存的信息，不包含模型对象。
    def info(self):
        # 避免入口组装配置时修改冻结身份。
        return deepcopy(self._info)

    # 按查询ID联结文档，不能用可能重复的问题文字作为键。
    def get_hits(self, query_id):
        # 未知ID由字典自然报告KeyError，保留具体查询身份。
        row = self._rows[query_id]
        # 只创建当前这一题的候选副本。
        hits = []
        # 保留原始候选顺序及其对应分数。
        for identifier, score in zip(row['retrieved_ids'], row['scores']):
            # 保留正文、source_id、嵌套locator及其他原始文档字段。
            hit = deepcopy(self._documents[identifier])
            # score始终表示本次冻结的原始检索分数。
            hit['score'] = score
            # 不将qrels或相关性等级放入候选。
            hits.append(hit)
        # 返回值可直接传给用户已实现的rerank。
        return hits


# 从冻结回执恢复同一批查询、候选与原文，data_dir必须明确提供。
def load_frozen_candidates(receipt_path, *, data_dir):
    # 以回执位置解析相对产物路径。
    receipt_path = Path(receipt_path).resolve()
    # 记录用户实际传入的数据目录。
    data_dir = Path(data_dir).resolve()
    # 冻结回执只读解析。
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    # 三个原始产物共同说明候选、分数及来源配置。
    paths = {}
    # 不接受只检查条数而忽略原始文件是否改变。
    for name in ('results.jsonl', 'run.json', 'summary.json'):
        # 从回执取得对应文件的身份。
        metadata = receipt['files'][name]
        # 回执也可以使用相对自身的文件路径。
        path = Path(metadata['path'])
        # 绝对路径保持原样，相对路径按回执目录展开。
        path = path if path.is_absolute() else receipt_path.parent / path
        # 文件内容不匹配时停止，不能混入另一轮结果。
        if _sha256(path) != metadata['sha256']:
            # 异常说明具体被替换的产物。
            raise ValueError(f'Frozen source changed: {path}')
        # 保存实际解析到的路径。
        paths[name] = path.resolve()
    # 读取原始摘要，不改写模型或评分参数。
    summary = json.loads(paths['summary.json'].read_text(encoding='utf-8'))
    # 使用摘要声明的划分，不偷偷切到测试集。
    split = summary['split']
    # 数据身份核对覆盖语料、原查询以及当前划分标签。
    inputs = {'corpus': data_dir / 'corpus.jsonl', 'queries': data_dir / 'queries.jsonl', 'qrels': data_dir / 'qrels' / f'{split}.tsv'}
    # 允许目录搬迁，但文件内容必须与原实验相同。
    for name, path in inputs.items():
        # 不因目录名相同就认定是同一批材料。
        if _sha256(path) != summary['input_sha256'][name]['sha256']:
            # 原文或查询变更需要新实验，不能继续沿用冻结候选。
            raise ValueError(f'Frozen dataset input changed: {path}')
    # 使用同一个读取器恢复原query和标题加正文。
    corpus, queries, qrels = load_beir_dataset(data_dir, split=split)
    # 文档正文只按ID保存一次。
    documents = corpus.set_index('id', drop=False).to_dict(orient='index')
    # 查询文字用于核对，不能替代查询ID。
    query_texts = dict(zip(queries['id'], queries['query']))
    # 读取标准评分run，用于交叉核对分数归属。
    run = json.loads(paths['run.json'].read_text(encoding='utf-8'))
    # 原始逐题列表保留原先的排名顺序。
    raw_rows = [json.loads(line) for line in paths['results.jsonl'].read_text(encoding='utf-8').splitlines() if line.strip()]
    # 以查询ID建立候选映射。
    rows = {}
    # 计数用于验证总候选数，不假设每题一定非空。
    total_pairs = 0
    # 对照每道题的原文字、候选ID及对应分数。
    for row in raw_rows:
        # 当前记录的查询身份。
        query_id = row['query_id']
        # 同一题不能重复，也不能来自另一个划分。
        if query_id in rows or query_id not in query_texts or row['query'] != query_texts[query_id]:
            # 不按位置或问题文字猜测题目对应关系。
            raise ValueError(f'Frozen query mismatch: {query_id}')
        # 候选列表保持已保存的顺序。
        identifiers = row['retrieved_ids']
        # 标准JSON分数转换为普通Python float。
        scores = [float(value) for value in row['scores']]
        # 候选不得重复、丢失对应分数或超过冻结预算。
        if len(identifiers) != len(scores) or len(identifiers) != len(set(identifiers)) or len(identifiers) > receipt['candidates_per_query']:
            # 不通过截断或补候选掩盖不一致。
            raise ValueError(f'Frozen candidate count mismatch: {query_id}')
        # 所有候选必须能在同一原始语料中找到，分数必须有限。
        if not set(identifiers) <= documents.keys() or not all(isfinite(value) for value in scores):
            # 拒绝错用另一库文档或非法分数。
            raise ValueError(f'Frozen document or score mismatch: {query_id}')
        # 标准run和逐题结果应指向同一组文档及分数。
        if run.get(query_id) != dict(zip(identifiers, scores)):
            # 只对顺序读取原列表，不对分数重新排序。
            raise ValueError(f'Frozen run mismatch: {query_id}')
        # 保存该题的独立候选列表与分数。
        rows[query_id] = {'retrieved_ids': list(identifiers), 'scores': scores}
        # 累积真实候选数，空题贡献0且仍保留查询。
        total_pairs += len(identifiers)
    # 所有原查询都必须出现，空候选也不能被删题。
    if set(rows) != set(query_texts) or set(run) != set(query_texts):
        # 避免只重排容易题而改变评测分母。
        raise ValueError('Frozen query coverage differs from the source split')
    # 摘要、回执和实际文件中的规模须一致。
    if len(rows) != receipt['query_count'] or len(rows) != summary['query_count'] or len(documents) != summary['document_count'] or total_pairs != receipt['total_pairs']:
        # 不用过期计数描述实际加载的数据。
        raise ValueError('Frozen source counts disagree')
    # 原回执若声明Recall@100不变量，应与原摘要一致。
    if 'same_candidate_set_requires_recall_at_100' in receipt and receipt['same_candidate_set_requires_recall_at_100'] != summary['metrics']['recall_at_100']:
        # 不把另一轮的召回率当成当前候选基线。
        raise ValueError('Frozen baseline Recall@100 mismatch')
    # 汇总实际元数据，后续保存时可直接引用。
    info = {'source_run_name': receipt['source_run_name'], 'dataset_name': summary['dataset_name'], 'data_dir': str(data_dir), 'split': split, 'candidate_k': receipt['candidates_per_query'], 'query_count': len(rows), 'total_pairs': total_pairs, 'candidate_count_distribution': dict(Counter(str(len(row['retrieved_ids'])) for row in rows.values())), 'source_retrieval_method': summary['retrieval_method'], 'source_config': summary['config'], 'baseline_metrics': summary['metrics'], 'source_retrieval_latency_ms': summary['latency_ms'], 'frozen_receipt': {'path': str(receipt_path), 'sha256': _sha256(receipt_path)}, 'source_files': {name: {'path': str(path), 'sha256': receipt['files'][name]['sha256']} for name, path in paths.items()}, 'input_sha256': {name: {'path': str(path), 'sha256': summary['input_sha256'][name]['sha256']} for name, path in inputs.items()}}
    # 返回评测输入对象，不执行任何推理或评分。
    return FrozenCandidates(queries, qrels, documents, rows, info)

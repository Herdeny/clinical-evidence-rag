# 下面的文档字符串说明本模块、类或函数的用途和适用边界。
"""Independently check every excerpt, fingerprint, identifier and token budget.

Checks data integrity, not clinical truth, retrieval quality or answer support.
"""

# 从 collections 中的指定接口导入 Counter。
from collections import Counter
# 从 functools 中的指定接口导入 lru_cache。
from functools import lru_cache
# 导入内容指纹工具。
import hashlib
# 导入JSON 编解码工具。
import json
# 导入路径对象 Path，便于定位脚本、组合目录并读写文件。
from pathlib import Path
# 导入耗时测量和请求间隔工具。
import time

# 从 lxml 中的指定接口导入 etree。
from lxml import etree
# 从 transformers 中的指定接口导入 AutoTokenizer。
from transformers import AutoTokenizer

# 从 数据准备包中的公共工具导入 DATA、MAX_TOKENS、ROOT、TOKENIZER_NAME、file_sha。
from scripts.data.build_medical_corpus import DATA, MAX_TOKENS, ROOT, TOKENIZER_NAME, file_sha
# 从 数据准备包中的公共工具导入 clean、render。
from scripts.data.medical_corpus_parsing import clean, render
# 从 数据准备包中的公共工具导入 dump、sha、xml_root。
from scripts.data.prepare_medical_corpus import dump, sha, xml_root


# 定义 validate：独立核对数据来源、位置、长度和划分；不验证医学正确性或运行生成模型。
def validate():
    # 设置started：读取单调高精度计时器，用于计算耗时。
    started = time.perf_counter()
    # 设置来源或构建清单：解析 JSON 文本或字节，恢复为 Python 对象。
    manifest = json.loads((DATA / 'corpus_manifest.json').read_text())
    # 按顺序遍历manifest['files'].items()，本轮元素记作 (name, info)。
    for name, info in manifest['files'].items():
        # 校验 file_sha(DATA / name) == info['sha256']；不满足时抛出 AssertionError，使核验失败。
        assert file_sha(DATA / name) == info['sha256'], name
    # 设置来源清单：解析 JSON 文本或字节，恢复为 Python 对象。
    sources = json.loads((DATA / 'sources.json').read_text())
    # 设置source_map：按遍历顺序筛选并整理 来源清单 中的数据。
    source_map = {s['id']: s for s in sources}
    # 校验 len(source_map) == len(sources)；不满足时抛出 AssertionError，使核验失败。
    assert len(source_map) == len(sources)
    # 设置source_errors：空列表。
    source_errors = []
    # 设置(units_checked, cell_references_checked)：元组。
    units_checked, cell_references_checked = 0, 0
    # 按顺序遍历enumerate(sources, 1)，本轮元素记作 (index, source)。
    for index, source in enumerate(sources, 1):
        # 校验 file_sha(ROOT / source['snapshot_path']) == source['snapshot_sha256']；不满足时抛出 AssertionError，使核验失败。
        assert file_sha(ROOT / source['snapshot_path']) == source['snapshot_sha256'], source['id']
        # 当 source.get('metadata_path') 成立时，执行下面的分支。
        if source.get('metadata_path'):
            # 校验 file_sha(ROOT / source['metadata_path']) == source['metadata_sha256']；不满足时抛出 AssertionError，使核验失败。
            assert file_sha(ROOT / source['metadata_path']) == source['metadata_sha256']
        # 当 source['source_type'] not in {'paper', 'drug_label'} 成立时，执行下面的分支。
        if source['source_type'] not in {'paper', 'drug_label'}:
            # 跳过当前项，继续检查本层循环中的下一项。
            continue
        # 校验 file_sha(ROOT / source['parsed_path']) == source['parsed_sha256']；不满足时抛出 AssertionError，使核验失败。
        assert file_sha(ROOT / source['parsed_path']) == source['parsed_sha256']
        # 设置document：解析 JSON 文本或字节，恢复为 Python 对象。
        document = json.loads((ROOT / source['parsed_path']).read_text())
        # 设置root：安全解析 XML 字节，禁用外部实体展开和解析器联网。
        root = xml_root((ROOT / source['snapshot_path']).read_bytes())
        # 设置tree：取得原始节点的完整元素树。
        tree = root.getroottree()
        # Canonical XPath keys are evaluated by walking the original tree; no
        # assumptions about an XML default namespace are needed here.
        # 设置origins：按遍历顺序筛选并整理 root.iter() 中的数据。
        origins = {tree.getpath(node): node for node in root.iter() if isinstance(node.tag, str)}
        # 按顺序遍历document['units']，本轮元素记作 unit。
        for unit in document['units']:
            # 设置locator：按键或位置读取 当前文本单元 中的对应内容。
            locator = unit['locator']
            # 校验 locator['xpath'] in origins；不满足时抛出 AssertionError，使核验失败。
            assert locator['xpath'] in origins, (source['id'], locator['xpath'])
            # 当 locator['extraction_kind'] != 'structured_table_row' 成立时，执行下面的分支。
            if locator['extraction_kind'] != 'structured_table_row':
                # 校验 clean(render(origins[locator['xpath']])) == unit['text']；不满足时抛出 AssertionError，使核验失败。
                assert clean(render(origins[locator['xpath']])) == unit['text'], source['id']
            # 前面的条件都不满足时，执行这一分支。
            else:
                # 按顺序遍历locator['cells']，本轮元素记作 cell。
                for cell in locator['cells']:
                    # 校验 cell['xpath'] in origins；不满足时抛出 AssertionError，使核验失败。
                    assert cell['xpath'] in origins
                    # 校验 clean(render(origins[cell['xpath']])) == cell['text']；不满足时抛出 AssertionError，使核验失败。
                    assert clean(render(origins[cell['xpath']])) == cell['text'], source['id']
                    # 更新cell_references_checked，累计本轮处理量或内容。
                    cell_references_checked += 1
                # 校验 locator['table_xpath'] in origins；不满足时抛出 AssertionError，使核验失败。
                assert locator['table_xpath'] in origins
            # 更新units_checked，累计本轮处理量或内容。
            units_checked += 1
        # 当 index % 1000 == 0 成立时，执行下面的分支。
        if index % 1000 == 0:
            # 打印当前进度、输出文件位置或核验结果，方便观察执行状态。
            print('source provenance checked', index, flush=True)
    # 设置tokenizer：按参数加载 tokenizer；这里用于长度检查，不运行嵌入模型。
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME, local_files_only=True)
    # 设置tokenizer.model_max_length：10 ** 9。
    tokenizer.model_max_length = 10**9

    # 为上方调用传入 maxsize 参数；取值按本行指定。
    @lru_cache(maxsize=16)
    # 定义 load_units：读取并缓存一个解析文档的 unit_id 到文本单元映射。
    def load_units(relative):
        # 返回按遍历顺序筛选并整理 json.loads((ROOT / relative).read_text())['units'] 中的数据，结束本次函数调用。
        return {u['unit_id']: u for u in json.loads((ROOT / relative).read_text())['units']}

    # 设置(seen, content_hashes)：元组。
    seen, content_hashes = set(), set()
    # 设置(counts, source_counts, token_counts)：元组。
    counts, source_counts, token_counts = Counter(), Counter(), Counter()
    # 设置当前批次：空列表。
    batch = []
    # 设置old_lines：将文件文本按行拆分。
    old_lines = (ROOT / 'data/v2/evidence.jsonl').read_text().splitlines()
    # 设置old_index：常量 0。
    old_index = 0
    # 设置count：常量 0。
    count = 0

    # 定义 token_check：对一批实际入库正文重新计数，验证记录中的 token 数和长度上限。
    def token_check(items):
        # 对当前正文分词并请求字符偏移；关闭截断，使长度校验覆盖完整正文。
        encoded = tokenizer([i['text'] for i in items], add_special_tokens=True, truncation=False)['input_ids']
        # 按顺序遍历zip(items, encoded)，本轮元素记作 (item, ids)。
        for item, ids in zip(items, encoded):
            # 设置length：取得对象中元素或字符的数量。
            length = len(ids)
            # 校验 length == item['embedding_token_count']；不满足时抛出 AssertionError，使核验失败。
            assert length == item['embedding_token_count'], item['id']
            # 校验 length <= MAX_TOKENS；不满足时抛出 AssertionError，使核验失败。
            assert length <= MAX_TOKENS, item['id']
            # 更新token_counts[length]，累计本轮处理量或内容。
            token_counts[length] += 1

    # 进入受管理的上下文：按指定读写模式打开文件，并在 with 退出时关闭句柄。
    with (DATA / 'evidence.jsonl').open(encoding='utf-8') as stream:
        # 按顺序遍历stream，本轮元素记作 line。
        for line in stream:
            # 设置item：解析 JSON 文本或字节，恢复为 Python 对象。
            item = json.loads(line)
            # 校验 item['id'] not in seen；不满足时抛出 AssertionError，使核验失败。
            assert item['id'] not in seen
            # 将 HTML 节点保存为带章节、锚点和原元素位置的正文块。
            seen.add(item['id'])
            # 校验 item['source_id'] in source_map；不满足时抛出 AssertionError，使核验失败。
            assert item['source_id'] in source_map
            # 设置当前来源：按键或位置读取 source_map 中的对应内容。
            source = source_map[item['source_id']]
            # 校验 item['raw_path'] == source['snapshot_path']；不满足时抛出 AssertionError，使核验失败。
            assert item['raw_path'] == source['snapshot_path']
            # 校验 item['raw_sha256'] == source['snapshot_sha256']；不满足时抛出 AssertionError，使核验失败。
            assert item['raw_sha256'] == source['snapshot_sha256']
            # 校验 item['retrieval_ready'] is True；不满足时抛出 AssertionError，使核验失败。
            assert item['retrieval_ready'] is True
            # 设置content_digest：计算一段字节内容的 SHA-256 指纹。
            content_digest = sha(item['text'].encode())
            # 将 HTML 节点保存为带章节、锚点和原元素位置的正文块。
            content_hashes.add(content_digest)
            # 当 item['locator']['type'] == 'canonical_unit_span' 成立时，执行下面的分支。
            if item['locator']['type'] == 'canonical_unit_span':
                # 校验 item['content_sha256'] == content_digest；不满足时抛出 AssertionError，使核验失败。
                assert item['content_sha256'] == content_digest
                # 设置规范化文本单元：读取并缓存一个解析文档的 unit_id 到文本单元映射。
                units = load_units(item['locator']['blocks_file'])
                # 设置parts：按键或位置读取 item['locator'] 中的对应内容。
                parts = item['locator']['parts']
                # 校验 len(parts) == 1；不满足时抛出 AssertionError，使核验失败。
                assert len(parts) == 1
                # 按顺序遍历parts + item['locator']['alias_parts']，本轮元素记作 part。
                for part in parts + item['locator']['alias_parts']:
                    # 设置当前文本单元：按键或位置读取 规范化文本单元 中的对应内容。
                    unit = units[part['unit_id']]
                    # 校验 0 <= part['char_start'] < part['char_end'] <= len(unit['text'])；不满足时抛出 AssertionError，使核验失败。
                    assert 0 <= part['char_start'] < part['char_end'] <= len(unit['text'])
                    # 校验 item['text'] == unit['text'][part['char_start']:part['char_end']]；不满足时抛出 AssertionError，使核验失败。
                    assert item['text'] == unit['text'][part['char_start']:part['char_end']]
                # 校验 item['locator']['xpath'] == units[parts[0]['unit_id']]['locator']['xpath']；不满足时抛出 AssertionError，使核验失败。
                assert item['locator']['xpath'] == units[parts[0]['unit_id']]['locator']['xpath']
                # 校验 item['document_version'] == source['document_version']；不满足时抛出 AssertionError，使核验失败。
                assert item['document_version'] == source['document_version']
                # 当 source['source_type'] == 'paper' 成立时，执行下面的分支。
                if source['source_type'] == 'paper':
                    # 校验 source['license_code'] in {'CC BY', 'CC0'}；不满足时抛出 AssertionError，使核验失败。
                    assert source['license_code'] in {'CC BY', 'CC0'}
                # 当 source['source_type'] == 'drug_label' 成立时，执行下面的分支。
                if source['source_type'] == 'drug_label':
                    # 校验 source['identity']['setid'] in source['id']；不满足时抛出 AssertionError，使核验失败。
                    assert source['identity']['setid'] in source['id']
                    # 校验 source['identity']['active_ingredients']；不满足时抛出 AssertionError，使核验失败。
                    assert source['identity']['active_ingredients']
                    # 校验 source['identity']['products']；不满足时抛出 AssertionError，使核验失败。
                    assert source['identity']['products']
            # 前面的条件都不满足时，执行这一分支。
            else:
                # 校验 old_index < len(old_lines)；不满足时抛出 AssertionError，使核验失败。
                assert old_index < len(old_lines)
                # 校验 line.rstrip('\n') == old_lines[old_index]；不满足时抛出 AssertionError，使核验失败。
                assert line.rstrip('\n') == old_lines[old_index], 'Existing CT evidence changed'
                # 更新old_index，累计本轮处理量或内容。
                old_index += 1
            # 更新counts[item['source_type']]，累计本轮处理量或内容。
            counts[item['source_type']] += 1
            # 更新source_counts[item['source_id']]，累计本轮处理量或内容。
            source_counts[item['source_id']] += 1
            # 把当前结果加入 batch 的末尾，保留处理顺序。
            batch.append(item)
            # 当 len(batch) == 256 成立时，执行下面的分支。
            if len(batch) == 256:
                # 对一批实际入库正文重新计数，验证记录中的 token 数和长度上限。
                token_check(batch)
                # 设置当前批次：空列表。
                batch = []
            # 更新count，累计本轮处理量或内容。
            count += 1
            # 当 count % 50000 == 0 成立时，执行下面的分支。
            if count % 50000 == 0:
                # 打印当前进度、输出文件位置或核验结果，方便观察执行状态。
                print('excerpt and tokenizer checks', count, flush=True)
    # 当 batch 成立时，执行下面的分支。
    if batch:
        # 对一批实际入库正文重新计数，验证记录中的 token 数和长度上限。
        token_check(batch)
    # 校验 old_index == 238；不满足时抛出 AssertionError，使核验失败。
    assert old_index == 238
    # 校验 count == manifest['chunk_count']；不满足时抛出 AssertionError，使核验失败。
    assert count == manifest['chunk_count']
    # 校验 len(source_counts) == len(sources)；不满足时抛出 AssertionError，使核验失败。
    assert len(source_counts) == len(sources)
    # 校验 len(content_hashes) == manifest['global_unique_exact_text_count']；不满足时抛出 AssertionError，使核验失败。
    assert len(content_hashes) == manifest['global_unique_exact_text_count']
    # 校验 file_sha(DATA / 'cases.ct.dev.jsonl') == file_sha(ROOT / 'data/v2/cases.dev.jsonl')；不满足时抛出 AssertionError，使核验失败。
    assert file_sha(DATA / 'cases.ct.dev.jsonl') == file_sha(ROOT / 'data/v2/cases.dev.jsonl')
    # 校验 file_sha(ROOT / 'data/v2/evidence.jsonl') == '686e2c6703214803ac5beeb550e5ee815c15d5269a70fb7738e180f2e5…；不满足时抛出 AssertionError，使核验失败。
    assert file_sha(ROOT / 'data/v2/evidence.jsonl') == '686e2c6703214803ac5beeb550e5ee815c15d5269a70fb7738e180f2e5fbaa00'
    # 校验 file_sha(ROOT / 'data/v2/cases.dev.jsonl') == 'f13291a4718866e06701370a0a6b1622bbf329f1514faac2885105f0f…；不满足时抛出 AssertionError，使核验失败。
    assert file_sha(ROOT / 'data/v2/cases.dev.jsonl') == 'f13291a4718866e06701370a0a6b1622bbf329f1514faac2885105f0fdc6f786'
    # Verify that each subset is the exact ordered subsequence of the combined
    # file. Do not trust counts alone to detect dropped or duplicated records.
    # 设置expected：字典，保存paper、drug_label、guideline。
    expected = {'paper': 'pmc', 'drug_label': 'dailymed', 'guideline': 'nih'}
    # 设置digest_by_subset：按遍历顺序筛选并整理 expected 中的数据。
    digest_by_subset = {kind: hashlib.sha256() for kind in expected}
    # 进入受管理的上下文：按指定读写模式打开文件，并在 with 退出时关闭句柄。
    with (DATA / 'evidence.jsonl').open('rb') as stream:
        # 按顺序遍历stream，本轮元素记作 raw。
        for raw in stream:
            # 设置item：解析 JSON 文本或字节，恢复为 Python 对象。
            item = json.loads(raw)
            # 当 item['locator']['type'] == 'canonical_unit_span' 成立时，执行下面的分支。
            if item['locator']['type'] == 'canonical_unit_span':
                # 把下一块内容加入同一个摘要计算器。
                digest_by_subset[item['source_type']].update(raw)
    # 按顺序遍历expected.items()，本轮元素记作 (kind, suffix)。
    for kind, suffix in expected.items():
        # 校验 digest_by_subset[kind].hexdigest() == file_sha(DATA / f'evidence.{suffix}.jsonl')；不满足时抛出 AssertionError，使核验失败。
        assert digest_by_subset[kind].hexdigest() == file_sha(DATA / f'evidence.{suffix}.jsonl')
    # 设置report：字典，保存当前处理或完成状态、入库来源数量、可检索片段数量、global_unique_exact_text_count、source_units_checked等信息。
    report = {'status': 'passed', 'source_count': len(sources), 'chunk_count': count,
              # 写入字段 global_unique_exact_text_count（跨来源统计的不同正文数量，不等于独立医学知识数）；字段 source_units_checked（已逐一核对原节点的规范化单元数量）。
              'global_unique_exact_text_count': len(content_hashes), 'source_units_checked': units_checked,
              # 写入字段 table_cell_references_checked（核对过原始位置的表格单元格引用数量）。
              'table_cell_references_checked': cell_references_checked,
              # 写入字段 all_excerpt_spans_checked（是否检查了全部片段的字符范围）；字段 all_raw_and_parsed_fingerprints_checked（是否检查了全部原始文件和解析文件指纹）。
              'all_excerpt_spans_checked': True, 'all_raw_and_parsed_fingerprints_checked': True,
              # 写入字段 all_token_counts_checked（是否逐条复核了token数量）；字段 max_tokens（实测片段的最大token数量）。
              'all_token_counts_checked': True, 'max_tokens': max(token_counts),
              # 写入字段 chunk_counts_by_source_type（按来源角色统计的片段数）。
              'chunk_counts_by_source_type': dict(counts),
              # 写入字段 token_length_histogram（按实际token数量统计的片段分布）。
              'token_length_histogram': dict(sorted(token_counts.items())),
              # 写入字段 original_ct_data_and_dev_fingerprints_unchanged（原CT证据和开发题指纹是否保持不变）。
              'original_ct_data_and_dev_fingerprints_unchanged': True,
              # 写入字段 benchmark_questions_read（是否使用了外部基准问题内容）；字段 models_or_paid_apis_called（是否调用了模型或付费接口）。
              'benchmark_questions_read': False, 'models_or_paid_apis_called': False,
              # 写入字段 clinical_correctness_verified（是否验证了医学结论正确性，本检查不冒充临床验证）；字段 semantic_table_alignment_verified（是否验证表格的医学语义对应，不由位置检查自动保证）。
              'clinical_correctness_verified': False, 'semantic_table_alignment_verified': False,
              # 写入字段 validation_seconds（完整性校验的实际耗时秒数）。
              'validation_seconds': round(time.perf_counter() - started, 3)}
    # 以临时文件加替换的方式保存 JSON 记录。
    dump(ROOT / 'results/medical_corpus_v3_validation.json', report)
    # 设置manifest['status']：字符串 'frozen_integrity_validated_clinical_review_pending'。
    manifest['status'] = 'frozen_integrity_validated_clinical_review_pending'
    # 设置manifest['validation_report']：字符串 'results/medical_corpus_v3_validation.json'。
    manifest['validation_report'] = 'results/medical_corpus_v3_validation.json'
    # 以临时文件加替换的方式保存 JSON 记录。
    dump(DATA / 'corpus_manifest.json', manifest)
    # 打印当前进度、输出文件位置或核验结果，方便观察执行状态。
    print(json.dumps({k: report[k] for k in ['status', 'source_count', 'chunk_count', 'max_tokens', 'validation_seconds']}), flush=True)
    # 返回report，结束本次函数调用。
    return report


# 当 __name__ == '__main__' 成立时，执行下面的分支。
if __name__ == '__main__':
    # 调用 validate，取得该步骤的处理结果。
    validate()

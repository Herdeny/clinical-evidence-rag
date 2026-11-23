# 下面的文档字符串说明本模块、类或函数的用途和适用边界。
"""Build an auditable corpus snapshot, without embedding, retrieval or LLM calls.

Input manifests and original snapshots stay intact. Normalized text units are
stored separately so every indexed excerpt can be reconstructed by character
offsets. No benchmark question, option, answer or evaluation label is read.
"""

# 导入argparse 模块。
import argparse
# 从 collections 中的指定接口导入 Counter。
from collections import Counter
# 从 datetime 中的指定接口导入 datetime、timezone。
from datetime import datetime, timezone
# 导入内容指纹工具。
import hashlib
# 导入JSON 编解码工具。
import json
# 导入路径对象 Path，便于定位脚本、组合目录并读写文件。
from pathlib import Path
# 导入耗时测量和请求间隔工具。
import time

# 从 lxml 中的指定接口导入 etree、html。
from lxml import etree, html
# 从 transformers 中的指定接口导入 AutoTokenizer。
from transformers import AutoTokenizer

# 从 数据准备包中的公共工具导入 clean、html_units、render、split_unit、xml_units。
from scripts.data.medical_corpus_parsing import clean, html_units, render, split_unit, xml_units
# 从 数据准备包中的公共工具导入 DATA、DATE、ROOT、dump、sha、xml_root。
from scripts.data.prepare_medical_corpus import DATA, DATE, ROOT, dump, sha, xml_root

# 固定用于片段长度计数的 BGE tokenizer 名称；此处不运行嵌入模型。
TOKENIZER_NAME = 'BAAI/bge-small-en-v1.5'
# 固定正文片段的 token 准入上限，为 512 token 的模型保留余量。
MAX_TOKENS = 480
# 只准入研究、综述、病例等列出的论文类型，评论和新闻等另行隔离。
PAPER_TYPES = {'research-article', 'review-article', 'case-report', 'systematic-review',
               # 继续组装上方容器中的本行元素，保持其原始顺序和取值。
               'brief-report', 'methods-article', 'case-study', 'data-paper'}


# 定义 json_line：将一个记录编码成一行 JSONL。
def json_line(value):
    # 返回json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n'，结束本次函数调用。
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n'


# 定义 file_sha：分块计算文件 SHA-256 指纹。
def file_sha(path):
    # 设置摘要计算器：初始化 SHA-256 内容摘要。
    digest = hashlib.sha256()
    # 进入受管理的上下文：按指定读写模式打开文件，并在 with 退出时关闭句柄。
    with Path(path).open('rb') as stream:
        # 每次读取 1 MiB；遇到空字节 b'' 时停止，避免一次读入整个大文件。
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            # 把下一块内容加入同一个摘要计算器。
            digest.update(block)
    # 返回取出已经计算好的十六进制内容指纹，结束本次函数调用。
    return digest.hexdigest()


# 定义 checked_raw：读取原始快照，并确认字节内容仍与采集回执一致。
def checked_raw(receipt, key='xml'):
    # 设置当前记录：按键或位置读取 采集回执 中的对应内容。
    record = receipt[key]
    # 设置文件路径：将目录与右侧子路径组合，得到完整输出位置。
    path = ROOT / record['path']
    # 设置原始字节内容：读取指定文件的原始字节。
    raw = path.read_bytes()
    # 当 sha(raw) != record['sha256'] 成立时，执行下面的分支。
    if sha(raw) != record['sha256']:
        # 抛出 ValueError 并停止当前操作。
        raise ValueError('raw_sha256_mismatch:' + str(path))
    # 返回原始字节内容，结束本次函数调用。
    return raw


# 定义 paper_source：从已准入论文的元数据和 JATS 提取身份、作者、许可与来源位置。
def paper_source(receipt):
    # 当 receipt['article_type'] not in PAPER_TYPES 成立时，执行下面的分支。
    if receipt['article_type'] not in PAPER_TYPES:
        # 抛出 ValueError 并停止当前操作。
        raise ValueError('article_type_not_in_research_review_or_case_allowlist:' + receipt['article_type'])
    # 设置原始字节内容：读取原始快照，并确认字节内容仍与采集回执一致。
    raw = checked_raw(receipt)
    # 设置官方元数据：解析 JSON 文本或字节，恢复为 Python 对象。
    meta = json.loads(checked_raw(receipt, 'metadata'))
    # 设置root：安全解析 XML 字节，禁用外部实体展开和解析器联网。
    root = xml_root(raw)
    # 设置article_meta：按键或位置读取 root.xpath('./*[local-name()="front"]/*[local-name()="article-meta"]') 中的对应内容。
    article_meta = root.xpath('./*[local-name()="front"]/*[local-name()="article-meta"]')[0]
    # 设置contributors：按 XPath 在原始结构中查找节点或字段值。
    contributors = article_meta.xpath('./*[local-name()="contrib-group"]/*[local-name()="contrib"][@contrib-type="author"]')
    # 设置authors：按遍历顺序筛选并整理 contributors 中的数据。
    authors = [clean(' '.join(''.join(n.itertext()) for n in node if etree.QName(n).localname in {'name', 'string-name', 'collab'})) for node in contributors]
    # 设置dates：按遍历顺序筛选并整理 article_meta 中的数据。
    dates = [{**dict(node.attrib), 'parts': {etree.QName(part).localname: clean(''.join(part.itertext())) for part in node if isinstance(part.tag, str)}}
             # 推导式继续按此处的顺序遍历，生成上方表达式所需的数据。
             for node in article_meta if etree.QName(node).localname == 'pub-date']
    # 设置publishers：按 XPath 在原始结构中查找节点或字段值。
    publishers = root.xpath('./*[local-name()="front"]/*[local-name()="journal-meta"]/*[local-name()="publisher"]/*[local-name()="publisher-name"]/text()')
    # 设置copyright_statements：按 XPath 在原始结构中查找节点或字段值。
    copyright_statements = article_meta.xpath('./*[local-name()="permissions"]/*[local-name()="copyright-statement"]/text()')
    # 设置pmcid：按键或位置读取 采集回执 中的对应内容。
    pmcid = receipt['pmcid']
    # 设置当前来源：字典，保存记录的唯一标识、来源角色，区分指南、论文、说明书等、原始文档或章节标题、来源发布机构或标签提交机构、论文作者署名等信息。
    source = {'id': receipt['source_id'], 'source_type': 'paper', 'title': meta['title'],
              # 写入字段 publisher（来源发布机构或标签提交机构）；字段 authors（论文作者署名）。
              'publisher': '; '.join(publishers) or None, 'authors': [a for a in authors if a],
              # 写入字段 citation（来源元数据给出的完整文献引用）；字段 pmcid（PMC 文章标识）；字段 pmid（PubMed 文献标识）；字段 doi（论文 DOI）。
              'citation': meta.get('citation'), 'pmcid': pmcid, 'pmid': meta.get('pmid'), 'doi': meta.get('doi'),
              # 写入字段 url（来源原始链接或带章节锚点的链接）。
              'url': f'https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/',
              # 写入字段 document_version（来源文档的版本）；字段 publication_dates（源 XML 中声明的发表日期信息）。
              'document_version': str(meta['version']), 'publication_dates': dates,
              # 写入字段 article_type（论文原文声明的文章类型）；字段 evidence_role（该来源可承担的证据角色，避免把研究当成指南）。
              'article_type': receipt['article_type'], 'evidence_role': 'research_or_review_not_automatically_a_guideline',
              # 写入字段 license_code（官方元数据声明的许可类型）；字段 license_urls（原文中的许可链接）。
              'license_code': meta['license_code'], 'license_urls': receipt['license_links'],
              # 写入字段 copyright_statements（源XML内保留的版权声明文本）。
              'copyright_statements': copyright_statements,
              # 写入字段 distribution_decision（本项目按来源作出的分发范围决定）。
              'distribution_decision': 'licensed_text_only_with_attribution; excludes_figures_and_supplements',
              # 写入字段 region（来源适用或产品注册的目标地区）；字段 scope_note（来源范围与后续命题适用性核验的说明）。
              'region': None, 'scope_note': 'Study population and applicability require claim-level verification.',
              # 写入字段 selection_topics（将该论文召回的预定义医学主题）；字段 selection_rank（独立于网络完成顺序的候选优先级）。
              'selection_topics': receipt['topics'], 'selection_rank': receipt['selection_rank'],
              # 写入字段 verified_at（来源或快照的核验日期）；字段 snapshot_path（来源快照的位置）。
              'verified_at': receipt['downloaded_on'], 'snapshot_path': receipt['xml']['path'],
              # 写入字段 snapshot_sha256（固定来源快照的指纹）；字段 metadata_path（官方元数据快照的位置）。
              'snapshot_sha256': receipt['xml']['sha256'], 'metadata_path': receipt['metadata']['path'],
              # 写入字段 metadata_sha256（元数据快照的内容指纹）；字段 snapshot_url（取得固定原始快照的官方链接）。
              'metadata_sha256': receipt['metadata']['sha256'], 'snapshot_url': receipt['xml']['url'],
              # 写入字段 provider_md5（官方地址提供的MD5值，仅核对字节完整性）。
              'provider_md5': receipt['xml'].get('provider_md5')}
    # 返回元组，结束本次函数调用。
    return root, source


# 定义 label_source：将 SPL 回执整理成保留具体产品身份的统一来源记录。
def label_source(receipt):
    # 设置root：安全解析 XML 字节，禁用外部实体展开和解析器联网。
    root = xml_root(checked_raw(receipt))
    # 设置当前来源：字典，保存记录的唯一标识、来源角色，区分指南、论文、说明书等、原始文档或章节标题、来源发布机构或标签提交机构、来源原始链接或带章节锚点的链接等信息。
    source = {'id': receipt['source_id'], 'source_type': 'drug_label', 'title': receipt['title'],
              # 写入字段 publisher（来源发布机构或标签提交机构）。
              'publisher': '; '.join(receipt['labelers']) or None,
              # 写入字段 url（来源原始链接或带章节锚点的链接）。
              'url': 'https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=' + receipt['setid'],
              # 写入字段 document_version（来源文档的版本）；字段 updated_at（原来源声明的更新时间）。
              'document_version': receipt['spl_version'], 'updated_at': receipt['effective_time'],
              # 写入字段 region（来源适用或产品注册的目标地区）；字段 evidence_role（该来源可承担的证据角色，避免把研究当成指南）。
              'region': 'US', 'evidence_role': 'product_specific_submitted_label',
              # 写入字段 distribution_decision（本项目按来源作出的分发范围决定）。
              'distribution_decision': receipt['distribution_decision'],
              # 写入字段 verified_at（来源或快照的核验日期）；字段 snapshot_path（来源快照的位置）。
              'verified_at': receipt['downloaded_on'], 'snapshot_path': receipt['xml']['path'],
              # 写入字段 snapshot_sha256（固定来源快照的指纹）；字段 snapshot_url（取得固定原始快照的官方链接）。
              'snapshot_sha256': receipt['xml']['sha256'], 'snapshot_url': receipt['xml']['url'],
              # 写入字段 queried_terms（将该产品召回的预定义药物词）。
              'queried_terms': receipt['queried_terms'],
              # 写入字段 identity（需要完全一致才能复用的缓存身份）。
              'identity': {key: receipt[key] for key in ['setid', 'spl_version', 'effective_time', 'active_ingredients',
                            # 继续组装上方容器中的本行元素，保持其原始顺序和取值。
                            'labelers', 'products', 'marketing_category_reported', 'approval_verification', 'label_status']},
              # 写入字段 api_xml_version_agrees（API列表与XML声明的版本是否一致）。
              'api_xml_version_agrees': receipt['api_xml_version_agrees']}
    # 返回元组，结束本次函数调用。
    return root, source


# 定义 source_units：根据来源类型调用对应解析器，统一返回来源、文本单元和隔离记录。
def source_units(receipt, kind):
    # 当 kind == 'paper' 成立时，执行下面的分支。
    if kind == 'paper':
        # 设置(root, source)：从已准入论文的元数据和 JATS 提取身份、作者、许可与来源位置。
        root, source = paper_source(receipt)
        # 设置(units, excluded)：从论文或 SPL 的约定结构提取文本单元，隔离不可靠内容。
        units, excluded = xml_units(root, kind)
        # The omitted structures remain available in the original XML; they are
        # not silently flattened and presented as complete clinical evidence.
        # 设置structures：创建分类计数器，用于累计来源、分片或校验数量。
        structures = Counter(etree.QName(node).localname for node in root.iter() if isinstance(node.tag, str)
                             # 继续为 Counter 提供本行的参数或输入片段。
                             and etree.QName(node).localname in {'fig', 'table-wrap', 'supplementary-material'})
        # 设置source['nonindexed_structure_counts']：创建或复制字典。
        source['nonindexed_structure_counts'] = dict(structures)
    # 当 kind == 'drug_label' 成立时，执行下面的分支。
    elif kind == 'drug_label':
        # 设置(root, source)：将 SPL 回执整理成保留具体产品身份的统一来源记录。
        root, source = label_source(receipt)
        # 设置(units, excluded)：从论文或 SPL 的约定结构提取文本单元，隔离不可靠内容。
        units, excluded = xml_units(root, kind)
    # 前面的条件都不满足时，执行这一分支。
    else:
        # 设置原始字节内容：读取指定文件的原始字节。
        raw = (ROOT / receipt['raw_path']).read_bytes()
        # 当 sha(raw) != receipt['sha256'] 成立时，执行下面的分支。
        if sha(raw) != receipt['sha256']:
            # 抛出 ValueError 并停止当前操作：guideline_sha256_mismatch。
            raise ValueError('guideline_sha256_mismatch')
        # 设置root：把 HTML 快照解析为元素树。
        root = html.fromstring(raw)
        # 设置当前来源：字典，保存记录的唯一标识、来源角色，区分指南、论文、说明书等、原始文档或章节标题、来源发布机构或标签提交机构、来源原始链接或带章节锚点的链接等信息。
        source = {'id': receipt['source_id'], 'source_type': 'guideline', 'title': receipt['title'],
                  # 写入字段 publisher（来源发布机构或标签提交机构）。
                  'publisher': 'HHS Panel on Antiretroviral Guidelines for Adults and Adolescents',
                  # 写入字段 url（来源原始链接或带章节锚点的链接）；字段 document_version（来源文档的版本）；字段 region（来源适用或产品注册的目标地区）。
                  'url': receipt['final_url'], 'document_version': None, 'region': 'US',
                  # 写入字段 evidence_role（该来源可承担的证据角色，避免把研究当成指南）；字段 distribution_decision（本项目按来源作出的分发范围决定）。
                  'evidence_role': 'guideline', 'distribution_decision': receipt['distribution_decision'],
                  # 写入字段 snapshot_path（来源快照的位置）；字段 snapshot_sha256（固定来源快照的指纹）。
                  'snapshot_path': receipt['raw_path'], 'snapshot_sha256': receipt['sha256'],
                  # 写入字段 verified_at（来源或快照的核验日期）。
                  'verified_at': receipt['downloaded_on']}
        # 设置(units, excluded)：从 NIH 指南 HTML 正文提取段落和表格行，排除导航与参考文献。
        units, excluded = html_units(root)
    # 返回元组，结束本次函数调用。
    return source, units, excluded


# 定义 prepare_document：为一个来源分段、做同源精确去重，并保存可回溯证据和解析单元。
def prepare_document(receipt, kind, tokenizer):
    # 设置(source, units, excluded)：根据来源类型调用对应解析器，统一返回来源、文本单元和隔离记录。
    source, units, excluded = source_units(receipt, kind)
    # 当 not units 成立时，执行下面的分支。
    if not units:
        # 抛出 ValueError 并停止当前操作：no_indexable_units。
        raise ValueError('no_indexable_units')
    # 设置输出目录：将目录与右侧子路径组合，得到完整输出位置。
    folder = DATA / 'parsed/documents' / kind
    # 设置key：将临时文件提交或改名到指定位置。
    key = source['id'].replace(':', '_')
    # 设置document_path：将目录与右侧子路径组合，得到完整输出位置。
    document_path = folder / (key + '.json')
    # 设置(records, by_text)：元组。
    records, by_text = [], {}
    # 设置本批统计：创建分类计数器，用于累计来源、分片或校验数量。
    stats = Counter()
    # 按顺序遍历规范化文本单元，本轮元素记作 unit。
    for unit in units:
        # 设置当前文本：按键或位置读取 当前文本单元 中的对应内容。
        text = unit['text']
        # 设置is_table：unit['locator']['extraction_kind'] == 'structured_table_row'。
        is_table = unit['locator']['extraction_kind'] == 'structured_table_row'
        # 当 is_table 成立时，执行下面的分支。
        if is_table:
            # 设置count：取得对象中元素或字符的数量。
            count = len(tokenizer.encode(text, truncation=False))
            # 当 count > MAX_TOKENS 成立时，执行下面的分支。
            if count > MAX_TOKENS:
                # 把当前结果加入 excluded 的末尾，保留处理顺序。
                excluded.append({'unit_id': unit['unit_id'], 'reason': 'oversized_table_row_not_split', 'tokens': count})
                # 跳过当前项，继续检查本层循环中的下一项。
                continue
            # 设置spans：列表。
            spans = [(0, len(text), count)]
        # 前面的条件都不满足时，执行这一分支。
        else:
            # 设置spans：按 tokenizer 的真实字符偏移切分长段落，确保不丢词且不隐藏截断。
            spans = split_unit(text, tokenizer, MAX_TOKENS)
        # 按顺序遍历enumerate(spans, 1)，本轮元素记作 (part_index, (start, end, token_count))。
        for part_index, (start, end, token_count) in enumerate(spans, 1):
            # 设置excerpt：按键或位置读取 当前文本 中的对应内容。
            excerpt = text[start:end]
            # 校验 excerpt and token_count <= MAX_TOKENS；不满足时抛出 AssertionError，使核验失败。
            assert excerpt and token_count <= MAX_TOKENS
            # 设置location：字典，保存规范化文本单元的标识、相对原文本的起始字符位置，包含该位置、相对原文本的结束字符位置，不包含该位置。
            location = {'unit_id': unit['unit_id'], 'char_start': start, 'char_end': end}
            # 设置摘要计算器：计算一段字节内容的 SHA-256 指纹。
            digest = sha(excerpt.encode('utf-8'))
            # Preserve product identity. Never merge snippets across sources.
            # 当 digest in by_text 成立时，执行下面的分支。
            if digest in by_text:
                # 把当前结果加入 by_text[digest]['locator']['alias_parts'] 的末尾，保留处理顺序。
                by_text[digest]['locator']['alias_parts'].append(location)
                # 更新stats['within_source_exact_duplicates']，累计本轮处理量或内容。
                stats['within_source_exact_duplicates'] += 1
                # 跳过当前项，继续检查本层循环中的下一项。
                continue
            # 设置evidence：字典，保存记录的唯一标识、来源唯一标识，用于反查原始文件、来源角色，区分指南、论文、说明书等、text_kind、本条正文或题目报告文字等信息。
            evidence = {'id': f"{source['id']}::{unit['unit_id']}::s{part_index:03d}",
                        # 写入字段 source_id（来源唯一标识，用于反查原始文件）；字段 source_type（来源角色，区分指南、论文、说明书等）。
                        'source_id': source['id'], 'source_type': source['source_type'],
                        # 写入字段 text_kind（正文是原始提取、结构化提取还是项目转述）；字段 text（本条正文或题目报告文字）。
                        'text_kind': 'structured_extracted_text', 'text': excerpt,
                        # 写入字段 locator（原始证据位置结构）；字段 type（当前定位或结构对象的类型标记）；字段 url（来源原始链接或带章节锚点的链接）。
                        'locator': {'type': 'canonical_unit_span', 'url': source['url'],
                                    # 写入字段 heading_path（由外到内的章节标题路径）。
                                    'heading_path': unit['section_path'],
                                    # 写入字段 blocks_file（正文单元所在的解析 JSON 文件）。
                                    'blocks_file': str(document_path.relative_to(ROOT)),
                                    # 写入字段 parts（可用于还原正文的原单元及字符范围）；字段 alias_parts（同源去重时保留的其他等价位置）。
                                    'parts': [location], 'alias_parts': [],
                                    # 写入字段 xpath（原始 XML 或 HTML 节点的 XPath）；字段 element_id（原始节点自带的 id）。
                                    'xpath': unit['locator']['xpath'], 'element_id': unit['locator']['element_id'],
                                    # 写入字段 requires_parent_context（是否需要回读父段落或整表条件）。
                                    'requires_parent_context': len(spans) > 1 or is_table},
                        # 写入字段 raw_path（原始快照相对项目根目录的位置）；字段 raw_sha256（原始快照的 SHA-256）。
                        'raw_path': source['snapshot_path'], 'raw_sha256': source['snapshot_sha256'],
                        # 写入字段 document_version（来源文档的版本）。
                        'document_version': source['document_version'],
                        # 写入字段 distribution（当前片段的分发条件）。
                        'distribution': source['distribution_decision'],
                        # 写入字段 review_status（原文位置或医学复核的完成状态）。
                        'review_status': 'automated_source_span_checks_only_not_clinician_reviewed',
                        # 写入字段 retrieval_ready（是否允许作为本轮检索输入）；字段 embedding_token_count（含特殊 token 的实际正文长度）。
                        'retrieval_ready': True, 'embedding_token_count': token_count,
                        # 写入字段 quality_flags（需要额外核验的解析或上下文标记）。
                        'quality_flags': (['fragment_of_long_unit'] if len(spans) > 1 else [])
                                         # 继续组装上方容器中的本行元素，保持其原始顺序和取值。
                                         + (['structured_table_not_clinically_reviewed'] if is_table else []),
                        # 写入字段 content_sha256（规范化片段正文的精确内容指纹）。
                        'content_sha256': digest}
            # 把当前结果加入 records 的末尾，保留处理顺序。
            records.append(evidence)
            # 设置by_text[digest]：evidence。
            by_text[digest] = evidence
            # 更新stats['chunks']，累计本轮处理量或内容。
            stats['chunks'] += 1
            # 更新stats['tokens']，累计本轮处理量或内容。
            stats['tokens'] += token_count
            # 更新stats['structured_table_rows']，累计本轮处理量或内容。
            stats['structured_table_rows'] += is_table
    # 当 not records 成立时，执行下面的分支。
    if not records:
        # 抛出 ValueError 并停止当前操作：no_admitted_chunks。
        raise ValueError('no_admitted_chunks')
    # 以临时文件加替换的方式保存 JSON 记录。
    dump(document_path, {'source_id': source['id'], 'source_type': kind,
                         # 写入字段 raw_path（原始快照相对项目根目录的位置）；字段 raw_sha256（原始快照的 SHA-256）。
                         'raw_path': source['snapshot_path'], 'raw_sha256': source['snapshot_sha256'],
                         # 写入字段 normalization（提取文本做了哪些可回查的规范化处理）。
                         'normalization': 'Whitespace collapsed; superscripts/subscripts and bibliography refs explicit. Not a byte-for-byte quote.',
                         # 写入字段 units（可以回到原始节点的规范化文本单元）；字段 excluded_units（未准入单元的原因和原始位置）。
                         'units': units, 'excluded_units': excluded})
    # 按该对象的 update 规则更新映射或累计统计。
    source.update({'parsed_path': str(document_path.relative_to(ROOT)),
                   # 写入字段 parsed_sha256（解析文档的内容指纹）；字段 unit_count（当前文档的规范化正文单元数）；字段 chunk_count（可检索片段数量）。
                   'parsed_sha256': file_sha(document_path), 'unit_count': len(units), 'chunk_count': len(records)})
    # 设置stats['units']：取得对象中元素或字符的数量。
    stats['units'] = len(units)
    # 设置stats['excluded_units']：取得对象中元素或字符的数量。
    stats['excluded_units'] = len(excluded)
    # 返回元组，结束本次函数调用。
    return source, records, stats, excluded


# 定义 build：组装主语料快照、子集和来源清单；不执行嵌入或检索。
def build():
    # 设置started：读取单调高精度计时器，用于计算耗时。
    started = time.perf_counter()
    # 设置pmc：解析 JSON 文本或字节，恢复为 Python 对象。
    pmc = json.loads((DATA / 'pmc_raw_manifest.json').read_text())
    # 设置spl：解析 JSON 文本或字节，恢复为 Python 对象。
    spl = json.loads((DATA / 'dailymed_raw_manifest.json').read_text())
    # 设置nih：解析 JSON 文本或字节，恢复为 Python 对象。
    nih = json.loads((DATA / 'nih_arv_raw_manifest.json').read_text())
    # 当 pmc['accepted_count'] < 10000 or spl['accepted_count'] < 1000 成立时，执行下面的分支。
    if pmc['accepted_count'] < 10000 or spl['accepted_count'] < 1000:
        # 抛出 ValueError 并停止当前操作：Raw corpus target incomplete; preserve the actual failure report before changing scope.。
        raise ValueError('Raw corpus target incomplete; preserve the actual failure report before changing scope.')
    # 设置tokenizer：按参数加载 tokenizer；这里用于长度检查，不运行嵌入模型。
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME, local_files_only=True)
    # Tokenizer only. This larger counting ceiling does not change the explicit
    # <=480 admission check or any future embedding-model context window.
    # 设置tokenizer.model_max_length：10 ** 9。
    tokenizer.model_max_length = 10**9
    # 设置来源清单：解析 JSON 文本或字节，恢复为 Python 对象。
    sources = json.loads((ROOT / 'data/v2/sources.json').read_text())
    # 设置(ids, content_hashes)：元组。
    ids, content_hashes = set(), set()
    # 设置(by_kind, excluded_docs, excluded_units)：元组。
    by_kind, excluded_docs, excluded_units = {}, [], Counter()
    # 设置aggregate：创建分类计数器，用于累计来源、分片或校验数量。
    aggregate = Counter()
    # 设置inventory：列表。
    inventory = [('paper', pmc['articles'], 'pmc'), ('drug_label', spl['labels'], 'dailymed'), ('guideline', nih['pages'], 'nih')]
    # 设置output：将目录与右侧子路径组合，得到完整输出位置。
    output = DATA / 'evidence.jsonl'
    # 进入受管理的上下文：按指定读写模式打开文件，并在 with 退出时关闭句柄。
    with output.with_suffix('.jsonl.part').open('w', encoding='utf-8') as combined:
        # 按顺序遍历(ROOT / 'data/v2/evidence.jsonl').read_text().splitlines()，本轮元素记作 line。
        for line in (ROOT / 'data/v2/evidence.jsonl').read_text().splitlines():
            # 设置item：解析 JSON 文本或字节，恢复为 Python 对象。
            item = json.loads(line)
            # 将本行给出的完整文本或字节写入已打开的文件，保留指定的分行格式。
            combined.write(line + '\n')
            # 将 HTML 节点保存为带章节、锚点和原元素位置的正文块。
            ids.add(item['id'])
            # 将 HTML 节点保存为带章节、锚点和原元素位置的正文块。
            content_hashes.add(sha(item['text'].encode()))
            # 更新aggregate['chunks']，累计本轮处理量或内容。
            aggregate['chunks'] += 1
            # 更新aggregate['tokens']，累计本轮处理量或内容。
            aggregate['tokens'] += item['embedding_token_count']
        # 设置by_kind['ct_v2_retained']：字典，保存documents、chunks。
        by_kind['ct_v2_retained'] = {'documents': len(sources), 'chunks': aggregate['chunks']}
        # 按顺序遍历inventory，本轮元素记作 (kind, receipts, output_name)。
        for kind, receipts, output_name in inventory:
            # 设置本批统计：创建分类计数器，用于累计来源、分片或校验数量。
            stats = Counter()
            # 设置part_path：将目录与右侧子路径组合，得到完整输出位置。
            part_path = DATA / f'evidence.{output_name}.jsonl'
            # 进入受管理的上下文：按指定读写模式打开文件，并在 with 退出时关闭句柄。
            with part_path.with_suffix('.jsonl.part').open('w', encoding='utf-8') as subset:
                # 按顺序遍历enumerate(receipts, 1)，本轮元素记作 (index, receipt)。
                for index, receipt in enumerate(receipts, 1):
                    # 开始需要异常处理的操作；失败时转入对应 except 分支。
                    try:
                        # 设置(source, records, doc_stats, exclusions)：为一个来源分段、做同源精确去重，并保存可回溯证据和解析单元。
                        source, records, doc_stats, exclusions = prepare_document(receipt, kind, tokenizer)
                    # 捕获这里指定的异常，并执行下方的恢复、隔离或报告逻辑。
                    except Exception as exc:
                        # 把当前结果加入 excluded_docs 的末尾，保留处理顺序。
                        excluded_docs.append({'source_id': receipt['source_id'], 'reason': type(exc).__name__ + ':' + str(exc)[:400]})
                        # 跳过当前项，继续检查本层循环中的下一项。
                        continue
                    # 把当前结果加入 sources 的末尾，保留处理顺序。
                    sources.append(source)
                    # 按顺序遍历处理记录列表，本轮元素记作 item。
                    for item in records:
                        # 当 item['id'] in ids 成立时，执行下面的分支。
                        if item['id'] in ids:
                            # 抛出 ValueError 并停止当前操作。
                            raise ValueError('duplicate_evidence_id:' + item['id'])
                        # 将 HTML 节点保存为带章节、锚点和原元素位置的正文块。
                        ids.add(item['id'])
                        # 将 HTML 节点保存为带章节、锚点和原元素位置的正文块。
                        content_hashes.add(item['content_sha256'])
                        # 设置line：将一个记录编码成一行 JSONL。
                        line = json_line(item)
                        # 将本行给出的完整文本或字节写入已打开的文件，保留指定的分行格式。
                        subset.write(line)
                        # 将本行给出的完整文本或字节写入已打开的文件，保留指定的分行格式。
                        combined.write(line)
                    # 按该对象的 update 规则更新映射或累计统计。
                    stats.update(doc_stats)
                    # 更新stats['documents']，累计本轮处理量或内容。
                    stats['documents'] += 1
                    # 按该对象的 update 规则更新映射或累计统计。
                    excluded_units.update(e['reason'] for e in exclusions)
                    # 当 index % 250 == 0 or index == len(receipts) 成立时，执行下面的分支。
                    if index % 250 == 0 or index == len(receipts):
                        # 以临时文件加替换的方式保存 JSON 记录。
                        dump(DATA / 'research/build_progress.json', {'kind': kind, 'processed': index, 'stats': dict(stats), 'excluded_documents': len(excluded_docs)})
                        # 打印当前进度、输出文件位置或核验结果，方便观察执行状态。
                        print('parse', kind, index, json.dumps(dict(stats)), flush=True)
            # 将临时文件提交或改名到指定位置。
            part_path.with_suffix('.jsonl.part').replace(part_path)
            # 设置by_kind[kind]：创建或复制字典。
            by_kind[kind] = dict(stats)
            # 按该对象的 update 规则更新映射或累计统计。
            aggregate.update(stats)
    # 将临时文件提交或改名到指定位置。
    output.with_suffix('.jsonl.part').replace(output)
    # 以临时文件加替换的方式保存 JSON 记录。
    dump(DATA / 'sources.json', sources)
    # Existing gold IDs stay exactly as labeled; no answer is used for selecting
    # the principal corpus. The original holdout and MIRAGE files stay separate.
    # 设置dev：将目录与右侧子路径组合，得到完整输出位置。
    dev = ROOT / 'data/v2/cases.dev.jsonl'
    # 将给定字节写入指定文件。
    (DATA / 'cases.ct.dev.jsonl').write_bytes(dev.read_bytes())
    # 以临时文件加替换的方式保存 JSON 记录。
    dump(DATA / 'exclusions.json', {'documents': excluded_docs, 'unit_reason_counts': dict(excluded_units),
                                   # 写入字段 raw_pmc_exclusion_count（PMC原始下载阶段未通过的数量）。
                                   'raw_pmc_exclusion_count': len(json.loads((DATA / 'research/pmc_exclusions.json').read_text())['excluded_or_failed']),
                                   # 写入字段 raw_spl_exclusion_count（SPL原始下载阶段未通过的数量）。
                                   'raw_spl_exclusion_count': len(spl['excluded']),
                                   # 写入字段 nih_download_failures（NIH来源未能取得原文的失败记录）。
                                   'nih_download_failures': nih['failures']})
    # 设置files：列表。
    files = ['evidence.jsonl', 'evidence.pmc.jsonl', 'evidence.dailymed.jsonl', 'evidence.nih.jsonl', 'sources.json', 'cases.ct.dev.jsonl', 'exclusions.json']
    # 设置report：字典，保存snapshot_date、实际构建时间的 UTC 记录、当前处理或完成状态、入库来源数量、可检索片段数量等信息。
    report = {'snapshot_date': DATE, 'built_at_utc': datetime.now(timezone.utc).isoformat(),
              # 写入字段 status（当前处理或完成状态）。
              'status': 'built_pending_independent_validation',
              # 写入字段 source_count（入库来源数量）；字段 chunk_count（可检索片段数量）。
              'source_count': len(sources), 'chunk_count': aggregate['chunks'],
              # 写入字段 global_unique_exact_text_count（跨来源统计的不同正文数量，不等于独立医学知识数）；字段 by_collection（分别按语料集合汇总的统计）。
              'global_unique_exact_text_count': len(content_hashes), 'by_collection': by_kind,
              # 写入字段 total_embedding_tokens（文档分词的累计数量，不是生成API账单）；字段 max_tokens_policy（本版本片段准入的token上限规则）。
              'total_embedding_tokens': aggregate['tokens'], 'max_tokens_policy': MAX_TOKENS,
              # 写入字段 embedding_model（计数或编码使用的模型名称）；字段 embedding_execution（是否真正执行过嵌入模型）。
              'embedding_model': TOKENIZER_NAME, 'embedding_execution': 'not_run_tokenizer_only',
              # 写入字段 vector_float32_bytes_estimate（仅向量矩阵的预计字节数，不含索引和程序对象）。
              'vector_float32_bytes_estimate': aggregate['chunks'] * 384 * 4,
              # 写入字段 excluded_documents（解析或准入未通过的文档数量）；字段 excluded_unit_reasons（按原因汇总的单元隔离数量）。
              'excluded_documents': len(excluded_docs), 'excluded_unit_reasons': dict(excluded_units),
              # 写入字段 baseline_comparability（本语料与原始MedRAG设置的可比性边界）。
              'baseline_comparability': 'custom corpus; not original MedRAG corpus reproduction',
              # 写入字段 benchmark_access（数据准备阶段是否读取基准题的说明）。
              'benchmark_access': 'MIRAGE questions/options/answers never read by this pipeline',
              # 写入字段 clinical_review（独立医生复核的实际完成状态）。
              'clinical_review': 'none; no clinical correctness claim',
              # 写入字段 files（需要固定版本的文件清单）；字段 sha256（文件或响应的 SHA-256）；字段 bytes（文件原始字节数）。
              'files': {f: {'sha256': file_sha(DATA / f), 'bytes': (DATA / f).stat().st_size} for f in files},
              # 写入字段 code_sha256（构建所用各个源代码文件的指纹）。
              'code_sha256': {f: file_sha(ROOT / f) for f in ['scripts/data/prepare_medical_corpus.py', 'scripts/data/prepare_drug_sources.py', 'scripts/data/medical_corpus_parsing.py', 'scripts/data/build_medical_corpus.py']},
              # 写入字段 build_seconds（本次数据构建实际耗时秒数）。
              'build_seconds': round(time.perf_counter() - started, 3)}
    # 以临时文件加替换的方式保存 JSON 记录。
    dump(DATA / 'corpus_manifest.json', report)
    # 打印当前进度、输出文件位置或核验结果，方便观察执行状态。
    print(json.dumps({k: report[k] for k in ['source_count', 'chunk_count', 'global_unique_exact_text_count', 'excluded_documents', 'build_seconds']}, ensure_ascii=False), flush=True)
    # 返回report，结束本次函数调用。
    return report


# 当 __name__ == '__main__' 成立时，执行下面的分支。
if __name__ == '__main__':
    # 读取命令行参数；--help 会显示帮助并退出。
    argparse.ArgumentParser(description=__doc__).parse_args()
    # 组装主语料快照、子集和来源清单；不执行嵌入或检索。
    build()

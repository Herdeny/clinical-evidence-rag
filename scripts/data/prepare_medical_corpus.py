# 下面的文档字符串说明本模块、类或函数的用途和适用边界。
"""Prepare a licensed PMC corpus without reading benchmark questions or running models.

Data preparation is assistant-owned; retrieval, scoring and Agent code stay with
the learner. Uses only the official ESearch and anonymous PMC Cloud interfaces.
"""

# 导入argparse 模块。
import argparse
# 从 concurrent.futures 中的指定接口导入 ThreadPoolExecutor、as_completed。
from concurrent.futures import ThreadPoolExecutor, as_completed
# 导入内容指纹工具。
import hashlib
# 导入JSON 编解码工具。
import json
# 导入路径对象 Path，便于定位脚本、组合目录并读写文件。
from pathlib import Path
# 导入正则表达式工具，用于匹配标题或规范化空白。
import re
# 导入线程本地状态工具。
import threading
# 导入耗时测量和请求间隔工具。
import time
# 从 urllib.parse 中的指定接口导入 urlsplit、parse_qs。
from urllib.parse import urlsplit, parse_qs

# 从 lxml 中的指定接口导入 etree。
from lxml import etree
# 导入公开来源的 HTTP 下载客户端。
import requests
# 从 requests.adapters 中的指定接口导入 HTTPAdapter。
from requests.adapters import HTTPAdapter
# 从 urllib3.util.retry 中的指定接口导入 Retry。
from urllib3.util.retry import Retry

# 从 scripts/data 的位置向上两级确定项目根目录，让数据路径不随启动目录改变。
ROOT = Path(__file__).resolve().parents[2]
# 设置v3 数据目录：将目录与右侧子路径组合，得到完整输出位置。
DATA = ROOT / "data/v3"
# 固定本次采样快照及查询截止日期；不是每次运行时自动变化的当前日期。
DATE = "2026-11-18"
# 指定 PMC 官方开放语料桶的匿名 HTTPS 下载入口。
S3 = "https://pmc-oa-opendata.s3.amazonaws.com/"
# 指定 NCBI ESearch 官方候选检索 API。
ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
# 限制单个下载响应的最大字节数，超限时中止并记录失败。
MAX_BYTES = 12 * 1024 * 1024
# 固定 PMC 下载允许的许可类型。
ALLOWED_LICENSES = {"CC BY", "CC0"}
# 固定独立医学检索主题与标题关键词，避免按测试题挑语料。
TOPICS = {
    # 为 anatomy 主题设置标题检索词，形成独立采样分层。
    "anatomy": ["anatomy", "anatomical"],
    # 为 physiology 主题设置标题检索词，形成独立采样分层。
    "physiology": ["physiology", "physiological"],
    # 为 biochemistry_metabolism 主题设置标题检索词，形成独立采样分层。
    "biochemistry_metabolism": ["biochemistry", "metabolism"],
    # 为 genetics 主题设置标题检索词，形成独立采样分层。
    "genetics": ["genetic", "genetics"],
    # 为 immunology 主题设置标题检索词，形成独立采样分层。
    "immunology": ["immunology", "immunity"],
    # 为 microbiology 主题设置标题检索词，形成独立采样分层。
    "microbiology": ["bacterial infection", "microbiology"],
    # 为 pharmacology 主题设置标题检索词，形成独立采样分层。
    "pharmacology": ["pharmacology", "pharmacokinetics"],
    # 为 cardiovascular 主题设置标题检索词，形成独立采样分层。
    "cardiovascular": ["cardiovascular", "heart failure"],
    # 为 respiratory 主题设置标题检索词，形成独立采样分层。
    "respiratory": ["asthma", "chronic obstructive pulmonary"],
    # 为 gastroenterology 主题设置标题检索词，形成独立采样分层。
    "gastroenterology": ["gastrointestinal", "inflammatory bowel"],
    # 为 hepatology 主题设置标题检索词，形成独立采样分层。
    "hepatology": ["liver disease", "hepatitis"],
    # 为 nephrology 主题设置标题检索词，形成独立采样分层。
    "nephrology": ["kidney disease", "renal failure"],
    # 为 endocrinology 主题设置标题检索词，形成独立采样分层。
    "endocrinology": ["diabetes", "thyroid"],
    # 为 neurology 主题设置标题检索词，形成独立采样分层。
    "neurology": ["stroke", "epilepsy"],
    # 为 psychiatry 主题设置标题检索词，形成独立采样分层。
    "psychiatry": ["depression", "schizophrenia"],
    # 为 hematology 主题设置标题检索词，形成独立采样分层。
    "hematology": ["anemia", "coagulation"],
    # 为 oncology 主题设置标题检索词，形成独立采样分层。
    "oncology": ["cancer diagnosis", "cancer treatment"],
    # 为 infectious_disease 主题设置标题检索词，形成独立采样分层。
    "infectious_disease": ["infectious disease", "viral infection"],
    # 为 hiv 主题设置标题检索词，形成独立采样分层。
    "hiv": ["HIV", "antiretroviral"],
    # 为 rheumatology 主题设置标题检索词，形成独立采样分层。
    "rheumatology": ["rheumatoid arthritis", "lupus"],
    # 为 dermatology 主题设置标题检索词，形成独立采样分层。
    "dermatology": ["psoriasis", "dermatitis"],
    # 为 musculoskeletal 主题设置标题检索词，形成独立采样分层。
    "musculoskeletal": ["osteoporosis", "osteoarthritis"],
    # 为 pediatrics 主题设置标题检索词，形成独立采样分层。
    "pediatrics": ["pediatric", "paediatric"],
    # 为 obstetrics 主题设置标题检索词，形成独立采样分层。
    "obstetrics": ["pregnancy", "obstetric"],
    # 为 gynecology 主题设置标题检索词，形成独立采样分层。
    "gynecology": ["gynecology", "ovarian"],
    # 为 urology 主题设置标题检索词，形成独立采样分层。
    "urology": ["urinary", "prostate"],
    # 为 ophthalmology 主题设置标题检索词，形成独立采样分层。
    "ophthalmology": ["glaucoma", "retinal"],
    # 为 otolaryngology 主题设置标题检索词，形成独立采样分层。
    "otolaryngology": ["hearing loss", "otolaryngology"],
    # 为 critical_care 主题设置标题检索词，形成独立采样分层。
    "critical_care": ["sepsis", "critical care"],
    # 为 perioperative 主题设置标题检索词，形成独立采样分层。
    "perioperative": ["perioperative", "anesthesia"],
    # 为 public_health 主题设置标题检索词，形成独立采样分层。
    "public_health": ["vaccination", "public health"],
    # 为 drug_interactions 主题设置标题检索词，形成独立采样分层。
    "drug_interactions": ["drug interaction", "statin"],
# 结束上方的字典或集合。
}
# 设置_local：调用 threading.local，取得该步骤的处理结果。
_local = threading.local()


# 定义 sha：计算一段字节内容的 SHA-256 指纹。
def sha(payload):
    # 返回取出已经计算好的十六进制内容指纹，结束本次函数调用。
    return hashlib.sha256(payload).hexdigest()


# 定义 dump：以临时文件加替换的方式保存 JSON 记录。
def dump(path, value):
    # 设置文件路径：创建文件路径对象，便于跨目录组合与读写。
    path = Path(path)
    # 创建输出目录，按参数允许补建父目录或复用已有目录。
    path.parent.mkdir(parents=True, exist_ok=True)
    # 设置temporary：调用 path.with_name，取得该步骤的处理结果。
    temporary = path.with_name(path.name + ".part")
    # 将给定文本写入指定文件。
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    # 将临时文件提交或改名到指定位置。
    temporary.replace(path)


# 定义 session：为当前下载线程复用带超时重试配置的 HTTP 会话。
def session():
    # 当 not hasattr(_local, 'session') 成立时，执行下面的分支。
    if not hasattr(_local, "session"):
        # 设置client：创建可复用连接的 HTTP 会话。
        client = requests.Session()
        # 设置client.headers['User-Agent']：字符串 'clinical-evidence-rag/0.1 public-source-ingestion'。
        client.headers["User-Agent"] = "clinical-evidence-rag/0.1 public-source-ingestion"
        # 设置retry：配置可重试状态码、次数、退避和服务器等待时间。
        retry = Retry(total=2, backoff_factor=0.6, status_forcelist=[429, 500, 502, 503, 504], respect_retry_after_header=True)
        # 按参数使用已配置的 HTTP 会话。
        client.mount("https://", HTTPAdapter(max_retries=retry))
        # 设置_local.session：client。
        _local.session = client
    # 返回_local.session，结束本次函数调用。
    return _local.session


# 定义 fetch：以超时、大小限制和 HTTP 状态检查下载原始字节，不绕过失败状态。
def fetch(url, *, params=None):
    # 通过 HTTP GET 获取公开来源，使用本行的参数、超时和流式读取配置。
    with session().get(url, params=params, timeout=(10, 30), stream=True) as response:
        # 遇到 HTTP 4xx／5xx 时立即抛错，不把失败页面当原文。
        response.raise_for_status()
        # 设置(pieces, size)：元组。
        pieces, size = [], 0
        # 按顺序遍历response.iter_content(65536)，本轮元素记作 piece。
        for piece in response.iter_content(65536):
            # 更新size，累计本轮处理量或内容。
            size += len(piece)
            # 当 size > MAX_BYTES 成立时，执行下面的分支。
            if size > MAX_BYTES:
                # 抛出 ValueError 并停止当前操作：source_file_exceeds_12_MiB。
                raise ValueError("source_file_exceeds_12_MiB")
            # 把当前结果加入 pieces 的末尾，保留处理顺序。
            pieces.append(piece)
        # 返回元组，结束本次函数调用。
        return b"".join(pieces), response.url


# 定义 discover：按独立医学标题主题从官方 ESearch 获取候选，不使用评测题选库。
def discover(per_topic=600):
    # 设置输出目录：将目录与右侧子路径组合，得到完整输出位置。
    folder = DATA / "research/pmc_search"
    # 创建输出目录，按参数允许补建父目录或复用已有目录。
    folder.mkdir(parents=True, exist_ok=True)
    # 设置(selections, counts)：元组。
    selections, counts = {}, {}
    # 按顺序遍历TOPICS.items()，本轮元素记作 (topic, terms)。
    for topic, terms in TOPICS.items():
        # 设置title_terms：用指定分隔符连接各段文字。
        title_terms = " OR ".join(f'"{term}"[Title]' for term in terms)
        # 设置query：f'({title_terms}) AND (cc by license[filter] OR cc0 license[filter]) AND english[Language] AND 2010/01/0…。
        query = (f'({title_terms}) AND (cc by license[filter] OR cc0 license[filter]) '
                 # 继续声明 discover 的输入参数或返回类型约定。
                 'AND english[Language] AND 2010/01/01:2026/11/18[Publication Date] NOT pmc embargo[filter]')
        # 设置文件路径：将目录与右侧子路径组合，得到完整输出位置。
        path = folder / f"{topic}.json"
        # 当 path.exists() 成立时，执行下面的分支。
        if path.exists():
            # 设置saved：解析 JSON 文本或字节，恢复为 Python 对象。
            saved = json.loads(path.read_text())
            # 当 saved['query'] != query or saved['per_topic'] != per_topic 成立时，执行下面的分支。
            if saved["query"] != query or saved["per_topic"] != per_topic:
                # 抛出 ValueError 并停止当前操作：Existing search snapshot differs; create a new dataset version。
                raise ValueError("Existing search snapshot differs; create a new dataset version")
        # 前面的条件都不满足时，执行这一分支。
        else:
            # 设置(payload, url)：调用 fetch，取得该步骤的处理结果。
            payload, url = fetch(ESEARCH, params={"db": "pmc", "retmode": "json", "retmax": per_topic, "sort": "pub date", "term": query})
            # 设置value：按键或位置读取 json.loads(payload) 中的对应内容。
            value = json.loads(payload)["esearchresult"]
            # 当 value.get('errorlist') or value.get('error') 成立时，执行下面的分支。
            if value.get("errorlist") or value.get("error"):
                # 抛出 ValueError 并停止当前操作。
                raise ValueError(f"Invalid ESearch query {topic}: {value.get('errorlist')}")
            # 设置saved：字典，保存queried_on、用于获取候选的固定查询、per_topic、来源原始链接或带章节锚点的链接、官方 API 响应的字节指纹等信息。
            saved = {"queried_on": DATE, "query": query, "per_topic": per_topic, "url": url,
                     # 写入字段 response_sha256（官方 API 响应的字节指纹）；字段 result（当前处理或检查结果）。
                     "response_sha256": sha(payload), "result": value}
            # 以临时文件加替换的方式保存 JSON 记录。
            dump(path, saved)
            # 等待指定时间，控制公共 API 的请求频率。
            time.sleep(0.4)
        # 设置处理结果：按键或位置读取 saved 中的对应内容。
        result = saved["result"]
        # 设置selections[topic]：按键或位置读取 处理结果 中的对应内容。
        selections[topic] = result["idlist"]
        # 设置counts[topic]：转为整数。
        counts[topic] = int(result["count"])
        # 打印当前进度、输出文件位置或核验结果，方便观察执行状态。
        print(f"discovery {topic}: {len(result['idlist'])} selected / {result['count']} eligible", flush=True)
    # 设置(order, tags)：元组。
    order, tags = [], {}
    # Round-robin over fixed topic lists; never use completion time or test items.
    # 按顺序遍历range(max(map(len, selections.values())))，本轮元素记作 rank。
    for rank in range(max(map(len, selections.values()))):
        # 按顺序遍历selections.items()，本轮元素记作 (topic, ids)。
        for topic, ids in selections.items():
            # 当 rank < len(ids) 成立时，执行下面的分支。
            if rank < len(ids):
                # 设置pmcid：'PMC' + ids[rank]。
                pmcid = "PMC" + ids[rank]
                # 当 pmcid not in tags 成立时，执行下面的分支。
                if pmcid not in tags:
                    # 把当前结果加入 order 的末尾，保留处理顺序。
                    order.append(pmcid)
                    # 设置tags[pmcid]：空列表。
                    tags[pmcid] = []
                # 把当前结果加入 tags[pmcid] 的末尾，保留处理顺序。
                tags[pmcid].append(topic)
    # 设置处理结果：字典，保存本轮准备记录的创建日期、selection、per_topic、eligible_counts、candidate_count等信息。
    result = {"created_on": DATE, "selection": "independent medical title strata, round-robin; no benchmark questions",
              # 写入字段 per_topic（每个医学主题最多选取多少篇候选）；字段 eligible_counts（官方查询返回的各主题可用总数）；字段 candidate_count（去重后的候选总数）。
              "per_topic": per_topic, "eligible_counts": counts, "candidate_count": len(order),
              # 写入字段 candidates（尚待下载或准入的候选记录列表）；字段 pmcid（pmcid）；字段 topics（候选论文所属的独立采样主题）；字段 selection_rank（selection_rank）。
              "candidates": [{"pmcid": key, "topics": tags[key], "selection_rank": rank} for rank, key in enumerate(order)]}
    # 以临时文件加替换的方式保存 JSON 记录。
    dump(DATA / "research/pmc_candidates.json", result)
    # 返回处理结果，结束本次函数调用。
    return result


# 定义 xml_root：安全解析 XML 字节，禁用外部实体展开和解析器联网。
def xml_root(payload):
    # 返回将原始 XML 字节解析成元素树，结束本次函数调用。
    return etree.fromstring(payload, parser=etree.XMLParser(resolve_entities=False, no_network=True, recover=False))


# 定义 article_check：检查 JATS 根节点、类型、标识、许可和正文是否满足下载准入条件。
def article_check(payload, meta):
    # 设置root：安全解析 XML 字节，禁用外部实体展开和解析器联网。
    root = xml_root(payload)
    # 当 etree.QName(root).localname != 'article' 成立时，执行下面的分支。
    if etree.QName(root).localname != "article":
        # 抛出 ValueError 并停止当前操作：not_jats_article。
        raise ValueError("not_jats_article")
    # 设置article_type：按键读取字段，缺失时使用指定默认值或 None。
    article_type = root.get("article-type", "unknown")
    # 当 article_type in {'retraction', 'correction', 'editorial', 'letter', 'expression-of-concern'} 成立时，执行下面的分支。
    if article_type in {"retraction", "correction", "editorial", "letter", "expression-of-concern"}:
        # 抛出 ValueError 并停止当前操作。
        raise ValueError("excluded_article_type:" + article_type)
    # 设置titles：按 XPath 在原始结构中查找节点或字段值。
    titles = root.xpath("./*[local-name()='front']/*[local-name()='article-meta']/*[local-name()='title-group']/*[local-name()='article-title']")
    # 设置title：用指定分隔符连接各段文字。
    title = " ".join("".join(node.itertext()) for node in titles)
    # 当 re.match('\\s*(retracted|retraction|correction|corrigendum|erratum)\\b', title, re.I) 成立时，执行下面的分支。
    if re.match(r"\s*(retracted|retraction|correction|corrigendum|erratum)\b", title, re.I):
        # 抛出 ValueError 并停止当前操作：excluded_notice_title。
        raise ValueError("excluded_notice_title")
    # 设置ids：按 XPath 在原始结构中查找节点或字段值。
    ids = root.xpath("./*[local-name()='front']/*[local-name()='article-meta']/*[local-name()='article-id']")
    # 设置pmc_ids：按遍历顺序筛选并整理 ids 中的数据。
    pmc_ids = ["PMC" + re.sub(r"\D", "", "".join(node.itertext())) for node in ids if node.get("pub-id-type") in {"pmc", "pmcid"}]
    # 当 pmc_ids and meta['pmcid'] not in pmc_ids 成立时，执行下面的分支。
    if pmc_ids and meta["pmcid"] not in pmc_ids:
        # 抛出 ValueError 并停止当前操作：xml_metadata_pmcid_mismatch。
        raise ValueError("xml_metadata_pmcid_mismatch")
    # 设置licenses：按 XPath 在原始结构中查找节点或字段值。
    licenses = root.xpath("./*[local-name()='front']/*[local-name()='article-meta']/*[local-name()='permissions']/*[local-name()='license']")
    # 设置license_links：空列表。
    license_links = []
    # 按顺序遍历licenses，本轮元素记作 node。
    for node in licenses:
        # 按顺序遍历node.iter()，本轮元素记作 element。
        for element in node.iter():
            # 按顺序遍历element.attrib.values()，本轮元素记作 value。
            for value in element.attrib.values():
                # 当 'creativecommons.org/' in value 成立时，执行下面的分支。
                if "creativecommons.org/" in value:
                    # 把当前结果加入 license_links 的末尾，保留处理顺序。
                    license_links.append(value)
    # 当 license_links and (not any((re.search('creativecommons\\.org/(licenses/by/|publicdomain/zero/)', value) … 成立时，执行下面的分支。
    if license_links and not any(re.search(r"creativecommons\.org/(licenses/by/|publicdomain/zero/)", value) for value in license_links):
        # 抛出 ValueError 并停止当前操作：xml_metadata_license_conflict。
        raise ValueError("xml_metadata_license_conflict")
    # 设置body：按 XPath 在原始结构中查找节点或字段值。
    body = root.xpath("./*[local-name()='body']")
    # 当 not body or len(' '.join((''.join(node.itertext()) for node in body))) < 600 成立时，执行下面的分支。
    if not body or len(" ".join("".join(node.itertext()) for node in body)) < 600:
        # 抛出 ValueError 并停止当前操作：insufficient_body_text。
        raise ValueError("insufficient_body_text")
    # 返回字典，保存论文原文声明的文章类型、xml_title、从 XML 收集的许可链接，结束本次函数调用。
    return {"article_type": article_type, "xml_title": title, "license_links": sorted(set(license_links))}


# 定义 metadata_eligible：按 PMC 官方元数据核对许可、开放状态及撤稿等排除条件。
def metadata_eligible(meta):
    # 返回meta.get('license_code') in ALLOWED_LICENSES and meta.get('is_pmc_openaccess') is True and (meta.get('is…，结束本次函数调用。
    return (meta.get("license_code") in ALLOWED_LICENSES and meta.get("is_pmc_openaccess") is True
            # 继续声明 metadata_eligible 的输入参数或返回类型约定。
            and meta.get("is_retracted") is False and meta.get("is_manuscript") is False
            # 继续声明 metadata_eligible 的输入参数或返回类型约定。
            and meta.get("is_historical_ocr") is False)


# 定义 metadata_options：依次提供符合准入条件的 PMC 出版版元数据。
def metadata_options(pmcid):
    # 设置first_url：S3 + f'metadata/{pmcid}.1.json'。
    first_url = S3 + f"metadata/{pmcid}.1.json"
    # 开始需要异常处理的操作；失败时转入对应 except 分支。
    try:
        # 设置(payload, url)：调用 fetch，取得该步骤的处理结果。
        payload, url = fetch(first_url)
        # 设置官方元数据：解析 JSON 文本或字节，恢复为 Python 对象。
        meta = json.loads(payload)
        # 当 metadata_eligible(meta) 成立时，执行下面的分支。
        if metadata_eligible(meta):
            # (yield (meta, payload, url))。
            yield meta, payload, url
            # 返回空结果 None，结束本次函数调用。
            return
    # 捕获这里指定的异常，并执行下方的恢复、隔离或报告逻辑。
    except requests.HTTPError as exc:
        # 当 exc.response.status_code != 404 成立时，执行下面的分支。
        if exc.response.status_code != 404:
            # 继续抛出当前异常，保留最初失败原因。
            raise
    # 设置(payload, _)：调用 fetch，取得该步骤的处理结果。
    payload, _ = fetch(S3, params={"list-type": "2", "prefix": f"metadata/{pmcid}.", "max-keys": 100})
    # 设置listing：安全解析 XML 字节，禁用外部实体展开和解析器联网。
    listing = xml_root(payload)
    # 设置keys：按 XPath 在原始结构中查找节点或字段值。
    keys = listing.xpath(".//*[local-name()='Key']/text()")
    # 按顺序遍历sorted(keys)，本轮元素记作 key。
    for key in sorted(keys):
        # 当 key == f'metadata/{pmcid}.1.json' 成立时，执行下面的分支。
        if key == f"metadata/{pmcid}.1.json":
            # 跳过当前项，继续检查本层循环中的下一项。
            continue
        # 设置(raw, url)：调用 fetch，取得该步骤的处理结果。
        raw, url = fetch(S3 + key)
        # 设置官方元数据：解析 JSON 文本或字节，恢复为 Python 对象。
        meta = json.loads(raw)
        # 当 metadata_eligible(meta) 成立时，执行下面的分支。
        if metadata_eligible(meta):
            # (yield (meta, raw, url))。
            yield meta, raw, url


# 定义 download_article：下载或复核一篇论文的官方元数据与 XML，保留完整采集回执。
def download_article(candidate):
    # 设置pmcid：按键或位置读取 当前候选 中的对应内容。
    pmcid = candidate["pmcid"]
    # 设置输出目录：将目录与右侧子路径组合，得到完整输出位置。
    folder = DATA / "raw/pmc" / pmcid
    # 设置receipt_path：将目录与右侧子路径组合，得到完整输出位置。
    receipt_path = folder / "receipt.json"
    # 开始需要异常处理的操作；失败时转入对应 except 分支。
    try:
        # 当 receipt_path.exists() 成立时，执行下面的分支。
        if receipt_path.exists():
            # 设置采集回执：解析 JSON 文本或字节，恢复为 Python 对象。
            receipt = json.loads(receipt_path.read_text())
            # 按顺序遍历('metadata', 'xml')，本轮元素记作 key。
            for key in ("metadata", "xml"):
                # 当 sha((ROOT / receipt[key]['path']).read_bytes()) != receipt[key]['sha256'] 成立时，执行下面的分支。
                if sha((ROOT / receipt[key]["path"]).read_bytes()) != receipt[key]["sha256"]:
                    # 抛出 ValueError 并停止当前操作：cached_source_fingerprint_changed。
                    raise ValueError("cached_source_fingerprint_changed")
            # 返回字典，保存，结束本次函数调用。
            return {**receipt, **candidate}
        # 按顺序遍历metadata_options(pmcid)，本轮元素记作 (meta, metadata_payload, metadata_url)。
        for meta, metadata_payload, metadata_url in metadata_options(pmcid):
            # 设置parsed：拆分 URL 的协议、域名、路径和查询参数。
            parsed = urlsplit(meta["xml_url"])
            # 当 parsed.scheme != 's3' or parsed.netloc != 'pmc-oa-opendata' 成立时，执行下面的分支。
            if parsed.scheme != "s3" or parsed.netloc != "pmc-oa-opendata":
                # 抛出 ValueError 并停止当前操作：unexpected_official_xml_location。
                raise ValueError("unexpected_official_xml_location")
            # 设置xml_url：S3 + parsed.path.lstrip('/')。
            xml_url = S3 + parsed.path.lstrip("/")
            # 设置(payload, final_url)：调用 fetch，取得该步骤的处理结果。
            payload, final_url = fetch(xml_url)
            # 设置md5：按键或位置读取 parse_qs(parsed.query).get('md5', [None]) 中的对应内容。
            md5 = parse_qs(parsed.query).get("md5", [None])[0]
            # 当 md5 and hashlib.md5(payload).hexdigest() != md5 成立时，执行下面的分支。
            if md5 and hashlib.md5(payload).hexdigest() != md5:
                # 抛出 ValueError 并停止当前操作：provider_md5_mismatch。
                raise ValueError("provider_md5_mismatch")
            # 设置checked：检查 JATS 根节点、类型、标识、许可和正文是否满足下载准入条件。
            checked = article_check(payload, meta)
            # 创建输出目录，按参数允许补建父目录或复用已有目录。
            folder.mkdir(parents=True, exist_ok=True)
            # 设置(meta_path, article_path)：元组。
            meta_path, article_path = folder / "metadata.json", folder / "article.xml"
            # 将给定字节写入指定文件。
            meta_path.write_bytes(metadata_payload)
            # 将给定字节写入指定文件。
            article_path.write_bytes(payload)
            # 设置采集回执：字典，保存本轮采集使用的快照日期、当前处理或完成状态、PMC 文章标识、version、来源唯一标识，用于反查原始文件等信息。
            receipt = {"downloaded_on": DATE, "status": "licensed_article_raw_ready", "pmcid": pmcid,
                       # 写入字段 version（原文或元数据结构声明的版本号）；字段 source_id（source_id）。
                       "version": meta["version"], "source_id": f"pmc:{pmcid}.v{meta['version']}",
                       # 写入字段 license_code（官方元数据声明的许可类型）。
                       "license_code": meta["license_code"], **checked, **candidate,
                       # 写入字段 metadata（官方元数据快照的位置和指纹）；字段 path（相对项目根目录的文件位置）；字段 url（来源原始链接或带章节锚点的链接）；字段 sha256（文件或响应的 SHA-256）；字段 bytes（文件原始字节数）。
                       "metadata": {"path": str(meta_path.relative_to(ROOT)), "url": metadata_url, "sha256": sha(metadata_payload), "bytes": len(metadata_payload)},
                       # 写入字段 xml（原始 XML 的路径、指纹和来源链接）；字段 path（相对项目根目录的文件位置）；字段 url（来源原始链接或带章节锚点的链接）；字段 sha256（文件或响应的 SHA-256）；字段 provider_md5（官方地址提供的MD5值，仅核对字节完整性）；字段 bytes（文件原始字节数）。
                       "xml": {"path": str(article_path.relative_to(ROOT)), "url": final_url, "sha256": sha(payload), "provider_md5": md5, "bytes": len(payload)}}
            # 以临时文件加替换的方式保存 JSON 记录。
            dump(receipt_path, receipt)
            # 返回采集回执，结束本次函数调用。
            return receipt
        # 抛出 ValueError 并停止当前操作：no_eligible_published_cc_by_or_cc0_version。
        raise ValueError("no_eligible_published_cc_by_or_cc0_version")
    # 捕获这里指定的异常，并执行下方的恢复、隔离或报告逻辑。
    except Exception as exc:
        # 返回字典，保存当前处理或完成状态、失败时的异常类型、拒绝、隔离或失败的具体原因，结束本次函数调用。
        return {**candidate, "status": "excluded_or_failed", "error_type": type(exc).__name__, "reason": str(exc)[:400]}


# 定义 download：按固定候选顺序分批并发下载，达到原文目标后保存选择清单。
def download(target=10000, workers=8):
    # 设置candidates：按键或位置读取 json.loads((DATA / 'research/pmc_candidates.json').read_text()) 中的对应内容。
    candidates = json.loads((DATA / "research/pmc_candidates.json").read_text())["candidates"]
    # 设置(accepted, failures)：元组。
    accepted, failures = [], []
    # 按顺序遍历range(0, len(candidates), 256)，本轮元素记作 start。
    for start in range(0, len(candidates), 256):
        # 设置当前批次：按键或位置读取 candidates 中的对应内容。
        batch = candidates[start:start + 256]
        # 进入受管理的上下文：创建有并发数上限的下载线程池。
        with ThreadPoolExecutor(max_workers=workers) as pool:
            # 设置futures：按遍历顺序筛选并整理 当前批次 中的数据。
            futures = [pool.submit(download_article, item) for item in batch]
            # 按顺序遍历as_completed(futures)，本轮元素记作 future。
            for future in as_completed(futures):
                # 设置item：取得并发任务返回的处理结果。
                item = future.result()
                # 把当前结果加入 (accepted if item['status'] == 'licensed_article_raw_ready' else failures) 的末尾，保留处理顺序。
                (accepted if item["status"] == "licensed_article_raw_ready" else failures).append(item)
        # 调用 accepted.sort，取得该步骤的处理结果。
        accepted.sort(key=lambda item: item["selection_rank"])
        # 设置progress：字典，保存updated_on、本次准备任务的目标数量、processed、accepted、excluded_or_failed。
        progress = {"updated_on": DATE, "target": target, "processed": start + len(batch), "accepted": len(accepted), "excluded_or_failed": len(failures)}
        # 以临时文件加替换的方式保存 JSON 记录。
        dump(DATA / "research/pmc_download_progress.json", progress)
        # 打印当前进度、输出文件位置或核验结果，方便观察执行状态。
        print("download", json.dumps(progress), flush=True)
        # 当 len(accepted) >= target 成立时，执行下面的分支。
        if len(accepted) >= target:
            # 退出当前这一层循环，停止继续收集本层记录。
            break
    # 设置selected：按键或位置读取 accepted 中的对应内容。
    selected = accepted[:target]
    # 设置来源或构建清单：字典，保存本轮准备记录的创建日期、当前处理或完成状态、本次准备任务的目标数量、通过本阶段检查的记录数量、source等信息。
    manifest = {"created_on": DATE, "status": "raw_target_complete" if len(selected) == target else "raw_target_incomplete",
                # 写入字段 target（本次准备任务的目标数量）；字段 accepted_count（通过本阶段检查的记录数量）；字段 source（当前来源或接口名称）。
                "target": target, "accepted_count": len(selected), "source": "official PMC Cloud",
                # 写入字段 version_rule（论文出版版本的选择规则）。
                "version_rule": "eligible published v1 when available, otherwise first eligible published metadata version; snapshot, not a latest-version guarantee",
                # 写入字段 license_allowlist（允许收录的许可类型白名单）；字段 selection_uses_benchmark_content（选库是否使用了外部测试题内容）。
                "license_allowlist": sorted(ALLOWED_LICENSES), "selection_uses_benchmark_content": False,
                # 写入字段 raw_xml_bytes（选中XML文件的总字节数）。
                "raw_xml_bytes": sum(item["xml"]["bytes"] for item in selected),
                # 写入字段 articles（本轮选择的论文原始快照列表）；字段 reserve_count（额外下载但没有进入主选择清单的记录数）。
                "articles": selected, "reserve_count": max(0, len(accepted) - target)}
    # 以临时文件加替换的方式保存 JSON 记录。
    dump(DATA / "pmc_raw_manifest.json", manifest)
    # 以临时文件加替换的方式保存 JSON 记录。
    dump(DATA / "research/pmc_exclusions.json", {"excluded_or_failed": failures})
    # 打印当前进度、输出文件位置或核验结果，方便观察执行状态。
    print("raw corpus", json.dumps({key: manifest[key] for key in ("status", "accepted_count", "raw_xml_bytes", "reserve_count")}), flush=True)
    # 返回来源或构建清单，结束本次函数调用。
    return manifest


# 当 __name__ == '__main__' 成立时，执行下面的分支。
if __name__ == "__main__":
    # 设置parser：调用 argparse.ArgumentParser，取得该步骤的处理结果。
    parser = argparse.ArgumentParser()
    # 定义这一项命令行参数的名称、可选值和默认值。
    parser.add_argument("--phase", choices=["discover", "download"], required=True)
    # 定义这一项命令行参数的名称、可选值和默认值。
    parser.add_argument("--per-topic", type=int, default=600)
    # 定义这一项命令行参数的名称、可选值和默认值。
    parser.add_argument("--target", type=int, default=10000)
    # 定义这一项命令行参数的名称、可选值和默认值。
    parser.add_argument("--workers", type=int, default=8)
    # 设置args：读取命令行参数；--help 会显示帮助并退出。
    args = parser.parse_args()
    # 当 args.phase == 'discover' 成立时，执行下面的分支。
    if args.phase == "discover":
        # 设置处理结果：按独立医学标题主题从官方 ESearch 获取候选，不使用评测题选库。
        result = discover(args.per_topic)
        # 打印当前进度、输出文件位置或核验结果，方便观察执行状态。
        print("candidate_count", result["candidate_count"])
    # 前面的条件都不满足时，执行这一分支。
    else:
        # 按固定候选顺序分批并发下载，达到原文目标后保存选择清单。
        download(args.target, args.workers)

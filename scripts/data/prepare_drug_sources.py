# 下面的文档字符串说明本模块、类或函数的用途和适用边界。
"""Download identity-preserving SPL snapshots and official NIH guideline pages.

No clinical answers, retrieval or models. SPL redistribution is not assumed to
be authorized merely because an API returns a document.
"""

# 导入argparse 模块。
import argparse
# 从 concurrent.futures 中的指定接口导入 ThreadPoolExecutor、as_completed。
from concurrent.futures import ThreadPoolExecutor, as_completed
# 导入JSON 编解码工具。
import json
# 导入路径对象 Path，便于定位脚本、组合目录并读写文件。
from pathlib import Path
# 导入正则表达式工具，用于匹配标题或规范化空白。
import re
# 导入耗时测量和请求间隔工具。
import time
# 从 urllib.parse 中的指定接口导入 urljoin、urlsplit。
from urllib.parse import urljoin, urlsplit

# 从 bs4 中的指定接口导入 BeautifulSoup。
from bs4 import BeautifulSoup
# 从 lxml 中的指定接口导入 etree。
from lxml import etree

# 从 数据准备包中的公共工具导入 DATA、DATE、ROOT、dump、fetch、sha、xml_root。
from scripts.data.prepare_medical_corpus import DATA, DATE, ROOT, dump, fetch, sha, xml_root

# 指定 DailyMed 官方 v2 Web Services 的地址前缀。
API = "https://dailymed.nlm.nih.gov/dailymed/services/v2/"
# 限定只沿 NIH 成人／青少年 ARV 指南路径采集，防止抓取范围扩大。
GUIDE_PREFIX = "https://clinicalinfo.hiv.gov/en/guidelines/hiv-clinical-guidelines-adult-and-adolescent-arv/"
# 固定 DailyMed 药物检索词，用于分层获取产品候选。
TERMS = [
    # 继续组装上方容器中的本行元素，保持其原始顺序和取值。
    "atorvastatin", "rosuvastatin", "simvastatin", "pravastatin", "lovastatin", "pitavastatin", "fluvastatin",
    # 继续组装上方容器中的本行元素，保持其原始顺序和取值。
    "ritonavir", "cobicistat", "darunavir", "atazanavir", "elvitegravir", "dolutegravir", "bictegravir",
    # 继续组装上方容器中的本行元素，保持其原始顺序和取值。
    "efavirenz", "rilpivirine", "tenofovir", "emtricitabine", "lamivudine", "abacavir",
    # 继续组装上方容器中的本行元素，保持其原始顺序和取值。
    "warfarin", "apixaban", "rivaroxaban", "dabigatran", "clopidogrel",
    # 继续组装上方容器中的本行元素，保持其原始顺序和取值。
    "metformin", "insulin glargine", "lisinopril", "amlodipine", "metoprolol",
    # 继续组装上方容器中的本行元素，保持其原始顺序和取值。
    "omeprazole", "famotidine", "clarithromycin", "rifampin", "rifabutin",
    # 继续组装上方容器中的本行元素，保持其原始顺序和取值。
    "tacrolimus", "cyclosporine", "carbamazepine", "phenytoin", "levothyroxine",
# 结束上方的列表或索引。
]


# 定义 direct：按 XML 局部标签名取得当前节点的直接子元素。
def direct(root, name):
    # 返回按 XPath 在原始结构中查找节点或字段值，结束本次函数调用。
    return root.xpath(f"./*[local-name()='{name}']")


# 定义 text：提取 XML 节点中的全部文字并合并空白。
def text(node):
    # 返回去掉文字首尾的空白，结束本次函数调用。
    return re.sub(r"\s+", " ", "".join(node.itertext())).strip()


# 定义 discover_labels：按预先确定的药物词查询 DailyMed，按 setID 去重形成候选池。
def discover_labels(per_term=100):
    # 设置(lists, totals)：元组。
    lists, totals = {}, {}
    # 设置输出目录：将目录与右侧子路径组合，得到完整输出位置。
    folder = DATA / "research/dailymed_search"
    # 按顺序遍历TERMS，本轮元素记作 term。
    for term in TERMS:
        # 设置文件路径：将目录与右侧子路径组合，得到完整输出位置。
        path = folder / (term.replace(" ", "_") + ".json")
        # 当 path.exists() 成立时，执行下面的分支。
        if path.exists():
            # 设置saved：解析 JSON 文本或字节，恢复为 Python 对象。
            saved = json.loads(path.read_text())
        # 前面的条件都不满足时，执行这一分支。
        else:
            # 设置(payload, url)：调用 fetch，取得该步骤的处理结果。
            payload, url = fetch(API + "spls.json", params={"drug_name": term, "doctype": "34391-3", "pagesize": per_term, "page": 1})
            # 设置value：解析 JSON 文本或字节，恢复为 Python 对象。
            value = json.loads(payload)
            # 设置saved：字典，保存queried_on、term、来源原始链接或带章节锚点的链接、官方 API 响应的字节指纹、response。
            saved = {"queried_on": DATE, "term": term, "url": url, "response_sha256": sha(payload), "response": value}
            # 以临时文件加替换的方式保存 JSON 记录。
            dump(path, saved)
            # 等待指定时间，控制公共 API 的请求频率。
            time.sleep(0.3)
        # 设置lists[term]：按键读取字段，缺失时使用指定默认值或 None。
        lists[term] = saved["response"].get("data", [])
        # 设置totals[term]：按键读取字段，缺失时使用指定默认值或 None。
        totals[term] = saved["response"].get("metadata", {}).get("total_elements", 0)
        # 打印当前进度、输出文件位置或核验结果，方便观察执行状态。
        print(f"SPL discovery {term}: {len(lists[term])} selected / {totals[term]} available", flush=True)
    # 设置(order, records)：元组。
    order, records = [], {}
    # 按顺序遍历range(max(map(len, lists.values())))，本轮元素记作 rank。
    for rank in range(max(map(len, lists.values()))):
        # 按顺序遍历lists.items()，本轮元素记作 (term, entries)。
        for term, entries in lists.items():
            # 当 rank < len(entries) 成立时，执行下面的分支。
            if rank < len(entries):
                # 设置entry：按键或位置读取 entries 中的对应内容。
                entry = entries[rank]
                # 设置key：按键或位置读取 entry 中的对应内容。
                key = entry["setid"]
                # 当 key not in records 成立时，执行下面的分支。
                if key not in records:
                    # 把当前结果加入 order 的末尾，保留处理顺序。
                    order.append(key)
                    # 设置records[key]：字典，保存queried_terms。
                    records[key] = {**entry, "queried_terms": []}
                # 把当前结果加入 records[key]['queried_terms'] 的末尾，保留处理顺序。
                records[key]["queried_terms"].append(term)
    # 设置处理结果：字典，保存本轮准备记录的创建日期、selection、per_term、term_total_counts、candidates。
    result = {"created_on": DATE, "selection": "independent active-ingredient strata, current API first page, round-robin; not benchmark-driven",
              # 写入字段 per_term（每个药物检索词最多选取多少条候选）；字段 term_total_counts（每个药物词在官方API中的候选总量）；字段 candidates（尚待下载或准入的候选记录列表）。
              "per_term": per_term, "term_total_counts": totals, "candidates": [records[key] for key in order]}
    # 以临时文件加替换的方式保存 JSON 记录。
    dump(DATA / "research/dailymed_candidates.json", result)
    # 返回处理结果，结束本次函数调用。
    return result


# 定义 parse_identity：从 SPL 核对 setID、版本、产品类别、成分、剂型和产品代码。
def parse_identity(payload, expected_setid):
    # 设置root：安全解析 XML 字节，禁用外部实体展开和解析器联网。
    root = xml_root(payload)
    # 当 etree.QName(root).localname != 'document' 成立时，执行下面的分支。
    if etree.QName(root).localname != "document":
        # 抛出 ValueError 并停止当前操作：not_spl_document。
        raise ValueError("not_spl_document")
    # 设置(set_ids, versions, effective, codes)：按遍历顺序筛选并整理 ('setId', 'versionNumber', 'effectiveTime', 'code') 中的数据。
    set_ids, versions, effective, codes = (direct(root, key) for key in ("setId", "versionNumber", "effectiveTime", "code"))
    # 当 not set_ids or set_ids[0].get('root', '').lower() != expected_setid.lower() 成立时，执行下面的分支。
    if not set_ids or set_ids[0].get("root", "").lower() != expected_setid.lower():
        # 抛出 ValueError 并停止当前操作：spl_setid_mismatch。
        raise ValueError("spl_setid_mismatch")
    # 当 not codes or codes[0].get('code') != '34391-3' 成立时，执行下面的分支。
    if not codes or codes[0].get("code") != "34391-3":
        # 抛出 ValueError 并停止当前操作：not_human_prescription_label。
        raise ValueError("not_human_prescription_label")
    # 当 not versions 成立时，执行下面的分支。
    if not versions:
        # 抛出 ValueError 并停止当前操作：missing_spl_version。
        raise ValueError("missing_spl_version")
    # 设置categories：按 XPath 在原始结构中查找节点或字段值。
    categories = root.xpath(".//*[local-name()='marketingCategory' or local-name()='approval']/*[local-name()='code']")
    # 设置category_names：按指定排序规则返回有序结果。
    category_names = sorted({node.get("displayName", "") for node in categories})
    # 当 not set(category_names) & {'NDA', 'ANDA', 'BLA'} 成立时，执行下面的分支。
    if not set(category_names) & {"NDA", "ANDA", "BLA"}:
        # 抛出 ValueError 并停止当前操作：no_label_reported_nda_anda_or_bla。
        raise ValueError("no_label_reported_nda_anda_or_bla")
    # 设置names：按 XPath 在原始结构中查找节点或字段值。
    names = root.xpath(".//*[local-name()='ingredient'][starts-with(@classCode,'ACTI')]//*[local-name()='ingredientSubstance']/*[local-name()='name']")
    # 设置labelers：按 XPath 在原始结构中查找节点或字段值。
    labelers = root.xpath("./*[local-name()='author']//*[local-name()='representedOrganization']/*[local-name()='name']")
    # 设置products：按 XPath 在原始结构中查找节点或字段值。
    products = root.xpath(".//*[local-name()='manufacturedProduct'][*[local-name()='code']]")
    # 设置product_info：空列表。
    product_info = []
    # 按顺序遍历products，本轮元素记作 product。
    for product in products:
        # 设置children：按 XML 局部标签名取得当前节点的直接子元素。
        children = direct(product, "code")
        # 设置product_names：按 XML 局部标签名取得当前节点的直接子元素。
        product_names = direct(product, "name")
        # 设置forms：按 XML 局部标签名取得当前节点的直接子元素。
        forms = direct(product, "formCode")
        # 设置ingredients：空列表。
        ingredients = []
        # 按顺序遍历product.xpath("./*[local-name()='ingredient'][starts-with(@classCode,'ACTI')]")，本轮元素记作 ingredient。
        for ingredient in product.xpath("./*[local-name()='ingredient'][starts-with(@classCode,'ACTI')]"):
            # 设置substances：按 XPath 在原始结构中查找节点或字段值。
            substances = ingredient.xpath("./*[local-name()='ingredientSubstance']/*[local-name()='name']")
            # 把当前结果加入 ingredients 的末尾，保留处理顺序。
            ingredients.append({"name": text(substances[0]) if substances else None,
                                # 写入字段 class_code（SPL成分节点声明的类别代码）。
                                "class_code": ingredient.get("classCode"),
                                # 写入字段 quantity（源标签的强度分子和分母结构）；字段 component（强度结构中的分子或分母名称）。
                                "quantity": [{"component": etree.QName(node).localname, **dict(node.attrib)}
                                             # 推导式继续按此处的顺序遍历，生成上方表达式所需的数据。
                                             for node in ingredient.xpath("./*[local-name()='quantity']/*")],
                                # 写入字段 active_moieties（源标签声明的活性基团）。
                                "active_moieties": ingredient.xpath(".//*[local-name()='activeMoiety']/*[local-name()='name']/text()")})
        # 把当前结果加入 product_info 的末尾，保留处理顺序。
        product_info.append({"code": children[0].get("code") if children else None,
                             # 写入字段 name（该对象在原文中的名称）。
                             "name": text(product_names[0]) if product_names else None,
                             # 写入字段 form（源标签中的剂型名称）。
                             "form": forms[0].get("displayName") if forms else None,
                             # 写入字段 ingredients（具体产品的成分和强度结构）。
                             "ingredients": ingredients})
    # 设置titles：按 XML 局部标签名取得当前节点的直接子元素。
    titles = direct(root, "title")
    # 返回字典，保存DailyMed 产品标签集合标识、SPL 文档版本号、SPL 声明的有效时间、原始文档或章节标题、标签中的活性成分名称等信息，结束本次函数调用。
    return {"setid": expected_setid.lower(), "spl_version": versions[0].get("value"),
            # 写入字段 effective_time（SPL 声明的有效时间）。
            "effective_time": effective[0].get("value") if effective else None,
            # 写入字段 title（原始文档或章节标题）。
            "title": text(titles[0]) if titles else None,
            # 写入字段 active_ingredients（标签中的活性成分名称）；字段 labelers（标签提交机构名称）。
            "active_ingredients": sorted(set(map(text, names))), "labelers": sorted(set(map(text, labelers))),
            # 写入字段 products（保留强度、剂型和代码的产品记录）；字段 marketing_category_reported（标签自报的 NDA、ANDA 或 BLA 类别）。
            "products": product_info, "marketing_category_reported": category_names,
            # 写入字段 application_identifiers_reported（标签自报的申请或批准文号）。
            "application_identifiers_reported": root.xpath(".//*[local-name()='approval']/*[local-name()='id']/@extension"),
            # 写入字段 approval_verification（是否另行核验批准状态的说明）。
            "approval_verification": "label-reported category only; not independently verified against Drugs@FDA",
            # 写入字段 label_status（DailyMed in-use 标签状态的适用边界）。
            "label_status": "DailyMed in-use submitted labeling snapshot, not a guarantee of current FDA-approved labeling"}


# 定义 download_label：下载或复核一个产品的 SPL XML，并保存版本与身份回执。
def download_label(candidate):
    # 设置setid：按键或位置读取 当前候选 中的对应内容。
    setid = candidate["setid"]
    # 设置输出目录：将目录与右侧子路径组合，得到完整输出位置。
    folder = DATA / "raw/dailymed" / setid
    # 设置receipt_path：将目录与右侧子路径组合，得到完整输出位置。
    receipt_path = folder / "receipt.json"
    # 开始需要异常处理的操作；失败时转入对应 except 分支。
    try:
        # 当 receipt_path.exists() 成立时，执行下面的分支。
        if receipt_path.exists():
            # 设置采集回执：解析 JSON 文本或字节，恢复为 Python 对象。
            receipt = json.loads(receipt_path.read_text())
            # 当 sha((ROOT / receipt['xml']['path']).read_bytes()) != receipt['xml']['sha256'] 成立时，执行下面的分支。
            if sha((ROOT / receipt["xml"]["path"]).read_bytes()) != receipt["xml"]["sha256"]:
                # 抛出 ValueError 并停止当前操作：cached_spl_fingerprint_changed。
                raise ValueError("cached_spl_fingerprint_changed")
            # 返回字典，保存queried_terms，结束本次函数调用。
            return {**receipt, "queried_terms": candidate["queried_terms"]}
        # 设置(payload, url)：调用 fetch，取得该步骤的处理结果。
        payload, url = fetch(API + f"spls/{setid}.xml")
        # 设置identity：从 SPL 核对 setID、版本、产品类别、成分、剂型和产品代码。
        identity = parse_identity(payload, setid)
        # 创建输出目录，按参数允许补建父目录或复用已有目录。
        folder.mkdir(parents=True, exist_ok=True)
        # 设置文件路径：将目录与右侧子路径组合，得到完整输出位置。
        path = folder / f"version-{identity['spl_version']}.xml"
        # 将给定字节写入指定文件。
        path.write_bytes(payload)
        # 设置采集回执：字典，保存当前处理或完成状态、本轮采集使用的快照日期、来源唯一标识，用于反查原始文件、api_record、queried_terms等信息。
        receipt = {"status": "spl_raw_ready", "downloaded_on": DATE, **identity,
                   # 写入字段 source_id（来源唯一标识，用于反查原始文件）。
                   "source_id": f"dailymed:{setid}.v{identity['spl_version']}",
                   # 写入字段 api_record（官方API返回的原始产品记录）；字段 queried_terms（将该产品召回的预定义药物词）。
                   "api_record": candidate, "queried_terms": candidate["queried_terms"],
                   # 写入字段 api_xml_version_agrees（API列表与XML声明的版本是否一致）。
                   "api_xml_version_agrees": str(candidate["spl_version"]) == identity["spl_version"],
                   # 写入字段 distribution_decision（本项目按来源作出的分发范围决定）。
                   "distribution_decision": "local_only_pending_source_specific_redistribution_review",
                   # 写入字段 xml（原始 XML 的路径、指纹和来源链接）；字段 path（相对项目根目录的文件位置）；字段 url（来源原始链接或带章节锚点的链接）；字段 sha256（文件或响应的 SHA-256）；字段 bytes（文件原始字节数）。
                   "xml": {"path": str(path.relative_to(ROOT)), "url": url, "sha256": sha(payload), "bytes": len(payload)}}
        # 以临时文件加替换的方式保存 JSON 记录。
        dump(receipt_path, receipt)
        # 返回采集回执，结束本次函数调用。
        return receipt
    # 捕获这里指定的异常，并执行下方的恢复、隔离或报告逻辑。
    except Exception as exc:
        # 返回字典，保存DailyMed 产品标签集合标识、当前处理或完成状态、失败时的异常类型、拒绝、隔离或失败的具体原因，结束本次函数调用。
        return {"setid": setid, "status": "excluded_or_failed", "error_type": type(exc).__name__, "reason": str(exc)[:400]}


# 定义 download_labels：按固定批次获取合格产品标签，保存入选和失败记录。
def download_labels(target=1000, workers=3):
    # 设置candidates：按键或位置读取 json.loads((DATA / 'research/dailymed_candidates.json').read_text()) 中的对应内容。
    candidates = json.loads((DATA / "research/dailymed_candidates.json").read_text())["candidates"]
    # 设置(accepted, excluded)：元组。
    accepted, excluded = [], []
    # Full fixed batches and priority order make the chosen set independent of network completion order.
    # 按顺序遍历range(0, len(candidates), 64)，本轮元素记作 start。
    for start in range(0, len(candidates), 64):
        # 设置当前批次：按键或位置读取 candidates 中的对应内容。
        batch = candidates[start:start + 64]
        # 进入受管理的上下文：创建有并发数上限的下载线程池。
        with ThreadPoolExecutor(max_workers=workers) as pool:
            # 设置处理结果列表：将可迭代结果按顺序收集为列表。
            results = list(pool.map(download_label, batch))
        # 按顺序遍历处理结果列表，本轮元素记作 item。
        for item in results:
            # 把当前结果加入 (accepted if item['status'] == 'spl_raw_ready' else excluded) 的末尾，保留处理顺序。
            (accepted if item["status"] == "spl_raw_ready" else excluded).append(item)
        # 打印当前进度、输出文件位置或核验结果，方便观察执行状态。
        print("SPL download", start + len(batch), "accepted", len(accepted), "excluded", len(excluded), flush=True)
        # 以临时文件加替换的方式保存 JSON 记录。
        dump(DATA / "research/dailymed_download_progress.json", {"processed": start + len(batch), "accepted": len(accepted), "excluded": excluded})
        # 当 start == 0 and (not accepted) 成立时，执行下面的分支。
        if start == 0 and not accepted:
            # 抛出 RuntimeError 并停止当前操作：First SPL batch had no admitted document; inspect progress before retrying。
            raise RuntimeError("First SPL batch had no admitted document; inspect progress before retrying")
        # 当 len(accepted) >= target 成立时，执行下面的分支。
        if len(accepted) >= target:
            # 退出当前这一层循环，停止继续收集本层记录。
            break
    # 设置处理结果：字典，保存本轮准备记录的创建日期、本次准备任务的目标数量、当前处理或完成状态、通过本阶段检查的记录数量、source等信息。
    result = {"created_on": DATE, "target": target, "status": "raw_target_complete" if len(accepted) >= target else "raw_target_incomplete",
              # 写入字段 accepted_count（通过本阶段检查的记录数量）；字段 source（当前来源或接口名称）；字段 region（来源适用或产品注册的目标地区）。
              "accepted_count": min(len(accepted), target), "source": "DailyMed official v2 API", "region": "US",
              # 写入字段 distribution_decision（本项目按来源作出的分发范围决定）。
              "distribution_decision": "local_only_pending_source_specific_redistribution_review",
              # 写入字段 labels（选中的产品说明书列表）；字段 reserve_count（额外下载但没有进入主选择清单的记录数）；字段 excluded（未通过准入或下载失败的记录）。
              "labels": accepted[:target], "reserve_count": max(0, len(accepted) - target), "excluded": excluded}
    # 以临时文件加替换的方式保存 JSON 记录。
    dump(DATA / "dailymed_raw_manifest.json", result)
    # 返回处理结果，结束本次函数调用。
    return result


# 定义 download_guidelines：仅沿 NIH 指定成人 ARV 指南路径采集网页，保留失败原因。
def download_guidelines(limit=80):
    # 设置seeds：列表。
    seeds = [GUIDE_PREFIX + "drug-interactions-protease-inhibitors", GUIDE_PREFIX + "cardiovascular-complications"]
    # 设置(queue, visited, records, failures)：元组。
    queue, visited, records, failures = list(seeds), set(), [], []
    # 设置canonical_seen：创建集合，去掉重复元素。
    canonical_seen = set()
    # 在 queue and len(records) < limit 仍成立时继续循环。
    while queue and len(records) < limit:
        # 设置url：调用 queue.pop，取得该步骤的处理结果。
        url = queue.pop(0)
        # 当 url in visited 成立时，执行下面的分支。
        if url in visited:
            # 跳过当前项，继续检查本层循环中的下一项。
            continue
        # 将 HTML 节点保存为带章节、锚点和原元素位置的正文块。
        visited.add(url)
        # 设置slug：按键或位置读取 url.rstrip('/').split('/') 中的对应内容。
        slug = url.rstrip("/").split("/")[-1]
        # 设置输出目录：将目录与右侧子路径组合，得到完整输出位置。
        folder = DATA / "raw/nih_arv"
        # 创建输出目录，按参数允许补建父目录或复用已有目录。
        folder.mkdir(parents=True, exist_ok=True)
        # 设置文件路径：将目录与右侧子路径组合，得到完整输出位置。
        path = folder / f"{slug}.html"
        # 设置receipt_path：将目录与右侧子路径组合，得到完整输出位置。
        receipt_path = folder / f"{slug}.receipt.json"
        # 开始需要异常处理的操作；失败时转入对应 except 分支。
        try:
            # 当 receipt_path.exists() 成立时，执行下面的分支。
            if receipt_path.exists():
                # 设置采集回执：解析 JSON 文本或字节，恢复为 Python 对象。
                receipt = json.loads(receipt_path.read_text())
                # 设置下载响应字节：读取指定文件的原始字节。
                payload = (ROOT / receipt["raw_path"]).read_bytes()
                # 当 sha(payload) != receipt['sha256'] 成立时，执行下面的分支。
                if sha(payload) != receipt["sha256"]:
                    # 抛出 ValueError 并停止当前操作：cached_guideline_fingerprint_changed。
                    raise ValueError("cached_guideline_fingerprint_changed")
                # 设置final_url：按键或位置读取 采集回执 中的对应内容。
                final_url = receipt["final_url"]
            # 前面的条件都不满足时，执行这一分支。
            else:
                # 设置(payload, final_url)：调用 fetch，取得该步骤的处理结果。
                payload, final_url = fetch(url)
                # 当 not final_url.startswith(GUIDE_PREFIX) 成立时，执行下面的分支。
                if not final_url.startswith(GUIDE_PREFIX):
                    # 抛出 ValueError 并停止当前操作：redirect_outside_selected_guideline。
                    raise ValueError("redirect_outside_selected_guideline")
                # 设置page：将原始 HTML 解析为可查找的 DOM 树。
                page = BeautifulSoup(payload, "lxml")
                # 设置main：page.find('main') or page.find(id='main-content')。
                main = page.find("main") or page.find(id="main-content")
                # 当 main is None or 'Guidelines for the Use of Antiretroviral Agents' not in page.get_text(' ', strip=True) 成立时，执行下面的分支。
                if main is None or "Guidelines for the Use of Antiretroviral Agents" not in page.get_text(" ", strip=True):
                    # 抛出 ValueError 并停止当前操作：unexpected_guideline_page。
                    raise ValueError("unexpected_guideline_page")
                # 设置title：根据 page.title 选择两种结果中的一种。
                title = page.title.get_text(" ", strip=True) if page.title else slug
                # 设置采集回执：字典，保存本轮采集使用的快照日期、来源唯一标识，用于反查原始文件、来源原始链接或带章节锚点的链接、final_url、原始文档或章节标题等信息。
                receipt = {"downloaded_on": DATE, "source_id": "nih-arv:" + slug, "url": url, "final_url": final_url,
                           # 写入字段 title（原始文档或章节标题）；字段 raw_path（原始快照相对项目根目录的位置）；字段 sha256（文件或响应的 SHA-256）；字段 bytes（文件原始字节数）。
                           "title": title, "raw_path": str(path.relative_to(ROOT)), "sha256": sha(payload), "bytes": len(payload),
                           # 写入字段 source_type（来源角色，区分指南、论文、说明书等）；字段 region（来源适用或产品注册的目标地区）；字段 distribution_decision（本项目按来源作出的分发范围决定）。
                           "source_type": "guideline", "region": "US", "distribution_decision": "local_only_pending_page_specific_review"}
                # 将给定字节写入指定文件。
                path.write_bytes(payload)
                # 以临时文件加替换的方式保存 JSON 记录。
                dump(receipt_path, receipt)
                # 等待指定时间，控制公共 API 的请求频率。
                time.sleep(0.3)
            # 设置page：将原始 HTML 解析为可查找的 DOM 树。
            page = BeautifulSoup(payload, "lxml")
            # 按顺序遍历page.find_all('a', href=True)，本轮元素记作 anchor。
            for anchor in page.find_all("a", href=True):
                # 设置linked：调用 urljoin(final_url, anchor['href']).split('#')[0].split('?')[0].rstrip，取得该步骤的处理结果。
                linked = urljoin(final_url, anchor["href"]).split("#")[0].split("?")[0].rstrip("/")
                # 当 linked.startswith(GUIDE_PREFIX) and linked != GUIDE_PREFIX.rstrip('/') and (linked not in visited) and (… 成立时，执行下面的分支。
                if linked.startswith(GUIDE_PREFIX) and linked != GUIDE_PREFIX.rstrip("/") and linked not in visited and linked not in queue:
                    # 把当前结果加入 queue 的末尾，保留处理顺序。
                    queue.append(linked)
            # 当 final_url not in canonical_seen 成立时，执行下面的分支。
            if final_url not in canonical_seen:
                # 将 HTML 节点保存为带章节、锚点和原元素位置的正文块。
                canonical_seen.add(final_url)
                # 把当前结果加入 records 的末尾，保留处理顺序。
                records.append(receipt)
                # 打印当前进度、输出文件位置或核验结果，方便观察执行状态。
                print("NIH guideline", len(records), slug, flush=True)
        # 捕获这里指定的异常，并执行下方的恢复、隔离或报告逻辑。
        except Exception as exc:
            # 把当前结果加入 failures 的末尾，保留处理顺序。
            failures.append({"url": url, "reason": type(exc).__name__ + ":" + str(exc)[:300]})
    # 设置处理结果：字典，保存本轮准备记录的创建日期、pages、page_count、failures、scope。
    result = {"created_on": DATE, "pages": records, "page_count": len(records), "failures": failures,
              # 写入字段 scope（本项统计或来源的适用范围）。
              "scope": "official adult/adolescent ARV guideline HTML pages linked from two independently selected seeds"}
    # 以临时文件加替换的方式保存 JSON 记录。
    dump(DATA / "nih_arv_raw_manifest.json", result)
    # 返回处理结果，结束本次函数调用。
    return result


# 当 __name__ == '__main__' 成立时，执行下面的分支。
if __name__ == "__main__":
    # 设置parser：调用 argparse.ArgumentParser，取得该步骤的处理结果。
    parser = argparse.ArgumentParser()
    # 定义这一项命令行参数的名称、可选值和默认值。
    parser.add_argument("--phase", choices=["discover-labels", "download-labels", "guidelines"], required=True)
    # 定义这一项命令行参数的名称、可选值和默认值。
    parser.add_argument("--target", type=int, default=1000)
    # 设置args：读取命令行参数；--help 会显示帮助并退出。
    args = parser.parse_args()
    # 当 args.phase == 'discover-labels' 成立时，执行下面的分支。
    if args.phase == "discover-labels":
        # 设置处理结果：按预先确定的药物词查询 DailyMed，按 setID 去重形成候选池。
        result = discover_labels()
        # 打印当前进度、输出文件位置或核验结果，方便观察执行状态。
        print("SPL candidates", len(result["candidates"]))
    # 当 args.phase == 'download-labels' 成立时，执行下面的分支。
    elif args.phase == "download-labels":
        # 设置处理结果：按固定批次获取合格产品标签，保存入选和失败记录。
        result = download_labels(args.target)
        # 打印当前进度、输出文件位置或核验结果，方便观察执行状态。
        print("SPL ready", result["accepted_count"], result["status"])
    # 前面的条件都不满足时，执行这一分支。
    else:
        # 设置处理结果：仅沿 NIH 指定成人 ARV 指南路径采集网页，保留失败原因。
        result = download_guidelines()
        # 打印当前进度、输出文件位置或核验结果，方便观察执行状态。
        print("NIH pages ready", result["page_count"])

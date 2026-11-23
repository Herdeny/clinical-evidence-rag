# 下面的文档字符串说明本模块、类或函数的用途和适用边界。
"""Offline CT corpus preparation. Assistant implementation, not a retrieval baseline.

Preserves the existing v1 corpus and notebooks. Source pages are the user's local
snapshots; website-specific adapters emit the same blocks and evidence schema.
"""

# 从 collections 中的指定接口导入 Counter。
from collections import Counter
# 导入内容指纹工具。
import hashlib
# 导入JSON 编解码工具。
import json
# 导入路径对象 Path，便于定位脚本、组合目录并读写文件。
from pathlib import Path
# 导入正则表达式工具，用于匹配标题或规范化空白。
import re
# 从 urllib.parse 中的指定接口导入 quote。
from urllib.parse import quote

# 从 bs4 中的指定接口导入 BeautifulSoup、Tag。
from bs4 import BeautifulSoup, Tag
# 从 transformers 中的指定接口导入 AutoTokenizer。
from transformers import AutoTokenizer

# 从 数据准备包中的公共工具导入 parse_lungrads_notes。
from scripts.data.document_parsing import parse_lungrads_notes


# 从 scripts/data 的位置向上两级确定项目根目录，让数据路径不随启动目录改变。
ROOT = Path(__file__).resolve().parents[2]
# 设置CT 数据构建日期：字符串 '2026-11-16'。
BUILD_DATE = "2026-11-16"


# 定义 digest：计算字节内容的 SHA-256 指纹。
def digest(data):
    # 返回取出已经计算好的十六进制内容指纹，结束本次函数调用。
    return hashlib.sha256(data).hexdigest()


# 定义 clean：只合并空白字符，保留医学数字、单位、否定词和符号。
def clean(text):
    # 下面的文档字符串说明本模块、类或函数的用途和适用边界。
    """Whitespace only: do not change units, inequality signs or medical values."""
    # 返回用指定分隔符连接各段文字，结束本次函数调用。
    return " ".join(text.split())


# 定义 write_json：创建父目录并以 UTF-8 保存格式化 JSON。
def write_json(path, value):
    # 创建输出目录，按参数允许补建父目录或复用已有目录。
    path.parent.mkdir(parents=True, exist_ok=True)
    # 将给定文本写入指定文件。
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# 定义 write_jsonl：创建父目录并逐条序列化为 JSONL。
def write_jsonl(path, values):
    # 创建输出目录，按参数允许补建父目录或复用已有目录。
    path.parent.mkdir(parents=True, exist_ok=True)
    # 将给定文本写入指定文件。
    path.write_text("".join(json.dumps(v, ensure_ascii=False) + "\n" for v in values), encoding="utf-8")


# 定义 CT 来源网页适配器，输出统一的正文块和位置。
class HtmlAdapter:
    # 定义 __init__：读取 HTML 快照并初始化正文块及元素位置映射。
    def __init__(self, path, source):
        # 设置(self.path, self.source)：元组。
        self.path, self.source = path, source
        # 设置self.soup：将原始 HTML 解析为可查找的 DOM 树。
        self.soup = BeautifulSoup(path.read_bytes(), "lxml")
        # 设置self.blocks：空列表。
        self.blocks = []
        # 设置self.element_indices：按遍历顺序筛选并整理 ('p', 'ul', 'ol', 'tr', 'div') 中的数据。
        self.element_indices = {
            # 继续声明 __init__ 的输入参数或返回类型约定。
            name: {id(node): i for i, node in enumerate(self.soup.find_all(name))}
            # 推导式继续按此处的顺序遍历，生成上方表达式所需的数据。
            for name in ("p", "ul", "ol", "tr", "div")
        # 结束上方的字典或集合。
        }

    # 定义 add：将 HTML 节点保存为带章节、锚点和原元素位置的正文块。
    def add(self, node, headings, anchor=None, text=None, extra=None):
        # 设置当前文本：根据 text is None 选择两种结果中的一种。
        text = clean(node.get_text(" ", strip=True)) if text is None else text
        # 当 not text 成立时，执行下面的分支。
        if not text:
            # 返回常量 None，结束本次函数调用。
            return None
        # 设置block_id：f'b{len(self.blocks) + 1:04d}'。
        block_id = f"b{len(self.blocks) + 1:04d}"
        # 设置locator：字典，保存type、selector、element_index、anchor、来源原始链接或带章节锚点的链接。
        locator = {
            # 写入字段 type（当前定位或结构对象的类型标记）。
            "type": "html_element",
            # 写入字段 selector（原HTML元素的标签类型）。
            "selector": node.name,
            # 写入字段 element_index（该类HTML元素在原始页面中的位置）。
            "element_index": self.element_indices[node.name][id(node)],
            # 写入字段 anchor（原网页中的章节锚点）。
            "anchor": anchor,
            # 写入字段 url（来源原始链接或带章节锚点的链接）。
            "url": self.source["url"] + ("#" + quote(anchor, safe="_-") if anchor else ""),
        # 结束上方的字典或集合。
        }
        # 当 extra 成立时，执行下面的分支。
        if extra:
            # 按该对象的 update 规则更新映射或累计统计。
            locator.update(extra)
        # 设置当前正文块：字典，保存记录的唯一标识、来源唯一标识，用于反查原始文件、本条正文或题目报告文字、由外到内的章节标题路径、原始证据位置结构。
        block = {"id": block_id, "source_id": self.source["id"], "text": text,
                 # 写入字段 heading_path（由外到内的章节标题路径）；字段 locator（原始证据位置结构）。
                 "heading_path": headings, "locator": locator}
        # 把当前结果加入 self.blocks 的末尾，保留处理顺序。
        self.blocks.append(block)
        # 返回当前正文块，结束本次函数调用。
        return block

    # 定义 nci：按 NCI 页面章节结构提取正文，过滤引用列表和导航内容。
    def nci(self):
        # 设置article：按给定标签、属性或选择器查找所需网页结构。
        article = self.soup.find("article")
        # 当 article is None 成立时，执行下面的分支。
        if article is None:
            # 抛出 ValueError 并停止当前操作。
            raise ValueError(f"Missing NCI article: {self.path}")
        # 按顺序遍历article.find_all(['p', 'ul', 'ol'])，本轮元素记作 node。
        for node in article.find_all(["p", "ul", "ol"]):
            # 设置section：按给定标签、属性或选择器查找所需网页结构。
            section = node.find_parent("section")
            # 当 section is None or not section.get('id') 成立时，执行下面的分支。
            if section is None or not section.get("id"):
                # 跳过当前项，继续检查本层循环中的下一项。
                continue
            # 当 node.find_parent(['ul', 'ol', 'table']) 成立时，执行下面的分支。
            if node.find_parent(["ul", "ol", "table"]):
                # 跳过当前项，继续检查本层循环中的下一项。
                continue
            # 设置ancestors：list(reversed(list(section.find_parents('section')))) + [section]。
            ancestors = list(reversed(list(section.find_parents("section")))) + [section]
            # 设置headings：空列表。
            headings = []
            # 按顺序遍历ancestors，本轮元素记作 ancestor。
            for ancestor in ancestors:
                # 设置heading：按给定标签、属性或选择器查找所需网页结构。
                heading = ancestor.find(re.compile(r"^h[2-5]$"), recursive=False)
                # 当 heading 成立时，执行下面的分支。
                if heading:
                    # 把当前结果加入 headings 的末尾，保留处理顺序。
                    headings.append(clean(heading.get_text(" ", strip=True)))
            # 当 any((h.startswith('Latest Updates') for h in headings)) 成立时，执行下面的分支。
            if any(h.startswith("Latest Updates") for h in headings):
                # 跳过当前项，继续检查本层循环中的下一项。
                continue
            # 当 section['id'].startswith('_AboutThis_') and section['id'] not in ('_AboutThis_2', '_AboutThis_10') 成立时，执行下面的分支。
            if section["id"].startswith("_AboutThis_") and section["id"] not in ("_AboutThis_2", "_AboutThis_10"):
                # 跳过当前项，继续检查本层循环中的下一项。
                continue
            # References and navigation lists are not medical evidence passages.
            # 当 node.name in ('ul', 'ol') 成立时，执行下面的分支。
            if node.name in ("ul", "ol"):
                # 当 node.find('a', string=re.compile('PUBMED Abstract')) 成立时，执行下面的分支。
                if node.find("a", string=re.compile(r"PUBMED Abstract")):
                    # 跳过当前项，继续检查本层循环中的下一项。
                    continue
                # 设置items：按给定标签、属性或选择器查找所需网页结构。
                items = node.find_all("li", recursive=False)
                # 当 items and all((li.find('a') and clean(li.get_text(' ', strip=True)) == clean(li.find('a').get_text(' ', … 成立时，执行下面的分支。
                if items and all(li.find("a") and clean(li.get_text(" ", strip=True)) == clean(li.find("a").get_text(" ", strip=True)) for li in items):
                    # 跳过当前项，继续检查本层循环中的下一项。
                    continue
            # 设置当前文本：只合并空白字符，保留医学数字、单位、否定词和符号。
            text = clean(node.get_text(" ", strip=True))
            # 当 text.startswith(('Go to Patient Version', 'Other PDQ summaries containing', 'For more information on')) 成立时，执行下面的分支。
            if text.startswith(("Go to Patient Version", "Other PDQ summaries containing", "For more information on")):
                # 跳过当前项，继续检查本层循环中的下一项。
                continue
            # 将 HTML 节点保存为带章节、锚点和原元素位置的正文块。
            self.add(node, headings, section["id"])
        # 返回self.blocks，结束本次函数调用。
        return self.blocks

    # 定义 uspstf：提取 USPSTF 推荐表格与指定正文面板，同时保留标题和单元格。
    def uspstf(self):
        # 设置article：按给定标签、属性或选择器查找所需网页结构。
        article = self.soup.find("article")
        # 设置table：按给定标签、属性或选择器查找所需网页结构。
        table = article.select_one(".summary-table table")
        # 当 table 成立时，执行下面的分支。
        if table:
            # 设置headers：按遍历顺序筛选并整理 table.find_all('th') 中的数据。
            headers = [clean(x.get_text(" ", strip=True)) for x in table.find_all("th")]
            # 按顺序遍历table.select('tbody tr')，本轮元素记作 row。
            for row in table.select("tbody tr"):
                # 设置cells：按遍历顺序筛选并整理 row.find_all('td', recursive=False) 中的数据。
                cells = [clean(x.get_text(" ", strip=True)) for x in row.find_all("td", recursive=False)]
                # 将 HTML 节点保存为带章节、锚点和原元素位置的正文块。
                self.add(row, ["Recommendation Summary"], "fullrecommendationstart",
                         # 为上方调用传入 text 参数；取值按本行指定。
                         text="\n".join(f"{h}: {v}" for h, v in zip(headers, cells)),
                         # 写入字段 table_headers（原表的列标题）；字段 table_cells（按原顺序保留的单元格文本）。
                         extra={"table_headers": headers, "table_cells": cells})
        # 设置panels：列表。
        panels = ["Importance", "USPSTF Assessment of Magnitude of Net Benefit", "Practice Considerations",
                  # 继续组装上方容器中的本行元素，保持其原始顺序和取值。
                  "Update of Previous USPSTF Recommendation", "Supporting Evidence", "Research Needs and Gaps",
                  # 继续组装上方容器中的本行元素，保持其原始顺序和取值。
                  "Recommendations of Others"]
        # 按顺序遍历panels，本轮元素记作 name。
        for name in panels:
            # 设置panel：按给定标签、属性或选择器查找所需网页结构。
            panel = article.find(id=name)
            # 当 panel is None 成立时，执行下面的分支。
            if panel is None:
                # 抛出 ValueError 并停止当前操作。
                raise ValueError(f"Missing USPSTF section {name}")
            # 设置headings：列表。
            headings = [name]
            # 按顺序遍历panel.find_all(['h3', 'h4', 'p', 'ul', 'ol'])，本轮元素记作 node。
            for node in panel.find_all(["h3", "h4", "p", "ul", "ol"]):
                # 当 node.name in ('h3', 'h4') 成立时，执行下面的分支。
                if node.name in ("h3", "h4"):
                    # 设置title：只合并空白字符，保留医学数字、单位、否定词和符号。
                    title = clean(node.get_text(" ", strip=True))
                    # 设置headings：根据 node.name == 'h3' 选择两种结果中的一种。
                    headings = [name, title] if node.name == "h3" else headings[:2] + [title]
                    # 跳过当前项，继续检查本层循环中的下一项。
                    continue
                # 当 node.find_parent(['ul', 'ol', 'table']) 成立时，执行下面的分支。
                if node.find_parent(["ul", "ol", "table"]):
                    # 跳过当前项，继续检查本层循环中的下一项。
                    continue
                # 设置当前文本：只合并空白字符，保留医学数字、单位、否定词和符号。
                text = clean(node.get_text(" ", strip=True))
                # 当 text in ('Return to Table of Contents', 'Expand All') or len(text) < 35 成立时，执行下面的分支。
                if text in ("Return to Table of Contents", "Expand All") or len(text) < 35:
                    # 跳过当前项，继续检查本层循环中的下一项。
                    continue
                # 将 HTML 节点保存为带章节、锚点和原元素位置的正文块。
                self.add(node, headings.copy(), name)
        # 返回self.blocks，结束本次函数调用。
        return self.blocks

    # 定义 acr_scope：提取 ACR Lung-RADS 入口页中说明筛查范围的段落。
    def acr_scope(self):
        # 按顺序遍历self.soup.find_all('p')，本轮元素记作 node。
        for node in self.soup.find_all("p"):
            # 当 clean(node.get_text(' ', strip=True)).startswith('Standardized lung cancer screening CT reporting') 成立时，执行下面的分支。
            if clean(node.get_text(" ", strip=True)).startswith("Standardized lung cancer screening CT reporting"):
                # 将 HTML 节点保存为带章节、锚点和原元素位置的正文块。
                self.add(node, ["Lung-RADS", "Screening CT reporting scope"])
        # 返回self.blocks，结束本次函数调用。
        return self.blocks

    # 定义 acr_incidental：将 ACR Variant 场景与完整检查建议表格行关联保存。
    def acr_incidental(self):
        # Whole variant context plus each intact procedure row; headers/cells stay explicit.
        # 设置tables：按给定标签、属性或选择器查找所需网页结构。
        tables = self.soup.find_all("table")
        # 按顺序遍历enumerate(self.soup.select('.divVar'), start=1)，本轮元素记作 (number, context)。
        for number, context in enumerate(self.soup.select(".divVar"), start=1):
            # 设置heading：列表。
            heading = [f"Variant {number}"]
            # 设置context_block：将 HTML 节点保存为带章节、锚点和原元素位置的正文块。
            context_block = self.add(context, heading)
            # 当 number > len(tables) 成立时，执行下面的分支。
            if number > len(tables):
                # 抛出 ValueError 并停止当前操作：Variant/table mismatch。
                raise ValueError("Variant/table mismatch")
            # 设置table：按键或位置读取 tables 中的对应内容。
            table = tables[number - 1]
            # 设置rows：按给定标签、属性或选择器查找所需网页结构。
            rows = table.find_all("tr")
            # 按顺序遍历rows[1:]，本轮元素记作 row。
            for row in rows[1:]:
                # 设置cells：按遍历顺序筛选并整理 row.find_all(['td', 'th'], recursive=False) 中的数据。
                cells = [clean(x.get_text(" ", strip=True)) for x in row.find_all(["td", "th"], recursive=False)]
                # 当 len(cells) < 3 成立时，执行下面的分支。
                if len(cells) < 3:
                    # 跳过当前项，继续检查本层循环中的下一项。
                    continue
                # 将 HTML 节点保存为带章节、锚点和原元素位置的正文块。
                self.add(row, heading, text="\n".join([
                    # 继续为 '\n'.join 提供本行的参数或输入片段。
                    "Procedure: " + cells[0], "Appropriateness: " + cells[1],
                    # 继续为 '\n'.join 提供本行的参数或输入片段。
                    "Relative radiation level: " + cells[2]]),
                    # 写入字段 table_index（原页面中所属表格的位置）；字段 table_cells（按原顺序保留的单元格文本）。
                    extra={"table_index": number - 1, "table_cells": cells,
                           # 写入字段 context_block_id（表格行所属场景的父正文块ID）。
                           "context_block_id": context_block["id"]})
        # 返回self.blocks，结束本次函数调用。
        return self.blocks


# 定义 make_evidence：合并自然文本单元并附加来源切片和邻接上下文位置。
def make_evidence(blocks, source, raw_path, raw_sha):
    # 下面的文档字符串说明本模块、类或函数的用途和适用边界。
    """Natural semantic units; attach lists/short lead-ins to their paragraph."""
    # 设置规范化文本单元：空列表。
    units = []
    # 按顺序遍历原始正文块，本轮元素记作 block。
    for block in blocks:
        # 设置same_heading：units and units[-1][-1]['heading_path'] == block['heading_path']。
        same_heading = units and units[-1][-1]["heading_path"] == block["heading_path"]
        # 设置prev_short：units and len(units[-1][-1]['text']) < 120。
        prev_short = units and len(units[-1][-1]["text"]) < 120
        # 设置is_list：block['locator']['selector'] in ('ul', 'ol')。
        is_list = block["locator"]["selector"] in ("ul", "ol")
        # 设置is_contextual_table：'context_block_id' in block['locator']。
        is_contextual_table = "context_block_id" in block["locator"]
        # 当 same_heading and (prev_short or is_list) and (not is_contextual_table) and (units[-1][-1]['locator']['se… 成立时，执行下面的分支。
        if same_heading and (prev_short or is_list) and not is_contextual_table and units[-1][-1]["locator"]["selector"] != "tr":
            # 把当前结果加入 units[-1] 的末尾，保留处理顺序。
            units[-1].append(block)
        # 前面的条件都不满足时，执行这一分支。
        else:
            # 把当前结果加入 units 的末尾，保留处理顺序。
            units.append([block])
    # 设置block_map：按遍历顺序筛选并整理 原始正文块 中的数据。
    block_map = {b["id"]: b for b in blocks}
    # 设置evidence：空列表。
    evidence = []
    # 按顺序遍历规范化文本单元，本轮元素记作 unit。
    for unit in units:
        # 设置context_id：按键读取字段，缺失时使用指定默认值或 None。
        context_id = unit[0]["locator"].get("context_block_id")
        # 当 context_id 成立时，执行下面的分支。
        if context_id:
            # 设置当前文本单元：[block_map[context_id]] + unit。
            unit = [block_map[context_id]] + unit
        # 设置当前文本：用指定分隔符连接各段文字。
        text = "\n\n".join(b["text"] for b in unit)
        # 设置locator：字典，保存type、由外到内的章节标题路径、来源原始链接或带章节锚点的链接、正文单元所在的解析 JSON 文件、可用于还原正文的原单元及字符范围。
        locator = {
            # 写入字段 type（当前定位或结构对象的类型标记）；字段 heading_path（由外到内的章节标题路径）。
            "type": "html_blocks", "heading_path": unit[-1]["heading_path"],
            # 写入字段 url（来源原始链接或带章节锚点的链接）。
            "url": unit[-1]["locator"]["url"],
            # 写入字段 blocks_file（正文单元所在的解析 JSON 文件）。
            "blocks_file": f"data/v2/parsed/documents/{source['id']}.json",
            # 写入字段 parts（可用于还原正文的原单元及字符范围）；字段 block_id（正文块标识）；字段 char_start（相对原文本的起始字符位置，包含该位置）；字段 char_end（相对原文本的结束字符位置，不包含该位置）。
            "parts": [{"block_id": b["id"], "char_start": 0, "char_end": len(b["text"])} for b in unit],
        # 结束上方的字典或集合。
        }
        # 设置unit_ids：按遍历顺序筛选并整理 当前文本单元 中的数据。
        unit_ids = {b["id"] for b in unit}
        # 设置adjacent：空列表。
        adjacent = []
        # 按顺序遍历enumerate(blocks)，本轮元素记作 (i, block)。
        for i, block in enumerate(blocks):
            # 当 block['id'] in unit_ids 成立时，执行下面的分支。
            if block["id"] in unit_ids:
                # 按顺序遍历blocks[max(0, i - 1):i + 2]，本轮元素记作 neighbor。
                for neighbor in blocks[max(0, i - 1):i + 2]:
                    # 当 neighbor['id'] not in unit_ids and neighbor['heading_path'] == block['heading_path'] 成立时，执行下面的分支。
                    if neighbor["id"] not in unit_ids and neighbor["heading_path"] == block["heading_path"]:
                        # 把当前结果加入 adjacent 的末尾，保留处理顺序。
                        adjacent.append(neighbor["id"])
        # 设置locator['context_block_ids']：将可迭代结果按顺序收集为列表。
        locator["context_block_ids"] = list(dict.fromkeys(adjacent))
        # 把当前结果加入 evidence 的末尾，保留处理顺序。
        evidence.append({
            # 写入字段 id（记录的唯一标识）；字段 source_id（来源唯一标识，用于反查原始文件）。
            "id": f"{source['id']}::{unit[-1]['id']}", "source_id": source["id"],
            # 写入字段 source_type（来源角色，区分指南、论文、说明书等）。
            "source_type": source["source_type"],
            # 写入字段 text_kind（正文是原始提取、结构化提取还是项目转述）。
            "text_kind": "structured_extraction" if any(b["locator"]["selector"] == "tr" for b in unit) else "extracted_text",
            # 写入字段 text（本条正文或题目报告文字）；字段 locator（原始证据位置结构）；字段 raw_path（原始快照相对项目根目录的位置）。
            "text": text, "locator": locator, "raw_path": str(raw_path.relative_to(ROOT)),
            # 写入字段 raw_sha256（原始快照的 SHA-256）；字段 document_version（来源文档的版本）。
            "raw_sha256": raw_sha, "document_version": source["document_version"],
            # 写入字段 review_status（原文位置或医学复核的完成状态）。
            "review_status": "source_span_verified_not_clinician_reviewed",
            # 写入字段 distribution（当前片段的分发条件）。
            "distribution": "nci_text_with_attribution" if source["id"].startswith("nci-") else "local_only_pending_reuse_review",
            # 写入字段 retrieval_ready（是否允许作为本轮检索输入）。
            "retrieval_ready": True,
        # 结束上方的字典或集合。
        })
    # 返回evidence，结束本次函数调用。
    return evidence


# 定义 build_corpus：从既有 CT 原始快照批量构建证据，检查长度并隔离不适用记录。
def build_corpus(root=ROOT):
    # 设置root：创建文件路径对象，便于跨目录组合与读写。
    root = Path(root)
    # 设置来源清单：解析 JSON 文本或字节，恢复为 Python 对象。
    sources = json.loads((root / "data/v2/source_candidates.json").read_text(encoding="utf-8"))
    # 设置tokenizer：按参数加载 tokenizer；这里用于长度检查，不运行嵌入模型。
    tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-small-en-v1.5", local_files_only=True)
    # 设置(all_cards, inventory, exclusions, duplicates)：元组。
    all_cards, inventory, exclusions, duplicates = [], [], [], []
    # 按顺序遍历来源清单，本轮元素记作 source。
    for source in sources:
        # 设置source_id：按键或位置读取 当前来源 中的对应内容。
        source_id = source["id"]
        # 设置raw_path：将目录与右侧子路径组合，得到完整输出位置。
        raw_path = root / "data/v2/raw" / (source_id + (".pdf" if source_id == "acr-lungrads-2022" else ".html"))
        # 当 not raw_path.exists() 成立时，执行下面的分支。
        if not raw_path.exists():
            # 把当前结果加入 exclusions 的末尾，保留处理顺序。
            exclusions.append({"source_id": source_id, "reason": "No successful local source snapshot; do not reuse v1 paraphrases as new source text."})
            # 跳过当前项，继续检查本层循环中的下一项。
            continue
        # 设置raw_sha：计算字节内容的 SHA-256 指纹。
        raw_sha = digest(raw_path.read_bytes())
        # 把当前结果加入 inventory 的末尾，保留处理顺序。
        inventory.append({**source, "snapshot_path": str(raw_path.relative_to(root)), "snapshot_sha256": raw_sha,
                          # 写入字段 snapshot_bytes（原始快照的文件大小）。
                          "snapshot_bytes": raw_path.stat().st_size,
                          # 写入字段 policy_rechecked_at（来源使用条件的再次核验日期）。
                          "policy_rechecked_at": BUILD_DATE,
                          # 写入字段 distribution_decision（本项目按来源作出的分发范围决定）。
                          "distribution_decision": "nci_text_with_attribution" if source_id.startswith("nci-") else "local_only_pending_reuse_review"})
        # 当 source_id == 'acr-lungrads-2022' 成立时，执行下面的分支。
        if source_id == "acr-lungrads-2022":
            # Keep the user's page text and established character coordinate system.
            # 设置pages_path：将目录与右侧子路径组合，得到完整输出位置。
            pages_path = root / "data/v2/parsed/acr-lungrads-2022.pages.json"
            # 设置pages：解析 JSON 文本或字节，恢复为 Python 对象。
            pages = json.loads(pages_path.read_text(encoding="utf-8"))
            # 按顺序遍历parse_lungrads_notes(pages[1])，本轮元素记作 note。
            for note in parse_lungrads_notes(pages[1]):
                # 把当前结果加入 all_cards 的末尾，保留处理顺序。
                all_cards.append({
                    # 写入字段 id（记录的唯一标识）；字段 source_id（来源唯一标识，用于反查原始文件）。
                    "id": f"{source_id}::p2::note{note['note_number']}", "source_id": source_id,
                    # 写入字段 source_type（来源角色，区分指南、论文、说明书等）；字段 text_kind（正文是原始提取、结构化提取还是项目转述）；字段 text（本条正文或题目报告文字）。
                    "source_type": source["source_type"], "text_kind": "extracted_text", "text": note["text"],
                    # 写入字段 locator（原始证据位置结构）；字段 type（当前定位或结构对象的类型标记）；字段 page（从 1 开始的原文页码）；字段 note_number（PDF 注释的编号）。
                    "locator": {"type": "pdf_note", "page": note["page"], "note_number": note["note_number"],
                                # 写入字段 char_start（相对原文本的起始字符位置，包含该位置）；字段 char_end（相对原文本的结束字符位置，不包含该位置）。
                                "char_start": note["char_start"], "char_end": note["char_end"],
                                # 写入字段 pages_file（PDF逐页原始文字记录文件）；字段 url（来源原始链接或带章节锚点的链接）。
                                "pages_file": str(pages_path.relative_to(root)), "url": source["url"] + "#page=2"},
                    # 写入字段 raw_path（原始快照相对项目根目录的位置）；字段 raw_sha256（原始快照的 SHA-256）。
                    "raw_path": str(raw_path.relative_to(root)), "raw_sha256": raw_sha,
                    # 写入字段 document_version（来源文档的版本）。
                    "document_version": source["document_version"],
                    # 写入字段 review_status（原文位置或医学复核的完成状态）。
                    "review_status": "source_span_verified_not_clinician_reviewed",
                    # 写入字段 distribution（当前片段的分发条件）；字段 retrieval_ready（是否允许作为本轮检索输入）。
                    "distribution": "local_only_pending_reuse_review", "retrieval_ready": True,
                # 结束上方的字典或集合。
                })
            # 把当前结果加入 exclusions 的末尾，保留处理顺序。
            exclusions.append({"source_id": source_id, "page": 1, "reason": "Merged table cells and unit encoding unresolved; only three manually checked reference rows exist. Not indexed as verified table rules."})
            # 跳过当前项，继续检查本层循环中的下一项。
            continue
        # 设置adapter：调用 HtmlAdapter，取得该步骤的处理结果。
        adapter = HtmlAdapter(raw_path, source)
        # 当 source_id.startswith('nci-') 成立时，执行下面的分支。
        if source_id.startswith("nci-"):
            # 设置原始正文块：按 NCI 页面章节结构提取正文，过滤引用列表和导航内容。
            blocks = adapter.nci()
        # 当 source_id.startswith('uspstf-') 成立时，执行下面的分支。
        elif source_id.startswith("uspstf-"):
            # 设置原始正文块：提取 USPSTF 推荐表格与指定正文面板，同时保留标题和单元格。
            blocks = adapter.uspstf()
        # 当 source_id == 'acr-lungrads-scope' 成立时，执行下面的分支。
        elif source_id == "acr-lungrads-scope":
            # 设置原始正文块：提取 ACR Lung-RADS 入口页中说明筛查范围的段落。
            blocks = adapter.acr_scope()
        # 前面的条件都不满足时，执行这一分支。
        else:
            # 设置原始正文块：将 ACR Variant 场景与完整检查建议表格行关联保存。
            blocks = adapter.acr_incidental()
        # 当 not blocks 成立时，执行下面的分支。
        if not blocks:
            # 抛出 ValueError 并停止当前操作。
            raise ValueError(f"Empty extracted source: {source_id}")
        # 创建父目录并以 UTF-8 保存格式化 JSON。
        write_json(root / f"data/v2/parsed/documents/{source_id}.json", {"source_id": source_id, "raw_sha256": raw_sha, "blocks": blocks})
        # 把当前批次的各条记录依次加入 all_cards。
        all_cards.extend(make_evidence(blocks, source, raw_path, raw_sha))

    # Exact normalized duplicates only; do not merge merely similar clinical rules.
    # 设置(unique, seen)：元组。
    unique, seen = [], {}
    # 按顺序遍历all_cards，本轮元素记作 card。
    for card in all_cards:
        # 设置key：元组。
        key = (card["source_id"], clean(card["text"]))
        # 当 key in seen 成立时，执行下面的分支。
        if key in seen:
            # 把当前结果加入 duplicates 的末尾，保留处理顺序。
            duplicates.append({"excluded_id": card["id"], "kept_id": seen[key]})
            # 跳过当前项，继续检查本层循环中的下一项。
            continue
        # 设置seen[key]：按键或位置读取 card 中的对应内容。
        seen[key] = card["id"]
        # 设置token_count：取得对象中元素或字符的数量。
        token_count = len(tokenizer.encode(card["text"], add_special_tokens=True, truncation=False))
        # 设置card['embedding_token_count']：token_count。
        card["embedding_token_count"] = token_count
        # 设置card['quality_flags']：空列表。
        card["quality_flags"] = []
        # 当 token_count > 512 成立时，执行下面的分支。
        if token_count > 512:
            # 设置card['retrieval_ready']：常量 False。
            card["retrieval_ready"] = False
            # 把当前结果加入 card['quality_flags'] 的末尾，保留处理顺序。
            card["quality_flags"].append("exceeds_bge_512_requires_context_preserving_split")
        # 当 '/uni00' in card['text'] 成立时，执行下面的分支。
        if "/uni00" in card["text"]:
            # 设置card['retrieval_ready']：常量 False。
            card["retrieval_ready"] = False
            # 把当前结果加入 card['quality_flags'] 的末尾，保留处理顺序。
            card["quality_flags"].append("unresolved_pdf_unit_encoding")
        # 当 'T o calculate' in card['text'] 成立时，执行下面的分支。
        if "T o calculate" in card["text"]:
            # 把当前结果加入 card['quality_flags'] 的末尾，保留处理顺序。
            card["quality_flags"].append("pdf_word_spacing_preserved")
        # 当 card['id'] == 'acr-lungrads-2022::p2::note6' 成立时，执行下面的分支。
        if card["id"] == "acr-lungrads-2022::p2::note6":
            # The original rendered page also has this diameter/volume expression;
            # do not silently 'correct' a source-level ambiguity during parsing.
            # 设置card['retrieval_ready']：常量 False。
            card["retrieval_ready"] = False
            # 把当前结果加入 card['quality_flags'] 的末尾，保留处理顺序。
            card["quality_flags"].append("source_diameter_volume_parenthesis_requires_medical_review")
        # 当 'Multi-Cancer Detection' in card['locator'].get('heading_path', []) 成立时，执行下面的分支。
        if "Multi-Cancer Detection" in card["locator"].get("heading_path", []):
            # 设置card['retrieval_ready']：常量 False。
            card["retrieval_ready"] = False
            # 把当前结果加入 card['quality_flags'] 的末尾，保留处理顺序。
            card["quality_flags"].append("outside_current_ct_scope_time_specific_regulatory_claims")
        # 把当前结果加入 unique 的末尾，保留处理顺序。
        unique.append(card)
    # 设置ready：按遍历顺序筛选并整理 unique 中的数据。
    ready = [card for card in unique if card["retrieval_ready"]]
    # 创建父目录并逐条序列化为 JSONL。
    write_jsonl(root / "data/v2/evidence_candidates.jsonl", unique)
    # 创建父目录并逐条序列化为 JSONL。
    write_jsonl(root / "data/v2/evidence.jsonl", ready)
    # 创建父目录并逐条序列化为 JSONL。
    write_jsonl(root / "data/v2/evidence_nci_text.jsonl", [card for card in ready if card["distribution"] == "nci_text_with_attribution"])
    # 创建父目录并以 UTF-8 保存格式化 JSON。
    write_json(root / "data/v2/sources.json", inventory)
    # 创建父目录并以 UTF-8 保存格式化 JSON。
    write_json(root / "data/v2/exclusions.json", {"source_exclusions": exclusions, "exact_duplicates": duplicates})
    # 设置report：字典，保存built_at、implemented_by、入库来源数量、raw_candidate_count、unique_candidate_count等信息。
    report = {"built_at": BUILD_DATE, "implemented_by": "assistant_at_user_request", "source_count": len(inventory),
              # 写入字段 raw_candidate_count（原始候选数量，尚未等于准入数量）；字段 unique_candidate_count（去重后的候选数量）；字段 retrieval_ready_count（可以进入检索的记录数量）。
              "raw_candidate_count": len(all_cards), "unique_candidate_count": len(unique), "retrieval_ready_count": len(ready),
              # 写入字段 by_source（按来源标识汇总的数量）。
              "by_source": dict(Counter(card["source_id"] for card in ready)),
              # 写入字段 by_source_type（按证据角色汇总的数量）。
              "by_source_type": dict(Counter(card["source_type"] for card in ready)),
              # 写入字段 tokenizer（长度检查所用tokenizer及本地加载说明）；字段 max_input_tokens（编码模型允许的输入token上限）。
              "tokenizer": "BAAI/bge-small-en-v1.5 (local cache only)", "max_input_tokens": 512,
              # 写入字段 max_ready_tokens（准入证据中实际最大的token数量）。
              "max_ready_tokens": max(card["embedding_token_count"] for card in ready),
              # 写入字段 quarantined_ids（被隔离的具体证据ID）。
              "quarantined_ids": [card["id"] for card in unique if not card["retrieval_ready"]],
              # 写入字段 evidence_sha256（输入证据文件的字节指纹）。
              "evidence_sha256": digest((root / "data/v2/evidence.jsonl").read_bytes()),
              # 写入字段 medical_review（医学内容复核状态，区别于位置校验）。
              "medical_review": "assistant_initial_labels_only_no_clinician_review",
              # 写入字段 algorithm_evaluation（是否已进行检索或生成算法评测的状态说明）。
              "algorithm_evaluation": "not_run; no embedding, retrieval, model or answer-quality scores claimed"}
    # 创建父目录并以 UTF-8 保存格式化 JSON。
    write_json(root / "results/ct_v2_corpus_manifest.json", report)
    # 返回report，结束本次函数调用。
    return report


# 定义 build_cases：从固定蓝本创建合成题及场景家族划分，并核对引用的证据 ID。
def build_cases(root=ROOT):
    # 从 数据准备包中的公共工具导入 FAMILIES、SOURCE_SNAPSHOT_SHA256。
    from scripts.data.ct_case_blueprints import FAMILIES, SOURCE_SNAPSHOT_SHA256

    # 设置root：创建文件路径对象，便于跨目录组合与读写。
    root = Path(root)
    # 设置snapshots：解析 JSON 文本或字节，恢复为 Python 对象。
    snapshots = json.loads((root / "data/v2/sources.json").read_text())
    # 设置actual_fingerprints：按遍历顺序筛选并整理 snapshots 中的数据。
    actual_fingerprints = {s["id"]: s["snapshot_sha256"] for s in snapshots}
    # 当 actual_fingerprints != SOURCE_SNAPSHOT_SHA256 成立时，执行下面的分支。
    if actual_fingerprints != SOURCE_SNAPSHOT_SHA256:
        # 抛出 ValueError 并停止当前操作：Source snapshots changed: review annotations instead of reusing old gold IDs.。
        raise ValueError("Source snapshots changed: review annotations instead of reusing old gold IDs.")
    # 设置cards：按遍历顺序筛选并整理 (json.loads(line) for line in (root / 'data/v2/evidence.jsonl').read_text().splitlines()) 中的数据。
    cards = {c["id"]: c for c in (json.loads(line) for line in (root / "data/v2/evidence.jsonl").read_text().splitlines())}
    # 设置(cases, families)：元组。
    cases, families = [], []
    # 按顺序遍历FAMILIES，本轮元素记作 spec。
    for spec in FAMILIES:
        # 设置family_ids：空列表。
        family_ids = []
        # 按顺序遍历enumerate(spec['examples'])，本轮元素记作 (offset, item)。
        for offset, item in enumerate(spec["examples"]):
            # 设置groups：按键读取字段，缺失时使用指定默认值或 None。
            groups = item.get("evidence_groups", spec["evidence_groups"])
            # 按顺序遍历groups，本轮元素记作 group。
            for group in groups:
                # 当 not group or any((key not in cards for key in group)) 成立时，执行下面的分支。
                if not group or any(key not in cards for key in group):
                    # 抛出 ValueError 并停止当前操作。
                    raise ValueError(f"Unknown or quarantined evidence in family {spec['family']}")
            # 设置case_id：f'CT2-{len(cases) + 1:03d}'。
            case_id = f"CT2-{len(cases) + 1:03d}"
            # 把当前结果加入 family_ids 的末尾，保留处理顺序。
            family_ids.append(case_id)
            # 设置canonical：按遍历顺序筛选并整理 groups 中的数据。
            canonical = [group[0] for group in groups]
            # 把当前结果加入 cases 的末尾，保留处理顺序。
            cases.append({
                # 写入字段 id（记录的唯一标识）；字段 split（开发集或留出集的固定划分）；字段 group（场景家族标识，用于隔离开发与留出）。
                "id": case_id, "split": spec["split"], "group": spec["family"],
                # 写入字段 pair_id（同一场景家族的配对标识）；字段 variant（同一家族中合成变体的编号）；字段 task（这道题需要验证的任务）。
                "pair_id": spec["family"], "variant": chr(65 + offset), "task": spec["task"],
                # 写入字段 report（作为查询输入的合成报告）；字段 question（作为查询输入的问题）。
                "report": item["report"], "question": item["question"],
                # 写入字段 expected_behavior（AI 初标的参考行为，尚非临床复核结论）。
                "expected_behavior": item["expected_behavior"],
                # 写入字段 required_missing_fields（当前任务确实缺少、需要追问的条件）。
                "required_missing_fields": item["required_missing_fields"],
                # 写入字段 expected_action（按必要缺失条件确定的参考动作）。
                "expected_action": "clarify" if item["required_missing_fields"] else "answer_with_evidence_and_limits",
                # 写入字段 gold_evidence_ids（逐题评分使用的标准证据 ID）。
                "gold_evidence_ids": canonical,
                # 写入字段 gold_evidence_groups（逐题评分使用的需求组与替代证据）。
                "gold_evidence_groups": groups,
                # 写入字段 gold_source_ids（参考证据对应的来源标识）。
                "gold_source_ids": sorted({cards[key]["source_id"] for key in canonical}),
                # 写入字段 forbidden_claims（合成参考中禁止无依据扩大的结论）。
                "forbidden_claims": spec["forbidden"],
                # 写入字段 annotation（标注来源、审核状态与固定来源版本）；字段 origin（这份数据或标注的生成来源）；字段 status（当前处理或完成状态）。
                "annotation": {"origin": "assistant_generated_synthetic", "status": "draft_requires_human_review",
                               # 写入字段 clinician_reviewed（是否已经经过医生复核）；字段 created_at（合成标注或记录的创建日期）。
                               "clinician_reviewed": False, "created_at": BUILD_DATE,
                               # 写入字段 grounding（参考标注的依据及验证边界）。
                               "grounding": "Source text and applicable conditions checked by the drafting assistant; not independent clinical validation.",
                               # 写入字段 source_snapshot_sha256（参考标注对应的原始来源版本指纹）。
                               "source_snapshot_sha256": {cards[key]["source_id"]: actual_fingerprints[cards[key]["source_id"]] for group in groups for key in group},
                               # 写入字段 retrieval_scores_used（是否使用检索结果参与题目设计）；字段 model_answers_used（是否使用模型回答参与标注）。
                               "retrieval_scores_used": False, "model_answers_used": False},
            # 结束上方的字典或集合。
            })
        # 把当前结果加入 families 的末尾，保留处理顺序。
        families.append({"group": spec["family"], "split": spec["split"], "task": spec["task"], "case_ids": family_ids})
    # 创建父目录并逐条序列化为 JSONL。
    write_jsonl(root / "data/v2/cases.jsonl", cases)
    # 按顺序遍历('dev', 'holdout')，本轮元素记作 split。
    for split in ("dev", "holdout"):
        # 创建父目录并逐条序列化为 JSONL。
        write_jsonl(root / f"data/v2/cases.{split}.jsonl", [case for case in cases if case["split"] == split])
    # 创建父目录并以 UTF-8 保存格式化 JSON。
    write_json(root / "data/v2/splits.json", {"method": "scenario_family_assigned_before_algorithm_runs",
               # 写入字段 annotation_status（合成标注当前的审核状态）；字段 families（预先定义的场景家族列表）。
               "annotation_status": "assistant_draft_requires_human_review", "families": families,
               # 写入字段 case_counts（按划分汇总的题目数量）。
               "case_counts": dict(Counter(case["split"] for case in cases)),
               # 写入字段 v1_holdout（旧留出题没有参与新题设计或调参的说明）。
               "v1_holdout": "not_read_or_modified; not used for the new family design"})
    # 返回字典，保存题目总数、family_count、by_split，结束本次函数调用。
    return {"case_count": len(cases), "family_count": len(families), "by_split": dict(Counter(c["split"] for c in cases))}


# 当 __name__ == '__main__' 成立时，执行下面的分支。
if __name__ == "__main__":
    # 打印当前进度、输出文件位置或核验结果，方便观察执行状态。
    print(json.dumps(build_corpus(), ensure_ascii=False, indent=2))
    # 打印当前进度、输出文件位置或核验结果，方便观察执行状态。
    print(json.dumps(build_cases(), ensure_ascii=False, indent=2))

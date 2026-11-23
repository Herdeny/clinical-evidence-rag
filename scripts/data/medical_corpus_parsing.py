# 下面的文档字符串说明本模块、类或函数的用途和适用边界。
"""Traceable text extraction for JATS, SPL and guideline HTML snapshots.

Every excerpt is reconstructed from a canonical unit plus offsets. Superscripts
and subscripts are explicit, and unparsed mathematical markup is not indexed.
"""

# 导入正则表达式工具，用于匹配标题或规范化空白。
import re

# 从 lxml 中的指定接口导入 etree。
from lxml import etree


# 定义无法可靠读取公式时使用的专用异常类型。
class UnparsedMath(ValueError):
    # 占位语句，不执行额外操作。
    pass


# 定义 name：取得不带 XML 命名空间的局部标签名。
def name(node):
    # 返回根据 isinstance(node.tag, str) 选择两种结果中的一种，结束本次函数调用。
    return etree.QName(node).localname.lower() if isinstance(node.tag, str) else ""


# 定义 clean：只合并空白字符，保留医学数字、单位、否定词和符号。
def clean(value):
    # 返回去掉文字首尾的空白，结束本次函数调用。
    return re.sub(r"\s+", " ", value).strip()


# 定义 render：将结构化节点转成可追溯文字，显式保留上下标并拒绝不可读公式。
def render(node):
    # 设置tag：取得不带 XML 命名空间的局部标签名。
    tag = name(node)
    # 当 tag in {'inline-formula', 'disp-formula', 'alternatives'} 成立时，执行下面的分支。
    if tag in {"inline-formula", "disp-formula", "alternatives"}:
        # 设置tex：按 XPath 在原始结构中查找节点或字段值。
        tex = node.xpath(".//*[local-name()='tex-math']")
        # 当 tex 成立时，执行下面的分支。
        if tex:
            # 返回'$' + ''.join(tex[0].itertext()) + '$'，结束本次函数调用。
            return "$" + "".join(tex[0].itertext()) + "$"
        # 当 node.xpath(".//*[local-name()='math']") 成立时，执行下面的分支。
        if node.xpath(".//*[local-name()='math']"):
            # 抛出 UnparsedMath 并停止当前操作：MathML without a TeX representation。
            raise UnparsedMath("MathML without a TeX representation")
    # 当 tag == 'math' 成立时，执行下面的分支。
    if tag == "math":
        # 抛出 UnparsedMath 并停止当前操作：MathML without a TeX representation。
        raise UnparsedMath("MathML without a TeX representation")
    # 设置parts：列表。
    parts = [node.text or ""]
    # 按顺序遍历node，本轮元素记作 child。
    for child in node:
        # 设置child_tag：取得不带 XML 命名空间的局部标签名。
        child_tag = name(child)
        # 设置style_codes：创建集合，去掉重复元素。
        style_codes = set(child.get('styleCode', '').lower().split())
        # 当 child_tag in {'graphic', 'inline-graphic'} 成立时，执行下面的分支。
        if child_tag in {"graphic", "inline-graphic"}:
            # 抛出 UnparsedMath 并停止当前操作：inline graphic has no verified text representation。
            raise UnparsedMath('inline graphic has no verified text representation')
        # 当 child_tag in {'fig', 'table-wrap', 'table', 'media', 'script', 'style', 'ref-list'} 成立时，执行下面的分支。
        if child_tag in {"fig", "table-wrap", "table", "media", "script", "style", "ref-list"}:
            # 设置value：字符串 ' '。
            value = " "
        # 当 child_tag in {'sup', 'sub'} or style_codes & {'sup', 'superscript', 'sub', 'subscript'} 成立时，执行下面的分支。
        elif child_tag in {"sup", "sub"} or style_codes & {'sup', 'superscript', 'sub', 'subscript'}:
            # 设置value：('^{' if child_tag == 'sup' or style_codes & {'sup', 'superscript'} else '_{') + render(child) + '}'。
            value = ("^{" if child_tag == "sup" or style_codes & {'sup', 'superscript'} else "_{") + render(child) + "}"
        # 当 child_tag == 'xref' and child.get('ref-type') == 'bibr' 成立时，执行下面的分支。
        elif child_tag == "xref" and child.get("ref-type") == "bibr":
            # 设置value：' [ref:' + clean(render(child)) + '] '。
            value = " [ref:" + clean(render(child)) + "] "
        # 当 child_tag in {'br', 'break'} 成立时，执行下面的分支。
        elif child_tag in {"br", "break"}:
            # 设置value：字符串 ' '。
            value = " "
        # 当 child_tag in {'p', 'paragraph', 'item', 'list', 'li', 'title'} 成立时，执行下面的分支。
        elif child_tag in {"p", "paragraph", "item", "list", "li", "title"}:
            # 设置value：' ' + render(child) + ' '。
            value = " " + render(child) + " "
        # 前面的条件都不满足时，执行这一分支。
        else:
            # 设置value：将结构化节点转成可追溯文字，显式保留上下标并拒绝不可读公式。
            value = render(child)
        # 把当前批次的各条记录依次加入 parts。
        parts.extend([value, child.tail or ""])
    # 返回用指定分隔符连接各段文字，结束本次函数调用。
    return "".join(parts)


# 定义 headings：沿祖先节点提取当前内容所属的章节标题路径。
def headings(node):
    # 设置values：空列表。
    values = []
    # 按顺序遍历reversed(list(node.iterancestors()))，本轮元素记作 parent。
    for parent in reversed(list(node.iterancestors())):
        # 设置parent_tag：取得不带 XML 命名空间的局部标签名。
        parent_tag = name(parent)
        # 当 parent_tag == 'abstract' 成立时，执行下面的分支。
        if parent_tag == "abstract":
            # 把当前结果加入 values 的末尾，保留处理顺序。
            values.append("Abstract")
        # 当 parent_tag in {'sec', 'section'} 成立时，执行下面的分支。
        if parent_tag in {"sec", "section"}:
            # 按顺序遍历parent，本轮元素记作 title。
            for title in parent:
                # 当 name(title) == 'title' 成立时，执行下面的分支。
                if name(title) == "title":
                    # 设置value：只合并空白字符，保留医学数字、单位、否定词和符号。
                    value = clean(render(title))
                    # 当 value 成立时，执行下面的分支。
                    if value:
                        # 把当前结果加入 values 的末尾，保留处理顺序。
                        values.append(value)
                    # 退出当前这一层循环，停止继续收集本层记录。
                    break
    # 返回values，结束本次函数调用。
    return values


# 定义 unit_record：为规范化文本组装章节与原始 XPath 定位记录。
def unit_record(node, tree, text, section_path, **extra):
    # 返回字典，保存本条正文或题目报告文字、正文所属章节路径、原始证据位置结构，结束本次函数调用。
    return {"text": clean(text), "section_path": section_path,
            # 写入字段 locator（原始证据位置结构）；字段 xpath（原始 XML 或 HTML 节点的 XPath）；字段 element_id（原始节点自带的 id）。
            "locator": {"xpath": tree.getpath(node), "element_id": node.get("id"), **extra}}


# 定义 table_units：展开表格跨行跨列关系，并让每个输出行保留原单元格位置。
def table_units(table, tree, section_path):
    # 下面的文档字符串说明本模块、类或函数的用途和适用边界。
    """Expand spans and keep every inherited cell's source XPath."""
    # 设置rows：按遍历顺序筛选并整理 table.iter() 中的数据。
    rows = [row for row in table.iter() if name(row) == "tr" and next((p for p in row.iterancestors() if name(p) == "table"), None) is table]
    # 设置(grid, carried)：元组。
    grid, carried = [], {}
    # 按顺序遍历enumerate(rows)，本轮元素记作 (row_index, row)。
    for row_index, row in enumerate(rows):
        # 设置(row_cells, next_carried)：元组。
        row_cells, next_carried = {}, {}
        # 按顺序遍历carried.items()，本轮元素记作 (column, (cell, remaining))。
        for column, (cell, remaining) in carried.items():
            # 设置row_cells[column]：cell。
            row_cells[column] = cell
            # 当 remaining > 1 成立时，执行下面的分支。
            if remaining > 1:
                # 设置next_carried[column]：元组。
                next_carried[column] = (cell, remaining - 1)
        # 设置column：常量 0。
        column = 0
        # 按顺序遍历row，本轮元素记作 element。
        for element in row:
            # 当 name(element) not in {'td', 'th'} 成立时，执行下面的分支。
            if name(element) not in {"td", "th"}:
                # 跳过当前项，继续检查本层循环中的下一项。
                continue
            # 在 column in row_cells 仍成立时继续循环。
            while column in row_cells:
                # 更新column，累计本轮处理量或内容。
                column += 1
            # 设置value：只合并空白字符，保留医学数字、单位、否定词和符号。
            value = clean(render(element))
            # 设置(colspan, rowspan)：元组。
            colspan, rowspan = int(element.get("colspan", "1")), int(element.get("rowspan", "1"))
            # 当 not 1 <= colspan <= 100 or not 1 <= rowspan <= 500 成立时，执行下面的分支。
            if not 1 <= colspan <= 100 or not 1 <= rowspan <= 500:
                # 抛出 ValueError 并停止当前操作：unsupported table span。
                raise ValueError("unsupported table span")
            # 设置cell：字典，保存本条正文或题目报告文字、原始 XML 或 HTML 节点的 XPath、header。
            cell = {"text": value, "xpath": tree.getpath(element), "header": name(element) == "th"}
            # 按顺序遍历range(colspan)，本轮元素记作 offset。
            for offset in range(colspan):
                # 设置row_cells[column + offset]：cell。
                row_cells[column + offset] = cell
                # 当 rowspan > 1 成立时，执行下面的分支。
                if rowspan > 1:
                    # 设置next_carried[column + offset]：元组。
                    next_carried[column + offset] = (cell, rowspan - 1)
            # 更新column，累计本轮处理量或内容。
            column += colspan
        # 设置carried：next_carried。
        carried = next_carried
        # 把当前结果加入 grid 的末尾，保留处理顺序。
        grid.append((row, row_cells))
    # 设置header_rows：空列表。
    header_rows = []
    # 按顺序遍历enumerate(grid)，本轮元素记作 (index, (row, cells))。
    for index, (row, cells) in enumerate(grid):
        # 当 cells and (all((cell['header'] for cell in cells.values())) or any((name(parent) == 'thead' for parent i… 成立时，执行下面的分支。
        if cells and (all(cell["header"] for cell in cells.values()) or any(name(parent) == "thead" for parent in row.iterancestors())):
            # 把当前结果加入 header_rows 的末尾，保留处理顺序。
            header_rows.append(index)
        # 当 header_rows 成立时，执行下面的分支。
        elif header_rows:
            # 退出当前这一层循环，停止继续收集本层记录。
            break
        # 前面的条件都不满足时，执行这一分支。
        else:
            # 退出当前这一层循环，停止继续收集本层记录。
            break
    # 设置headers：字典，保存。
    headers = {}
    # 按顺序遍历header_rows，本轮元素记作 index。
    for index in header_rows:
        # 按顺序遍历grid[index][1].items()，本轮元素记作 (column, cell)。
        for column, cell in grid[index][1].items():
            # 当 cell['text'] 成立时，执行下面的分支。
            if cell["text"]:
                # 读取已有分组；若不存在则放入初始容器。
                headers.setdefault(column, [])
                # 当 cell['text'] not in headers[column] 成立时，执行下面的分支。
                if cell["text"] not in headers[column]:
                    # 把当前结果加入 headers[column] 的末尾，保留处理顺序。
                    headers[column].append(cell["text"])
    # 设置caption：调用 next，取得该步骤的处理结果。
    caption = next((clean(render(child)) for child in table if name(child) in {"caption", "title"}), "")
    # 按顺序遍历enumerate(grid)，本轮元素记作 (index, (row, cells))。
    for index, (row, cells) in enumerate(grid):
        # 当 index in header_rows or not cells 成立时，执行下面的分支。
        if index in header_rows or not cells:
            # 跳过当前项，继续检查本层循环中的下一项。
            continue
        # 设置values：空列表。
        values = []
        # 按顺序遍历sorted(cells)，本轮元素记作 column。
        for column in sorted(cells):
            # 设置label：' / '.join(headers.get(column, [])) or f'Column {column + 1}'。
            label = " / ".join(headers.get(column, [])) or f"Column {column + 1}"
            # 把当前结果加入 values 的末尾，保留处理顺序。
            values.append(label + ": " + cells[column]["text"])
        # 当 len(values) == 1 and (not any(headers.values())) 成立时，执行下面的分支。
        if len(values) == 1 and not any(headers.values()):
            # A one-cell heading is not silently treated as a recommendation row.
            # 设置caption：cells[min(cells)]['text'] or caption。
            caption = cells[min(cells)]["text"] or caption
            # 跳过当前项，继续检查本层循环中的下一项。
            continue
        # 设置当前文本：('Table: ' + caption + '. ' if caption else '') + ' | '.join(values)。
        text = ("Table: " + caption + ". " if caption else "") + " | ".join(values)
        # 当 len(clean(text)) < 35 成立时，执行下面的分支。
        if len(clean(text)) < 35:
            # 跳过当前项，继续检查本层循环中的下一项。
            continue
        # (yield unit_record(row, tree, text, section_path, table_xpath=tree.getpath(table), row_index=index, cell…。
        yield unit_record(row, tree, text, section_path, table_xpath=tree.getpath(table),
                          # 为上方调用传入 row_index、cells 参数；取值按本行指定。
                          row_index=index, cells=[cells[column] for column in sorted(cells)],
                          # 为上方调用传入 column_headers 参数；取值按本行指定。
                          column_headers={str(column): labels for column, labels in headers.items()},
                          # 为上方调用传入 table_caption、extraction_kind 参数；取值按本行指定。
                          table_caption=caption, extraction_kind="structured_table_row")


# 定义 xml_units：从论文或 SPL 的约定结构提取文本单元，隔离不可靠内容。
def xml_units(root, kind):
    # 设置tree：取得原始节点的完整元素树。
    tree = root.getroottree()
    # 设置(units, exclusions)：元组。
    units, exclusions = [], []
    # 当 kind == 'paper' 成立时，执行下面的分支。
    if kind == "paper":
        # 设置candidates：按 XPath 在原始结构中查找节点或字段值。
        candidates = root.xpath("./*[local-name()='front']/*[local-name()='article-meta']/*[local-name()='abstract']//*[local-name()='p'] | ./*[local-name()='body']//*[local-name()='p']")
    # 前面的条件都不满足时，执行这一分支。
    else:
        # 设置candidates：按 XPath 在原始结构中查找节点或字段值。
        candidates = root.xpath(".//*[local-name()='section']/*[local-name()='text']//*[local-name()='paragraph' or local-name()='item' or local-name()='p']")
    # 设置candidate_set：创建集合，去掉重复元素。
    candidate_set = set(candidates)
    # 按顺序遍历candidates，本轮元素记作 node。
    for node in candidates:
        # 设置ancestors：将可迭代结果按顺序收集为列表。
        ancestors = list(node.iterancestors())
        # 当 any((name(parent) in {'table', 'table-wrap', 'fig', 'ref-list', 'supplementary-material'} for parent in … 成立时，执行下面的分支。
        if any(name(parent) in {"table", "table-wrap", "fig", "ref-list", "supplementary-material"} for parent in ancestors):
            # 跳过当前项，继续检查本层循环中的下一项。
            continue
        # 当 any((parent in candidate_set for parent in ancestors)) 成立时，执行下面的分支。
        if any(parent in candidate_set for parent in ancestors):
            # 跳过当前项，继续检查本层循环中的下一项。
            continue
        # 开始需要异常处理的操作；失败时转入对应 except 分支。
        try:
            # 设置当前文本：只合并空白字符，保留医学数字、单位、否定词和符号。
            text = clean(render(node))
            # 当 len(text) >= (80 if kind == 'paper' else 35) 成立时，执行下面的分支。
            if len(text) >= (80 if kind == "paper" else 35):
                # 把当前结果加入 units 的末尾，保留处理顺序。
                units.append(unit_record(node, tree, text, headings(node), extraction_kind="structured_xml_text"))
        # 捕获这里指定的异常，并执行下方的恢复、隔离或报告逻辑。
        except UnparsedMath:
            # 把当前结果加入 exclusions 的末尾，保留处理顺序。
            exclusions.append({"xpath": tree.getpath(node), "reason": "unparsed_math"})
    # 当 kind == 'drug_label' 成立时，执行下面的分支。
    if kind == "drug_label":
        # 按顺序遍历root.xpath(".//*[local-name()='section']/*[local-name()='text']//*[local-name()='table']")，本轮元素记作 table。
        for table in root.xpath(".//*[local-name()='section']/*[local-name()='text']//*[local-name()='table']"):
            # 开始需要异常处理的操作；失败时转入对应 except 分支。
            try:
                # 把当前批次的各条记录依次加入 units。
                units.extend(table_units(table, tree, headings(table)))
            # 捕获这里指定的异常，并执行下方的恢复、隔离或报告逻辑。
            except (ValueError, UnparsedMath) as exc:
                # 把当前结果加入 exclusions 的末尾，保留处理顺序。
                exclusions.append({"xpath": tree.getpath(table), "reason": "table_extraction:" + str(exc)})
    # Preserve document order even though paragraphs and tables were collected separately.
    # 设置order：按遍历顺序筛选并整理 enumerate(root.iter()) 中的数据。
    order = {tree.getpath(node): index for index, node in enumerate(root.iter()) if isinstance(node.tag, str)}
    # 调用 units.sort，取得该步骤的处理结果。
    units.sort(key=lambda item: order[item["locator"]["xpath"]])
    # 按顺序遍历enumerate(units, 1)，本轮元素记作 (index, item)。
    for index, item in enumerate(units, 1):
        # 设置item['unit_id']：f'u{index:06d}'。
        item["unit_id"] = f"u{index:06d}"
    # 返回元组，结束本次函数调用。
    return units, exclusions


# 定义 html_units：从 NIH 指南 HTML 正文提取段落和表格行，排除导航与参考文献。
def html_units(root):
    # 下面的文档字符串说明本模块、类或函数的用途和适用边界。
    """Extract the NIH guideline body; navigation and references are excluded."""
    # 设置containers：按 XPath 在原始结构中查找节点或字段值。
    containers = root.xpath("//*[contains(concat(' ',normalize-space(@class),' '),' field--name-body ')]")
    # 当 containers 成立时，执行下面的分支。
    if containers:
        # 设置container：取满足规则的最大值或最大项。
        container = max(containers, key=lambda node: len("".join(node.itertext())))
    # 前面的条件都不满足时，执行这一分支。
    else:
        # 设置found：按 XPath 在原始结构中查找节点或字段值。
        found = root.xpath("//main | //*[@id='main-content']")
        # 当 not found 成立时，执行下面的分支。
        if not found:
            # 抛出 ValueError 并停止当前操作：guideline body not found。
            raise ValueError("guideline body not found")
        # 设置container：取满足规则的最大值或最大项。
        container = max(found, key=lambda node: len("".join(node.itertext())))
    # 设置tree：取得原始节点的完整元素树。
    tree = root.getroottree()
    # 设置(sections, units, exclusions)：元组。
    sections, units, exclusions = [], [], []
    # 按顺序遍历container.iter()，本轮元素记作 node。
    for node in container.iter():
        # 设置tag：取得不带 XML 命名空间的局部标签名。
        tag = name(node)
        # 当 tag in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'} 成立时，执行下面的分支。
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            # 设置title：只合并空白字符，保留医学数字、单位、否定词和符号。
            title = clean(render(node))
            # 当 title.lower() in {'references', 'reference'} 成立时，执行下面的分支。
            if title.lower() in {"references", "reference"}:
                # 退出当前这一层循环，停止继续收集本层记录。
                break
            # 设置level：转为整数。
            level = int(tag[1])
            # 设置sections：[(depth, value) for depth, value in sections if depth < level] + [(level, title)]。
            sections = [(depth, value) for depth, value in sections if depth < level] + [(level, title)]
        # 当 tag in {'p', 'li'} 成立时，执行下面的分支。
        elif tag in {"p", "li"}:
            # 设置ancestors：将可迭代结果按顺序收集为列表。
            ancestors = list(node.iterancestors())
            # 当 any((name(parent) in {'table', 'nav', 'script', 'style', 'p', 'li'} for parent in ancestors if parent is… 成立时，执行下面的分支。
            if any(name(parent) in {"table", "nav", "script", "style", "p", "li"} for parent in ancestors if parent is not container):
                # 跳过当前项，继续检查本层循环中的下一项。
                continue
            # 开始需要异常处理的操作；失败时转入对应 except 分支。
            try:
                # 设置当前文本：只合并空白字符，保留医学数字、单位、否定词和符号。
                text = clean(render(node))
                # 当 len(text) >= 35 成立时，执行下面的分支。
                if len(text) >= 35:
                    # 把当前结果加入 units 的末尾，保留处理顺序。
                    units.append(unit_record(node, tree, text, [title for _, title in sections], extraction_kind="structured_html_text"))
            # 捕获这里指定的异常，并执行下方的恢复、隔离或报告逻辑。
            except UnparsedMath:
                # 把当前结果加入 exclusions 的末尾，保留处理顺序。
                exclusions.append({"xpath": tree.getpath(node), "reason": "unparsed_math"})
        # 当 tag == 'table' and (not any((name(parent) == 'table' for parent in node.iterancestors()))) 成立时，执行下面的分支。
        elif tag == "table" and not any(name(parent) == "table" for parent in node.iterancestors()):
            # 开始需要异常处理的操作；失败时转入对应 except 分支。
            try:
                # 把当前批次的各条记录依次加入 units。
                units.extend(table_units(node, tree, [title for _, title in sections]))
            # 捕获这里指定的异常，并执行下方的恢复、隔离或报告逻辑。
            except (ValueError, UnparsedMath) as exc:
                # 把当前结果加入 exclusions 的末尾，保留处理顺序。
                exclusions.append({"xpath": tree.getpath(node), "reason": "table_extraction:" + str(exc)})
    # 按顺序遍历enumerate(units, 1)，本轮元素记作 (index, item)。
    for index, item in enumerate(units, 1):
        # 设置item['unit_id']：f'u{index:06d}'。
        item["unit_id"] = f"u{index:06d}"
    # 返回元组，结束本次函数调用。
    return units, exclusions


# 定义 split_unit：按 tokenizer 的真实字符偏移切分长段落，确保不丢词且不隐藏截断。
def split_unit(text, tokenizer, max_tokens=480):
    # 对当前正文分词并请求字符偏移；关闭截断，使长度校验覆盖完整正文。
    encoded = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True, truncation=False)
    # 当 len(encoded['input_ids']) + tokenizer.num_special_tokens_to_add() <= max_tokens 成立时，执行下面的分支。
    if len(encoded["input_ids"]) + tokenizer.num_special_tokens_to_add() <= max_tokens:
        # 返回列表，结束本次函数调用。
        return [(0, len(text), len(encoded["input_ids"]) + tokenizer.num_special_tokens_to_add())]
    # 设置(spans, start)：元组。
    spans, start = [], 0
    # 设置offsets：按键或位置读取 encoded 中的对应内容。
    offsets = encoded["offset_mapping"]
    # 在 start < len(text) 仍成立时继续循环。
    while start < len(text):
        # 在 start < len(text) and text[start].isspace() 仍成立时继续循环。
        while start < len(text) and text[start].isspace():
            # 更新start，累计本轮处理量或内容。
            start += 1
        # 当 start == len(text) 成立时，执行下面的分支。
        if start == len(text):
            # 退出当前这一层循环，停止继续收集本层记录。
            break
        # 设置relevant：按遍历顺序筛选并整理 offsets 中的数据。
        relevant = [(left, right) for left, right in offsets if right > start]
        # 当 len(relevant) <= max_tokens - 8 成立时，执行下面的分支。
        if len(relevant) <= max_tokens - 8:
            # 设置end：取得对象中元素或字符的数量。
            end = len(text)
        # 前面的条件都不满足时，执行这一分支。
        else:
            # 设置limit：按键或位置读取 relevant[max_tokens - 9] 中的对应内容。
            limit = relevant[max_tokens - 9][1]
            # 设置stops：按遍历顺序筛选并整理 re.finditer('[.!?](?:\\s+|$)', text[start:limit]) 中的数据。
            stops = [match.end() for match in re.finditer(r"[.!?](?:\s+|$)", text[start:limit]) if match.end() > (limit-start)//2]
            # 设置end：根据 stops 选择两种结果中的一种。
            end = start + stops[-1] if stops else text.rfind(" ", start + 1, limit)
            # 当 end <= start 成立时，执行下面的分支。
            if end <= start:
                # 设置end：limit。
                end = limit
        # 在 end > start and text[end - 1].isspace() 仍成立时继续循环。
        while end > start and text[end-1].isspace():
            # 更新end，累计本轮处理量或内容。
            end -= 1
        # 设置count：取得对象中元素或字符的数量。
        count = len(tokenizer.encode(text[start:end], add_special_tokens=True, truncation=False))
        # 在 count > max_tokens and end > start + 1 仍成立时继续循环。
        while count > max_tokens and end > start + 1:
            # 设置shortened：调用 text.rfind，取得该步骤的处理结果。
            shortened = text.rfind(" ", start + 1, end)
            # 设置end：根据 shortened > start 选择两种结果中的一种。
            end = shortened if shortened > start else end - 1
            # 设置count：取得对象中元素或字符的数量。
            count = len(tokenizer.encode(text[start:end], add_special_tokens=True, truncation=False))
        # 当 end <= start 成立时，执行下面的分支。
        if end <= start:
            # 抛出 ValueError 并停止当前操作：could not split unit without truncating。
            raise ValueError("could not split unit without truncating")
        # 把当前结果加入 spans 的末尾，保留处理顺序。
        spans.append((start, end, count))
        # 设置start：end。
        start = end
    # 返回spans，结束本次函数调用。
    return spans

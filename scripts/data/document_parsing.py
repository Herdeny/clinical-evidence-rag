# 下面的文档字符串说明本模块、类或函数的用途和适用边界。
"""编号文本分段与 Lung-RADS 注释适配；由助手按本次授权实现。"""

# 导入正则表达式工具，用于匹配标题或规范化空白。
import re


# 定义 split_numbered_sections：按编号标题切分文本，同时保留相对完整原文的字符范围。
def split_numbered_sections(
    # 继续声明 split_numbered_sections 的输入参数或返回类型约定。
    text: str,
    # 继续声明 split_numbered_sections 的输入参数或返回类型约定。
    heading_pattern: str,
    # 继续声明 split_numbered_sections 的输入参数或返回类型约定。
    start: int = 0,
    # 继续声明 split_numbered_sections 的输入参数或返回类型约定。
    end: int | None = None,
# 继续声明 split_numbered_sections 的输入参数或返回类型约定。
) -> list[dict]:
    # 下面的文档字符串说明本模块、类或函数的用途和适用边界。
    """按编号标题分段，保留相对完整 text 的字符位置及原始切片。

    heading_pattern 的第一捕获组必须为整数编号。start/end 左闭右开，
    end=None 表示到文本末尾。规则只适用于阅读顺序可靠的编号文本。
    """
    # 当 not isinstance(text, str) 成立时，执行下面的分支。
    if not isinstance(text, str):
        # 抛出 TypeError 并停止当前操作：text 必须是字符串。
        raise TypeError("text 必须是字符串")
    # 当 end is None 成立时，执行下面的分支。
    if end is None:
        # 设置end：取得对象中元素或字符的数量。
        end = len(text)
    # 当 not 0 <= start <= end <= len(text) 成立时，执行下面的分支。
    if not 0 <= start <= end <= len(text):
        # 抛出 ValueError 并停止当前操作：文本范围必须满足 0 <= start <= end <= len(text)。
        raise ValueError("文本范围必须满足 0 <= start <= end <= len(text)")

    # 设置pattern：编译正则表达式，供后续重复匹配。
    pattern = re.compile(heading_pattern, flags=re.MULTILINE)
    # 当 pattern.groups < 1 成立时，执行下面的分支。
    if pattern.groups < 1:
        # 抛出 ValueError 并停止当前操作：heading_pattern 的第一捕获组必须提供整数编号。
        raise ValueError("heading_pattern 的第一捕获组必须提供整数编号")
    # 设置matches：将可迭代结果按顺序收集为列表。
    matches = list(pattern.finditer(text, start, end))
    # 当 not matches 成立时，执行下面的分支。
    if not matches:
        # 抛出 ValueError 并停止当前操作：指定范围内未找到编号标题。
        raise ValueError("指定范围内未找到编号标题")

    # 设置sections：空列表。
    sections = []
    # 按顺序遍历enumerate(matches)，本轮元素记作 (index, match)。
    for index, match in enumerate(matches):
        # 设置number_text：调用 match.group，取得该步骤的处理结果。
        number_text = match.group(1)
        # 当 match.start() == match.end() or not number_text or (not number_text.isdecimal()) 成立时，执行下面的分支。
        if match.start() == match.end() or not number_text or not number_text.isdecimal():
            # 抛出 ValueError 并停止当前操作：编号标题必须非空，第一捕获组必须为整数编号。
            raise ValueError("编号标题必须非空，第一捕获组必须为整数编号")
        # 设置char_start：调用 match.start，取得该步骤的处理结果。
        char_start = match.start()
        # 设置char_end：根据 index + 1 < len(matches) 选择两种结果中的一种。
        char_end = matches[index + 1].start() if index + 1 < len(matches) else end
        # 把当前结果加入 sections 的末尾，保留处理顺序。
        sections.append(
            # 继续为 sections.append 提供本行的参数或输入片段。
            {
                # 写入字段 number（编号段落的整数编号）。
                "number": int(number_text),
                # 写入字段 text（本条正文或题目报告文字）。
                "text": text[char_start:char_end],
                # 写入字段 char_start（相对原文本的起始字符位置，包含该位置）。
                "char_start": char_start,
                # 写入字段 char_end（相对原文本的结束字符位置，不包含该位置）。
                "char_end": char_end,
            # 结束上方的字典或集合。
            }
        # 结束上方的函数调用、元组或分组表达式。
        )
    # 返回sections，结束本次函数调用。
    return sections


# 定义 parse_lungrads_notes：定位 Lung-RADS 页内 NOTES 范围，再复用通用编号分段器。
def parse_lungrads_notes(page_record: dict) -> list[dict]:
    # 下面的文档字符串说明本模块、类或函数的用途和适用边界。
    """从一页记录提取 NOTES；当前在本地 v2022 第 2 页验证。

    文件特有的范围和标题规则留在本适配器中；不修复字符、不处理表格，
    不把注释条数写成算法常量。返回文本仍与完整原页字符串的切片一致。
    """
    # 设置当前文本：按键或位置读取 page_record 中的对应内容。
    text = page_record["text"]
    # 设置source_id：按键或位置读取 page_record 中的对应内容。
    source_id = page_record["source_id"]
    # 设置page：按键或位置读取 page_record 中的对应内容。
    page = page_record["page"]
    # 当 not isinstance(text, str) 成立时，执行下面的分支。
    if not isinstance(text, str):
        # 抛出 TypeError 并停止当前操作：页记录的 text 必须是字符串。
        raise TypeError("页记录的 text 必须是字符串")
    # 当 not isinstance(source_id, str) or not source_id 成立时，执行下面的分支。
    if not isinstance(source_id, str) or not source_id:
        # 抛出 ValueError 并停止当前操作：页记录需要非空 source_id。
        raise ValueError("页记录需要非空 source_id")
    # 当 not isinstance(page, int) or page < 1 成立时，执行下面的分支。
    if not isinstance(page, int) or page < 1:
        # 抛出 ValueError 并停止当前操作：页码必须是从 1 开始的整数。
        raise ValueError("页码必须是从 1 开始的整数")

    # 设置notes_heading：寻找首个满足正则规则的位置。
    notes_heading = re.search(r"^NOTES[ \t]*\r?$", text, flags=re.MULTILINE)
    # 当 notes_heading is None 成立时，执行下面的分支。
    if notes_heading is None:
        # 抛出 ValueError 并停止当前操作：未找到 NOTES 标题。
        raise ValueError("未找到 NOTES 标题")
    # 设置footer：寻找首个满足正则规则的位置。
    footer = re.search(r"^Abbreviations:", text[notes_heading.end():], flags=re.MULTILINE)
    # 当 footer is None 成立时，执行下面的分支。
    if footer is None:
        # 抛出 ValueError 并停止当前操作：未找到 Abbreviations 边界，停止提取以免混入页脚。
        raise ValueError("未找到 Abbreviations 边界，停止提取以免混入页脚")
    # 设置notes_end：notes_heading.end() + footer.start()。
    notes_end = notes_heading.end() + footer.start()

    # 本页标题以整数、句点及大写英文开头；避免将行首小数当成新条目。
    # 设置sections：按编号标题切分文本，同时保留相对完整原文的字符范围。
    sections = split_numbered_sections(
        # 继续为 split_numbered_sections 提供本行的参数或输入片段。
        text,
        # 为上方调用传入 heading_pattern 参数；取值按本行指定。
        heading_pattern=r"^[ \t]*(\d+)\.[ \t]*(?=[A-Z])",
        # 为上方调用传入 start 参数；取值按本行指定。
        start=notes_heading.end(),
        # 为上方调用传入 end 参数；取值按本行指定。
        end=notes_end,
    # 结束上方的函数调用、元组或分组表达式。
    )
    # 返回按遍历顺序筛选并整理 sections 中的数据，结束本次函数调用。
    return [
        # 继续声明 parse_lungrads_notes 的输入参数或返回类型约定。
        {
            # 写入字段 source_id（来源唯一标识，用于反查原始文件）。
            "source_id": source_id,
            # 写入字段 page（从 1 开始的原文页码）。
            "page": page,
            # 写入字段 note_number（PDF 注释的编号）。
            "note_number": section["number"],
            # 写入字段 text（本条正文或题目报告文字）。
            "text": section["text"],
            # 写入字段 char_start（相对原文本的起始字符位置，包含该位置）。
            "char_start": section["char_start"],
            # 写入字段 char_end（相对原文本的结束字符位置，不包含该位置）。
            "char_end": section["char_end"],
        # 结束上方的字典或集合。
        }
        # 推导式继续按此处的顺序遍历，生成上方表达式所需的数据。
        for section in sections
    # 结束上方的列表或索引。
    ]

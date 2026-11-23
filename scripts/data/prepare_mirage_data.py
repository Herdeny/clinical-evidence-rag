# 下面的文档字符串说明本模块、类或函数的用途和适用边界。
"""Download and pin MIRAGE evaluation data; never runs a model or retrieval.

Only counts/schema are displayed. Questions and gold answers stay in raw files.
The five upstream dataset terms still need a use-specific review.
"""

# 导入内容指纹工具。
import hashlib
# 导入JSON 编解码工具。
import json
# 导入路径对象 Path，便于定位脚本、组合目录并读写文件。
from pathlib import Path
# 导入正则表达式工具，用于匹配标题或规范化空白。
import re

# 导入公开来源的 HTTP 下载客户端。
import requests


# 从 scripts/data 的位置向上两级确定项目根目录，让数据路径不随启动目录改变。
ROOT = Path(__file__).resolve().parents[2]
# 设置REPO：字符串 'gzxiong/MIRAGE'。
REPO = "gzxiong/MIRAGE"
# 保留脚本最初核验日期常量；实际下载进度另以已有采集记录为准。
VERIFIED_AT = "2026-11-17"
# 限制单个下载响应的最大字节数，超限时中止并记录失败。
MAX_FILE_BYTES = 16 * 1024 * 1024


# 定义 fetch：以超时、大小限制和 HTTP 状态检查下载原始字节，不绕过失败状态。
def fetch(url):
    # 通过 HTTP GET 获取公开来源，使用本行的参数、超时和流式读取配置。
    with requests.get(url, timeout=(10, 30), stream=True) as response:
        # 遇到 HTTP 4xx／5xx 时立即抛错，不把失败页面当原文。
        response.raise_for_status()
        # 设置(chunks, size)：元组。
        chunks, size = [], 0
        # 按顺序遍历response.iter_content(chunk_size=65536)，本轮元素记作 chunk。
        for chunk in response.iter_content(chunk_size=65536):
            # 更新size，累计本轮处理量或内容。
            size += len(chunk)
            # 当 size > MAX_FILE_BYTES 成立时，执行下面的分支。
            if size > MAX_FILE_BYTES:
                # 抛出 ValueError 并停止当前操作。
                raise ValueError(f"Public file exceeds the configured size limit: {url}")
            # 把当前结果加入 chunks 的末尾，保留处理顺序。
            chunks.append(chunk)
        # 返回用指定分隔符连接各段文字，结束本次函数调用。
        return b"".join(chunks)


# 定义 check_benchmark：仅核对外部题库字段关系和任务题数，不展示题目或运行模型。
def check_benchmark(payload):
    # 设置benchmark：解析 JSON 文本或字节，恢复为 Python 对象。
    benchmark = json.loads(payload)
    # 设置counts：字典，保存。
    counts = {}
    # 按顺序遍历benchmark.items()，本轮元素记作 (task, items)。
    for task, items in benchmark.items():
        # 设置values：根据 isinstance(items, dict) 选择两种结果中的一种。
        values = items.values() if isinstance(items, dict) else items
        # 设置counts[task]：取得对象中元素或字符的数量。
        counts[task] = len(items)
        # 按顺序遍历values，本轮元素记作 item。
        for item in values:
            # 当 not isinstance(item, dict) or not {'question', 'options', 'answer'} <= item.keys() 成立时，执行下面的分支。
            if not isinstance(item, dict) or not {"question", "options", "answer"} <= item.keys():
                # 抛出 ValueError 并停止当前操作。
                raise ValueError(f"Unexpected question schema in task {task}")
            # 当 not isinstance(item['question'], str) or not item['question'].strip() 成立时，执行下面的分支。
            if not isinstance(item["question"], str) or not item["question"].strip():
                # 抛出 ValueError 并停止当前操作。
                raise ValueError(f"Empty question in task {task}")
            # 当 not isinstance(item['options'], dict) or item['answer'] not in item['options'] 成立时，执行下面的分支。
            if not isinstance(item["options"], dict) or item["answer"] not in item["options"]:
                # 抛出 ValueError 并停止当前操作。
                raise ValueError(f"Invalid options/answer relationship in task {task}")
    # 当 len(counts) != 5 or sum(counts.values()) != 7663 成立时，执行下面的分支。
    if len(counts) != 5 or sum(counts.values()) != 7663:
        # 抛出 ValueError 并停止当前操作。
        raise ValueError(f"Unexpected benchmark counts: {counts}")
    # 返回counts，结束本次函数调用。
    return counts


# 定义 prepare_mirage：下载或复核 MIRAGE 原题、许可和说明，并固定本地文件指纹。
def prepare_mirage(root=ROOT):
    # 设置root：创建文件路径对象，便于跨目录组合与读写。
    root = Path(root)
    # 设置输出目录：将目录与右侧子路径组合，得到完整输出位置。
    folder = root / "data/external/mirage"
    # 设置manifest_path：将目录与右侧子路径组合，得到完整输出位置。
    manifest_path = folder / "source_manifest.json"
    # 当 manifest_path.exists() 成立时，执行下面的分支。
    if manifest_path.exists():
        # 设置来源或构建清单：解析 JSON 文本或字节，恢复为 Python 对象。
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        # 按顺序遍历manifest['files'].values()，本轮元素记作 record。
        for record in manifest["files"].values():
            # 设置下载响应字节：读取指定文件的原始字节。
            payload = (root / record["path"]).read_bytes()
            # 当 hashlib.sha256(payload).hexdigest() != record['sha256'] 成立时，执行下面的分支。
            if hashlib.sha256(payload).hexdigest() != record["sha256"]:
                # 抛出 ValueError 并停止当前操作：Pinned MIRAGE file changed; preserve the benchmark snapshot。
                raise ValueError("Pinned MIRAGE file changed; preserve the benchmark snapshot")
        # 设置counts：仅核对外部题库字段关系和任务题数，不展示题目或运行模型。
        counts = check_benchmark((root / manifest["files"]["benchmark.json"]["path"]).read_bytes())
        # 当 counts != manifest['task_counts'] 成立时，执行下面的分支。
        if counts != manifest["task_counts"]:
            # 抛出 ValueError 并停止当前操作：Pinned benchmark counts do not match the manifest。
            raise ValueError("Pinned benchmark counts do not match the manifest")
        # 返回来源或构建清单，结束本次函数调用。
        return manifest

    # 设置metadata_url：f'https://api.github.com/repos/{REPO}/commits/main'。
    metadata_url = f"https://api.github.com/repos/{REPO}/commits/main"
    # 设置metadata_error：常量 None。
    metadata_error = None
    # 开始需要异常处理的操作；失败时转入对应 except 分支。
    try:
        # 设置revision：按键或位置读取 json.loads(fetch(metadata_url)) 中的对应内容。
        revision = json.loads(fetch(metadata_url))["sha"]
        # 当 not re.fullmatch('[0-9a-f]{40}', revision) 成立时，执行下面的分支。
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            # 抛出 ValueError 并停止当前操作：Invalid Git revision from the public repository。
            raise ValueError("Invalid Git revision from the public repository")
    # 捕获这里指定的异常，并执行下方的恢复、隔离或报告逻辑。
    except requests.RequestException as exc:
        # Raw-file SHA-256 still fixes an exact local snapshot when only the API
        # is unavailable. Never disable TLS verification to retrieve metadata.
        # 设置revision：常量 None。
        revision = None
        # 设置metadata_error：type(exc).__name__。
        metadata_error = type(exc).__name__
    # 设置git_ref：revision or 'main'。
    git_ref = revision or "main"
    # 设置(payloads, files)：元组。
    payloads, files = {}, {}
    # 按顺序遍历('benchmark.json', 'LICENSE', 'README.md')，本轮元素记作 name。
    for name in ("benchmark.json", "LICENSE", "README.md"):
        # 设置url：f'https://raw.githubusercontent.com/{REPO}/{git_ref}/{name}'。
        url = f"https://raw.githubusercontent.com/{REPO}/{git_ref}/{name}"
        # 设置payloads[name]：调用 fetch，取得该步骤的处理结果。
        payloads[name] = fetch(url)
        # 设置文件路径：将目录与右侧子路径组合，得到完整输出位置。
        path = folder / "raw" / (revision or "sha256-snapshot") / name
        # 设置files[name]：字典，保存来源原始链接或带章节锚点的链接、相对项目根目录的文件位置、文件原始字节数、文件或响应的 SHA-256。
        files[name] = {"url": url, "path": str(path.relative_to(root)),
                       # 写入字段 bytes（文件原始字节数）；字段 sha256（文件或响应的 SHA-256）。
                       "bytes": len(payloads[name]), "sha256": hashlib.sha256(payloads[name]).hexdigest()}
    # 设置counts：仅核对外部题库字段关系和任务题数，不展示题目或运行模型。
    counts = check_benchmark(payloads["benchmark.json"])
    # 当 b'PUBLIC DOMAIN NOTICE' not in payloads['LICENSE'] 成立时，执行下面的分支。
    if b"PUBLIC DOMAIN NOTICE" not in payloads["LICENSE"]:
        # 抛出 ValueError 并停止当前操作：Repository license notice changed; review it before continuing。
        raise ValueError("Repository license notice changed; review it before continuing")
    # 设置来源或构建清单：字典，保存来源或快照的核验日期、repo、revision、metadata_fetch_error、snapshot_pinning等信息。
    manifest = {
        # 写入字段 verified_at（来源或快照的核验日期）；字段 repo（官方来源仓库地址）；字段 revision（固定Git提交或模型版本；未取得时不能伪造）。
        "verified_at": VERIFIED_AT, "repo": f"https://github.com/{REPO}", "revision": revision,
        # 写入字段 metadata_fetch_error（获取Git元数据失败时的异常类型）；字段 snapshot_pinning（固定原始文件版本所用的方式）。
        "metadata_fetch_error": metadata_error, "snapshot_pinning": "sha256_of_each_raw_file",
        # 写入字段 role（该数据在系统中的用途，区分检索与评测）；字段 files（需要固定版本的文件清单）。
        "role": "external_evaluation_only_not_retrieval_corpus", "files": files,
        # 写入字段 task_counts（五个外部任务各自的题目数量）；字段 total_questions（外部基准总题数）。
        "task_counts": counts, "total_questions": sum(counts.values()),
        # 写入字段 status（当前处理或完成状态）。
        "status": "raw_download_and_schema_checks_complete_not_evaluated",
        # 写入字段 protocol（外部基准的输入、生成和评分约定）；字段 retrieval_input（检索侧允许使用的题目字段）；字段 options（多选题选项，仅在生成侧使用）。
        "protocol": {"retrieval_input": "question_only", "options": "generation_only",
                     # 写入字段 answer（标准答案，仅用于评测）；字段 few_shot_examples（是否给模型提供示例题）。
                     "answer": "evaluation_only", "few_shot_examples": False},
        # 写入字段 license_notice（保留的原始许可声明和归属要求）。
        "license_notice": "Repository NCBI public-domain notice retained; cite original authors.",
        # 写入字段 upstream_dataset_terms_review（五个上游题库的使用条件是否分别核验）。
        "upstream_dataset_terms_review": "pending_before_redistribution_or_final_benchmark_use",
        # 写入字段 retrieval_corpus（检索语料是否已选定或接入的阶段说明）；字段 model_calls（模型调用次数）。
        "retrieval_corpus": "not_selected_or_downloaded", "model_calls": 0,
        # 写入字段 test_question_or_answer_content_displayed（是否展示过外部题目或标准答案内容）。
        "test_question_or_answer_content_displayed": False,
    # 结束上方的字典或集合。
    }
    # 按顺序遍历files.items()，本轮元素记作 (name, record)。
    for name, record in files.items():
        # 设置文件路径：将目录与右侧子路径组合，得到完整输出位置。
        path = root / record["path"]
        # 创建输出目录，按参数允许补建父目录或复用已有目录。
        path.parent.mkdir(parents=True, exist_ok=True)
        # 将给定字节写入指定文件。
        path.write_bytes(payloads[name])
    # 将给定文本写入指定文件。
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # 将给定文本写入指定文件。
    (folder / "README.md").write_text(
        # 继续为 (folder / 'README.md').write_text 提供本行的参数或输入片段。
        "# MIRAGE 外部评测原始快照\n\n"
        # 继续为 (folder / 'README.md').write_text 提供本行的参数或输入片段。
        "已按 source_manifest.json 中各文件 SHA-256 固定原题、LICENSE 和官方说明；Git 提交若无法获取则明确留空。\n"
        # 继续为 (folder / 'README.md').write_text 提供本行的参数或输入片段。
        "仅检查五个子任务合计 7,663 题及字段关系，未展示题目或答案，未运行模型。\n"
        # 继续为 (folder / 'README.md').write_text 提供本行的参数或输入片段。
        "原题属于评测数据，不能作为检索语料；检索只用 question，options 用于生成，answer 仅用于评分。\n"
        # 继续为 (folder / 'README.md').write_text 提供本行的参数或输入片段。
        "五个上游数据集使用条件仍待分别核对，不因文件下载成功就声称已获全部再分发许可。\n"
        # 继续为 (folder / 'README.md').write_text 提供本行的参数或输入片段。
        "对应的广泛医学检索语料、评测适配器与全量对照实验尚未完成。\n",
        # 为上方调用传入 encoding 参数；取值按本行指定。
        encoding="utf-8",
    # 结束上方的函数调用、元组或分组表达式。
    )
    # 返回来源或构建清单，结束本次函数调用。
    return manifest


# 当 __name__ == '__main__' 成立时，执行下面的分支。
if __name__ == "__main__":
    # 设置处理结果：下载或复核 MIRAGE 原题、许可和说明，并固定本地文件指纹。
    result = prepare_mirage()
    # 打印当前进度、输出文件位置或核验结果，方便观察执行状态。
    print(json.dumps({key: result[key] for key in ["revision", "task_counts", "total_questions", "status", "model_calls"]}, ensure_ascii=False, indent=2))

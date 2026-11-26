# 下面的文档字符串说明本模块、类或函数的用途和适用边界。
"""Download and pin MIRAGE evaluation data; never runs a model or retrieval.

Only counts/schema are displayed. Questions and gold answers stay in raw files.
Published upstream notices and their scope are recorded in docs/benchmark_scope.md.
"""

# 为既有入口增加独立开发材料和只校验模式。
import argparse
# 导入内容指纹工具。
import hashlib
# 导入JSON 编解码工具。
import json
# 导入路径对象 Path，便于定位脚本、组合目录并读写文件。
from pathlib import Path
# 导入正则表达式工具，用于匹配标题或规范化空白。
import re
# 下载完成后整体放置数据目录，避免留下可误用的半包。
import tempfile
# 汇总原始专家标签，不生成新标签。
from collections import Counter

# 导入公开来源的 HTTP 下载客户端。
import requests
# 显示用户终端中的单文件下载字节进度。
from tqdm.auto import tqdm


# 从 scripts/data 的位置向上两级确定项目根目录，让数据路径不随启动目录改变。
ROOT = Path(__file__).resolve().parents[2]
# 设置REPO：字符串 'gzxiong/MIRAGE'。
REPO = "gzxiong/MIRAGE"
# 保留脚本最初核验日期常量；实际下载进度另以已有采集记录为准。
VERIFIED_AT = "2026-11-17"
# 限制单个下载响应的最大字节数，超限时中止并记录失败。
MAX_FILE_BYTES = 16 * 1024 * 1024
# 固定本轮已从原作者仓库核实的提交，不跟随master变化。
PUBMEDQA_REVISION = "1cbae8e92f72f20c8d3747cbb3bf5bc53554d997"
# 保存题库、官方测试ID及其公开声明和划分代码。
PUBMEDQA_FILES = ("data/ori_pqal.json", "data/test_ground_truth.json", "LICENSE", "README.md", "preprocess/split_dataset.py")


# 定义 fetch：以超时、大小限制和 HTTP 状态检查下载原始字节，不绕过失败状态。
def fetch(url, *, progress=False):
    # 通过 HTTP GET 获取公开来源，使用本行的参数、超时和流式读取配置。
    with requests.get(url, timeout=(10, 30), stream=True) as response:
        # 遇到 HTTP 4xx／5xx 时立即抛错，不把失败页面当原文。
        response.raise_for_status()
        # 设置(chunks, size)：元组。
        chunks, size = [], 0
        # Content-Length缺失时仍显示已接收字节，不推测总大小。
        total = int(response.headers.get("Content-Length", 0)) or None
        # 原有下载调用默认不显示进度，开发材料下载显式打开。
        with tqdm(total=total, unit="B", unit_scale=True, desc=url.rsplit("/", 1)[-1], disable=not progress) as bar:
            # 继续使用流式读取和原大小上限。
            for chunk in response.iter_content(chunk_size=65536):
                # 累计实际接收量。
                size += len(chunk)
                # 防止错误页面或异常文件无限增长。
                if size > MAX_FILE_BYTES:
                    # 保留公开来源URL供排查，不绕过失败。
                    raise ValueError(f"Public file exceeds the configured size limit: {url}")
                # 保留下载原始字节。
                chunks.append(chunk)
                # 更新当前文件进度。
                bar.update(len(chunk))
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


# 从官方专家题和官方测试ID确定CV池；只做格式转换和重叠核查。
def build_pubmedqa_development(labeled, test_gold, mirage):
    # 当前固定PQA-L版本应有1000个专家标注样本和500个官方测试ID。
    if len(labeled) != 1000 or len(test_gold) != 500 or not set(test_gold) <= set(labeled):
        # 不根据错误来源默默生成一个新的划分。
        raise ValueError("Unexpected official PQA-L or test-ID counts")
    # MIRAGE的PubMedQA测试ID必须与官方测试ID完全一致。
    if set(mirage["pubmedqa"]) != set(test_gold):
        # 不能将两个不同版本的测试集拼成开发划分。
        raise ValueError("Official PubMedQA test IDs differ from the pinned MIRAGE snapshot")
    # 选项映射沿用MIRAGE作者的构建方式，标签来自原始专家标注。
    answer_keys = {"yes": "A", "no": "B", "maybe": "C"}
    # 校验所有来源记录，避免原始上下文或模型预测被误当专家标签。
    for pmid, item in labeled.items():
        # 题号保持字符串，问题必须保持有效原文。
        if not isinstance(pmid, str) or not isinstance(item["QUESTION"], str) or not item["QUESTION"].strip():
            # 在写入任何prepared文件前拒绝错误来源。
            raise ValueError("Invalid official PQA-L identity or question")
        # 只允许官方任务定义的三个答案值。
        if item["final_decision"] not in answer_keys:
            # 不从LONG_ANSWER或其他预测字段推测标签。
            raise ValueError("Unknown expert final_decision in PQA-L")
    # 测试题只用于身份比对，不打印内容或送入模型。
    for pmid, decision in test_gold.items():
        # 取得已固定的MIRAGE测试记录。
        reference = mirage["pubmedqa"][pmid]
        # 同时核对官方标签、问题原文和MIRAGE选项解码结果。
        if decision != labeled[pmid]["final_decision"] or reference["question"] != labeled[pmid]["QUESTION"] or reference["options"][reference["answer"]] != decision:
            # 不通过删除不匹配测试题来凑成500条。
            raise ValueError("Official PubMedQA test contents differ from MIRAGE")
    # 官方1000题去掉官方500个测试ID，即官方500题交叉验证池。
    cv_ids = sorted(set(labeled) - set(test_gold))
    # 仅在重叠审计时统一大小写和连续空白，不改写实际输入。
    normalize = lambda value: " ".join(value.casefold().split())
    # 跨五任务检查同题，不只检查PubMedQA测试部分。
    final_questions = {normalize(item["question"]) for records in mirage.values() for item in records.values()}
    # 保存冲突ID，避免在错误消息中打印最终试题。
    overlaps = [pmid for pmid in cv_ids if normalize(labeled[pmid]["QUESTION"]) in final_questions]
    # 有同题冲突时不静默删题、补题或更改公开划分。
    if overlaps:
        # 拒绝生成可被误用为独立开发集的prepared文件。
        raise ValueError(f"Development pool overlaps MIRAGE questions: {len(overlaps)} IDs")
    # 共同参考论文不等于同一道题，单独统计而不宣称主题完全隔离。
    reference_pmids = {str(pmid) for records in mirage.values() for item in records.values() for pmid in item.get("PMID", [])}
    # 生成与现有读取器一致的单任务结构。
    prepared = {"pubmedqa": {pmid: {"question": labeled[pmid]["QUESTION"], "options": {"A": "yes", "B": "no", "C": "maybe"}, "answer": answer_keys[labeled[pmid]["final_decision"]]} for pmid in cv_ids}}
    # 统计结果不包含题干、正确选项或给定支持上下文。
    stats = {"expert_labeled_count": len(labeled), "official_test_count": len(test_gold), "development_count": len(cv_ids), "mirage_test_id_overlap_count": len(set(cv_ids) & set(test_gold)), "mirage_normalized_question_overlap_count": len(overlaps), "shared_reference_pmid_count": len(set(cv_ids) & reference_pmids), "label_counts": dict(Counter(labeled[pmid]["final_decision"] for pmid in cv_ids))}
    # 返回格式转换结果和可回查的划分统计。
    return prepared, stats


# 复用本脚本的下载与快照约定，为后续QA联调准备官方开发材料。
def prepare_pubmedqa_development(root=ROOT, *, verify_only=False):
    # 所有输出仍限制在调用者指定的项目根目录。
    root = Path(root)
    # 开发材料与MIRAGE最终题库保存在不同目录。
    folder = root / "data/external/pubmedqa_development"
    # 以来源清单判断已完成包，避免再次联网更新它。
    manifest_path = folder / "source_manifest.json"
    # 必须先有已固定的MIRAGE，不能在准备开发材料时隐式下载测试集。
    mirage_manifest_path = root / "data/external/mirage/source_manifest.json"
    # 清单缺失自然抛FileNotFoundError。
    mirage_manifest_bytes = mirage_manifest_path.read_bytes()
    # 使用清单中的真实路径，不猜测测试题文件位置。
    mirage_manifest = json.loads(mirage_manifest_bytes)
    # 读取固定测试快照用于隔离核查。
    mirage_bytes = (root / mirage_manifest["files"]["benchmark.json"]["path"]).read_bytes()
    # 任何测试快照变化必须先重新核查，而非继续沿用旧隔离结论。
    if hashlib.sha256(mirage_bytes).hexdigest() != mirage_manifest["files"]["benchmark.json"]["sha256"]:
        # 不修改原采集清单来掩盖变化。
        raise ValueError("Pinned MIRAGE snapshot changed")
    # 仅在本地解析，不展示最终题目。
    mirage = json.loads(mirage_bytes)
    # 已有完整包时只核验，无论是否传verify_only都不联网。
    if manifest_path.exists():
        # 原清单保存采集时点，不重写其日期和状态。
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        # 核对当时用于隔离的测试快照仍一致。
        if manifest["mirage_sha256"] != hashlib.sha256(mirage_bytes).hexdigest():
            # 不把不同测试版本当成同一评测。
            raise ValueError("Development package was checked against a different MIRAGE snapshot")
        # 逐项读取已保存的原件与转换结果。
        payloads = {name: (root / item["path"]).read_bytes() for name, item in manifest["files"].items()}
        # 内容身份必须与原来源记录相符。
        if any(hashlib.sha256(payloads[name]).hexdigest() != item["sha256"] for name, item in manifest["files"].items()):
            # 不覆盖人工更改过的数据。
            raise ValueError("Pinned PubMedQA development file changed")
        # 重新按官方ID核查划分及标签关系。
        expected, stats = build_pubmedqa_development(json.loads(payloads["data/ori_pqal.json"]), json.loads(payloads["data/test_ground_truth.json"]), mirage)
        # prepared必须与原件转换结果一致，数量或摘要相同不足以证明保真。
        if json.loads(payloads["prepared/benchmark.json"]) != expected or manifest["split_checks"] != stats:
            # 拒绝悄悄过滤、补写或改标后的结果。
            raise ValueError("Prepared PubMedQA development data no longer matches its official sources")
        # 返回原采集记录，不创建额外运行文件。
        return manifest
    # 只核验模式绝不发起下载。
    if verify_only:
        # 在任何创建目录和网络请求前退出。
        raise FileNotFoundError(manifest_path)
    # 不完整或手工创建的同名目录不能被覆盖。
    if folder.exists():
        # 留给用户检查原件，不自行清空目录。
        raise FileExistsError(folder)
    # 固定原作者的公开仓库及提交号。
    base_url = f"https://raw.githubusercontent.com/pubmedqa/pubmedqa/{PUBMEDQA_REVISION}"
    # 获取原始字节后先核查，再创建prepared文件。
    payloads = {}
    # 五个文件包括数据、测试ID、声明、README和原始划分代码。
    for name in PUBMEDQA_FILES:
        # 用户终端能看到当前文件和随后字节进度。
        print(f"下载官方来源：{name}", flush=True)
        # 沿用流式下载、超时和大小限制。
        payloads[name] = fetch(f"{base_url}/{name}", progress=True)
    # 核查公开许可原件没有被替换成错误页面。
    if b"MIT License" not in payloads["LICENSE"]:
        # 不根据下载HTTP成功就默认内容正确。
        raise ValueError("PubMedQA license notice differs from the reviewed source")
    # 使用官方专家标签，不读取人工生成PQA-A样本。
    prepared, stats = build_pubmedqa_development(json.loads(payloads["data/ori_pqal.json"]), json.loads(payloads["data/test_ground_truth.json"]), mirage)
    # 用JSON字节保存转换结果，原问题字符串和标签含义保持不变。
    payloads["prepared/benchmark.json"] = (json.dumps(prepared, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    # 为每份原件和prepared结果记录最终位置与指纹。
    files = {name: {"path": str((folder / (name if name.startswith("prepared/") else f"raw/{PUBMEDQA_REVISION}/{name}")).relative_to(root)), "url": None if name.startswith("prepared/") else f"{base_url}/{name}", "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)} for name, payload in payloads.items()}
    # 元数据明确这是公开CV池的项目开发用途，不是原论文十折训练结果。
    manifest = {"repo": "https://github.com/pubmedqa/pubmedqa", "revision": PUBMEDQA_REVISION, "review_date": "2026-11-26", "role": "development_only_not_MIRAGE_final_evaluation", "split_origin": "Official PQA-L 1000 expert-labeled IDs minus official test_ground_truth 500 IDs; use the full official CV pool for project development, not a reported ten-fold experiment", "files": files, "split_checks": stats, "mirage_sha256": hashlib.sha256(mirage_bytes).hexdigest(), "mirage_manifest_sha256": hashlib.sha256(mirage_manifest_bytes).hexdigest(), "task_counts": {"pubmedqa": stats["development_count"]}, "total_questions": stats["development_count"], "status": "prepared_development_pool_not_model_evaluated", "model_calls": 0, "license_notice": "Official repository MIT notice retained; cite Jin et al., EMNLP 2019; do not infer blanket redistribution rights over third-party abstracts", "input_scope": "prepared contains question/options/answer only; supplied contexts, LONG_ANSWER and prediction fields stay in raw and are not model inputs"}
    # 先创建父目录，临时内容仍留在当前项目内。
    folder.parent.mkdir(parents=True, exist_ok=True)
    # 临时目录在失败时自动清理，不留下看似完成的数据包。
    with tempfile.TemporaryDirectory(prefix=".pubmedqa-development-", dir=folder.parent) as temporary:
        # 整个数据包放在临时子目录后一次性改名。
        staging = Path(temporary) / "dataset"
        # 逐份写入原始字节和转换文件。
        for name, payload in payloads.items():
            # 文件的相对层级与最终目录一致。
            target = staging / (name if name.startswith("prepared/") else f"raw/{PUBMEDQA_REVISION}/{name}")
            # 为嵌套的原始路径创建父目录。
            target.parent.mkdir(parents=True, exist_ok=True)
            # 原件不经过解码重写。
            target.write_bytes(payload)
        # 清单只在完整包准备好后写入。
        (staging / "source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        # 同名最终目录已提前保护，不用覆盖式替换。
        staging.rename(folder)
    # 下载后再次按同一离线分支验证所有文件及转换关系。
    return prepare_pubmedqa_development(root, verify_only=True)


# 当 __name__ == '__main__' 成立时，执行下面的分支。
if __name__ == "__main__":
    # 在既有脚本中选择数据准备范围，不新增入口文件。
    parser = argparse.ArgumentParser()
    # 默认仍保持原MIRAGE准备行为。
    parser.add_argument("--development", action="store_true", help="Prepare the official PubMedQA CV pool for QA development")
    # 明确保证缺包时退出，而不是隐式下载。
    parser.add_argument("--verify-only", action="store_true", help="Verify an existing package without downloading")
    # 读取用户实际传入的模式。
    args = parser.parse_args()
    # 开发材料和最终评测材料使用不同数据目录。
    if args.development:
        # 准备或离线核验官方CV池。
        result = prepare_pubmedqa_development(verify_only=args.verify_only)
    # 没选development时保持原有MIRAGE行为。
    else:
        # 只核验模式缺少原包时不联网。
        if args.verify_only and not (ROOT / "data/external/mirage/source_manifest.json").exists():
            # 提示缺失的实际来源清单。
            raise FileNotFoundError(ROOT / "data/external/mirage/source_manifest.json")
        # 已有原包时prepare_mirage只读取与校验。
        result = prepare_mirage()
    # 额外展示开发池的隔离核查结果，不输出试题正文。
    if args.development:
        # 即使没有模型调用，也明确展示这只是数据准备。
        print(json.dumps(result["split_checks"], ensure_ascii=False, indent=2))
    # 打印当前进度、输出文件位置或核验结果，方便观察执行状态。
    print(json.dumps({key: result[key] for key in ["revision", "task_counts", "total_questions", "status", "model_calls"]}, ensure_ascii=False, indent=2))

# 下载并固定公开检索基准，不编写检索、适配或评分核心。
"""Acquire the official BEIR NFCorpus snapshot for local academic evaluation."""

# 为命令行核验提供参数。
import argparse
# 检查TSV中的相关性标签。
import csv
# 计算官方MD5和本地SHA-256。
import hashlib
# 从内存中的ZIP读取成员。
import io
# 保存下载收据及结构检查。
import json
# 根据模块位置定位项目根目录。
from pathlib import Path
# 只解包明确需要的官方文件。
from zipfile import ZipFile

# 沿用现有环境的HTTP客户端。
import requests
# 读取BEIR官方镜像当前发布的Parquet容器。
import pandas as pd
# 对偶发连接中断执行有限重试。
from requests.adapters import HTTPAdapter
# 不重试权限拒绝，只处理临时连接或服务问题。
from urllib3.util.retry import Retry
# 不将临时重定向地址中的签名参数写入收据。
from urllib.parse import urlsplit

# 数据工具位于scripts/data。
ROOT = Path(__file__).resolve().parents[2]
# 官方BEIR发布的NFCorpus文件。
ARCHIVE_URL = "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/nfcorpus.zip"
# BEIR官方数据表给出的MD5，不以下载后自算的值代替供应方校验。
EXPECTED_MD5 = "a89dba18a62ef92f7d323ec890a0d38d"
# 固定已从官方API核对的正文镜像提交。
HF_CORPUS_REVISION = "b5026a0e96e8a7ac4f95f482a596389289d46269"
# 标签仓库与正文仓库分别固定提交。
HF_QRELS_REVISION = "a451b3b26d3ae1358f259c1a3a4dd61fcea35a65"
# 同时保留版本说明、使用条件及参考加载器，后者不被执行。
REFERENCES = {"beir.README.md": "https://raw.githubusercontent.com/beir-cellar/beir/main/README.md", "nfcorpus.homepage.html": "https://www.cl.uni-heidelberg.de/statnlpgroup/nfcorpus/", "beir.data_loader.py.txt": "https://raw.githubusercontent.com/beir-cellar/beir/main/beir/datasets/data_loader.py"}
# 只允许这五个数据文件，不直接extractall。
MEMBERS = ("corpus.jsonl", "queries.jsonl", "qrels/train.tsv", "qrels/dev.tsv", "qrels/test.tsv")


# 计算小型数据文件的固定身份。
def sha256(path):
    # NFCorpus原始文件规模有限，可直接计算。
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# 从官方HTTPS地址取得有大小上限的原始字节。
def fetch(url):
    # 每次请求使用有限重试的会话。
    session = requests.Session()
    # 不关闭TLS验证，不重试403。
    session.mount("https://", HTTPAdapter(max_retries=Retry(total=2, backoff_factor=0.5, status_forcelist=(429, 502, 503, 504), allowed_methods=("GET",))))
    # 默认验证TLS，不绕过403或证书检查。
    with session, session.get(url, stream=True, timeout=(8, 15)) as response:
        # 失败页面不能作为数据保存。
        response.raise_for_status()
        # 用独立计数限制下载大小。
        chunks, byte_count = [], 0
        # 按64KiB读取。
        for chunk in response.iter_content(65536):
            # 记录真实响应体长度。
            byte_count += len(chunk)
            # 该公开包远小于64MiB，超出则停止。
            if byte_count > 64 * 1024 * 1024:
                # 不接受异常大的响应。
                raise ValueError("Public NFCorpus response exceeds 64 MiB")
            # 保留当前有效字节。
            chunks.append(chunk)
        # 返回正文和实际响应地址。
        return b"".join(chunks), urlsplit(response.url)._replace(query="", fragment="").geturl()


# 核对官方ID、划分及标签，不运行检索。
def check_dataset(folder):
    # JSONL记录保持官方字段。
    corpus_rows = [json.loads(line) for line in (folder / "corpus.jsonl").read_text().splitlines() if line.strip()]
    # 这里只读取ID和字段关系，不展示测试题。
    query_rows = [json.loads(line) for line in (folder / "queries.jsonl").read_text().splitlines() if line.strip()]
    # 用集合检查ID完整性。
    corpus_ids, query_ids = {row["_id"] for row in corpus_rows}, {row["_id"] for row in query_rows}
    # ID必须唯一，避免后续字典覆盖数据。
    if len(corpus_ids) != len(corpus_rows) or len(query_ids) != len(query_rows):
        # 不修补或删除官方数据。
        raise ValueError("Duplicate official IDs")
    # 保持ID为字符串，避免pandas自动转型。
    if any(not isinstance(value, str) or not value for value in corpus_ids | query_ids):
        # ID类型影响检索结果与gold连接。
        raise ValueError("Official IDs must be nonempty strings")
    # 正文及查询必须可直接作为文本使用。
    if any(not isinstance(row.get("text"), str) or not row["text"].strip() for row in corpus_rows + query_rows):
        # 空文本不静默过滤。
        raise ValueError("Empty official text")
    # 标题是独立字段，留给用户的适配函数组装检索输入。
    if any(not isinstance(row.get("title"), str) for row in corpus_rows):
        # 保持官方数据格式明确。
        raise ValueError("Unexpected corpus title type")
    # 保存各划分的真实规模和相关性等级。
    splits, split_query_ids = {}, {}
    # 按官方划分检查，不重新随机分题。
    for split in ("train", "dev", "test"):
        # TSV由标准库解析，不手工按空格拆。
        with (folder / "qrels" / f"{split}.tsv").open(newline="", encoding="utf-8") as stream:
            # BEIR文件包含固定列头。
            reader = csv.DictReader(stream, delimiter="\t")
            # 列名变化须先更新适配契约。
            if reader.fieldnames != ["query-id", "corpus-id", "score"]:
                # 保留具体出错划分。
                raise ValueError(f"Unexpected qrels header: {split}")
            # 当前划分规模很小，保存以验证唯一性。
            rows = list(reader)
        # 每对query和document只能有一项等级。
        pairs = {(row["query-id"], row["corpus-id"]) for row in rows}
        # 检查所有引用都属于官方配套数据。
        if len(pairs) != len(rows) or any(row["query-id"] not in query_ids or row["corpus-id"] not in corpus_ids for row in rows):
            # 不将错误ID强行映射到项目主医学库。
            raise ValueError(f"Invalid official qrels IDs: {split}")
        # 相关性等级完整保留，之后不能全变成布尔值。
        grades = sorted({int(row["score"]) for row in rows})
        # 保存划分实际使用的查询。
        split_query_ids[split] = {row["query-id"] for row in rows}
        # 标签是否为正用于之后的Recall，而nDCG仍应保留等级。
        splits[split] = {"queries": len(split_query_ids[split]), "qrel_rows": len(rows), "grades": grades, "positive_qrels": sum(int(row["score"]) > 0 for row in rows)}
    # 官方划分不应有相同query ID跨集。
    if any(split_query_ids[left] & split_query_ids[right] for left, right in (("train", "dev"), ("train", "test"), ("dev", "test"))):
        # 不让日常开发接触同一个测试题号。
        raise ValueError("Official query IDs cross splits")
    # BEIR的官方版本有3633篇文档与323个测试查询。
    if len(corpus_rows) != 3633 or splits["test"]["queries"] != 323:
        # 包内容变化时停止，不宣称沿用同一基准。
        raise ValueError("Unexpected BEIR NFCorpus snapshot counts")
    # 只返回数量和字段，不打印查询或答案。
    return {"documents": len(corpus_rows), "queries_total": len(query_rows), "splits": splits, "query_id_splits_disjoint": True, "all_qrels_ids_resolve": True, "official_text_values_and_split_assignments_preserved": True}


# 下载一次，后续只验证已有快照。
def prepare(root=ROOT, verify_only=False, source="huggingface"):
    # 默认输出位于独立外部基准目录。
    folder = Path(root) / "data/external/nfcorpus"
    # 下载和检查结果都绑定同一清单。
    manifest_path = folder / "source_manifest.json"
    # 已有清单时不再次联网覆盖版本。
    if manifest_path.exists():
        # 按已有指纹复验，不更新原核验日期。
        manifest = json.loads(manifest_path.read_text())
        # 文件内容变化必须停止。
        if any(sha256(folder / name) != value["sha256"] for name, value in manifest["files"].items()):
            # 不把修改后的文件继续当官方数据。
            raise ValueError("A pinned NFCorpus file changed")
        # 再检查数据内部关系。
        check_dataset(folder / manifest["data_directory"])
        # 返回既有版本的收据。
        return manifest
    # 离线检查不应触发隐式下载。
    if verify_only:
        # 缺少快照时要求先执行正常下载。
        raise FileNotFoundError("NFCorpus has not been prepared")
    # 创建原始数据目录。
    raw = folder / "raw"
    # 只创建本基准自己的输出路径。
    raw.mkdir(parents=True, exist_ok=True)
    # 不同发布容器有各自来源身份，不冒充ZIP逐字节相同。
    receipts = {}
    # 原站可访问时支持供应方ZIP版本。
    if source == "beir":
        # 下载官方ZIP并检查供应方MD5。
        payload, final_url = fetch(ARCHIVE_URL)
        # 不能仅靠自算SHA替代供应方校验。
        if hashlib.md5(payload).hexdigest() != EXPECTED_MD5:
            # 不静默采用变更后的发布包。
            raise ValueError("Official NFCorpus archive MD5 mismatch")
        # 保存官方原始文件。
        (raw / "nfcorpus.zip").write_bytes(payload)
        # 记录实际校验过MD5的文件。
        receipts["raw/nfcorpus.zip"] = {"url": ARCHIVE_URL, "final_url": final_url, "md5": EXPECTED_MD5}
        # 数据目录保存原始ZIP成员。
        data_directory = "raw/nfcorpus"
        # 白名单展开，不使用extractall。
        with ZipFile(io.BytesIO(payload)) as archive:
            # 仅展开五个固定数据文件。
            for name in MEMBERS:
                # 使用已知官方相对路径。
                member = "nfcorpus/" + name
                # 拒绝异常大的成员。
                if archive.getinfo(member).file_size > 64 * 1024 * 1024:
                    # 不写出异常数据。
                    raise ValueError("Unexpected uncompressed member size")
                # 补建输出目录。
                destination = folder / data_directory / name
                # qrels仍保持子目录。
                destination.parent.mkdir(parents=True, exist_ok=True)
                # 完整保留原始成员字节。
                destination.write_bytes(archive.read(member))
                # 记录源成员身份。
                receipts[data_directory + "/" + name] = {"archive_member": member}
    # 官方HF镜像与BEIR格式有相同任务身份，但发布容器为Parquet。
    elif source == "huggingface":
        # 格式转换的文件与原始下载分开存放。
        data_directory = "prepared/nfcorpus"
        # 保存两份明确固定的官方仓库身份。
        repositories = {"BeIR/nfcorpus": HF_CORPUS_REVISION, "BeIR/nfcorpus-qrels": HF_QRELS_REVISION}
        # 固定仓库内的正文、查询和说明文件路径。
        downloads = [("BeIR/nfcorpus", "corpus/corpus-00000-of-00001.parquet", "corpus.parquet"), ("BeIR/nfcorpus", "queries/queries-00000-of-00001.parquet", "queries.parquet"), ("BeIR/nfcorpus", "README.md", "nfcorpus.README.md"), ("BeIR/nfcorpus-qrels", "README.md", "qrels.README.md")]
        # 标签保留各自官方文件，不重新划分。
        downloads += [("BeIR/nfcorpus-qrels", f"{split}.tsv", f"{split}.tsv") for split in ("train", "dev", "test")]
        # 原始HF文件单独固定。
        (raw / "huggingface").mkdir(exist_ok=True)
        # 逐个下载不可变提交中的文件。
        for repository, remote, local in downloads:
            # 不使用main或latest作为实际数据身份。
            url = f"https://huggingface.co/datasets/{repository}/resolve/{repositories[repository]}/{remote}"
            # TLS验证及有限重试仍生效。
            content, actual_url = fetch(url)
            # 只写本基准原始目录。
            destination = raw / "huggingface" / local
            # 保留供应方发布容器字节。
            destination.write_bytes(content)
            # 记录仓库、提交及相对路径。
            receipts["raw/huggingface/" + local] = {"url": url, "final_url": actual_url, "repository": repository, "revision": repositories[repository], "repository_path": remote}
        # 创建规范BEIR格式目录。
        prepared = folder / data_directory
        # 预先建立标签子目录。
        (prepared / "qrels").mkdir(parents=True, exist_ok=True)
        # 只转换容器格式，不组装检索输入或生成标签。
        for name, fields in (("corpus", ["_id", "title", "text"]), ("queries", ["_id", "text"])):
            # pyarrow读取官方Parquet，不使用dataset远程代码。
            frame = pd.read_parquet(raw / "huggingface" / f"{name}.parquet")
            # 保留规范BEIR的必需模型字段。
            records = frame[fields].to_dict("records")
            # 输出UTF-8 JSONL，字段值不修改。
            target = prepared / f"{name}.jsonl"
            # 不在构建器中连接title和text，该适配由用户实现。
            target.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records), encoding="utf-8")
            # 回读必须与供应方字段逐值相同。
            if [json.loads(line) for line in target.read_text().splitlines()] != records:
                # 不接受容器转换改变正文。
                raise ValueError("Parquet-to-JSONL field values changed")
            # 明确该文件是转换产物，不是原始ZIP成员。
            receipts[data_directory + f"/{name}.jsonl"] = {"derived_from": "raw/huggingface/" + name + ".parquet", "conversion": "Preserve _id, text and corpus title values; raw Parquet retained."}
        # 标签TSV原字节复制，不重写等级或顺序。
        for split in ("train", "dev", "test"):
            # 同一标签文件具有两个明确角色。
            (prepared / "qrels" / f"{split}.tsv").write_bytes((raw / "huggingface" / f"{split}.tsv").read_bytes())
            # 保存复制来源，供独立复验。
            receipts[data_directory + f"/qrels/{split}.tsv"] = {"derived_from": f"raw/huggingface/{split}.tsv", "conversion": "Byte-identical copy."}
    # 非法来源名不能默默回退。
    else:
        # 保持数据来源选择可审计。
        raise ValueError("source must be beir or huggingface")
    # 核对数据关系后才发布完成清单。
    validation = check_dataset(folder / data_directory)
    # 为所有固定输入计算本地SHA和字节数。
    for name, receipt in receipts.items():
        # 原文身份覆盖数据与来源说明。
        receipt.update(sha256=sha256(folder / name), bytes=(folder / name).stat().st_size)
    # 学术使用条件不扩展为任意公开分发许可。
    manifest = {"dataset": "BEIR NFCorpus", "client_date": "2026-11-21", "status": "downloaded_and_structurally_checked_not_evaluated", "archive_url": ARCHIVE_URL, "official_archive_md5": EXPECTED_MD5, "snapshot_pinning": "supplier MD5 plus SHA-256 of original files; no Git revision claimed", "files": receipts, "validation": validation, "qrels_origin": "Automatically extracted website-link relevance, not assistant-generated and not clinical expert judgments.", "usage": "Original NFCorpus site permits academic use; other uses and redistribution need their own applicable terms. BEIR software license does not license all data.", "official_terms_url": REFERENCES["nfcorpus.homepage.html"], "retrieval_corpus": "The included NFCorpus corpus only; separate from medical_v3", "test_query_text_displayed": False, "models_or_retrieval_run": False}
    # 真实记录采用的发布源，不把镜像说成已校验原站ZIP。
    manifest.update(source=source, data_directory=data_directory, official_archive_md5_verified=source == "beir", reference_urls=REFERENCES)
    # HF源使用独立提交和本地SHA固定。
    if source == "huggingface":
        # 两个官方仓库的提交分别保留。
        manifest.update(snapshot_pinning="Official BEIR Hugging Face repository revisions plus file SHA-256; original ZIP MD5 not verified.", repositories=repositories)
    # 保存可复现的完整来源清单。
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # 返回实际验证结果。
    return manifest


# 提供独立、可重现的数据准备入口。
if __name__ == "__main__":
    # 参数只控制离线复验，不控制算法。
    parser = argparse.ArgumentParser()
    # 重复检查时禁止触发网络下载。
    parser.add_argument("--verify-only", action="store_true")
    # 下载站超时时明确选择官方HF镜像，不隐式混合来源。
    parser.add_argument("--source", choices=("huggingface", "beir"), default="huggingface")
    # 解析用户指定行为。
    args = parser.parse_args()
    # 数据准备不调用用户的检索或生成代码。
    result = prepare(verify_only=args.verify_only, source=args.source)
    # 只打印规模和状态，不输出测试查询内容。
    print(json.dumps({"status": result["status"], **result["validation"]}, ensure_ascii=False, indent=2))

# 独立读回公开基准与原始镜像文件，不运行模型或检索。
"""Audit NFCorpus identity, splits and local tokenizer length diagnostics."""

# 检查内容指纹。
import hashlib
# 读取固定来源清单。
import json
# 定位项目数据和配置。
from pathlib import Path
# 支持其他机器指定同版本本地分词器。
import argparse

# 用不同于下载器的表格读取路径核对数据。
import pandas as pd
# 仅调用本地tokenizer，不加载权重。
from tokenizers import Tokenizer

# 当前脚本位于scripts/data。
ROOT = Path(__file__).resolve().parents[2]
# 延续已有BGE版本，避免诊断时隐式换模型。
MODEL_REVISION = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
# 使用现有本地缓存，不联网补下载。
DEFAULT_TOKENIZER = Path("/home/herdeny/.cache/huggingface/hub/models--BAAI--bge-small-en-v1.5/snapshots") / MODEL_REVISION / "tokenizer.json"


# NFCorpus各文件都很小，直接计算SHA即可。
def digest(path):
    # 指纹基于文件原始字节。
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# 校验公开数据，不实现用户的数据适配函数。
def validate(tokenizer_path=DEFAULT_TOKENIZER):
    # 将路径参数标准化。
    tokenizer_path = Path(tokenizer_path)
    # 数据与医学主库独立存放。
    folder = ROOT / "data/external/nfcorpus"
    # 取得本次真实来源版本。
    manifest = json.loads((folder / "source_manifest.json").read_text())
    # 根据清单而非猜测定位数据目录。
    data = folder / manifest["data_directory"]
    # 原始和转换文件都必须与下载收据相符。
    assert all(digest(folder / name) == receipt["sha256"] for name, receipt in manifest["files"].items())
    # 读取原始BEIR字段，不加入项目专用字段或标签。
    corpus = pd.read_json(data / "corpus.jsonl", lines=True, dtype=False)
    # 查询文件包含所有划分，尚未当作开发输入。
    queries = pd.read_json(data / "queries.jsonl", lines=True, dtype=False)
    # 保留文档ID和查询ID作为独立命名空间。
    corpus_ids, query_ids = set(corpus["_id"]), set(queries["_id"])
    # HF格式转换须逐字段保真。
    parquet_preserved = None
    # 原站ZIP来源没有Parquet容器，不作不存在的校验。
    if manifest["source"] == "huggingface":
        # 两份数据都与实际下载的Parquet字段逐值比较。
        parquet_preserved = all(pd.read_parquet(folder / "raw/huggingface" / f"{name}.parquet")[fields].to_dict("records") == frame[fields].to_dict("records") for name, fields, frame in (("corpus", ["_id", "title", "text"], corpus), ("queries", ["_id", "text"], queries)))
        # 容器转换不能改变标识、标题或正文。
        assert parquet_preserved
    # 只保存聚合结果，不展示测试内容。
    split_stats, split_ids = {}, {}
    # 独立解析官方标签。
    for split in ("train", "dev", "test"):
        # 强制ID为字符串，score为整数。
        qrels = pd.read_csv(data / "qrels" / f"{split}.tsv", sep="\t", dtype={"query-id": str, "corpus-id": str, "score": int})
        # 每对query和document必须唯一。
        assert not qrels.duplicated(["query-id", "corpus-id"]).any()
        # 不删除未找到的ID来掩盖连接失败。
        assert set(qrels["query-id"]) <= query_ids and set(qrels["corpus-id"]) <= corpus_ids
        # 原始HF标签和规范目录中的副本必须逐字节相同。
        if manifest["source"] == "huggingface":
            # 标签没有重新构造或随机分配。
            assert digest(data / "qrels" / f"{split}.tsv") == digest(folder / "raw/huggingface" / f"{split}.tsv")
        # 保存原始划分的题号集合。
        split_ids[split] = set(qrels["query-id"])
        # 相关性等级保持整数，不变成单一gold文档。
        split_stats[split] = {"queries": len(split_ids[split]), "qrel_rows": len(qrels), "grade_counts": {str(key): int(value) for key, value in qrels["score"].value_counts().sort_index().items()}}
    # 官方题号应在三个划分间隔离。
    assert all(not split_ids[left] & split_ids[right] for left, right in (("train", "dev"), ("train", "test"), ("dev", "test")))
    # 查询均应有明确的官方划分。
    assert set.union(*split_ids.values()) == query_ids
    # 只构造计划中的文档输入用于长度诊断，不作为已编码向量。
    texts = corpus["title"].str.cat(corpus["text"], sep=" ").str.strip().str.replace("\n", " ", regex=False)
    # 读取固定本地tokenizer。
    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    # 全长计数，不能静默截断再声称没有长文。
    tokenizer.no_truncation()
    # 不将padding算入原文长度。
    tokenizer.no_padding()
    # 长度包含CLS与SEP等特殊token。
    document_lengths = [len(tokenizer.encode(text, add_special_tokens=True).ids) for text in texts]
    # 查询长度诊断只查看开发集输入。
    dev_texts = queries.loc[queries["_id"].isin(split_ids["dev"]), "text"]
    # 延续原有BGE检索提示。
    prefix = "Represent this sentence for searching relevant passages: "
    # 模拟现有LangChain封装的换行处理。
    dev_lengths = [len(tokenizer.encode(prefix + text.replace("\n", " "), add_special_tokens=True).ids) for text in dev_texts]
    # 检查旧实验和用户核心模块未被数据准备改写。
    protected = json.loads((ROOT / "results/ct_eval_v3_input_receipt.json").read_text())["protected_sha256"]
    # 只比对指纹，不运行旧检索。
    assert all(digest(ROOT / name) == sha for name, sha in protected.items())
    # 输出独立的数据审计结果，编码设置仍明确标为计划。
    report = {"status": "passed_data_integrity_no_retrieval_or_model_run", "client_date": "2026-11-21", "source": manifest["source"], "source_manifest_sha256": digest(folder / "source_manifest.json"), "validator_sha256": digest(Path(__file__)), "documents": len(corpus), "queries_total": len(queries), "splits": split_stats, "all_raw_and_prepared_hashes_match": True, "parquet_field_values_preserved": parquet_preserved, "all_qrels_ids_resolve": True, "official_split_query_ids_disjoint": True, "all_queries_assigned": True, "protected_old_artifact_and_learner_module_count": len(protected), "protected_files_unchanged": True, "length_diagnostics": {"tokenizer_revision": MODEL_REVISION, "tokenizer_sha256": digest(tokenizer_path), "special_tokens_included": True, "truncation_disabled_for_counting": True, "max_document_tokens": max(document_lengths), "documents_over_512": sum(value > 512 for value in document_lengths), "max_dev_query_tokens_with_prefix": max(dev_lengths)}, "planned_dense_input_policy": "title + space + full body as input; BGE v1.5 max_seq_length=512 means encoding truncation for long documents, explicitly logged; raw documents and qrels remain intact. No benchmark encoding has run.", "qrels_origin": manifest["qrels_origin"], "retrieval_models_called": False, "test_query_text_displayed": False, "clinical_validation": False}
    # 只新增本公开基准的验证记录。
    destination = ROOT / "results/nfcorpus_data_validation.json"
    # 保存完整校验明细。
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # 返回聚合信息。
    return report


# 提供离线复验入口。
if __name__ == "__main__":
    # 参数只影响本地分词器位置。
    parser = argparse.ArgumentParser()
    # 允许其他开发机器指定同版本缓存。
    parser.add_argument("--tokenizer", type=Path, default=DEFAULT_TOKENIZER)
    # 执行结构和长度诊断，不编码文档。
    result = validate(parser.parse_args().tokenizer)
    # 不打印测试题或标签明细。
    print(json.dumps({key: result[key] for key in ("status", "documents", "queries_total", "splits", "length_diagnostics")}, ensure_ascii=False, indent=2))

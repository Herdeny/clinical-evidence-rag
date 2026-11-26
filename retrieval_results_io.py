# 下面的文档字符串说明本模块、类或函数的用途和适用边界。
"""Save learner-computed retrieval results; never encodes, retrieves or scores."""

# 导入内容指纹工具。
import hashlib
# 导入JSON 编解码工具。
import json
# 导入路径对象 Path，便于定位脚本、组合目录并读写文件。
from pathlib import Path

# 导入表格及 JSONL 读写工具。
import pandas as pd


# 定义 _sha256_file：以流式读取计算输入文件指纹，记录评测真正使用的数据版本。
def _sha256_file(path):
    # 设置摘要计算器：初始化 SHA-256 内容摘要。
    digest = hashlib.sha256()
    # 进入受管理的上下文：按指定读写模式打开文件，并在 with 退出时关闭句柄。
    with Path(path).open("rb") as stream:
        # 每次读取 1 MiB；遇到空字节 b'' 时停止，避免一次读入整个大文件。
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            # 把下一块内容加入同一个摘要计算器。
            digest.update(block)
    # 返回取出已经计算好的十六进制内容指纹，结束本次函数调用。
    return digest.hexdigest()


# 按实际检索方法验证运行元数据，同时兼容旧的顶层配置。
def _validate_method_metadata(config, method):
    # 单路方法的模型或实现信息属于该方法自己的配置。
    metadata_keys = {"model_name", "device", "query_prefix"}
    # 只有出现检索子配置才将RRF识别为新的分组布局。
    grouped_rrf = method == "rrf" and any(name in config for name in ("dense", "bm25"))
    # 组合方法分别记录两路信息，不要求虚构一个全局模型名。
    if method == 'frozen_rerank':
        # 候选来源与本轮模型分别保留，不能冒写成一次新的Dense实验。
        sections = [('config.candidate_source', config.get('candidate_source'), {'source_run_name', 'candidate_k', 'query_count', 'frozen_receipt', 'source_files', 'input_sha256'}), ('config.rerank', config.get('rerank'), {'model_name', 'revision', 'device', 'max_length', 'batch_size', 'score_type', 'actual_device', 'actual_weight_dtype', 'actual_max_length'})]
    # 组合方法分别核对两路检索参数。
    elif grouped_rrf:
        # 每一项包含报错路径、实际配置以及该层必须具有的字段。
        sections = [("config.dense", config.get("dense"), metadata_keys), ("config.bm25", config.get("bm25"), metadata_keys), ("config.rrf", config.get("rrf"), {"candidate_k", "rrf_constant"})]
    # 单路方法优先使用自己的分组配置。
    elif method in ("dense", "bm25") and method in config:
        # 新布局中不要求把同样字段再复制到顶层。
        sections = [(f"config.{method}", config[method], metadata_keys)]
    # 以前的平铺配置继续按原有字段验证。
    else:
        # 只兼容读取，不把旧配置重写为新布局。
        sections = [("config", config, metadata_keys)]
    # 分别验证实际使用的配置层。
    for label, section, required_keys in sections:
        # 无效或缺失子配置应给出具体路径。
        if not isinstance(section, dict):
            # 避免后续以含糊的属性错误掩盖配置问题。
            raise ValueError(f"{label} 必须为字典")
        # 只检查这一层需要的元数据，不扁平化或修改输入。
        missing = required_keys - section.keys()
        # 缺失时保留实际字段路径，便于定位。
        if missing:
            # 清楚说明是哪个方法配置缺少哪些字段。
            raise ValueError(f"{label} 缺少字段：{sorted(missing)}")
    # 新RRF配置还需要保证候选数和常量是有效记录。
    if grouped_rrf:
        # 两个参数与查询编排中使用的名称一致。
        for name in ("candidate_k", "rrf_constant"):
            # 读取实际参数，但不改写其值。
            value = config["rrf"][name]
            # 与查询函数约定相同，排除布尔值和非正整数。
            if type(value) is not int or value <= 0:
                # 明确指出无效参数属于RRF配置层。
                raise ValueError(f"config.rrf.{name} 必须为正整数")


# 定义 save_retrieval_results：验证用户已算好的逐题结果，保存原始结果和带输入指纹的摘要。
def save_retrieval_results(result_df, config, *, run_name=None, result_dir="results"):
    # 下面的文档字符串说明本模块、类或函数的用途和适用边界。
    """Export an existing result table and actual configuration.

    Shared evidence_path, cases_path and query_template stay at the top level.
    New configurations keep model_name, device and query_prefix inside dense
    or bm25. RRF keeps both method sections plus candidate_k/rrf_constant in
    rrf. Legacy flat metadata remains accepted; the original layout is saved
    unchanged. Add actual encoding parameters as needed.
    Metric columns must be computed by the learner before calling this function.
    CT retrieval timing uses retrieve_latency_ms, matching the evaluator output.
    Additional review fields are preserved without being folded into retrieval timing.
    retrieval_method defaults to dense for existing callers. When run_name is
    omitted, output names use <corpus_name>_<retrieval_method>_dev, with
    corpus_name defaulting to ct_v2 for compatibility with saved callers.
    """
    # 设置required：集合。
    required = {"case_id", "split", "group", "report", "question", "gold_evidence_ids",
                # 继续声明 save_retrieval_results 的输入参数或返回类型约定。
                "gold_evidence_groups", "retrieved_ids", "scores", "retrieve_latency_ms"}
    # 设置metrics：按遍历顺序筛选并整理 ('canonical_recall', 'group_recall') 中的数据。
    metrics = [f"{name}_at_{k}" for name in ("canonical_recall", "group_recall") for k in (1, 3, 5)]
    # 设置missing：required.union(metrics) - set(result_df.columns)。
    missing = required.union(metrics) - set(result_df.columns)
    # 当 missing 成立时，执行下面的分支。
    if missing:
        # 抛出 ValueError 并停止当前操作。
        raise ValueError(f"结果表缺少字段：{sorted(missing)}")
    # 评估结果和评估耗时应当成对出现，纯检索结果无需提供它们。
    review_columns = {"evidence_review", "review_latency_ms"}
    # 只在已出现评估字段时检查同阶段信息是否完整。
    if review_columns.intersection(result_df.columns) and not review_columns.issubset(result_df.columns):
        # 缺少任一字段时无法完整记录评估阶段。
        raise ValueError("评估结果需要同时提供evidence_review和review_latency_ms")
    # 设置config_keys：集合。
    config_keys = {"evidence_path", "cases_path", "query_template"}
    # 当 config_keys - config.keys() 成立时，执行下面的分支。
    if config_keys - config.keys():
        # 抛出 ValueError 并停止当前操作。
        raise ValueError(f"配置缺少字段：{sorted(config_keys - config.keys())}")
    # 设置method：按键读取字段，缺失时使用指定默认值或 None。
    method = config.get("retrieval_method", "dense")
    # 当 method not in ('dense', 'bm25', 'rrf') 成立时，执行下面的分支。
    if method not in ("dense", "bm25", "rrf"):
        # 抛出 ValueError 并停止当前操作：retrieval_method 应为 dense、bm25 或 rrf。
        raise ValueError("retrieval_method 应为 dense、bm25 或 rrf")
    # 模型和设备元数据从当前方法层验证，旧平铺配置仍可使用。
    _validate_method_metadata(config, method)
    # 设置corpus_name：按键读取字段，缺失时使用指定默认值或 None。
    corpus_name = config.get("corpus_name", "ct_v2")
    # 当 not isinstance(corpus_name, str) or not corpus_name or Path(corpus_name).name != corpus_name 成立时，执行下面的分支。
    if not isinstance(corpus_name, str) or not corpus_name or Path(corpus_name).name != corpus_name:
        # 抛出 ValueError 并停止当前操作：corpus_name 应为非空的文件名前缀。
        raise ValueError("corpus_name 应为非空的文件名前缀")
    # 当 run_name is None 成立时，执行下面的分支。
    if run_name is None:
        # 设置run_name：f'{corpus_name}_{method}_dev'。
        run_name = f"{corpus_name}_{method}_dev"
    # 当 result_df.empty or not result_df['split'].eq('dev').all() or (not result_df['case_id'].is_unique) 成立时，执行下面的分支。
    if result_df.empty or not result_df["split"].eq("dev").all() or not result_df["case_id"].is_unique:
        # 抛出 ValueError 并停止当前操作：当前导出应为非空、ID 唯一的开发集结果。
        raise ValueError("当前导出应为非空、ID 唯一的开发集结果")
    # 设置(evidence_path, cases_path)：元组。
    evidence_path, cases_path = Path(config["evidence_path"]), Path(config["cases_path"])
    # Only IDs are needed here. Do not load the entire expanded corpus a second
    # time beside the learner's already-built index and evidence table.
    # 设置evidence_ids：创建集合，去掉重复元素。
    evidence_ids = set()
    # 设置evidence_count：常量 0。
    evidence_count = 0
    # 进入受管理的上下文：按指定读写模式打开文件，并在 with 退出时关闭句柄。
    with evidence_path.open(encoding="utf-8") as stream:
        # 按顺序遍历stream，本轮元素记作 line。
        for line in stream:
            # 当 line.strip() 成立时，执行下面的分支。
            if line.strip():
                # 设置当前记录：解析 JSON 文本或字节，恢复为 Python 对象。
                record = json.loads(line)
                # 当 record['id'] in evidence_ids 成立时，执行下面的分支。
                if record["id"] in evidence_ids:
                    # 抛出 ValueError 并停止当前操作：证据 ID 不唯一。
                    raise ValueError("证据 ID 不唯一")
                # 将 HTML 节点保存为带章节、锚点和原元素位置的正文块。
                evidence_ids.add(record["id"])
                # 更新evidence_count，累计本轮处理量或内容。
                evidence_count += 1
    # 设置cases_df：调用 pd.read_json，取得该步骤的处理结果。
    cases_df = pd.read_json(cases_path, lines=True)
    # 当 set(result_df['case_id']) != set(cases_df['id']) 成立时，执行下面的分支。
    if set(result_df["case_id"]) != set(cases_df["id"]):
        # 抛出 ValueError 并停止当前操作：结果题目与所声明的开发题文件不一致。
        raise ValueError("结果题目与所声明的开发题文件不一致")
    # 按顺序遍历zip(result_df['retrieved_ids'], result_df['scores'])，本轮元素记作 (ids, scores)。
    for ids, scores in zip(result_df["retrieved_ids"], result_df["scores"]):
        # 当 len(ids) != 5 or len(scores) != 5 or len(set(ids)) != 5 or (not set(ids) <= evidence_ids) 成立时，执行下面的分支。
        if len(ids) != 5 or len(scores) != 5 or len(set(ids)) != 5 or not set(ids) <= evidence_ids:
            # 抛出 ValueError 并停止当前操作：每题必须包含来自当前证据表的 5 个不同 ID 及对应得分。
            raise ValueError("每题必须包含来自当前证据表的 5 个不同 ID 及对应得分")
        # 当 any((float(scores[i]) < float(scores[i + 1]) for i in range(4))) 成立时，执行下面的分支。
        if any(float(scores[i]) < float(scores[i + 1]) for i in range(4)):
            # 抛出 ValueError 并停止当前操作：检索得分应按降序保存。
            raise ValueError("检索得分应按降序保存")
    # 当 not result_df[metrics].ge(0).all().all() or not result_df[metrics].le(1).all().all() 成立时，执行下面的分支。
    if not result_df[metrics].ge(0).all().all() or not result_df[metrics].le(1).all().all():
        # 抛出 ValueError 并停止当前操作：Recall 应为 0 到 1 之间的有效数值。
        raise ValueError("Recall 应为 0 到 1 之间的有效数值")
    # 验证核心输出的检索阶段耗时，不将评估耗时混入其中。
    if not result_df["retrieve_latency_ms"].ge(0).all():
        # 抛出 ValueError 并停止当前操作：检索耗时必须是非负数。
        raise ValueError("检索耗时必须是非负数")
    # 当 Path(run_name).name != run_name or not run_name 成立时，执行下面的分支。
    if Path(run_name).name != run_name or not run_name:
        # 抛出 ValueError 并停止当前操作：run_name 只接受文件名前缀。
        raise ValueError("run_name 只接受文件名前缀")
    # 设置output：创建文件路径对象，便于跨目录组合与读写。
    output = Path(result_dir)
    # 创建输出目录，按参数允许补建父目录或复用已有目录。
    output.mkdir(parents=True, exist_ok=True)
    # 设置(rows_path, summary_path)：元组。
    rows_path, summary_path = output / f"{run_name}_results.jsonl", output / f"{run_name}_summary.json"
    # 保存层也保护原件，入口仍须在模型调用前提前检查同样两个路径。
    for path in (rows_path, summary_path):
        # 任一输出已存在时，不覆盖或只更新另一半。
        if path.exists():
            # 保留原有文件并提示调用方使用新的运行编号。
            raise FileExistsError(path)
    # 设置exported：调用 result_df.copy，取得该步骤的处理结果。
    exported = result_df.copy()
    # 设置exported['scores']：取得并发任务返回的处理结果。
    exported["scores"] = exported["scores"].map(lambda values: [float(value) for value in values])
    # 设置summary：字典，保存stage、实际检索方法、config、evidence_count、题目总数等信息。
    summary = {
        # 写入字段 stage（本份结果所属的数据版本与检索阶段）；字段 retrieval_method（实际检索方法）；字段 config（本次执行实际使用的参数字典）。
        "stage": f"{'CT-v2' if corpus_name == 'ct_v2' else corpus_name}-{method}-baseline", "retrieval_method": method, "config": config,
        # 写入字段 evidence_count（本次运行实际使用的证据条数）；字段 case_count（题目总数）；字段 split（开发集或留出集的固定划分）。
        "evidence_count": evidence_count, "case_count": len(exported), "split": "dev",
        # 写入字段 input_sha256（用于复现实验的输入文件指纹）。
        "input_sha256": {str(path): _sha256_file(path) for path in (evidence_path, cases_path)},
        # 写入字段 metrics（用户或验证器计算的指标汇总）。
        "metrics": exported[metrics].mean().to_dict(),
        # 按核心字段名汇总检索阶段耗时，评估阶段仍保留独立字段。
        "retrieve_latency_ms": {"mean": float(exported["retrieve_latency_ms"].mean()), "median": float(exported["retrieve_latency_ms"].median()),
                       # 写入字段 scope（本项统计或来源的适用范围）。
                       "scope": "retrieve only, including first query; excludes model loading, document encoding, index building, printing and metric calculation"},
        # 写入字段 annotation_note（标注仍需独立临床复核的说明）。
        "annotation_note": "AI initial labels, not independently clinician-reviewed",
        # 写入字段 provenance（这份结果由谁计算、辅助模块做了什么的说明）。
        "provenance": "learner-computed result table; helper only validates and saves",
    # 结束上方的字典或集合。
    }
    # 开启评估时，在同一份摘要中附加统计，不增加独立结果文件。
    if "evidence_review" in exported.columns:
        # 取出逐题完整评估记录，后续原样保留到JSONL。
        reviews = exported["evidence_review"].tolist()
        # 状态用于区分正常判断与评估失败，不把失败当作证据不足。
        if any(not isinstance(record, dict) or record.get("status") not in ("ok", "error") for record in reviews):
            # 无法识别的状态不能进入成功／失败统计。
            raise ValueError("evidence_review应包含ok或error状态")
        # 评估耗时单独检查，不影响检索阶段计时。
        if not exported["review_latency_ms"].ge(0).all():
            # 拒绝负数或缺失的耗时记录。
            raise ValueError("评估耗时必须是非负数")
        # 与已有改写记录一致，只汇总完整的实际用量。
        token_fields = ("input_tokens", "output_tokens", "total_tokens")
        # 成功与失败响应都可能已有可计费的用量信息。
        known_usage = []
        # 检查每题的原始SDK用量，不从模型解释中估计费用。
        for record in reviews:
            # 没有收到可用响应时，该值可以为None。
            usage = record.get("usage_metadata")
            # 三项用量均完整有效时才参与完整用量求和。
            if isinstance(usage, dict) and all(type(usage.get(key)) is int and usage[key] >= 0 for key in token_fields):
                # 解析失败但已取得用量的响应也会计入。
                known_usage.append(usage)
        # 这些数量是模型评估的状态统计，不代表医学准确率。
        summary["evidence_review"] = {
            "query_count": len(reviews),  # 全部参评题都计入总数。
            "ok_count": sum(record["status"] == "ok" for record in reviews),  # 成功完成评估的题数。
            "error_count": sum(record["status"] == "error" for record in reviews),  # 包含API和解析失败。
            "sufficient_count": sum(record["status"] == "ok" and isinstance(record.get("review"), dict) and record["review"].get("sufficient") is True for record in reviews),  # 模型自评充分的题数。
            "insufficient_count": sum(record["status"] == "ok" and isinstance(record.get("review"), dict) and record["review"].get("sufficient") is False for record in reviews),  # 正常判断不足的题数。
            "usage_known_count": len(known_usage),  # 可以完整统计用量的响应数。
            "usage_unknown_count": len(reviews) - len(known_usage),  # 未知用量不视为免费。
            "known_token_totals": {key: sum(usage[key] for usage in known_usage) if known_usage else None for key in token_fields},  # 全未知时保留None。
            "usage_scope": "Complete usage records only; includes errors with known usage; excludes unknown or partial usage.",  # 明示成本统计范围。
        }
        # 评估阶段耗时采用与逐题表一致的字段名。
        summary["review_latency_ms"] = {
            "mean": float(exported["review_latency_ms"].mean()),  # 只汇总评估回调的耗时。
            "median": float(exported["review_latency_ms"].median()),  # 保留中位数便于比较。
            "scope": "review_fn call only; excludes retrieval, model loading and metric computation",  # 不宣称端到端延迟。
        }
    # Validate JSON serializability before writing either artifact.
    # 设置summary_text：json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + '\n'。
    summary_text = json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    # 设置result_text：调用 exported.to_json，取得该步骤的处理结果。
    result_text = exported.to_json(orient="records", lines=True, force_ascii=False, double_precision=15)
    # 将给定文本写入指定文件。
    rows_path.write_text(result_text, encoding="utf-8")
    # 将给定文本写入指定文件。
    summary_path.write_text(summary_text, encoding="utf-8")
    # 设置loaded：调用 pd.read_json，取得该步骤的处理结果。
    loaded = pd.read_json(rows_path, lines=True)
    # 当 loaded['case_id'].tolist() != exported['case_id'].tolist() or loaded['retrieved_ids'].tolist() != export… 成立时，执行下面的分支。
    if loaded["case_id"].tolist() != exported["case_id"].tolist() or loaded["retrieved_ids"].tolist() != exported["retrieved_ids"].tolist():
        # 抛出 ValueError 并停止当前操作：结果保存后读回不一致。
        raise ValueError("结果保存后读回不一致")
    # 打印当前进度、输出文件位置或核验结果，方便观察执行状态。
    print("逐题结果：", rows_path.resolve())
    # 打印当前进度、输出文件位置或核验结果，方便观察执行状态。
    print("运行摘要：", summary_path.resolve())
    # 返回summary，结束本次函数调用。
    return summary


# 保存已经计算好的BEIR逐题结果和评分输入，不调用检索器或重新评分。
def save_beir_results(result_df, run, *, config, run_name, result_dir):
    # CSV仅用于读取当前划分的题号，避免把其他划分并入结果。
    import csv
    # 检查浮点数是否有限。
    from math import isfinite
    # 记录本次真正使用的评分包版本。
    from importlib.metadata import version
    # 配置只要求实际运行所需的共同信息，方法参数保留在各自子配置。
    required = {"dataset_name", "data_dir", "split", "retrieval_method", "ks"}
    # 缺少公共运行信息时不创建输出文件。
    if not isinstance(config, dict) or required - config.keys():
        # 给出稳定的配置错误。
        raise ValueError(f"config必须提供{sorted(required)}")
    # 支持原有检索与离线冻结候选重排，划分仍沿用BEIR标准。
    if config["retrieval_method"] not in {"dense", "bm25", "rrf", "frozen_rerank"} or config["split"] not in {"train", "dev", "test"}:
        # 未知方法或划分不能被误标成有效运行。
        raise ValueError("未知retrieval_method或split")
    # 沿用原有方法层元数据检查，不要求移动到顶层。
    _validate_method_metadata(config, config["retrieval_method"])
    # 数据集身份用于摘要，不能留空。
    if not isinstance(config["dataset_name"], str) or not config["dataset_name"].strip():
        # 拒绝没有身份的结果。
        raise ValueError("dataset_name应为非空字符串")
    # 使用与用户评测函数一致的K集合。
    ks = config["ks"]
    # 避免空、重复、布尔值或非正整数K。
    if not ks or any(type(k) is not int or k <= 0 for k in ks) or len(ks) != len(set(ks)):
        # 导出不能改变评测预算。
        raise ValueError("config.ks应为不重复的正整数序列")
    # 结果前缀限制为单个文件名。
    if not isinstance(run_name, str) or not run_name or Path(run_name).name != run_name:
        # 阻止结果写到指定目录以外。
        raise ValueError("run_name只能是非空文件名前缀")
    # 按实际K确定所有需要保存的指标。
    metrics = [f"{name}_at_{k}" for k in ks for name in ("ndcg", "recall")]
    # 查询、命中与耗时必须保留，便于逐题排错。
    columns = {"query_id", "query", "retrieved_ids", "scores", "latency_ms", *metrics}
    # 不接受空结果、重复题号或缺失字段。
    if columns - set(result_df.columns) or result_df.empty or not result_df["query_id"].is_unique:
        # 本阶段不允许静默丢题或合并重复题。
        raise ValueError("BEIR结果必须非空、题号唯一且字段完整")
    # 只读取原始文件的身份，不另行解析正文或重新运行数据准备流程。
    data_dir = Path(config["data_dir"]).resolve()
    # 三个实际输入文件都进入来源指纹。
    inputs = {"corpus": data_dir / "corpus.jsonl", "queries": data_dir / "queries.jsonl", "qrels": data_dir / "qrels" / f"{config['split']}.tsv"}
    # 在写结果前确认输入存在。
    for path in inputs.values():
        # 缺失文件保留明确的异常类型。
        if not path.is_file():
            # 不把缺文件当成一次成功评测。
            raise FileNotFoundError(path)
    # 语料只保留文档ID集合，不复制全部正文到内存。
    with inputs["corpus"].open(encoding="utf-8") as stream:
        # 标准BEIR文档身份来自原始_id字段。
        document_ids = {json.loads(line)["_id"] for line in stream if line.strip()}
    # 当前划分的题号由所选qrels决定。
    with inputs["qrels"].open(encoding="utf-8", newline="") as stream:
        # 只收集query-id，不向任何检索器传入标签。
        query_ids = {row["query-id"] for row in csv.DictReader(stream, delimiter="\t")}
    # 保留原划分大小，显式子集不能冒写为完整划分。
    split_query_ids = query_ids
    # 只有调用方明确声明子集时才改变本次应覆盖的题号集合。
    if "query_subset_ids" in config:
        # 子集来自事先确定的问题身份，不从命中情况或指标反推。
        subset_ids = config["query_subset_ids"]
        # 要求可JSON记录的非空、唯一字符串列表，避免集合转换掩盖重复。
        if not isinstance(subset_ids, list) or not subset_ids or any(not isinstance(identifier, str) or not identifier for identifier in subset_ids) or len(subset_ids) != len(set(subset_ids)):
            # 错误属于子集声明的值，不修改或丢弃结果来补救。
            raise ValueError("query_subset_ids必须为非空且唯一的字符串列表")
        # 子集中的题必须属于所声明的原始划分。
        if not set(subset_ids) <= split_query_ids:
            # 拒绝跨划分或未知题号。
            raise ValueError("query_subset_ids包含不属于当前划分的题号")
        # 结果及run仍须完整覆盖明确声明的这一组题。
        query_ids = set(subset_ids)
    # 文件、逐题结果与评分输入必须覆盖同一组题。
    if not isinstance(run, dict) or set(result_df["query_id"]) != query_ids or set(run) != query_ids:
        # 避免删除空命中或只保存容易题而改变分母。
        raise ValueError("结果、run与所选qrels的查询ID不一致")
    # 转成独立行字典，保持原始查询次序。
    records = result_df.to_dict(orient="records")
    # 为标准JSON准备真实浮点检索分数。
    normalized_run = {}
    # 核对每条查询的命中表与run是否一致。
    for row in records:
        # 用查询身份报告具体哪一题失败。
        query_id, ids, scores = row["query_id"], row["retrieved_ids"], row["scores"]
        # 文档列表需要与分数逐项对应，允许空命中或少于K。
        if len(ids) != len(scores) or len(ids) > max(ks) or len(ids) != len(set(ids)) or not set(ids) <= document_ids:
            # 不补齐或删除不合法的命中。
            raise ValueError(f"query_id={query_id}:命中ID或数量不合法")
        # 保留检索分数的Python浮点表示。
        row["scores"] = [float(value) for value in scores]
        # 非有限分数不能进入JSON或评分复现文件。
        if not all(isfinite(value) for value in row["scores"]):
            # 报告当前题号。
            raise ValueError(f"query_id={query_id}:分数必须有限")
        # 用已有逐题命中构造期望评分输入。
        expected = dict(zip(ids, row["scores"]))
        # 不允许逐题结果和评分输入保存不同文档或分数。
        if expected != run[query_id]:
            # 拒绝矛盾的实验产物。
            raise ValueError(f"query_id={query_id}:run与逐题结果不一致")
        # 保留空命中查询键。
        normalized_run[query_id] = expected
        # 指标与耗时只验证、汇总，不重新评分。
        for name in (*metrics, "latency_ms"):
            # 转成JSON原生浮点数。
            row[name] = float(row[name])
            # 指标有上下界，耗时只要求非负有限。
            if not isfinite(row[name]) or row[name] < 0 or (name != "latency_ms" and row[name] > 1):
                # 清楚定位哪一题的哪个字段不合法。
                raise ValueError(f"query_id={query_id}:{name}数值不合法")
    # 重排额外验证原候选来源和当前输出集合，不重新运行模型或评分。
    if config['retrieval_method'] == 'frozen_rerank':
        # 使用已经加载并通过核对的来源信息。
        source = config['candidate_source']
        # 所声明的原始数据必须与这次保存实际读取的输入一致。
        if any(_sha256_file(path) != source['input_sha256'][name]['sha256'] for name, path in inputs.items()):
            # 拒绝把另一版语料、查询或标签混入重排结果。
            raise ValueError('Reranking inputs differ from frozen candidate source')
        # 描述文件和三份原始检索产物都应保持原内容。
        source_files = [source['frozen_receipt'], *source['source_files'].values()]
        # 逐一核对关联的实际源文件。
        for item in source_files:
            # 已保存的来源如果变化，当前结果不能再引用旧身份。
            if _sha256_file(item['path']) != item['sha256']:
                # 来源文件名保留在错误中。
                raise ValueError(f"Frozen candidate source changed: {item['path']}")
        # 原逐题候选用于核对每题输出只来自自己的原始候选。
        source_rows = [json.loads(line) for line in Path(source['source_files']['results.jsonl']['path']).read_text(encoding='utf-8').splitlines() if line.strip()]
        # 按问题ID关联，不按原文件行号或可能重复的问题文字关联。
        original = {row['query_id']: row for row in source_rows}
        # 保留原实验全部查询，不能静默丢失空候选题。
        if len(source_rows) != len(original) or set(original) != set(normalized_run) or len(records) != source['query_count']:
            # 不改变评测分母。
            raise ValueError('Reranking query coverage differs from frozen source')
        # 每题只能重排自己原有的候选，截取数由本轮ks决定。
        for row in records:
            # 获取该题原始结果。
            old = original[row['query_id']]
            # 返回数量须等于预算内原候选数，且不得跨题换文档或改问题。
            if row['query'] != old['query'] or len(row['retrieved_ids']) != min(max(ks), len(old['retrieved_ids'])) or not set(row['retrieved_ids']) <= set(old['retrieved_ids']):
                # 明确定位对应问题。
                raise ValueError(f"query_id={row['query_id']}:reranking candidates differ from frozen source")
    # 按实际运行方法记录计时含义，避免把离线重排写成端到端召回耗时。
    latency_scope = 'frozen candidate copy and rerank only; excludes source retrieval, file/model loading and metric computation' if config['retrieval_method'] == 'frozen_rerank' else 'retrieve_fn call only; includes query encoding, excludes index construction and metric computation'
    # 所有输入检查完成后准备输出路径。
    output = Path(result_dir).resolve()
    # 独立保存逐题结果、评分输入和汇总。
    paths = {"results": output / f"{run_name}_results.jsonl", "run": output / f"{run_name}_run.json", "summary": output / f"{run_name}_summary.json"}
    # 汇总使用全部查询行，包括空命中题。
    summary = {"dataset_name": config["dataset_name"], "split": config["split"], "retrieval_method": config["retrieval_method"], "config": config, "document_count": len(document_ids), "query_count": len(records), "metrics": {name: sum(row[name] for row in records) / len(records) for name in metrics}, "latency_ms": {"mean": sum(row["latency_ms"] for row in records) / len(records), "median": float(pd.Series([row["latency_ms"] for row in records]).median()), "scope": latency_scope}, "scorer": {"package": "pytrec-eval-terrier", "version": version("pytrec-eval-terrier")}, "input_sha256": {name: {"path": str(path), "sha256": _sha256_file(path)} for name, path in inputs.items()}, "files": {name: str(path) for name, path in paths.items()}, "provenance": "learner-computed per-query metrics; helper validates, aggregates and saves"}
    # 旧的整划分输出保持原布局，子集摘要额外明确原划分和本次分母。
    if "query_subset_ids" in config:
        # 具体题号已原样保留在config.query_subset_ids中。
        summary["query_scope"] = {"mode": "explicit_subset", "split_query_count": len(split_query_ids), "evaluated_query_count": len(query_ids)}
    # 所有内容先完成严格序列化，再创建文件。
    texts = {"results": "".join(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n" for row in records), "run": json.dumps(normalized_run, ensure_ascii=False, indent=2, allow_nan=False) + "\n", "summary": json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n"}
    # 已有结果不覆盖，保留原实验身份。
    for path in paths.values():
        # 三个目标中任何一个已存在就拒绝整次导出。
        if path.exists():
            # 调用者可使用新的运行名称。
            raise FileExistsError(path)
    # 确认全部验证通过后创建结果目录。
    output.mkdir(parents=True, exist_ok=True)
    # 保存本次创建的文件，用于普通写入失败时清理。
    created = []
    # 摘要最后写入，普通写入失败不留下半套结果。
    try:
        # 字典顺序对应逐题、run、摘要。
        for name, path in paths.items():
            # 排他创建可以避免误覆盖并发生成的同名文件。
            with path.open("x", encoding="utf-8") as stream:
                # 只记录本次已成功创建的文件。
                created.append(path)
                # 写入已完成验证和序列化的内容。
                stream.write(texts[name])
    # 仅清理本次创建的文件，不动已有实验。
    except Exception:
        # 写入失败时回收当前导出拥有的文件。
        for path in created:
            # 排他创建确保此处不删除别人的旧文件。
            path.unlink(missing_ok=True)
        # 原始异常保留给调用者。
        raise
    # 返回汇总，供CLI打印或后续独立核验。
    return summary

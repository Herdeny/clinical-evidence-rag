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
    if grouped_rrf:
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
    retrieval_method defaults to dense for existing callers. When run_name is
    omitted, output names use <corpus_name>_<retrieval_method>_dev, with
    corpus_name defaulting to ct_v2 for compatibility with saved callers.
    """
    # 设置required：集合。
    required = {"case_id", "split", "group", "report", "question", "gold_evidence_ids",
                # 继续声明 save_retrieval_results 的输入参数或返回类型约定。
                "gold_evidence_groups", "retrieved_ids", "scores", "latency_ms"}
    # 设置metrics：按遍历顺序筛选并整理 ('canonical_recall', 'group_recall') 中的数据。
    metrics = [f"{name}_at_{k}" for name in ("canonical_recall", "group_recall") for k in (1, 3, 5)]
    # 设置missing：required.union(metrics) - set(result_df.columns)。
    missing = required.union(metrics) - set(result_df.columns)
    # 当 missing 成立时，执行下面的分支。
    if missing:
        # 抛出 ValueError 并停止当前操作。
        raise ValueError(f"结果表缺少字段：{sorted(missing)}")
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
    # 当 not result_df['latency_ms'].ge(0).all() 成立时，执行下面的分支。
    if not result_df["latency_ms"].ge(0).all():
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
        # 写入字段 latency_ms（计时范围内的毫秒延迟）；字段 mean（逐题数值的算术平均值）；字段 median（逐题数值的中位数）。
        "latency_ms": {"mean": float(exported["latency_ms"].mean()), "median": float(exported["latency_ms"].median()),
                       # 写入字段 scope（本项统计或来源的适用范围）。
                       "scope": "retrieve only, including first query; excludes model loading, document encoding, index building, printing and metric calculation"},
        # 写入字段 annotation_note（标注仍需独立临床复核的说明）。
        "annotation_note": "AI initial labels, not independently clinician-reviewed",
        # 写入字段 provenance（这份结果由谁计算、辅助模块做了什么的说明）。
        "provenance": "learner-computed result table; helper only validates and saves",
    # 结束上方的字典或集合。
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

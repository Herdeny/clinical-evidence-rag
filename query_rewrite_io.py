import json  # 将逐题结果、统计和公开配置写为JSON。
from pathlib import Path  # 处理输出目录及文件名。


def save_rewrite_results(records, *, config, run_name, result_dir):  # 保存已取得的结果，不调用模型。
    records = list(records)  # 固定本次需要保存的记录，不修改各记录内容。
    if not isinstance(run_name, str):  # 文件名必须由字符串指定。
        raise TypeError("run_name must be a string")  # 保留类型错误的实际含义。
    if not run_name.strip() or Path(run_name).name != run_name or run_name in (".", ".."):  # 限制为单个非空文件名前缀。
        raise ValueError("run_name must be a nonempty filename prefix")  # 防止前缀指向输出目录之外。
    required = {"query_id", "original_query", "status", "retrieval_query", "changed", "reason", "usage_metadata", "response_metadata", "error"}  # 每题保留ID及核心函数的八个字段。
    query_ids = []  # 收集题号，以检查重复记录。
    for record in records:  # 保存前先检查整批记录的基本结构。
        if not required.issubset(record):  # 基本字段缺失会影响后续题目对齐和成本统计。
            raise ValueError(f"Missing rewrite record fields: {sorted(required - set(record))}")  # 明确指出缺少的字段。
        if not isinstance(record["query_id"], str) or not record["query_id"].strip():  # 原样保留非空字符串ID。
            raise ValueError("query_id must be a nonempty string")  # 不通过类型转换改变题号。
        if record["status"] not in ("ok", "error"):  # 两种状态与已验收的核心协议一致。
            raise ValueError("status must be ok or error")  # 避免无法分类的记录被遗漏。
        query_ids.append(record["query_id"])  # 保持输入顺序。
    if len(query_ids) != len(set(query_ids)):  # 同一次运行中每道题只能出现一次。
        raise ValueError("Duplicate query_id in rewrite results")  # 阻止后续按ID读取时相互覆盖。
    token_fields = ("input_tokens", "output_tokens", "total_tokens")  # 分别统计三种实际用量。
    known_usage = []  # 只汇总具备完整数值的响应元数据。
    for record in records:  # 成功和失败记录都参与用量检查。
        usage = record["usage_metadata"]  # 读取SDK用量，而不是模型reason中的数字。
        if isinstance(usage, dict) and all(type(usage.get(key)) is int and usage[key] >= 0 for key in token_fields):  # 三项均已知时才计入完整用量。
            known_usage.append(usage)  # 解析失败但有用量的调用也会计入。
    summary = {  # 汇总状态和已知成本，不判断医学语义或检索效果。
        "query_count": len(records),  # 保存的题目总数。
        "ok_count": sum(record["status"] == "ok" for record in records),  # 成功取得结构化改写的题数。
        "error_count": sum(record["status"] == "error" for record in records),  # 失败题数。
        "changed_count": sum(record["status"] == "ok" and record["changed"] is True for record in records),  # 成功且改写发生变化的题数。
        "unchanged_count": sum(record["status"] == "ok" and record["changed"] is False for record in records),  # 成功且表达不变的题数。
        "usage_known_count": len(known_usage),  # 能完整统计三项token用量的题数。
        "usage_unknown_count": len(records) - len(known_usage),  # 用量缺失或不完整的题数，不能视为免费。
        "known_token_totals": {key: sum(usage[key] for usage in known_usage) if known_usage else None for key in token_fields},  # 仅对已知用量求和，全未知时保留None。
        "usage_scope": "Complete usage records only; includes errors with known usage; excludes unknown or partial usage.",  # 明示统计覆盖范围。
    }  # 逐题原始usage_metadata仍完整保留在JSONL中。
    result_dir = Path(result_dir)  # 接受字符串或Path形式的输出目录。
    paths = {  # 三份文件共用用户指定的运行前缀。
        "results": result_dir / f"{run_name}_results.jsonl",  # 一行一题，供后续按query_id关联检索结果。
        "summary": result_dir / f"{run_name}_summary.json",  # 保存状态数量和已知token统计。
        "run": result_dir / f"{run_name}_run.json",  # 保存调用方提供的公开运行配置。
    }  # 不自动生成时间戳或改变已有运行名。
    payloads = {  # 先完成全部序列化，避免坏数据写出半份文件。
        "results": "".join(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n" for record in records),  # 保留全部逐题字段和输入顺序。
        "summary": json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False) + "\n",  # 生成可读统计JSON。
        "run": json.dumps({"run_name": run_name, "config": config}, ensure_ascii=False, indent=2, allow_nan=False) + "\n",  # 配置由入口提供，不读取环境变量。
    }  # 此前没有创建或覆盖任何结果文件。
    for path in paths.values():  # 写入前检查三份输出是否已经存在。
        if path.exists():  # 任意一份已存在时整批拒绝覆盖。
            raise FileExistsError(path)  # 提示调用方手动改用新的运行编号。
    result_dir.mkdir(parents=True, exist_ok=True)  # 创建结果目录，不创建模型缓存或网络连接。
    created = []  # 仅跟踪本次成功创建的文件。
    try:  # 写入失败时清理本次创建的部分产物。
        for kind, path in paths.items():  # 按结果、统计、配置的顺序写入。
            with path.open("x", encoding="utf-8") as stream:  # 独占创建，已有文件不会被截断。
                created.append(path)  # 在实际写入前登记本次新文件。
                stream.write(payloads[kind])  # 写入已经验证可序列化的文本。
    except Exception:  # 只为清理本次文件而捕获错误。
        for path in created:  # 不触碰预先存在或未由本次创建的文件。
            path.unlink(missing_ok=True)  # 删除本次未完成的一组产物。
        raise  # 原样传播写入异常，不伪造成功。
    return summary  # 返回与摘要文件一致的统计字典。

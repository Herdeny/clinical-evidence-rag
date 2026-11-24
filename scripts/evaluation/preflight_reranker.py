# 在用户终端检查真实重排模型，不运行完整排序评测。
import argparse
# 保存实际输入、模型配置与预检结果。
import json
# 记录实际文件内容身份。
import hashlib
# 组合显式传入的项目路径。
from pathlib import Path
# 分别测量加载与小批打分，不冒充稳定查询延迟。
from time import perf_counter
# 检查原始分数的形状和有限性。
import numpy as np
# 读取真实GPU属性及显存峰值。
import torch
# 在联合输入统计阶段显示逐题进度。
from tqdm import tqdm
# 记录包装器实际设置的缓存位置。
from huggingface_hub import constants as hub_constants
# 复用已有只读候选加载器。
from frozen_candidates_io import load_frozen_candidates
# 与正式运行入口共用唯一模型构造与描述接口。
from reranker_adapter import build_reranker, describe_reranker


# 分块读取文件指纹，不一次复制大文件。
def file_sha256(path):
    # 每个输入单独计算SHA256。
    digest = hashlib.sha256()
    # 输入只读打开。
    with Path(path).open('rb') as stream:
        # 每次最多读取1MiB。
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            # 累加实际内容。
            digest.update(block)
    # 返回可保存的摘要。
    return digest.hexdigest()


# 用模型真实预处理器统计问题、正文、指令和模板合计长度。
def scan_candidate_lengths(reranker, frozen):
    # 使用和predict默认解析一致的指令。
    prompt = reranker.prompts.get(reranker.default_prompt_name)
    # 保存每个句对的真实长度，不保留全部副本文档。
    lengths = []
    # 前两个实际句对用于小批检查。
    samples = []
    # 另取最长联合输入，覆盖本批材料的实际长度边界。
    longest = None
    # 遍历原问题表，保留相同文字但不同ID的题目。
    for row in tqdm(frozen.queries_df.to_dict(orient='records'), desc='统计联合输入长度', unit='query'):
        # 只按ID取得原候选，不调用检索或读取相关性等级。
        hits = frozen.get_hits(row['id'])
        # CPU分词每批32对；这与配置中的GPU推理batch_size无关。
        for start in range(0, len(hits), 32):
            # 控制本次分词的内存占用。
            batch = hits[start:start + 32]
            # 原问题和完整正文作为模型实际句对。
            pairs = [(row['query'], hit['text']) for hit in batch]
            # 只关闭此次统计的截断，模型本身的正式输入预算不变。
            features = reranker.preprocess(pairs, prompt=prompt, processing_kwargs={'text': {'padding': True, 'truncation': False}, 'chat_template': {'truncation': False}})
            # 注意力掩码排除填充，统计真实模板后的token数量。
            counts = features['attention_mask'].sum(dim=1).tolist()
            # 每个句对必须有自己的长度，不能默默漏掉输入。
            if len(counts) != len(batch):
                # 记录预处理器没有按预期返回的情况。
                raise ValueError('Joint token lengths do not match candidate count')
            # 分别保存实际句对长度与少量样本。
            for hit, count in zip(batch, counts):
                # JSON使用普通Python整数。
                count = int(count)
                # 累积本轮分布统计。
                lengths.append(count)
                # 样本保留原文供稍后真实predict使用。
                sample = {'query_id': row['id'], 'document_id': hit['id'], 'query': row['query'], 'text': hit['text'], 'joint_tokens': count}
                # 首两个句对保持原始顺序。
                if len(samples) < 2:
                    # 只保存少量候选引用。
                    samples.append(sample)
                # 最长输入作为额外显存样本。
                if longest is None or count > longest['joint_tokens']:
                    # 每次只替换单个最长样本。
                    longest = sample
    # 没有句对时无法声称完成模型打分预检。
    if not lengths:
        # 合法空候选评测由核心支持，当前工具需要真实打分样本。
        raise ValueError('No candidate pairs are available for model preflight')
    # 超限统计依据模型实际生效的联合输入上限。
    limit = reranker.max_seq_length
    # 去重避免最长样本与开头样本重复。
    samples = list({(item['query_id'], item['document_id']): item for item in [*samples, longest]}.values())
    # 返回汇总与最多三个待打分样本。
    return {'pair_count': len(lengths), 'joint_token_min': min(lengths), 'joint_token_max': max(lengths), 'joint_token_p95': float(np.percentile(lengths, 95)), 'pairs_over_limit': sum(count > limit for count in lengths), 'max_length': limit}, samples


# 检查原始分数，不要求概率范围或L2归一化。
def check_scores(values, count):
    # 与用户rerank使用相同的NumPy输出语义。
    scores = np.asarray(values)
    # 每个句对应返回一个有限分数。
    if scores.ndim != 1 or scores.shape != (count,) or not np.isfinite(scores).all():
        # 不裁剪或补分掩盖错误输出。
        raise ValueError(f'Invalid reranker score array: {scores.shape}, expected {(count,)}')
    # 转成普通浮点数写入JSON，保留负数和大于1的合法logit。
    return {'shape': list(scores.shape), 'dtype': str(scores.dtype), 'all_finite': True, 'scores': [float(value) for value in scores]}


# 正式GPU预检仅在用户显式运行本工具时发生。
def run_preflight(config_dir, data_dir, receipt_path, profile_name):
    # 使用与正式入口相同的配置文件。
    profile_path = Path(config_dir) / 'reranker_profiles.json'
    # 配置文本通过标准JSON解析。
    profile = json.loads(profile_path.read_text(encoding='utf-8'))[profile_name]
    # 先核对实际候选来源，再占用GPU。
    frozen = load_frozen_candidates(receipt_path, data_dir=data_dir)
    # 预检必须在用户可见GPU终端执行，不自动回退到CPU。
    if torch.device(profile['device']).type != 'cuda' or not torch.cuda.is_available():
        # 没有GPU时直接说明运行环境要求。
        raise RuntimeError('Run this preflight in your CUDA terminal')
    # 显式GPU索引优先，cuda未写索引时使用当前设备。
    requested_index = torch.device(profile['device']).index
    # CUDA统计接口统一接收实际整数索引。
    device = torch.cuda.current_device() if requested_index is None else requested_index
    # 按配置设备设置当前统计对象。
    torch.cuda.set_device(device)
    # 将加载和小批推理都计入本次显存峰值。
    torch.cuda.reset_peak_memory_stats(device)
    # 核对预检期间配置、代码和来源文件没有变化。
    source_info = frozen.info
    # 保存参与本轮的代码与配置路径。
    paths = {'profile_file': profile_path, 'receipt': Path(receipt_path), 'preflight_code': Path(__file__), 'adapter_code': Path(__file__).resolve().parents[2] / 'reranker_adapter.py'}
    # 实际corpus、queries与qrels也需要维持原身份。
    paths.update({f'input_{name}': Path(item['path']) for name, item in source_info['input_sha256'].items()})
    # 原三份检索产物保持同一版本。
    paths.update({f'source_{name}': Path(item['path']) for name, item in source_info['source_files'].items()})
    # 模型加载前绑定这些实际输入。
    input_sha256 = {name: file_sha256(path) for name, path in paths.items()}
    # 显示模型加载阶段。
    print(f"加载固定重排模型：{profile['model_name']}", flush=True)
    # 记录包含初始化的加载时间。
    started = perf_counter()
    # 与正式入口共用相同构造函数。
    reranker = build_reranker(profile)
    # 等待GPU加载完成。
    torch.cuda.synchronize(device)
    # 单独记录模型加载耗时。
    load_seconds = perf_counter() - started
    # 读取并核对实际设备、精度、长度、指令与激活。
    runtime = describe_reranker(reranker, profile_name=profile_name, profile=profile, config_path=profile_path)
    # 使用实际预处理器统计全部固定候选的联合长度。
    print(f"统计{source_info['query_count']}题的原始候选联合输入长度", flush=True)
    # 不执行完整32400句对的模型打分。
    length_report, samples = scan_candidate_lengths(reranker, frozen)
    # 先展示长度结果，即使需要调整预算也能定位原因。
    print(json.dumps(length_report, ensure_ascii=False), flush=True)
    # 本轮要求完整保留这些输入，不能默默截断后继续声称相同材料。
    if length_report['pairs_over_limit']:
        # 显示超限规模与实际最大值。
        raise ValueError(f'Joint input exceeds configured budget: {length_report}')
    # 样本由首两对和最长联合输入组成。
    pairs = [(sample['query'], sample['text']) for sample in samples]
    # 显示真正要送GPU的少量输入规模。
    print(f"小批真实打分：{len(pairs)}个句对，batch_size={profile['batch_size']}", flush=True)
    # 同步后开始记录小批打分时间。
    torch.cuda.synchronize(device)
    # 不把该小批耗时当作完整查询延迟。
    started = perf_counter()
    # 采用用户rerank中已经使用的实际predict参数。
    values = reranker.predict(pairs, batch_size=profile['batch_size'], show_progress_bar=True, convert_to_numpy=True)
    # 等待GPU完成后结束计时。
    torch.cuda.synchronize(device)
    # 记录少量样本的实际打分时间。
    sample_seconds = perf_counter() - started
    # 检查一维有限的原始打分。
    score_report = check_scores(values, len(pairs))
    # 预检过程不应同时混入新配置或新输入。
    if input_sha256 != {name: file_sha256(path) for name, path in paths.items()}:
        # 文件发生变化时不写成通过结果。
        raise RuntimeError('Preflight inputs or source changed during execution')
    # 保存样本身份、长度与分数，不重复写入长篇正文。
    sample_report = [{key: value for key, value in sample.items() if key != 'text'} | {'score': score} for sample, score in zip(samples, score_report['scores'])]
    # 生成可回查的预检报告，不计算排序效果指标。
    return {'status': 'passed', 'scope': 'real runtime metadata, joint length scan and at most three real scores; no full ranking benchmark', 'profile_name': profile_name, 'reranker': runtime, 'candidate_source': source_info, 'input_sha256': input_sha256, 'query_count': source_info['query_count'], 'length_check': length_report, 'score_check': score_report, 'samples': sample_report, 'model_load_seconds': load_seconds, 'sample_predict_seconds': sample_seconds, 'gpu_name': torch.cuda.get_device_name(device), 'gpu_total_bytes': torch.cuda.get_device_properties(device).total_memory, 'gpu_peak_allocated_bytes': torch.cuda.max_memory_allocated(device), 'gpu_peak_reserved_bytes': torch.cuda.max_memory_reserved(device), 'cache_locations': {'hf_hub_cache': hub_constants.HF_HUB_CACHE, 'hf_xet_cache': hub_constants.HF_XET_CACHE}}


# 导入模块不会启动模型或解析命令行。
if __name__ == '__main__':
    # 所有模型与输入位置都明确出现在命令里。
    parser = argparse.ArgumentParser(description='Check a fixed reranker in your GPU terminal')
    # 沿用显式配置目录的项目约定。
    parser.add_argument('--config-dir', type=Path, required=True)
    # 配套数据必须与冻结描述文件一致。
    parser.add_argument('--data-dir', type=Path, required=True)
    # 指向已经核对的固定候选描述文件。
    parser.add_argument('--receipt', type=Path, required=True)
    # 三种既定候选共用一个预检工具。
    parser.add_argument('--profile', choices=['qwen3_4b', 'qwen3_8b', 'bge_v2_m3'], required=True)
    # 每次真实运行使用独立报告名。
    parser.add_argument('--output', type=Path, required=True)
    # 解析实际传入值。
    args = parser.parse_args()
    # 在占用GPU前拒绝覆盖已有报告。
    if args.output.exists():
        # 重跑时由用户指定新编号。
        raise FileExistsError(args.output)
    # 仅此处执行真实预检。
    report = run_preflight(args.config_dir, args.data_dir, args.receipt, args.profile)
    # 成功后准备结果目录。
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # 使用排他创建保留已有报告。
    with args.output.open('x', encoding='utf-8') as stream:
        # 标准JSON拒绝非法数值。
        stream.write(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    # 终端只展示主要结果，完整来源保留在报告。
    display = {name: report[name] for name in ('status', 'profile_name', 'gpu_name', 'query_count', 'length_check', 'score_check', 'gpu_peak_allocated_bytes', 'gpu_peak_reserved_bytes')}
    # 展示实际生效的模型运行属性。
    display['actual_runtime'] = {name: report['reranker'][name] for name in ('actual_device', 'actual_weight_dtype', 'actual_max_length')}
    # 报告位置便于后续核对。
    display['report_path'] = str(args.output.resolve())
    # 即时输出当前预检结论。
    print(json.dumps(display, ensure_ascii=False, indent=2), flush=True)

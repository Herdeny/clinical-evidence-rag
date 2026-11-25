# 在用户可见终端检查模型配置与小批编码，不构建全量文档缓存或运行检索评测。
import argparse
# 保存配置、输入指纹和小批检查结果。
import json
# 计算实际使用文件的内容身份。
import hashlib
# 组合配置、输入和结果路径。
from pathlib import Path
# 分别记录模型加载和小批编码时间。
from time import perf_counter
# 只读取明确的模型缓存变量，用于证明实际加载位置。
import os
# 检查向量形状、有限值和归一化。
import numpy as np
# 读取真实GPU信息与权重精度，不改变驱动或模型规模。
import torch
# 集中构造模型并选择同一输出适配策略，正式入口也应调用此辅助。
from embedding_adapter import build_embedding_model
# 保存Hub真实解析出的缓存路径，不读取认证信息。
from huggingface_hub import constants as hub_constants
# 复用已验收的BEIR读取器，只读取dev及其配套语料。
from benchmark_data import load_beir_dataset

# 从本模块位置定位项目根目录。
ROOT = Path(__file__).resolve().parents[2]


# 分块计算文件指纹，避免额外复制输入。
def file_sha256(path):
    # 每个文件使用独立摘要器。
    digest = hashlib.sha256()
    # 只读目标文件。
    with Path(path).open('rb') as stream:
        # 每次最多读取1MiB。
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            # 累加当前块。
            digest.update(block)
    # 返回用于回查的十六进制摘要。
    return digest.hexdigest()


# 按实际LangChain换行处理和显式prompt统计未截断的输入长度。
def token_lengths(tokenizer, texts, prompt):
    # 保存与原文顺序相同的长度。
    lengths = []
    # 分批分词，避免一次展开整个语料。
    for start in range(0, len(texts), 64):
        # LangChain先把原文换行替换为空格，再由编码器添加prompt。
        inputs = [prompt + text.replace('\n', ' ') for text in texts[start:start + 64]]
        # 关闭截断才能测出超过实际上限的输入，保留模型特殊token。
        encoded = tokenizer(inputs, padding=False, truncation=False, return_length=True)
        # 按原顺序累积真实分词长度。
        lengths.extend(int(length) for length in encoded['length'])
    # 返回普通列表，便于写入JSON。
    return lengths


# 验证实际编码结果，不把配置声明当作模型输出。
def check_vectors(values, rows, dimension):
    # LangChain返回浮点列表，磁盘缓存也将采用float32。
    vectors = np.asarray(values, dtype=np.float32)
    # 形状必须与实际样本和完整输出维度一致。
    if vectors.shape != (rows, dimension) or not np.isfinite(vectors).all():
        # 错误结果不能进入后续建库。
        raise ValueError(f'Invalid embedding matrix: {vectors.shape}, expected {(rows, dimension)}')
    # 使用高精度范数检查归一化。
    norms = np.linalg.norm(vectors.astype(np.float64), axis=1)
    # 当前两套固定配置都要求单位向量。
    if not np.allclose(norms, 1.0, rtol=1e-3, atol=1e-5):
        # 显式暴露归一化偏差。
        raise ValueError(f'Embeddings are not L2 normalized: min={norms.min():.9f}, max={norms.max():.9f}')
    # 保存数值检查摘要，不保存无用的完整向量。
    return {'shape': list(vectors.shape), 'dtype': str(vectors.dtype), 'all_finite': True, 'norm_min': float(norms.min()), 'norm_max': float(norms.max())}


# 用户终端执行真实预检；只编码最多三篇文档及一条原查询。
def run_preflight(config_dir, data_dir, profile_name):
    # 配置目录必须由调用方明确提供。
    profile_path = config_dir / 'embedding_profiles.json'
    # 使用与正式入口相同的受版本管理参数。
    profile = json.loads(profile_path.read_text(encoding='utf-8'))[profile_name]
    # 本轮目标是在CUDA运行，无法看到设备时立即失败。
    if profile['model_kwargs']['device'] != 'cuda' or not torch.cuda.is_available():
        # 不偷偷回退CPU而改变实验条件。
        raise RuntimeError('CUDA is required; run this preflight in your GPU terminal')
    # 只使用当前可见的默认GPU。
    device = torch.cuda.current_device()
    # 峰值从模型加载前开始记录，包含权重及小批推理。
    torch.cuda.reset_peak_memory_stats(device)
    # 保存参与本轮检查的输入与代码身份。
    paths = {'profiles': profile_path, 'corpus': data_dir / 'corpus.jsonl', 'queries': data_dir / 'queries.jsonl', 'qrels_dev': data_dir / 'qrels/dev.tsv', 'preflight_code': Path(__file__)}
    # 开始时绑定所有输入文件。
    input_sha = {name: file_sha256(path) for name, path in paths.items()}
    # 模型加载前先显示当前阶段，避免下载／加载期间看不到进度。
    print(f"加载固定模型：{profile['model_name']}", flush=True)
    # 记录实际加载开始时间。
    started = perf_counter()
    # 使用共享构造辅助，同时保留权重精度、prompt和输出策略。
    model = build_embedding_model(profile)
    # 等待CUDA完成加载后再记录耗时。
    torch.cuda.synchronize(device)
    # 记录包含CPU初始化和GPU加载的实际耗时。
    load_seconds = perf_counter() - started
    # 读取真实模型输出维度和输入上限。
    dimension, limit = model._client.get_embedding_dimension(), model._client.max_seq_length
    # 配置和实际值必须一致。
    if dimension != profile['dimension'] or limit != profile['max_seq_length']:
        # 不允许以错误元数据继续建立缓存。
        raise ValueError(f'Model/config mismatch: dimension={dimension}, max_seq_length={limit}')
    # 读取真实权重设备与精度，而非只打印配置。
    parameter = next(model._client.parameters())
    # 确保实际权重已经位于CUDA。
    if parameter.device.type != 'cuda':
        # 显式禁止意外CPU运行。
        raise ValueError(f'Unexpected model device: {parameter.device}')
    # Qwen固定配置使用未量化BF16权重。
    if profile_name == 'qwen3_8b' and parameter.dtype != torch.bfloat16:
        # 不将其他精度的成本误记为当前配置。
        raise ValueError(f'Unexpected Qwen weight dtype: {parameter.dtype}')
    # 读取与真实评测相同的文档和dev查询。
    corpus, queries, _ = load_beir_dataset(data_dir, split='dev')
    # 保留标题拼接后的完整原文。
    texts, questions = corpus['text'].tolist(), queries['query'].tolist()
    # 分词统计阶段单独显示进度。
    print(f'统计输入长度：{len(texts)}篇文档，{len(questions)}条dev查询', flush=True)
    # 按实际文档prompt和分词器统计所有正文。
    document_lengths = token_lengths(model._client.tokenizer, texts, model.encode_kwargs['prompt'])
    # 查询使用实际Qwen或BGE前缀，不沿用另一模型的格式。
    query_lengths = token_lengths(model._client.tokenizer, questions, model.query_encode_kwargs['prompt'])
    # 取前两篇及实际最长文档，避免仅检查最短样本。
    indices = list(dict.fromkeys([0, min(1, len(texts) - 1), int(np.argmax(document_lengths))]))
    # 文本仍保持读取器返回的原始内容，交由真实LangChain接口处理。
    samples = [texts[index] for index in indices]
    # 编码前提示用户实际批次与样本数。
    print(f"小批编码：{len(samples)}篇文档＋1条查询，文档batch={model.encode_kwargs['batch_size']}", flush=True)
    # 计时从同步完成的GPU状态开始。
    torch.cuda.synchronize(device)
    # 记录小批正文编码开始时间。
    started = perf_counter()
    # 真实正文只调用一次编码接口。
    document_check = check_vectors(model.embed_documents(samples), len(samples), dimension)
    # 保存正文输出归一化前后的实测范数，后续query不会覆盖此副本。
    document_check['output_normalization'] = getattr(model, 'last_output_normalization', None)
    # 等待GPU完成再记录端到端小批耗时。
    torch.cuda.synchronize(device)
    # 这不是全库编码时间或逐题检索延迟。
    document_seconds = perf_counter() - started
    # 单独记录查询编码开始时间。
    started = perf_counter()
    # 查询采用dev第一条原文，不使用标签或答案。
    query_check = check_vectors([model.embed_query(questions[0])], 1, dimension)
    # 查询也记录同一输出策略的实际效果。
    query_check['output_normalization'] = getattr(model, 'last_output_normalization', None)
    # 等待查询编码完成。
    torch.cuda.synchronize(device)
    # 保存单条查询编码耗时，不声称稳定延迟。
    query_seconds = perf_counter() - started
    # 检查运行期间配置与输入没有变化。
    if input_sha != {name: file_sha256(path) for name, path in paths.items()}:
        # 发生并行编辑时不把混合输入声明为通过。
        raise RuntimeError('Inputs or preflight source changed during execution')
    # 缓存位置独立记录，不改变模型语义配置或旧文档向量身份。
    cache_locations = {'hf_home': hub_constants.HF_HOME, 'hf_hub_cache': hub_constants.HF_HUB_CACHE, 'hf_xet_cache': hub_constants.HF_XET_CACHE, 'sentence_transformers_home': os.environ.get('SENTENCE_TRANSFORMERS_HOME')}
    # 返回真实模型小批与长度检查，不包含公开基准效果分数。
    return {'status': 'passed', 'scope': 'real model metadata and small-batch encoding; no corpus cache, retrieval, test split or MIRAGE run', 'profile': profile_name, 'profile_config': profile, 'cache_locations': cache_locations, 'input_sha256': input_sha, 'actual_device': str(parameter.device), 'actual_weight_dtype': str(parameter.dtype), 'actual_dimension': dimension, 'actual_max_seq_length': limit, 'gpu_name': torch.cuda.get_device_name(device), 'gpu_total_bytes': torch.cuda.get_device_properties(device).total_memory, 'gpu_peak_allocated_bytes': torch.cuda.max_memory_allocated(device), 'gpu_peak_reserved_bytes': torch.cuda.max_memory_reserved(device), 'model_load_seconds': load_seconds, 'document_sample_seconds': document_seconds, 'single_query_encode_seconds': query_seconds, 'document_count': len(texts), 'dev_query_count': len(questions), 'document_token_max': max(document_lengths), 'documents_over_limit': sum(length > limit for length in document_lengths), 'query_token_max': max(query_lengths), 'queries_over_limit': sum(length > limit for length in query_lengths), 'sample_document_ids': corpus.iloc[indices]['id'].tolist(), 'sample_query_id': queries.iloc[0]['id'], 'document_vectors': document_check, 'query_vectors': query_check}


# 显式运行时才解析参数和调用模型。
if __name__ == '__main__':
    # 三个路径与配置选项均明确记录在命令中。
    parser = argparse.ArgumentParser(description='Check one frozen embedding profile in your GPU terminal')
    # 配置目录沿用既有入口的--config。
    parser.add_argument('--config', type=Path, required=True)
    # 配套BEIR目录默认当前已准备的NFCorpus。
    parser.add_argument('--data-dir', type=Path, default=ROOT / 'data/external/nfcorpus/prepared/nfcorpus')
    # 本工具可复用于两套固定模型。
    parser.add_argument('--profile', choices=['bge_small', 'qwen3_8b'], required=True)
    # 每次运行显式选择独立结果文件。
    parser.add_argument('--output', type=Path, required=True)
    # 解析用户真实提供的参数。
    args = parser.parse_args()
    # 拒绝覆盖已经保存的预检结果。
    if args.output.exists():
        # 重跑时由用户指定新的文件名。
        raise FileExistsError(args.output)
    # 真实运行失败时自然返回非零状态，终端日志保留完整异常。
    report = run_preflight(args.config, args.data_dir, args.profile)
    # 成功后才保存通过报告。
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # 保存配置、真实设备、向量及长度检查。
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    # 终端只展示关键检查结果，完整配置与指纹保存在JSON中。
    display = {key: report[key] for key in ('status', 'gpu_name', 'actual_device', 'actual_weight_dtype', 'actual_dimension', 'actual_max_seq_length', 'document_count', 'dev_query_count', 'document_token_max', 'documents_over_limit', 'query_token_max', 'queries_over_limit', 'gpu_peak_allocated_bytes', 'gpu_peak_reserved_bytes', 'document_vectors', 'query_vectors')}
    # 告知完整报告的实际保存位置。
    display['report_path'] = str(args.output.resolve())
    # 进度和关键摘要可直接在用户终端查看。
    print(json.dumps(display, ensure_ascii=False, indent=2), flush=True)

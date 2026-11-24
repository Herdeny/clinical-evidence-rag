# 复制构造参数，避免第三方构造器修改原始实验配置。
from copy import deepcopy
# 记录实际采用的配置文件身份。
import hashlib
# 保存真实依赖版本。
from importlib.metadata import version
# 将模型缓存明确限定在项目目录。
from pathlib import Path
# 使用真实CrossEncoder类，不重新实现模型打分。
from sentence_transformers import CrossEncoder
# 显式保留原始logit，并读取实际权重精度。
import torch


# 统一预检与正式运行的模型构造方式。
def build_reranker(profile):
    # 缓存位置来自模块位置，与终端当前目录无关。
    cache_folder = Path(__file__).resolve().parent / 'cache/huggingface/hub'
    # 库内部负责加载模型原有模块及聊天模板。
    return CrossEncoder(
        # 模型名称与固定版本分别传入。
        profile['model_name'],
        # 不自动回退到其他设备。
        device=profile['device'],
        # 固定已核对的模型提交。
        revision=profile['revision'],
        # 正式加载只读取项目内已下载内容。
        local_files_only=profile['local_files_only'],
        # 明确采用项目内缓存。
        cache_folder=str(cache_folder),
        # 沿用库内置实现，无需执行远程Python代码。
        trust_remote_code=False,
        # 最大长度覆盖问题、正文和模板的联合输入。
        max_length=profile['max_length'],
        # 权重精度和注意力实现从配置原样传入。
        model_kwargs=deepcopy(profile['model_kwargs']),
        # 保留各模型适合的填充方向。
        processor_kwargs=deepcopy(profile['processor_kwargs']),
        # 指令由模型模板插入，不在业务代码拼接第二遍。
        prompts=deepcopy(profile['prompts']),
        # BGE无默认指令，Qwen采用显式query指令。
        default_prompt_name=profile['default_prompt_name'],
        # Identity不改变分数，不把logit包装成概率。
        activation_fn=torch.nn.Identity(),
    )


# 把模型的真实运行属性与声明配置一起保存，不执行打分。
def describe_reranker(reranker, *, profile_name, profile, config_path):
    # 读取真实权重，避免把配置声明当成实际设备或精度。
    parameter = next(reranker.parameters())
    # 记录完整配置副本，调用方可以直接放入config.rerank。
    metadata = deepcopy(profile)
    # 将配置名称和文件身份纳入实验记录。
    metadata.update({'profile_name': profile_name, 'profile_file': {'path': str(Path(config_path).resolve()), 'sha256': hashlib.sha256(Path(config_path).read_bytes()).hexdigest()}})
    # 保存实际加载后可以观察到的模型属性。
    metadata.update({'actual_device': str(parameter.device), 'actual_weight_dtype': str(parameter.dtype), 'actual_max_length': reranker.max_seq_length, 'actual_activation': type(reranker.activation_fn).__name__, 'actual_prompts': deepcopy(reranker.prompts), 'actual_default_prompt_name': reranker.default_prompt_name})
    # 设备可显式指定索引；未写索引时只核对设备类型。
    requested_device = torch.device(profile['device'])
    # 读取当前配置要求的真实torch精度。
    requested_dtype = getattr(torch, profile['model_kwargs']['dtype'])
    # 模型设备、精度或长度未按配置生效时不能记录成正常实验。
    if parameter.device.type != requested_device.type or (requested_device.index is not None and parameter.device.index != requested_device.index) or parameter.dtype != requested_dtype or reranker.max_seq_length != profile['max_length']:
        # 直接给出实际值，后续据真实运行判断原因。
        raise ValueError(f'Reranker runtime differs from profile: {metadata}')
    # 原始打分实验须确实使用Identity，指令也须按配置生效。
    if not isinstance(reranker.activation_fn, torch.nn.Identity) or reranker.prompts != profile['prompts'] or reranker.default_prompt_name != profile['default_prompt_name']:
        # 模板或激活不同会改变分数含义。
        raise ValueError('Reranker prompt or activation differs from profile')
    # 分别记录已安装库版本，便于恢复实际模型解释方式。
    metadata['libraries'] = {name: version(name) for name in ('sentence-transformers', 'transformers', 'torch')}
    # 返回可直接写入JSON的字典，不保存模型对象。
    return metadata

# 在同一LangChain接口上集中处理输出精度，供预检和正式入口共用。
from typing import ClassVar
# 只在模型输出的小批矩阵上进行FP32数值运算。
import numpy as np
# 保留原有模型加载、prompt和文档／查询接口。
from langchain_huggingface import HuggingFaceEmbeddings
# 保存最近一次调用的数值摘要，不把运行状态当作模型参数。
from pydantic import PrivateAttr


# 对明确选择此策略的模型，在输出端再次执行FP32归一化。
class Float32L2HuggingFaceEmbeddings(HuggingFaceEmbeddings):
    # 策略版本进入缓存身份；后续改变算法时应使用新版本。
    output_normalization: ClassVar[str] = 'float32_l2_v1'
    # Pydantic私有状态只用于预检记录，不参与初始化参数或缓存身份。
    _last_output_normalization: dict = PrivateAttr(default_factory=dict)

    # 调用方取得副本，防止后续查询覆盖已经保存的文档摘要。
    @property
    # 返回最近一批输出的归一化前后范数。
    def last_output_normalization(self):
        # 不对外暴露内部可变字典。
        return dict(self._last_output_normalization)

    # 父类的embed_documents和embed_query都会调用此接口。
    def _embed(self, texts, encode_kwargs):
        # 复用父类的文本处理、模型推理及列表转换。
        values = super()._embed(texts, encode_kwargs)
        # 每次调用先清空上一批摘要。
        self._last_output_normalization = {}
        # 未要求归一化或输入为空时保留原接口语义。
        if not encode_kwargs.get('normalize_embeddings') or not texts:
            # 不擅自改变未归一化编码任务的输出。
            return values
        # 明确在FP32矩阵上计算，而非仅在保存时转换数据类型。
        vectors = np.asarray(values, dtype=np.float32)
        # 拒绝行数不符、空维度及非有限数值。
        if vectors.ndim != 2 or vectors.shape[0] != len(texts) or not vectors.shape[1] or not np.isfinite(vectors).all():
            # 无效模型输出不能靠归一化掩盖。
            raise ValueError('Invalid embedding output before FP32 L2 normalization')
        # 以FP64记录输入范数，准确展示低精度输出已有的偏差。
        before = np.linalg.norm(vectors.astype(np.float64), axis=1)
        # 实际缩放使用FP32计算，保留每行的轴以便广播。
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        # 零向量或范数溢出没有可靠的归一化结果。
        if not np.isfinite(norms).all() or np.any(norms <= 0):
            # 不用极小分母把异常结果伪装成合法向量。
            raise ValueError('Embedding norms must be finite and positive')
        # 对正文和查询采取相同的FP32输出归一化。
        normalized = vectors / norms
        # 独立检查实际输出范数，保留原先的严格阈值。
        after = np.linalg.norm(normalized.astype(np.float64), axis=1)
        # 归一化后的实际结果仍须满足单位向量约定。
        if not np.allclose(after, 1.0, rtol=1e-3, atol=1e-5):
            # 不以放宽验收标准代替数值修复。
            raise ValueError('FP32 L2 normalization failed')
        # 保存可复核的原始偏差和修复后范围。
        self._last_output_normalization = {'policy': self.output_normalization, 'before_norm_min': float(before.min()), 'before_norm_max': float(before.max()), 'after_norm_min': float(after.min()), 'after_norm_max': float(after.max()), 'output_dtype': str(normalized.dtype)}
        # 保持LangChain原有的普通浮点列表返回接口。
        return normalized.tolist()


# 用同一份完整profile构造模型，避免预检与正式入口各自选择策略。
def build_embedding_model(profile):
    # 旧BGE配置未声明策略，继续使用原生类以复用已有缓存。
    policy = profile.get('output_normalization', 'model_native')
    # 拒绝拼写错误，避免静默回退到另一套数值处理。
    if policy not in ('model_native', 'float32_l2_v1'):
        # 参数错误必须发生在模型初始化之前。
        raise ValueError(f'Unknown output normalization policy: {policy}')
    # 明确的FP32策略要求正文和查询都承诺单位向量。
    if policy == 'float32_l2_v1' and not all(profile[key].get('normalize_embeddings') for key in ('encode_kwargs', 'query_encode_kwargs')):
        # 防止文档和查询采用不同的归一化约定。
        raise ValueError('FP32 L2 policy requires normalized documents and queries')
    # 策略只决定输出适配类，不改变模型规模、权重精度或prompt。
    embedding_class = Float32L2HuggingFaceEmbeddings if policy == 'float32_l2_v1' else HuggingFaceEmbeddings
    # 仍只把原先四项参数传给LangChain，不将项目元数据混入构造器。
    return embedding_class(**{key: profile[key] for key in ('model_name', 'model_kwargs', 'encode_kwargs', 'query_encode_kwargs')})

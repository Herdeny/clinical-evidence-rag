# 下面的文档字符串说明本模块、类或函数的用途和适用边界。
"""Assistant-owned embedding persistence; never loads or calls a model.

The learner owns batch selection and embed_documents calls. Cache identity binds
the actual ordered id/text rows, input snapshot and document encoding settings.
"""

# 导入文件锁接口，防止两个进程同时改写同一份缓存。
import fcntl
# 导入内容指纹工具。
import hashlib
# 读取已安装包的版本号，用于绑定可复现的编码环境。
from importlib.metadata import version
# 导入JSON 编解码工具。
import json
# 导入底层文件同步与原子替换接口。
import os
# 导入路径对象 Path，便于定位脚本、组合目录并读写文件。
from pathlib import Path

# 导入数值数组和内存映射工具。
import numpy as np


# 定义 _json：把对象转成键顺序固定、保留中文的 JSON 字符串，用于稳定计算缓存身份。
def _json(value):
    # 保留中文、固定字典键顺序并拒绝 NaN，让相同身份总能得到相同 JSON 和指纹。
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


# 定义 _file_sha256：分块读取文件并计算 SHA-256，避免为了校验而一次读入大文件。
def _file_sha256(path):
    # 设置摘要计算器：初始化 SHA-256 内容摘要。
    digest = hashlib.sha256()
    # 进入受管理的上下文：按指定读写模式打开文件，并在 with 退出时关闭句柄。
    with Path(path).open('rb') as stream:
        # 每次读取 1 MiB；遇到空字节 b'' 时停止，避免一次读入整个大文件。
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            # 把下一块内容加入同一个摘要计算器。
            digest.update(block)
    # 返回取出已经计算好的十六进制内容指纹，结束本次函数调用。
    return digest.hexdigest()


# 定义 _atomic_json：先写临时清单并同步落盘，再原子替换正式 JSON 文件。
def _atomic_json(path, value):
    # 在正式清单旁生成临时文件名，先写完整内容再替换正式清单。
    temporary = path.with_name(path.name + '.tmp')
    # 进入受管理的上下文：按指定读写模式打开文件，并在 with 退出时关闭句柄。
    with temporary.open('w', encoding='utf-8') as stream:
        # 将本行给出的完整文本或字节写入已打开的文件，保留指定的分行格式。
        stream.write(_json(value) + '\n')
        # 先把 Python 用户态缓冲中的内容交给操作系统。
        stream.flush()
        # 要求操作系统把该文件的数据同步到磁盘；fileno() 提供底层文件描述符。
        os.fsync(stream.fileno())
    # 以原子替换提交新清单，避免读取者看到只写了一半的 JSON。
    os.replace(temporary, path)


# 定义与模型、证据行序绑定的磁盘向量缓存管理器。
class DocumentEmbeddingCache:
    # 下面的文档字符串说明本模块、类或函数的用途和适用边界。
    """One locked cache directory per ordered corpus and encoding identity.

    Use as a context manager. Read completed_rows to resume; write_batch accepts
    only the next contiguous rows. finish publishes a verified read-only mmap.
    """

    # 定义 __init__：检查证据和固定模型配置，计算有序身份并准备缓存路径；不调用模型。
    def __init__(self, evidences, embedding_model, *, evidence_path, cache_dir, dimension=384):
        # 向量维度必须是正整数，不能是小数、布尔值或非正数。
        if type(dimension) is not int or dimension <= 0:
            # 抛出 ValueError 并停止当前操作：向量维度必须是正整数。
            raise ValueError('dimension must be a positive integer')
        # 要求证据表非空且包含 id、text 两列，后续要据此固定向量行映射。
        if len(evidences) == 0 or not {'id', 'text'} <= set(evidences.columns):
            # 抛出 ValueError 并停止当前操作：证据表必须非空并提供 id 与 text。
            raise ValueError('evidences must contain nonempty id/text rows')
        # 重复证据 ID 会使向量到证据的对应关系含混，因此提前拒绝。
        if not evidences['id'].is_unique:
            # 抛出 ValueError 并停止当前操作：证据 ID 不能重复。
            raise ValueError('evidence IDs must be unique')
        # 复制实际模型初始化参数，避免后续处理改动调用者的配置字典。
        model_kwargs = dict(embedding_model.model_kwargs)
        # 模型必须指定固定版本，避免同名模型更新后误用旧向量。
        if not model_kwargs.get('revision'):
            # 抛出 ValueError 并停止当前操作：创建缓存前必须固定模型版本。
            raise ValueError('Pin model_kwargs.revision before creating a document cache')
        # Authentication is not part of the embedding computation or cache key.
        # 检查模型参数中是否有凭据字段，避免将秘密写入缓存清单。
        if {'token', 'use_auth_token', 'api_key', 'password'} & model_kwargs.keys():
            # 抛出 ValueError 并停止当前操作：拒绝把模型凭据写入缓存配置。
            raise ValueError('Do not put credentials into persisted model_kwargs')
        # 设置config：字典，保存编码模型或检索实现的名称、创建模型时的实际参数、文档编码使用的参数、实际编码类的完整 Python 名称、影响复现的依赖版本等信息。
        config = {
            # 写入字段 model_name（编码模型或检索实现的名称）。
            'model_name': embedding_model.model_name,
            # 写入字段 model_kwargs（创建模型时的实际参数）。
            'model_kwargs': model_kwargs,
            # 写入字段 encode_kwargs（文档编码使用的参数）。
            'encode_kwargs': dict(embedding_model.encode_kwargs),
            # 写入字段 embedding_interface（实际编码类的完整 Python 名称）。
            'embedding_interface': type(embedding_model).__module__ + '.' + type(embedding_model).__qualname__,
            # 写入字段 packages（影响复现的依赖版本）。
            'packages': {name: version(name) for name in ['langchain-huggingface', 'sentence-transformers', 'torch', 'numpy']},
            # 写入字段 document_input（文档向量的输入接口说明）。
            'document_input': 'text via HuggingFaceEmbeddings.embed_documents',
        # 结束上方的字典或集合。
        }
        # 设置有序证据内容摘要：初始化 SHA-256 内容摘要。
        row_digest = hashlib.sha256()
        # 按证据实际行顺序读取 ID 和正文；不把 DataFrame 的行标签混入位置映射。
        for identifier, text in evidences[['id', 'text']].itertuples(index=False, name=None):
            # 每条 ID 和正文都必须是字符串；缺失或其他类型会中止建立缓存身份。
            if not isinstance(identifier, str) or not isinstance(text, str):
                # 抛出 ValueError 并停止当前操作：证据 ID 和正文必须都是字符串。
                raise ValueError('Each evidence id and text must be a string')
            # 依次把每行 ID 和正文加入摘要，行内容或行顺序改变都会改变指纹。
            row_digest.update((_json([identifier, text]) + '\n').encode('utf-8'))
        # 记住矩阵的行数和列数；每行必须始终对应一条证据。
        self.total_rows, self.dimension = len(evidences), dimension
        # 建立仅包含可序列化值的身份字典，绑定文件、行序、模型和编码配置。
        self.identity = json.loads(_json({
            # 写入字段 schema（当前清单结构的版本号）。
            'schema': 1,
            # 写入字段 evidence_sha256（输入证据文件的字节指纹）。
            'evidence_sha256': _file_sha256(evidence_path),
            # 写入字段 ordered_id_text_sha256（实际证据 ID、正文和行序的联合指纹）。
            'ordered_id_text_sha256': row_digest.hexdigest(),
            # 写入字段 rows（向量矩阵的证据行数）；字段 dimension（每行向量的维度）；字段 dtype（数组元素的数据类型）。
            'rows': self.total_rows, 'dimension': dimension, 'dtype': 'float32',
            # 写入字段 document_config（决定文档向量内容的模型和编码配置）。
            'document_config': config,
        # 结束上方的字典或集合。
        }))
        # 对稳定序列化后的身份计算 SHA-256，作为缓存目录名。
        self.fingerprint = hashlib.sha256(_json(self.identity).encode()).hexdigest()
        # 让不同数据或模型配置使用不同目录，避免相互覆盖。
        self.directory = Path(cache_dir) / self.fingerprint
        # 设置缓存状态和指纹清单的位置。
        self.manifest_path = self.directory / 'manifest.json'
        # 设置全部编码完成后正式向量矩阵的位置。
        self.array_path = self.directory / 'vectors.npy'
        # 设置可断点续写的未完成矩阵位置，和正式文件明确区分。
        self.partial_path = self.directory / 'vectors.incomplete.npy'
        # 文件锁句柄和写入映射先置空，进入 with 后再打开资源。
        self._lock = self._writer = None
        # 缓存清单尚未读取，用 None 标记未初始化。
        self._manifest = None
        # 初始化本次进入缓存时的已完成行数，之后用于运行摘要。
        self._initial_completed_rows = 0
        # 初始化本次进入时是否命中完整缓存，避免新建完成后误报为缓存命中。
        self._initial_complete = False

    # 定义 __enter__：进入 with 时加排他锁，并创建、恢复或校验当前缓存。
    def __enter__(self):
        # 创建当前缓存目录及必要父目录；已有目录可以复用。
        self.directory.mkdir(parents=True, exist_ok=True)
        # 打开锁文件句柄；文件可以保留，真正的排他性由操作系统锁管理。
        self._lock = (self.directory / '.lock').open('a+b')
        # 开始需要异常处理的操作；失败时转入对应 except 分支。
        try:
            # 申请非阻塞排他锁；若已有人写入，立即报错而不是并发破坏缓存。
            fcntl.flock(self._lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        # 处理锁已被其他写入者占用的情况。
        except BlockingIOError:
            # 关闭锁文件句柄；同时释放与该句柄关联的系统资源。
            self._lock.close()
            # 清除句柄引用，标记当前对象已不持有文件锁。
            self._lock = None
            # 抛出 RuntimeError 并停止当前操作：另一写入者已占用这份缓存。
            raise RuntimeError('This embedding cache is already in use') from None
        # 开始需要异常处理的操作；失败时转入对应 except 分支。
        try:
            # 若已有清单，优先核对并恢复旧缓存，而不是重新编码。
            if self.manifest_path.exists():
                # 读取磁盘清单，取得缓存身份、状态和已完成行数。
                self._manifest = json.loads(self.manifest_path.read_text())
                # 要求磁盘身份与当前证据及模型完全一致，避免误用不对应的向量。
                if self._manifest.get('identity') != self.identity:
                    # 抛出 ValueError 并停止当前操作：磁盘缓存身份与当前输入不一致。
                    raise ValueError('Cache manifest does not match the requested identity')
                # 读取上次成功提交的行数；未提交的写入不能算作已完成。
                completed = self._manifest.get('completed_rows')
                # 检查断点是合法行号，并且没有越过当前语料末尾。
                if type(completed) is not int or not 0 <= completed <= self.total_rows:
                    # 抛出 ValueError 并停止当前操作：磁盘记录的已完成行数不合法。
                    raise ValueError('Invalid cache checkpoint')
                # 发现上次在发布完整文件时中断，先按已记录指纹恢复发布。
                if self._manifest.get('status') == 'finalizing':
                    # 校验正式或临时向量文件，并把发布状态恢复为完整。
                    self._recover_publication()
                # 完整缓存走读取路径，不再进行文档编码或覆写。
                if self.is_complete:
                    # 完成状态必须同时满足所有行都已经提交。
                    if completed != self.total_rows:
                        # 抛出 ValueError 并停止当前操作：完成状态与已完成行数互相矛盾。
                        raise ValueError('Complete cache has an incomplete checkpoint')
                    # 复核正式向量文件的形状、类型和完整字节指纹。
                    self._checked_array(self.array_path, verify_digest=True)
                # 构建中状态允许从最后提交的行数继续写入。
                elif self._manifest.get('status') == 'building':
                    # 检查正式文件是否与当前状态冲突，避免把不明来源的向量覆盖掉。
                    if self.array_path.exists():
                        # 抛出 ValueError 并停止当前操作：发现与当前清单状态不符的正式向量文件。
                        raise ValueError('Unexpected published array without a completion record')
                    # 若未完成文件缺失，判断是否仍能从零安全重建。
                    if not self.partial_path.exists():
                        # 已有非零断点却丢失矩阵时不能假装从断点恢复。
                        if completed:
                            # 抛出 ValueError 并停止当前操作：已有断点却缺失部分矩阵，不能伪装恢复。
                            raise ValueError('Partial array is missing for a nonempty checkpoint')
                        # 创建与当前证据数量、维度一致的未完成矩阵文件。
                        self._create_partial()
                    # 核对未完成文件的矩阵形状和类型；未写完区域不作为可用向量。
                    self._checked_array(self.partial_path)
                    # 以可读写内存映射打开已有部分矩阵，保留之前成功提交的行。
                    self._writer = np.lib.format.open_memmap(self.partial_path, mode='r+')
                # 前面的条件都不满足时，执行这一分支。
                else:
                    # 抛出 ValueError 并停止当前操作：缓存状态值无法识别。
                    raise ValueError('Unknown cache status')
            # 前面的条件都不满足时，执行这一分支。
            else:
                # 检查正式文件是否与当前状态冲突，避免把不明来源的向量覆盖掉。
                if self.array_path.exists():
                    # 抛出 ValueError 并停止当前操作：正式矩阵缺少清单，拒绝覆盖。
                    raise ValueError('Published array has no manifest; refusing to overwrite it')
                # 创建与当前证据数量、维度一致的未完成矩阵文件。
                self._create_partial()
                # 创建初始清单：身份已固定，状态为构建中，已完成行数为零。
                self._manifest = {'identity': self.identity, 'status': 'building', 'completed_rows': 0}
                # 原子保存当前清单，使断点和状态以完整 JSON 提交。
                _atomic_json(self.manifest_path, self._manifest)
            # 记录本次打开时的断点，供结果摘要区分首次编码和续写。
            self._initial_completed_rows = self.completed_rows
            # 记录本次打开时是否命中完整缓存；完成新编码不会回改这个事实。
            self._initial_complete = self.is_complete
            # 把当前缓存对象交给 with 后面的 as cache 使用。
            return self
        # 捕获这里指定的异常，并执行下方的恢复、隔离或报告逻辑。
        except Exception:
            # 释放写入映射和文件锁，已保存到磁盘的内容继续保留。
            self.close()
            # 继续抛出当前异常，保留最初失败原因。
            raise

    # 定义 _create_partial：创建指定形状的 float32 未完成向量文件并同步到磁盘。
    def _create_partial(self):
        # 创建磁盘上的 .npy 写入映射，不先在内存中收集整个向量矩阵。
        self._writer = np.lib.format.open_memmap(
            # 使用未完成文件名，并按 float32 创建新矩阵；w+ 用于创建或重建文件。
            self.partial_path, mode='w+', dtype=np.float32,
            # 矩阵形状固定为证据总数乘向量维度。
            shape=(self.total_rows, self.dimension),
        # 结束上方的函数调用、元组或分组表达式。
        )
        # 先把当前写入同步到磁盘，再允许提交进度或正式发布。
        self._sync_writer()

    # 定义 _require_open：检查缓存是否已在 with 上下文中打开。
    def _require_open(self):
        # 要求缓存已进入 with 并完成初始化，防止在关闭状态读写。
        if self._lock is None or self._manifest is None:
            # 抛出 RuntimeError 并停止当前操作：缓存尚未在 with 中正确打开。
            raise RuntimeError('Use DocumentEmbeddingCache inside a with block')

    # 将下方方法暴露为只读属性，读取时不需要加调用括号。
    @property
    # 定义 completed_rows：读取已成功保存的连续行数，作为下一批编码的起点。
    def completed_rows(self):
        # 先验证当前对象持有有效的缓存上下文。
        self._require_open()
        # 返回已经成功提交的连续行数。
        return self._manifest['completed_rows']

    # 将下方方法暴露为只读属性，读取时不需要加调用括号。
    @property
    # 定义 is_complete：读取清单状态，判断缓存是否已经完整发布。
    def is_complete(self):
        # 只有清单存在且明确标记 complete，才认定为完整缓存。
        return self._manifest is not None and self._manifest.get('status') == 'complete'

    # 将下方方法暴露为只读属性，读取时不需要加调用括号。
    @property
    # 定义 info：生成可写入运行摘要的缓存元数据，保留进入时的命中与恢复状态。
    def info(self):
        # 下面的文档字符串说明本模块、类或函数的用途和适用边界。
        """JSON-ready facts; cache_hit describes entry, not the post-build state."""
        # 先验证当前对象持有有效的缓存上下文。
        self._require_open()
        # 返回字典，保存这一份缓存的唯一身份指纹、缓存清单的完整位置、完整向量文件的位置、进入时是否已有完整缓存、进入时已经提交的行数等信息，结束本次函数调用。
        return {
            # 写入字段 fingerprint（这一份缓存的唯一身份指纹）。
            'fingerprint': self.fingerprint,
            # 写入字段 manifest_path（缓存清单的完整位置）。
            'manifest_path': str(self.manifest_path.resolve()),
            # 写入字段 vectors_path（完整向量文件的位置）。
            'vectors_path': str(self.array_path.resolve()),
            # 写入字段 cache_hit（进入时是否已有完整缓存）。
            'cache_hit': self._initial_complete,
            # 写入字段 initial_completed_rows（进入时已经提交的行数）。
            'initial_completed_rows': self._initial_completed_rows,
            # 写入字段 rows（向量矩阵的证据行数）；字段 dimension（每行向量的维度）；字段 dtype（数组元素的数据类型）。
            'rows': self.total_rows, 'dimension': self.dimension, 'dtype': 'float32',
            # 写入字段 status（当前处理或完成状态）。
            'status': self._manifest['status'],
        # 结束上方的字典或集合。
        }

    # 定义 _sync_writer：把内存映射的改动及文件缓冲同步到磁盘。
    def _sync_writer(self):
        # 将可写内存映射中修改过的页同步到文件。
        self._writer.flush()
        # 打开未完成文件的只读句柄，以便对它执行底层同步。
        with self.partial_path.open('rb') as stream:
            # 要求操作系统把该文件的数据同步到磁盘；fileno() 提供底层文件描述符。
            os.fsync(stream.fileno())

    # 定义 _checked_array：检查向量文件形状和数据类型，按需复核文件指纹。
    def _checked_array(self, path, *, verify_digest=False):
        # 按只读内存映射读取数值矩阵，并禁止反序列化 pickle 对象。
        array = np.load(path, mmap_mode='r', allow_pickle=False)
        # 核对向量数量、维度和 float32 类型，防止矩阵与证据表不对应。
        if array.shape != (self.total_rows, self.dimension) or array.dtype != np.dtype('float32'):
            # 抛出 ValueError 并停止当前操作：缓存矩阵的形状或类型不正确。
            raise ValueError('Cached array shape or dtype mismatch')
        # 需要完整校验时，重新计算文件指纹并与清单比较，检测损坏或篡改。
        if verify_digest and _file_sha256(path) != self._manifest.get('array_sha256'):
            # 抛出 ValueError 并停止当前操作：缓存文件内容指纹不匹配。
            raise ValueError('Cached array SHA-256 mismatch')
        # 返回已通过校验的只读内存映射，供现有 NumPy 检索使用。
        return array

    # 定义 write_batch：校验并保存下一段连续向量，落盘成功后更新断点。
    def write_batch(self, start, vectors):
        # 下面的文档字符串说明本模块、类或函数的用途和适用边界。
        """Persist model outputs for the next contiguous rows and checkpoint."""
        # 先验证当前对象持有有效的缓存上下文。
        self._require_open()
        # 完整缓存走读取路径，不再进行文档编码或覆写。
        if self.is_complete:
            # 抛出 RuntimeError 并停止当前操作：完整缓存只允许读取，不能继续写入。
            raise RuntimeError('Cache is complete; load it instead of writing')
        # 本批起点必须恰好等于断点，禁止跳行或重复覆盖已提交向量。
        if type(start) is not int or start != self.completed_rows:
            # 抛出 ValueError 并停止当前操作：批次起点必须等于当前断点。
            raise ValueError('Batch start must equal completed_rows')
        # 将这一小批模型输出转成 float32 数组，不复制整个语料的矩阵。
        batch = np.asarray(vectors, dtype=np.float32)
        # 每批必须是非空二维矩阵，并且列数等于约定的向量维度。
        if batch.ndim != 2 or batch.shape[1] != self.dimension or not len(batch):
            # 抛出 ValueError 并停止当前操作：批次必须非空且维度正确。
            raise ValueError('Expected a nonempty batch with the configured dimension')
        # 计算本批的右开结束行号。
        end = start + len(batch)
        # 拒绝越界写入以及包含 NaN 或无穷值的模型输出。
        if end > self.total_rows or not np.isfinite(batch).all():
            # 抛出 ValueError 并停止当前操作：批次越界或包含非有限数值。
            raise ValueError('Batch exceeds corpus bounds or contains non-finite values')
        # 若本次文档编码承诺已归一化，就额外核对每行 L2 范数。
        if self.identity['document_config']['encode_kwargs'].get('normalize_embeddings'):
            # 按行计算 L2 范数；axis=1 表示沿每个向量的各维度计算。
            norms = np.linalg.norm(batch, axis=1)
            # 允许小量浮点误差，但拒绝明显没有归一化的输出；不自动修改模型结果。
            if not np.allclose(norms, 1.0, rtol=1e-3, atol=1e-5):
                # 抛出 ValueError 并停止当前操作：模型输出没有满足归一化约定，辅助层不会偷偷修改。
                raise ValueError('Expected L2-normalized vectors; model output was not modified')
        # 把本批向量写到与原证据行号相同的位置。
        self._writer[start:end] = batch
        # 先把当前写入同步到磁盘，再允许提交进度或正式发布。
        self._sync_writer()
        # Checkpoint follows data flush; uncommitted rows can be overwritten on
        # resume. A partial file is never treated as a completed cache.
        # 仅在向量成功落盘后，推进已完成行数。
        self._manifest['completed_rows'] = end
        # 原子保存当前清单，使断点和状态以完整 JSON 提交。
        _atomic_json(self.manifest_path, self._manifest)

    # 定义 finish：仅在全部行已保存后发布完整缓存，并返回只读矩阵。
    def finish(self):
        # 下面的文档字符串说明本模块、类或函数的用途和适用边界。
        """Publish only after every row was committed; return a read-only mmap."""
        # 先验证当前对象持有有效的缓存上下文。
        self._require_open()
        # 完整缓存走读取路径，不再进行文档编码或覆写。
        if self.is_complete:
            # 复用完整文件的只读加载与校验逻辑。
            return self.load()
        # 只有所有证据行都已提交，才允许发布完整矩阵。
        if self.completed_rows != self.total_rows:
            # 抛出 ValueError 并停止当前操作：所有行完成前不能发布完整缓存。
            raise ValueError('Cannot finalize an incomplete document cache')
        # 先把当前写入同步到磁盘，再允许提交进度或正式发布。
        self._sync_writer()
        # 释放当前可写映射引用；已提交数据仍保留在磁盘。
        self._writer = None
        # 先保存待发布文件的指纹与 finalizing 状态，使改名中断也能恢复。
        self._manifest.update(status='finalizing', array_sha256=_file_sha256(self.partial_path))
        # 原子保存当前清单，使断点和状态以完整 JSON 提交。
        _atomic_json(self.manifest_path, self._manifest)
        # 校验正式或临时向量文件，并把发布状态恢复为完整。
        self._recover_publication()
        # 复用完整文件的只读加载与校验逻辑。
        return self.load()

    # 定义 _recover_publication：恢复向量文件发布中断，校验后将清单状态提交为完成。
    def _recover_publication(self):
        # 当 self._manifest['completed_rows'] != self.total_rows 成立时，执行下面的分支。
        if self._manifest['completed_rows'] != self.total_rows:
            # 抛出 ValueError 并停止当前操作：行数尚未完成，不能恢复为已发布状态。
            raise ValueError('Cannot recover publication with incomplete rows')
        # 根据上次是否已经完成改名，选择正式文件或未完成文件作为恢复对象。
        candidate = self.array_path if self.array_path.exists() else self.partial_path
        # 恢复发布前按清单核对候选文件的形状、类型和完整指纹。
        self._checked_array(candidate, verify_digest=True)
        # 如果还在未完成文件名下，就执行正式发布改名。
        if candidate == self.partial_path:
            # 将已校验的完整矩阵原子改名为正式 vectors.npy。
            os.replace(self.partial_path, self.array_path)
        # 文件发布成功后，最后把清单标记为完整。
        self._manifest['status'] = 'complete'
        # 原子保存当前清单，使断点和状态以完整 JSON 提交。
        _atomic_json(self.manifest_path, self._manifest)

    # 定义 load：读取完整且通过校验的向量文件，返回只读内存映射。
    def load(self):
        # 先验证当前对象持有有效的缓存上下文。
        self._require_open()
        # 读取完整矩阵前先拒绝仍在构建中的缓存。
        if not self.is_complete:
            # 抛出 ValueError 并停止当前操作：不能把半成品读作完整矩阵。
            raise ValueError('Partial cache cannot be loaded as a complete matrix')
        # 返回形状、类型和文件指纹均正确的只读矩阵。
        return self._checked_array(self.array_path, verify_digest=True)

    # 定义 close：释放可写映射和排他锁，保留已经保存的断点。
    def close(self):
        # 释放当前可写映射引用；已提交数据仍保留在磁盘。
        self._writer = None
        # 仅在当前对象持有锁句柄时执行解锁和关闭。
        if self._lock is not None:
            # 显式释放系统排他锁，让后续进程能够打开同一缓存。
            fcntl.flock(self._lock.fileno(), fcntl.LOCK_UN)
            # 关闭锁文件句柄；同时释放与该句柄关联的系统资源。
            self._lock.close()
            # 清除句柄引用，标记当前对象已不持有文件锁。
            self._lock = None

    # 定义 __exit__：离开 with 时释放资源；不吞掉调用者遇到的异常。
    def __exit__(self, exc_type, exc, traceback):
        # 释放写入映射和文件锁，已保存到磁盘的内容继续保留。
        self.close()

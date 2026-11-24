# 用微型BEIR输入验证公开入口，真实检索和保存只处理临时数据。
import argparse
# 执行实际CLI参数块，避免调用正式main。
import ast
# 捕获进度和结果路径输出。
from contextlib import redirect_stderr, redirect_stdout
# 为捕获输出提供内存缓冲。
from io import StringIO
# 按用户main的实际签名读取CLI传参。
import inspect
# 创建JSONL原始输入。
import json
# 处理临时输入与输出路径。
from pathlib import Path
# 自动清理微型语料和缓存。
import tempfile
# 沿用项目测试框架。
import unittest
# 替换真实模型并统计索引构建次数。
from unittest.mock import Mock, create_autospec, patch
# 使用实际安装类的API规格，避免假模型误报合法的新方法名。
from sentence_transformers import SentenceTransformer
# 只构造无权重Pooling模块验证真实维度API，不加载预训练模型。
from sentence_transformers.models import Pooling
# 生成384维单位向量，不使用GPU。
import numpy as np
# 只导入实际入口，导入本身不得启动基准。
import run_benchmark_eval as entry

# 保留不同方法实际到达的阶段，用于解释共享阻断。
OBSERVATIONS = []
# 定位正式源文件，仅用于CLI参数块的语法读取。
ENTRY_PATH = Path(entry.__file__).resolve()
# 静态配置属于版本管理的输入，临时运行目录要提供同一份内容。
PROFILE_PATH = ENTRY_PATH.parent / 'configs/embedding_profiles.json'


# 提供与LangChain封装相同的必要属性，不加载任何权重。
class SyntheticEmbeddings:
    # 保留入口实际传入的模型参数。
    def __init__(self, **kwargs):
        # 标识进入缓存身份，但不下载模型。
        self.model_name = kwargs["model_name"]
        # 设备字符串只是配置，本假模型完全在CPU构造数组。
        self.model_kwargs = kwargs["model_kwargs"]
        # 文档编码参数进入真实缓存身份。
        self.encode_kwargs = kwargs["encode_kwargs"]
        # 查询参数保持入口传入的内容。
        self.query_encode_kwargs = kwargs["query_encode_kwargs"]
        # 两套假模型分别使用实际配置对应的维度，不加载任何权重。
        self.dimension = 4096 if self.model_name == 'Qwen/Qwen3-Embedding-8B' else 384
        # 原BGE没有分词器覆盖配置，Qwen则应实际设置8192上限。
        length = self.model_kwargs.get('processor_kwargs', {}).get('model_max_length', 512)
        # 依据当前安装类生成严格规格，不再凭记忆手写客户端方法名。
        self._client = create_autospec(SentenceTransformer, instance=True, spec_set=True)
        # max_seq_length是实际类公开的属性。
        self._client.max_seq_length = length
        # 5.7.0推荐get_embedding_dimension，旧名称已弃用。
        self._client.get_embedding_dimension.return_value = self.dimension
        # 记录文档实际编码次数。
        self.document_calls = []
        # 记录查询编码，核对复用文档缓存后查询仍然执行。
        self.query_calls = []
    # 根据虚构文档中的主题选择单位向量。
    def embed_documents(self, texts):
        # 复制输入，便于检查标题和正文是否被使用。
        self.document_calls.append(list(texts))
        # 仅分配当前四行和对应维度，避免4096乘4096的大型合成矩阵。
        vectors = np.zeros((len(texts), self.dimension), dtype=np.float32)
        # 按正文主题为每行设置不同的单位向量。
        for row, text in enumerate(texts):
            # 每个虚构主题对应一个固定列号。
            column = next(index for index, word in enumerate(('alpha', 'beta', 'gamma', 'delta')) if word in text.lower())
            # 单位值同时保证输出已经归一化。
            vectors[row, column] = 1.0
        # 保持实际嵌入接口的浮点列表结构。
        return vectors.tolist()
    # 原始查询只匹配第一或第二个虚构主题。
    def embed_query(self, query):
        # 记录传入的原始查询，不在假模型中改写它。
        self.query_calls.append(query)
        # 只创建一条对应维度的向量。
        vector = np.zeros(self.dimension, dtype=np.float32)
        # 第一和第二条虚构查询匹配对应主题。
        vector[0 if 'alpha' in query.lower() else 1] = 1.0
        # 返回实际接口使用的一维浮点列表。
        return vector.tolist()


# 在指定目录构建完整微型BEIR输入。
def write_fixture(data_dir):
    # 创建标准标签目录。
    (data_dir / "qrels").mkdir(parents=True)
    # 四篇虚构文档足够执行真实小型BM25与向量检索。
    corpus = [{"_id": identifier, "title": f"{word} title", "text": f"{word} evidence for this topic"} for identifier, word in zip(("A", "B", "C", "D"), ("alpha", "beta", "gamma", "delta"))]
    # 第三条查询不属于dev，读取器应筛除。
    queries = [{"_id": "q1", "text": "alpha question"}, {"_id": "q2", "text": "beta question"}, {"_id": "other", "text": "Unused query"}]
    # 保存原始容器。
    for name, rows in (("corpus", corpus), ("queries", queries)):
        # 每行一条标准记录。
        (data_dir / f"{name}.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    # 只提供当前开发划分，其他划分不参与执行。
    (data_dir / "qrels/dev.tsv").write_text("query-id\tcorpus-id\tscore\nq1\tA\t2\nq2\tB\t1\n", encoding="utf-8")


# 验证主函数、缓存身份和CLI参数，不消耗真实基准。
class BenchmarkEntryTests(unittest.TestCase):
    # 每个测试单独创建数据、缓存和输出。
    def setUp(self):
        # 自动清理合成输入和结果。
        temporary = tempfile.TemporaryDirectory(prefix="beir-entry-check-")
        # 即使失败也清理临时数据。
        self.addCleanup(temporary.cleanup)
        # 独立工作根目录。
        self.root = Path(temporary.name)
        # 目录故意不叫nfcorpus，用于检查通用身份。
        self.data_dir = self.root / "another_beir_dataset"
        # 创建真实可读取的微型输入。
        write_fixture(self.data_dir)
        # 入口按脚本目录读取配置，所以临时目录也提供配置目录。
        (self.root / 'configs').mkdir()
        # 复制受版本管理的真实配置，不在测试中偷偷补齐用户字段。
        (self.root / 'configs/embedding_profiles.json').write_bytes(PROFILE_PATH.read_bytes())
        # 保留所有假模型，检查文档编码复用。
        self.models = []
        # 模型工厂只产生本地数组。
        def factory(**kwargs):
            # 使用入口实际传入的参数。
            model = SyntheticEmbeddings(**kwargs)
            # 保存实例以便核对文档调用次数。
            self.models.append(model)
            # 返回与现有接口一致的假模型。
            return model
        # 只替换真实权重加载，缓存和检索仍使用真实实现。
        self.model = self.start_patch("HuggingFaceEmbeddings", side_effect=factory)
        # 保留真实分批编码缓存，并观察实际调用路径。
        self.prepare = self.start_patch("prepare_document_embeddings", wraps=entry.prepare_document_embeddings)
        # 保留真实小语料BM25构建。
        self.build = self.start_patch("build_bm25", wraps=entry.build_bm25)
        # 观察真实评分调用，原始查询由已验收函数处理。
        self.evaluate = self.start_patch("evaluate_beir_retrieval", wraps=entry.evaluate_beir_retrieval)
        # 保留真实保存检查，不能补齐用户缺失配置。
        self.save = self.start_patch("save_beir_results", wraps=entry.save_beir_results)
        # 重定向用户main按__file__计算的结果根目录。
        self.start_patch("__file__", new=str(self.root / "run_benchmark_eval.py"))

    # 创建可自动恢复的入口命名空间替换。
    def start_patch(self, name, **kwargs):
        # 作用于用户入口实际引用的对象。
        patcher = patch.object(entry, name, **kwargs)
        # 启动替换并保留其计数对象。
        value = patcher.start()
        # 用例结束时恢复原对象。
        self.addCleanup(patcher.stop)
        # 返回实际包装对象。
        return value

    # 执行实际主函数，记录到达保存时的配置与资源初始化次数。
    def invoke(self, method, run_name, profile=None):
        # 使用用户保存的参数名，避免仅因名称不同判为功能错误。
        parameters = inspect.signature(entry.main).parameters
        # 公共角色通过关键字绑定，使功能测试能够定位函数内部问题。
        arguments = dict(method=method, data_dir=self.data_dir, split='dev', cache_dir=self.root / 'cache', run_name=run_name)
        # 若用户添加了配置目录参数，功能测试提供真实临时目录；另有专门测试检查旧接口兼容。
        if 'config_dir' in parameters:
            # 配置目录只包含本仓库同一份静态JSON。
            arguments['config_dir'] = self.root / 'configs'
        # 显式选择模型时读取实际签名支持的配置名称参数。
        if profile is not None:
            # 两种名称都表达同一个角色，不强制用户为命名重写核心。
            parameter = 'config_embedding_model' if 'config_embedding_model' in parameters else 'embedding_profile'
            # 真实传入所选名称，不补丁替换用户的选择逻辑。
            arguments[parameter] = profile
        # 捕获临时进度，保持测试结果简洁。
        try:
            # 不改变检索、评分或保存逻辑。
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                # 全部路径只指向临时目录。
                return entry.main(**arguments)
        # 失败时仍保存真实执行到的位置，不吞掉异常。
        finally:
            # 只记录用户实际传给保存函数的配置。
            config = self.save.call_args.kwargs["config"] if self.save.call_args else {}
            # 缓存输入如果执行过则保留实际路径。
            cache_input = str(self.prepare.call_args.kwargs["evidence_path"]) if self.prepare.call_args else None
            # 观察只用于诊断，不修改用户配置。
            OBSERVATIONS.append({"method": method, "model_calls": self.model.call_count, "prepare_calls": self.prepare.call_count, "bm25_build_calls": self.build.call_count, "evaluate_calls": self.evaluate.call_count, "save_calls": self.save.call_count, "cache_evidence_path": cache_input, "config": config})

    # 统一检查主函数实际生成的三份文件与运行身份。
    def assert_summary(self, summary, method):
        # 数据规模来自微型语料而非硬编码真实基准。
        self.assertEqual((summary["document_count"], summary["query_count"]), (4, 2))
        # 摘要方法与实际分支一致。
        self.assertEqual(summary["retrieval_method"], method)
        # 数据集名称随传入目录变化。
        self.assertEqual(summary["dataset_name"], self.data_dir.name)
        # 声明的是原查询协议，不是CT模板。
        self.assertEqual(summary["config"]["query_template"], "{query}")
        # 实际标题拼接规则需要记录。
        self.assertIn("corpus_text", summary["config"])
        # 运行预算进入配置。
        self.assertEqual(list(summary["config"]["ks"]), [10, 100])
        # 三类产物必须实际落盘。
        self.assertTrue(all(Path(path).is_file() for path in summary["files"].values()))

    # BM25模式不创建模型或向量缓存。
    def test_bm25_entry_builds_once_without_model(self):
        # 仅对四篇临时文档执行真实BM25。
        summary = self.invoke("bm25", "tiny_bm25")
        # 检查实际身份和文件。
        self.assert_summary(summary, "bm25")
        # 模型与向量编码不应初始化。
        self.assertEqual((self.model.call_count, self.prepare.call_count, self.build.call_count), (0, 0, 1))

    # Dense使用当前corpus路径，并在第二次运行复用向量。
    def test_dense_entry_uses_current_corpus_and_reuses_cache(self):
        # 第一次只编码四篇虚构文档。
        summary = self.invoke("dense", "tiny_dense_first")
        # 先检查完整导出。
        self.assert_summary(summary, "dense")
        # 缓存身份必须绑定当前原始corpus。
        self.assertEqual(self.prepare.call_args.kwargs["evidence_path"], self.data_dir / "corpus.jsonl")
        # 同一个语料再次运行，使用另一个结果名。
        second = self.invoke("dense", "tiny_dense_second")
        # 第二次结果仍应正常保存。
        self.assert_summary(second, "dense")
        # 第二个模型实例不应重新编码任何文档。
        self.assertEqual([len(model.document_calls) for model in self.models], [1, 0])
        # Dense不构建BM25索引。
        self.assertEqual(self.build.call_count, 0)

    # RRF两路预算与实际记录必须一致。
    def test_rrf_entry_builds_each_index_once(self):
        # 使用真实融合及两路临时检索。
        summary = self.invoke("rrf", "tiny_rrf")
        # 核对完整输出。
        self.assert_summary(summary, "rrf")
        # 两路资源各初始化一次。
        self.assertEqual((self.model.call_count, self.prepare.call_count, self.build.call_count), (1, 1, 1))
        # 公开基准候选预算沿用预先固定值。
        self.assertEqual(summary["config"]["rrf"], {"candidate_k": 100, "rrf_constant": 60})

    # 无效方法应在读取或索引构建之前拒绝。
    def test_invalid_method_rejected_before_loading(self):
        # 哨兵能发现参数检查是否发生得过晚。
        with patch.object(entry, "load_beir_dataset", side_effect=AssertionError("invalid method reached loader")):
            # main自身应明确拒绝无效方法。
            with self.assertRaises(ValueError):
                # 本次不访问任何文件或模型。
                self.invoke('unknown', 'invalid')

    # 执行用户实际CLI代码块，唯一替换为不会运行资源的main。
    def cli_arguments(self, arguments):
        # 读取实际入口语法树。
        tree = ast.parse(ENTRY_PATH.read_text(encoding="utf-8"))
        # 找到标准入口守卫的条件。
        guard = ast.dump(ast.parse('__name__ == "__main__"', mode="eval").body)
        # 不把函数定义或导入代码重新执行。
        block = next(node for node in tree.body if isinstance(node, ast.If) and ast.dump(node.test) == guard)
        # 仅编译当前真实CLI块。
        module = ast.fix_missing_locations(ast.Module(body=block.body, type_ignores=[]))
        # 继承实际需要的库，但阻止main访问真实数据。
        namespace = {**vars(entry), "__file__": str(ENTRY_PATH), "main": Mock(return_value={"metrics": {}})}
        # 使用标准库argparse处理真实参数声明。
        with patch("sys.argv", [str(ENTRY_PATH), *arguments]), redirect_stdout(StringIO()):
            # 只执行CLI参数解析和对假main的调用。
            exec(compile(module, str(ENTRY_PATH), "exec"), namespace)
        # 接受用户实际参数顺序，通过签名绑定识别每个角色。
        args, kwargs = namespace["main"].call_args
        # 返回实际传入main的参数。
        return inspect.signature(entry.main).bind(*args, **kwargs).arguments

    # 无参数运行应定位到已准备的开发数据并默认BM25。
    def test_cli_defaults_point_to_bm25_dev(self):
        # 不执行任何真实索引或模型。
        arguments = self.cli_arguments([])
        # 初次真实运行优先CPU BM25。
        self.assertEqual(arguments["method"], "bm25")
        # 默认划分必须是存在的dev。
        self.assertEqual(arguments["split"], "dev")
        # 定位到包含corpus和qrels的实际BEIR目录。
        self.assertEqual(arguments["data_dir"], ENTRY_PATH.parent / "data/external/nfcorpus/prepared/nfcorpus")
        # BM25默认名允许保留原规则或统一带默认配置标签，不把命名偏好当成功能故障。
        self.assertIn(arguments['run_name'], ('nfcorpus_bm25_dev', 'nfcorpus_bm25_bge_small_dev'))

    # 显式参数和默认结果名不能被硬编码数据集身份覆盖。
    def test_cli_explicit_paths_and_generated_run_name(self):
        # 使用一个虚构的可配置路径。
        cache = self.root / "alternate_cache"
        # 指定方法、目录和划分，但让结果名前缀自动生成。
        arguments = self.cli_arguments(["--method", "rrf", "--data-dir", str(self.data_dir), "--cache", str(cache), "--split", "dev"])
        # 路径保持调用者给定的值。
        self.assertEqual((arguments["data_dir"], arguments["cache_dir"]), (self.data_dir, cache))
        # 多模型对照按用户选择将配置名写入自动名称。
        self.assertEqual(arguments['run_name'], f'{self.data_dir.name}_rrf_bge_small_dev')

    # 用户明确要求config_dir必填，不再验收省略配置目录的旧调用。
    def test_config_directory_is_required_for_direct_calls(self):
        # 查看实际函数签名，允许用户自行选择位置或关键字参数形式。
        signature = inspect.signature(entry.main)
        # 必填参数不能保留None或其他默认值。
        self.assertIs(signature.parameters['config_dir'].default, inspect.Parameter.empty)
        # 不提供config_dir时应在参数绑定阶段明确失败。
        with self.assertRaises(TypeError):
            # 其他参数都按角色提供，避免因位置错位造成假失败。
            signature.bind(method='dense', data_dir=self.data_dir, split='dev', cache_dir=self.root / 'cache', run_name='missing_config')
        # 显式提供配置目录后应真正完成临时检索与保存。
        summary = self.invoke('dense', 'required_config_dir')
        # 验证成功路径，避免只测试必填声明而遗漏实现。
        self.assert_summary(summary, 'dense')

    # Qwen必须贯通4096维、真实配置及独立缓存，第二次不重复文档编码。
    def test_qwen_profile_metadata_dimensions_and_reuse(self):
        # 先建立原BGE临时缓存作为身份对照。
        legacy = self.invoke('dense', 'legacy_bge')
        # 使用同一入口选择Qwen配置，真实向量由假模型生成。
        first = self.invoke('dense', 'qwen_first', profile='qwen3_8b')
        # 第三次读取Qwen完整缓存。
        second = self.invoke('dense', 'qwen_second', profile='qwen3_8b')
        # 所有指标仍通过已有真实评分与保存路径。
        self.assert_summary(first, 'dense')
        # 拿到实际写入的Dense元数据。
        dense = first['config']['dense']
        # 参数来源是受版本管理的配置，不复制一套近似值。
        expected = json.loads(PROFILE_PATH.read_text(encoding='utf-8'))['qwen3_8b']
        # 名称、长度与完整维度必须属于Qwen。
        self.assertEqual((dense['embedding_profile'], dense['embedding_dimension'], dense['max_seq_length']), ('qwen3_8b', 4096, 8192))
        # 形状来自真实缓存输出，而不是摘要硬编码。
        self.assertEqual(list(dense['embeddings_shape']), [4, 4096])
        # 四项实际构造配置逐一保留。
        for key in ('model_name', 'model_kwargs', 'encode_kwargs', 'query_encode_kwargs'):
            # 深层精度、长度和prompt也要完全相等。
            self.assertEqual(dense[key], expected[key])
        # 前缀摘要必须等于真正的查询编码参数。
        self.assertEqual(dense['query_prefix'], expected['query_encode_kwargs']['prompt'])
        # 原BGE和Qwen不能混用缓存。
        self.assertNotEqual(legacy['config']['dense']['embeddings_cache']['fingerprint'], dense['embeddings_cache']['fingerprint'])
        # 首次Qwen从零开始，重复Qwen则实际命中完整缓存。
        self.assertFalse(dense['embeddings_cache']['cache_hit'])
        # 最后一次运行应标记真实缓存命中。
        self.assertTrue(second['config']['dense']['embeddings_cache']['cache_hit'])
        # 各次运行的模型初始化与文档调用严格对应。
        self.assertEqual([len(model.document_calls) for model in self.models], [1, 1, 0])
        # 文档缓存复用后，两条查询仍按原文编码。
        self.assertEqual(self.models[-1].query_calls, ['alpha question', 'beta question'])

    # 无效配置名必须在加载语料或模型之前明确拒绝。
    def test_unknown_profile_rejected_before_loading(self):
        # 任何越过配置检查的读取都会使测试失败。
        with patch.object(entry, 'load_beir_dataset', side_effect=AssertionError('invalid profile reached loader')):
            # 约定使用ValueError表达用户配置无效。
            with self.assertRaises(ValueError):
                # 当前名称不存在于配置文件。
                self.invoke('dense', 'bad_profile', profile='missing_profile')
        # 不得为非法配置创建模型。
        self.assertEqual(self.model.call_count, 0)

    # BM25不能静默接受未使用的Qwen模型选择。
    def test_bm25_with_qwen_rejected_before_loading(self):
        # 拒绝过程不需要读取任何语料。
        with patch.object(entry, 'load_beir_dataset', side_effect=AssertionError('invalid combination reached loader')):
            # 明确拒绝矛盾配置。
            with self.assertRaises(ValueError):
                # 仍调用用户自己的参数选择逻辑。
                self.invoke('bm25', 'bad_combination', profile='qwen3_8b')
        # 既不创建模型也不构建索引。
        self.assertEqual((self.model.call_count, self.build.call_count), (0, 0))

    # 实际模型维度或长度与声明不一致时必须在缓存和评测之前失败。
    def test_real_model_metadata_mismatch_rejected_before_encoding(self):
        # 分别让实际维度与实际长度偏离声明。
        for changed in ('dimension', 'length'):
            # 每个分支独立显示失败原因。
            with self.subTest(changed=changed):
                # 这个构造器仍只创建无权重假对象。
                def mismatch_factory(**kwargs):
                    # 保留入口实际提供的参数。
                    model = SyntheticEmbeddings(**kwargs)
                    # 只改一项返回值以检测对应核对逻辑。
                    if changed == 'dimension':
                        # 4097与配置的4096不同。
                        model._client.get_embedding_dimension.return_value = 4097
                    # 另一分支维度保持正常，只改变输入长度。
                    else:
                        # 8193与配置的8192不同。
                        model._client.max_seq_length = 8193
                    # 返回实际元数据有偏差的假模型。
                    return model
                # 替换真实模型初始化，不修改任何用户函数。
                self.model.side_effect = mismatch_factory
                # 错误必须明确暴露，不继续创建错误缓存。
                with self.assertRaises(ValueError):
                    # 同一配置在两种偏差下都必须失败。
                    self.invoke('dense', f'mismatch_{changed}', profile='qwen3_8b')
                # 编码和评分均不能发生。
                self.assertEqual((self.prepare.call_count, self.evaluate.call_count), (0, 0))

    # 识别用户当前使用的CLI参数名称，不因等价命名阻断逻辑验收。
    def profile_option(self):
        # 优先使用任务文档中的名称，否则使用用户已保存的等价名称。
        return '--embedding-profile' if '--embedding-profile' in ENTRY_PATH.read_text(encoding='utf-8') else '--config-embedding-model'

    # Qwen CLI必须将所选配置传入main，并生成独立结果名。
    def test_cli_qwen_profile_forwarding_and_generated_name(self):
        # 只执行CLI语法块，不加载模型或语料。
        arguments = self.cli_arguments(['--method', 'dense', self.profile_option(), 'qwen3_8b'])
        # 读取实际签名中的角色名。
        parameter = 'config_embedding_model' if 'config_embedding_model' in inspect.signature(entry.main).parameters else 'embedding_profile'
        # 参数不能只解析后留在CLI局部变量中。
        self.assertEqual(arguments[parameter], 'qwen3_8b')
        # 自动名包含Qwen配置，避免覆盖已有Dense结果。
        self.assertEqual(arguments['run_name'], 'nfcorpus_dense_qwen3_8b_dev')

    # 显式结果名必须优先于自动命名规则。
    def test_cli_explicit_name_keeps_precedence(self):
        # 无实际main运行，只检查解析和传参。
        arguments = self.cli_arguments(['--method', 'dense', self.profile_option(), 'qwen3_8b', '--run-name', 'custom_qwen_run'])
        # 用户指定的名字不应被自动前缀覆盖。
        self.assertEqual(arguments['run_name'], 'custom_qwen_run')

    # 使用真实安装类和无权重模块，证明推荐维度API确实可调用。
    def test_runtime_dimension_api_uses_installed_class(self):
        # Pooling只保存配置，没有预训练模型权重或网络请求。
        pooling = Pooling(embedding_dimension=4096, pooling_mode='lasttoken')
        # 以CPU构造真实SentenceTransformer，禁止推断GPU或加载远端模型。
        client = SentenceTransformer(modules=[pooling], device='cpu')
        # 直接调用真实新API，避免仅用假对象证明自己的假设。
        self.assertEqual(client.get_embedding_dimension(), 4096)


# 支持从项目根目录独立运行入口验收。
if __name__ == "__main__":
    # 所有输入、模型向量与输出均为合成临时材料。
    unittest.main()

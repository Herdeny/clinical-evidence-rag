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
# 为假模型提供最大长度属性。
from types import SimpleNamespace
# 自动清理微型语料和缓存。
import tempfile
# 沿用项目测试框架。
import unittest
# 替换真实模型并统计索引构建次数。
from unittest.mock import Mock, patch
# 生成384维单位向量，不使用GPU。
import numpy as np
# 只导入实际入口，导入本身不得启动基准。
import run_benchmark_eval as entry

# 保留不同方法实际到达的阶段，用于解释共享阻断。
OBSERVATIONS = []
# 定位正式源文件，仅用于CLI参数块的语法读取。
ENTRY_PATH = Path(entry.__file__).resolve()


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
        # 若入口读取实际最大长度，返回冻结模型的预期值。
        self._client = SimpleNamespace(max_seq_length=512)
        # 记录文档实际编码次数。
        self.document_calls = []
    # 根据虚构文档中的主题选择单位向量。
    def embed_documents(self, texts):
        # 复制输入，便于检查标题和正文是否被使用。
        self.document_calls.append(list(texts))
        # 每个主题对应不同的384维单位向量。
        return [np.eye(384, dtype=np.float32)[next(index for index, word in enumerate(("alpha", "beta", "gamma", "delta")) if word in text.lower())].tolist() for text in texts]
    # 原始查询只匹配第一或第二个虚构主题。
    def embed_query(self, query):
        # 原始查询未携带CT模板或标注答案。
        return np.eye(384, dtype=np.float32)[0 if "alpha" in query.lower() else 1].tolist()


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
    def invoke(self, method, run_name):
        # 捕获临时进度，保持测试结果简洁。
        try:
            # 不改变检索、评分或保存逻辑。
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                # 全部路径只指向临时目录。
                return entry.main(method, self.data_dir, "dev", self.root / "cache", run_name)
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
                entry.main("unknown", self.data_dir, "dev", self.root / "cache", "invalid")

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
        # 默认结果名应包含数据集、方法与划分。
        self.assertEqual(arguments["run_name"], "nfcorpus_bm25_dev")

    # 显式参数和默认结果名不能被硬编码数据集身份覆盖。
    def test_cli_explicit_paths_and_generated_run_name(self):
        # 使用一个虚构的可配置路径。
        cache = self.root / "alternate_cache"
        # 指定方法、目录和划分，但让结果名前缀自动生成。
        arguments = self.cli_arguments(["--method", "rrf", "--data-dir", str(self.data_dir), "--cache", str(cache), "--split", "dev"])
        # 路径保持调用者给定的值。
        self.assertEqual((arguments["data_dir"], arguments["cache_dir"]), (self.data_dir, cache))
        # 实际数据集、方法和划分组成运行身份。
        self.assertEqual(arguments["run_name"], f"{self.data_dir.name}_rrf_dev")


# 支持从项目根目录独立运行入口验收。
if __name__ == "__main__":
    # 所有输入、模型向量与输出均为合成临时材料。
    unittest.main()

# 验证扩题过程保留原数据、划分和人工复核内容。
"""Behavioral checks for the source-bound CT evaluation data builder."""

# 深拷贝蓝本，检查构建不改写输入。
from copy import deepcopy
# 读取本地固定数据，不请求网络。
import json
# 使用自动清理的目录验证重建。
from pathlib import Path
# 避免测试输出进入正式评测目录。
import tempfile
# 沿用项目现有测试框架。
import unittest

# 只导入助手的数据辅助模块，不导入模型或检索入口。
from scripts.data.build_ct_evaluation import ROOT, build, make_new_cases, resolve_evidence_sets


# 将数据发布与标签结构的关键行为集中验证。
class CtEvaluationTests(unittest.TestCase):
    # 准备一个包含适用场景的微型来源，避免复制医学规则。
    def fixture(self):
        # 一个固定来源即可验证事实缺失和证据缺失的不同动作。
        source = {"s": {"snapshot_sha256": "fixed"}}
        # 两条完整保留同一Variant条件的合成行。
        cards = {"A": {"source_id": "s", "text": "Variant: 1 first"}, "B": {"source_id": "s", "text": "Variant: 1 second"}}
        # 列出四种独立的补全状态。
        variants = [("ready", {}), ("fact", {"missing": ["exam_date"]}), ("rule", {"evidence_gaps": ["category_table"]}), ("both", {"missing": ["exam_date"], "evidence_gaps": ["category_table"]})]
        # 只为行为测试构造一族合成题。
        spec = {"authored_at_client_date": "2026-11-21", "evidence_sets": {"rule": ["A", "B"]}, "families": [{"group": "family", "split": "dev", "task": "test", "evidence_groups": ["rule"], "cases": [[name, name, "Question", "Expected", options] for name, options in variants]}]}
        # 返回相互独立的输入对象。
        return spec, cards, source

    # 条件选择器失配时不能继续沿用gold。
    def test_source_selection_rejects_drift_and_unknown_ids(self):
        # 取出微型固定数据。
        spec, cards, _ = self.fixture()
        # 用来源与场景前缀选择两个完整行。
        spec["evidence_sets"] = {"rule": {"source_id": "s", "text_startswith": "Variant: 1 ", "expected_count": 2}}
        # 正常情况下得到固定且可替代的ID集合。
        self.assertEqual(resolve_evidence_sets(spec, cards), {"rule": ["A", "B"]})
        # 模拟源格式变化导致只找到一行。
        with self.assertRaisesRegex(ValueError, "selection changed"):
            # 删除一行应触发身份检查，不静默缩小参考集合。
            resolve_evidence_sets(spec, {"A": cards["A"]})
        # 模拟把隔离或不存在的条目写进gold。
        spec["evidence_sets"] = {"rule": ["unadmitted"]}
        # 这种标签必须在输出题目之前拒绝。
        with self.assertRaisesRegex(ValueError, "quarantined"):
            # 不接受未准入ID。
            resolve_evidence_sets(spec, cards)

    # 下游Agent必须区分向人追问和补查来源。
    def test_fact_and_evidence_gaps_are_distinct_without_mutation(self):
        # 准备四种缺失状态。
        spec, cards, sources = self.fixture()
        # 保存深拷贝，避免构建悄悄改变标签输入。
        before = deepcopy(spec)
        # 不运行任何检索或模型。
        rows = make_new_cases(spec, {"rule": ["A", "B"]}, cards, sources, {"family": "dev"})
        # 两类缺失分别映射到独立动作。
        self.assertEqual([row["expected_action"] for row in rows], ["answer_with_evidence_and_limits", "clarify", "retrieve_more_or_state_evidence_limit", "clarify_and_retrieve_more"])
        # gold集合使用复制，修改输出不能反向污染蓝本。
        rows[0]["gold_evidence_groups"][0].append("C")
        # 蓝本必须保持原值。
        self.assertEqual(spec, before)
        # 任何构建均不能自行标记为已由医生复核。
        self.assertTrue(all(not row["annotation"]["clinician_reviewed"] for row in rows))

    # 已经用于开发的家族不能重新包装为留出。
    def test_existing_family_cannot_move_to_holdout(self):
        # 准备开发家族。
        spec, cards, sources = self.fixture()
        # 模拟新蓝本错误移动到留出。
        spec["families"][0]["split"] = "holdout"
        # 既定边界优先于蓝本的新划分。
        with self.assertRaisesRegex(ValueError, "split changed"):
            # 应在生成任何题目前失败。
            make_new_cases(spec, {"rule": ["A", "B"]}, cards, sources, {"family": "dev"})

    # 实际固定快照应能离线重建，并保护用户填写的复核意见。
    def test_real_snapshot_rebuild_is_deterministic_and_protects_review(self):
        # 复用正式清单进行内容比较，不显示留出正文。
        published = json.loads((ROOT / "data/evaluation/ct_v3/manifest.json").read_text())
        # 所有输出都进入测试专用临时目录。
        with tempfile.TemporaryDirectory() as directory:
            # 指定隔离输出位置。
            output = Path(directory)
            # 第一次只做数据组装与本地分词计数。
            first = build(output)
            # 九份生成文件应逐字节重现。
            self.assertEqual(first["files"], published["files"])
            # 再次构建也应产生相同数据。
            self.assertEqual(build(output)["files"], first["files"])
            # 模拟用户开始填写复核记录。
            review = output / "review.dev.csv"
            # 保留确切修改值用于检查。
            edited = review.read_bytes() + b"\nreviewer-note"
            # 在临时复核表写入人工作业。
            review.write_bytes(edited)
            # 重建必须停止，不能覆盖已经填写的内容。
            with self.assertRaisesRegex(ValueError, "Modified evaluation output: review.dev.csv"):
                # 不提供强制覆盖选项，改用新版本目录。
                build(output)
            # 确认保护检查没有改写人工内容。
            self.assertEqual(review.read_bytes(), edited)


# 支持单独运行本组检查。
if __name__ == "__main__":
    # 启动标准单元测试，不执行真实检索评测。
    unittest.main()

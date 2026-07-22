from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from _test_paths import REPO_ROOT


SPEC = importlib.util.spec_from_file_location(
    "knowledge_lifecycle", REPO_ROOT / "system/scripts/knowledge_lifecycle.py"
)
assert SPEC and SPEC.loader
KNOWLEDGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(KNOWLEDGE)
DOCTOR_SPEC = importlib.util.spec_from_file_location(
    "knowledge_doctor", REPO_ROOT / "system/scripts/workspace_doctor.py"
)
assert DOCTOR_SPEC and DOCTOR_SPEC.loader
DOCTOR = importlib.util.module_from_spec(DOCTOR_SPEC)
DOCTOR_SPEC.loader.exec_module(DOCTOR)


FOLDERS = {
    "exploration": "wiki/explorations",
    "pattern": "wiki/patterns",
    "rule": "wiki/rules",
}


def page(
    root: Path, kind: str, name: str, frontmatter: str, body: str = "# note\n"
) -> Path:
    folder = root / FOLDERS[kind]
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_text(
        f"---\n{frontmatter.strip()}\n---\n\n{body}", encoding="utf-8"
    )
    return path


EMPTY_FILTERS = {
    "domain": [],
    "ticker": [],
    "decision_scenarios": [],
    "recall_signals": [],
}


class KnowledgeLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "workspace").mkdir()
        (self.root / "workspace/workspace-config.md").write_text(
            "# config\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_rebuild_indexes_and_load_by_recall_signal(self) -> None:
        page(
            self.root,
            "exploration",
            "exp.md",
            """
id: EXP-20260720-01
type: exploration
title: 800V 电源架构
status: validated
summary: 高压架构改变功率器件约束
review_due: 2099-01-01
based_on: [S1, S2]
recall_signals: [800V, 高压电源]
decision_scenarios: [功率半导体研究]
""",
        )
        page(
            self.root,
            "pattern",
            "pat.md",
            """
id: PAT-20260720-01
type: pattern
title: 架构升级先卡在瓶颈器件
status: active
summary: 系统架构升级会先放大关键器件约束
review_due: 2099-01-01
source_explorations: [EXP-20260720-01, EXP-20260720-02]
primary_confirmations: 2
recall_signals: [电源架构升级, 碳化硅]
decision_scenarios: [功率半导体研究]
failure_signals: [供给不再紧张]
""",
        )
        page(
            self.root,
            "rule",
            "rule.md",
            """
id: RULE-20260720-01
type: rule
title: 先验证瓶颈再判断龙头
status: active
summary: 只有瓶颈约束被独立证据确认时，龙头映射才有意义
scope: 功率器件供给受架构升级约束时
review_due: 2099-01-01
source_patterns: [PAT-20260720-01]
independent_confirmations: 3
recall_signals: [瓶颈器件]
decision_scenarios: [公司研究]
invalidation_signals: [供给快速宽松]
""",
        )
        indexes = KNOWLEDGE.rebuild_indexes(self.root, apply=True)
        self.assertTrue(any(item["applied"] for item in indexes))
        exploration_index = (
            self.root / "wiki/explorations/_index.md"
        ).read_text(encoding="utf-8")
        self.assertIn("EXP-20260720-01", exploration_index)
        matches = KNOWLEDGE.load_knowledge(
            self.root,
            context="研究 800V 高压电源架构和碳化硅瓶颈器件",
            selected_types={"exploration", "pattern", "rule"},
            limit=8,
            include_review=False,
            all_active=False,
            filters=EMPTY_FILTERS,
        )
        self.assertEqual(
            [item["type"] for item in matches],
            ["rule", "pattern", "exploration"],
        )

    def test_weakened_knowledge_is_not_loaded_by_default(self) -> None:
        page(
            self.root,
            "pattern",
            "weak.md",
            """
id: PAT-20260720-02
type: pattern
title: 旧模式
status: weakened
summary: 已出现反例
review_due: 2099-01-01
recall_signals: [旧模式]
decision_scenarios: [研究]
""",
        )
        matches = KNOWLEDGE.load_knowledge(
            self.root,
            context="旧模式",
            selected_types={"pattern"},
            limit=8,
            include_review=False,
            all_active=False,
            filters=EMPTY_FILTERS,
        )
        self.assertEqual(matches, [])
        reviewed = KNOWLEDGE.load_knowledge(
            self.root,
            context="旧模式",
            selected_types={"pattern"},
            limit=8,
            include_review=True,
            all_active=False,
            filters=EMPTY_FILTERS,
        )
        self.assertEqual(len(reviewed), 1)

    def test_transition_requires_gates_and_records_history(self) -> None:
        path = page(
            self.root,
            "pattern",
            "candidate.md",
            """
id: PAT-20260720-03
type: pattern
title: 候选模式
status: draft
summary: 可观察结构
review_due: 2099-01-01
source_explorations: [EXP-1, EXP-2]
primary_confirmations: 2
recall_signals: [结构信号]
decision_scenarios: [公司研究]
failure_signals: [反例出现]
""",
        )
        meta, _, error = KNOWLEDGE.read_page(path)
        self.assertIsNone(error)
        page_data = {"type": "pattern", "path": path, "meta": meta}
        self.assertEqual(KNOWLEDGE.transition_errors(page_data, "active"), [])
        queue_item, created = KNOWLEDGE.queue_transition(
            self.root, page_data, "active", "两个独立案例确认", ["EXP-1", "EXP-2"]
        )
        self.assertTrue(created)
        self.assertEqual(queue_item["type"], "knowledge-pattern")
        KNOWLEDGE.apply_transition(
            path, "active", "两个独立案例确认", ["EXP-1", "EXP-2"]
        )
        updated = path.read_text(encoding="utf-8")
        self.assertIn("status: active", updated)
        self.assertIn("## 生命周期记录", updated)

    def test_load_record_is_append_only(self) -> None:
        page(
            self.root,
            "rule",
            "record.md",
            """
id: RULE-20260720-02
type: rule
title: 可记录规则
status: active
summary: 规则
scope: 研究
review_due: 2099-01-01
recall_signals: [规则]
decision_scenarios: [研究]
invalidation_signals: [反例]
""",
        )
        matches = KNOWLEDGE.load_knowledge(
            self.root,
            context="研究规则",
            selected_types={"rule"},
            limit=1,
            include_review=False,
            all_active=False,
            filters=EMPTY_FILTERS,
        )
        invocation = KNOWLEDGE.record_load(
            self.root, "研究规则", matches, "R-1"
        )
        self.assertTrue(invocation.startswith("KU-"))
        usage = self.root / "workspace/knowledge-usage.jsonl"
        event = json.loads(usage.read_text(encoding="utf-8"))
        self.assertEqual(event["research_id"], "R-1")
        self.assertEqual(event["knowledge_ids"], ["RULE-20260720-02"])

    def test_doctor_validates_links_and_active_rule_gate(self) -> None:
        page(
            self.root,
            "pattern",
            "broken.md",
            """
id: PAT-20260720-04
type: pattern
title: 断链模式
status: active
summary: 用于验证断链
review_due: 2099-01-01
source_explorations: [EXP-MISSING]
primary_confirmations: 2
recall_signals: [断链]
decision_scenarios: [测试]
failure_signals: [反例]
""",
        )
        page(
            self.root,
            "rule",
            "under-confirmed.md",
            """
id: RULE-20260720-03
type: rule
title: 未满足门槛规则
status: active
summary: 案例不足
scope: 测试
review_due: 2099-01-01
source_patterns: [PAT-20260720-04]
independent_confirmations: 2
recall_signals: [测试]
decision_scenarios: [测试]
invalidation_signals: [反例]
""",
        )
        result = DOCTOR.validate(self.root)
        codes = {item["code"] for item in result["findings"]}
        self.assertIn("broken-knowledge-link", codes)
        self.assertIn("rule-confirmations", codes)
        self.assertEqual(result["objects"]["knowledge"], 2)

    def test_cycle_top_example_keeps_mother_cases_out_of_confirmations(self) -> None:
        fixture = REPO_ROOT / "examples/knowledge-lifecycle-cycle-top/wiki"
        shutil.copytree(fixture, self.root / "wiki", dirs_exist_ok=True)

        summary = KNOWLEDGE.summarize(self.root)
        self.assertEqual(summary["counts"]["exploration"]["promoted"], 2)
        self.assertEqual(summary["counts"]["pattern"]["draft"], 1)
        self.assertEqual(summary["promotion_candidates"], [])

        default_matches = KNOWLEDGE.load_knowledge(
            self.root,
            context="制造业扩产 ROIC 设备订单 周期见顶",
            selected_types={"pattern"},
            limit=8,
            include_review=False,
            all_active=False,
            filters=EMPTY_FILTERS,
        )
        self.assertEqual(default_matches, [])

        review_matches = KNOWLEDGE.load_knowledge(
            self.root,
            context="制造业扩产 ROIC 设备订单 周期见顶",
            selected_types={"pattern"},
            limit=8,
            include_review=True,
            all_active=False,
            filters=EMPTY_FILTERS,
        )
        self.assertEqual(
            [item["id"] for item in review_matches], ["PAT-EXAMPLE-CYCLE-TOP-01"]
        )

        pattern_page = next(
            page
            for page in KNOWLEDGE.iter_pages(self.root, {"pattern"})
            if page["meta"].get("id") == "PAT-EXAMPLE-CYCLE-TOP-01"
        )
        errors = KNOWLEDGE.transition_errors(pattern_page, "active")
        self.assertIn("pattern 至少需要两次 primary confirmation 才能 active", errors)

        independently_confirmed = {
            **pattern_page,
            "meta": {**pattern_page["meta"], "primary_confirmations": 2},
        }
        self.assertEqual(
            KNOWLEDGE.transition_errors(independently_confirmed, "active"), []
        )


if __name__ == "__main__":
    unittest.main()

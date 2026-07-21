from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from _test_paths import REPO_ROOT


SPEC = importlib.util.spec_from_file_location(
    "research_preflight", REPO_ROOT / "system/scripts/research_preflight.py"
)
assert SPEC and SPEC.loader
PREFLIGHT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREFLIGHT)
DOCTOR_SPEC = importlib.util.spec_from_file_location(
    "preflight_doctor", REPO_ROOT / "system/scripts/workspace_doctor.py"
)
assert DOCTOR_SPEC and DOCTOR_SPEC.loader
DOCTOR = importlib.util.module_from_spec(DOCTOR_SPEC)
DOCTOR_SPEC.loader.exec_module(DOCTOR)


def write_page(path: Path, frontmatter: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\n{frontmatter.strip()}\n---\n\n{body.strip()}\n", encoding="utf-8"
    )


class ResearchPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "workspace-root"
        (self.root / "workspace").mkdir(parents=True)
        (self.root / "workspace/workspace-config.md").write_text(
            "- wiki_root: `./wiki`\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_preflight_combines_rules_and_regular_wiki_scan(self) -> None:
        write_page(
            self.root / "wiki/rules/power-bottleneck.md",
            """
id: RULE-20260721-01
type: rule
title: 先验证瓶颈再映射龙头
status: active
summary: 架构升级先验证关键器件供给约束
scope: 功率半导体
review_due: 2099-01-01
recall_signals: [800V, 功率器件瓶颈]
decision_scenarios: [公司研究]
invalidation_signals: [供给快速宽松]
""",
            "# 先验证瓶颈再映射龙头\n\n规则正文。",
        )
        write_page(
            self.root / "wiki/entities/ifx.md",
            """
title: 英飞凌
type: entity
status: current
ticker: [IFX.DE]
concepts: [功率半导体, 碳化硅]
tags: [800V]
""",
            "# 英飞凌\n\n功率半导体与碳化硅供应商。",
        )
        write_page(
            self.root / "wiki/concepts/800v.md",
            """
title: 800V 电源架构
type: concept
status: stable
concepts: [高压电源, 碳化硅]
""",
            "# 800V 电源架构\n\nAI 服务器电源架构升级。",
        )
        write_page(
            self.root / "wiki/sources/unrelated.md",
            """
title: 医药行业周报
type: source-summary
status: processed
source_url: https://example.com/health
""",
            "# 医药行业周报\n\n医保政策与创新药进展。",
        )

        result = PREFLIGHT.build_preflight(
            self.root,
            context="英飞凌 IFX.DE 800V 功率半导体 碳化硅 公司研究",
            research_id="R20260721-01",
            tickers=["IFX.DE"],
        )

        self.assertEqual([item["id"] for item in result["knowledge"]], ["RULE-20260721-01"])
        paths = {item["path"] for item in result["wiki_matches"]}
        self.assertIn("wiki/entities/ifx.md", paths)
        self.assertIn("wiki/concepts/800v.md", paths)
        self.assertNotIn("wiki/sources/unrelated.md", paths)
        self.assertEqual(result["scanned"]["sources"], 1)

    def test_external_wiki_root_is_resolved_from_workspace_config(self) -> None:
        external = self.root.parent / "personal-wiki"
        write_page(
            external / "entities/ifx.md",
            "title: 英飞凌\nticker: [IFX.DE]\nstatus: current",
            "# 英飞凌\n\n外部 Wiki 页面。",
        )
        (self.root / "workspace/workspace-config.md").write_text(
            "- wiki_root: `../personal-wiki`\n", encoding="utf-8"
        )

        resolved = PREFLIGHT.resolve_wiki_root(self.root)
        result = PREFLIGHT.build_preflight(
            self.root,
            context="英飞凌 IFX.DE",
            research_id="R-EXT",
        )

        self.assertEqual(resolved, external.resolve())
        self.assertEqual(len(result["wiki_matches"]), 1)
        self.assertEqual(Path(result["wiki_root"]), external.resolve())

    def test_review_flags_and_receipt_are_verifiable(self) -> None:
        write_page(
            self.root / "wiki/entities/old-company.md",
            """
title: 旧公司判断
status: stale
ticker: [OLD]
review_due: 2020-01-01
""",
            """
# 旧公司判断

## 反方证据

最新数据与旧判断冲突。
""",
        )
        result = PREFLIGHT.build_preflight(
            self.root,
            context="OLD 旧公司判断",
            research_id="R-FLAG",
        )
        receipt = PREFLIGHT.save_receipt(self.root, result)
        text = receipt.read_text(encoding="utf-8")

        self.assertEqual(len(result["review_flags"]), 1)
        flags = result["review_flags"][0]["flags"]
        self.assertTrue(any("stale" in item for item in flags))
        self.assertTrue(any("复审已到期" in item for item in flags))
        self.assertTrue(any("反方" in item for item in flags))
        self.assertIn("wiki_pages_loaded:", text)
        self.assertIn("Wiki check:", text)

    def test_legacy_knowledge_match_surfaces_missing_lifecycle_fields(self) -> None:
        write_page(
            self.root / "wiki/explorations/legacy.md",
            "title: 800V 旧判断\ntype: exploration\nstatus: tentative",
            "# 800V 旧判断\n\n尚未迁移生命周期字段。",
        )
        result = PREFLIGHT.build_preflight(
            self.root, context="800V 电源架构", research_id="R-LEGACY"
        )
        self.assertEqual(len(result["knowledge"]), 1)
        flags = result["knowledge"][0]["flags"]
        self.assertIn("缺少稳定知识 ID", flags)
        self.assertIn("缺少复审日期", flags)
        self.assertIn("缺少召回信号", flags)

    def test_recorded_knowledge_usage_remains_append_only(self) -> None:
        match = {
            "id": "RULE-1",
            "type": "rule",
            "title": "规则",
            "status": "active",
            "summary": "摘要",
            "scope": "测试",
            "review_due": "2099-01-01",
            "failure_signals": [],
            "path": "wiki/rules/rule.md",
            "score": 10,
            "matched_by": ["召回信号"],
            "flags": [],
            "content": "# rule",
        }
        invocation = PREFLIGHT.lifecycle.record_load(
            self.root, "测试", [match], "R-1"
        )
        event = json.loads(
            (self.root / "workspace/knowledge-usage.jsonl").read_text(encoding="utf-8")
        )
        self.assertTrue(invocation.startswith("KU-"))
        self.assertEqual(event["knowledge_ids"], ["RULE-1"])

    def test_research_report_receives_preflight_links(self) -> None:
        report = self.root / "output/research/ifx.md"
        report.parent.mkdir(parents=True)
        report.write_text(
            "---\nid: R-IFX\nstatus: draft\npreflight_id:\n"
            "knowledge_used: []\nwiki_pages_loaded: []\n---\n\n# IFX\n",
            encoding="utf-8",
        )
        result = {
            "id": "PF-R-IFX-1234",
            "research_id": "R-IFX",
            "knowledge": [{"id": "RULE-1"}],
            "wiki_matches": [{"path": "wiki/entities/ifx.md"}],
        }
        updated = PREFLIGHT.update_research_file(self.root, report, result)
        content = updated.read_text(encoding="utf-8")

        self.assertIn("preflight_id: PF-R-IFX-1234", content)
        self.assertIn('knowledge_used: ["RULE-1"]', content)
        self.assertIn('wiki_pages_loaded: ["wiki/entities/ifx.md"]', content)

        result["research_id"] = "R-OTHER"
        with self.assertRaisesRegex(ValueError, "research id mismatch"):
            PREFLIGHT.update_research_file(self.root, report, result)

    def test_cli_record_writes_receipt_usage_and_report(self) -> None:
        report = self.root / "output/research/ifx.md"
        report.parent.mkdir(parents=True)
        report.write_text(
            "---\nid: R-CLI\nstatus: draft\npreflight_id:\n"
            "knowledge_used: []\nwiki_pages_loaded: []\n---\n\n# IFX\n",
            encoding="utf-8",
        )
        write_page(
            self.root / "wiki/entities/ifx.md",
            "title: 英飞凌\nticker: [IFX.DE]\nstatus: current",
            "# 英飞凌\n\n功率半导体。",
        )
        argv = [
            "research_preflight.py",
            "--root",
            str(self.root),
            "--context",
            "英飞凌 IFX.DE 功率半导体",
            "--research-id",
            "R-CLI",
            "--research-file",
            str(report),
            "--record",
            "--json",
        ]
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch("sys.argv", argv), redirect_stdout(stdout), redirect_stderr(stderr):
            code = PREFLIGHT.main()

        self.assertEqual(code, 0, stderr.getvalue())
        payload = json.loads(stdout.getvalue())
        self.assertTrue((self.root / payload["receipt_path"]).is_file())
        self.assertTrue((self.root / "workspace/knowledge-usage.jsonl").is_file())
        self.assertIn("preflight_id: PF-R-CLI-", report.read_text(encoding="utf-8"))

    def test_doctor_verifies_report_against_preflight_receipt(self) -> None:
        report = self.root / "output/research/doctor.md"
        report.parent.mkdir(parents=True)
        report.write_text(
            "---\nid: R-DOC\nstatus: active\nlinked_hypotheses: []\n"
            "preflight_id:\nknowledge_used: []\nwiki_pages_loaded: []\n---\n\n# Doctor\n",
            encoding="utf-8",
        )
        result = PREFLIGHT.build_preflight(
            self.root, context="本地扫描测试", research_id="R-DOC"
        )
        PREFLIGHT.save_receipt(self.root, result)
        PREFLIGHT.update_research_file(self.root, report, result)

        valid = DOCTOR.validate(self.root)
        self.assertEqual(valid["errors"], 0, valid["findings"])
        content = report.read_text(encoding="utf-8")
        content = PREFLIGHT.lifecycle.replace_frontmatter_scalar(
            content, "wiki_pages_loaded", '["wiki/entities/missing.md"]'
        )
        report.write_text(content, encoding="utf-8")
        invalid = DOCTOR.validate(self.root)
        codes = {item["code"] for item in invalid["findings"]}
        self.assertIn("preflight-load-mismatch", codes)


if __name__ == "__main__":
    unittest.main()

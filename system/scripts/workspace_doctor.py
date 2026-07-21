#!/usr/bin/env python3
"""Validate research object schemas and cross-file links in a workspace."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # Core Mode remains dependency-free.
    yaml = None

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

RESEARCH_STATUSES = {"draft", "active", "closed", "archived"}
HYPOTHESIS_STATUSES = {
    "new",
    "active",
    "paused",
    "invalidated",
    "realized",
    "archived",
    # Legacy values remain valid during gradual migration.
    "新建",
    "观察",
    "暂停",
    "推翻",
    "已兑现",
    "closed",
    "rejected",
}
EVIDENCE_DIRECTIONS = {"pending", "strengthen", "weaken", "neutral", "mixed"}
EVIDENCE_REVIEW_STATUSES = {"pending", "confirmed", "rejected"}
KNOWLEDGE_PATHS = {
    "exploration": ("wiki/explorations/*.md",),
    "pattern": ("wiki/patterns/*.md", "workspace/patterns/*.md"),
    "rule": ("wiki/rules/*.md",),
}
KNOWLEDGE_PREFIXES = {"exploration": "EXP-", "pattern": "PAT-", "rule": "RULE-"}
KNOWLEDGE_STATUSES = {
    "exploration": {
        "tentative",
        "validated",
        "weakened",
        "invalidated",
        "promoted",
        "archived",
    },
    "pattern": {"draft", "active", "weakened", "promoted", "retired", "archived"},
    "rule": {"candidate", "active", "weakened", "deprecated", "archived"},
}


def find_workspace_root(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "workspace" / "workspace-config.md").is_file():
            return candidate
    return current


def relative(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def read_frontmatter(path: Path) -> tuple[dict[str, Any], str | None]:
    try:
        content = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        return {}, str(exc)
    match = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", content, re.DOTALL)
    if not match:
        return {}, "missing frontmatter"
    if yaml is not None:
        try:
            payload = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError as exc:
            return {}, f"invalid YAML: {exc}"
        return (payload, None) if isinstance(payload, dict) else ({}, "frontmatter is not a mapping")

    values: dict[str, Any] = {}
    current_key: str | None = None
    for line in match.group(1).splitlines():
        field = re.match(r"^([A-Za-z_][\w-]*):\s*(.*?)\s*$", line)
        if field:
            key = field.group(1)
            value = field.group(2).strip().strip('"\'')
            current_key = key if not value else None
            if value.startswith("[") and value.endswith("]"):
                values[key] = [
                    item.strip().strip('"\'')
                    for item in value[1:-1].split(",")
                    if item.strip()
                ]
            else:
                values[key] = value or None
            continue
        list_item = re.match(r"^-\s+(.+?)\s*$", line)
        if list_item and current_key:
            if not isinstance(values.get(current_key), list):
                values[current_key] = []
            values[current_key].append(list_item.group(1).strip('"\''))
            continue
        nested = re.match(r"^\s+([^:]+):\s*(.*?)\s*$", line)
        if nested and current_key:
            if not isinstance(values.get(current_key), dict):
                values[current_key] = {}
            values[current_key][nested.group(1).strip()] = nested.group(2).strip('"\'')
    return values, None


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)] if str(value).strip() else []


def finding(
    severity: str, code: str, path: str, message: str
) -> dict[str, str]:
    return {"severity": severity, "code": code, "path": path, "message": message}


def collect_objects(
    root: Path,
    pattern: str,
    expected_prefix: str,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    objects: list[dict[str, Any]] = []
    findings: list[dict[str, str]] = []
    seen: dict[str, str] = {}
    for path in sorted(root.glob(pattern)):
        if path.name.lower() == "readme.md":
            continue
        relpath = relative(path, root)
        meta, error = read_frontmatter(path)
        if error:
            findings.append(finding("ERROR", "frontmatter", relpath, error))
            continue
        object_id = str(meta.get("id") or "").strip()
        if not object_id:
            findings.append(finding("ERROR", "missing-id", relpath, "缺少稳定 id"))
            continue
        if not object_id.upper().startswith(expected_prefix.upper()):
            findings.append(
                finding(
                    "ERROR",
                    "invalid-id",
                    relpath,
                    f"id `{object_id}` 不符合 {expected_prefix}* 约定",
                )
            )
        if object_id in seen:
            findings.append(
                finding(
                    "ERROR",
                    "duplicate-id",
                    relpath,
                    f"id `{object_id}` 已被 {seen[object_id]} 使用",
                )
            )
        else:
            seen[object_id] = relpath
        objects.append({"id": object_id, "path": relpath, "meta": meta})
    return objects, findings


def parse_watchlist_hypotheses(path: Path) -> list[tuple[str, str]]:
    if not path.is_file():
        return []
    headers: list[str] | None = None
    references: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if headers is None and "Ticker" in cells and "Hypothesis" in cells:
            headers = cells
            continue
        if headers is not None and cells == headers:
            continue
        if headers is None or len(cells) != len(headers) or set("".join(cells)) == {"-"}:
            continue
        row = dict(zip(headers, cells, strict=True))
        for hypothesis_id in re.split(r"[,;/\s]+", row.get("Hypothesis", "")):
            if hypothesis_id:
                references.append((row.get("Ticker", ""), hypothesis_id))
    return references


def parse_iso_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def collect_knowledge(
    root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    pages: list[dict[str, Any]] = []
    findings: list[dict[str, str]] = []
    seen: dict[str, str] = {}
    for knowledge_type, patterns in KNOWLEDGE_PATHS.items():
        for pattern in patterns:
            for path in sorted(root.glob(pattern)):
                if path.name.startswith("_") or path.name.lower() == "readme.md":
                    continue
                relpath = relative(path, root)
                meta, error = read_frontmatter(path)
                if error:
                    findings.append(
                        finding(
                            "WARN",
                            "legacy-knowledge-frontmatter",
                            relpath,
                            f"旧知识页尚未接入生命周期：{error}",
                        )
                    )
                    continue
                item_id = str(meta.get("id") or "").strip()
                if not item_id:
                    findings.append(
                        finding(
                            "WARN",
                            "legacy-knowledge-id",
                            relpath,
                            "缺少稳定 id；下次复盘时迁移，不自动改写旧页面",
                        )
                    )
                elif not item_id.upper().startswith(KNOWLEDGE_PREFIXES[knowledge_type]):
                    findings.append(
                        finding(
                            "ERROR",
                            "knowledge-id",
                            relpath,
                            f"id `{item_id}` 应使用 {KNOWLEDGE_PREFIXES[knowledge_type]} 前缀",
                        )
                    )
                elif item_id in seen:
                    findings.append(
                        finding(
                            "ERROR",
                            "duplicate-knowledge-id",
                            relpath,
                            f"id `{item_id}` 已被 {seen[item_id]} 使用",
                        )
                    )
                else:
                    seen[item_id] = relpath

                declared_type = str(meta.get("type") or "")
                if declared_type and declared_type != knowledge_type:
                    findings.append(
                        finding(
                            "ERROR",
                            "knowledge-type",
                            relpath,
                            f"目录类型为 {knowledge_type}，frontmatter 却是 `{declared_type}`",
                        )
                    )
                status = str(meta.get("status") or "")
                if status not in KNOWLEDGE_STATUSES[knowledge_type]:
                    findings.append(
                        finding(
                            "ERROR",
                            "knowledge-status",
                            relpath,
                            f"非法 status `{status}`",
                        )
                    )
                for required in ("summary", "recall_signals", "decision_scenarios", "review_due"):
                    if not meta.get(required):
                        findings.append(
                            finding(
                                "WARN",
                                "knowledge-load-field",
                                relpath,
                                f"缺少加载或复审字段 `{required}`",
                            )
                        )
                if meta.get("review_due") and parse_iso_date(meta.get("review_due")) is None:
                    findings.append(
                        finding("ERROR", "knowledge-review-date", relpath, "review_due 必须是 YYYY-MM-DD")
                    )
                elif (
                    parse_iso_date(meta.get("review_due"))
                    and parse_iso_date(meta.get("review_due")) < date.today()
                    and status in {"tentative", "validated", "active", "promoted", "candidate", "weakened"}
                ):
                    findings.append(
                        finding("WARN", "knowledge-review-overdue", relpath, "知识卡已到复审日期")
                    )
                if knowledge_type == "pattern" and status in {"active", "promoted"}:
                    if not as_list(meta.get("failure_signals")):
                        findings.append(
                            finding("ERROR", "pattern-failure-signals", relpath, "生效 pattern 必须定义 failure_signals")
                        )
                    if not as_list(meta.get("source_explorations")):
                        findings.append(
                            finding("ERROR", "pattern-sources", relpath, "生效 pattern 必须关联 source_explorations")
                        )
                if knowledge_type == "rule" and status == "active":
                    if not meta.get("scope"):
                        findings.append(finding("ERROR", "rule-scope", relpath, "生效 rule 必须限定 scope"))
                    if not as_list(meta.get("invalidation_signals")):
                        findings.append(
                            finding("ERROR", "rule-invalidation", relpath, "生效 rule 必须定义 invalidation_signals")
                        )
                    try:
                        confirmations = int(meta.get("independent_confirmations") or 0)
                    except (TypeError, ValueError):
                        confirmations = 0
                    if confirmations < 3:
                        findings.append(
                            finding("ERROR", "rule-confirmations", relpath, "生效 rule 至少需要三个独立案例确认")
                        )
                pages.append(
                    {"id": item_id, "type": knowledge_type, "path": relpath, "meta": meta}
                )
    return pages, findings


def validate(root: Path) -> dict[str, Any]:
    research, findings = collect_objects(root, "output/research/*.md", "R")
    preflights, more = collect_objects(root, "output/research/preflight/*.md", "PF-")
    findings.extend(more)
    hypotheses, more = collect_objects(root, "hypothesis/H*.md", "H")
    findings.extend(more)
    evidence, more = collect_objects(root, "evidence/**/*.md", "E-")
    findings.extend(more)
    knowledge, more = collect_knowledge(root)
    findings.extend(more)

    research_ids = {item["id"] for item in research}
    preflight_by_id = {item["id"]: item for item in preflights}
    hypothesis_ids = {item["id"] for item in hypotheses}
    knowledge_ids = {item["id"] for item in knowledge if item["id"]}
    exploration_ids = {
        item["id"] for item in knowledge if item["id"] and item["type"] == "exploration"
    }
    pattern_ids = {
        item["id"] for item in knowledge if item["id"] and item["type"] == "pattern"
    }

    for item in knowledge:
        meta = item["meta"]
        references: list[tuple[str, list[str], set[str]]] = []
        if item["type"] == "pattern":
            references.append(("source_explorations", as_list(meta.get("source_explorations")), exploration_ids))
        if item["type"] == "rule":
            references.append(("source_patterns", as_list(meta.get("source_patterns")), pattern_ids))
        references.append(("supersedes", as_list(meta.get("supersedes")), knowledge_ids))
        references.append(("superseded_by", as_list(meta.get("superseded_by")), knowledge_ids))
        promoted_to = as_list(meta.get("promoted_to"))
        if promoted_to:
            references.append(("promoted_to", promoted_to, knowledge_ids))
        for field, values, valid_ids in references:
            for reference in values:
                if reference not in valid_ids:
                    findings.append(
                        finding(
                            "ERROR",
                            "broken-knowledge-link",
                            item["path"],
                            f"{field} 引用了不存在的知识 `{reference}`",
                        )
                    )

    for item in research:
        meta = item["meta"]
        status = str(meta.get("status") or "")
        if status not in RESEARCH_STATUSES:
            findings.append(
                finding("ERROR", "research-status", item["path"], f"非法 status `{status}`")
            )
        for hypothesis_id in as_list(meta.get("linked_hypotheses")):
            if hypothesis_id not in hypothesis_ids:
                findings.append(
                    finding(
                        "ERROR",
                        "broken-hypothesis-link",
                        item["path"],
                        f"关联假设 `{hypothesis_id}` 不存在",
                    )
                )
        preflight_id = str(meta.get("preflight_id") or "").strip()
        if not preflight_id and status in {"active", "closed"}:
            findings.append(
                finding(
                    "WARN",
                    "missing-research-preflight",
                    item["path"],
                    "进行中或已收口研究缺少 Research Preflight 回执",
                )
            )
        elif preflight_id and preflight_id not in preflight_by_id:
            findings.append(
                finding(
                    "ERROR",
                    "broken-research-preflight",
                    item["path"],
                    f"引用的 preflight `{preflight_id}` 不存在",
                )
            )
        elif preflight_id:
            receipt = preflight_by_id[preflight_id]
            if str(receipt["meta"].get("research_id") or "") != item["id"]:
                findings.append(
                    finding(
                        "ERROR",
                        "preflight-research-mismatch",
                        item["path"],
                        f"回执 `{preflight_id}` 属于另一研究",
                    )
                )
            for field in ("knowledge_used", "wiki_pages_loaded"):
                if set(as_list(meta.get(field))) != set(as_list(receipt["meta"].get(field))):
                    findings.append(
                        finding(
                            "ERROR",
                            "preflight-load-mismatch",
                            item["path"],
                            f"报告与回执的 `{field}` 不一致",
                        )
                    )

    for item in hypotheses:
        meta = item["meta"]
        status = str(meta.get("status") or "")
        if status not in HYPOTHESIS_STATUSES:
            findings.append(
                finding("ERROR", "hypothesis-status", item["path"], f"非法 status `{status}`")
            )
        certainty = meta.get("certainty")
        if isinstance(certainty, str):
            certainty = certainty.rstrip("%")
        try:
            certainty_value = float(certainty)
            if not 0 <= certainty_value <= 100:
                raise ValueError
        except (TypeError, ValueError):
            findings.append(
                finding("ERROR", "certainty", item["path"], "certainty 必须是 0-100 的数字")
            )
        for research_id in as_list(meta.get("linked_research")):
            if research_id not in research_ids:
                findings.append(
                    finding(
                        "ERROR",
                        "broken-research-link",
                        item["path"],
                        f"来源研究 `{research_id}` 不存在",
                    )
                )

    for item in evidence:
        meta = item["meta"]
        direction = str(meta.get("direction") or "")
        review_status = str(meta.get("review_status") or "")
        if direction not in EVIDENCE_DIRECTIONS:
            findings.append(
                finding("ERROR", "evidence-direction", item["path"], f"非法 direction `{direction}`")
            )
        if review_status not in EVIDENCE_REVIEW_STATUSES:
            findings.append(
                finding(
                    "ERROR",
                    "evidence-review-status",
                    item["path"],
                    f"非法 review_status `{review_status}`",
                )
            )
        linked = as_list(meta.get("linked_hypotheses"))
        if not linked:
            findings.append(finding("ERROR", "orphan-evidence", item["path"], "证据未关联任何假设"))
        for hypothesis_id in linked:
            if hypothesis_id not in hypothesis_ids:
                findings.append(
                    finding(
                        "ERROR",
                        "broken-hypothesis-link",
                        item["path"],
                        f"关联假设 `{hypothesis_id}` 不存在",
                    )
                )
        raw_impacts = meta.get("hypothesis_impacts")
        impacts = raw_impacts or {}
        if raw_impacts is None:
            findings.append(
                finding(
                    "WARN",
                    "missing-hypothesis-impacts",
                    item["path"],
                    "旧证据缺少 hypothesis_impacts，建议下次复盘时补齐",
                )
            )
        elif not isinstance(impacts, dict):
            findings.append(
                finding("ERROR", "hypothesis-impacts", item["path"], "hypothesis_impacts 必须是映射")
            )
            impacts = {}
        if raw_impacts is not None:
            for hypothesis_id in linked:
                impact = str(impacts.get(hypothesis_id) or "")
                if impact not in EVIDENCE_DIRECTIONS - {"mixed"}:
                    findings.append(
                        finding(
                            "ERROR",
                            "hypothesis-impact",
                            item["path"],
                            f"假设 `{hypothesis_id}` 缺少合法的逐假设影响判断",
                        )
                    )
        for hypothesis_id in impacts:
            if str(hypothesis_id) not in linked:
                findings.append(
                    finding(
                        "ERROR",
                        "orphan-impact",
                        item["path"],
                        f"hypothesis_impacts 包含未链接假设 `{hypothesis_id}`",
                    )
                )
        for required in (
            "source_provider",
            "source_url",
            "source_published_at",
            "fetched_at",
            "raw_value",
            "dedup_key",
        ):
            if not meta.get(required):
                findings.append(
                    finding("WARN", "missing-provenance", item["path"], f"缺少来源字段 `{required}`")
                )

    watchlist_path = root / "config" / "daily-watchlist-watchlist.md"
    for ticker, hypothesis_id in parse_watchlist_hypotheses(watchlist_path):
        if hypothesis_id not in hypothesis_ids:
            findings.append(
                finding(
                    "ERROR",
                    "watchlist-hypothesis",
                    relative(watchlist_path, root),
                    f"{ticker or '未知标的'} 引用了不存在的假设 `{hypothesis_id}`",
                )
            )

    errors = sum(item["severity"] == "ERROR" for item in findings)
    warnings = sum(item["severity"] == "WARN" for item in findings)
    return {
        "workspace": str(root),
        "objects": {
            "research": len(research),
            "preflights": len(preflights),
            "hypotheses": len(hypotheses),
            "evidence": len(evidence),
            "knowledge": len(knowledge),
        },
        "errors": errors,
        "warnings": warnings,
        "findings": findings,
    }


def render_text(result: dict[str, Any]) -> str:
    objects = result["objects"]
    lines = [
        "AI Workspace Hub 结构验证",
        f"工作区：{result['workspace']}",
        f"对象：研究 {objects['research']} / Preflight {objects['preflights']} / 假设 {objects['hypotheses']} / 证据 {objects['evidence']}",
        f"知识：{objects['knowledge']} 张生命周期卡",
        f"结果：{result['errors']} errors / {result['warnings']} warnings",
    ]
    for item in result["findings"]:
        lines.append(
            f"- [{item['severity']}] {item['code']} {item['path']} - {item['message']}"
        )
    if not result["findings"]:
        lines.append("- OK：对象格式和关联关系正常。")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = validate(find_workspace_root(args.root))
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render_text(result))
    return 2 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

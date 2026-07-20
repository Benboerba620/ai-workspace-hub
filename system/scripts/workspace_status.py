#!/usr/bin/env python3
"""Summarize actionable research-workspace state without changing files."""

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


def find_workspace_root(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "workspace" / "workspace-config.md").is_file():
            return candidate
    return current


def parse_frontmatter(path: Path) -> dict[str, Any]:
    try:
        content = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        return {}
    match = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", content, re.DOTALL)
    if not match:
        return {}
    if yaml is not None:
        try:
            payload = yaml.safe_load(match.group(1)) or {}
            return payload if isinstance(payload, dict) else {}
        except yaml.YAMLError:
            return {}

    values: dict[str, Any] = {}
    for line in match.group(1).splitlines():
        field = re.match(r"^([A-Za-z_][\w-]*):\s*(.*?)\s*$", line)
        if not field:
            continue
        value = field.group(2).strip().strip('"\'')
        if value.startswith("[") and value.endswith("]"):
            values[field.group(1)] = [
                item.strip().strip('"\'')
                for item in value[1:-1].split(",")
                if item.strip()
            ]
        else:
            values[field.group(1)] = value or None
    return values


def relative(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def pending_queue_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    rows: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 7 or cells[-1].lower() != "pending":
            continue
        rows.append({"id": cells[0], "type": cells[1], "object": cells[2]})
    return rows


def is_overdue(value: Any) -> bool:
    if not value:
        return False
    try:
        return date.fromisoformat(str(value)[:10]) < date.today()
    except ValueError:
        return False


def collect_status(root: Path) -> dict[str, Any]:
    active_research: list[dict[str, str]] = []
    for path in sorted((root / "output" / "research").glob("*.md")):
        meta = parse_frontmatter(path)
        status = str(meta.get("status") or "draft").lower()
        if status in {"draft", "active", "in_progress", "进行中"}:
            active_research.append(
                {
                    "id": str(meta.get("id") or path.stem),
                    "path": relative(path, root),
                    "status": status,
                }
            )

    open_hypotheses: list[dict[str, Any]] = []
    overdue_reviews: list[str] = []
    closed_statuses = {"closed", "archived", "rejected", "推翻", "已兑现", "暂停"}
    for path in sorted((root / "hypothesis").glob("H*.md")):
        meta = parse_frontmatter(path)
        status = str(meta.get("status") or "unknown")
        filename_match = re.match(r"H\d+", path.stem)
        hypothesis_id = str(
            meta.get("id") or (filename_match.group(0) if filename_match else path.stem)
        )
        if status.lower() not in closed_statuses and status not in closed_statuses:
            open_hypotheses.append(
                {
                    "id": hypothesis_id,
                    "status": status,
                    "certainty": meta.get("certainty"),
                    "path": relative(path, root),
                }
            )
        if is_overdue(meta.get("next_review_at")):
            overdue_reviews.append(hypothesis_id)

    pending_evidence: list[dict[str, str]] = []
    for path in sorted((root / "evidence").glob("**/*.md")):
        if path.name.lower() == "readme.md":
            continue
        meta = parse_frontmatter(path)
        if str(meta.get("review_status") or "pending").lower() == "pending":
            pending_evidence.append(
                {
                    "id": str(meta.get("id") or path.stem),
                    "path": relative(path, root),
                }
            )

    knowledge_counts: dict[str, dict[str, int]] = {}
    overdue_knowledge_reviews: list[dict[str, str]] = []
    knowledge_promotion_candidates: list[dict[str, str]] = []
    knowledge_locations = {
        "exploration": (root / "wiki/explorations",),
        "pattern": (root / "wiki/patterns", root / "workspace/patterns"),
        "rule": (root / "wiki/rules",),
    }
    for knowledge_type, folders in knowledge_locations.items():
        for folder in folders:
            if not folder.is_dir():
                continue
            for path in sorted(folder.glob("*.md")):
                if path.name.startswith("_") or path.name.lower() == "readme.md":
                    continue
                meta = parse_frontmatter(path)
                status = str(meta.get("status") or "missing")
                knowledge_counts.setdefault(knowledge_type, {})[status] = (
                    knowledge_counts.setdefault(knowledge_type, {}).get(status, 0) + 1
                )
                item_id = str(meta.get("id") or path.stem)
                if is_overdue(meta.get("review_due")):
                    overdue_knowledge_reviews.append(
                        {"id": item_id, "type": knowledge_type, "path": relative(path, root)}
                    )
                confirmations = meta.get(
                    "primary_confirmations"
                    if knowledge_type == "pattern"
                    else "independent_confirmations"
                )
                try:
                    confirmation_count = int(confirmations or 0)
                except (TypeError, ValueError):
                    confirmation_count = 0
                reason = ""
                if knowledge_type == "exploration" and status == "validated":
                    reason = "复盘是否提炼为 pattern"
                elif knowledge_type == "pattern" and status == "active" and confirmation_count >= 3:
                    reason = "已达到 rule 的案例数量门槛"
                elif knowledge_type == "rule" and status == "candidate" and confirmation_count >= 3:
                    reason = "可确认是否启用"
                if reason:
                    knowledge_promotion_candidates.append(
                        {"id": item_id, "type": knowledge_type, "reason": reason, "path": relative(path, root)}
                    )

    queue = pending_queue_rows(root / "workspace" / "review-queue.md")
    watchlist = root / "config" / "daily-watchlist-watchlist.md"
    profile_path = root / "workspace" / "research-profile.md"
    profile_text = (
        profile_path.read_text(encoding="utf-8-sig") if profile_path.is_file() else ""
    )
    version_match = re.search(r"^- version:\s*`?([^`\n]+)", profile_text, re.MULTILINE)
    count_match = re.search(
        r"^- calibrated_research_count:\s*`?(\d+)", profile_text, re.MULTILINE
    )

    recommendations: list[str] = []
    if pending_evidence:
        recommendations.append(
            f"复盘 {len(pending_evidence)} 条待确认新证据，再决定是否调整假设。"
        )
    if queue:
        recommendations.append(f"处理 {len(queue)} 条待确认动作。")
    if overdue_reviews:
        recommendations.append("复盘已到期假设：" + "、".join(overdue_reviews) + "。")
    if overdue_knowledge_reviews:
        recommendations.append(f"复盘 {len(overdue_knowledge_reviews)} 张已到期知识卡。")
    if knowledge_promotion_candidates:
        recommendations.append(f"审查 {len(knowledge_promotion_candidates)} 张知识卡是否应晋级。")
    if active_research:
        recommendations.append("继续或收口进行中的研究。")
    if not watchlist.is_file():
        recommendations.append("初始化唯一执行股票池 config/daily-watchlist-watchlist.md。")
    if not recommendations:
        recommendations.append("当前没有积压；可以开始新研究或生成今日日报。")

    return {
        "workspace": str(root),
        "active_research": active_research,
        "open_hypotheses": open_hypotheses,
        "pending_evidence": pending_evidence,
        "pending_reviews": queue,
        "overdue_hypothesis_reviews": overdue_reviews,
        "knowledge_lifecycle": {
            "counts": knowledge_counts,
            "overdue_reviews": overdue_knowledge_reviews,
            "promotion_candidates": knowledge_promotion_candidates,
        },
        "watchlist_ready": watchlist.is_file(),
        "research_profile": {
            "version": version_match.group(1).strip() if version_match else "unknown",
            "calibrated_research_count": int(count_match.group(1)) if count_match else 0,
        },
        "recommendations": recommendations,
    }


def render_text(status: dict[str, Any]) -> str:
    lines = ["AI Workspace Hub 状态", f"工作区：{status['workspace']}", ""]
    lines.extend(
        [
            f"进行中研究：{len(status['active_research'])}",
            f"开放假设：{len(status['open_hypotheses'])}",
            f"待复盘证据：{len(status['pending_evidence'])}",
            f"待确认动作：{len(status['pending_reviews'])}",
            f"已到期复盘：{len(status['overdue_hypothesis_reviews'])}",
            f"到期知识卡：{len(status['knowledge_lifecycle']['overdue_reviews'])}",
            f"知识晋级候选：{len(status['knowledge_lifecycle']['promotion_candidates'])}",
            f"执行股票池：{'READY' if status['watchlist_ready'] else 'MISSING'}",
            "",
            "建议下一步：",
        ]
    )
    lines.extend(f"- {item}" for item in status["recommendations"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    status = collect_status(find_workspace_root(args.root))
    if args.json:
        print(json.dumps(status, ensure_ascii=False, indent=2))
    else:
        print(render_text(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

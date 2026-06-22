"""
扫描 hypothesis markdown 文件并输出概览。

Usage:
  python scripts/sync_hypothesis.py
  python scripts/sync_hypothesis.py --json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

from workspace_paths import find_workspace_root, resolve_hypothesis_dir

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def extract_frontmatter(content: str) -> dict[str, object]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", content, re.DOTALL)
    if not match:
        return {}
    payload = yaml.safe_load(match.group(1)) or {}
    return payload if isinstance(payload, dict) else {}


def extract_title(content: str, fallback: str) -> str:
    match = re.search(r"^#\s+H\d+\s*[:：]\s*(.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else fallback


def read_hypothesis_files(hypothesis_dir: Path) -> dict[str, dict[str, object]]:
    data: dict[str, dict[str, object]] = {}
    for file_path in sorted(hypothesis_dir.glob("H*.md")):
        content = file_path.read_text(encoding="utf-8")
        frontmatter = extract_frontmatter(content)
        match = re.match(r"(H\d+)", file_path.stem)
        if not match:
            continue
        hypothesis_id = match.group(1)
        data[hypothesis_id] = {
            "certainty": frontmatter.get("certainty"),
            "status": frontmatter.get("status"),
            "title": extract_title(content, file_path.name),
            "file": file_path.name,
        }
    return data


def format_certainty_bar(certainty: object) -> str:
    if certainty is None:
        return "—"
    certainty_value = int(certainty)
    if certainty_value >= 80:
        return f"🟢 {certainty_value}%"
    if certainty_value >= 50:
        return f"🟡 {certainty_value}%"
    return f"🔴 {certainty_value}%"


def main() -> int:
    workspace_root = find_workspace_root(Path(__file__).resolve().parent)
    hypothesis_dir = resolve_hypothesis_dir(workspace_root)
    data = read_hypothesis_files(hypothesis_dir)

    if "--json" in sys.argv:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    print(f"Read {len(data)} hypothesis files:\n")
    print("| ID | Certainty | Status | File |")
    print("|-----|-----------|--------|------|")
    for hypothesis_id, info in sorted(data.items(), key=lambda item: int(item[0][1:])):
        bar = format_certainty_bar(info["certainty"])
        status_value = info["status"] or "—"
        print(f"| {hypothesis_id} | {bar} | {status_value} | {info['file']} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

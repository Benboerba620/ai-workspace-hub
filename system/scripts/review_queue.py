#!/usr/bin/env python3
"""Add, list, or update persistent review-queue items."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

VALID_STATUSES = {"pending", "approved", "rejected", "done"}
TABLE_HEADER = (
    "| ID | 类型 | 对象 | 建议动作 | 来源 | 创建日期 | 状态 |\n"
    "|---|---|---|---|---|---|---|\n"
)


def find_workspace_root(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "workspace" / "workspace-config.md").is_file():
            return candidate
    return current


def queue_path(root: Path) -> Path:
    return root / "workspace" / "review-queue.md"


def sanitize(value: str) -> str:
    return " ".join(value.replace("|", "/").split())


def parse_rows(content: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in content.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 7 or not re.fullmatch(r"Q-\d{8}-\d{2}", cells[0]):
            continue
        rows.append(
            dict(
                zip(
                    ("id", "type", "object", "action", "source", "created", "status"),
                    cells,
                    strict=True,
                )
            )
        )
    return rows


def ensure_queue(path: Path) -> str:
    if path.is_file():
        return path.read_text(encoding="utf-8-sig")
    path.parent.mkdir(parents=True, exist_ok=True)
    content = (
        "# Review Queue\n\n"
        "> 需要用户确认后才能生效的研究动作。\n\n"
        + TABLE_HEADER
        + "\n状态只使用：`pending` / `approved` / `rejected` / `done`。\n"
    )
    path.write_text(content, encoding="utf-8")
    return content


def next_id(rows: list[dict[str, str]], today: date) -> str:
    prefix = f"Q-{today.strftime('%Y%m%d')}-"
    used = [int(row["id"].rsplit("-", 1)[1]) for row in rows if row["id"].startswith(prefix)]
    return prefix + f"{max(used, default=0) + 1:02d}"


def add_item(
    path: Path,
    *,
    item_type: str,
    object_id: str,
    action: str,
    source: str,
    today: date | None = None,
) -> tuple[dict[str, str], bool]:
    content = ensure_queue(path)
    rows = parse_rows(content)
    normalized = tuple(sanitize(value) for value in (item_type, object_id, action, source))
    for row in rows:
        existing = (row["type"], row["object"], row["action"], row["source"])
        if row["status"] == "pending" and existing == normalized:
            return row, False

    current_date = today or date.today()
    item = {
        "id": next_id(rows, current_date),
        "type": normalized[0],
        "object": normalized[1],
        "action": normalized[2],
        "source": normalized[3],
        "created": current_date.isoformat(),
        "status": "pending",
    }
    row_text = (
        f"| {item['id']} | {item['type']} | {item['object']} | {item['action']} | "
        f"{item['source']} | {item['created']} | {item['status']} |\n"
    )
    lines = content.splitlines(keepends=True)
    separator_index = next(
        (
            index
            for index, line in enumerate(lines)
            if line.strip().startswith("|---|---|---|---|---|---|---|")
        ),
        None,
    )
    if separator_index is None:
        content = content.rstrip() + "\n\n" + TABLE_HEADER + row_text
    else:
        lines.insert(separator_index + 1, row_text)
        content = "".join(lines)
    path.write_text(content, encoding="utf-8")
    return item, True


def update_item(path: Path, item_id: str, status: str) -> bool:
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status}")
    content = ensure_queue(path)
    pattern = re.compile(
        rf"(?m)^(\|\s*{re.escape(item_id)}\s*\|.*?\|\s*)"
        r"(pending|approved|rejected|done)(\s*\|\s*)$"
    )
    updated, count = pattern.subn(rf"\g<1>{status}\g<3>", content, count=1)
    if count:
        path.write_text(updated, encoding="utf-8")
    return bool(count)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("--type", required=True)
    add_parser.add_argument("--object", required=True)
    add_parser.add_argument("--action", required=True)
    add_parser.add_argument("--source", required=True)
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--status", choices=sorted(VALID_STATUSES))
    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("id")
    update_parser.add_argument("--status", required=True, choices=sorted(VALID_STATUSES))
    args = parser.parse_args()
    path = queue_path(find_workspace_root(args.root))

    if args.command == "add":
        item, created = add_item(
            path,
            item_type=args.type,
            object_id=args.object,
            action=args.action,
            source=args.source,
        )
        print(json.dumps({"created": created, "item": item}, ensure_ascii=False))
        return 0
    if args.command == "list":
        rows = parse_rows(ensure_queue(path))
        if args.status:
            rows = [row for row in rows if row["status"] == args.status]
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0

    if update_item(path, args.id, args.status):
        print(json.dumps({"updated": True, "id": args.id, "status": args.status}))
        return 0
    print(f"ERROR: queue item not found: {args.id}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

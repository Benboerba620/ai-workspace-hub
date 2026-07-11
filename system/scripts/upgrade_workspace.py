#!/usr/bin/env python3
"""Preview or safely apply managed-file upgrades from a newer Hub checkout."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

EXCLUDED_DIR_NAMES = {"__pycache__", ".ruff_cache", ".pytest_cache", ".mypy_cache"}
EXCLUDED_FILE_NAMES = {".DS_Store", ".coverage"}


def is_excluded(path: Path) -> bool:
    if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
        return True
    if path.suffix in {".pyc", ".pyo"} or path.name in EXCLUDED_FILE_NAMES:
        return True
    return path.name.startswith(".env") and path.name != ".env.example"


def digest(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(source: Path) -> dict[str, Any]:
    path = source / "system" / "managed-files.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload.get("ownership"), dict):
        raise ValueError(f"Invalid ownership manifest: {path}")
    return payload


def expand_source_paths(source: Path, patterns: list[str]) -> list[Path]:
    paths: set[Path] = set()
    for pattern in patterns:
        if pattern.endswith("/**"):
            base = source / pattern[:-3]
            matches = base.rglob("*") if base.is_dir() else []
        else:
            matches = source.glob(pattern)
        for path in matches:
            if path.is_file() and not is_excluded(path.relative_to(source)):
                paths.add(path.relative_to(source))
    return sorted(paths, key=lambda item: item.as_posix())


def compare(source: Path, target: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    ownership = manifest["ownership"]
    managed_paths = expand_source_paths(source, list(ownership.get("managed") or []))
    managed: list[dict[str, str]] = []
    for relpath in managed_paths:
        source_path = source / relpath
        target_path = target / relpath
        if not target_path.exists():
            state = "add"
        elif digest(source_path) != digest(target_path):
            state = "change"
        else:
            state = "same"
        managed.append({"path": relpath.as_posix(), "state": state})

    mixed: list[dict[str, str]] = []
    for relpath in expand_source_paths(source, list(ownership.get("mixed") or [])):
        target_path = target / relpath
        if not target_path.exists():
            state = "missing"
        elif digest(source / relpath) != digest(target_path):
            state = "manual-merge"
        else:
            state = "same"
        mixed.append({"path": relpath.as_posix(), "state": state})
    migrations: list[dict[str, str]] = []
    migration_config = manifest.get("migrations") or {}
    for directory in migration_config.get("additive_directories") or []:
        target_path = target / str(directory)
        migrations.append(
            {
                "kind": "directory",
                "source": "",
                "target": str(directory),
                "state": "same" if target_path.is_dir() else "add",
            }
        )
    for item in migration_config.get("additive_files") or []:
        source_rel = str(item["source"])
        target_rel = str(item["target"])
        migrations.append(
            {
                "kind": "file",
                "source": source_rel,
                "target": target_rel,
                "state": "same" if (target / target_rel).exists() else "add",
            }
        )
    return {"managed": managed, "mixed": mixed, "migrations": migrations}


def apply_managed(
    source: Path,
    target: Path,
    manifest: dict[str, Any],
    changes: dict[str, Any],
) -> tuple[int, Path | None]:
    actionable = [item for item in changes["managed"] if item["state"] != "same"]
    migrations = [
        item for item in changes.get("migrations", []) if item["state"] == "add"
    ]
    if not actionable and not migrations:
        return 0, None
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = target / "workspace" / ".hub-backups" / timestamp
    for item in actionable:
        relpath = Path(item["path"])
        source_path = source / relpath
        target_path = target / relpath
        if target_path.is_file():
            backup_path = backup_root / relpath
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target_path, backup_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)

    for item in migrations:
        target_path = target / item["target"]
        if target_path.exists():
            continue
        if item["kind"] == "directory":
            target_path.mkdir(parents=True, exist_ok=True)
        else:
            source_path = source / item["source"]
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)

    state_path = target / "workspace" / ".hub-state.json"
    state: dict[str, Any] = {}
    if state_path.is_file():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            state = {}
    state.update(
        {
            "schema_version": 1,
            "installed_version": manifest.get("hub_version"),
            "last_upgrade_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(state, ensure_ascii=True, indent=2) + "\n", encoding="utf-8"
    )
    return len(actionable) + len(migrations), backup_root if backup_root.exists() else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="New Hub checkout")
    parser.add_argument("--target", type=Path, required=True, help="Installed workspace")
    parser.add_argument(
        "--apply-managed",
        action="store_true",
        help="Apply managed files and safe additive migrations; never overwrite user files",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    source = args.source.resolve()
    target = args.target.resolve()
    if source == target:
        print("ERROR: source and target must be different directories", file=sys.stderr)
        return 2
    try:
        manifest = load_manifest(source)
        changes = compare(source, target, manifest)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    actionable = [item for item in changes["managed"] if item["state"] != "same"]
    manual = [item for item in changes["mixed"] if item["state"] != "same"]
    migrations = [
        item for item in changes.get("migrations", []) if item["state"] != "same"
    ]
    result: dict[str, Any] = {
        "hub_version": manifest.get("hub_version"),
        "managed_changes": actionable,
        "manual_merges": manual,
        "safe_additions": migrations,
        "applied": 0,
        "backup": None,
    }
    if args.apply_managed:
        applied, backup = apply_managed(source, target, manifest, changes)
        result["applied"] = applied
        result["backup"] = str(backup) if backup else None

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        action = "已应用" if args.apply_managed else "预览"
        print(f"Hub {manifest.get('hub_version')} 升级{action}")
        print(f"受管文件变化：{len(actionable)}")
        for item in actionable:
            print(f"- [{item['state']}] {item['path']}")
        print(f"需要人工合并：{len(manual)}")
        for item in manual:
            print(f"- [{item['state']}] {item['path']}")
        print(f"只新增不覆盖：{len(migrations)}")
        for item in migrations:
            print(f"- [{item['state']}] {item['target']}")
        if args.apply_managed:
            print(f"已应用：{result['applied']}")
            if result["backup"]:
                print(f"备份：{result['backup']}")
        else:
            print("未修改目标工作区。确认后加 --apply-managed。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

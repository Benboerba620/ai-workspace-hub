#!/usr/bin/env python3
"""Check which AI Workspace Hub capabilities are ready to use.

The core workspace should be useful without API keys or Python packages. Optional
automation can light up later when the user adds dependencies and local keys.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from pathlib import Path

# Windows 控制台可能默认 cp1252/GBK，统一 UTF-8 输出避免中文触发 UnicodeEncodeError
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


CORE_FILES = (
    "AGENTS.md",
    "CLAUDE.md",
    "workspace/workspace-config.md",
    "workspace/meta/active-context.md",
    "wiki/_schema.md",
    "inbox/first-note.md",
    "system/integrations/personal-wiki.md",
    "system/skills/first-ingest.md",
    "system/skills/research.md",
    "system/skills/screen.md",
)

CORE_DIRECTORIES = (
    "inbox",
    "wiki",
    "wiki/sources",
    "output",
    "output/research",
    "output/screen",
    "hypothesis",
    "workspace/meta",
)

ENV_FILES = (
    "config/pod2wiki.env",
    "config/daily-watchlist.env",
    ".env",
)

PLACEHOLDER_PREFIXES = ("your_", "YOUR_", "replace_", "REPLACE_")
PLACEHOLDER_VALUES = {
    "",
    "changeme",
    "CHANGE_ME",
    "xxx",
    "XXX",
    "todo",
    "TODO",
    "none",
    "None",
    "null",
    "NULL",
}


def find_workspace_root(start: Path) -> Path:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "AGENTS.md").is_file() and (
            candidate / "workspace" / "workspace-config.md"
        ).is_file():
            return candidate
    return current


def is_placeholder(value: str | None) -> bool:
    if value is None:
        return True
    value = value.strip().strip('"').strip("'")
    if value in PLACEHOLDER_VALUES:
        return True
    return value.startswith(PLACEHOLDER_PREFIXES)


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_key_values(root: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for relative in ENV_FILES:
        values.update(parse_env_file(root / relative))
    for key in ("LLM_API_KEY", "FMP_API_KEY", "TUSHARE_TOKEN"):
        if os.environ.get(key):
            values[key] = os.environ[key]
    return values


def has_key(values: dict[str, str], key: str) -> bool:
    return not is_placeholder(values.get(key))


def status_line(ok: bool, label: str, detail: str = "") -> str:
    marker = "OK" if ok else "WARN"
    suffix = f" - {detail}" if detail else ""
    return f"  [{marker}] {label}{suffix}"


def fail_line(label: str, detail: str = "") -> str:
    suffix = f" - {detail}" if detail else ""
    return f"  [FAIL] {label}{suffix}"


def module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def check(root: Path) -> int:
    root = find_workspace_root(root)
    values = load_key_values(root)

    print("AI Workspace Hub workspace check")
    print(f"Root: {root}")
    print()

    core_ok = True
    print("Core Mode（零 API，应该立刻可用）")
    for relative in CORE_FILES:
        exists = (root / relative).is_file()
        core_ok = core_ok and exists
        line = status_line(True, relative) if exists else fail_line(relative, "missing")
        print(line)
    for relative in CORE_DIRECTORIES:
        exists = (root / relative).is_dir()
        core_ok = core_ok and exists
        line = status_line(True, relative) if exists else fail_line(relative, "missing")
        print(line)

    print()
    if core_ok:
        print("Core Mode result: READY")
        print("Next: ask your agent to turn inbox/first-note.md into a wiki note.")
    else:
        print("Core Mode result: NOT READY")
        print("Fix missing files/directories before using this as a workspace.")

    print()
    print("Enhanced Mode（可选自动化，缺 key 不代表安装失败）")
    py_ok = sys.version_info >= (3, 10)
    print(
        status_line(
            py_ok,
            "Python >= 3.10",
            f"current {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        )
    )
    print(status_line(module_available("requests"), "dependency: requests"))
    print(status_line(module_available("dotenv"), "dependency: python-dotenv / dotenv"))
    print(status_line(module_available("yaml"), "dependency: pyyaml / yaml"))
    print(status_line(has_key(values, "LLM_API_KEY"), "LLM_API_KEY for podcast summaries"))
    print(status_line(has_key(values, "FMP_API_KEY"), "FMP_API_KEY for global market data"))
    print(status_line(has_key(values, "TUSHARE_TOKEN"), "TUSHARE_TOKEN for China A-share data"))

    print()
    print("Interpretation:")
    print("- Missing API keys only disable optional automation.")
    print("- Configure your own API keys if you want podcast, market data, or daily-watch automation.")
    print("- Keep keys in local config/*.env files; do not commit real secrets.")
    print("- Core Mode remains useful for Markdown wiki, research drafts, and hypothesis files.")
    return 0 if core_ok else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Workspace root. Defaults to the current directory.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return check(args.root)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Install AI Workspace Hub into a new or explicitly merged workspace."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


DIRECTORIES = (
    "workspace/meta",
    "workspace/patterns",
    "wiki/raw",
    "wiki/sources",
    "wiki/entities",
    "wiki/concepts",
    "wiki/explorations",
    "inbox",
    "output/research",
    "output/screen",
    "output/pod2wiki",
    "monitoring",
    "hypothesis",
    "evidence",
    "daily-watchlist-reports",
    "portfolio/journal",
    "config",
    "system/interfaces",
)

FILE_MAPPINGS = (
    ("START-HERE.md", "START-HERE.md"),
    ("system/templates/AGENTS.md", "AGENTS.md"),
    ("system/templates/CLAUDE.md", "CLAUDE.md"),
    ("system/templates/workspace-config.md", "workspace/workspace-config.md"),
    ("system/templates/active-context.md", "workspace/meta/active-context.md"),
    ("system/templates/friction-log.md", "workspace/meta/friction-log.md"),
    ("system/templates/research-profile.md", "workspace/research-profile.md"),
    ("system/templates/review-queue.md", "workspace/review-queue.md"),
    ("system/templates/interfaces-README.md", "system/interfaces/README.md"),
    ("wiki/_schema.md", "wiki/_schema.md"),
    ("wiki/explorations/_index.md", "wiki/explorations/_index.md"),
    ("wiki/rules.md", "wiki/rules.md"),
    ("wiki/false-beliefs.md", "wiki/false-beliefs.md"),
    ("workspace/patterns/_index.md", "workspace/patterns/_index.md"),
    ("workspace/patterns/_template.md", "workspace/patterns/_template.md"),
    ("evidence/README.md", "evidence/README.md"),
    ("requirements.txt", "requirements.txt"),
    ("requirements.lock", "requirements.lock"),
    ("requirements-pdf.txt", "requirements-pdf.txt"),
    ("system/managed-files.json", "system/managed-files.json"),
    (".gitignore", ".gitignore"),
    ("LICENSE", "LICENSE"),
    ("inbox/first-note.md", "inbox/first-note.md"),
    ("inbox/sample-ai-workspace.pdf", "inbox/sample-ai-workspace.pdf"),
)

DIRECTORY_MAPPINGS = (
    ("system/skills", "system/skills"),
    ("system/integrations", "system/integrations"),
    ("system/templates", "system/templates"),
    ("system/scripts", "system/scripts"),
    ("tools/podcast", "tools/podcast"),
    ("tools/daily-watch", "tools/daily-watch"),
)

CONFIG_MAPPINGS = (
    (
        "tools/daily-watch/config-examples/daily-watchlist.example.yaml",
        "config/daily-watchlist.yaml",
    ),
    (
        "tools/daily-watch/config-examples/daily-watchlist.env.example",
        "config/daily-watchlist.env",
    ),
    (
        "tools/daily-watch/config-examples/daily-watchlist.watchlist.example.md",
        "config/daily-watchlist-watchlist.md",
    ),
    (
        "tools/daily-watch/config-examples/hypothesis-tracker.example.yaml",
        "config/hypothesis-tracker.yaml",
    ),
    (
        "tools/daily-watch/config-examples/hypothesis-tracker.rules.example.md",
        "config/hypothesis-tracker.rules.md",
    ),
    ("tools/podcast/examples/config.ai-investing.yaml", "config/pod2wiki.config.yaml"),
    ("tools/podcast/.env.example", "config/pod2wiki.env"),
)


def copy_file(source: Path, destination: Path, merge: bool) -> str:
    if destination.exists():
        if merge:
            return "skipped"
        raise FileExistsError(f"Refusing to overwrite existing file: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return "created"


EXCLUDED_DIR_NAMES = {"__pycache__", ".ruff_cache", ".pytest_cache", ".mypy_cache"}
EXCLUDED_FILE_NAMES = {".DS_Store"}


def is_excluded(item: Path) -> bool:
    if any(part in EXCLUDED_DIR_NAMES for part in item.parts):
        return True
    if item.suffix in {".pyc", ".pyo"} or item.name in EXCLUDED_FILE_NAMES:
        return True
    # Never copy local secrets (.env, .env.local, ...); .env.example stays.
    if item.name.startswith(".env") and item.name != ".env.example":
        return True
    return False


def copy_directory(source: Path, destination: Path, merge: bool) -> tuple[int, int]:
    created = 0
    skipped = 0
    for item in source.rglob("*"):
        if is_excluded(item):
            continue
        relative = item.relative_to(source)
        target = destination / relative
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        result = copy_file(item, target, merge)
        created += result == "created"
        skipped += result == "skipped"
    return created, skipped


def customize_workspace_config(
    config_path: Path, name: str, primary_use: str, wiki_root: str
) -> None:
    text = config_path.read_text(encoding="utf-8")
    text = text.replace("name: `MY_AI_WORKSPACE`", f"name: `{name}`")
    text = text.replace(
        "primary_use: `research / writing / investing / podcast / mixed`",
        f"primary_use: `{primary_use}`",
    )
    text = text.replace("wiki_root: `./wiki`", f"wiki_root: `{wiki_root}`")
    config_path.write_text(text, encoding="utf-8")


def read_hub_version(source_root: Path) -> str:
    manifest_path = source_root / "system" / "managed-files.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    version = manifest.get("hub_version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError(f"Invalid hub_version in {manifest_path}")
    return version


def write_hub_state(target_root: Path, version: str, merge: bool) -> str:
    state_path = target_root / "workspace" / ".hub-state.json"
    if state_path.exists():
        return "skipped"
    state = {
        "schema_version": 1,
        "installed_version": version,
        "install_mode": "merge" if merge else "fresh",
    }
    state_path.write_text(
        json.dumps(state, ensure_ascii=True, indent=2) + "\n", encoding="utf-8"
    )
    return "created"


def install(
    source_root: Path,
    target_root: Path,
    *,
    merge: bool,
    name: str,
    primary_use: str,
    wiki_root: str,
) -> tuple[int, int]:
    source_root = source_root.resolve()
    target_root = target_root.resolve()
    if source_root == target_root:
        raise ValueError("Source and target workspace must be different directories")
    if not (source_root / "INSTALL-FOR-AI.md").is_file():
        raise FileNotFoundError(f"Invalid AI Workspace Hub source: {source_root}")
    hub_version = read_hub_version(source_root)

    if target_root.exists() and not target_root.is_dir():
        raise ValueError(f"Target exists but is not a directory: {target_root}")
    if target_root.is_dir() and any(target_root.iterdir()) and not merge:
        raise FileExistsError(
            f"Target is not empty: {target_root}. Use --merge to keep existing files."
        )
    target_root.mkdir(parents=True, exist_ok=True)
    for directory in DIRECTORIES:
        (target_root / directory).mkdir(parents=True, exist_ok=True)

    created = 0
    skipped = 0
    workspace_config_created = False
    for source_rel, target_rel in FILE_MAPPINGS + CONFIG_MAPPINGS:
        result = copy_file(source_root / source_rel, target_root / target_rel, merge)
        created += result == "created"
        skipped += result == "skipped"
        if target_rel == "workspace/workspace-config.md":
            workspace_config_created = result == "created"

    for source_rel, target_rel in DIRECTORY_MAPPINGS:
        new_count, skipped_count = copy_directory(
            source_root / source_rel, target_root / target_rel, merge
        )
        created += new_count
        skipped += skipped_count

    workspace_config = target_root / "workspace/workspace-config.md"
    if workspace_config_created:
        customize_workspace_config(workspace_config, name, primary_use, wiki_root)
    state_result = write_hub_state(target_root, hub_version, merge)
    created += state_result == "created"
    skipped += state_result == "skipped"
    return created, skipped


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, type=Path, help="Workspace directory")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="AI Workspace Hub source checkout",
    )
    parser.add_argument("--name", default="MY_AI_WORKSPACE")
    parser.add_argument("--primary-use", default="investing")
    parser.add_argument("--wiki-root", default="./wiki")
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Allow a non-empty target and keep every existing file unchanged",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        created, skipped = install(
            args.source,
            args.target,
            merge=args.merge,
            name=args.name,
            primary_use=args.primary_use,
            wiki_root=args.wiki_root,
        )
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    target = args.target.resolve()
    print(f"Installed AI Workspace Hub to {target}")
    print(f"Created files: {created}; preserved existing files: {skipped}")
    print(f'Next: python3 "{target / "system/scripts/check_workspace.py"}" --root "{target}" (verifies Core Mode)')
    print("Enhanced Mode (optional): run tools/daily-watch/scripts/check_setup.py later.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

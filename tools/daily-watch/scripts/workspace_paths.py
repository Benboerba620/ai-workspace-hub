from __future__ import annotations

from pathlib import Path

CONFIG_DIRNAME = "config"
REPORTS_DIRNAME = "daily-watchlist-reports"
HYPOTHESIS_DIRNAME = "hypothesis"
PORTFOLIO_DIRNAME = "portfolio"
JOURNAL_DIRNAME = "journal"
ROOT_INTEGRATION_HEADING = "## Daily Watchlist"

ENV_FILE_CANDIDATES = (
    "daily-watchlist.env",
    ".env",
)

CONFIG_FILE_CANDIDATES = (
    "daily-watchlist.yaml",
    "config.yaml",
)

WATCHLIST_FILE_CANDIDATES = (
    "daily-watchlist-watchlist.md",
    "watchlist.md",
)

TEMPLATE_FILE_CANDIDATES = (
    "daily-watchlist-report-template.md",
    "report-template.md",
)

HYPOTHESIS_CONFIG_CANDIDATES = (
    "hypothesis-tracker.yaml",
)


def find_existing_path(directory: Path, candidates: tuple[str, ...]) -> Path | None:
    """Return the first candidate that exists in directory, or None."""
    for candidate in candidates:
        path = directory / candidate
        if path.is_file():
            return path
    return None


def preferred_path(directory: Path, candidates: tuple[str, ...]) -> Path:
    """Return the preferred (first) candidate path without checking existence."""
    return directory / candidates[0]


# Contract shared by all resolve_* helpers below:
# they return the first EXISTING candidate if one is found, otherwise the
# preferred (first) candidate path, WHICH MAY NOT EXIST. Callers that read the
# returned path must therefore check .is_file() / .exists() themselves (or be
# prepared to handle FileNotFoundError) before opening it.


def find_workspace_root(start_dir: Path) -> Path:
    current = start_dir.resolve()
    candidates = (current, *current.parents)
    for candidate in candidates:
        if (candidate / "workspace" / "workspace-config.md").is_file():
            return candidate
    for candidate in candidates:
        config_dir = candidate / CONFIG_DIRNAME
        if find_existing_path(config_dir, CONFIG_FILE_CANDIDATES):
            return candidate
    raise FileNotFoundError(
        "Could not locate workspace root from "
        f"{start_dir} by searching for config files"
    )


def resolve_config_dir(workspace_root: Path) -> Path:
    return workspace_root / CONFIG_DIRNAME


def resolve_config_path(config_dir: Path) -> Path:
    """Resolve the main config file; may return a non-existent preferred path."""
    return find_existing_path(config_dir, CONFIG_FILE_CANDIDATES) or preferred_path(
        config_dir, CONFIG_FILE_CANDIDATES
    )


def resolve_watchlist_path(config_dir: Path) -> Path:
    """Resolve the watchlist file; may return a non-existent preferred path."""
    return find_existing_path(config_dir, WATCHLIST_FILE_CANDIDATES) or preferred_path(
        config_dir, WATCHLIST_FILE_CANDIDATES
    )


def resolve_env_path(config_dir: Path) -> Path:
    """Resolve the env file; may return a non-existent preferred path."""
    return find_existing_path(config_dir, ENV_FILE_CANDIDATES) or preferred_path(
        config_dir, ENV_FILE_CANDIDATES
    )


def resolve_template_path(workspace_root: Path) -> Path:
    """Resolve the report template; may return a non-existent preferred path."""
    search_dirs = [
        workspace_root / "templates",
        Path(__file__).resolve().parent.parent / "templates",
    ]
    for templates_dir in search_dirs:
        existing = find_existing_path(templates_dir, TEMPLATE_FILE_CANDIDATES)
        if existing:
            return existing
    return preferred_path(search_dirs[0], TEMPLATE_FILE_CANDIDATES)


def resolve_hypothesis_dir(workspace_root: Path) -> Path:
    return workspace_root / HYPOTHESIS_DIRNAME


def resolve_portfolio_dir(workspace_root: Path) -> Path:
    return workspace_root / PORTFOLIO_DIRNAME


def resolve_journal_dir(workspace_root: Path) -> Path:
    return resolve_portfolio_dir(workspace_root) / JOURNAL_DIRNAME


def resolve_trades_path(workspace_root: Path) -> Path:
    return resolve_portfolio_dir(workspace_root) / "trades.csv"


def resolve_holdings_path(workspace_root: Path) -> Path:
    return resolve_portfolio_dir(workspace_root) / "holdings.csv"


def resolve_hypothesis_config_path(config_dir: Path) -> Path:
    """Resolve hypothesis-tracker config; may return a non-existent preferred path."""
    return find_existing_path(
        config_dir, HYPOTHESIS_CONFIG_CANDIDATES
    ) or preferred_path(config_dir, HYPOTHESIS_CONFIG_CANDIDATES)

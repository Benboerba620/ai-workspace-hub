#!/usr/bin/env python3
"""
Daily Watchlist + Hypothesis Tracker 环境检查。
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from io import StringIO
from pathlib import Path

from workspace_paths import (
    CONFIG_FILE_CANDIDATES,
    ENV_FILE_CANDIDATES,
    WATCHLIST_FILE_CANDIDATES,
    resolve_config_path,
    resolve_env_path,
    resolve_holdings_path,
    resolve_hypothesis_config_path,
    resolve_hypothesis_dir,
    resolve_journal_dir,
    resolve_trades_path,
    resolve_watchlist_path,
)

# Windows 控制台可能默认 cp1252/GBK，统一 UTF-8 输出避免中文触发 UnicodeEncodeError
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


OK = "[OK]"
FAIL = "[FAIL]"
WARN = "[WARN]"
PIP_INSTALL = f"{sys.executable} -m pip install"

CONFIG_EXAMPLE_MAPPINGS = {
    "daily-watchlist.example.yaml": "daily-watchlist.yaml",
    "daily-watchlist.env.example": "daily-watchlist.env",
    "daily-watchlist.watchlist.example.md": "daily-watchlist-watchlist.md",
    "hypothesis-tracker.example.yaml": "hypothesis-tracker.yaml",
    "hypothesis-tracker.rules.example.md": "hypothesis-tracker.rules.md",
}


def check(name: str, passed: bool, msg: str = "") -> bool:
    status = OK if passed else FAIL
    detail = f" - {msg}" if msg else ""
    print(f"  {status} {name}{detail}")
    return passed


def warn(name: str, msg: str = "") -> None:
    detail = f" - {msg}" if msg else ""
    print(f"  {WARN} {name}{detail}")


def load_env_file(env_file: Path) -> None:
    raw_text = env_file.read_text(encoding="utf-8-sig")
    try:
        from dotenv import dotenv_values

        parsed = dotenv_values(stream=StringIO(raw_text))
        for key, value in parsed.items():
            if value is not None and key not in os.environ:
                os.environ[key] = value
        return
    except ImportError:
        # check_setup.py must stay readable even before dependencies are installed.
        # This small fallback is enough for simple KEY=VALUE example env files.
        pass

    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def initialize_config(root: Path) -> list[Path]:
    examples_dir = Path(__file__).resolve().parent.parent / "config-examples"
    config_dir = root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    for source_name, target_name in CONFIG_EXAMPLE_MAPPINGS.items():
        source = examples_dir / source_name
        destination = config_dir / target_name
        if not destination.exists():
            shutil.copy2(source, destination)
            created.append(destination)
    # Working directories the checks below expect; create them up front so a
    # fresh workspace passes right after --init. (Directories are not added to
    # the returned list, which only tracks copied config files.)
    for directory in (
        resolve_hypothesis_dir(root),
        resolve_journal_dir(root),
    ):
        directory.mkdir(parents=True, exist_ok=True)
    return created


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--init",
        action="store_true",
        help="Copy missing example configuration files into config/ before checking",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print("Daily Watchlist + Hypothesis Tracker 环境检查\n")
    all_pass = True

    version = sys.version_info
    all_pass &= check(
        "Python >= 3.10",
        version >= (3, 10),
        (
            f"当前版本 {version.major}.{version.minor}.{version.micro}"
            if version >= (3, 10)
            else (
                f"当前版本 {version.major}.{version.minor}.{version.micro}；"
                "请改用 python3.10 / python3.11 / python3.12，或安装新版 Python"
            )
        ),
    )

    for pkg in ["requests", "dotenv", "yaml"]:
        try:
            __import__(pkg)
            check(f"依赖包 {pkg}", True)
        except ImportError:
            real_name = {"dotenv": "python-dotenv", "yaml": "pyyaml"}.get(pkg, pkg)
            all_pass &= check(f"依赖包 {pkg}", False, f"请执行 {PIP_INSTALL} {real_name}")

    script_dir = Path(__file__).resolve().parent
    try:
        from workspace_paths import find_workspace_root
        root = find_workspace_root(script_dir)
    except FileNotFoundError:
        root = Path.cwd()
        print(
            f"  {WARN} 未找到 workspace 根目录标记"
            "（workspace/workspace-config.md 或 config/ 配置文件），"
            f"退回使用当前目录：{root}"
        )
    if args.init:
        created = initialize_config(root)
        if created:
            print(f"已初始化 {len(created)} 个配置文件到 {root / 'config'}\n")
        else:
            print("配置文件已存在，没有覆盖。\n")
    config_dir = root / "config"
    env_file = resolve_env_path(config_dir)

    all_pass &= check(
        "config/ 目录",
        config_dir.exists(),
        "" if config_dir.exists() else "运行 check_setup.py --init 创建",
    )

    if not env_file.exists():
        all_pass &= check(
            f"config/{ENV_FILE_CANDIDATES[0]}",
            False,
            f"请创建 {ENV_FILE_CANDIDATES[0]} 并填入 API Key",
        )
    else:
        check(f"config/{env_file.name}", True)
        load_env_file(env_file)

        fmp_key = os.getenv("FMP_API_KEY", "")
        if not fmp_key or fmp_key.startswith("your_"):
            warn("FMP_API_KEY", "未配置（可选；美股会尝试 Nasdaq 无 Key 降级源）")
        else:
            try:
                import requests

                response = requests.get(
                    f"https://financialmodelingprep.com/api/v3/quote/AAPL?apikey={fmp_key}",
                    timeout=10,
                )
                data = response.json()
                if isinstance(data, list) and data and "symbol" in data[0]:
                    price = data[0].get("price", "?")
                    check("FMP_API_KEY", True, f"可用（AAPL = ${price}）")
                else:
                    all_pass &= check(
                        "FMP_API_KEY", False, f"返回异常：{str(data)[:100]}"
                    )
            except Exception as exc:  # noqa: BLE001
                all_pass &= check("FMP_API_KEY", False, f"连接失败：{exc}")

        ts_token = os.getenv("TUSHARE_TOKEN", "")
        if ts_token and not ts_token.startswith("your_"):
            try:
                import tushare as ts

                pro = ts.pro_api(ts_token)
                pro.trade_cal(
                    exchange="SSE", start_date="20260101", end_date="20260102"
                )
                check("TUSHARE_TOKEN", True, "可用")
            except ImportError:
                msg = (
                    f"已配置，但未安装 tushare"
                    f"（{PIP_INSTALL} -r tools/daily-watch/requirements-tushare.txt）"
                )
                warn("TUSHARE_TOKEN", msg)
            except Exception as exc:  # noqa: BLE001
                warn("TUSHARE_TOKEN", f"检查跳过：{exc}")
        else:
            warn("TUSHARE_TOKEN", "未配置（可选，仅 A 股/港股需要）")

    config_file = resolve_config_path(config_dir)
    if config_file.exists():
        check(f"config/{config_file.name}", True)
    else:
        all_pass &= check(
            f"config/{CONFIG_FILE_CANDIDATES[0]}",
            False,
            f"请创建 {CONFIG_FILE_CANDIDATES[0]}",
        )

    watchlist_file = resolve_watchlist_path(config_dir)
    if watchlist_file.exists():
        check(f"config/{watchlist_file.name}", True)
    else:
        all_pass &= check(
            f"config/{WATCHLIST_FILE_CANDIDATES[0]}",
            False,
            f"请创建 {WATCHLIST_FILE_CANDIDATES[0]} 或通过 /dw-import 生成",
        )

    hypothesis_config = resolve_hypothesis_config_path(config_dir)
    all_pass &= check(
        "config/hypothesis-tracker.yaml",
        hypothesis_config.exists(),
        "内置假设跟踪配置缺失" if not hypothesis_config.exists() else "",
    )

    hypothesis_dir = resolve_hypothesis_dir(root)
    all_pass &= check(
        "hypothesis/",
        hypothesis_dir.exists(),
        "" if hypothesis_dir.exists() else "运行 check_setup.py --init 创建，或手动 mkdir hypothesis",
    )

    journal_dir = resolve_journal_dir(root)
    all_pass &= check(
        "portfolio/journal/",
        journal_dir.exists(),
        ""
        if journal_dir.exists()
        else "运行 check_setup.py --init 创建，或手动 mkdir -p portfolio/journal",
    )

    trades_path = resolve_trades_path(root)
    if not trades_path.exists():
        warn("portfolio/trades.csv", "首次交易时自动创建")
    else:
        check("portfolio/trades.csv", True)

    holdings_path = resolve_holdings_path(root)
    if not holdings_path.exists():
        warn("portfolio/holdings.csv", "首次交易时自动创建")
    else:
        check("portfolio/holdings.csv", True)

    print()
    if all_pass:
        print(
            "所有必要检查已通过。现在可以运行 "
            "/dw-today、/ht-new、/ht-status、/ht-trade。"
        )
        return 0

    print("仍有未完成项，请按上面的提示修复后再运行。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

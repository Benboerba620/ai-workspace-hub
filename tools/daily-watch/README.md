# Daily Watch Tool

日报监控 + 假设追踪 + 交易记录工具。获取股票行情，生成每日报告，管理投资假设。

原始项目：[daily-watchlist](https://github.com/Benboerba620/daily-watchlist)

## 快速使用

以下命令默认使用 `python3`，且需要 Python 3.10+。先运行 `python3 --version`；如果版本低于 3.10，请改用 `python3.10` / `python3.11` / `python3.12`，或安装新版 Python。如果你的环境只有 `python` 且版本 ≥3.10，把命令里的 `python3` 替换成 `python` 即可。

```bash
# 环境检查
python3 tools/daily-watch/scripts/check_setup.py --init

# 生成日报
python3 tools/daily-watch/scripts/generate_daily_report.py

# 查询行情
python3 tools/daily-watch/scripts/fetch_market_data.py --profile NVDA,AAPL

# 假设状态
python3 tools/daily-watch/scripts/sync_hypothesis.py
```

## 依赖

```bash
python3 -m pip install -r tools/daily-watch/requirements.txt
```

使用 tushare 时再安装：`python3 -m pip install -r tools/daily-watch/requirements-tushare.txt`。

## 配置

示例文件在 `tools/daily-watch/config-examples/`，复制到 `config/` 后使用：

| 文件 | 用途 |
|------|------|
| `daily-watchlist.yaml` | 主配置（模块开关、阈值） |
| `daily-watchlist.env` | API key |
| `daily-watchlist-watchlist.md` | 股票池 |
| `hypothesis-tracker.yaml` | 假设追踪配置 |
| `hypothesis-tracker.rules.md` | 投资纪律 |

## 数据源

| 数据源 | 市场 | 费用 | 必要性 |
|--------|------|------|--------|
| tushare | A 股 | 按官方套餐 | A 股可选 |
| FMP | 全球 | 按官方套餐 | 全球数据可选 |
| Nasdaq | 美股基础行情 | 无 Key | 自动 fallback |
| Finnhub/EOD/yfinance | 各种 | 各自规则 | 可选 fallback |

无任何 API key 时，报告骨架仍然生成，行情数据标 `[待补充]`。

Longbridge Skill/CLI 是独立 Agent 扩展，不是本脚本的内置数据源。需要时按[官方说明](https://open.longbridge.com/zh-CN/skill/)另行安装和授权。

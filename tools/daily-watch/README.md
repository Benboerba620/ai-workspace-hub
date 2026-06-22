# Daily Watch Tool

日报监控 + 假设追踪 + 交易记录工具。获取股票行情，生成每日报告，管理投资假设。

原始项目：[daily-watchlist](https://github.com/Benboerba620/daily-watchlist)

## 快速使用

```bash
# 环境检查
python tools/daily-watch/scripts/check_setup.py

# 生成日报
python tools/daily-watch/scripts/generate_daily_report.py

# 查询行情
python tools/daily-watch/scripts/fetch_market_data.py --profile NVDA,AAPL

# 假设状态
python tools/daily-watch/scripts/sync_hypothesis.py
```

## 依赖

```bash
pip install -r tools/daily-watch/requirements.txt
```

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
| Longbridge | HK + US | 免费 | 推荐默认 |
| tushare | A 股 | 免费额度 | A 股必需 |
| FMP | 全球 | 免费 250 次/天 | 可选替代 |
| Stooq/Finnhub/EOD/yfinance | 各种 | 免费 | 自动 fallback |

无任何 API key 时，报告骨架仍然生成，行情数据标 `[待补充]`。

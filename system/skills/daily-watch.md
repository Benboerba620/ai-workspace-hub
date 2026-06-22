# Daily Watch（日报监控）

> 获取股票行情、检测异动、搜索新闻、生成每日结构化报告，并把证据回写到假设。
> 代码位于 `tools/daily-watch/`，原始项目 [daily-watchlist](https://github.com/Benboerba620/daily-watchlist)。

## 触发词

"今日日报" / "daily watchlist" / "盯盘日报" / "dw-today" / "生成日报"

## 前置条件

1. 安装依赖：`pip install -r tools/daily-watch/requirements.txt`
2. 配置文件（首次使用时从 `tools/daily-watch/config-examples/` 复制到 `config/`）：
   - `daily-watchlist.yaml` — 主配置
   - `daily-watchlist.env` — API key
   - `daily-watchlist-watchlist.md` — 股票池
   - `hypothesis-tracker.yaml` — 假设追踪配置
   - `hypothesis-tracker.rules.md` — 投资纪律
3. 在 `config/daily-watchlist.env` 填入至少一个数据源 key

Agent 首次使用时检查上述条件，缺什么补什么。

## 核心流程（dw-today）

1. 读取 `config/daily-watchlist.yaml` + `config/daily-watchlist-watchlist.md`
2. 运行数据脚本：
   ```bash
   python tools/daily-watch/scripts/generate_daily_report.py
   ```
3. 脚本输出报告骨架到 `daily-watchlist-reports/YYYY-MM/YYYY-MM-DD.md`
4. Agent 用 websearch 补充新闻：异动原因、财报反应、行业动态
5. Agent 扫描 `hypothesis/H*.md`，把当日发现关联到相关假设
6. 最终报告写入，更新 `workspace/meta/active-context.md`

## 数据源优先级

| 优先级 | 数据源 | 市场 | env key | 费用 |
|--------|--------|------|---------|------|
| 1 | Longbridge | HK + US | `LONGBRIDGE_APP_KEY` 等 | 免费 | [注册](https://open.longbridge.com/zh-CN/skill/) |
| 2 | tushare | A 股 (.SH/.SZ) | `TUSHARE_TOKEN` | 免费额度 | [注册](https://tushare.pro/register) |
| 3 | FMP | 全球 | `FMP_API_KEY` | 免费 250 次/天 | [注册](https://financialmodelingprep.com/) |
| 4+ | Stooq / Finnhub / EOD / yfinance | 各种 | 各自 key | 自动 fallback | — |

无任何 key → 报告骨架仍生成，行情数据标 `[待补充]`，agent 用 websearch 补充。

## 输出路径

| 输出 | 路径 |
|------|------|
| 日报 | `daily-watchlist-reports/YYYY-MM/YYYY-MM-DD.md` |
| 假设证据 | `hypothesis/H*.md`（回写） |
| 长期结论 | `wiki/explorations/`（可选沉淀） |

## 股票池格式

`config/daily-watchlist-watchlist.md` 是 markdown 表格：

```markdown
| Ticker | Name | Market | Market Cap | Category | Tier | Hypothesis | Notes |
|--------|------|--------|------------|----------|------|------------|-------|
| NVDA | NVIDIA | US | Mega | Semiconductor | HOT | H1 | AI GPU leader |
```

必需列：Ticker, Name, Market, Market Cap, Category
可选列：Tier, Hypothesis, Notes

## 异动阈值（可在 yaml 配置）

- 大盘股：±3%
- 小盘股：±7%

## 降级策略

| 缺少 | 行为 |
|------|------|
| 所有数据源 key | 生成骨架报告，行情数据标 `[待补充]` |
| websearch | 只输出数据表格，跳过新闻分析 |
| 假设文件 | 跳过假设关联段 |

## 冒烟测试

```bash
python tools/daily-watch/scripts/check_setup.py
```

# Daily Watch Tool

日报监控 + 假设追踪 + 交易记录工具。获取股票行情，生成每日报告，管理投资假设。

原始项目：[daily-watchlist](https://github.com/Benboerba620/daily-watchlist)

## 快速使用

以下命令默认使用 `python3`，且需要 Python 3.10+。先运行 `python3 --version`；如果版本低于 3.10，请改用 `python3.10` / `python3.11` / `python3.12`，或安装新版 Python。如果你的环境只有 `python` 且版本 >=3.10，把命令里的 `python3` 替换成 `python` 即可。

```bash
# 1. 安装依赖
python3 -m pip install -r tools/daily-watch/requirements.txt

# 2. 初始化配置（复制示例文件到 config/）
python3 tools/daily-watch/scripts/check_setup.py --init

# 3. 编辑 config/daily-watchlist.env，填入你的 API key（可选）

# 4. 生成日报
python3 tools/daily-watch/scripts/generate_daily_report.py

# 5. 查询指定股票 profile
python3 tools/daily-watch/scripts/fetch_market_data.py --profile NVDA,AAPL

# 6. 查看假设状态
python3 tools/daily-watch/scripts/sync_hypothesis.py
```

`check_setup.py --init` 会把 `config-examples/` 下的示例文件复制到 `config/`，已有的文件不会被覆盖。之后修改 `config/` 下的文件即可。

## 依赖

核心依赖：

```bash
python3 -m pip install -r tools/daily-watch/requirements.txt
```

包含 `requests`、`python-dotenv`、`pyyaml`。

A 股数据需要额外装 tushare：

```bash
python3 -m pip install -r tools/daily-watch/requirements-tushare.txt
```

## 目录结构

```
tools/daily-watch/
├── config-examples/          # 示例配置，--init 时复制到 config/
│   ├── daily-watchlist.example.yaml
│   ├── daily-watchlist.env.example
│   ├── daily-watchlist.watchlist.example.md
│   ├── hypothesis-tracker.example.yaml
│   └── hypothesis-tracker.rules.example.md
├── scripts/                  # 所有可执行脚本
│   ├── check_setup.py        # 环境检查 + 初始化
│   ├── generate_daily_report.py  # 生成日报（主入口）
│   ├── fetch_market_data.py  # 行情拉取 + 股票 profile
│   ├── fetch_macro_data.py   # 宏观数据（VIX/SPY/QQQ/GLD/WTI/BTC）
│   ├── sync_hypothesis.py    # 假设状态同步
│   ├── trade_stats.py        # 交易统计
│   └── workspace_paths.py    # 路径解析（被其他脚本引用）
└── templates/                # 报告模板
    ├── daily-watchlist-report-template.md
    ├── hypothesis-tracker-hypothesis-template.md
    ├── hypothesis-tracker-journal-template.md
    └── hypothesis-tracker-report-template.md
```

运行后在 workspace 根目录下生成：

```
config/                       # 实际配置文件（从 config-examples/ 复制）
daily-watchlist-reports/      # 生成的日报
  └── 2026-06/
      └── 2026-06-24.md
hypothesis/                   # 假设文件（H1.md, H2.md, ...）
portfolio/                    # 交易和持仓
  ├── trades.csv
  ├── holdings.csv
  └── journal/
```

## 配置

示例文件在 `tools/daily-watch/config-examples/`，运行 `check_setup.py --init` 复制到 `config/` 后使用：

| 文件 | 用途 |
|------|------|
| `daily-watchlist.yaml` | 主配置（模块开关、阈值、关注主题） |
| `daily-watchlist.env` | API key |
| `daily-watchlist-watchlist.md` | 股票池 |
| `hypothesis-tracker.yaml` | 假设追踪配置（确定性阈值、交易规则、风控） |
| `hypothesis-tracker.rules.md` | 投资纪律（文本，供假设决策参考） |

## 配置文件格式

主配置文件 `config/daily-watchlist.yaml`，所有字段均有默认值，可以只写需要改的部分。

### 最小配置

只需指定市场类型即可运行：

```yaml
market: us
```

### 完整配置

```yaml
# 市场类型：us / cn / hk / mixed
market: mixed

# 模块开关：关闭后对应章节不会拉取数据
modules:
  macro: true          # 宏观数据（VIX/SPY/QQQ/GLD/WTI/BTC）
  earnings: true       # 财报日历（需要 FMP key）
  focus_areas: true    # 重点主题
  wiki: auto           # wiki 联动

# 报告生成参数
reporting:
  model_profile: domestic    # default / domestic（选择 LLM profile）
  secondary_verify: true     # 国内模型时建议开启二次验证
  theme_min_score: 3         # 主题命中最低分
  theme_min_hits: 2          # 主题命中最低次数

# 异动阈值（涨跌幅超过此值的股票会进入"重点异动"）
thresholds:
  large_cap_move: 3    # 大盘股异动阈值 %
  small_cap_move: 7    # 中小盘股异动阈值 %

# 假设追踪
hypothesis_tracking:
  enabled: true
  directory: hypothesis        # 假设文件存放目录
  max_matches: 8               # 日报中最多展示的信号数
  auto_writeback: true         # 自动回写信号到假设文件的证据时间线
  suggest_new_hypothesis_threshold: 2  # 重复主题超过此数建议建立新假设

# 重点关注领域（最多 3 个）
focus_areas:
  - name: "AI 与数据中心"
    keywords: ["AI", "data center", "GPU", "inference", "LLM", "算力", "大模型"]
    required_any: ["AI", "data center", "GPU", "inference"]  # 至少命中一个才算
    exclude: ["airline", "ceasefire"]  # 排除关键词
```

**字段说明**：

- `thresholds`：用于自动识别异动股。大盘股（Market Cap = Large）用 `large_cap_move`，其余用 `small_cap_move`。
- `focus_areas.required_any`：假设必须命中其中至少一个关键词才会被归入该主题。不设则只看 `keywords`。
- `hypothesis_tracking.auto_writeback`：开启后，脚本会自动把当日触发的信号（异动、财报）追加到对应 `hypothesis/H*.md` 文件的"证据时间线"章节。

## 股票池格式

股票池文件 `config/daily-watchlist-watchlist.md` 是标准 Markdown 表格。按行业分组，每组一个二级标题 + 一张表。

### 格式要求

- 前五列（Ticker / Name / Market / Market Cap / Category）**必填**
- 后三列（Tier / Hypothesis / Notes）可选
- 每个行业分组用 `## 行业名` 作为二级标题，下面跟一张表
- 表头行和分隔行（`|---|---|`）必须有

### 示例

```markdown
## Technology
| Ticker | Name | Market | Market Cap | Category | Tier | Hypothesis | Notes |
|------|------|------|----------|------|------|------------|-------|
| NVDA | NVIDIA | US | Large | Technology | HOT | H1 | GPU supply chain bellwether |
| MSFT | Microsoft | US | Large | Technology | HOT | H1 | Cloud + AI infrastructure |
| AAPL | Apple | US | Large | Technology | WARM | H1 | AI device cycle / services |

## Energy
| Ticker | Name | Market | Market Cap | Category | Tier | Hypothesis | Notes |
|------|------|------|----------|------|------|------------|-------|
| XOM | Exxon Mobil | US | Large | Energy | WARM | H3 | Oil cycle monitor |
```

### 字段说明

| 字段 | 说明 | 取值 |
|------|------|------|
| Ticker | 股票代码 | 美股直接写 `NVDA`；A 股写 `601857.SH` / `000001.SZ`；港股写 `0700.HK` |
| Market | 市场 | `US` / `CN` / `HK` / `KR` / `FI` 等 |
| Market Cap | 市值分类 | `Large` / `Mid` / `Small`（影响异动阈值） |
| Category | 行业 | 任意文本，用于报告分组 |
| Tier | 监控热度 | `HOT`（重点）/ `WARM`（跟踪）/ `COLD`（基准） |
| Hypothesis | 关联假设 | 对应 `hypothesis/` 下的假设 ID，如 `H1`、`H2` |

**Ticker 后缀规则**：脚本用后缀判断数据源。`.SH`/`.SZ` 走 tushare（A 股），`.HK` 走 tushare（港股），无后缀默认走 FMP/Nasdaq（美股）。后缀必须大写。

## 输出示例

运行 `generate_daily_report.py` 后在 `daily-watchlist-reports/YYYY-MM/YYYY-MM-DD.md` 生成一份 Markdown 日报。

### 报告结构

```
# 每日监控简报 - 2026-06-24（星期二）

## 市场概览
VIX / SPY / QQQ / GLD / WTI / BTC 的当前价和涨跌幅表格
市场情绪摘要

## 个股异动
### 重点异动         ← 超过阈值的股票，附分类和摘要占位
### 其他异动         ← 涨跌幅排序的其他股票（前 5）

## 财报跟踪
### 已披露           ← 本周已出财报的 watchlist 股票
### 本周待披露       ← 本周即将出财报的 watchlist 股票

## 重点主题           ← 按 focus_areas 配置生成的主题区块

## 假设联动
### 已追踪假设概览   ← hypothesis/ 下所有假设的状态表
### 今日触发信号     ← 异动/财报/主题与假设的交叉命中
### 操作建议

## 信息来源           ← 本次拉取的数据源清单
```

报告由脚本生成数据骨架。新闻检索和原因分析部分是占位符，设计上由 Claude Code 通过 WebSearch 补充。

### 假设联动回写

开启 `auto_writeback` 后，如果当日有股票异动或财报事件命中了某条假设的关联标的，脚本会自动在对应 `hypothesis/H*.md` 的"证据时间线"章节下追加一条带日期戳的记录，格式如：

```
### 2026-06-24

- 🟡 **[DW-2026-06-24-mover-nvda] Daily Watchlist** - NVDA 今日涨跌幅 +4.52%，分类 Technology
  - 来源：daily-watchlist-reports/2026-06/2026-06-24.md
  - 影响：日报自动回写，待结合新闻后再决定是否调整确定性。
```

同一天同一信号不会重复写入（用 marker 去重）。

## 零 Key 运行

没有配置任何 API key 时（`daily-watchlist.env` 保持默认的 `your_*` 占位符），工具仍然可以运行：

- **美股**：自动 fallback 到 Nasdaq 无 Key 源，能拿到基础行情（最新价、涨跌幅）
- **宏观数据**：需要 FMP key，没有则宏观表格全部显示 `N/A`
- **A 股 / 港股**：需要 tushare token，没有则对应股票无数据
- **财报日历**：需要 FMP key，没有则财报章节为空
- **报告骨架**：无论有没有 key，报告文件都会生成，缺失的数据位显示 `N/A` 或 `[待补充]`

所以最低成本的试跑路径是：只放几只美股到 watchlist，不配任何 key，直接跑。

## 数据源

| 数据源 | 市场 | 费用 | 必要性 | env key |
|--------|------|------|--------|---------|
| FMP | 全球（行情 + 财报 + 宏观） | 按官方套餐 | 可选（全功能需要） | `FMP_API_KEY` |
| tushare | A 股（.SH/.SZ）、港股（.HK） | 按官方套餐 | A 股/港股需要 | `TUSHARE_TOKEN` |
| Nasdaq | 美股基础行情 | 无 Key | 自动 fallback（FMP 未返回时） | 无 |
| Finnhub | 美股 | 免费/付费 | 可选 fallback | `FINNHUB_API_KEY` |
| EOD | 港股、韩国、芬兰等 | 付费 | 可选 fallback | `EOD_API_KEY` |
| yfinance | 全球 | 无 Key | 可选 fallback（需额外安装） | `ENABLE_YFINANCE=true` |

**Fallback 顺序**（单只股票 FMP 未返回时）：Nasdaq → Finnhub → EOD → yfinance。每个源按 env key 是否配置自动决定是否尝试。

Longbridge Skill/CLI 是独立 Agent 扩展，不是本脚本的内置数据源。需要时按[官方说明](https://open.longbridge.com/zh-CN/skill/)另行安装和授权。

## 环境变量

配置文件 `config/daily-watchlist.env`：

```bash
# 可选：Financial Modeling Prep（全球行情、财报和宏观）
FMP_API_KEY=your_fmp_api_key

# 可选：Tushare Pro，用于 A 股（.SH/.SZ）和港股（.HK）
TUSHARE_TOKEN=your_tushare_token

# 备用行情源（全部可选）
FINNHUB_API_KEY=
EOD_API_KEY=
ENABLE_YFINANCE=
```

值为空或以 `your_` 开头的 key 会被自动跳过，不会触发 API 调用。

## 脚本说明

| 脚本 | 用途 | 输出 |
|------|------|------|
| `check_setup.py` | 检查 Python 版本、依赖包、配置文件、API 连通性 | 终端打印检查结果 |
| `check_setup.py --init` | 同上 + 把示例配置复制到 `config/` | 终端打印 + 创建文件 |
| `generate_daily_report.py` | 拉取行情 + 宏观 + 假设，生成日报 | JSON（`{"report_path": "..."}`）到 stdout |
| `fetch_market_data.py` | 拉取 watchlist 所有股票行情 + 异动 + 财报 | JSON 到 stdout |
| `fetch_market_data.py --profile NVDA,AAPL` | 查询指定股票的公司 profile | JSON 到 stdout |
| `fetch_macro_data.py` | 拉取宏观指标（VIX/SPY/QQQ/GLD/WTI/BTC） | JSON 到 stdout |
| `sync_hypothesis.py` | 扫描 hypothesis/ 下的假设文件，输出状态汇总 | 终端输出 |
| `trade_stats.py` | 读取 portfolio/trades.csv 计算交易统计 | 终端输出 |

所有数据脚本的结构化数据输出到 stdout（JSON），日志和警告输出到 stderr。

## 常见问题

### `python3` 不是内部或外部命令

Windows 上通常只有 `python`。确认版本 >= 3.10 后把所有命令里的 `python3` 换成 `python`：

```bash
python --version          # 确认 >= 3.10
python tools/daily-watch/scripts/check_setup.py --init
```

### tushare 返回 500 错误

通常是 token 权限不够。tushare 的部分接口需要积分。到 [tushare 个人中心](https://tushare.pro/user/token) 检查积分和接口权限。`daily_basic`（用于 A 股市值）需要 120 积分以上。

### 某只股票没有数据返回

按以下顺序排查：

1. **Ticker 格式**：A 股必须带后缀（`601857.SH` 不是 `601857`），港股必须带 `.HK`（`0700.HK` 不是 `700`），后缀必须大写
2. **数据源**：A 股 / 港股需要 tushare token；纯美股无 key 时 Nasdaq 源能覆盖大部分
3. **非交易时间**：脚本取最近 5-10 个交易日的数据，周末和假日也能拿到最近一个交易日的数据
4. **FMP 限流**：免费 plan 有 250 次/天的限制，股票池太大时会被截断

### 找不到配置文件

```
Error: Could not locate workspace root
```

脚本从自身位置向上查找包含 `config/daily-watchlist.yaml` 或 `workspace/workspace-config.md` 的目录作为 workspace 根。确保：

1. 已运行 `check_setup.py --init` 生成 `config/` 目录
2. 从 workspace 根目录（或其子目录）运行脚本

### 报告中数据全是 N/A

说明所有数据源都没有返回有效数据。运行 `check_setup.py` 看哪些源是通的：

```bash
python3 tools/daily-watch/scripts/check_setup.py
```

输出会逐项标注 `[OK]` / `[FAIL]` / `[WARN]`，包括 FMP key 连通性测试和 tushare token 验证。

# Workspace Config

> 这个文件描述当前项目是什么、材料在哪里、输出写哪里。它是项目级配置，不是全局人格设定。

## 项目定位

- name: `MY_AI_WORKSPACE`
- primary_use: `research / writing / investing / podcast / mixed`
- language: `zh-CN`

## 核心目录

| 目录 | 用途 |
|---|---|
| `inbox/` | 临时输入材料 |
| `wiki/raw/` | 原始材料归档 |
| `wiki/sources/` | 结构化来源页面 |
| `wiki/entities/` | 公司、人、项目等实体 |
| `wiki/concepts/` | 概念和主题 |
| `wiki/explorations/` | 综合判断和阶段性结论 |
| `output/` | 报告、日报、文章草稿等输出 |
| `monitoring/` | 用户阅读的监控看板，不驱动日报 |
| `hypothesis/` | 假设、证据引用和复盘 |
| `evidence/` | 独立证据账本，保存来源、方向和审核状态 |
| `daily-watchlist-reports/` | 日报输出 |
| `portfolio/` | 交易记录 |
| `config/` | 用户配置文件（不入 git） |
| `tools/` | 内置工具代码 |
| `system/` | 机器零件箱 |
| `workspace/meta/` | active-context 和 friction-log |
| `workspace/patterns/` | 跨案例可迁移模式，用短索引按结构特征加载 |
| `workspace/review-queue.md` | 需要用户确认后才能生效的动作 |
| `workspace/research-profile.md` | 从真实研究中学习的用户研究偏好 |

## 输出约定

所有输出都要尽量包含：

1. 核心结论
2. 关键证据
3. 反方证据
4. 待验证问题
5. 下一步动作

## 数据标注

涉及事实或数字时，标注来源：

- `[本地]` 来自本地文件
- `[网页]` 来自联网资料
- `[tushare]` / `[FMP]` 来自日报脚本 API；`[Longbridge Skill]` 来自独立 Agent 扩展
- `[推测]` agent 的推理
- `[待验证]` 尚未确认

## 简单规则

1. 输入材料时，先按 `wiki/_schema.md` 分类。
2. 研究、分析、写作或输出时，先查 `workspace/meta/active-context.md`、`wiki/explorations/_index.md`、`workspace/patterns/_index.md` 和相关 wiki 文件；输出里保留一行 `Wiki check`。
3. 遇到路径不清、规则不清、工具缺失或重复绕路时，写入 `workspace/meta/friction-log.md`。

对象 ID、frontmatter 当前状态和待确认队列统一遵循 `system/integrations/object-model.md`。

## 内置核心

### personal wiki

- status: `enabled`
- wiki_root: `./wiki`
- source_schema: `karpathy-claude-wiki compatible`
- reads_from:
  - `wiki/raw/`
- writes_to:
  - `wiki/sources/`
  - `wiki/entities/`
  - `wiki/concepts/`
  - `wiki/explorations/`
- loading_indexes:
  - `wiki/explorations/_index.md`
  - `workspace/patterns/_index.md`
- distillation: `source -> exploration -> pattern -> rule`

### research（研究闭环）

- status: `enabled`（基座能力，wiki + websearch 零依赖起步）
- skill: `system/skills/research.md`
- profile: `workspace/research-profile.md`（首次研究生成 v0.1，至少 3 次后再固化模板）
- inputs: `wiki/` + `websearch` + `data_sources`（可选）
- writes_to: `output/research/` → 确认后回写 `wiki/explorations/`
- focus_points: 默认 `业务/驱动因子, 竞争格局, 关键数据, 风险, 催化剂`（按需自定义）

### screen（快速筛选）

- status: `enabled`（基座能力，websearch + 可选数据源）
- skill: `system/skills/screen.md`
- inputs: `websearch` + `data_sources`（可选）
- writes_to: `output/screen/`
- presets: `价值股` / `AI产业链`

### 假设追踪（基座自带，无需安装）

- status: `enabled`
- 契约: `system/integrations/hypothesis-tracker.md`
- reads_from:
  - `hypothesis/`
  - `wiki/`
- writes_to:
  - `hypothesis/`
  - `wiki/explorations/`

## 内置工具

### podcast（播客/博客摄入）

- status: `enabled`
- skill: `system/skills/podcast.md`
- project_path: `./tools/podcast`
- writes_to:
  - `wiki/sources/`
  - `wiki/raw/podcasts/`
  - `output/pod2wiki/`

### daily-watch（日报监控）

- status: `enabled`
- skill: `system/skills/daily-watch.md`
- project_path: `./tools/daily-watch`
- reads_from:
  - `config/daily-watchlist-watchlist.md`
  - `wiki/entities/`
  - `wiki/concepts/`
- writes_to:
  - `daily-watchlist-reports/`
  - `evidence/`
  - `hypothesis/`（只追加证据引用，不自动改变状态）

## 数据源（配了才用，没配降级不报错）

> key 走环境变量或 `config/*.env`，不要写进 repo。没配的字段 agent 会标 `[待验证]` 而不是编造。

### longbridge-skill（外部 Agent 扩展）

- status: `optional-external`
- auth: 独立安装后通过 Longbridge CLI / MCP 授权，不读取 `config/*.env`
- markets: 以 Longbridge 官方当前支持范围为准
- used_by: `screen`, `research`
- note: 不是 `tools/daily-watch/` 的内置数据源
- 安装方式: https://open.longbridge.com/zh-CN/skill/

### tushare（A 股行情 / 财务）

- status: `available-unconfigured`
- env_key: `TUSHARE_TOKEN`
- markets: CN (.SH/.SZ), HK (.HK)
- used_by: `daily-watch`, `screen`, `research`
- 获取方式: https://tushare.pro/register

### fmp（可选：全球行情 / 财报 / 宏观）

- status: `available-unconfigured`
- env_key: `FMP_API_KEY`
- markets: US, HK, EU, JP, CN
- used_by: `daily-watch`, `screen`, `research`
- pricing: 以 FMP 官方当前套餐为准
- 获取方式: https://financialmodelingprep.com/

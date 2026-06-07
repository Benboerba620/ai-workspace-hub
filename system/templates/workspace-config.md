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
| `monitoring/` | 监控对象和看板 |
| `hypothesis/` | 假设、证据、复盘 |
| `system/interfaces/` | 已部署模块的接口总览 |
| `system/integrations/` | 模块接入契约（含 `_template.md`） |
| `system/skills/` | 能力说明书（含 `_template.md`） |
| `workspace/meta/` | active-context 和 friction-log |

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
- `[推测]` agent 的推理
- `[待验证]` 尚未确认

## 简单规则

1. 输入材料时，先按 `wiki/_schema.md` 分类。
2. 研究、分析、写作或输出时，先查 `workspace/meta/active-context.md` 和相关 wiki 文件；输出里保留一行 `Wiki check`。
3. 遇到路径不清、规则不清、工具缺失或重复绕路时，写入 `workspace/meta/friction-log.md`。

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

### research（研究闭环）

- status: `enabled`（基座能力，wiki + websearch 零依赖起步）
- skill: `system/skills/research.md`
- inputs: `wiki/` + `websearch` + `data_sources`（可选）
- writes_to: `output/research/` → 确认后回写 `wiki/explorations/`
- focus_points: 默认 `业务/驱动因子, 竞争格局, 关键数据, 风险, 催化剂`（按需自定义）

## 可选数据源（research 外挂，配了才用）

> 接入照 `system/integrations/_template.md`；key 走环境变量，不要写进 repo。没配的字段 research 会标 `[待验证]`。

### tushare（示例：A股行情 / 财务）

- status: `planned`
- env_key: `TUSHARE_TOKEN`
- used_by: `system/skills/research.md`

## 外挂项目

### pod2wiki

- status: `optional` / `enabled` / `planned`
- project_path:
- writes_to:
  - `wiki/sources/`
  - `wiki/raw/podcasts/`
  - `output/pod2wiki/`

### daily-watchlist

- status: `planned`
- project_path:
- reads_from:
  - `monitoring/`
  - `wiki/entities/`
  - `wiki/concepts/`
- writes_to:
  - `output/daily-watchlist/`
  - `hypothesis/`

### hypothesis-tracker

- status: `planned`
- project_path:
- reads_from:
  - `hypothesis/`
  - `wiki/`
- writes_to:
  - `hypothesis/`
  - `wiki/explorations/`

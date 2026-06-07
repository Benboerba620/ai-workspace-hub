# Workspace Config

> 这是最小可运行配置。目标不是完整投研系统，而是让 Codex / Claude 能直接试跑一条输入 -> personal wiki 的路径。

## 项目定位

- name: `ai-workspace-hub`
- primary_use: `research / writing / investing / podcast / mixed`
- language: `zh-CN`

## 核心目录

| 目录 | 用途 |
|---|---|
| `inbox/` | 临时输入材料 |
| `wiki/raw/` | 原始材料归档 |
| `wiki/sources/` | 结构化来源页面 |
| `wiki/entities/` | 实体档案 |
| `wiki/concepts/` | 概念和主题 |
| `wiki/explorations/` | 综合判断 |
| `output/` | 报告、日报、文章草稿 |
| `monitoring/` | 监控对象 |
| `hypothesis/` | 假设、证据、复盘 |
| `system/interfaces/` | 已部署模块的接口总览 |
| `system/integrations/` | 模块接入契约（含 `_template.md`） |
| `system/skills/` | 能力说明书（含 `_template.md`） |
| `workspace/meta/` | active-context 和 friction-log |

## 简单规则

1. 输入材料时，先按 `wiki/_schema.md` 分类。
2. 研究、分析、写作或输出时，先查 `workspace/meta/active-context.md` 和相关 wiki 文件；输出里保留一行 `Wiki check`。
3. 遇到路径不清、规则不清、工具缺失或重复绕路时，写入 `workspace/meta/friction-log.md`。

## 内置核心

### personal wiki

- status: `enabled`
- wiki_root: `./wiki`
- source_schema: `karpathy-claude-wiki compatible`
- schema_file: `wiki/_schema.md`
- raw_dir: `wiki/raw/`
- sources_dir: `wiki/sources/`
- entities_dir: `wiki/entities/`
- concepts_dir: `wiki/concepts/`
- explorations_dir: `wiki/explorations/`

### research（研究闭环）

- status: `enabled`（基座能力，wiki + websearch 零依赖起步）
- skill: `system/skills/research.md`
- inputs: `wiki/` + `websearch` + `data_sources`（可选）
- writes_to: `output/research/` → 确认后回写 `wiki/explorations/`
- focus_points: 默认 `业务/驱动因子, 竞争格局, 关键数据, 风险, 催化剂`（按需自定义这一行）

## 可选数据源（research 外挂，配了才用）

> 接入照 `system/integrations/_template.md`；key 走环境变量，**不要**写进 repo。没配的字段 research 会标 `[待验证]`。

### tushare（示例：A股行情 / 财务）

- status: `planned`
- env_key: `TUSHARE_TOKEN`
- used_by: `system/skills/research.md`

### gangtise（示例：卖方纪要）

- status: `planned`
- env_key: `GANGTISE_API_KEY`
- used_by: `system/skills/research.md`

## 可选模块

> 一键部署见 `system/skills/deploy-modules.md`（"帮我安装博客抓取 / 日报监控 / 假设追踪"）。

### pod2wiki（博客 / 播客抓取，输入槽）

- status: `planned`
- repo: `https://github.com/Benboerba620/pod2wiki`
- project_path: `./pod2wiki`
- writes_to:
  - `wiki/sources/`
  - `wiki/raw/podcasts/`
  - `output/pod2wiki/`

### daily-watchlist（日报监控，输出槽）

- status: `planned`
- repo: `https://github.com/Benboerba620/daily-watchlist`
- project_path: `./daily-watchlist`
- reads_from:
  - `monitoring/`
  - `wiki/entities/`
  - `wiki/concepts/`
- writes_to:
  - `output/daily-watchlist/`
  - `hypothesis/`

### hypothesis-tracker（假设追踪，决策层）

- status: `planned`
- repo: `https://github.com/Benboerba620/hypothesis-tracker`
- project_path: `./hypothesis-tracker`
- reads_from:
  - `hypothesis/`
  - `wiki/`
- writes_to:
  - `hypothesis/`
  - `wiki/explorations/`

## 可选能力

### pdf-ingest

- status: `available`（按需自装）
- slot: `input`
- skill: `system/skills/pdf-ingest.md`
- script: `system/scripts/pdf_to_md.py`
- deps: `requirements-pdf.txt`（pypdf，agent 首次执行时自装）

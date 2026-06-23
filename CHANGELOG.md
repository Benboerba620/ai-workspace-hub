# Changelog

## Unreleased

### 修复

- 新增标准库安装器，安装协议明确先取得源码；非空目标默认停止，`--merge` 只补缺失文件、不覆盖用户资料。
- 修复 all-in-one 工作区在配置文件创建前无法识别根目录的问题，`check_setup.py --init` 可安全初始化缺失配置。
- 更正 Longbridge 定位：它是独立 Agent Skill/CLI/MCP，不再宣称为 daily-watch Python 脚本的内置环境变量数据源。
- `faster-whisper` 拆到可选的 `requirements-transcribe.txt`，避免基础播客安装拉取重型转录依赖。
- LLM 环境变量优先于示例 YAML；摘要全部失败时返回非零状态，不再静默报告成功。
- 新增安装、路径、文档链接和仓库契约测试，以及 Python 3.10/3.12 CI。

## 0.3.0 - 2026-06-22

### 新增

- **All-in-One 集成**：pod2wiki（播客/博客摄入）和 daily-watchlist（日报监控）代码合并进 `tools/podcast/` 和 `tools/daily-watch/`，一次 clone 拿到全部六大能力。原始独立 repo 继续存在。
- **screen 快速筛选**（基座能力）：给定主题 → websearch 候选 → 拉数据 → 过滤 → 表格 + Top 5 分析。内置两个预设模板（价值股 / AI 产业链）。无 API 时降级为纯 websearch。
- **Longbridge 数据源**：新增 Longbridge 为默认免费数据源（HK + US 行情），与 tushare（A 股）并列为零成本起步选项。FMP 降为付费可选。
- **统一 config/ 目录**：所有工具的用户配置文件统一放在 `config/`（不入 git）。

### 改进

- **README 重写**：从"最小种子 + 槽位"改为"all-in-one 六大能力"。
- **INSTALL 简化**：移除"选模块"步骤，全量安装是唯一路径。
- **ARCHITECTURE 更新**：架构图和目录结构反映 tools/ + 数据源层。
- **AGENTS.md / CLAUDE.md 路由表扩展**：新增 podcast、daily-watch、screen 三条路由。
- **workspace-config 更新**：新增数据源段（Longbridge/tushare/FMP）+ screen 能力 + podcast/daily-watch 内置登记。

### 移除

- `system/skills/deploy-modules.md`（不再需要 clone 外部模块）。
- 文档中"外部模块 clone"流程和相关引导。

## 0.2.4 - 2026-06-22

### 修复

- **INSTALL 路径补上试跑材料**：走 `INSTALL-FOR-AI.md` 安装的用户 `inbox/` 是空的，README「直接试跑」段引用的 `first-note.md` 不存在导致跑不通。现在 Step 2 复制清单包含 `inbox/first-note.md`，两条安装路径都能直接试跑。

## 0.2.3 - 2026-06-07

### 改进

- **active-context 上限与自动清理**：给断点续传协议补上"内联自动剪"。agent 写断点时自检「最近对话延续」段，把**超过 14 天或超过 20 条**的旧条目整行移到 `workspace/meta/active-context-archive-YYYY-MM.md`（保留续接锚点）——零脚本、自动执行、不等手动体检。`structure-health` 的 active-context 检查改为**周度兜底**（万一内联没剪到位才点出来），并对齐归档路径。

## 0.2.2 - 2026-06-07

### 改进

- **active-context 断点续传协议落地**：把"今天停、明天接"做成 agent 自动行为，不再只是格式说明。AGENTS / CLAUDE（含 `system/templates/`）新增「active-context：断点续传」段，写明两条自动触发规则——① 开场说"继续 / 接着 / 昨天"→ 自动读 `active-context.md` 顺着「续接锚点」接上；② 用户说"今天到此 / 明天继续 / 暂停"或工作落盘 / 做决策 / 长对话收尾 → 自动追一行（含状态标签 `PAUSED` / `DONE` / `决策` + 续接锚点）。`active-context.md`（含模板）头部说明与段名同步为 `## 最近对话延续`，README 增加大白话说明。

## 0.2.1 - 2026-06-07

### 改进

- **假设追踪改为基座自带能力**：不再当作"要另装的外部模块"。`hypothesis/` 目录记假设与证据（一假设一 `H*.md`），复盘结论回写 `wiki/explorations/`，开箱即用、零依赖、无需安装。README / AGENTS / CLAUDE / ARCHITECTURE / INSTALL 全量改为「内置」口径。

### 修复

- 移除文档中指向已转为私有的 `hypothesis-tracker` repo 的失效链接，以及"帮我安装假设追踪"的部署引导（deploy-modules 触发词、workspace-config 模块登记、interfaces 契约同步清理）。

## 0.2.0 - 2026-06-07

### 新增

- **research 研究闭环**（基座自带能力，零依赖起步）：输入源 = `wiki/` + websearch + 可选数据源（tushare / gangtise / 自有 API，key 走环境变量）；按研究要点模板输出到 `output/research/`，每条事实标来源（`[本地]` / `[网页]` / `[推测]` / `[待验证]`）；讨论升级后主动提示"是否沉淀进 wiki"，确认后回写 `wiki/explorations/`，形成闭环。见 `system/skills/research.md`。
- **ARCHITECTURE.md**：架构图（基座 + 槽位 + 维护）+ 文件夹结构图 + 完整闭环图。

### 改进

- **结构精简**：把机械零件（`skills/` `integrations/` `scripts/` `interfaces/` `templates/`）统一收进 `system/`，顶层目录 13 → 8，新人一眼能分清"自己读的"和"agent 用的"。
- **防臃肿加固**：`structure-health` 不再把 `status: planned` 模块的未来输出目录误报为"缺失"；`post-install-cleanup` 增加"瘦身后清扫归档样例残留引用"的步骤，避免死链。

### 文档

- README / INSTALL-FOR-AI 全量同步到 `system/` 路径；README 增加「研究闭环」示例段、「最近更新」段，以及「安装到你自己的工作区」段（首次把 `INSTALL-FOR-AI.md` 链进 README）。

## 0.1.0 - 2026-06-06

- Initial Codex-first, Claude-compatible starter workspace.
- Added personal wiki core with `wiki/_schema.md`.
- Added first-ingest smoke test.
- Added PDF ingest smoke path with optional Python + pypdf path.
- Added simple workspace rules in `workspace/workspace-config.md`.

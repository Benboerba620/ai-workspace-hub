# Changelog

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

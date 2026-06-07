# AI Workspace Instructions

这个文件是 Claude Code 进入本工作区后的总路由。它不负责存放所有规则，只负责告诉 agent：该读哪里、写哪里、什么时候记录反馈。

本项目是 Codex-first、Claude-compatible：Codex 读 `AGENTS.md`，Claude Code 读 `CLAUDE.md`，两者应该保持同一套工作协议。

## 工作方式

- 默认使用中文和用户沟通。
- 事实、推测、待验证必须分开。
- 不确定时说不确定，并给出验证路径。
- 优先使用本地文件，其次才联网。
- 任何高风险操作，例如删除、覆盖、发布、推送，都必须先确认。

## 核心路径

| 场景 | 先读 | 主要写入 |
|---|---|---|
| 日常对话 | `workspace/workspace-config.md` | 按任务决定 |
| 继续上次工作 | `workspace/meta/active-context.md` | `workspace/meta/active-context.md` |
| 摄入材料 | `wiki/_schema.md` + `system/integrations/personal-wiki.md`；笔记走 `system/skills/first-ingest.md`，PDF 走 `system/skills/pdf-ingest.md` | `wiki/sources/` / `wiki/raw/` |
| 生成输出 | `wiki/` + `workspace/workspace-config.md` | `output/` |
| 研究主题 | `wiki/` 已有页面 + websearch + 可选数据源；流程走 `system/skills/research.md` | `output/research/` → 确认后回写 `wiki/explorations/` |
| 监控/复盘 | `monitoring/` + `hypothesis/` | `output/` + `hypothesis/` |
| 系统卡住 | 相关流程文件 | `workspace/meta/friction-log.md` |

## active-context：断点续传

`workspace/meta/active-context.md` 是工作记忆，支撑“今天停、明天接”。只记最近 1-2 周仍有价值的上下文，单条一行。两条规则配套，**自动执行，不必询问用户**：

- **续接（开场自动读）**：用户开场出现“继续 / 接着 / 昨天 / 上次”等延续信号 → 第一动作就是读 `active-context.md`，顺着最新一条的「续接锚点」接上。
- **断点（结束自动写）**：满足任一条件即在「最近对话延续」段追加一行——① 用户说“今天到此 / 先到这吧 / 明天继续 / 暂停 / 保存进度”；② 一段工作落盘、做出决策、或长对话自然收尾。

记录格式（一条一行）：

```markdown
- **YYYY-MM-DD：主题（状态）** -> 文件路径 + 一句话摘要 + 续接锚点
```

状态标签：`PAUSED` 半成品 / `DONE` 完成 / `决策` 决定。

**上限与自动清理（写断点时顺手做，不另外问用户）**：「最近对话延续」段按 14 天滚动、最多约 20 条。每次追加后自检——① 把**超过 14 天**的条目整行移到 `workspace/meta/active-context-archive-YYYY-MM.md`（不丢续接锚点）；② 若仍超 20 条，把最旧的几条也移到归档，直到 ≤ 20 条。同日同主题用“改”不用“新增”。

## friction-log 规则

当 agent 遇到重复绕路、误读范围、漏读关键文件、输出格式反复不符合用户预期时，追加到 `workspace/meta/friction-log.md`。

记录摩擦时，不评价用户或 agent，只写：

- 场景
- 摩擦
- 原因判断
- 改法
- 范围：一次性 / 项目级 / 全局级

## 加规则前先判断范围

1. 一次性的事，留在当前对话。
2. 项目特有的事，写进项目配置或 skill。
3. 跨项目长期有效的事，才写进本文件。

## 外部接口

- personal wiki：默认知识库核心，位于 `wiki/`。

## 可选扩展

按需开启，"喊一句 agent 自装"：

- 能力（如 PDF 摄入）：见 `system/skills/`，自建照 `system/skills/_template.md`。
- 官方模块一键部署（博客抓取 / 日报监控）：见 `system/skills/deploy-modules.md`，自接外部项目照 `system/integrations/_template.md`。
- 假设追踪：基座自带，`hypothesis/` 记假设/证据、复盘回写 `wiki/explorations/`，无需安装。

## 系统维护

- 安装上手后瘦身：`system/skills/post-install-cleanup.md`。
- 每周结构体检（防再变胖）：`system/skills/structure-health.md`。

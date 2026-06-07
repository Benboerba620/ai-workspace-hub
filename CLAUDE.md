# AI Workspace Instructions

这个 repo 本身就是一个最小可运行的 AI research workspace。Claude Code 进入本目录后，先读本文件，再读 `workspace/workspace-config.md`。

本文件与 `AGENTS.md` 保持**同一套工作协议**（Codex-first、Claude-compatible）。两者内容应当同源，改一个就同步另一个。

## 工作方式

- 默认使用中文。
- 事实、推测、待验证必须分开。
- 优先使用本地文件。
- 删除、覆盖、发布、推送前必须确认。

## 核心路由

简单优先：先读 `workspace/workspace-config.md`。非简单任务按其中“三条简单规则”执行。

| 场景 | 先读 | 主要写入 |
|---|---|---|
| 开始工作 | `workspace/workspace-config.md` | 按任务决定 |
| 继续上下文 | `workspace/meta/active-context.md` | `workspace/meta/active-context.md` |
| 摄入材料 | `wiki/_schema.md` + `system/integrations/personal-wiki.md`；笔记走 `system/skills/first-ingest.md`，PDF 走 `system/skills/pdf-ingest.md` | `wiki/raw/` / `wiki/sources/` / `wiki/concepts/` / `wiki/explorations/` |
| 生成输出 | `workspace/meta/active-context.md` + 相关 `wiki/` 文件 | `output/` |
| 研究主题 | `wiki/` 已有页面 + websearch + 可选数据源；流程走 `system/skills/research.md` | `output/research/` → 确认后回写 `wiki/explorations/` |
| 监控/复盘 | `monitoring/` + `hypothesis/` | `output/` + `hypothesis/` |
| 遇到摩擦 | 相关文件 | `workspace/meta/friction-log.md` |

## active-context：断点续传

`workspace/meta/active-context.md` 是工作记忆，支撑“今天停、明天接”。只记最近 1-2 周仍有价值的上下文，单条一行。两条规则配套，**自动执行，不必询问用户**：

- **续接（开场自动读）**：用户开场出现“继续 / 接着 / 昨天 / 上次”等延续信号 → 第一动作就是读 `active-context.md`，顺着最新一条的「续接锚点」接上，不要让用户重新交代上下文。
- **断点（结束自动写）**：满足任一条件即在「最近对话延续」段追加一行——① 用户说“今天到此 / 先到这吧 / 明天继续 / 暂停 / 保存进度”；② 一段工作落盘、做出决策、或长对话自然收尾。

格式（一条一行）：

```markdown
- **YYYY-MM-DD：主题（状态）** -> 文件路径 + 一句话摘要 + 续接锚点
```

状态标签：`PAUSED` 半成品 / `DONE` 完成 / `决策` 决定。纪律：同日同主题用“改”不用“新增”；过期条目剪到归档，别让文件无限长。

## 最小试跑（基座，零依赖）

用户可以直接说：

> 把 `inbox/first-note.md` 整理进 personal wiki。

Claude 应该创建一篇 `wiki/sources/YYYY-MM-DD-first-note.md`，并在 `workspace/meta/active-context.md` 记录本次试跑结果。这条链路只读写 markdown，不需要安装任何依赖。

## 可选能力（喊一句，agent 自己装）

基座之外的能力按需开启，Claude 读对应 skill 后自行安装依赖，不需要用户预先配置环境。例如 PDF：

> 帮我开启 PDF 摄入，把 `inbox/sample-ai-workspace.pdf` 整理进 wiki。

Claude 读 `system/skills/pdf-ingest.md` → 自检并 `pip install pypdf` → 跑 `python system/scripts/pdf_to_md.py` → 按 `wiki/_schema.md` 摄入。

## 模块与槽位

基座预留两类槽位，"接现成项目"和"自己 DIY"长同一个样（skill + 可选 script + 在 `workspace-config` 登记一行）。新增模块照 `system/skills/_template.md` 和 `system/integrations/_template.md` 抄。

官方模块一键部署：用户说"帮我安装博客抓取 / 日报监控" → 执行 `system/skills/deploy-modules.md`（git clone + 接线到 wiki）。

- personal wiki：默认核心，位于 `wiki/`。
- research（研究闭环）：基座能力，wiki + websearch 零依赖起步，见 `system/skills/research.md`。
- 假设追踪：基座自带，`hypothesis/` 记假设与证据（一假设一 `H*.md`），复盘结论回写 `wiki/explorations/`，不需要装模块，契约见 `system/integrations/hypothesis-tracker.md`。
- pdf-ingest：输入能力，参考样板，见 `system/skills/pdf-ingest.md`。
- pod2wiki（博客/播客抓取）：可选输入模块，见 `system/integrations/pod2wiki.md`。
- daily-watchlist（日报监控）：可选输出模块，见 `system/integrations/daily-watchlist.md`。

## 系统维护（防臃肿）

- 装好上手后一次性瘦身：`system/skills/post-install-cleanup.md`（清安装脚手架 + 精简必读文件）。
- 每周结构体检、给精简建议：`system/skills/structure-health.md`。

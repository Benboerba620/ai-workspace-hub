# AI Workspace Instructions

这个 repo 是一个 all-in-one AI 研究工作系统，包含六大能力。Codex 进入本目录后，先读本文件，再读 `workspace/workspace-config.md`。

本文件与 `CLAUDE.md` 保持**同一套工作协议**。两者内容应当同源，改一个就同步另一个。研究对象、状态和 ID 统一遵循 `system/integrations/object-model.md`。

## 工作方式

- 默认使用中文。
- 事实、推测、待验证必须分开。
- 优先使用本地文件。
- 删除、覆盖、发布、推送前必须确认。

## 核心路由

先读 `workspace/workspace-config.md`。非简单任务按其中"三条简单规则"执行。

路径约定：本文件和各 skill 中的 `wiki/` 是默认示例。若 `workspace-config.md` 的 `wiki_root` 不是 `./wiki`，所有 wiki 读写都以配置值为根目录，不要同时写入本地 `wiki/`。

| 场景 | 先读 | 主要写入 |
|---|---|---|
| 开始工作 | `workspace/workspace-config.md` | 按任务决定 |
| 继续上下文 | `workspace/meta/active-context.md` | `workspace/meta/active-context.md` |
| 查看当前待办 | `system/skills/workspace-status.md` + `workspace/review-queue.md` | 只读汇总，不修改判断 |
| 升级工作区 | `system/skills/upgrade-workspace.md` | 先预览，确认后只更新受管文件 |
| 摄入材料 | `wiki/_schema.md` + `system/integrations/personal-wiki.md`；笔记走 `system/skills/first-ingest.md` 并自动打标签，PDF 走 `system/skills/pdf-ingest.md` | `wiki/` |
| 首次股票研究 | `system/skills/first-research.md` + `workspace/research-profile.md` | `output/research/` + 研究偏好 v0.1 |
| 后续研究 | `workspace/research-profile.md` + `system/skills/research.md` + 两个知识索引；结束走 `system/skills/research-closeout.md` | `output/research/` → 知识与假设分流 |
| 开始研究 / 扫描本地知识 | `research_preflight.py` + `system/skills/research.md` | 一次加载 Rule / Pattern / Exploration，并扫描 Entity / Concept / Source |
| 知识复盘 / 提炼 / 加载规则 | `system/skills/knowledge-lifecycle.md` + `knowledge_lifecycle.py` | exploration 验证 → pattern → rule；按场景选择性加载 |
| 快速筛选 | `system/skills/screen.md` | `output/screen/` |
| 播客摄入 | `system/skills/podcast.md` | `wiki/sources/` + `wiki/raw/podcasts/` + `output/pod2wiki/` |
| 日报监控 | `system/skills/daily-watch.md`（接线细节见 `system/integrations/daily-watchlist.md`） | `daily-watchlist-reports/` + `evidence/` + 假设引用 |
| 管理股票池 | `system/skills/daily-watch-import.md` | `config/daily-watchlist-watchlist.md` |
| 假设操作 | `system/skills/daily-watch-ht.md` | `hypothesis/` + `portfolio/` |
| 假设复盘 | `system/skills/hypothesis-review.md` + 相关研究和日报 | `hypothesis/` → 确认后更新 `wiki/explorations/` |
| 处理待确认项 | `workspace/review-queue.md` | 执行后更新队列状态 |
| 生成输出 | `workspace/meta/active-context.md` + 相关 wiki 文件 | `output/` |
| 遇到摩擦 | 相关文件 | `workspace/meta/friction-log.md` |

## 六大能力

| 能力 | 说明 | Skill 文件 | 需要 API? |
|---|---|---|---|
| wiki | 知识库（基座核心） | `system/integrations/personal-wiki.md` | 否 |
| research | 研究闭环 | `system/skills/research.md` | 否（websearch） |
| screen | 快速筛选 | `system/skills/screen.md` | 可选（外部 Longbridge Skill / tushare / FMP） |
| hypothesis | 假设追踪 | `system/integrations/hypothesis-tracker.md` | 否 |
| podcast | 播客/博客摄入 | `system/skills/podcast.md` | 需要 LLM key |
| daily-watch | 日报监控 | `system/skills/daily-watch.md` | 可选（tushare / FMP） |

工具代码在 `tools/` 目录下。首次使用时 agent 检查依赖，缺什么用 `python3 -m pip install ...` 安装；如果环境只有 `python`，再替换成 `python -m pip ...`。

## 状态与确认

- Markdown frontmatter 是研究、假设和证据“当前状态”的唯一来源；正文只保存分析与历史。
- `config/daily-watchlist-watchlist.md` 是日报执行股票池的唯一来源；`monitoring/` 只是用户看板。
- wiki 沉淀、假设状态调整、股票池新增、研究偏好固化等需要确认的动作，先追加到 `workspace/review-queue.md`，不能只留在对话里。
- 研究开始时必须先运行 `research_preflight.py --context ... --research-id ... --research-file ... --record`，加载命中的 `rule / pattern / exploration` 并扫描相关 `entity / concept / source`；打开命中页面全文后才联网。
- 研究报告必须记录 `preflight_id / knowledge_used / wiki_pages_loaded` 和 `Wiki check`；扫描失败可以人工降级，但不能静默跳过。
- 新建、复盘或改变知识状态后运行 `knowledge_lifecycle.py rebuild-index --apply`；三类 `_index.md` 是自动生成的加载路由，不手工堆证据。
- 用户说“看看现在该做什么”时，运行 `python system/scripts/workspace_status.py`（macOS/Linux 可用 `python3`）。

## active-context：断点续传

`workspace/meta/active-context.md` 是工作记忆，支撑"今天停、明天接"。只记最近 1-2 周仍有价值的上下文，单条一行。两条规则配套，**自动执行，不必询问用户**：

- **续接（开场自动读）**：用户开场出现"继续 / 接着 / 昨天 / 上次"等延续信号 → 第一动作就是读 `active-context.md`，顺着最新一条的「续接锚点」接上，不要让用户重新交代上下文。
- **断点（结束自动写）**：满足任一条件即在「最近对话延续」段追加一行——① 用户说"今天到此 / 先到这吧 / 明天继续 / 暂停 / 保存进度"；② 一段工作落盘、做出决策、或长对话自然收尾。

格式（一条一行）：

```markdown
- **YYYY-MM-DD：主题（状态）** -> 文件路径 + 一句话摘要 + 续接锚点
```

状态标签：`PAUSED` 半成品 / `DONE` 完成 / `决策` 决定。

**上限与自动清理（写断点时顺手做，不另外问用户）**：「最近对话延续」段按 14 天滚动、最多约 20 条。每次追加新行后自检——① 把**超过 14 天**的条目整行移到 `workspace/meta/active-context-archive-YYYY-MM.md`（不丢续接锚点）；② 若移完仍超 20 条，再把最旧的几条一并移到归档，直到段内 ≤ 20 条。同日同主题用"改"不用"新增"，避免堆叠。

## 最小试跑（基座，零依赖）

用户可以直接说：

> 把 `inbox/first-note.md` 整理进 personal wiki。

Codex 应该创建一篇 `wiki/sources/YYYY-MM-DD-first-note.md`，并在 `workspace/meta/active-context.md` 记录本次试跑结果。这条链路只读写 markdown，不需要安装任何依赖。

## 数据源

配置在 `config/*.env` 中，配了才用，没配降级不报错。

| 数据源 | 市场 | env key | 费用 |
|--------|------|---------|------|
| tushare | A 股 | `TUSHARE_TOKEN` | 按官方套餐 |
| FMP | 全球 | `FMP_API_KEY` | 按官方套餐 |
| Finnhub / EOD / yfinance | 美股（daily-watch 降级源） | `FINNHUB_API_KEY` / `EOD_API_KEY` / `ENABLE_YFINANCE` | 免费档可用 |
| Longbridge Skill | 多市场 | 独立安装与授权 | 外部 Agent 扩展，不是日报脚本内置源 |

获取方式：
- Longbridge：https://open.longbridge.com/zh-CN/skill/
- tushare：https://tushare.pro/register
- FMP：https://financialmodelingprep.com/

## 系统维护（防臃肿）

- 装好上手后一次性瘦身：`system/skills/post-install-cleanup.md`（清安装脚手架 + 精简必读文件）。
- 每周结构体检、给精简建议：`system/skills/structure-health.md`。

<!-- 文件说明：Codex 入口路由和工作规则。 -->

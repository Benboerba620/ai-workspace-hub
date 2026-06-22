# INSTALL-FOR-AI

把下面这句话发给 Codex、Claude Code、Cursor、Cline 或任何能读写文件的 AI agent：

> 帮我按这个协议安装 AI Workspace Hub：https://github.com/Benboerba620/ai-workspace-hub/blob/main/INSTALL-FOR-AI.md

---

## Agent 安装目标

你要帮用户创建一个 all-in-one AI 研究工作系统，包含六大能力。

注意：如果用户只是想试跑本 repo，不需要安装。直接在 Codex 里打开本目录，然后执行 `SMOKE-TEST.md` 里的任务即可。

完成后，用户应该得到：

```text
my-ai-workspace/
├── AGENTS.md
├── CLAUDE.md
├── workspace/workspace-config.md
├── workspace/meta/active-context.md
├── workspace/meta/friction-log.md
├── wiki/_schema.md
├── wiki/raw/ / sources/ / entities/ / concepts/ / explorations/
├── inbox/
├── output/ / output/screen/
├── monitoring/
├── hypothesis/
├── daily-watchlist-reports/
├── portfolio/journal/
├── config/
├── tools/podcast/（含 scripts/ examples/ .env.example requirements.txt）
├── tools/daily-watch/（含 scripts/ config-examples/ templates/ requirements.txt）
├── system/interfaces/ / integrations/ / skills/ / scripts/ / templates/
└── requirements.txt / requirements-pdf.txt
```

---

## 安装前只问 3 个问题

一次只问一个问题。

1. 工作区要放在哪里？默认：当前目录。
2. 主要用途是什么？例如：研究、写作、投研、播客整理、个人知识库。
3. 是否已经有 wiki？如果有，路径是什么？

如果用户不确定，就用默认值继续，不要卡住。

---

## 安装步骤

### Step 1：创建目录

```text
workspace/meta/
wiki/raw/
wiki/sources/
wiki/entities/
wiki/concepts/
wiki/explorations/
inbox/
output/
output/screen/
monitoring/
hypothesis/
daily-watchlist-reports/
portfolio/journal/
config/
tools/podcast/scripts/
tools/podcast/examples/
tools/daily-watch/scripts/
tools/daily-watch/config-examples/
tools/daily-watch/templates/
system/interfaces/
system/integrations/
system/skills/
system/scripts/
system/templates/
```

### Step 2：写入核心文件

复制模板和工具代码：

**入口文件**（从 `system/templates/` 复制）：
- `system/templates/AGENTS.md` -> `AGENTS.md`
- `system/templates/CLAUDE.md` -> `CLAUDE.md`
- `system/templates/workspace-config.md` -> `workspace/workspace-config.md`
- `system/templates/active-context.md` -> `workspace/meta/active-context.md`
- `system/templates/friction-log.md` -> `workspace/meta/friction-log.md`
- `system/templates/interfaces-README.md` -> `system/interfaces/README.md`

**知识库**：
- `wiki/_schema.md` -> `wiki/_schema.md`

**Skills**（能力说明书）：
- `system/skills/first-ingest.md` -> `system/skills/first-ingest.md`
- `system/skills/research.md` -> `system/skills/research.md`
- `system/skills/screen.md` -> `system/skills/screen.md`
- `system/skills/podcast.md` -> `system/skills/podcast.md`
- `system/skills/daily-watch.md` -> `system/skills/daily-watch.md`
- `system/skills/daily-watch-import.md` -> `system/skills/daily-watch-import.md`
- `system/skills/daily-watch-ht.md` -> `system/skills/daily-watch-ht.md`
- `system/skills/pdf-ingest.md` -> `system/skills/pdf-ingest.md`
- `system/skills/post-install-cleanup.md` -> `system/skills/post-install-cleanup.md`
- `system/skills/structure-health.md` -> `system/skills/structure-health.md`
- `system/skills/_template.md` -> `system/skills/_template.md`

**Integrations**（内部接线说明）：
- `system/integrations/personal-wiki.md` -> `system/integrations/personal-wiki.md`
- `system/integrations/hypothesis-tracker.md` -> `system/integrations/hypothesis-tracker.md`
- `system/integrations/_template.md` -> `system/integrations/_template.md`

**工具代码**：
- `tools/podcast/` 整个目录（scripts/ examples/ .env.example requirements.txt pyproject.toml）
- `tools/daily-watch/` 整个目录（scripts/ config-examples/ templates/ requirements.txt pyproject.toml）
- `system/scripts/pdf_to_md.py` -> `system/scripts/pdf_to_md.py`

**依赖文件**：
- `requirements.txt` -> `requirements.txt`
- `requirements-pdf.txt` -> `requirements-pdf.txt`

**试跑材料**：
- `inbox/first-note.md` -> `inbox/first-note.md`

按用户用途替换模板里的占位符。

说明：

- Codex 优先读取 `AGENTS.md`。
- Claude Code 优先读取 `CLAUDE.md`。
- 两个文件应该表达同一套规则，不要分叉成两套系统。

### Step 3：写入接口说明

在 `system/interfaces/README.md` 中记录：

```markdown
# Interfaces

## personal wiki
- status: enabled
- wiki_root: ./wiki
- schema: karpathy-claude-wiki compatible

## podcast
- status: enabled
- project_path: ./tools/podcast
- writes_to: wiki/sources, wiki/raw/podcasts, output/pod2wiki

## daily-watch
- status: enabled
- project_path: ./tools/daily-watch
- reads_from: config/daily-watchlist-watchlist.md, monitoring, wiki/entities, wiki/concepts
- writes_to: daily-watchlist-reports, hypothesis

## screen
- status: enabled
- writes_to: output/screen
```

### Step 4：接入 personal wiki

如果用户已有 wiki，不要复制旧 wiki，只记录路径：

```markdown
- personal_wiki_status: `enabled`
- wiki_root: `用户给出的路径`
```

如果没有现成 wiki，保留新建的最小 `wiki/` 目录。

### Step 5：配置数据源

问用户追踪哪些市场，然后设置对应配置：

1. 复制工具配置示例到 `config/`：
   - `tools/daily-watch/config-examples/daily-watchlist.example.yaml` -> `config/daily-watchlist.yaml`
   - `tools/daily-watch/config-examples/daily-watchlist.env.example` -> `config/daily-watchlist.env`
   - `tools/daily-watch/config-examples/daily-watchlist.watchlist.example.md` -> `config/daily-watchlist-watchlist.md`
   - `tools/daily-watch/config-examples/hypothesis-tracker.example.yaml` -> `config/hypothesis-tracker.yaml`
   - `tools/daily-watch/config-examples/hypothesis-tracker.rules.example.md` -> `config/hypothesis-tracker.rules.md`
   - `tools/podcast/examples/config.ai-investing.yaml` -> `config/pod2wiki.config.yaml`
   - `tools/podcast/.env.example` -> `config/pod2wiki.env`

2. 告诉用户哪些 key 要填：

| 功能 | 需要填的 key | 没填时 | 获取方式 |
|------|-------------|--------|---------|
| 日报/筛选（港美股） | `LONGBRIDGE_APP_KEY` 等 | 降级到 websearch | [Longbridge](https://open.longbridge.com/zh-CN/skill/) |
| 日报/筛选（A 股） | `TUSHARE_TOKEN` | 跳过 A 股 | [tushare](https://tushare.pro/register) |
| 播客摘要 | `LLM_API_KEY`（DeepSeek 等） | `--no-llm` 模式 | [DeepSeek](https://platform.deepseek.com/) |
| 日报（付费可选） | `FMP_API_KEY` | 用 Longbridge 替代 | [FMP](https://financialmodelingprep.com/) |

### Step 6：完成后告诉用户

给用户 3 个可见结果：

1. `AGENTS.md` 和 `CLAUDE.md` 已创建。
2. `tools/podcast/` 和 `tools/daily-watch/` 已就位。
3. `config/` 目录已准备好，列出需要填写的 API key。

然后建议做第一件小任务：

> 把一篇文章或一段笔记放进 `inbox/`，让 AI agent 帮你转成 `wiki/sources/` 页面。

### Step 7：上手后提议瘦身

等用户跑通几次、不再需要上手引导，主动提议一次性瘦身：

> 你已经熟悉了，要不要我把安装时的脚手架清掉、精简每次必读的文件？说一句"精简系统"即可。

这会执行 `system/skills/post-install-cleanup.md`。

---

## 安装原则

- 不要默认安装 Python 依赖（首次使用对应工具时再装）。
- 不要默认创建 Git commit。
- 不要默认 push 到 GitHub。
- 不要把用户的旧资料复制进新项目。
- 不要把一次性偏好写进 `AGENTS.md` 或 `CLAUDE.md`。
- 遇到摩擦时，优先记录到 `workspace/meta/friction-log.md`。

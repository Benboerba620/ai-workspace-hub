# INSTALL-FOR-AI

把下面这句话发给 Codex、Claude Code、Cursor、Cline 或任何能读写文件的 AI agent：

> 帮我按这个协议安装 AI Workspace Hub：https://raw.githubusercontent.com/Benboerba620/ai-workspace-hub/main/INSTALL-FOR-AI.md
> 如果抓不到协议全文，先 `git clone https://github.com/Benboerba620/ai-workspace-hub.git`，再读源码里的 `INSTALL-FOR-AI.md` 逐字执行。

（给 agent 的提醒：网页抓取常返回摘要。执行安装前确认你拿到的是协议**全文**——全文包含「安装步骤 Step 0-8」；只拿到摘要就走 git clone 通路。）

---

## Agent 安装目标

你要帮用户创建一个 all-in-one AI 研究工作系统，包含六大能力。

安装分两档：Core Mode 是零 API 的 Markdown 工作流，安装后应立刻可用；Enhanced Mode 是播客摘要、行情数据、日报监控等自动化能力。如果用户只是试跑，可以先不填 key；如果用户明确想启用自动化，安装后应建议他填写自己的 API key。

注意：如果用户只是想试跑本 repo，不需要安装。直接在 Codex 里打开本目录，然后执行 `SMOKE-TEST.md` 里的任务即可。

完成后，用户应该得到：

```text
my-ai-workspace/
├── AGENTS.md
├── CLAUDE.md
├── workspace/workspace-config.md
├── workspace/meta/active-context.md
├── workspace/meta/friction-log.md
├── workspace/review-queue.md
├── workspace/monitoring/ / archive/
├── wiki/_schema.md
├── wiki/raw/ / sources/ / entities/ / concepts/ / explorations/
├── inbox/
├── output/ / output/screen/ / output/daily-watch/
├── hypothesis/
├── evidence/
├── portfolio/journal/
├── config/
├── tools/podcast/（含 scripts/ examples/ .env.example requirements.txt）
├── tools/daily-watch/（含 scripts/ config-examples/ templates/ requirements.txt）
├── system/interfaces/ / integrations/ / skills/ / scripts/ / templates/
└── requirements.txt / requirements-pdf.txt
```

完成安装不等于必须配完 API key。只要 Core Mode 可用，用户就可以先开始使用；但如果目标是播客摘要、行情日报、自动监控，API key 是推荐配置项。

---

## 安装前只问 4 个问题

一次只问一个问题。

1. 工作区要放在哪里？默认：当前目录。
2. 主要用途是什么？默认：股票研究；也可以选择写作、播客整理或个人知识库。
3. 是否已经有 wiki？如果有，路径是什么？
4. 你用 Obsidian 当阅读器吗？默认：不用。用 → 安装阅读台（Obsidian Bases 仪表盘，自动汇总 inbox / 研究 / 筛选 / 播客 / 日报的新内容）。

如果用户不确定，就用默认值继续，不要卡住。

---

## 安装步骤

### Step 0：取得安装源

安装需要联网读取本仓库。先判断当前目录是否已经是 AI Workspace Hub 源码：

- 若当前目录存在本文件和 `system/scripts/install_workspace.py`，将当前目录记为 `{SOURCE_ROOT}`。
- 否则，把仓库临时克隆到系统临时目录，再将该目录记为 `{SOURCE_ROOT}`：

```bash
git clone --depth 1 https://github.com/Benboerba620/ai-workspace-hub.git "{临时目录}/ai-workspace-hub-source"
```

临时目录按平台取：Windows 用 `%TEMP%`，macOS / Linux 用 `/tmp`（或 `mktemp -d`）。

如果环境没有 Git，下载 GitHub 源码 ZIP 并解压到临时目录。不要把临时源码目录当成用户工作区。

### 推荐：运行安全安装器

安装器只使用 Python 标准库，不安装依赖。目标目录为空时直接安装；目标目录非空时默认停止，只有用户确认合并后才加 `--merge`，并且所有已有文件都原样保留。

命令默认使用 `python3`，且需要 Python 3.10+。先运行 `python3 --version`；如果版本低于 3.10，改用 `python3.10` / `python3.11` / `python3.12`，或引导用户安装新版 Python。如果用户环境只有 `python` 且版本 ≥3.10，把 `python3` 替换成 `python`；不要因为命令名不同就判定安装失败。

```bash
python3 "{SOURCE_ROOT}/system/scripts/install_workspace.py" \
  --source "{SOURCE_ROOT}" \
  --target "{用户工作区}" \
  --name "{项目名}" \
  --primary-use "{主要用途}" \
  --wiki-root "{wiki路径}"
```

参数说明：用户没有现成 wiki 时，`--wiki-root` 直接省略（默认值 `./wiki`，即在工作区内新建）；只有用户给出**已存在**的 wiki 路径时才传该参数。用户用 Obsidian 时加 `--obsidian-reading-hub`；目标目录里已有 `.obsidian/`（装进现有 Obsidian 库）时安装器会自动启用，不用手动传参。

安装器成功后跳到 Step 3 继续。没有 Python 时，Agent 按下面的 Step 1-2 使用文件工具完成同样操作。

### Step 1：手动创建目录（安装器不可用时）

```text
workspace/meta/
workspace/monitoring/
workspace/archive/
wiki/raw/
wiki/sources/
wiki/entities/
wiki/concepts/
wiki/explorations/
inbox/
output/
output/research/
output/screen/
output/pod2wiki/
output/daily-watch/
hypothesis/
evidence/
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

### Step 2：手动写入核心文件（安装器不可用时）

复制模板和工具代码：

**入口文件**（从 `system/templates/` 复制）：
- `system/templates/AGENTS.md` -> `AGENTS.md`
- `system/templates/CLAUDE.md` -> `CLAUDE.md`
- `system/templates/workspace-config.md` -> `workspace/workspace-config.md`
- `system/templates/active-context.md` -> `workspace/meta/active-context.md`
- `system/templates/friction-log.md` -> `workspace/meta/friction-log.md`
- `system/templates/research-profile.md` -> `workspace/research-profile.md`
- `system/templates/review-queue.md` -> `workspace/review-queue.md`
- `system/templates/interfaces-README.md` -> `system/interfaces/README.md`

**可选：Obsidian 阅读台**（仅当用户使用 Obsidian）：
- `system/templates/reading-hub.base` -> `reading-hub.base`
- `system/templates/reading-hub.md` -> `reading-hub.md`

**知识库**：
- `wiki/_schema.md` -> `wiki/_schema.md`
- `evidence/README.md` -> `evidence/README.md`

**Skills**（能力说明书）：
- `system/skills/first-ingest.md` -> `system/skills/first-ingest.md`
- `system/skills/first-research.md` -> `system/skills/first-research.md`
- `system/skills/research.md` -> `system/skills/research.md`
- `system/skills/research-closeout.md` -> `system/skills/research-closeout.md`
- `system/skills/hypothesis-review.md` -> `system/skills/hypothesis-review.md`
- `system/skills/workspace-status.md` -> `system/skills/workspace-status.md`
- `system/skills/upgrade-workspace.md` -> `system/skills/upgrade-workspace.md`
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
- `system/integrations/pod2wiki.md` -> `system/integrations/pod2wiki.md`
- `system/integrations/daily-watchlist.md` -> `system/integrations/daily-watchlist.md`
- `system/integrations/object-model.md` -> `system/integrations/object-model.md`
- `system/integrations/_template.md` -> `system/integrations/_template.md`

**工具代码**：
- `tools/podcast/` 整个目录（scripts/ examples/ .env.example requirements.txt pyproject.toml）
- `tools/daily-watch/` 整个目录（scripts/ config-examples/ templates/ requirements.txt pyproject.toml）
- `system/scripts/pdf_to_md.py` -> `system/scripts/pdf_to_md.py`
- `system/scripts/install_workspace.py` -> `system/scripts/install_workspace.py`
- `system/scripts/check_workspace.py` -> `system/scripts/check_workspace.py`
- `system/scripts/workspace_status.py` -> `system/scripts/workspace_status.py`
- `system/scripts/review_queue.py` -> `system/scripts/review_queue.py`
- `system/scripts/upgrade_workspace.py` -> `system/scripts/upgrade_workspace.py`

**依赖文件**：
- `requirements.txt` -> `requirements.txt`
- `requirements-pdf.txt` -> `requirements-pdf.txt`

**试跑材料**：
- `inbox/first-note.md` -> `inbox/first-note.md`
- `inbox/sample-ai-workspace.pdf` -> `inbox/sample-ai-workspace.pdf`

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
- reads_from: config/daily-watchlist-watchlist.md, wiki/entities, wiki/concepts
- writes_to: output/daily-watch, evidence, hypothesis（证据引用）

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

### Step 5：运行 Core Mode 检查

安装后先检查零 API 的核心工作流，不要先要求用户填写 API key：

```bash
python3 "{用户工作区}/system/scripts/check_workspace.py" --root "{用户工作区}"
```

判断方式：

- `Core Mode result: READY`：安装成功，用户可以开始用 `inbox → wiki → output` 工作流。
- Enhanced Mode 里的 API key 警告：只代表可选自动化未开启，不是安装失败。
- 如果 Python 不可用，但核心文件都已经复制完成，也可以让用户直接用 AI agent 执行 `inbox/first-note.md → wiki` 的 Markdown 试跑。

### Step 6：默认建议配置自己的 LLM API（Enhanced Mode）

默认询问用户是否要填写自己的 LLM API key，用于 wiki 自动标签和播客摘要。不要把 key 当成安装成功的硬前置；用户暂时不填时，明确说明 Core Mode 仍可运行，但脚本自动标签会跳过。行情类数据源继续按需配置。

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
| 日报（A 股） | `TUSHARE_TOKEN` | 跳过 A 股 | [tushare](https://tushare.pro/register) |
| wiki 自动标签 + 播客摘要 | `LLM_API_KEY`（DeepSeek 等） | wiki 保留空标签；播客用 `--no-llm` | [DeepSeek](https://platform.deepseek.com/) |
| 日报（全球市场） | `FMP_API_KEY` | 美股尝试 Nasdaq 等降级源 | [FMP](https://financialmodelingprep.com/) |

Longbridge 不是上述脚本的环境变量数据源。它是独立 Agent Skill/CLI/MCP；用户需要时，按[官方安装说明](https://open.longbridge.com/zh-CN/skill/)另行安装和授权，可用于 screen / research 的行情查询。

### Step 7：完成后告诉用户

给用户这些可见结果：

1. `AGENTS.md` 和 `CLAUDE.md` 已创建。
2. `tools/podcast/` 和 `tools/daily-watch/` 已就位。
3. `check_workspace.py` 已显示 Core Mode 是否可用；如果用户还没填 API key，说明 Enhanced Mode 可之后再开。
4. 如果用户用 Obsidian：`reading-hub.md` 已安装为阅读首页（需要 Obsidian 1.9+ 的 Bases 功能），每天从它开始扫新内容。

先用一份材料确认系统能工作：

> 把一篇文章或一段笔记放进 `inbox/`，让 AI agent 帮你转成 `wiki/sources/` 页面。

样例通过后，打开 `START-HERE.md`，开始第一份真实股票研究：

> 研究一家公司，同时帮我建立第一版研究偏好。公司是：____；我现在关注它是因为：____。

首次研究形成研究偏好 v0.1，并把值得持续验证的判断分流为假设后，才算完成用户激活。

### Step 8：上手后提议瘦身

等用户跑通几次、不再需要上手引导，主动提议一次性瘦身：

> 你已经熟悉了，要不要我把安装时的脚手架清掉、精简每次必读的文件？说一句"精简系统"即可。

这会执行 `system/skills/post-install-cleanup.md`。

---

## 安装原则

- 不要把 API key 当成安装前提；先让 Core Mode 跑通。
- 如果用户想启用自动化功能，要主动建议他配置自己的 API key。
- 不要因为 Enhanced Mode 缺 key 就告诉用户“安装失败”。
- 不要默认安装 Python 依赖（首次使用对应工具时再装）。
- 不要声称安装过程不联网；取得源码需要联网，安装完成后的 Markdown 基座才可以离线运行。
- 不要默认创建 Git commit。
- 不要默认 push 到 GitHub。
- 不要把用户的旧资料复制进新项目。
- 不要把一次性偏好写进 `AGENTS.md` 或 `CLAUDE.md`。
- 遇到摩擦时，优先记录到 `workspace/meta/friction-log.md`。

<!-- 文件说明：交给 AI agent 执行的安装协议。 -->

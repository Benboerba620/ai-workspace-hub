# INSTALL-FOR-AI

把下面这句话发给 Codex、Claude Code、Cursor、Cline 或任何能读写文件的 AI agent：

> 帮我按这个协议安装 AI Workspace Hub：https://github.com/Benboerba620/ai-workspace-hub/blob/main/INSTALL-FOR-AI.md

---

## Agent 安装目标

你要帮用户创建一个最小 AI 工作系统，不是完整平台。

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
├── wiki/raw/
├── wiki/sources/
├── wiki/entities/
├── wiki/concepts/
├── wiki/explorations/
├── inbox/
├── output/
├── monitoring/
├── hypothesis/
├── system/interfaces/
├── system/integrations/
├── system/skills/
├── system/scripts/
└── requirements-pdf.txt
```

---

## 安装前只问 3 个问题

一次只问一个问题。模块（博客抓取 / 日报监控）**不在这里问**——基座装好后再主动提议（见 Step 5）。

1. 工作区要放在哪里？默认：当前目录。
2. 主要用途是什么？例如：研究、写作、投研、播客整理、个人知识库。
3. 是否已经有 wiki？如果有，路径是什么？

如果用户不确定，就用默认值继续，不要卡住。

---

## 安装步骤

### Step 1：创建目录

创建最小目录，不要创建复杂脚本。

```text
workspace/meta/
wiki/raw/
wiki/sources/
wiki/entities/
wiki/concepts/
wiki/explorations/
inbox/
output/
monitoring/
hypothesis/
system/interfaces/
system/integrations/
system/skills/
system/scripts/
```

### Step 2：写入核心文件

复制模板：

- `system/templates/AGENTS.md` -> `AGENTS.md`
- `system/templates/CLAUDE.md` -> `CLAUDE.md`
- `system/templates/workspace-config.md` -> `workspace/workspace-config.md`
- `system/templates/active-context.md` -> `workspace/meta/active-context.md`
- `system/templates/friction-log.md` -> `workspace/meta/friction-log.md`
- `system/templates/interfaces-README.md` -> `system/interfaces/README.md`
- `wiki/_schema.md` -> `wiki/_schema.md`
- `system/integrations/personal-wiki.md` -> `system/integrations/personal-wiki.md`
- `system/skills/first-ingest.md` -> `system/skills/first-ingest.md`
- `system/skills/research.md` -> `system/skills/research.md`（研究闭环，基座能力）
- `system/skills/pdf-ingest.md` -> `system/skills/pdf-ingest.md`（可选能力样板）
- `system/skills/deploy-modules.md` -> `system/skills/deploy-modules.md`（一键部署官方模块）
- `system/skills/post-install-cleanup.md` -> `system/skills/post-install-cleanup.md`（安装后瘦身）
- `system/skills/structure-health.md` -> `system/skills/structure-health.md`（每周结构体检）
- `system/skills/_template.md` -> `system/skills/_template.md`（新增能力照抄）
- `system/integrations/pod2wiki.md` -> `system/integrations/pod2wiki.md`
- `system/integrations/daily-watchlist.md` -> `system/integrations/daily-watchlist.md`
- `system/integrations/hypothesis-tracker.md` -> `system/integrations/hypothesis-tracker.md`（基座自带假设追踪的文件契约）
- `system/integrations/_template.md` -> `system/integrations/_template.md`（新增模块照抄）
- `system/scripts/pdf_to_md.py` -> `system/scripts/pdf_to_md.py`（PDF 可选能力，按需）
- `requirements-pdf.txt` -> `requirements-pdf.txt`（PDF 可选能力，按需）

按用户用途替换模板里的占位符。

说明：

- Codex 优先读取 `AGENTS.md`。
- Claude Code 优先读取 `CLAUDE.md`。
- 两个文件应该表达同一套规则，不要分叉成两套系统。

### Step 3：写入接口说明

在 `system/interfaces/README.md` 中记录或更新：

```markdown
# Interfaces

## personal wiki
- status: enabled
- wiki_root: ./wiki
- schema: karpathy-claude-wiki compatible
- owns: wiki/raw, wiki/sources, wiki/entities, wiki/concepts, wiki/explorations

## pod2wiki
- status: optional / enabled / planned
- project_path:
- writes_to: wiki/sources, wiki/raw/podcasts, output/pod2wiki

## daily-watchlist
- status: planned / enabled
- project_path:
- reads_from: monitoring, wiki/entities, wiki/concepts
- writes_to: output/daily-watchlist, hypothesis
```

### Step 4：接入 personal wiki

personal wiki 是默认核心模块。如果用户已有 wiki，不要复制旧 wiki，只记录路径：

```markdown
- personal_wiki_status: `enabled`
- wiki_root: `用户给出的路径`
```

如果用户没有现成 wiki，就保留新建的最小 `wiki/` 目录。

### Step 5：基座装好后，主动提议两个模块

基座（输入 → wiki → 输出 → 反馈 + 记忆）此时已零依赖可用。现在**主动问用户**是否要装这两个常用模块（一次问一个）：

1. **博客 / 播客抓取（pod2wiki）**——把播客、RSS、博客自动转成 wiki 页面。
2. **日报监控（daily-watchlist）**——读股票池和知识库，每天产出盯盘日报，并把证据回写假设。

提问时说清楚：

- 装它们会 `git clone` 一个外部 repo，**可能需要回答几个配置问题、花几分钟**。
- **现在不装完全没关系**，以后随时说一句"**帮我安装博客抓取**"或"**帮我安装日报监控**"即可。

用户答应某个 → 执行 `system/skills/deploy-modules.md` 的部署流程（clone → 读契约 → 接线到 wiki → 跑模块自带安装 → 验证）。用户说"以后再说" → 跳过，不阻塞，不要把 `status` 之外的东西写死。

> 假设追踪是**基座自带能力**，不是要另装的模块：`hypothesis/` 记假设与证据（一假设一 `H*.md`），复盘结论回写 `wiki/explorations/`。开箱即用，无需安装。

### Step 6：完成后告诉用户怎么验证

给用户 3 个可见结果：

1. `AGENTS.md` 和 `CLAUDE.md` 已创建。
2. `workspace/meta/active-context.md` 已创建。
3. `wiki/`、`output/`、`monitoring/`、`hypothesis/`、`system/integrations/` 目录已创建。

然后建议用户做第一件小任务：

> 把一篇文章或一段播客笔记放进 `inbox/`，让 AI agent 帮你转成 `wiki/sources/` 页面。

### Step 7：上手后提议瘦身

等用户跑通过几次、不再需要上手引导，主动提议一次性瘦身：

> 你已经熟悉了，要不要我把安装/试跑用的脚手架清掉、精简每次必读的文件？说一句"精简系统"即可。

这会执行 `system/skills/post-install-cleanup.md`。之后建议用户每周用 `system/skills/structure-health.md` 做一次结构体检，防止系统再变胖（排程方式见该 skill，由用户自己挂）。

---

## 安装原则

- 不要默认安装依赖。
- PDF Python 路径是可选项；只有用户明确要处理真实文本 PDF 时，才建议运行 `python -m pip install -r requirements-pdf.txt`。
- 不要默认创建 Git commit。
- 不要默认 push 到 GitHub。
- 不要把用户的旧资料复制进新项目。
- 不要把一次性偏好写进 `AGENTS.md` 或 `CLAUDE.md`。
- 遇到摩擦时，优先记录到 `workspace/meta/friction-log.md`。

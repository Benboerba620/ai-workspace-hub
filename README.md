<div align="center">

# AI Workspace Hub

**Turn Codex, Claude Code, Cursor, and Cline into a persistent research workspace.**

把 AI 编程助手变成一套能长期记忆、持续研究、自动沉淀的工作台。

[![CI](https://github.com/Benboerba620/ai-workspace-hub/actions/workflows/ci.yml/badge.svg)](https://github.com/Benboerba620/ai-workspace-hub/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![GitHub stars](https://img.shields.io/github/stars/Benboerba620/ai-workspace-hub?style=social)](https://github.com/Benboerba620/ai-workspace-hub/stargazers)
[![License](https://img.shields.io/github/license/Benboerba620/ai-workspace-hub)](LICENSE)

[30 秒上手](#-30-秒上手) · [六大能力](#-六大能力) · [第一周怎么用](#-第一周怎么用) · [故障排查](TROUBLESHOOTING.md)

</div>

---

> 对话很聪明，但工作流没有记忆；今天做完，明天又从头解释。

AI Workspace Hub 解决这个问题。六大能力开箱即用——**核心工作流不需要 API key**。

---

## ⚡ 30 秒上手

把下面这句话发给你的 AI agent（Codex / Claude Code / Cursor / Cline）：

```text
帮我按这个协议安装 AI Workspace Hub：
https://github.com/Benboerba620/ai-workspace-hub/blob/main/INSTALL-FOR-AI.md
```

Agent 会问你 3 个问题，然后自动创建完整工作区。装好后，对它说：

```text
把 inbox/first-note.md 整理进 personal wiki。
```

预期：agent 读 `AGENTS.md` → 按 `wiki/_schema.md` 整理 → 写入 `wiki/sources/` → 在 `active-context.md` 记录进度。

**不需要 API key，不需要联网，不需要写任何代码。**

<details>
<summary>更习惯手动 clone？</summary>

```bash
git clone https://github.com/Benboerba620/ai-workspace-hub.git my-ai-workspace
cd my-ai-workspace
```

用 AI agent 打开这个目录，直接试跑 `inbox/first-note.md → wiki`。

验证安装状态：

```bash
python3 system/scripts/check_workspace.py    # Windows: python system/scripts/check_workspace.py
```

Core Mode 显示 `READY` 即可开始使用。

</details>

---

## 🧩 六大能力

| | 能力 | 你可以怎么说 | 写入哪里 | API key |
|:--:|------|-------------|----------|---------|
| 📚 | **wiki** | "把这篇文章整理进知识库" | `wiki/` | 不需要 |
| 🔬 | **research** | "帮我研究一下某公司 / 某行业" | `output/research/` | 不需要 |
| 🔍 | **screen** | "帮我筛选 AI 产业链股票" | `output/screen/` | 可选 |
| 📊 | **daily-watch** | "生成今天的盯盘日报" | `daily-watchlist-reports/` | 可选 |
| 🧪 | **hypothesis** | "把这个投资假设建档并追踪" | `hypothesis/` | 不需要 |
| 🎙️ | **podcast** | "扫一下这几个播客并写进 wiki" | `wiki/sources/` + `output/pod2wiki/` | 需要 LLM key |

> **零 key 可用**：wiki、research、hypothesis、screen（websearch 模式）、daily-watch（报告骨架 + 美股降级源）。
>
> **按需增强**：DeepSeek / Kimi / GLM / Qwen（播客摘要）· tushare（A 股）· FMP（全球行情）· [Longbridge Skill](https://open.longbridge.com/zh-CN/skill/)（多市场查询）。

---

## 🔄 工作流程

```text
               ┌──────────────────────────────────────────────┐
               │            AI Workspace Hub                  │
               │                                              │
  inbox/       │   wiki/          output/       hypothesis/   │
  ┌─────┐      │   ┌─────┐       ┌─────────┐   ┌──────────┐  │
  │ PDF │──────│──▸│     │──────▸│research/│   │ H1.md    │  │
  │ 播客 │──────│──▸│知识库│──────▸│screen/  │   │ H2.md    │  │
  │ 笔记 │──────│──▸│     │──────▸│pod2wiki/│   │ ...      │  │
  └─────┘      │   └──┬──┘       └────┬────┘   └────┬─────┘  │
               │      │    ◂─确认回写──┘             │        │
               │      │    ◂──────复盘结论───────────┘        │
               │      ▾                                       │
               │   active-context.md  ← 断点续传，明天接着干   │
               └──────────────────────────────────────────────┘
```

核心不是"文件夹长什么样"，而是：**agent 进入目录后知道先读什么、做研究时先查本地 wiki、输出时事实与推测分开、暂停时自动记录进度、明天继续时从断点接上。**

> 系统不在某个模型里，而在这套文件协议里。谁读懂这套协议，谁就接上你的工作流。

---

## ⚙️ Core Mode / Enhanced Mode

| 模式 | API key | 能做什么 | 适合 |
|------|---------|----------|------|
| **Core** | 不需要 | wiki 摄入、研究草稿、快速筛选、假设建档、断点续传 | 首次试跑、日常 Markdown 工作流 |
| **Enhanced** | 按需填写 | 播客摘要、行情日报、A 股 / 全球市场数据、自动监控 | 启用自动化流程时 |

推荐路径：**Core 先跑通** → `check_workspace.py` 看状态 → 按需填 key 到 `config/*.env`。

---

## 📅 第一周怎么用

| 天数 | 动作 | 目标 |
|:----:|------|------|
| Day 1 | 跑通 `inbox/first-note.md → wiki` | 确认 agent 读得懂工作区 |
| Day 2 | 放入 3-5 条真实材料 | 建立第一批知识库 |
| Day 3 | 让 agent 研究一个公司 / 行业 | 生成第一篇结构化报告 |
| Day 4 | `check_workspace.py`，按需配 tushare / FMP | 增强行情能力 |
| Day 5 | 做一次主题筛选 | 形成候选池 |
| Day 6 | 配 LLM key，扫一次播客 / 博客 | 建立外部信息流 |
| Day 7 | 运行结构体检，删掉没用规则 | 防止系统变胖 |

---

## 适合谁？

**适合**：投资研究员、个人投资者、内容创作者、AI power user、Markdown / Obsidian 用户、想做长期项目而不是一次性对话的人。

**不适合**：想要 GUI 应用、自动交易系统，或不愿意用 Markdown 管理知识的人。

---

<details>
<summary><b>📂 目录结构</b></summary>

```text
ai-workspace-hub/
├── AGENTS.md                 # Codex 入口路由
├── CLAUDE.md                 # Claude Code 入口路由
├── INSTALL-FOR-AI.md         # 交给 AI agent 的安装协议
├── SMOKE-TEST.md             # 冒烟测试
├── ARCHITECTURE.md           # 架构说明
├── TROUBLESHOOTING.md        # 故障排查
├── workspace/                # 项目配置、断点续传、摩擦日志
├── inbox/                    # 临时输入材料
├── wiki/                     # personal wiki
├── output/                   # 研究、筛选、播客等输出
├── monitoring/               # 股票池 / 关注列表
├── hypothesis/               # 投资假设、证据、复盘
├── daily-watchlist-reports/  # 日报输出
├── portfolio/                # 交易记录
├── config/                   # 用户配置，不入 git
├── tools/                    # podcast / daily-watch 工具
└── system/                   # skills / integrations / scripts / templates
```

</details>

<details>
<summary><b>🗄️ 数据源与边界</b></summary>

| 名称 | 类型 | 用途 | 是否内置 |
|------|------|------|----------|
| Nasdaq | 无 key 降级源 | 美股基础行情 | 是 |
| Finnhub / EOD / yfinance | 降级源 | 美股行情备选（Finnhub / EOD 需各自免费 key，yfinance 用 `ENABLE_YFINANCE=1` 开启） | 是 |
| tushare | API 数据源 | A 股行情 / 财务 | 是，需 token |
| FMP | API 数据源 | 全球行情 / 财报 / 宏观 | 是，需 key |
| Longbridge Skill | 外部 Agent 扩展 | 多市场查询、筛选、研究 | 否，独立安装授权 |
| websearch | Agent 能力 | 补充新闻、资料、公司信息 | 取决于 agent |

**重要边界**：本项目不做自动交易，不承诺数据源永远免费，不把 AI 输出包装成投资建议。缺少 API key 时优雅降级，不会让用户误以为工作区坏了。

</details>

<details>
<summary><b>💻 常用命令</b></summary>

```bash
python3 system/scripts/check_workspace.py          # 总检查
python3 -m unittest discover -s tests -v            # 运行测试
python3 tools/daily-watch/scripts/check_setup.py --init  # 初始化日报配置
python3 tools/podcast/scripts/fetch_podcasts.py --help   # 播客工具帮助
```

Python 工具需要 3.10+。**Windows 用户**用 `python` 代替 `python3`，或 `py -3` 指定版本。

</details>

<details>
<summary><b>❓ 新手常见问题</b></summary>

**Q：我不会写代码，能用这个项目吗？**
可以。Core Mode 只需要把文本放进 `inbox/`，然后用自然语言告诉 AI agent 做什么。

**Q：一定要用 Codex / Claude Code 吗？**
不一定。任何能读写文件的 AI agent 都可以。Codex 和 Claude Code 效果最好，Cursor 和 Cline 也可以。

**Q：wiki 越来越大怎么办？**
用 Obsidian 打开 `wiki/` 目录做可视化管理，或让 AI agent 帮你整理归档。

**Q：API key 会不会泄露？**
`config/` 已被 `.gitignore` 排除，不会被 git 提交。

**Q：可以和 Obsidian 一起用吗？**
可以。把 `wiki/` 添加为 Obsidian vault 即可，所有笔记都是标准 Markdown。

更多问题见 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)。

</details>

---

## Roadmap

- 更多真实研究工作流样例
- 更强的 screen 预设
- 更完善的 daily-watch 降级策略
- 更好的 Obsidian 兼容说明
- 更多 agent 入口适配

---

## Contributing

欢迎提 issue / PR，尤其是新 agent 适配、研究报告模板、数据源接入、真实使用摩擦点、README / 教程 / 安装流程改进。

---

## Star History

如果这个项目对你有帮助，欢迎点一下 ⭐ Star。它会帮助更多需要"长期 AI 工作流"的人发现这个项目，也会让我知道哪些方向值得继续做。

[![Star History Chart](https://api.star-history.com/svg?repos=Benboerba620/ai-workspace-hub&type=Date)](https://www.star-history.com/#Benboerba620/ai-workspace-hub&Date)

---

## Disclaimer

AI Workspace Hub 是个人研究与知识管理工具，不构成投资建议。所有市场数据、公司信息、财务数字、新闻和监管信息都应以原始来源为准。

<!-- 文件说明：项目首页、价值介绍和快速上手。 -->

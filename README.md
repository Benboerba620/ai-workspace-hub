<div align="center">

# AI Workspace Hub

**Turn Codex, Claude Code, Cursor, and Cline into a persistent research workspace.**

把 AI 编程助手变成一套能长期记忆、持续研究、自动沉淀的工作台。

[![CI](https://github.com/Benboerba620/ai-workspace-hub/actions/workflows/ci.yml/badge.svg)](https://github.com/Benboerba620/ai-workspace-hub/actions/workflows/ci.yml)
[![GitHub stars](https://img.shields.io/github/stars/Benboerba620/ai-workspace-hub?style=social)](https://github.com/Benboerba620/ai-workspace-hub/stargazers)
[![License](https://img.shields.io/github/license/Benboerba620/ai-workspace-hub)](LICENSE)

[30 秒试跑](#30-秒试跑) · [Core / Enhanced](#core-mode--enhanced-mode) · [一键交给 AI 安装](#一键交给-ai-安装) · [六大能力](#六大能力) · [工作原理](#为什么不是一个普通模板)

⭐ 如果你也想让 AI 从“一次性聊天”进化成“长期工作系统”，欢迎点一下 Star。它会帮助更多研究员和 AI power user 发现这个项目。

</div>

---

AI Workspace Hub 是一套 **AI-native research workspace**：一次 clone，就拿到知识库、研究、筛选、盯盘、播客摄入、假设追踪六大能力。

核心工作流 **不需要 API key**：你可以先跑通 `inbox → wiki → output`，确认 AI agent 会读规则、会整理材料、会记录断点。API key 用于解锁播客摘要、行情数据、日报监控等增强自动化；如果你的目标是一开始就跑自动化流程，建议安装后马上填写自己的 API key。

它不是又一个 prompt，也不是单一脚本工具。它更像一套给 AI agent 使用的“工作台协议”：文件夹存材料，入口文档告诉 agent 怎么做，skills 定义能力流程，tools 提供可选自动化，active-context 负责断点续传。

你可以把它理解成：给 Codex / Claude Code / Cursor / Cline 准备的一套“研究员操作系统”。

---

## 这个项目解决什么问题？

很多人用 AI 做研究时，会遇到同一个瓶颈：

> 对话很聪明，但工作流没有记忆；今天做完，明天又从头解释。

AI Workspace Hub 的目标是把“临时对话”变成“可持续研究系统”。

一个研究员每天做的事，本质上是六步：

1. **收集材料**：播客、研报、纪要、博客、PDF、网页；
2. **沉淀知识**：把零散材料整理进 personal wiki；
3. **做研究**：带着问题查本地知识库和外部资料；
4. **筛选标的**：围绕主题快速形成候选列表；
5. **日常盯盘**：追踪价格异动、新闻和假设变化；
6. **追踪假设**：记录投资逻辑、证据、反证和复盘。

这个项目把这六步变成 AI agent 能读、能执行、能接续的文件协议。

---

## 效果示例

把一个想法、PDF、播客或网页丢进工作区，然后直接用自然语言要求 AI 处理。

```text
用户：把 inbox/first-note.md 整理进 personal wiki，并记录这次处理过程。

Agent：
1. 读取 AGENTS.md / CLAUDE.md，确认当前工作区规则；
2. 按 wiki/_schema.md 把材料整理为结构化笔记；
3. 写入 wiki/sources/YYYY-MM-DD-first-note.md；
4. 在 workspace/meta/active-context.md 记录本次进度，方便下次继续。
```

更复杂一点：

```text
用户：围绕 AI 数据中心电力链，整理已有 wiki，补充外部资料，
      输出一篇研究报告，并把关键假设建档追踪。

Agent：
- 先查本地 wiki，不从空白对话开始；
- 把事实、推测、待验证问题分开；
- 输出到 output/research/；
- 把核心假设写入 hypothesis/；
- 后续 daily-watch 可以持续追踪证据变化。
```

核心变化不是“AI 回答更聪明”，而是：它知道材料在哪里、流程怎么走、结果写到哪里、下次从哪里接上。

---

## 适合谁？

适合：

- 投资研究员 / 个人投资者：做公司研究、产业链跟踪、假设复盘；
- 内容创作者：把播客、文章、访谈整理成长期知识库；
- AI power user：想让 Codex / Claude Code / Cursor 不只是写代码，而是接管研究工作流；
- Markdown / Obsidian 用户：想让 personal wiki 变成 agent 可操作的系统；
- 想做“长期项目”而不是“一次性对话”的人。

不适合：想要 GUI 应用、自动交易系统，或者不愿意用 Markdown / 文件夹管理知识的人。

---

## 30 秒试跑

你可以先不安装任何 Python 依赖，直接验证最小链路。

```bash
git clone https://github.com/Benboerba620/ai-workspace-hub.git my-ai-workspace
cd my-ai-workspace
```

然后用 Codex / Claude Code / Cursor 打开这个目录，对 agent 说：

```text
把 inbox/first-note.md 整理进 personal wiki。
```

预期结果：

- agent 读取 `AGENTS.md` 或 `CLAUDE.md`；
- 读取 `wiki/_schema.md`；
- 把样例材料整理成 `wiki/sources/YYYY-MM-DD-first-note.md`；
- 在 `workspace/meta/active-context.md` 记录这次试跑。

这条 note → wiki 链路只读写 Markdown，**不需要 API key，不需要联网，不需要安装依赖**。

你也可以运行一次总检查，确认哪些能力已经可用：

```bash
python3 system/scripts/check_workspace.py
```

只要 Core Mode 显示 `READY`，就可以开始使用。Enhanced Mode 里的 API key 警告只是说明部分自动化暂未开启，不代表安装失败；如果你想让播客摘要、行情日报、自动监控真正跑起来，就需要继续填写自己的 API key。

---

## Core Mode / Enhanced Mode

AI Workspace Hub 分成两档体验，避免新用户被 API 配置卡住。

| 模式 | 是否需要 API key | 能做什么 | 适合什么时候 |
|------|------------------|----------|--------------|
| **Core Mode** | 不需要 | wiki 摄入、研究草稿、快速筛选、假设建档、断点续传 | 第一次试跑、日常 Markdown 工作流 |
| **Enhanced Mode** | 建议填写自己的 key | 播客摘要、行情日报、A 股 / 全球市场数据、自动化监控 | 你想启用自动化流程时 |

推荐顺序：

1. 先用 Core Mode 跑通 `inbox/first-note.md → wiki/sources/`。
2. 再运行 `python3 system/scripts/check_workspace.py` 看当前能力状态。
3. 如果要启用播客 / 行情 / 日报 / 自动监控，把自己的 API key 填到本地 `config/*.env`。

真实 API key 只应该保存在你的本地配置文件里，不要提交到 GitHub。

---

## 一键交给 AI 安装

如果你想把它安装成自己的研究工作区，把下面这句话直接发给你的 AI agent：

```text
帮我按这个协议安装 AI Workspace Hub：
https://github.com/Benboerba620/ai-workspace-hub/blob/main/INSTALL-FOR-AI.md
```

agent 会按协议问 3 个问题，然后创建一套完整工作区：工作区放在哪里、主要用途是什么、是否已有 wiki。

安装器默认安全：不覆盖已有文件、不默认安装 Python 依赖、不要求先配置 API key、不自动 commit / push；非空目录默认停止，只有你确认合并才补缺失文件。

详细协议见 [INSTALL-FOR-AI.md](INSTALL-FOR-AI.md)。

---

## 六大能力

| 能力 | 你可以怎么说 | 写入哪里 | API key |
|------|--------------|----------|---------|
| **wiki** | “把这篇文章整理进知识库” | `wiki/` | 不需要 |
| **research** | “帮我研究一下某公司 / 某行业” | `output/research/` | 不需要，websearch 可增强 |
| **screen** | “帮我筛选 AI 产业链股票” | `output/screen/` | 可选 |
| **daily-watch** | “生成今天的盯盘日报” | `daily-watchlist-reports/` | 可选 |
| **hypothesis** | “把这个投资假设建档并追踪” | `hypothesis/` | 不需要 |
| **podcast** | “扫一下这几个播客并写进 wiki” | `wiki/sources/` + `output/pod2wiki/` | 需要 LLM key |

零 key 可用：wiki、research、hypothesis、screen 的 websearch 模式，以及 daily-watch 的报告骨架和部分无 key 降级源。

按需增强：

- 播客摘要：DeepSeek / Kimi / GLM / Qwen 等兼容 LLM API；
- A 股行情：tushare；
- 全球行情 / 财报 / 宏观：FMP；
- 多市场查询和筛选：可另装 [Longbridge Skill](https://open.longbridge.com/zh-CN/skill/)。

---

## 为什么不是一个普通模板？

普通模板只给你目录。AI Workspace Hub 给的是一套 **agent-readable workflow protocol**。

核心不是“文件夹长什么样”，而是：agent 进入目录后知道先读什么；做研究时知道先查本地 wiki；输出时知道事实、推测、待验证要分开；暂停时知道把进度写到 active-context；明天继续时知道从哪里接上。

> 系统不在某个模型里，而在这套文件协议里。谁读懂这套协议，谁就接上你的工作流。

---

## 目录结构

```text
ai-workspace-hub/
├── AGENTS.md                 # Codex 入口路由
├── CLAUDE.md                 # Claude Code 入口路由
├── INSTALL-FOR-AI.md         # 交给 AI agent 的安装协议
├── SMOKE-TEST.md             # 冒烟测试
├── ARCHITECTURE.md           # 架构说明
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

---

## 数据源与边界

| 名称 | 类型 | 用途 | 是否内置 |
|------|------|------|----------|
| Nasdaq | 无 key 降级源 | 美股基础行情 | 是 |
| tushare | API 数据源 | A 股行情 / 财务 | 是，需 token |
| FMP | API 数据源 | 全球行情 / 财报 / 宏观 | 是，需 key |
| Longbridge Skill | 外部 Agent 扩展 | 多市场查询、筛选、研究 | 否，独立安装授权 |
| websearch | Agent 能力 | 补充新闻、资料、公司信息 | 取决于 agent |

重要边界：本项目不做自动交易，不承诺数据源永远免费，不把 AI 输出包装成投资建议。价格、财报、新闻、监管等动态信息需要当场验证；没有 key 时，无法验证的数字必须标 `[待验证]`。

缺少 API key 时，项目应该优雅降级：Core Mode 继续可用，Enhanced Mode 中依赖数据源的部分显示警告或跳过，而不是让用户误以为整个工作区坏了。

---

## 第一周怎么用

| 天数 | 动作 | 目标 |
|:----:|------|------|
| Day 1 | 跑通 `inbox/first-note.md → wiki` | 确认 agent 读得懂工作区 |
| Day 2 | 放入 3-5 条真实材料 | 建立第一批知识库 |
| Day 3 | 让 agent 研究一个公司 / 行业 | 生成第一篇结构化报告 |
| Day 4 | 运行 `check_workspace.py`，按需配置 tushare / FMP，或另装 Longbridge Skill | 增强行情能力 |
| Day 5 | 做一次主题筛选 | 形成候选池 |
| Day 6 | 配 LLM key，扫一次播客 / 博客 | 建立外部信息流 |
| Day 7 | 运行结构体检，删掉没用规则 | 防止系统变胖 |

---

## 常用命令

```bash
python3 system/scripts/check_workspace.py
python3 -m unittest discover -s tests -v
python3 tools/daily-watch/scripts/check_setup.py --init
python3 tools/podcast/scripts/fetch_podcasts.py --help
```

Core Mode 不需要 Python 依赖。Python 工具需要 Python 3.10+；如果你的 `python3` 指向 3.9，请改用 `python3.10` / `python3.11` / `python3.12`，或安装新版 Python。

---

## Roadmap

- 更清晰的 examples；
- 更多真实研究工作流样例；
- 更强的 screen 预设；
- 更完善的 daily-watch 降级策略；
- 更好的 Obsidian / personal wiki 兼容说明；
- 更多 agent 入口适配。

---

## Contributing

欢迎提 issue / PR，尤其是新 agent 适配、研究报告模板、数据源接入、真实使用摩擦点、README / 教程 / 安装流程改进。

---

## Star History

如果这个项目对你有帮助，欢迎点一下 ⭐ Star。它会帮助更多需要“长期 AI 工作流”的人发现这个项目，也会让我知道哪些方向值得继续做。

[![Star History Chart](https://api.star-history.com/svg?repos=Benboerba620/ai-workspace-hub&type=Date)](https://www.star-history.com/#Benboerba620/ai-workspace-hub&Date)

---

## Disclaimer

AI Workspace Hub 是个人研究与知识管理工具，不构成投资建议。所有市场数据、公司信息、财务数字、新闻和监管信息都应以原始来源为准。

<!-- 文件说明：项目首页、价值介绍和快速上手。 -->

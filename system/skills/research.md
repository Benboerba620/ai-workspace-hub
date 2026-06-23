# Research Skill（研究闭环）

> 基座能力，零依赖即可起步：核心输入 = `wiki/` 已有知识 + websearch（Claude / Codex 都自带）。
> 外挂数据源（tushare / gangtise / 自有 API）是**可选数据源**，配了就用，没配就跳过并标注 `[待验证]`，绝不编造数字。
> 目标是形成闭环：**查已有 → 补外部 → 按要点输出 → 讨论升级 → 确认后回写 wiki**。

## 触发词

用户说"研究 X" / "research X" / "帮我研究 / 分析一下 {主题}" / "深挖 {公司 / 行业 / 问题}"。

## 第 0 步：收敛 / 发散自检（先对齐，别闷头查）

动手前先判断模式，动词模糊（"研究""分析下"）时给用户两个具体候选再开工：

- **收敛任务**（决策、评估、加减仓）：先定 2-4 条可验证条件。
- **发散任务**（探索、摸行业、追线索）：不预设结论，结尾走"知识沉淀"。

确认这次研究的**关注要点**。默认套用下面的「研究要点模板」；用户有自己的要点清单（如只看"竞争格局 + 估值"）就按用户的来，可在 `workspace/workspace-config.md` 的 `research:` 段固化常用要点。

## 第 1 步：输入源（本地优先，逐层外扩）

按顺序，能在前一层解决就不必往后：

1. **wiki/（本地，最先查）**：检索 `wiki/sources/`、`wiki/entities/`、`wiki/concepts/`、`wiki/explorations/` 里已有的相关页面。
   - **矛盾扫描**：发现新材料与 wiki 已有结论冲突，直接指出"与 `{文件}` 不一致：`{具体矛盾}`"——补盲点，不是证错。
   - 避免重复研究：已有 exploration 覆盖的，先读它再决定要不要更新。
2. **websearch（联网补充）**：wiki 不够时联网。每条结论标来源；抓不到全文就走 `WebFetch` / 代理，全失败标注"待人工搜索"。
3. **可选数据源（用户自有 API）**：如 tushare（A股行情财务）、gangtise（卖方纪要）或用户自己的 API。
   - 这些是**可选数据源**，照 `system/integrations/_template.md` 接入，在 `workspace/workspace-config.md` 的 `data_sources:` 段登记 endpoint / 取数方式（key 走环境变量，不写进 repo）。
   - **没配置就跳过**，把需要它的数字标 `[待验证]` 并说明"需 {数据源} 补"，**不要编造**。

## 第 2 步：按研究要点输出

写到 `output/research/YYYY-MM-DD-{topic}.md`。默认结构（用户要点优先）：

```markdown
---
title: {研究主题}
date: YYYY-MM-DD
type: research
status: draft
mode: 收敛 / 发散
tags: []
---

# {研究主题}

## 研究问题与范围
- 要回答什么、边界在哪。收敛任务在此列出 2-4 条可验证条件。

## 关注要点
- 逐条对应本次要点清单（默认：业务/驱动因子、竞争格局、关键数据、风险、催化剂）。

## 核心结论
- 一句话能讲清的判断，事实与推测分开。

## 关键证据
- 每条标来源：[本地]=wiki / [网页]=websearch / [数据]=API / [推测] / [待验证]。

## 反方证据 / 风险
- 主动找证伪，不只堆支持证据。

## 关键数据
- 来自 API / wiki / web 的数字，逐个标来源；缺的标 [待验证] + 需何数据源。

## 待验证问题
- 这次没解决、需要进一步查或问的。

## 下一步
- 具体动作。

Wiki check: 查了 wiki/ 的 {x} 篇，{命中/未命中/有矛盾}。
```

**硬规则**：每个事实 / 数字都带来源标注；`[本地]` / `[网页]` / `[数据]` / `[推测]` / `[待验证]` 分清楚。投资决策依赖这份输出，把推测包装成事实会误导判断。

## 第 3 步：讨论升级（闭环的中段）

输出交付后，用户往往会继续追问、挑战、要求深挖某一点。这一轮交互里产生的新判断、被推翻的旧假设、达成的共识，都是研究的真正增量——**不要让它们停在对话里蒸发**。

跟进讨论时持续维护同一份 `output/research/` 文件（用 Edit 更新，不要每轮新建）。

## 第 4 步：闭环回写 wiki（确认后才写）

研究告一段落、或讨论出明确结论时，**主动提示一次**（一次对话最多提 1-2 次，避免噪音）：

> 💡 这次研究 + 讨论的结论要沉淀进 wiki 吗？

用户确认后，按 `wiki/_schema.md` 分流（**只有长期有用的判断才回写，不要把整篇 output 塞进 wiki**）：

| 内容 | 写入 |
|---|---|
| 跨来源的阶段性综合判断 / thesis | `wiki/explorations/YYYY-MM-DD-{topic}.md`（`status: tentative`） |
| 新出现、未来会反复查的公司 / 人 / 产品 | `wiki/entities/{name}.md` |
| 可复用的概念 / 框架 / 行业认知 | `wiki/concepts/{slug}.md` |
| 引用到的单篇外部来源摘要 | `wiki/sources/YYYY-MM-DD-{slug}.md` |

回写时维护**双向关联**：新 exploration 链接到引用的 sources / entities；更新 entity 时检查相关页面的关联网络。

最后更新 `workspace/meta/active-context.md` 记一行（主题 + 状态 + 文件 + 下一步锚点）。

## 不做什么

- 没配的数据源不编数字，标 `[待验证]`。
- 用户没确认不回写 wiki（output/ 可以先落地，wiki/ 必须确认）。
- 不重复已有 exploration——先读再决定更新还是新建。

## 边界与扩展

- 核心链路（wiki + websearch）零依赖，开箱即用。
- 接脚本数据源（tushare / FMP / 自有 API）：在 `workspace-config` 登记，key 走环境变量或 `config/*.env`。Longbridge Skill 需要独立安装和授权，由 Agent 按需调用，不读取本项目的 env。
- 想固化常用研究要点：编辑 `workspace/workspace-config.md` 的 `research:` 段，本 skill 会优先用用户要点。

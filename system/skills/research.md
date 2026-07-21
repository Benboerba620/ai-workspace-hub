# Research Skill（研究闭环）

> 基座能力，零依赖即可起步：核心输入 = `wiki/` 已有知识 + websearch（Claude / Codex 都自带）。
> 外挂数据源（tushare / gangtise / 自有 API）是**可选数据源**，配了就用，没配就跳过并标注 `[待验证]`，绝不编造数字。
> 目标是形成闭环：**查已有 → 补外部 → 按要点输出 → 讨论升级 → 确认后回写 wiki**。

开始前读取 `workspace/research-profile.md`。若版本为“未建立”，改走 `system/skills/first-research.md`；已有偏好则用于调整关注要点和表达，不机械套模板。研究结束统一走 `system/skills/research-closeout.md`。

## 触发词

用户说"研究 X" / "research X" / "帮我研究 / 分析一下 {主题}" / "深挖 {公司 / 行业 / 问题}"。

## 第 0 步：收敛 / 发散自检（先对齐，别闷头查）

动手前先判断模式，动词模糊（"研究""分析下"）时给用户两个具体候选再开工：

- **收敛任务**（决策、评估、加减仓）：先定 2-4 条可验证条件。
- **发散任务**（探索、摸行业、追线索）：不预设结论，结尾走"知识沉淀"。

确认这次研究的**关注要点**。默认套用下面的「研究要点模板」；用户有自己的要点清单（如只看"竞争格局 + 估值"）就按用户的来，可在 `workspace/workspace-config.md` 的 `research:` 段固化常用要点。

## 第 1 步：Research Preflight（必须先扫描本地）

先创建研究文件并分配稳定 ID，再把公司/主题、ticker、产业链位置、周期阶段、约束类型、催化类型和决策场景写成一组明确关键词。运行：

```bash
python3 system/scripts/research_preflight.py --root . \
  --context "英飞凌 IFX.DE 功率半导体 800V 碳化硅 供给瓶颈 公司研究" \
  --research-id {R-ID} --research-file output/research/{报告文件}.md \
  --ticker IFX.DE --record
```

Windows 只有 `python` 时用 `python`。扫描器读取 `workspace-config.md` 的 `wiki_root`，一次完成：

1. 按 `rule → pattern → exploration` 匹配仍然生效的可复用知识；默认排除弱化、失效、退役和归档卡。
2. 扫描 `entities / concepts / sources` 的标题、ticker、concepts、tags、related、摘要和正文；默认不扫 `raw/`。
3. 标出显式过期状态、到期复审、来源字段缺失和已经填写的反方/冲突章节。
4. 生成 `output/research/preflight/{R-ID}.md` 回执；`--research-file` 自动把 `preflight_id / knowledge_used / wiki_pages_loaded` 写进研究报告 frontmatter，研究 ID 不一致时拒绝写入。

Agent 必须打开命中的知识卡和 Wiki 页面全文，再开始外部搜索。关键词命中只是召回，不代表页面结论正确；看到“无关”、反例或冲突时按正文语义判断。脚本失败时允许用本地搜索降级，但必须在 `Wiki check` 写明失败和人工扫描范围，不能静默跳过。

## 第 2 步：输入源（本地优先，逐层外扩）

按顺序，能在前一层解决就不必往后：

1. **Preflight 命中的 Wiki 页面**：先读 Rule / Pattern / Exploration，再读 Entity / Concept / Source。
   - **矛盾扫描**：发现新材料与 wiki 已有结论冲突，直接指出"与 `{文件}` 不一致：`{具体矛盾}`"——补盲点，不是证错。
   - 避免重复研究：已有 exploration 覆盖的，先读它再决定要不要更新。
2. **补充本地检索**：Preflight 未命中但存在别名、旧文件名或弱结构页面时，用本地全文搜索补查，并把新增页面加入 `wiki_pages_loaded`。
3. **websearch（联网补充）**：wiki 不够时联网。每条结论标来源；抓不到全文就走 `WebFetch` / 代理，全失败标注"待人工搜索"。
4. **可选数据源（用户自有 API）**：如 tushare（A股行情财务）、gangtise（卖方纪要）或用户自己的 API。
   - 这些是**可选数据源**，照 `system/integrations/_template.md` 接入，在 `workspace/workspace-config.md` 的 `data_sources:` 段登记 endpoint / 取数方式（key 走环境变量，不写进 repo）。
   - **没配置就跳过**，把需要它的数字标 `[待验证]` 并说明"需 {数据源} 补"，**不要编造**。

## 第 3 步：按研究要点输出

写到 `output/research/YYYY-MM-DD-{topic}.md`。默认结构（用户要点优先）：

```markdown
---
id: RYYYYMMDD-01
title: {研究主题}
date: YYYY-MM-DD
type: research
status: draft
mode: 收敛 / 发散
tags: []
linked_hypotheses: []
linked_entities: []
preflight_id:
knowledge_used: []
wiki_pages_loaded: []
---

# {研究主题}

## 研究问题与范围
- 要回答什么、边界在哪。收敛任务在此列出 2-4 条可验证条件。

## 本地知识加载
- Preflight 回执、命中的知识卡和 Wiki 页面、过期/冲突提示。

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

Wiki check: 引用 Preflight 回执；扫描 {x} 篇，命中知识卡 {y} 张、普通 Wiki {z} 篇，{无复审提示/有过期或冲突提示}。
```

**硬规则**：每个事实 / 数字都带来源标注；`[本地]` / `[网页]` / `[数据]` / `[推测]` / `[待验证]` 分清楚。投资决策依赖这份输出，把推测包装成事实会误导判断。

## 第 4 步：讨论升级（闭环的中段）

输出交付后，用户往往会继续追问、挑战、要求深挖某一点。这一轮交互里产生的新判断、被推翻的旧假设、达成的共识，都是研究的真正增量——**不要让它们停在对话里蒸发**。

跟进讨论时持续维护同一份 `output/research/` 文件（用 Edit 更新，不要每轮新建）。

## 第 5 步：闭环回写 wiki（确认后才写）

研究告一段落、或讨论出明确结论时，**主动提示一次**（一次对话最多提 1-2 次，避免噪音）：

> 💡 这次研究 + 讨论的结论要沉淀进 wiki 吗？

用户确认后，按 `wiki/_schema.md` 分流（**只有长期有用的判断才回写，不要把整篇 output 塞进 wiki**）：

确认请求先追加到 `workspace/review-queue.md`。用户确认后执行回写并把该队列项改成 `done`；不要依赖对话记住一个尚未执行的“以后再写”。

| 内容 | 写入 |
|---|---|
| 跨来源的阶段性综合判断 / thesis | `wiki/explorations/YYYY-MM-DD-{topic}.md`（`status: tentative`） |
| 新出现、未来会反复查的公司 / 人 / 产品 | `wiki/entities/{name}.md` |
| 可复用的概念 / 框架 / 行业认知 | `wiki/concepts/{slug}.md` |
| 引用到的单篇外部来源摘要 | `wiki/sources/YYYY-MM-DD-{slug}.md` |

新建 source、entity、concept 或 exploration 页面后，按 `wiki/_schema.md` 调用统一 `wiki_tagger.py tag ... --apply` 补空字段；已有 `tagging.status: completed` 的页面不会重复调用 API。

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

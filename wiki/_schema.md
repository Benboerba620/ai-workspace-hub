# Personal Wiki Schema

> 这是 personal wiki 的分类规则。Codex / Claude 在摄入材料前先读本文件，再决定写入哪个目录。

## 核心原则

1. 原始材料先保留，再做摘要。
2. 单个来源写 `sources/`，跨来源判断写 `explorations/`。
3. 公司、人、产品、项目写 `entities/`。
4. 可复用主题、框架、概念写 `concepts/`。
5. 任务产物先写 `output/`；只有长期有用的判断才回写 wiki。
6. 事实、推测、待验证必须分开。
7. 索引是加载路由，不是缩短版报告；详细证据保留在页面正文。

## 阅读台可选元数据

使用 Obsidian 阅读台时，可以在任意被阅读台收录的 Markdown 顶部添加：

```yaml
read_status: 已读
```

- 可选值为 `已读` / `精读` / `跳过`；字段缺失或留空都视为未读。
- 阅读台优先把 `source_published_at`、`published_at`、`publish_time` 或 `date` 当作资料日期；其次识别文件名开头的 `YYYY-MM-DD`，再回退到 `created_at`、`created` 和文件时间。
- `status` 仍表示资料处理或知识生命周期状态，不要拿它代替 `read_status`。

## 分类决策树

按顺序判断：

| 问题 | 是 | 否 |
|---|---|---|
| 这是原始材料吗？ | 写入或复制到 `wiki/raw/` | 继续 |
| 这是单个来源的结构化摘要吗？ | 写入 `wiki/sources/` | 继续 |
| 这是公司、人、产品、项目等具体对象吗？ | 写入 `wiki/entities/` | 继续 |
| 这是可复用概念、主题、框架吗？ | 写入 `wiki/concepts/` | 继续 |
| 这是综合多个来源后的判断吗？ | 写入 `wiki/explorations/` | 写入 `output/` 或保留在当前任务 |

## 目录规则

### `wiki/raw/`

放原始材料，尽量不改写。

适合：

- 原文
- 播客转录
- PDF 转出的文本
- 手动放入的长笔记

不适合：

- agent 的综合判断
- 最终报告

### `wiki/sources/`

放单个来源的结构化摘要。

适合：

- 一篇文章的摘要
- 一集播客的摘要
- 一份研报的摘要
- 一次访谈纪要的摘要

要求：

- 必须有 `source_path` 或 `source_url`
- 只总结该来源，不做跨来源大判断
- 可以写“对研究的含义”，但必须标注为 `[推测]` 或 `[待验证]`

建议 frontmatter：

```yaml
---
title:
date:
type: source-summary
source_path:
source_url:
raw_path:
status: processed
read_status:
domain: []
ticker: []
concepts: []
related: []
entity_salience: {}
tags: []
---
```

新建或审核 exploration 后运行 `knowledge_lifecycle.py rebuild-index --apply`。`status` 使用 `tentative / validated / weakened / invalidated / promoted / archived`。只有通过跨案例审查的可迁移机制才进入 `wiki/patterns/`；规则进入 `wiki/rules/`，详见 `system/skills/knowledge-lifecycle.md`。

### `wiki/entities/`

放具体对象档案。

适合：

- 公司
- 人物
- 产品
- 项目
- 机构

创建条件：

- 该对象是材料的主角；或
- 该对象未来大概率会被反复查询；或
- 该对象与当前研究/监控/假设相关。

不创建条件：

- 只是顺嘴提到一次
- 没有后续追踪价值

### `wiki/concepts/`

放可复用概念和框架。

适合：

- 方法论
- 行业概念
- 技术概念
- 分析框架
- 反复出现的主题

创建条件：

- 这个概念能帮助未来分类、搜索或解释其他材料。

### `wiki/explorations/`

放阶段性综合判断。

适合：

- 综合 2 个以上 source 的判断
- agent 对某个问题的阶段性回答
- 需要后续验证的 thesis
- 对已有观点的修正

要求：

- 必须区分：
  - 已验证事实
  - 推测
  - 反方证据
  - 待验证问题
- 默认 `status: tentative`

建议 frontmatter：

```yaml
---
title:
date:
type: exploration
id:
status: tentative
summary:
created_at:
updated_at:
last_reviewed_at:
review_due:
based_on: []
promoted_to:
domain: []
ticker: []
concepts: []
related: []
entity_salience: {}
tags: []
recall_signals: []
decision_scenarios: []
---
```

### `wiki/patterns/` 与 `wiki/rules/`

这两个目录是一条规则一张卡，不再把所有内容堆进单个长文件。

| 类型 | 默认状态 | 生效门槛 | 默认是否加载 |
|---|---|---|---|
| pattern | `draft` | 至少两个独立 exploration、两次 `primary` 确认、写失效信号 | `active` / `promoted` |
| rule | `candidate` | 至少三个独立案例、限定 `scope`、写 `invalidation_signals` | `active` |

三类知识都要填写 `id / summary / review_due / recall_signals / decision_scenarios`。状态变化走 `knowledge_lifecycle.py transition`，用户确认后才加 `--apply --confirmed`。`wiki/patterns/_index.md` 和 `wiki/rules/_index.md` 是自动生成的短摘要；`wiki/rules.md` 与 `workspace/patterns/` 仅为旧版本兼容入口。

## 自动标签契约

新建 source 或 exploration 后，调用同一个打标器：

```bash
python3 system/scripts/wiki_tagger.py --root . --env-file config/pod2wiki.env tag <页面.md> --apply
```

它只补空字段，不覆盖人工已有值：

| 字段 | 用途 | 约束 |
|---|---|---|
| `domain` | 一级领域 | 只用 `investing / reading / tech / life / philosophy / meta` |
| `ticker` | 上市标的代码 | 只写材料直接相关标的 |
| `concepts` | 可复用主题或框架 | 优先复用 `wiki/concepts/` 已有名称 |
| `related` | 页面关联 | 使用带引号的 `"[[页面]]"` wikilink |
| `entity_salience` | source 对标的的重要度 | 只用 `core / reference / mention` |
| `tags` | 跨页面检索捷径 | 最多 5 个，复用旧标签，避免 ticker 和 concept 重复 |

`entity_salience` 的含义：`core` 是材料主角或影响判断，`reference` 是重要对照，`mention` 是顺带出现。批量补历史页面复用同一逻辑，默认只预览：

成功写入后会增加 `tagging: {status: completed, schema_version: 1}`。即使某些字段合法为空，也能据此避免重复调用 API。

```bash
python3 system/scripts/wiki_tagger.py --root . --env-file config/pod2wiki.env backfill wiki
# 确认预览后再加 --apply
```

预览结果缓存在 `workspace/cache/wiki_tagger.json`，随后执行同一命令并加 `--apply` 会直接复用，不重复计费。页面内容或已有标签词表变化后缓存自动失效；需要强制重算时加 `--refresh`。

## `output/` 和 wiki 的边界

`output/` 放任务结果，wiki 放长期知识。

| 内容 | 放哪里 |
|---|---|
| 本次测试报告 | `output/` |
| 日报 | `output/` |
| 文章草稿 | `output/` 或写作目录 |
| 单个来源摘要 | `wiki/sources/` |
| 可复用概念 | `wiki/concepts/` |
| 阶段性综合判断 | `wiki/explorations/` |

如果一个 output 里出现长期有用的判断，另写一页 `wiki/explorations/`，不要把整篇 output 塞进 wiki。

## 命名规则

| 类型 | 命名 |
|---|---|
| raw | `YYYY-MM-DD-{slug}.md` |
| source | `YYYY-MM-DD-{slug}.md` |
| entity | `{entity-name}.md` 或 `{ticker}-{name}.md` |
| concept | `{concept-slug}.md` |
| exploration | `YYYY-MM-DD-{question-or-topic}.md` |

文件名用短 slug。中文可以保留，但公开 repo 示例优先用英文 slug。

## 本次 MVP 的最低合格标准

一次 first-ingest 至少要产生：

1. `wiki/raw/{date}-{slug}.md`
2. `wiki/sources/{date}-{slug}.md`
3. source 的结构化字段完成自动标签，或在报告里明确记录 API 失败
4. 至少一个 `wiki/concepts/` 或 `wiki/entities/` 分类页
5. 如有阶段性判断，写 `wiki/explorations/`
6. 一份 `output/` 测试报告
7. 更新 `workspace/meta/active-context.md`

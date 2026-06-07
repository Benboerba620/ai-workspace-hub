# Personal Wiki Schema

> 这是 personal wiki 的分类规则。Codex / Claude 在摄入材料前先读本文件，再决定写入哪个目录。

## 核心原则

1. 原始材料先保留，再做摘要。
2. 单个来源写 `sources/`，跨来源判断写 `explorations/`。
3. 公司、人、产品、项目写 `entities/`。
4. 可复用主题、框架、概念写 `concepts/`。
5. 任务产物先写 `output/`；只有长期有用的判断才回写 wiki。
6. 事实、推测、待验证必须分开。

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
tags: []
---
```

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
status: tentative
tags: []
---
```

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
3. 至少一个 `wiki/concepts/` 或 `wiki/entities/` 分类页
4. 如有阶段性判断，写 `wiki/explorations/`
5. 一份 `output/` 测试报告
6. 更新 `workspace/meta/active-context.md`


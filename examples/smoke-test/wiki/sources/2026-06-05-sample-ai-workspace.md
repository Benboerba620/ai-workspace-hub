---
title: AI Workspace Smoke Test
date: 2026-06-05
type: source-summary
source_path: inbox/sample-ai-workspace.md
source_pdf: inbox/sample-ai-workspace.pdf
raw_path: wiki/raw/2026-06-05-sample-ai-workspace.md
raw_pdf: wiki/raw/2026-06-05-sample-ai-workspace.pdf
status: processed
tags: [pdf-ingest, personal-wiki, smoke-test]
---

# AI Workspace Smoke Test

## 核心结论

`[本地]` 这份 PDF 测试材料验证了 PDF 输入链路：PDF 可以先转成 Markdown，再按照 `wiki/_schema.md` 分类进入 personal wiki。材料的核心观点是：personal wiki 是知识核心，PDF 不是直接进入输出，而是先转写、分类、再被输出任务读取。

## 关键证据

- `[本地]` PDF 转写后的 Markdown 写明：“personal wiki is the knowledge core.”
- `[本地]` PDF 转写后的 Markdown 写明：“PDF files should become Markdown before classification.”
- `[本地]` PDF 转写后的 Markdown 写明：“Codex should classify the Markdown into source, concept, and output.”
- `[本地]` 本次测试已生成 raw PDF、raw Markdown、source summary、concept、exploration 和 output。

## 知识库分类

| 分类 | 结果 |
|---|---|
| 原始 PDF | `wiki/raw/2026-06-05-sample-ai-workspace.pdf` |
| 转写 Markdown | `wiki/raw/2026-06-05-sample-ai-workspace.md` |
| 来源摘要 | `wiki/sources/2026-06-05-sample-ai-workspace.md` |
| 概念分类 | `wiki/concepts/pdf-to-md-ingest.md` |
| 阶段性判断 | `wiki/explorations/2026-06-05-pdf-ingest-smoke-test.md` |
| 输出报告 | `output/pdf-ingest/2026-06-05-smoke-test.md` |

## 推测

- `[推测]` 对实际用户来说，PDF 转 Markdown 是 personal wiki 的关键前置步骤；如果这一步不可用，后面的分类和输出都会失真。
- `[推测]` 当前 Node smoke parser 只能证明链路可跑，不能代表复杂 PDF 支持已经完备。

## 待验证问题

- `[待验证]` 复杂 PDF、扫描 PDF、表格 PDF 是否需要接入专业解析器。
- `[待验证]` 公开 MVP 是否要内置 PDF 转换脚本，还是只保留为 smoke test 工具。

## 下一步动作

1. 用真实 PDF 或长文档复测。
2. 给 PDF 转换工具增加失败提示和 fallback 建议。
3. 决定是否在 README 中明确 “PDF smoke parser 不是生产级解析器”。


---
title: PDF to Markdown Ingest
type: concept
status: seed
tags: [pdf, ingest, personal-wiki]
---

# PDF to Markdown Ingest

## 定义

PDF to Markdown Ingest 是 personal wiki 的输入前处理流程：PDF 先转成 Markdown，再按 `wiki/_schema.md` 分类进入 raw、sources、concepts、explorations 或 output。

## 为什么需要

- PDF 通常不是 agent 最稳定的长期知识格式。
- Markdown 更容易被 Codex / Claude 读取、引用和分类。
- 转写后的 Markdown 可以保留来源路径，方便追溯到原 PDF。

## 当前 MVP 能力

`[本地]` PDF 是**可选能力**，按 `system/skills/pdf-ingest.md` 首次使用时 agent 自动安装依赖：

```text
system/scripts/pdf_to_md.py   # pypdf，文本型 PDF
```

agent 第一次执行时自检并 `pip install -r requirements-pdf.txt`，再跑 `python system/scripts/pdf_to_md.py <in.pdf> <out.md>`。这条路径可处理文本型 PDF，不承诺解析扫描件/复杂版面。

## 生产级缺口

- 扫描 PDF 需要 OCR。
- 表格和图表需要结构化解析。
- 双栏研报可能需要版面分析。
- 加密或权限 PDF 需要单独失败提示。

## 关联

- Source: `wiki/sources/2026-06-05-sample-ai-workspace.md`
- Exploration: `wiki/explorations/2026-06-05-pdf-ingest-smoke-test.md`


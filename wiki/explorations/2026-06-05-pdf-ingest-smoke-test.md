---
title: PDF Ingest Smoke Test
date: 2026-06-05
type: exploration
status: tentative
tags: [pdf-ingest, smoke-test, personal-wiki]
---

# PDF Ingest Smoke Test

## 核心结论

`[本地]` 当前 starter workspace 可以完成一个最小 PDF 输入闭环：生成测试 PDF、转成 Markdown、写入 raw/source/concept/exploration/output，并让输出任务读取 wiki 产物。

## 已验证事实

- `[本地]` `python system/scripts/pdf_to_md.py inbox/sample-ai-workspace.pdf inbox/sample-ai-workspace.md` 成功把样例 PDF 转成 Markdown（pypdf 6.x，Python 3.11）。
- `[本地]` 原始 PDF 已归档到 `wiki/raw/2026-06-05-sample-ai-workspace.pdf`。
- `[本地]` 转写 Markdown 已归档到 `wiki/raw/2026-06-05-sample-ai-workspace.md`。
- `[本地]` source、concept、exploration 和 output 均已生成。

## 推测

- `[推测]` 对实际用户来说，这条链路已经足够演示 MVP 的工作方式。
- `[推测]` 但这还不能证明系统能处理真实研报或扫描件。

## 反方证据

- `[本地]` PDF 是可选能力，不进基座；用户没装 Python/pypdf 时这条链路不可用，需 agent 现装。
- `[本地]` 当前没有 `pdftotext`、`mutool` 等命令行 PDF 工具，也不依赖它们。
- `[待验证]` pypdf 只适合文本型 PDF，扫描件/双栏/表格仍需 OCR / MinerU / 版面分析。

## 下一步

1. README 中明确 PDF 支持边界。
2. 后续接入生产级 PDF 转换工具。
3. 用真实 PDF 再跑一次。


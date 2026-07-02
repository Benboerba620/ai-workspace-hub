---
title: AI Workspace File Protocol
type: concept
status: seed
tags: [workspace, codex, personal-wiki]
---

# AI Workspace File Protocol

## 定义

AI Workspace File Protocol 指一套给 AI agent 读写的文件系统约定：输入先进知识库，输出落到输出层，长期判断再沉淀回知识库，短期上下文和摩擦反馈单独记录。

## 最小组件

| 组件 | 路径 | 作用 |
|---|---|---|
| 输入 | `inbox/` | 临时材料入口 |
| 原始归档 | `wiki/raw/` | 保存未加工材料 |
| 来源摘要 | `wiki/sources/` | 单个来源的结构化摘要 |
| 概念 | `wiki/concepts/` | 可复用主题和框架 |
| 综合判断 | `wiki/explorations/` | 跨来源判断 |
| 输出 | `output/` | 报告、日报、测试结果 |
| 短期记忆 | `workspace/meta/active-context.md` | 最近仍要带入的上下文 |
| 摩擦反馈 | `workspace/meta/friction-log.md` | 系统哪里卡住了 |

## 本次试跑结论

`[本地]` 通过 `inbox/first-note.md` 的 first-ingest 测试，最小协议可以完成输入、raw 归档、source 摘要、concept 分类、exploration 判断和 output 汇总。

## 关联

- Source: `wiki/sources/2026-06-05-first-note.md`
- Exploration: `wiki/explorations/2026-06-05-first-ingest-smoke-test.md`


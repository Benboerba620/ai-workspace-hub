---
title: First Ingest Smoke Test
date: 2026-06-05
type: exploration
status: tentative
tags: [smoke-test, personal-wiki, codex]
---

# First Ingest Smoke Test

## 核心结论

`[本地]` 这个 starter workspace 已经可以完成一次最小运行：从 `inbox/first-note.md` 出发，生成 raw、source、concept、exploration 和 output。它不依赖联网、不依赖 pod2wiki、不依赖 daily-watchlist。

## 已验证事实

- `[本地]` 根目录存在 `AGENTS.md`，Codex 有明确入口。
- `[本地]` `workspace/workspace-config.md` 定义了 personal wiki 的核心目录。
- `[本地]` `system/integrations/personal-wiki.md` 定义了知识库路由。
- `[本地]` `system/skills/first-ingest.md` 定义了试跑流程。
- `[本地]` 本次试跑已写入：
  - `wiki/raw/2026-06-05-first-note.md`
  - `wiki/sources/2026-06-05-first-note.md`
  - `wiki/concepts/ai-workspace-file-protocol.md`
  - `wiki/explorations/2026-06-05-first-ingest-smoke-test.md`
  - `output/first-ingest/2026-06-05-smoke-test.md`

## 推测

- `[推测]` 对零代码用户来说，这种“文件协议 + Codex 自然语言执行”的 MVP，比先写脚本更容易理解。
- `[推测]` 首版 GitHub README 应把“直接试跑 first-note”放在安装协议前面，因为它最能降低理解成本。

## 反方证据

- `[待验证]` 当前输入非常短，尚不能证明它能处理复杂播客、研报或多来源冲突。
- `[待验证]` 当前没有 `wiki/_schema.md`，真实使用时可能需要更强的 source frontmatter 规范。

## 下一步

1. 用真实文章做第二次 smoke test。
2. 增加 `wiki/_schema.md` 的最小版本。
3. 决定 pod2wiki 的发行方式：文档接口、submodule 或安装器拉取。


---
title: First Note
date: 2026-06-05
type: source-summary
source_path: inbox/first-note.md
raw_path: wiki/raw/2026-06-05-first-note.md
status: processed
tags: [workspace, personal-wiki, smoke-test]
---

# First Note

## 核心结论

这条输入验证了 AI Workspace Hub 的最小闭环：一段临时输入可以先归档为 raw，再结构化为 source，并进一步分类到 concept / exploration / output。系统的核心不是某个工具，而是稳定的文件路由。

## 关键证据

- `[本地]` 输入材料明确提出：对话上下文会过期，文件系统不会。
- `[本地]` 输入材料要求材料先进入 `wiki/raw/` 和 `wiki/sources/`，再用于输出。
- `[本地]` 输入材料定义了两类轻量系统记忆：`active-context.md` 保存近期上下文，`friction-log.md` 记录流程摩擦。
- `[本地]` 当前试跑已创建 raw、source、concept、exploration 和 output 文件，说明基本读写路径成立。

## 知识库分类

| 分类 | 处理结果 |
|---|---|
| raw | `wiki/raw/2026-06-05-first-note.md` |
| source | `wiki/sources/2026-06-05-first-note.md` |
| concept | `wiki/concepts/ai-workspace-file-protocol.md` |
| exploration | `wiki/explorations/2026-06-05-first-ingest-smoke-test.md` |
| output | `output/first-ingest/2026-06-05-smoke-test.md` |

## 待验证问题

- `[待验证]` 这个最小结构是否足够支持真实材料，而不只是示例输入。
- `[待验证]` pod2wiki 应保持可选输入模块，还是在某些发行版本中作为默认安装项。

## 下一步动作

1. 用一篇真实文章或播客笔记替换 `inbox/first-note.md` 再跑一次。
2. 决定 GitHub 首版是否包含更完整的 `wiki/_schema.md`。
3. 决定 pod2wiki 是 submodule、外部路径，还是仅文档接口。


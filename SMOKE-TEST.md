# Smoke Test

## Core Mode（零 API / 零依赖）

先运行总检查：

```bash
python3 system/scripts/check_workspace.py    # Windows: python system/scripts/check_workspace.py
```

预期：`Core Mode result: READY`。Enhanced Mode 里的 Python 版本、依赖包或 API key 警告不代表安装失败，只代表可选自动化暂未开启。

用 Codex 或 Claude 打开本目录后，发送：

> 把 `inbox/first-note.md` 整理进 personal wiki。

预期结果：

1. 新建 `wiki/sources/YYYY-MM-DD-first-note.md`。
2. 文件包含标题、来源、核心结论、关键证据、待验证问题、下一步动作。
3. `workspace/meta/active-context.md` 追加或更新一条试跑完成记录。
4. 不需要联网，不需要任何依赖。

生成的 wiki 页面大致如下：

```markdown
---
title: 我对 AI 工具的使用心得
source_type: note
date: 2026-06-24
status: evergreen
---

# 我对 AI 工具的使用心得

## 核心结论
AI 编程助手正在改变开发者的工作方式，核心价值在于"AI + 文件系统"的组合。

## 关键证据
- 重复性代码交给 AI，人专注架构和设计
- 文件系统沉淀知识比对话记忆高效
- AI 读到已有笔记后回答质量大幅提升

## 待验证
- [ ] wiki 系统在多人协作场景下的效果
- [ ] 长期积累的 wiki 维护难度

## 下一步
- 尝试更多材料的摄入（播客、PDF、研报）
```

（这只是示意，实际格式取决于 agent 对 `wiki/_schema.md` 的理解。）

## Enhanced Mode：播客工具（需 Python + 可选 LLM key）

以下命令默认使用 `python3`，且需要 Python 3.10+。先运行 `python3 --version`；如果版本低于 3.10，请改用 `python3.10` / `python3.11` / `python3.12`，或安装新版 Python。如果你的环境只有 `python` 且版本 ≥3.10，把命令里的 `python3` 替换成 `python` 即可。

```bash
python3 -m pip install -r tools/podcast/requirements.txt
python3 tools/podcast/scripts/fetch_podcasts.py --help
```

预期：输出帮助信息，无报错。

如果没有 `LLM_API_KEY`，使用播客功能时应走 `--no-llm` 或低置信降级路径；这不影响 Core Mode。

## Enhanced Mode：日报工具（需 Python + 可选行情 key）

```bash
python3 -m pip install -r tools/daily-watch/requirements.txt
python3 tools/daily-watch/scripts/check_setup.py --init
```

预期：缺失的示例配置会被初始化；缺 API key 只显示警告或跳过对应数据源，必要目录和依赖检查通过。

## 自动测试

```bash
python3 -m unittest discover -s tests -v
```

预期：安装器、路径识别、文档链接和仓库契约测试全部通过。

## 快速筛选（Core Mode 可用）

> 帮我筛选一下价值股。

预期：agent 用 websearch 找候选、输出表格到 `output/screen/`。

<!-- 文件说明：最小可运行测试说明。 -->

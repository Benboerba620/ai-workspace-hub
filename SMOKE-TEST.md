# Smoke Test

## 基座（零依赖）

用 Codex 或 Claude 打开本目录后，发送：

> 把 `inbox/first-note.md` 整理进 personal wiki。

预期结果：

1. 新建 `wiki/sources/YYYY-MM-DD-first-note.md`。
2. 文件包含标题、来源、核心结论、关键证据、待验证问题、下一步动作。
3. `workspace/meta/active-context.md` 追加或更新一条试跑完成记录。
4. 不需要联网，不需要任何依赖。

## 播客工具（需 Python）

```bash
pip install -r tools/podcast/requirements.txt
python tools/podcast/scripts/fetch_podcasts.py --help
```

预期：输出帮助信息，无报错。

## 日报工具（需 Python）

```bash
pip install -r tools/daily-watch/requirements.txt
python tools/daily-watch/scripts/check_setup.py
```

预期：输出环境检查结果（缺 API key 会提示，不算失败）。

## 快速筛选（零依赖）

> 帮我筛选一下价值股。

预期：agent 用 websearch 找候选、输出表格到 `output/screen/`。

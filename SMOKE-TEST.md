# Smoke Test

用 Codex 打开本目录后，发送：

> 把 `inbox/first-note.md` 整理进 personal wiki。

预期结果：

1. 新建 `wiki/sources/YYYY-MM-DD-first-note.md`。
2. 文件包含标题、来源、核心结论、关键证据、待验证问题、下一步动作。
3. `workspace/meta/active-context.md` 追加或更新一条试跑完成记录。
4. 不需要联网，不需要 pod2wiki，不需要 daily-watchlist。


# First Ingest Skill

当用户说“试跑”“first ingest”“把 inbox 材料整理进 wiki”时，执行这个最小流程。

## 输入

**任意** `inbox/` 下的材料文件，用户指定哪个就处理哪个。下面用 `{输入文件}` 指代；`inbox/first-note.md` 只是 repo 自带的试跑样例，不是唯一可处理对象。

## 步骤

1. 读取 `AGENTS.md`（Codex）或 `CLAUDE.md`（Claude）。
2. 读取 `workspace/workspace-config.md`。
3. 读取 `wiki/_schema.md`。
4. 读取 `system/integrations/personal-wiki.md`。
5. 读取 `{输入文件}`（用户未指定时默认 `inbox/first-note.md`）。
6. 创建 `wiki/sources/YYYY-MM-DD-{输入文件名}.md`。
7. 输出结构包含：
   - 标题
   - 来源
   - 核心结论
   - 关键证据
   - 待验证问题
   - 下一步动作
8. 按 `wiki/_schema.md` 判断是否需要创建 `concepts/`、`entities/` 或 `explorations/` 页面。
9. 更新 `workspace/meta/active-context.md`，记录试跑完成。
10. 如果过程中发现路径缺失或规则不清，追加到 `workspace/meta/friction-log.md`。

## 不做什么

- 不联网。
- 不调用 pod2wiki。
- 不修改 `hypothesis/`。
- 不生成日报。

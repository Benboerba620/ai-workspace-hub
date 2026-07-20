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
6. 把原始材料归档到 `wiki/raw/YYYY-MM-DD-{输入文件名}.md`（尽量不改写）。
7. 创建 `wiki/sources/YYYY-MM-DD-{输入文件名}.md`，按 `wiki/_schema.md` 写入 frontmatter，正文包含：
   - 标题
   - 来源
   - 核心结论
   - 关键证据
   - 待验证问题
   - 下一步动作
8. 用统一打标器补齐空的结构化字段：
   ```bash
   python3 system/scripts/wiki_tagger.py --root . --env-file config/pod2wiki.env tag wiki/sources/YYYY-MM-DD-{输入文件名}.md --apply
   ```
   Windows 用 `python`。脚本只补空字段，不覆盖已有人工值；API 缺失或失败时保留空字段，在报告中写明，不阻塞归档和摘要。
9. 根据打标结果和 `wiki/_schema.md` 分类决策树，**至少创建一个** `concepts/` 或 `entities/` 分类页；如有综合多来源的判断，另写 `wiki/explorations/`。这些新页面也用同一条 `wiki_tagger.py tag ... --apply` 命令补空字段。
10. 写一份 `output/YYYY-MM-DD-{输入文件名}-report.md` 试跑报告（处理了什么、标签写入了哪些字段、产出了哪些文件、遇到什么问题）。
11. 更新 `workspace/meta/active-context.md`，记录试跑完成。
12. 如果过程中发现路径缺失或规则不清，追加到 `workspace/meta/friction-log.md`。

以上第 6-11 步与 `wiki/_schema.md` 的「本次 MVP 的最低合格标准」一一对应，两份文档改一处要同步另一处。

## 不做什么

- 不联网抓取或补充外部事实；自动标签只把当前材料发送给用户配置的大模型 API。
- 不调用 pod2wiki。
- 不修改 `hypothesis/`。
- 不生成日报。

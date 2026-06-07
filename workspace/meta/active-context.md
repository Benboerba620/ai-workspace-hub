# Active Context

> 工作记忆，支撑“今天停、明天接”的断点续传（协议见 `AGENTS.md` / `CLAUDE.md` 的「active-context：断点续传」段）。
> 只保留最近 1-2 周仍值得带入对话的上下文，单条一行。结束时 agent 自动往下面追一行，开场说“继续”时 agent 顺着最新一条的「续接锚点」接上。

## 最近对话延续

- **2026-06-05：first-ingest smoke test（DONE）** -> 已用 `inbox/first-note.md` 完成输入 -> raw/source/concept/exploration/output 闭环；主要产物 `wiki/sources/2026-06-05-first-note.md` 和 `output/first-ingest/2026-06-05-smoke-test.md`；下一步用真实文章或播客笔记复测。
- **2026-06-05：personal wiki schema（DONE）** -> 已新增 `wiki/_schema.md`，确定 raw/source/entity/concept/exploration/output 分类决策树；入口文件已要求摄入前读取 schema。
- **2026-06-05：PDF ingest smoke test（DONE，带限制）** -> 已生成 `inbox/sample-ai-workspace.pdf` 并转为 `inbox/sample-ai-workspace.md`；完成 raw PDF/raw Markdown/source/concept/exploration/output 写入，并生成 `output/wiki-read-priority/2026-06-05-answer-from-wiki.md` 验证输出优先读取 wiki。限制：当前 PDF parser 仅 smoke-test 级别，复杂 PDF 需专业工具。
- **2026-06-05：Python PDF option（DONE，未在本机执行）** -> 已新增 `requirements-pdf.txt` + `system/scripts/pdf_to_md.py`，文档和 `system/skills/pdf-ingest.md` 已说明 Python+pypdf 文本 PDF 路径；当前机器 `python` 不可用，因此只验证文件和入口，未实际运行 Python 转换。
- **2026-06-06：wiki-first-output skill（DONE）** -> 已新增 `system/skills/wiki-first-output.md`，输出任务先读 personal wiki 再写 `output/`；已在 `AGENTS.md`/`CLAUDE.md`/`README.md`/`INSTALL-FOR-AI.md` 挂入口。
- **2026-06-06：wiki-first-output routing（DONE）** -> Yibo 判断仅放 skill 不够；已在 `workspace/workspace-config.md` 和 `system/templates/workspace-config.md` 增加 `wiki-first-output` 路由开关与触发条件，skill 只保留详细执行规则。
- **2026-06-06：系统减法（DONE）** -> Yibo 判断 preflight/wiki-first-output 设计偏复杂；已删除 `system/skills/context-preflight.md` 和 `system/skills/wiki-first-output.md`，默认规则收回到 `workspace-config.md` 的三条简单规则：输入按 schema、研究/写作/输出先查 active-context+wiki 并留 `Wiki check`、卡住写 friction-log。

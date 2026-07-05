# Post-Install Cleanup Skill（安装后瘦身）

> 目的：装好、试跑过之后，把"安装/上手专用"的内容从工作区里清掉，让 agent **每次必读的文件更轻**，减轻路由负担。
> 这是 onboarding 模式 → 日常运行模式的一次性切换。

## 触发词

用户说"我装好了" / "精简系统" / "清理安装内容" / "我熟悉了，瘦身吧"；或安装流程末尾（`INSTALL-FOR-AI.md` Step 8）主动提议。

## 前置确认（先问，别直接动手）

1. 确认用户**已完成首次试跑、不再需要上手引导**。没试跑过就先别清。
2. 告诉用户：清理只动"安装脚手架和上手文字"，**绝不碰你自己摄入的材料 / 输出 / 假设**。
3. 默认**归档（mv 到 `_archive/`）而不是硬删**，用户想彻底删再说。动手前列出清单让用户过目。

## 第一步：归档安装脚手架

把下列"只在安装/上手时有用"的东西 mv 到 `_archive/`（保留可回溯）：

| 类别 | 路径 |
|---|---|
| 安装说明 | `INSTALL-FOR-AI.md`、`SMOKE-TEST.md` |
| 安装模板（已复制进工作区） | `system/templates/` |
| 试跑样例输入 | `inbox/first-note.md`、`inbox/sample-ai-workspace.pdf`、`inbox/sample-ai-workspace.md` |
| 试跑 smoke 产物 | `wiki/raw/2026-06-05-*`、`wiki/sources/2026-06-05-*`、`wiki/explorations/2026-06-05-*`、`output/first-ingest/`、`output/pdf-ingest/`、`output/wiki-read-priority/` |

> 注意来源差异：用 `install_workspace.py` 装出的工作区**没有** `INSTALL-FOR-AI.md`、`SMOKE-TEST.md` 和 smoke 产物（它们只存在于直接 clone 的仓库副本里）。表里列的路径**不存在就跳过**，不算异常。

**判断项（问用户，不要默认删）**：
- `wiki/concepts/ai-workspace-file-protocol.md`、`wiki/concepts/pdf-to-md-ingest.md` 是讲系统理念的概念页，可能有长期参考价值——问用户保留还是归档。**若选择保留**：这两页里链向 `wiki/sources/2026-06-05-*` / `wiki/explorations/2026-06-05-*` 等 smoke 产物的链接会随归档悬空，必须一并把链接改指 `_archive/...` 或删掉死链，别留断链。

**不要动**：用户自己摄入的 wiki 页面、自己的 output、monitoring、hypothesis、active-context、friction-log、workspace-config，以及任何已部署的模块目录。

## 第二步：精简每次必读文件

从 `AGENTS.md` 和 `CLAUDE.md`（两个都改，保持同源）里：

1. **删掉「最小试跑」整段**——它是一次性上手内容，日常不再需要。
2. **把「可选能力」段压成一个简短指针块**，例如：

   ```markdown
   ## 扩展

   - 所有工具已内置（`tools/podcast/`、`tools/daily-watch/`）。
   - PDF 摄入等可选能力见 `system/skills/`，自建照 `system/skills/_template.md`。
   - 自建新工具照 `system/integrations/_template.md`。
   ```
3. **完整保留核心路由表**——尤其「摄入材料」那一行里对 `system/skills/first-ingest.md`、`system/skills/pdf-ingest.md`、`system/integrations/personal-wiki.md` 的指针**绝不能删**：删了「最小试跑」段后，这一行就是这些 skill / 模块在日常必读文件里的**唯一入口**，删掉它们会变成孤岛。
4. **保留**：工作方式（含删除/覆盖/推送前确认红线）、active-context / friction 规则、加规则前判断范围。

> 不要拿 `_archive/` 里归档的旧模板当目标照抄——以本步定义的"留什么删什么"为准。删完后自查：`grep -rl "system/skills/\|system/integrations/" AGENTS.md CLAUDE.md`，确认每个仍在 `system/skills/`、`system/integrations/` 里的文件都还能从 AGENTS/CLAUDE 找到，没有断引用。

### 第二步补：清扫归档样例的残留引用（别只改必读文件）

归档样例输入 / smoke 产物后，这些路径常被别处引用着，必须一并处理，否则留一堆指向 `_archive/` 的死链：

1. 全局扫一遍刚归档的样例路径在哪还被提到：`grep -rn "first-note\|sample-ai-workspace\|2026-06-05-" . --include="*.md" | grep -v "_archive/"`。
2. 命中的地方按性质处理：`README.md` / skill 里的**上手示例**——同步精简或改指 `_archive/...`；`workspace/meta/active-context.md` 里的**历史条目**——把 DONE 旧条目浓缩归档（剪到 `_archive/active-context-*.md`），不要留指向已归档样例的悬空路径。
3. 别漏 `active-context.md`：它最容易残留"6/05 smoke test（DONE）→ 某样例文件"这类条目。

## 第三步：同步 README（避免滞后）

`README.md` 不是每次必读，但仍是门面。瘦身后检查它有没有残留已归档的路径（`inbox/first-note.md`、`SMOKE-TEST.md`、目录树里的 `system/templates/` 等），把上手段落同步精简或标注，别让 README 指向 `_archive/` 里的东西。

## 第四步：报告

告诉用户：
- 归档了哪些文件（到 `_archive/`）。
- `AGENTS.md` / `CLAUDE.md` 从 **X 行 → Y 行**，`wc -l` 给实数。
- 工作区现在进入"日常运行模式"，以后用 `system/skills/structure-health.md` 每周体检防止再变胖。

## 边界

- 一次性操作，跑完即可。误删风险全靠"先归档不硬删 + 先列清单确认"兜底。
- 不改用户的任何知识内容，只改安装脚手架和必读文件里的上手段落。

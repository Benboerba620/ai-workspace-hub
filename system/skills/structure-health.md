# Structure Health Skill（结构体检）

> 目的：定期扫一遍 agent **每次都要读的必读文件**和**目录结构**，给出"精简建议"，防止系统随时间变胖、路由变重。
> 这是把"加规则前的三个问题"那条防臃肿纪律，变成一个可重复运行的检查。
> **只给建议，不自动改**——任何删改都留给用户确认。

## 触发词

用户说"结构体检" / "精简建议" / "系统是不是变胖了" / "体检一下"；或用户自己挂的每周定时任务（见末尾"怎么排程"）。

## 检查项

### A. 必读文件行数 vs 软上限

`wc -l` 量下面这些每次必读的文件，超限就指出**哪一段最肥、能不能拆到 skill 或删**：

| 文件 | 软上限（行） |
|---|---|
| `AGENTS.md` / `CLAUDE.md` | ~60 |
| `workspace/workspace-config.md` | ~100 |
| `workspace/meta/active-context.md` | 50 |
| `wiki/_schema.md` | ~200 |
| `system/interfaces/README.md` | ~80 |

### B. active-context 卫生

- 有没有 **超过 14 天**、状态已 `DONE` 还没归档的条目 → 建议剪到 `_archive/` 或删。
- 总行数有没有超 50 → 建议浓缩。
- 同一主题有没有重复堆叠多条 → 建议合并成一条。

### C. AGENTS / CLAUDE 同源漂移

- 归一化对比两文件（agent 名差异除外），列出任何路由 / 红线 / 模块清单的不一致 → 建议同步。

### D. 目录结构

- **空目录 / 只有 `.gitkeep`** 且长期没用 → 提示是否还需要。
- **存在但 `workspace-config` 没登记** 的目录，或登记了却不存在 → 指出对不上。
  - **例外**：`status: planned` 的模块，其 `reads_from` / `writes_to` 目录（如 `output/daily-watchlist/`、`wiki/raw/podcasts/`）尚未创建是**正常的**——那是装了模块才生成的输出槽，不算"缺失"，别报。
- **职责重复** 的目录（两个地方放同类东西）→ 建议合并。
- 安装脚手架（`INSTALL-FOR-AI.md`、`system/templates/`、`SMOKE-TEST.md`、6/05 smoke 产物）**是否还在** → 若用户已上手，提示跑 `system/skills/post-install-cleanup.md`。

### E. 一次性规则混入必读文件

- 扫 `AGENTS.md` / `CLAUDE.md` / `workspace-config.md` 里有没有**只对某一次任务有效**的规则（违反"加规则前判断范围"）→ 建议下放到对应 skill 或删除。

## 输出

写一份体检报告到 `output/health/YYYY-MM-DD-structure.md`，每条用统一格式：

```markdown
- **发现**：active-context 现 78 行，超 50 行软上限
- **建议**：把 5 月已 DONE 的 9 条剪到 _archive/active-context-2026-05.md
- **影响范围**：减轻每次 session 的工作记忆负担约 30 行
- **破坏性**：需用户确认（涉及移动文件）
```

报告末尾给一个**一句话总评**（系统是偏瘦、健康、还是开始变胖）+ **最该先改的 1 件事**。

## 怎么排程（建议用户自己挂，本 skill 不替用户挂）

每周跑一次最理想。按你用的工具自己设：

- **Claude Code**：用 `/schedule` 建一个每周触发的 routine，或系统 cron 每周调用一次"运行 structure-health"。
- **Codex**：用它的计划任务 / 定时功能，每周触发同一句指令。
- **最低限度**：不想挂自动化，就每周自己说一句"结构体检"。

> 本 skill 不会自动创建定时任务——排程是环境相关的，交给你按自己的工具设，避免在不通用的地方写死。

## 边界

- 只读不改：体检只产出建议报告，绝不自动删改任何文件。
- 破坏性操作（删条目、移目录、改必读文件）一律等用户看完报告点头再做。

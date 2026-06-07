# {模块名} Integration（外挂模块）

> 复制本文件为 `system/integrations/{模块名}.md`，按下面的槽填好，就把一个**外部项目**接进了基座的槽位。
> 已填好的范例：`system/integrations/pod2wiki.md`（输入侧）、`system/integrations/personal-wiki.md`（默认核心）、`system/interfaces/README.md` 里的 daily-watchlist（输出侧）。
>
> 「能力」和「模块」的区别：
> - **能力**（`system/skills/`）= 住在本 repo 里的动作，可能带脚本，agent 自装依赖。例：pdf-ingest。
> - **模块**（本文件）= 一个**独立的外部项目**（你的 repo 或别人的），通过**文件契约**接进来。基座不复制它的源码，只规定它读哪里、写哪里。例：pod2wiki、daily-watchlist。

## 集成原则（不要破坏的底线）

- 基座**不复制**模块源码。模块可以是独立 repo、子目录、submodule 或外部路径。
- 基座只规定**文件契约**：模块从哪些目录读、往哪些目录写。
- 模块缺席时不能阻塞基座——基座那一圈始终能独立跑。
- 知识库入口永远是 `wiki/`；任务产物永远先落 `output/`，长期结论才回写 wiki。

## 这个模块是什么

- 一句话定位：`{模块做什么}`。
- 槽位：`输入侧`（把外部材料变成 `wiki/` 可读输入）或 `输出侧`（消费 `wiki/` + `monitoring/`，产出到 `output/`，可回写 `hypothesis/`）。
- 来源：`{自己的 repo / 别人的项目 / DIY 脚本}`，项目地址或路径 `{...}`。

## 文件契约

| 动作 | 路径 |
|---|---|
| 读取 | `{wiki/entities/ 或 monitoring/ 或 ...}` |
| 写入主产物 | `{wiki/sources/ 或 output/{模块名}/ 或 ...}` |
| 写入原始材料（如有） | `{wiki/raw/{...}/}` |
| 回写证据（输出侧，如有） | `{hypothesis/}` |

> 输入侧默认写 `wiki/sources/`（结构化摘要）+ `wiki/raw/`（原文）。
> 输出侧默认写 `output/{模块名}/YYYY-MM/...`，证据回写 `hypothesis/`。

## 在 workspace-config 登记

在 `workspace/workspace-config.md` 的「可选模块」下加：

```markdown
### {模块名}
- status: `enabled` / `planned`
- project_path: `{路径或 repo}`
- slot: `input` / `output`
- reads_from:
  - `{...}`
- writes_to:
  - `{...}`
```

并在 `system/interfaces/README.md` 同步登记一条，作为所有模块的总览。

## Agent 使用入口

自然语言即可：

> `{用 {模块名} 做 X，结果写进 wiki / 生成日报}`

模块未安装时，agent 应先读本文件和 `workspace/workspace-config.md`，提示用户给出项目路径或安装方式，不要阻塞基座基础使用。

## 边界

- `{这个模块不负责什么}`
- `{下游交给谁}`

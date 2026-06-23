# {工具名} Integration（内部接线说明）

> 复制本文件为 `system/integrations/{工具名}.md`，按下面的槽填好，就把一个新工具接进了系统。
> 已填好的范例：`system/integrations/pod2wiki.md`（播客摄入）、`system/integrations/daily-watchlist.md`（日报监控）、`system/integrations/personal-wiki.md`（默认核心）。

## 集成原则

- 工具代码放在 `tools/{工具名}/`。
- 系统只规定**文件契约**：工具从哪些目录读、往哪些目录写。
- 任何工具缺席时不能阻塞基座——基座那一圈始终能独立跑。
- 知识库入口永远是 `wiki/`；任务产物永远先落 `output/`，长期结论才回写 wiki。

## 这个工具是什么

- 一句话定位：`{工具做什么}`。
- 类型：`输入侧`（把外部材料变成 `wiki/` 可读输入）或 `输出侧`（消费 `wiki/`，产出到 `output/`，可回写 `hypothesis/`）。
- 代码位置：`tools/{工具名}/`。

## 文件契约

| 动作 | 路径 |
|---|---|
| 读取 | `{wiki/entities/ 或 monitoring/ 或 ...}` |
| 写入主产物 | `{wiki/sources/ 或 output/{工具名}/ 或 ...}` |
| 写入原始材料（如有） | `{wiki/raw/{...}/}` |
| 回写证据（输出侧，如有） | `{hypothesis/}` |

## 在 workspace-config 登记

在 `workspace/workspace-config.md` 的「内置工具」下加：

```markdown
### {工具名}
- status: `enabled`
- skill: `system/skills/{工具名}.md`
- project_path: `./tools/{工具名}`
- reads_from:
  - `{...}`
- writes_to:
  - `{...}`
```

并在 `system/interfaces/README.md` 同步登记一条。

## Agent 使用入口

自然语言即可：

> `{用 {工具名} 做 X，结果写进 wiki / 生成日报}`

首次使用时 agent 检查依赖，缺什么用 `python3 -m pip install ...` 安装；如果环境只有 `python`，再替换成 `python -m pip ...`。

## 边界

- `{这个工具不负责什么}`
- `{下游交给谁}`

# hypothesis-tracker Integration（外挂模块 · 决策追踪）

> 假设追踪模块。独立管理投资 / 研究假设、证据和复盘，是 `hypothesis/` 的深度版。
> 一键部署见 `system/skills/deploy-modules.md`（用户说"帮我安装假设追踪"）。
> 新人不必先装：基座自带的 `hypothesis/` 目录 + daily-watchlist 的证据回写已够起步。

## 集成原则

- 基座**不复制** hypothesis-tracker 源码，只规定文件契约。
- 部署方式：`git clone https://github.com/Benboerba620/hypothesis-tracker` 到 `./hypothesis-tracker/`。
- 与 `hypothesis/` 共享同一套假设文件约定，不另起炉灶。

## 推荐位置

```text
my-ai-workspace/
├── hypothesis-tracker/         # git clone 下来的模块
├── hypothesis/                 # 假设、证据、复盘（基座目录，模块读写它）
└── wiki/explorations/          # 假设成熟后沉淀的综合判断
```

## 文件契约

| 动作 | 路径 |
|---|---|
| 读写假设与证据 | `hypothesis/H*.md` |
| 读取知识库背景 | `wiki/entities/` / `wiki/concepts/` / `wiki/explorations/` |
| 复盘结论沉淀 | `wiki/explorations/` |

## 在 workspace-config 登记

```markdown
### hypothesis-tracker
- status: `enabled`
- project_path: `./hypothesis-tracker`
- slot: `decision`
- reads_from:
  - `hypothesis/`
  - `wiki/`
- writes_to:
  - `hypothesis/`
  - `wiki/explorations/`
```

并在 `system/interfaces/README.md` 同步登记。

## Agent 使用入口

> 用 hypothesis-tracker 复盘 H3 这条假设的最新证据。

## 边界

- 只管假设的记录、证据归集和复盘，不抓材料、不产日报。
- 证据通常由 daily-watchlist 等输出模块回写进 `hypothesis/`，本模块负责组织和复盘。
- 假设升级为稳定结论后，沉淀到 `wiki/explorations/`，并标注事实 / 推测 / 待验证。

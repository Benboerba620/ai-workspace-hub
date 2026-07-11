# 假设追踪 Integration（基座自带 · 决策追踪）

> 假设追踪是**基座自带能力**，不是要另装的外部模块。
> 用 `hypothesis/` 管理投资 / 研究假设和复盘，用 `evidence/` 管理独立证据，开箱即用，无需 `git clone`。
> 触发：做研究、复盘、或讨论某条假设时，agent 自动读写 `hypothesis/`。

## 集成原则

- 基座自带，**不依赖任何外部 repo**——所有读写都落在本工作区的 `hypothesis/` 与 `wiki/explorations/`。
- 一条假设一个文件 `hypothesis/H{n}-{slug}.md`。独立证据保存在 `evidence/`，假设时间线只追加证据 ID 和简短引用。
- 默认建立自上而下的主题 / 产业假设；公司通过“关联标的”映射到假设，记录受益角色和公司特有风险。只有纯公司事件无法归入更高层逻辑时，才建立公司级假设。
- 假设成熟为稳定结论后，沉淀到 `wiki/explorations/`，不另起炉灶。

## 推荐位置

```text
my-ai-workspace/
├── hypothesis/                 # 假设和复盘（基座目录，agent 直接读写）
│   └── H*.md                   #   一条假设一个文件
├── evidence/                   # 独立证据账本
│   └── YYYY-MM/E-*.md          #   一条证据一个文件
└── wiki/explorations/          # 假设成熟后沉淀的综合判断
```

## 文件契约

| 动作 | 路径 |
|---|---|
| 读写假设与复盘 | `hypothesis/H*.md` |
| 读写独立证据 | `evidence/YYYY-MM/E-*.md` |
| 读取知识库背景 | `wiki/entities/` / `wiki/concepts/` / `wiki/explorations/` |
| 复盘结论沉淀 | `wiki/explorations/` |

## 在 workspace-config 登记

基座自带，默认 `enabled`，无需 `project_path`：

```markdown
### 假设追踪（基座自带）
- status: `enabled`
- slot: `decision`
- reads_from:
  - `hypothesis/`
  - `wiki/`
- writes_to:
  - `hypothesis/`
  - `wiki/explorations/`
```

## Agent 使用入口

> 复盘 H3 这条假设的最新证据。

建立假设前先问：这是关于产业世界如何变化的判断，还是只关于某家公司？如果多家公司会受同一驱动影响，优先建立一个主题假设，再链接公司，不要为每家公司复制一份相同逻辑。

## 边界

- 只管假设的记录、证据归集和复盘，不抓材料、不产日报。
- 证据通常由 daily-watch 等模块写入 `evidence/`，再把引用追加进 `hypothesis/`；假设追踪负责组织和复盘。
- 当前状态只认假设 frontmatter；确定性日志是历史，不是第二份当前状态。
- 假设升级为稳定结论后，沉淀到 `wiki/explorations/`，并标注事实 / 推测 / 待验证。

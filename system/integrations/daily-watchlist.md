# daily-watchlist Integration（外挂模块 · 输出槽）

> 日报监控模块。消费知识库和股票池，产出每日报告，并把证据回写到假设。
> 一键部署见 `system/skills/deploy-modules.md`（用户说"帮我安装日报监控"）。

## 集成原则

- 基座**不复制** daily-watchlist 源码，只规定文件契约。
- 部署方式：`git clone https://github.com/Benboerba620/daily-watchlist` 到 `./daily-watchlist/`。
- 模块缺席不影响基座；基座的 note → wiki 链路始终独立可跑。

## 推荐位置

```text
my-ai-workspace/
├── daily-watchlist/            # git clone 下来的模块
├── monitoring/                 # 股票池 / 监控对象
├── hypothesis/                 # 证据回写目标
├── wiki/                       # 读取知识库背景
└── output/daily-watchlist/     # 日报落盘
```

## 文件契约

| 动作 | 路径 |
|---|---|
| 读取股票池 | `monitoring/watchlist.md` 或 `daily-watchlist/config/` |
| 读取知识库背景 | `wiki/entities/` / `wiki/concepts/` |
| 写入日报 | `output/daily-watchlist/YYYY-MM/YYYY-MM-DD.md` |
| 回写证据 | `hypothesis/H*.md` |
| 可选沉淀 | `wiki/explorations/` |

> 本模块未部署时，若用户临时要一份手动日报，基座写到 `output/daily/YYYY-MM-DD-*.md`；装上本模块后由模块接管 `output/daily-watchlist/`。两条不冲突。

## 在 workspace-config 登记

```markdown
### daily-watchlist
- status: `enabled`
- project_path: `./daily-watchlist`
- slot: `output`
- reads_from:
  - `monitoring/`
  - `wiki/entities/`
  - `wiki/concepts/`
- writes_to:
  - `output/daily-watchlist/`
  - `hypothesis/`
```

并在 `system/interfaces/README.md` 同步登记。

## Agent 使用入口

> 用 daily-watchlist 生成今天的盯盘日报。

模块未部署时，agent 应提示用户"帮我安装日报监控"，不要阻塞基座基础使用。

## 边界

- 只产报告和回写证据，不负责抓取材料（那是输入槽的事）。
- 长期判断回写 `wiki/explorations/` 时需标注事实 / 推测 / 待验证。
- 假设的深度追踪交给 hypothesis-tracker（见 `system/integrations/hypothesis-tracker.md`）。

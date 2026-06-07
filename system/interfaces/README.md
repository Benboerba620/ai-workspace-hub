# Interfaces

> 官方模块一键部署见 `system/skills/deploy-modules.md`。状态 `planned` = 已登记契约、未 clone；`enabled` = 已部署接线。

## personal wiki

- status: `enabled`
- wiki_root: `./wiki`
- schema: `karpathy-claude-wiki compatible`
- owns:
  - `wiki/raw/`
  - `wiki/sources/`
  - `wiki/entities/`
  - `wiki/concepts/`
  - `wiki/explorations/`

## pod2wiki

- status: `planned`
- project_path:
- role: 可选输入层，把播客、RSS、长文转成知识库页面
- writes_to:
  - `wiki/sources/`
  - `wiki/raw/podcasts/`
  - `output/pod2wiki/`

## daily-watchlist

- status: `planned`
- project_path:
- role: 可选监控层，生成日报并把证据回写到假设
- reads_from:
  - `monitoring/`
  - `wiki/entities/`
  - `wiki/concepts/`
- writes_to:
  - `output/daily-watchlist/`
  - `hypothesis/`

## 假设追踪（基座自带）

- status: `enabled`
- role: 基座自带决策层，管理假设 / 证据 / 复盘（无需 clone 外部 repo）
- 契约: `system/integrations/hypothesis-tracker.md`
- reads_from:
  - `hypothesis/`
  - `wiki/`
- writes_to:
  - `hypothesis/`
  - `wiki/explorations/`


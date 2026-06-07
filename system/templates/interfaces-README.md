# Interfaces

> 这里记录本工作区和外挂项目之间的读写约定。接口先写清楚，再决定要不要改代码。

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

- status: `optional` / `enabled` / `planned`
- project_path:
- role: 可选输入层，把播客、RSS、长文转成知识库页面
- writes_to:
  - `wiki/sources/`
  - `wiki/raw/podcasts/`
  - `output/pod2wiki/`
- contract:
  - 原始材料保留在 `wiki/raw/`
  - 结构化摘要写入 `wiki/sources/`
  - 本轮扫描总结写入 `output/pod2wiki/`

## daily-watchlist

- status: `planned`
- project_path:
- role: 监控层，生成日报并把证据回写到假设
- reads_from:
  - `monitoring/`
  - `wiki/entities/`
  - `wiki/concepts/`
- writes_to:
  - `output/daily-watchlist/`
  - `hypothesis/`
- contract:
  - 股票池和关注主题由 `monitoring/` 或 daily-watchlist 自身配置管理
  - 日报写入 `output/daily-watchlist/`
  - 与投资假设相关的证据回写到 `hypothesis/`

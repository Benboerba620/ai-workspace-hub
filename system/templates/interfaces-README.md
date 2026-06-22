# Interfaces

> 记录系统内各工具的读写约定。所有工具已内置，无需额外安装。

## personal wiki
- status: `enabled`
- wiki_root: `./wiki`
- schema: `karpathy-claude-wiki compatible`
- owns: `wiki/raw/`, `wiki/sources/`, `wiki/entities/`, `wiki/concepts/`, `wiki/explorations/`

## podcast
- status: `enabled`
- project_path: `./tools/podcast`
- skill: `system/skills/podcast.md`
- writes_to: `wiki/sources/`, `wiki/raw/podcasts/`, `output/pod2wiki/`

## daily-watch
- status: `enabled`
- project_path: `./tools/daily-watch`
- skill: `system/skills/daily-watch.md`
- reads_from: `config/daily-watchlist-watchlist.md`, `monitoring/`, `wiki/entities/`, `wiki/concepts/`
- writes_to: `daily-watchlist-reports/`, `hypothesis/`

## screen
- status: `enabled`
- skill: `system/skills/screen.md`
- writes_to: `output/screen/`

## 假设追踪（基座自带）
- status: `enabled`
- 契约: `system/integrations/hypothesis-tracker.md`
- reads_from: `hypothesis/`, `wiki/`
- writes_to: `hypothesis/`, `wiki/explorations/`

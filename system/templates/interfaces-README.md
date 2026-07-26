# Interfaces

> 记录系统内各工具的读写约定。所有工具已内置，无需额外安装。

## personal wiki
- status: `enabled`
- wiki_root: `./wiki`
- schema: `karpathy-claude-wiki compatible`
- owns: `wiki/raw/`, `wiki/sources/`, `wiki/entities/`, `wiki/concepts/`, `wiki/explorations/`, `wiki/patterns/`, `wiki/rules/`
- lifecycle: `system/scripts/knowledge_lifecycle.py`
- load_order: `rule -> pattern -> exploration`
- usage_log: `workspace/knowledge-usage.jsonl`

## podcast
- status: `enabled`
- project_path: `./tools/podcast`
- skill: `system/skills/podcast.md`
- writes_to: `wiki/sources/`, `wiki/raw/podcasts/`, `output/pod2wiki/`

## daily-watch
- status: `enabled`
- project_path: `./tools/daily-watch`
- skill: `system/skills/daily-watch.md`
- reads_from: `config/daily-watchlist-watchlist.md`, `wiki/entities/`, `wiki/concepts/`
- writes_to: `output/daily-watch/`, `evidence/`, `hypothesis/`（引用）

## screen
- status: `enabled`
- skill: `system/skills/screen.md`
- writes_to: `output/screen/`

## research preflight
- status: `enabled`
- script: `system/scripts/research_preflight.py`
- reads_from: configured `wiki_root` 的 `rules/`, `patterns/`, `explorations/`, `entities/`, `concepts/`, `sources/`
- writes_to: `output/research/preflight/`, `workspace/knowledge-usage.jsonl`
- boundary: 本地确定性召回，不调用 LLM；命中不等于结论正确

## 假设追踪（基座自带）
- status: `enabled`
- 契约: `system/integrations/hypothesis-tracker.md`
- reads_from: `hypothesis/`, `wiki/`
- writes_to: `hypothesis/`, `wiki/explorations/`

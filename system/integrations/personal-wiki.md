# Personal Wiki Integration

> personal wiki 是本 Hub 的默认核心模块。它负责承接输入、沉淀知识、支持输出和监控回写。

## 集成原则

- Hub 默认创建最小 `wiki/` 结构。
- 分类规则以 `wiki/_schema.md` 为准。
- 用户已有 [karpathy-claude-wiki](https://github.com/Benboerba620/karpathy-claude-wiki) 时，Hub 只记录路径，不复制旧 wiki。
- pod2wiki、daily-watchlist、hypothesis 都围绕 personal wiki 读写。
- wiki 是知识层，不是任务层；任务结果写到 `output/`，长期结论再沉淀回 wiki。

## 最小结构

```text
wiki/
├── _schema.md
├── raw/
├── sources/
├── entities/
├── concepts/
├── explorations/
├── patterns/
└── rules/
```

## 路由

```text
inbox / pod2wiki / manual notes
  -> wiki/raw/
  -> wiki/sources/
  -> wiki_tagger（domain / ticker / concepts / related / salience / tags）
  -> wiki/entities/ + wiki/concepts/
  -> wiki/explorations/
  -> wiki/patterns/ -> wiki/rules/
```

## 自动标签

- `system/scripts/wiki_tagger.py` 是唯一打标实现，新材料和历史补标共用同一套 schema。
- `tag <file> --apply` 用于摄入时写入；`backfill <dir>` 默认只预览，确认后加 `--apply`。
- 打标器读取已有 tags 和 concept 名称，优先复用，避免同义标签越积越多。
- 只补空字段，不覆盖用户已有 frontmatter；模型结果必须通过字段、数量、ticker 和 salience 校验。
- 预览结果缓存到 `workspace/cache/wiki_tagger.json`，确认写入复用缓存；缓存不保存正文或 API key。
- 复用 `config/pod2wiki.env` 的用户自有大模型 API。调用失败时不编造结果，也不阻塞原始材料归档。

## 知识编译与加载

- `knowledge_lifecycle.py` 维护 `wiki/explorations/_index.md`、`wiki/patterns/_index.md` 和 `wiki/rules/_index.md` 三个短索引。
- 研究开始按场景调用 `knowledge_lifecycle.py load`，只加载命中的 rule / pattern / exploration，避免 wiki 增长后全量加载。
- `--record` 把实际调用写入 `workspace/knowledge-usage.jsonl`，不把调用次数当作证据。
- 提炼链路为 `source -> exploration -> pattern -> rule`；被证伪且可能重复出现的直觉记入 `wiki/false-beliefs.md`。
- 完整的验证、归因和晋级规则见 `system/skills/knowledge-lifecycle.md`。

## 目录职责

| 目录 | 职责 |
|---|---|
| `wiki/raw/` | 原始材料，不轻易改写 |
| `wiki/sources/` | 单个来源的结构化摘要 |
| `wiki/entities/` | 公司、人、项目、产品等实体档案 |
| `wiki/concepts/` | 主题、框架、概念 |
| `wiki/explorations/` | 综合 2 个以上来源后的阶段性判断 |
| `wiki/patterns/` | 跨案例可迁移机制卡 |
| `wiki/rules/` | 至少三个独立案例确认的决策规则 |

## workspace-config 记录

在 `workspace/workspace-config.md` 中记录：

```markdown
### personal wiki

- status: `enabled`
- wiki_root: `./wiki`
- source_schema: `karpathy-claude-wiki compatible`
- raw_dir: `wiki/raw/`
- sources_dir: `wiki/sources/`
- entities_dir: `wiki/entities/`
- concepts_dir: `wiki/concepts/`
- explorations_dir: `wiki/explorations/`
- patterns_dir: `wiki/patterns/`
- rules_dir: `wiki/rules/`
```

## Codex 使用入口

自然语言即可：

> 把 inbox 里的这篇材料整理进 personal wiki。

Codex 应该先读：

1. `AGENTS.md`
2. `workspace/workspace-config.md`
3. `wiki/_schema.md`
4. `system/integrations/personal-wiki.md`

然后再决定写入 `wiki/raw/`、`wiki/sources/` 或其他目录。

## 边界

- wiki 不负责抓取材料；抓取交给 pod2wiki 或其他输入器。
- wiki 不负责生成日报；日报写到 `output/`。
- wiki 不直接代表最终投资判断；综合判断需要标注事实、推测和待验证。

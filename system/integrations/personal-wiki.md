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
└── explorations/
```

## 路由

```text
inbox / pod2wiki / manual notes
  -> wiki/raw/
  -> wiki/sources/
  -> wiki/entities/ + wiki/concepts/
  -> wiki/explorations/
```

## 目录职责

| 目录 | 职责 |
|---|---|
| `wiki/raw/` | 原始材料，不轻易改写 |
| `wiki/sources/` | 单个来源的结构化摘要 |
| `wiki/entities/` | 公司、人、项目、产品等实体档案 |
| `wiki/concepts/` | 主题、框架、概念 |
| `wiki/explorations/` | 综合 2 个以上来源后的阶段性判断 |

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

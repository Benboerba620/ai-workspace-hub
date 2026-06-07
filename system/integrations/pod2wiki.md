# pod2wiki Integration

> pod2wiki 是本 Hub 的可选输入模块。它负责把播客、RSS、长文变成可被 agent 读取和维护的 wiki 页面。

## 集成原则

- Hub 不复制 pod2wiki 源码。
- Hub 只规定 pod2wiki 写入 personal wiki 的输入输出契约。
- pod2wiki 可以作为独立 repo、子目录、submodule 或外部路径存在。
- Hub 的知识库入口始终是 `wiki/`。

## 推荐位置

```text
my-ai-workspace/
├── system/integrations/
│   └── pod2wiki.md
├── pod2wiki/                  # 可选：本地 clone 或 submodule
├── wiki/
│   ├── raw/
│   │   └── podcasts/
│   └── sources/
└── output/
    └── pod2wiki/
```

## 路由

```text
podcast / RSS / blog feed
  -> pod2wiki
  -> wiki/raw/podcasts/
  -> wiki/sources/
  -> output/pod2wiki/
```

## 写入契约

| 输出 | 路径 | 说明 |
|---|---|---|
| 原始英文全文 / 转录 | `wiki/raw/podcasts/` | 永久保留，方便未来重翻译或重摘要 |
| 中文结构化摘要 | `wiki/sources/` | agent 日常读取的知识页面 |
| 本轮扫描总结 | `output/pod2wiki/` | 本次抓取的 insight log |

## workspace-config 记录

在 `workspace/workspace-config.md` 中记录：

```markdown
### pod2wiki

- status: `enabled` / `planned`
- project_path: `./pod2wiki`
- wiki_root: `./wiki`
- raw_output: `wiki/raw/podcasts/`
- source_output: `wiki/sources/`
- insight_output: `output/pod2wiki/`
```

## Codex 使用入口

自然语言即可：

> 用 pod2wiki 扫一下最近 7 天播客，把结果写进 wiki。

如果 pod2wiki 尚未安装，Codex 应该先检查 `system/integrations/pod2wiki.md` 和 `workspace/workspace-config.md`，然后提示用户提供 pod2wiki 路径或安装方式。不要阻塞 personal wiki 的基础使用。

## 边界

- pod2wiki 不负责投资判断。
- pod2wiki 不直接修改 `hypothesis/`。
- pod2wiki 只把外部材料变成 `wiki/` 可读输入。
- 后续是否进入 daily-watchlist / hypothesis，由 Hub 或 agent 再决定。

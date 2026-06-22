# daily-watch 内部接线说明

> daily-watch 工具（原 daily-watchlist）的代码在 `tools/daily-watch/`。
> 独立项目：[daily-watchlist](https://github.com/Benboerba620/daily-watchlist)

## 接线

```text
config/daily-watchlist-watchlist.md（股票池）
config/daily-watchlist.yaml（配置）
  → tools/daily-watch/scripts/generate_daily_report.py
  → daily-watchlist-reports/YYYY-MM/YYYY-MM-DD.md（日报）
  → hypothesis/H*.md（证据回写）
```

## 文件契约

| 动作 | 路径 |
|------|------|
| 读取股票池 | `config/daily-watchlist-watchlist.md` |
| 读取知识库 | `wiki/entities/` / `wiki/concepts/` |
| 写入日报 | `daily-watchlist-reports/YYYY-MM/YYYY-MM-DD.md` |
| 回写证据 | `hypothesis/H*.md` |
| 可选沉淀 | `wiki/explorations/` |

## workspace-config 记录

```markdown
### daily-watch
- status: enabled
- project_path: ./tools/daily-watch
- reads_from: config/daily-watchlist-watchlist.md, monitoring/, wiki/entities/, wiki/concepts/
- writes_to: daily-watchlist-reports/, hypothesis/
```

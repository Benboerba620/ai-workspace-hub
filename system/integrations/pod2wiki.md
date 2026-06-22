# podcast 内部接线说明

> podcast 工具（原 pod2wiki）的代码在 `tools/podcast/`。
> 独立项目：[pod2wiki](https://github.com/Benboerba620/pod2wiki)

## 接线

```text
YouTube / RSS / 博客
  → tools/podcast/scripts/fetch_podcasts.py
  → wiki/raw/podcasts/（英文原文归档）
  → wiki/sources/（中文结构化摘要）
  → output/pod2wiki/（本轮扫描日志）
```

## 写入契约

| 输出 | 路径 | 说明 |
|------|------|------|
| 原始英文全文 | `wiki/raw/podcasts/` | 永久保留 |
| 中文结构化摘要 | `wiki/sources/` | agent 日常读取 |
| 扫描总结 | `output/pod2wiki/` | insight log |

## workspace-config 记录

```markdown
### podcast
- status: enabled
- project_path: ./tools/podcast
- writes_to: wiki/sources/, wiki/raw/podcasts/, output/pod2wiki/
```

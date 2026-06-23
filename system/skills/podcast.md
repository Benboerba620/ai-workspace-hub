# Podcast（播客 / 博客摄入）

> 把 YouTube 播客、RSS 博客、长文自动转成双语摘要，写入 personal wiki。
> 代码位于 `tools/podcast/`，原始项目 [pod2wiki](https://github.com/Benboerba620/pod2wiki)。

## 触发词

"扫播客" / "scan podcasts" / "刷播客" / "播客追踪" / "podcast" / "抓博客" / "RSS"

## 前置条件

1. 安装依赖：`python3 -m pip install -r tools/podcast/requirements.txt`
   - 需要 Python 3.10+。先运行 `python3 --version`；如果低于 3.10，改用 `python3.10` / `python3.11` / `python3.12`，或引导用户安装新版 Python
   - 如果环境只有 `python` 且版本 ≥3.10，把命令里的 `python3` 替换成 `python`
2. 配置文件（首次使用时复制）：
   - `cp tools/podcast/examples/config.ai-investing.yaml config/pod2wiki.config.yaml`
   - `cp tools/podcast/.env.example config/pod2wiki.env`
3. 在 `config/pod2wiki.env` 填入 LLM API Key（默认 [DeepSeek](https://platform.deepseek.com/)，也支持 [Kimi](https://platform.moonshot.cn/)、[GLM](https://open.bigmodel.cn/)、[Qwen](https://dashscope.console.aliyun.com/)）

Agent 首次使用时检查上述条件，缺什么补什么。

## 运行命令

先读取 `workspace/workspace-config.md` 的 `wiki_root`，把下面的 `{wiki_root}` 替换成实际路径。

```bash
python3 tools/podcast/scripts/fetch_podcasts.py \
  --config config/pod2wiki.config.yaml \
  --env-file config/pod2wiki.env \
  --output-dir output/pod2wiki \
  --wiki-out {wiki_root}/sources \
  --days 7 \
  --write-insight-log
```

常用参数：
- `--days N`：扫描最近 N 天
- `--dry-run`：只检查配置，不调 LLM
- `--no-llm`：跳过摘要生成
- `--input-file PATH`：本地文件摄入（不联网）
- `--mode rss|youtube|all`：选择输入源
- `--translate-full`：生成全文翻译

## 输出路径

| 输出 | 路径 | 说明 |
|------|------|------|
| 中文结构化摘要 | `wiki/sources/YYYY-MM-DD-{channel}-{slug}.md` | agent 日常读取 |
| 英文原始全文 | `wiki/raw/podcasts/YYYY-MM-DD-{channel}-{slug}.md` | 永久归档 |
| 全文翻译 | `wiki/translations/...` | 可选，`--translate-full` |
| 本轮扫描总结 | `output/pod2wiki/ai-insights-log.md` | 累积 insight log |

## 配置说明

`config/pod2wiki.config.yaml` 核心结构：
- `theme`：研究主题标签
- `channels`：YouTube + RSS 频道列表
- `people_searches` / `exec_searches`：YouTube 人物搜索
- `blog_feeds`：纯 RSS 博客
- `hypotheses`：投资假设关键词（摘要时自动关联）
- `whisper`：音频转录设置（RSS 描述太短时自动触发）

## 降级策略

| 缺少 | 行为 |
|------|------|
| LLM API Key | `--no-llm` 模式，列出发现内容但不生成摘要 |
| YouTube 访问 | `--mode rss` 只扫 RSS 源 |
| Whisper / ffmpeg | 跳过音频转录，用 RSS 描述替代 |

## 冒烟测试

```bash
python3 tools/podcast/scripts/fetch_podcasts.py \
  --config config/pod2wiki.config.yaml \
  --env-file config/pod2wiki.env \
  --days 1 --dry-run
```

## 边界

- 只负责把外部材料变成 wiki 页面，不做投资判断。
- 不修改 `hypothesis/`（后续关联由 daily-watch 或 research 处理）。
- YouTube 有请求频率限制，单次建议不超过 5 个视频。

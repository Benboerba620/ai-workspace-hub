# Podcast / Blog Ingestion Tool

播客和博客摄入工具。把 YouTube/RSS/博客转成双语摘要，写入 personal wiki。

原始项目：[pod2wiki](https://github.com/Benboerba620/pod2wiki)

## 快速使用

```bash
python tools/podcast/scripts/fetch_podcasts.py \
  --config config/pod2wiki.config.yaml \
  --env-file config/pod2wiki.env \
  --output-dir output/pod2wiki \
  --wiki-out wiki/sources \
  --days 7 --write-insight-log
```

## 依赖

```bash
pip install -r tools/podcast/requirements.txt
```

可选：`faster-whisper`（音频转录，需要 ffmpeg）

## 配置

- 主题配置：`tools/podcast/examples/config.ai-investing.yaml`（复制到 `config/pod2wiki.config.yaml`）
- LLM key：`tools/podcast/.env.example`（复制到 `config/pod2wiki.env`）

## 需要的 API Key

| Key | 用途 | 必要性 |
|-----|------|--------|
| LLM API Key（DeepSeek 默认） | 摘要生成 | 必需 |
| PODCAST_PROXY | SOCKS5 代理（访问 YouTube） | 可选 |

无 LLM key 时可用 `--no-llm` 模式（仅列出发现的内容，不生成摘要）。

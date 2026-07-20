# Podcast / Blog Ingestion Tool

播客和博客摄入工具。把 YouTube/RSS/博客转成双语摘要，写入 personal wiki。

写入 Hub wiki 时默认调用 `system/scripts/wiki_tagger.py`，补齐统一结构化标签；需要保留摘要但跳过标签时加 `--no-auto-tag`。

原始项目：[pod2wiki](https://github.com/Benboerba620/pod2wiki)

## 快速使用

以下命令默认使用 `python3`，且需要 Python 3.10+。先运行 `python3 --version`；如果版本低于 3.10，请改用 `python3.10` / `python3.11` / `python3.12`，或安装新版 Python。如果你的环境只有 `python` 且版本 ≥3.10，把命令里的 `python3` 替换成 `python` 即可。

```bash
python3 tools/podcast/scripts/fetch_podcasts.py \
  --config config/pod2wiki.config.yaml \
  --env-file config/pod2wiki.env \
  --output-dir output/pod2wiki \
  --wiki-out wiki/sources \
  --days 7 --write-insight-log
```

## 依赖

```bash
python3 -m pip install -r tools/podcast/requirements.txt
```

可选音频转录：`python3 -m pip install -r tools/podcast/requirements-transcribe.txt`，并确保系统已有 ffmpeg。

## 配置

- 主题配置：`tools/podcast/examples/config.ai-investing.yaml`（复制到 `config/pod2wiki.config.yaml`）
- LLM key：`tools/podcast/.env.example`（复制到 `config/pod2wiki.env`）

## 需要的 API Key

| Key | 用途 | 必要性 |
|-----|------|--------|
| LLM API Key（DeepSeek 默认） | 摘要生成 | 必需 |
| PODCAST_PROXY | 代理（作用于 YouTube、RSS 抓取和播客音频下载，不影响 LLM 请求） | 可选 |

`PODCAST_PROXY` 取值语义：不设置 / 空 / `none` = 不走代理（默认）；`auto` = 自动扫描本机 12345-12350 端口寻找 SOCKS5 代理；其他值 = 直接作为代理 URL 使用（如 `socks5://127.0.0.1:1080`）。SOCKS 代理依赖 PySocks，已包含在 `requirements.txt` 的 `requests[socks]` 中。

无 LLM key 时可用 `--no-llm` 模式：不调用 LLM，改用本地抽取式逻辑（首段摘要 + 关键词 + 假设关键词匹配）生成低置信度（`confidence: low`）的 source page，并可输出 fallback 版 insight log。

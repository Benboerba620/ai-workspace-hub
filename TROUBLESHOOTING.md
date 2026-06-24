# 故障排查

> 遇到这里没列出的问题，欢迎到 [GitHub Issues](https://github.com/Benboerba620/ai-workspace-hub/issues) 提问。

---

## 1. 安装与环境

### `python3` 命令不存在

**原因**：Windows 默认只有 `python`，没有 `python3` 别名。

**解决**：改用 `python` 代替 `python3`，或安装 Python 3.10+（[下载页面](https://www.python.org/downloads/)），安装时勾选"Add to PATH"。

### `pip install` 失败

**原因**：pip 版本过旧、没有激活虚拟环境、或网络问题。

**解决**：先升级 pip（`python -m pip install --upgrade pip`），确认在虚拟环境内运行，国内用户可加镜像源（`-i https://pypi.tuna.tsinghua.edu.cn/simple`）。

### `check_workspace.py` 报错

**原因**：通常是工作目录不对，或 clone 不完整导致文件缺失。

**解决**：确认在项目根目录运行（`python system/scripts/check_workspace.py`），检查 `system/scripts/` 目录是否存在。

---

## 2. Core Mode 问题

### Agent 不读 AGENTS.md / CLAUDE.md

**原因**：部分 agent 需要明确提示才会读取入口文件。

**解决**：在对话开头加一句"先读 AGENTS.md（或 CLAUDE.md），然后按里面的规则做"。不同 agent 入口不同：Codex 读 AGENTS.md，Claude Code 读 CLAUDE.md。

### `inbox → wiki` 没反应

**原因**：`inbox/` 或 `wiki/` 目录不存在，或 inbox 里没有待处理文件。

**解决**：确认 `inbox/` 和 `wiki/` 目录存在（`ls inbox/ wiki/`），确认 `inbox/` 下有 `.md` 文件。首次试跑用 `inbox/first-note.md`。

### `active-context.md` 格式乱了

**原因**：多次编辑或 agent 写入格式不一致。

**解决**：可以安全地清空 `workspace/meta/active-context.md` 的内容重新开始，不会影响 wiki 和已有研究成果。保留文件、清空内容即可。

---

## 3. 播客工具

### `yt-dlp` 报错

**原因**：YouTube 经常更改接口，旧版 yt-dlp 会失效。

**解决**：升级到最新版：`pip install -U yt-dlp`。如果仍然报错，检查 [yt-dlp releases](https://github.com/yt-dlp/yt-dlp/releases) 是否有已知问题。

### LLM key 配了但摘要失败

**原因**：provider 名称和 base_url 不匹配，或 key 填错了位置。

**解决**：检查 `config/llm.env` 中的 `LLM_PROVIDER` 和 `LLM_BASE_URL` 是否对应同一家服务商。常见错误：填了 DeepSeek 的 key 但 provider 写成 openai。

### 没有 LLM key 能用播客吗

**原因**：播客摘要需要 LLM，但拉取音频和转录不一定需要。

**解决**：可以。用 `--no-llm` 参数只拉取和转录，跳过摘要步骤：`python tools/podcast/scripts/fetch_podcasts.py --no-llm`。

---

## 4. 日报工具

### 报告全是 `[待补充]`

**原因**：正常行为。没有配置 API key 时，日报工具会生成骨架但跳过需要数据源的部分。

**解决**：如果需要实际数据，在 `config/` 下配置对应的 API key（tushare / FMP）。不配 key 时 Core Mode 仍然可用。

### tushare 返回空数据

**原因**：tushare 的 A 股数据接口需要一定积分才能访问。

**解决**：登录 [tushare.pro](https://tushare.pro) 检查账户积分和接口权限。日线行情需要 120 积分，财务数据需要更高积分。

### 配置文件找不到

**原因**：首次使用时 `config/` 下没有 `.env` 文件。

**解决**：运行初始化命令生成模板配置：`python tools/daily-watch/scripts/check_setup.py --init`。

---

## 5. 通用问题

### Git clone 后文件不完整

**原因**：使用了 `--depth 1` 浅克隆，或网络中断导致部分文件缺失。

**解决**：重新完整克隆：`git clone https://github.com/Benboerba620/ai-workspace-hub.git`（不加 `--depth 1`）。已有仓库可以用 `git fetch --unshallow` 补全。

### 文件编码问题（乱码）

**原因**：项目所有文件使用 UTF-8 编码。Windows 某些编辑器默认用 GBK 或 UTF-16 打开。

**解决**：确保编辑器设置为 UTF-8。如果已有文件出现 BOM 头（`\xef\xbb\xbf`），用支持 UTF-8 的编辑器重新保存。Git 配置建议：`git config --global core.autocrlf true`（Windows）。

### 如何重置工作区

**原因**：想从头开始，但不想丢失已积累的知识库。

**解决**：删除 `workspace/meta/` 下的文件即可重置工作状态（active-context、friction-log 等）。`wiki/` 和 `config/` 目录保留不动，已有知识和配置不受影响。

<!-- 文件说明：常见问题排查指南，覆盖安装、Core Mode、播客、日报、通用问题。 -->

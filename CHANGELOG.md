# Changelog

## Unreleased

## 0.5.0 - 2026-07-11

### 新增

- 默认用途调整为股票研究，新增 `START-HERE.md` 和 `first-research` 引导：用户第一次研究公司时，不需要预先设计模板，而是在真实研究中逐步形成研究偏好。
- 新增 `workspace/research-profile.md`，沉淀用户关注维度、证据标准、估值习惯和反方偏好，后续研究可直接复用。
- 新增研究收口与假设复盘协议，把研究报告、长期知识、可证伪假设和每日监控连接成完整闭环。
- 新增 Hub 文件归属清单与 `workspace/.hub-state.json` 安装状态，为后续升级区分系统管理、用户所有和混合文件。

### 改进

- 假设模型改为自上而下的主题假设，公司作为受益映射和验证载体；模板补充时间跨度、公司角色、主题关系和公司特有风险。
- daily-watch 可从主题假设读取关联 ticker，并将公司异动、财报等可确认信号回写证据时间线；纯主题匹配只提示核验，不冒充已写入证据。
- 补充 `IFX.DE` 等欧洲 ticker 的回归验证；首次安装默认 `primary_use=investing`，并安装用户首页、研究偏好和升级状态文件。

### 修复

- 收紧研究结束时的文件落点和链接规则，避免结论只留在对话或报告中，未进入 wiki、假设与后续跟踪。
- 安装器继续沿用 0.4.0 的缓存与本地 `.env` 过滤规则，同时记录实际安装版本，不覆盖已有用户状态。

## 0.4.0 - 2026-07-05

### 修复（2026-07-05 全量体检批次）

三路并行代码审查（podcast / daily-watch / 安装链路）后的批量修复，共 40+ 项：

**daily-watch**

- 零 key 承诺兜底：`generate_daily_report.py` 缺 env 文件时警告后继续（原直接 `FileNotFoundError` 崩溃）。
- `hypothesis_tracking.enabled` / `auto_writeback` 配置真正生效：关闭后不再回写 `hypothesis/H*.md`（原开关形同虚设）。
- 关联标的识别支持 `601857.SH` / `0700.HK` / `BRK.B` / 单字母美股（原正则对 A 股、港股、类别股全部静默失效）。
- Nasdaq/EOD 降级源只剥已知市场后缀，`BF.B` 不再被剥成 `BF` 查错公司；yfinance 增加 `.SH` → `.SS` 映射（原对上交所永远失败）。
- `run_json_script` 失败时透出子进程 stderr（原真实错误被吞）；`generate_daily_report.py` 补 argparse，`--help` 不再误跑真报告。
- `check_setup.py --init` 补创建 `hypothesis/` 和 `portfolio/journal/`，FAIL 项附修复提示；根目录探测失败时回退 cwd 并警告。
- `sync_hypothesis.py` 容错手改的 frontmatter（`certainty: 80%`、坏 YAML 单文件跳过不崩全表）。
- `focus_areas.exclude` 真正实现；示例 yaml 标注仅 skill 层使用的字段；假设文件读取兼容 BOM；tushare 窗口 10 → 14 天覆盖长假；证据时间线插入段尾 `---` 之前。

**podcast**

- LLM provider/model 优先级改为「显式入参 > 环境变量 > 默认值」，并防止通用 `LLM_*` 变量串到显式指定的其他 provider（反转 0.3.1 的「环境变量优先」：config/CLI 显式指定不该被 .env 默认块静默压过）。
- Whisper 转录语言默认自动检测（原硬编码英文，中文播客产出错误转录并污染 wiki）；config 支持 `whisper.language`。
- history 去重前移到下载/转录之前，且逐条落盘——中途崩溃不再重付 LLM/Whisper 成本；显式 `--youtube-url` 绕过去重。
- 代理改为显式配置：`PODCAST_PROXY` 未设置即直连，`auto` 才扫描本地端口（原盲扫 12345-12350 误伤开发服务）；requirements 补 `requests[socks]`（原配了 SOCKS 代理必挂 Missing dependencies）。
- 单条坏 `pubDate` 不再毁掉整个 feed（逐条容错）；新增 Atom feed 支持（原静默 0 条）。
- `.m4a` 剪辑沿用源容器（原静默退化为整集转录）；LLM 返回非对象 JSON 走跳过路径不再崩整轮；转录 frontmatter 转义特殊字符；`podcast_rss_transcribe.py` / `podcast_feed_registry.py` 补 UTF-8 输出兜底（0.3.1 已覆盖其余入口）。

**安装 / 测试**

- 安装器不再把 `.ruff_cache` / `__pycache__` / `.DS_Store` / 本地 `.env`（含 API key）复制进新工作区；`--target` 指向文件时给友好报错。
- `check_workspace.py` 兼容带 BOM 的 env 文件；`inbox/first-note.md` 降级为可选项，post-install-cleanup 归档后不再误报 NOT READY。
- 文档修正：删除与 `.gitattributes` 冲突的 autocrlf 建议；post-install-cleanup 步骤编号与 installer 路径说明；daily-watch 数据源表列对齐。
- CI 统一 pytest 收集（unittest 会漏掉 pytest 风格用例）、钉 ruff 版本、补 `generate_daily_report.py --help` 冒烟；新增 41 个针对上述修复的单测（全套 55 个通过）。

以下修复来自一次完整的冷启动安装模拟测试（陌生环境、只凭 README 分享句从 GitHub 安装）：

### 修复

- **安装分享句改用 raw 链接 + git clone 双通路**：原 blob 页面链接是约 340KB 的 HTML，网页抓取只能拿到摘要，agent 可能凭残缺协议安装；raw 链接是 12KB 纯 markdown，与源文件逐字一致。协议开头同时提醒 agent 自检"拿到的是全文还是摘要"。
- `install_workspace.py` 完成提示指错下一步：原来指向 `check_setup.py`（Enhanced Mode 配置），会把新用户引向 API key；更正为协议 Step 5 的 `check_workspace.py --root`（Core Mode 检查）。
- `INSTALL-FOR-AI.md` 补两处 agent 只能靠猜的空白：用户没有现成 wiki 时 `--wiki-root` 直接省略（默认 `./wiki`）；临时克隆目录按平台取 `%TEMP%` / `/tmp`。
- `first-ingest.md` 步骤对齐 `wiki/_schema.md` 的「MVP 最低合格标准」（补 raw 归档、至少一个分类页、output 试跑报告），不同 agent 的产出不再因两份文档标准不一致而波动。

### 文档

- README「30 秒上手」新增「还没有 AI agent？先花 2 分钟装一个」：Claude Code / Codex CLI / Cursor 三条最短安装路径，收礼的朋友从零也能起步。
- README 开头与仓库 homepage 挂上设计思路长文《从0构建 AI 协作系统（一）：从最小可运行的 MVP 开始》（作者公众号）。
- **README 顶部新增 33 秒演示动图**（`docs/demo.gif`）：一句话安装 → 3 个问题 → Core Mode READY → 第一次摄入 → 配 API key（Enhanced Mode）→ 断点续传收尾。按安装协议真实流程脚本化生成（生成脚本 `docs/gen_demo_gif.py` 一并入库，流程变更时改台词重跑即可），并在图下注明"非实录"。

### 改进

- 仓库开启 GitHub template：点 "Use this template" 即可创建自己的（可私有）工作区副本，个人研究数据不必公开 fork。

## 0.3.1 - 2026-07-02

### 修复

- **手动 clone 不再继承维护者的工作状态**：`workspace/meta/active-context.md` 和 `friction-log.md` 重置为干净模板，仓库契约测试新增这两对模板一致性检查，防止个人工作日志再次混进发布内容。
  之所以这样改：README 的"手动 clone 直接用"路径会把维护者的断点记录带给新用户，走安装协议的用户不受影响，但两条路径应该拿到同样干净的工作区。
- **smoke-test 演示产物移入 `examples/smoke-test/`**：原先散在 `wiki/` 和 `output/` 里的 2026-06-05 试跑产物（含未在文档声明的 `output/first-ingest/` 等三个子目录）统一收进 `examples/`，配 README 说明"这是示例、可整目录删除"。用户的 `wiki/` 和 `output/` 现在从空白开始。
- `TROUBLESHOOTING.md` 播客排障段指错配置文件：`config/llm.env` 更正为实际存在的 `config/pod2wiki.env`。
- **Windows 西文 locale 下中文输出崩溃**：8 个入口脚本（`check_workspace.py`、`check_setup.py`、`fetch_podcasts.py` 等）在 cp1252 控制台打印中文会触发 `UnicodeEncodeError`；现在启动时统一把 stdout/stderr 重配为 UTF-8。新加的 Windows CI job 第一跑就抓到了这个问题。
- 新增标准库安装器，安装协议明确先取得源码；非空目标默认停止，`--merge` 只补缺失文件、不覆盖用户资料。
- 修复 all-in-one 工作区在配置文件创建前无法识别根目录的问题，`check_setup.py --init` 可安全初始化缺失配置。
- 更正 Longbridge 定位：它是独立 Agent Skill/CLI/MCP，不再宣称为 daily-watch Python 脚本的内置环境变量数据源。
- `faster-whisper` 拆到可选的 `requirements-transcribe.txt`，避免基础播客安装拉取重型转录依赖。
- LLM 环境变量优先于示例 YAML；摘要全部失败时返回非零状态，不再静默报告成功。

### 改进

- **CI 新增 Windows job**（windows-latest × Python 3.12）：README 明确支持 Windows 用户，编码、路径分隔符、`python`/`python3` 别名类问题现在能在 CI 被抓住。
- CI 的 pytest 步骤去掉 `|| true`，测试失败不再被吞掉。
- 新增安装、路径、文档链接和仓库契约测试，以及 Python 3.10/3.12 CI。

### 文档

- 数据源表（README / AGENTS / CLAUDE）补上代码里实际支持的 daily-watch 降级源：Finnhub / EOD / yfinance（`FINNHUB_API_KEY` / `EOD_API_KEY` / `ENABLE_YFINANCE`）。
- README「30 秒上手」和 SMOKE-TEST 的第一条命令内联标注 Windows 写法（`python` 代替 `python3`），不用翻到故障排查才发现。
- `AGENTS.md` 补上与 `CLAUDE.md` 的双向同步声明（此前只有 CLAUDE.md 单向声明）。
- 日报监控路由行补充 `system/integrations/daily-watchlist.md` 接线说明的入口。

### 移除

- 删除冗余的 `tools/daily-watch/.env.example`（与 `config-examples/daily-watchlist.env.example` 内容重复，安装器和文档都只用后者）。

## 0.3.0 - 2026-06-22

### 新增

- **All-in-One 集成**：pod2wiki（播客/博客摄入）和 daily-watchlist（日报监控）代码合并进 `tools/podcast/` 和 `tools/daily-watch/`，一次 clone 拿到全部六大能力。原始独立 repo 继续存在。
- **screen 快速筛选**（基座能力）：给定主题 → websearch 候选 → 拉数据 → 过滤 → 表格 + Top 5 分析。内置两个预设模板（价值股 / AI 产业链）。无 API 时降级为纯 websearch。
- **Longbridge 数据源**：新增 Longbridge 为默认免费数据源（HK + US 行情），与 tushare（A 股）并列为零成本起步选项。FMP 降为付费可选。（勘误：0.3.1 已更正——Longbridge 是独立 Agent Skill/CLI/MCP 外部扩展，不是日报脚本的内置数据源；FMP 仍为内置可选源。）
- **统一 config/ 目录**：所有工具的用户配置文件统一放在 `config/`（不入 git）。

### 改进

- **README 重写**：从"最小种子 + 槽位"改为"all-in-one 六大能力"。
- **INSTALL 简化**：移除"选模块"步骤，全量安装是唯一路径。
- **ARCHITECTURE 更新**：架构图和目录结构反映 tools/ + 数据源层。
- **AGENTS.md / CLAUDE.md 路由表扩展**：新增 podcast、daily-watch、screen 三条路由。
- **workspace-config 更新**：新增数据源段（Longbridge/tushare/FMP）+ screen 能力 + podcast/daily-watch 内置登记。

### 移除

- `system/skills/deploy-modules.md`（不再需要 clone 外部模块）。
- 文档中"外部模块 clone"流程和相关引导。

## 0.2.4 - 2026-06-22

### 修复

- **INSTALL 路径补上试跑材料**：走 `INSTALL-FOR-AI.md` 安装的用户 `inbox/` 是空的，README「直接试跑」段引用的 `first-note.md` 不存在导致跑不通。现在 Step 2 复制清单包含 `inbox/first-note.md`，两条安装路径都能直接试跑。

## 0.2.3 - 2026-06-07

### 改进

- **active-context 上限与自动清理**：给断点续传协议补上"内联自动剪"。agent 写断点时自检「最近对话延续」段，把**超过 14 天或超过 20 条**的旧条目整行移到 `workspace/meta/active-context-archive-YYYY-MM.md`（保留续接锚点）——零脚本、自动执行、不等手动体检。`structure-health` 的 active-context 检查改为**周度兜底**（万一内联没剪到位才点出来），并对齐归档路径。

## 0.2.2 - 2026-06-07

### 改进

- **active-context 断点续传协议落地**：把"今天停、明天接"做成 agent 自动行为，不再只是格式说明。AGENTS / CLAUDE（含 `system/templates/`）新增「active-context：断点续传」段，写明两条自动触发规则——① 开场说"继续 / 接着 / 昨天"→ 自动读 `active-context.md` 顺着「续接锚点」接上；② 用户说"今天到此 / 明天继续 / 暂停"或工作落盘 / 做决策 / 长对话收尾 → 自动追一行（含状态标签 `PAUSED` / `DONE` / `决策` + 续接锚点）。`active-context.md`（含模板）头部说明与段名同步为 `## 最近对话延续`，README 增加大白话说明。

## 0.2.1 - 2026-06-07

### 改进

- **假设追踪改为基座自带能力**：不再当作"要另装的外部模块"。`hypothesis/` 目录记假设与证据（一假设一 `H*.md`），复盘结论回写 `wiki/explorations/`，开箱即用、零依赖、无需安装。README / AGENTS / CLAUDE / ARCHITECTURE / INSTALL 全量改为「内置」口径。

### 修复

- 移除文档中指向已转为私有的 `hypothesis-tracker` repo 的失效链接，以及"帮我安装假设追踪"的部署引导（deploy-modules 触发词、workspace-config 模块登记、interfaces 契约同步清理）。

## 0.2.0 - 2026-06-07

### 新增

- **research 研究闭环**（基座自带能力，零依赖起步）：输入源 = `wiki/` + websearch + 可选数据源（tushare / gangtise / 自有 API，key 走环境变量）；按研究要点模板输出到 `output/research/`，每条事实标来源（`[本地]` / `[网页]` / `[推测]` / `[待验证]`）；讨论升级后主动提示"是否沉淀进 wiki"，确认后回写 `wiki/explorations/`，形成闭环。见 `system/skills/research.md`。
- **ARCHITECTURE.md**：架构图（基座 + 槽位 + 维护）+ 文件夹结构图 + 完整闭环图。

### 改进

- **结构精简**：把机械零件（`skills/` `integrations/` `scripts/` `interfaces/` `templates/`）统一收进 `system/`，顶层目录 13 → 8，新人一眼能分清"自己读的"和"agent 用的"。
- **防臃肿加固**：`structure-health` 不再把 `status: planned` 模块的未来输出目录误报为"缺失"；`post-install-cleanup` 增加"瘦身后清扫归档样例残留引用"的步骤，避免死链。

### 文档

- README / INSTALL-FOR-AI 全量同步到 `system/` 路径；README 增加「研究闭环」示例段、「最近更新」段，以及「安装到你自己的工作区」段（首次把 `INSTALL-FOR-AI.md` 链进 README）。

## 0.1.0 - 2026-06-06

- Initial Codex-first, Claude-compatible starter workspace.
- Added personal wiki core with `wiki/_schema.md`.
- Added first-ingest smoke test.
- Added PDF ingest smoke path with optional Python + pypdf path.
- Added simple workspace rules in `workspace/workspace-config.md`.

<!-- 文件说明：版本变化记录。 -->

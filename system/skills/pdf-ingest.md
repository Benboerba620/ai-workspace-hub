# PDF Ingest Skill（可选能力）

> 这是基座上的**第一个可选能力**，也是新增能力的**参考样板**。
> 基座本身不需要它——note → wiki 那条链路零依赖、开箱即用。
> 只有用户要摄入 PDF 时，agent 才按本文件"现装现用"。

当用户说"PDF 转 Markdown""摄入 PDF""开启 PDF 摄入""帮我装 PDF 能力"时，执行这个流程。

## 触发即自装（核心）

agent 第一次执行本能力时，先确认依赖，没有就自己装，不要让用户手动折腾：

1. 检查 Python：`python3 --version`，需要 Python 3.10+。如果版本低于 3.10，改用 `python3.10` / `python3.11` / `python3.12`，或引导用户安装新版 Python；如果环境只有 `python` 且版本 ≥3.10，用 `python --version`。
   - 没有 Python → 引导用户安装 Python 3.10+；Windows 安装器里务必勾选 "Add python.exe to PATH"。这一步需要用户操作，agent 等待即可。
2. 检查并安装 `pypdf`：
   ```bash
   python3 -m pip install -r requirements-pdf.txt
   ```
   装完一次后即可长期复用，无需每次重装。

## 适用边界

- ✅ 文本型 PDF（可复制文字的 PDF）→ 本能力可处理。
- ❌ 扫描件、图片型 PDF、复杂表格、双栏研报、加密 PDF → 超出本能力；引导用户接 OCR / MinerU / 专业解析工具，并在 `workspace/meta/friction-log.md` 记一条。

## 步骤

1. 读取 `AGENTS.md`（Codex）或 `CLAUDE.md`（Claude）。
2. 读取 `wiki/_schema.md`。
3. 转换：
   ```bash
   python3 system/scripts/pdf_to_md.py <input.pdf> <output.md>
   ```
   - 若报缺 `pypdf` → 回到"触发即自装"装好再跑。
   - 若报 "No extractable text" → 大概率是扫描件/图片 PDF，走"适用边界"的兜底。
4. 把生成的 Markdown 当作输入材料，按 `wiki/_schema.md` 分类。
5. 原 PDF 保留在 `wiki/raw/` 或 `inbox/`；结构化摘要写入 `wiki/sources/`。
6. 生成一份任务报告到 `output/`。
7. 更新 `workspace/meta/active-context.md`，记录本次摄入。

## 自检冒烟

repo 自带样例 PDF，可直接验证能力是否就绪：

```bash
python3 system/scripts/pdf_to_md.py inbox/sample-ai-workspace.pdf inbox/sample-ai-workspace.md
```

预期：生成的 `.md` 含标题、`source_pdf` 行和正文段落。

# PDF Ingest Smoke Test

## 结果

PASS，带限制。

系统完成了：

```text
PDF -> Markdown -> raw -> source -> concept -> exploration -> output
```

## 输入

- PDF: `inbox/sample-ai-workspace.pdf`
- Markdown: `inbox/sample-ai-workspace.md`

## 知识库写入

| 类型 | 文件 |
|---|---|
| raw PDF | `wiki/raw/2026-06-05-sample-ai-workspace.pdf` |
| raw Markdown | `wiki/raw/2026-06-05-sample-ai-workspace.md` |
| source | `wiki/sources/2026-06-05-sample-ai-workspace.md` |
| concept | `wiki/concepts/pdf-to-md-ingest.md` |
| exploration | `wiki/explorations/2026-06-05-pdf-ingest-smoke-test.md` |

## 分类判断

- PDF 原件属于 raw。
- PDF 转写 Markdown 属于 raw，因为它是原始材料的文本化版本。
- 单个 PDF 的摘要属于 source。
- “PDF to Markdown Ingest” 是可复用概念，进入 concepts。
- “当前系统能否完成 PDF 输入闭环” 是阶段性判断，进入 explorations。
- 本测试报告是任务产物，进入 output。

## 限制

- 当前脚本是 smoke parser，不是生产级 PDF 解析器。
- 当前环境没有可用 Python、`pdftotext` 或 `mutool`。
- 复杂 PDF、扫描件、表格、图表仍需专业工具。


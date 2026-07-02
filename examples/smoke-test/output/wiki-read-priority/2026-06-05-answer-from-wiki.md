# Answer From Wiki Test

## 用户问题

这个系统里，PDF 输入以后应该怎么进入知识库，并在输出时被优先读取？

## 回答

根据当前 personal wiki 中的材料，系统应该先把 PDF 转成 Markdown，再按 `wiki/_schema.md` 分类进入知识库。具体路径是：

```text
PDF
  -> Markdown
  -> wiki/raw/
  -> wiki/sources/
  -> wiki/concepts/ 或 wiki/entities/
  -> 如有阶段性判断，再进入 wiki/explorations/
  -> 输出任务优先读取 wiki 后再生成 output
```

## 本回答优先读取的 wiki 文件

- `wiki/_schema.md`
- `wiki/sources/2026-06-05-sample-ai-workspace.md`
- `wiki/concepts/pdf-to-md-ingest.md`
- `wiki/explorations/2026-06-05-pdf-ingest-smoke-test.md`

## 结论

`[本地]` 输出任务可以优先读取 wiki 再回答。当前测试已经证明路径可用，但 PDF 解析能力仍是 smoke-test 级别，不是生产级。


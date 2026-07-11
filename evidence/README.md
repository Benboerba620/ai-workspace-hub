# evidence

研究系统的证据账本。每条可能影响假设的新增事实单独保存，避免把行情信号、新闻和用户判断混在同一段文字里。

约定：

- 一条证据一个文件，路径为 `evidence/YYYY-MM/E-YYYYMMDD-{type}-{ref}-{hypothesis}.md`。
- `review_status: pending` 表示只完成了采集，尚未由用户确认其方向和权重。
- 日报可以自动登记可确认的行情或财报信号，但不能自动改变假设的 `certainty` 或 `status`。
- 同一事件使用 `dedup_key` 去重；假设文件只引用证据 ID，不复制整段内容。
- 新闻、管理层表述和行业资料必须保留原始 URL 或本地来源路径。

字段契约见 `system/integrations/object-model.md`。

<!-- 文件说明：用户证据账本的入口和边界。 -->

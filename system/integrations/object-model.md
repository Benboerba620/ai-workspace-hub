# 研究对象与状态契约

> Markdown 是用户界面，frontmatter 是机器可读的当前状态。正文保存分析和历史，不重复维护另一份“当前状态”。

## 稳定 ID

| 对象 | ID 示例 | 唯一真相 |
|---|---|---|
| 研究 | `R20260711-01` | `output/research/*.md` frontmatter |
| 假设 | `H1` | `hypothesis/H*.md` frontmatter |
| 证据 | `E-20260711-mover-ifx-de-H1` | `evidence/YYYY-MM/*.md` frontmatter |
| 待确认动作 | `Q-20260711-01` | `workspace/review-queue.md` 表格 |
| 公司 / 标的 | `IFX.DE` | 市场 ticker；无 ticker 时用稳定 entity slug |

ID 创建后不因标题、文件名或观点变化而改变。旧文件没有 `id` 时仍可读取，并在下次人工更新时补齐，不做批量重写。

## 状态唯一来源

- 假设的当前 `status`、`certainty`、`updated_at`、`last_reviewed_at` 只认 frontmatter。
- 研究的当前 `status` 只认 frontmatter；建议值为 `draft / active / closed / archived`。
- 证据的当前审核状态只认 `review_status`；建议值为 `pending / confirmed / rejected`。
- `config/daily-watchlist-watchlist.md` 是驱动日报的唯一股票池。`monitoring/` 只做用户看板和专题视图。
- 正文日志记录“曾经发生过什么”，不能反向覆盖 frontmatter 的当前状态。

## 证据最小字段

```yaml
---
id: E-20260711-mover-ifx-de-H1
type: evidence
observed_at: 2026-07-11
recorded_at: 2026-07-11
source_type: daily-watch
source_path: daily-watchlist-reports/2026-07/2026-07-11.md
source_url:
direction: pending
confidence: pending
review_status: pending
linked_hypotheses: [H1]
linked_entities: [IFX.DE]
metric: price_change
dedup_key: DW-2026-07-11-mover-ifx-de-H1
---
```

证据正文写清“观察到什么”和“为什么可能相关”。`direction` 只有复盘后才改成 `strengthen / weaken / neutral`；行情涨跌本身默认保持 `pending`。

## 待确认队列

以下动作必须先进入 `workspace/review-queue.md`：

- 把研究结论沉淀进 wiki；
- 新建假设或改变假设确定性、状态；
- 把标的加入执行股票池；
- 把研究偏好观察固化成稳定偏好。

用户确认后先执行动作，再把队列状态改成 `done`；拒绝则改成 `rejected`，保留决策记录。
队列新增、去重和状态更新由 `system/scripts/review_queue.py` 执行。

<!-- 文件说明：跨研究、假设、证据和待确认动作的统一对象协议。 -->

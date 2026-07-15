# 知识生命周期

> 复盘 wiki 中的阶段判断，只晋级可复用、经验证的知识。这是判断流程，不是自动摘要器。

## 触发

用户要求「复盘 wiki / 提炼近期研究 / 验证 exploration / 晋级 pattern / 整理知识链」时使用。

## 加载契约

研究、筛选和综合任务按以下顺序：

1. 全文读 `wiki/explorations/_index.md` 和 `workspace/patterns/_index.md`。两者必须始终保持精简。
2. 用产业链位置、周期阶段、约束类型、催化类型和决策场景描述当前对象。
3. 只打开匹配的 exploration 或 pattern 页面。只有共享关键词不算命中。
4. 在工作笔记里说明命中的 pattern、参照案例和失效条件。没有命中时直接继续，不强造类比。

## 提炼阶梯

```text
raw -> source -> entity/concept -> exploration -> pattern -> rule
                                           \-> false belief when invalidated
```

- `source`：单个来源，不下跨来源结论。
- `exploration`：跨来源阶段判断，默认 `status: tentative`。
- `pattern`：带可观测召回信号和失效条件的可迁移机制。
- `rule`：在至少三个独立案例中被确认为主机制的 pattern。
- `false belief`：原本合理、后被证据推翻的信念。

## 复盘流程

1. 用新证据复盘 tentative exploration，建议 `validated`、`invalidated`、部分验证（保持 `tentative` 并记录缺口）或不变。
2. 所有状态变更建议先写入 `workspace/review-queue.md`；用户确认后才执行。
3. 对新验证的 exploration 问三个问题：
   - 换公司、行业或主题后，是否仍有可迁移结构？
   - 已有 pattern 能否吸收它，且不会丢掉真实因果机制？
   - 若不能，证据是否足够起草新 pattern？
4. 案例并入 pattern 前必须过归因关：这张卡的判别式是否是本案例判断正确的主要原因？
   - `primary`：计入晋级次数。
   - `supporting`：只提供有用语境，不计数。
5. 优先丰富旧卡，避免创建近义重复卡。新卡和并卡都需用户确认。
6. 只有跨独立案例累计三次 `primary` 确认后，才建议晋级到 `wiki/rules.md`。用户决定范围和表述是否足够稳定。
7. exploration 被证伪时，只有它纠正了可能复发的信念，才建议写入 `wiki/false-beliefs.md`；否则保留 invalidated 历史即可。

## 索引维护

- 新建或复盘 exploration 时更新 `wiki/explorations/_index.md`。
- 新建、修改或退役 pattern 时更新 `workspace/patterns/_index.md`。
- 索引是路由层，不是小型报告；详细证据不进索引。

## 边界

- 同一来源或同一底层案例的重复不构成晋级。
- 不根据价格波动单独判定知识已验证。
- 不把用户的个人规则或案例复制进公开模板。
- 不强迫每篇有用 exploration 都晋级 pattern；单一对象事实可继续留在 entity 或 exploration。

<!-- 文件说明：分层知识提炼与选择性加载协议。 -->

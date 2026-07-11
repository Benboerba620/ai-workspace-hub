# First Research（首次研究引导）

> 第一次真实股票研究既产出结论，也建立用户的研究偏好 v0.1。不要先让用户设计模板。

## 触发

用户第一次研究公司，或说“同时建立我的研究方法 / 研究偏好”。若 `workspace/research-profile.md` 的版本为“未建立”，普通公司研究也进入本流程。

## 流程

1. 一次只确认一个关键问题：`为什么现在研究这家公司，最终想支持什么决定？`
2. 建立简短 research brief：分配稳定研究 ID（`RYYYYMMDD-NN`），记录研究对象、决策背景、时间范围、2-4 个可验证问题。
3. 读取 `workspace/research-profile.md`、相关 wiki 和已有假设，再按 `system/skills/research.md` 补充外部证据。
4. 报告必须回答：核心驱动、市场预期、反方证据、估值或预期差、什么会改变判断、未来跟踪什么。
5. 和用户讨论报告。优先记录用户的删改、追问和反驳，不用问一套调查问卷。
6. 研究收口时执行 `system/skills/research-closeout.md`。
7. 把本次体现出的偏好先写入 `workspace/research-profile.md` 的“本轮观察”。用户明确表达过的偏好可确认进入 v0.1；其余候选项写入“待确认调整”和 `workspace/review-queue.md`，不能替用户确认。研究次数加 1。

## 约束

- 一次研究只生成暂定偏好，不称为固定模板。
- 至少 3 次真实研究后，才建议把反复出现的偏好固化成模板。
- 用户没有表达的偏好不得代填为“已确认”。
- 研究报告按 `system/templates/research-report.md` 写入稳定 `id`，后续假设和证据只用 ID 关联，不依赖标题猜测。

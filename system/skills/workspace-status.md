# Workspace Status（研究工作区状态）

> 回答“现在正在做什么、积压了什么、下一步最值得做什么”，不改变任何研究判断。

## 触发

用户说“看看现在该做什么 / 当前有什么待处理 / 研究系统状态 / workspace status”。

## 流程

1. 运行 `python3 system/scripts/workspace_status.py`；Windows 或只有 `python` 的环境使用 `python`。
2. 如有待复盘证据，读取对应 `evidence/` 文件和关联假设，说明为什么值得先处理。
3. 如有 `workspace/review-queue.md` 待确认项，按决策影响排序，不默认批准。
4. 汇总进行中研究、开放假设、到期复盘、股票池状态和研究偏好校准次数。
5. 只推荐 1-3 个下一步，避免把所有可能任务一次性抛给用户。

新增或更新队列项使用 `system/scripts/review_queue.py`，不要手工制造重复 ID：

- 新增：`python system/scripts/review_queue.py add --type hypothesis --object H1 --action "复盘确定性" --source E-...`
- 完成：`python system/scripts/review_queue.py update Q-YYYYMMDD-01 --status done`

## 边界

- 状态检查默认只读。
- “开放”不等于“看多”，“待复盘”不等于需要调整确定性。
- 队列动作仍需用户确认后才能执行。

<!-- 文件说明：把分散文件汇总成用户可行动的研究工作台状态。 -->

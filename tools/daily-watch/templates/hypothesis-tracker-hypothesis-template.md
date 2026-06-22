---
certainty: {INITIAL_CERTAINTY}
status: 新建
created: {DATE}
tags:
  - hypothesis
  - active
aliases:
  - {ID}
---

# {ID}: {NAME}

> 创建日期：{DATE}
> 当前确定性：{INITIAL_CERTAINTY}%
> 状态：新建

---

## 核心逻辑

{CORE_LOGIC}

---

## 证伪条件

| # | 指标 | 阈值（触发证伪） | 时间窗口 |
|---|------|------------------|----------|
| 1 | {KILL_METRIC_1} | {KILL_THRESHOLD_1} | {KILL_WINDOW_1} |
| 2 | {KILL_METRIC_2} | {KILL_THRESHOLD_2} | {KILL_WINDOW_2} |

---

## 投资方向

{INVESTMENT_DIRECTION}

---

## 关联标的

| 公司 | 角色 | 主题 |
|------|------|------|
| {TICKER_1} | 核心标的 | {THEME} |

---

## 确定性变化日志

| 日期 | 确定性 | 变化 | 触发事件 |
|------|--------|------|----------|
| {DATE} | {INITIAL_CERTAINTY}% | 新建 | 假设建立 |

---

## 证据时间线

### {DATE}

- 🟡 **{INITIAL_EVIDENCE}** - {DESCRIPTION}
  - 影响：待补充

---

## Kill Thesis 月度回看

### {YYYY-MM}

1. 如果这个假设错了，最可能的原因是什么？
2. 最近一个月有哪些反面证据被忽略了？
3. 最早能从哪个指标看到转向信号？

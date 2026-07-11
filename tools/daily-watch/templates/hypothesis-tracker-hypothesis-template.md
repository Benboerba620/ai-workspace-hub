---
id: {ID}
type: hypothesis
certainty: {INITIAL_CERTAINTY}
status: 新建
created: {DATE}
updated_at: {DATE}
last_reviewed_at:
next_review_at:
scope: theme
time_horizon: {TIME_HORIZON}
linked_research: []
linked_entities:
  - {TICKER_1}
tags:
  - hypothesis
  - active
aliases:
  - {ID}
---

# {ID}: {NAME}

> 创建日期：{DATE}
> 当前状态与确定性以文件顶部 frontmatter 为唯一准则；本页日志只保存历史变化。

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

> 公司是主题假设的受益映射和验证载体，不是主题假设本身。

| Ticker | 公司 | 角色 | 与主题的关系 | 公司特有风险 |
|------|------|------|------|------|
| {TICKER_1} | {COMPANY_1} | 核心标的 | {THEME_LINK_1} | {COMPANY_RISK_1} |

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

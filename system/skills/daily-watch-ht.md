# Daily Watch HT（假设追踪 + 交易记录）

> 管理投资假设的生命周期：创建 → 追踪 → 交易 → 复盘。
> 假设文件存放在 `hypothesis/`，交易记录在 `portfolio/`。

## 触发词

### 创建假设
"建个假设" / "ht-new" / "新建 hypothesis"

### 查看状态
"假设状态" / "ht-status" / "hypothesis status"

### 记录交易
"记录交易" / "ht-trade" / "买了 / 卖了 XXX"

---

## 创建假设（ht-new）

用户给出投资逻辑，agent 用模板创建假设文件：

```bash
# 模板位置
tools/daily-watch/templates/hypothesis-tracker-hypothesis-template.md
```

**必填项**：
- 假设名称 + 核心逻辑
- Kill Metric（至少 2 个可证伪条件）
- 投资方向（多/空/观望）
- 关联 ticker

**输出**：`hypothesis/H{N}-{slug}.md`

## 查看状态（ht-status）

```bash
python3 tools/daily-watch/scripts/sync_hypothesis.py
```

输出所有假设的当前状态：置信度、状态（active/paused/killed）、关联 ticker。

## 记录交易（ht-trade）

用户说"买了 100 股 NVDA"或"平仓 AAPL"，agent：
1. 记录到 `portfolio/trades.csv`
2. 更新 `portfolio/holdings.csv`
3. 关联到对应假设（如有）
4. 检查风控规则（`config/hypothesis-tracker.rules.md`）：
   - 单只持仓不超总仓位 30%
   - 单假设不超总仓位 50%
   - 总持仓不超 8 只
   - 新仓位必须有止损

```bash
# 查看交易统计
python3 tools/daily-watch/scripts/trade_stats.py
```

## 假设生命周期

```
创建（ht-new）→ 追踪（dw-today 自动关联证据）→ 交易（ht-trade）→ 复盘（确认后回写 wiki/explorations/）
```

## 边界

- 假设追踪是记录和追踪工具，不做自动交易。
- Kill Metric 触发时提醒用户，不自动平仓。
- 风控规则是提醒，不是硬限制。

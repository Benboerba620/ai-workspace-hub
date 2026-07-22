# 产能扩张周期见顶：知识生命周期案例

这个案例提炼自维护者本地 Wiki 中对光伏、锂电和新能源车周期的复盘。公开版本只保留理解机制所需的事实和结构，不包含私人笔记全文。

## 这个案例验证什么

```text
4 个单一来源摘要
  -> 2 个行业 Exploration
  -> 1 个 draft Pattern
  -> 等待新的事前案例验证
```

光伏和锂电是这张 Pattern 的提炼来源，也就是“母案例”。它们可以证明这张卡值得建立，却不能再被计算为 Pattern 的独立确认。因此 `primary_confirmations` 必须保持为 `0`。

## 当前知识状态

| 类型 | 文件 | 状态 | 含义 |
|---|---|---|---|
| Exploration | `wiki/explorations/solar-cycle-review.md` | `promoted` | 两个来源支持复盘，且已提炼进 Pattern |
| Exploration | `wiki/explorations/lithium-cycle-review.md` | `promoted` | 两个来源支持复盘，且已提炼进 Pattern |
| Pattern | `wiki/patterns/capacity-expansion-cycle-top.md` | `draft` | 已形成机制，但尚无事前独立确认 |

## 自己运行

在仓库根目录查看生命周期摘要：

```bash
python3 system/scripts/knowledge_lifecycle.py \
  --root examples/knowledge-lifecycle-cycle-top summary
```

日常加载会排除 draft Pattern，因此下面应返回 0 条：

```bash
python3 system/scripts/knowledge_lifecycle.py \
  --root examples/knowledge-lifecycle-cycle-top load \
  --types pattern --context "制造业扩产 ROIC 设备订单 周期见顶"
```

复盘知识卡时显式加入 `--include-review`，才会看到这张 Pattern：

```bash
python3 system/scripts/knowledge_lifecycle.py \
  --root examples/knowledge-lifecycle-cycle-top load \
  --types pattern --context "制造业扩产 ROIC 设备订单 周期见顶" \
  --include-review
```

## 后续怎样晋级

1. 在固态电池等新行业尚未见顶时，提前用这张卡判断。
2. 结果兑现后，由人判断该机制是否为主要原因；成立才记一次 `primary`。
3. 再用另一个独立行业完成第二次事前验证。
4. 两次独立 `primary` 确认后，才能提议把 Pattern 改为 `active`。
5. 累计三次独立确认后，才讨论是否建立 Rule，例如“命中至少三项供给侧见顶信号时，启动退出复审”。

程序负责检查字段和数量门槛。来源是否独立、归因是否真实、规则是否应该影响投资动作，仍由用户确认。

<!-- 文件说明：用真实周期研究解释母案例、独立确认、Pattern 晋级和默认加载边界。 -->

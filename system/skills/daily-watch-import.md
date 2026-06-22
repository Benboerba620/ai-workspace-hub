# Daily Watch Import（导入 / 管理股票池）

> 导入、编辑、管理 `config/daily-watchlist-watchlist.md` 中的股票池。

## 触发词

"导入股票池" / "加个股票" / "dw-import" / "编辑 watchlist"

## 操作

### 添加股票

用户说"加 NVDA"或给出一批 ticker，agent：
1. 查询基本信息（名称、市场、市值分类）
2. 追加到 `config/daily-watchlist-watchlist.md` 表格
3. 可选：关联已有假设

### 批量导入

用户给出 ticker 列表或粘贴一段文字，agent 提取 ticker 后批量查询并追加。

### 删除 / 调整

用户说"去掉 XXX"或"把 YYY 的 Tier 改成 WARM"，agent 编辑对应行。

## 市值分类（自动判断）

| 分类 | USD | CNY/HKD |
|------|-----|---------|
| Mega | > 200B | > 1T |
| Large | > 10B | > 70B |
| Mid | > 2B | > 15B |
| Small | ≤ 2B | ≤ 15B |

## 边界

- 只管理股票池文件，不触发日报生成。
- 股票池变动后建议跑一次 dw-today 验证。

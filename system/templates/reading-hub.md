# 🏠 阅读台（Reading Hub）

> 工作区的阅读首页，面向 **Obsidian 1.9+**（用到 Bases 功能）。
> 它不是静态清单，而是实时查询：新文件落盘自动出现，读完标注自动归位。

## 怎么用

1. 每天打开本页，先扫「🎯 今日看什么」（近 3 天新内容）。
2. 直接点击表格里的 `read_status` 列，填 `已读` / `精读` / `跳过`；留空就是未读（Obsidian 可能在首次填写后才显示中文列名）。
3. `已读` 和 `跳过` 会自动从待读视图消失；`精读` 进入收藏清单。
4. 全部视图（研究 / 筛选 / Podcast / 日报 / Sources）→ 打开 [[reading-hub.base]]。

> 日期优先读取笔记的 `source_published_at` / `published_at` / `publish_time` / `date`；没有时读取文件名开头的 `YYYY-MM-DD`，再回退到 `created_at` / `created` 和文件时间。同步旧库时不会把所有旧资料误判成今天新增。

## 🎯 今日看什么

![[reading-hub.base#🎯 今日看什么]]

## 📥 Inbox 待处理

![[reading-hub.base#📥 Inbox（未读）]]

---

_不用 Obsidian？删除本文件和 `reading-hub.base` 即可，不影响工作区其他功能。_

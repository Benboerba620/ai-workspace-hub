# Upgrade Workspace（安全升级）

> 更新 Hub 管理的系统文件，同时保护用户研究资料和本地修改。

## 触发

用户明确说“升级 AI Workspace Hub / 检查新版本 / 更新工作区”。不要因发现新版本就自动应用。

## 流程

1. 取得新版 Hub 源码目录 `{NEW_HUB_SOURCE}`。
2. 先运行预览，不修改目标：
   `python3 system/scripts/upgrade_workspace.py --source "{NEW_HUB_SOURCE}" --target "{WORKSPACE}"`
3. 向用户解释四类结果：受管文件变化、只新增不覆盖的迁移文件、需要人工合并的混合文件、不会触碰的用户文件。
4. 用户明确确认后，才加 `--apply-managed`。
5. 告知备份目录，并再次运行 `check_workspace.py` 和测试。

## 边界

- 用户文件永不自动覆盖。
- 混合文件只提示人工合并。
- 不删除新版中已不存在的旧文件。
- 不自动 commit、push 或发布。

<!-- 文件说明：基于文件归属清单的可预览、可备份升级流程。 -->

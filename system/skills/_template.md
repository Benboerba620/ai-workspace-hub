# {能力名} Skill

> 复制本文件为 `system/skills/{能力名}.md`，按下面的槽填好，就给系统加上了一个新能力。
> 参考已填好的范例：`system/skills/screen.md`、`system/skills/podcast.md`、`system/skills/daily-watch.md`。

## 这个能力做什么

- 一句话定位：`{把什么变成什么 / 解决什么}`。
- 类型：`输入侧`（喂进 `wiki/`）或 `输出侧`（产出到 `output/`）。
- 触发词：用户说 `{"帮我 X""X 一下"}` 时执行。

## 前置条件

agent 第一次执行时先确认依赖，缺什么自动装：

1. 检查运行时：`{python3 --version / node --version / 其他}`；Python 工具默认需要 3.10+，如果 `python3` 版本过低，改用 `python3.10` / `python3.11` / `python3.12`；如果环境只有 `python` 且版本合格，用 `python --version`。
2. 安装依赖：
   ```bash
   python3 -m pip install -r tools/{能力名}/requirements.txt
   ```

> 纯 markdown 读写的能力（如 research）不需要装依赖，可删掉本节。

## 适用边界

- ✅ `{能稳定处理的情况}`
- ❌ `{超出能力的情况}` → 引导用户接专业工具，并在 `workspace/meta/friction-log.md` 记一条。

## 步骤

1. 读取 `workspace/workspace-config.md`。
2. 读取 `wiki/_schema.md`（涉及写入 wiki 时）。
3. 执行核心动作：`{命令或流程}`。
4. 把产物按归属落盘：输入侧 → `wiki/`；输出侧 → `output/`。
5. 更新 `workspace/meta/active-context.md`，记录本次执行。
6. 卡住或发现新 edge case → 写 `workspace/meta/friction-log.md`。

## 在 workspace-config 登记

在 `workspace/workspace-config.md` 的「内置工具」或「内置核心」下加：

```markdown
### {能力名}
- status: `enabled`
- skill: `system/skills/{能力名}.md`
- project_path: `./tools/{能力名}`   # 有代码目录才填
```

## 冒烟测试

```bash
{一条能验证能力就绪的最小命令}
```

预期：`{可见的成功结果}`。

# {能力名} Skill（可选能力）

> 复制本文件为 `system/skills/{能力名}.md`，按下面的槽填好，就给基座加上了一个新能力。
> 参考已填好的范例：`system/skills/pdf-ingest.md`（PDF → Markdown，输入侧）。
>
> 基座（note → wiki → output → friction + active-context）零依赖、开箱即用。
> 能力是基座之外的可选项：用户要用时，agent 读本文件「现装现用」，不需要用户预先配环境。

## 这个能力做什么

- 一句话定位：`{把什么变成什么 / 解决什么}`。
- 槽位：`输入侧`（喂进 `wiki/`）或 `输出侧`（产出到 `output/`）。
- 触发词：用户说 `{"开启 X""帮我 X""X 一下"}` 时执行。

## 触发即自装（核心）

agent 第一次执行本能力时，先确认依赖，没有就自己装，不要让用户手动折腾：

1. 检查运行时：`{python --version / node --version / 其他}`。
   - 没有 → 引导用户安装，并说明跨平台注意事项（如 Windows PATH）。这一步需要用户操作，agent 等待即可。
2. 检查并安装依赖：
   ```bash
   {python -m pip install -r requirements-{能力名}.txt  /  npm i ...}
   ```
   装一次即可长期复用，无需每次重装。

> 无需运行时、纯 markdown 读写的能力可删掉本节——那其实属于基座，不必单列成能力。

## 适用边界

- ✅ `{能稳定处理的情况}`
- ❌ `{超出能力的情况}` → 引导用户接专业工具，并在 `workspace/meta/friction-log.md` 记一条。

## 步骤

1. 读取 `AGENTS.md`（Codex）或 `CLAUDE.md`（Claude）。
2. 读取 `wiki/_schema.md`（涉及写入 wiki 时）。
3. 执行核心动作：`{命令或流程}`。
4. 把产物按归属落盘：输入侧 → `wiki/`；输出侧 → `output/`。
5. 更新 `workspace/meta/active-context.md`，记录本次执行。
6. 卡住或发现新 edge case → 写 `workspace/meta/friction-log.md`。

## 在 workspace-config 登记一行

在 `workspace/workspace-config.md` 的「可选模块」下加：

```markdown
### {能力名}
- status: `enabled` / `planned`
- script: `system/scripts/{...}`        # 有脚本才填
- deps: `requirements-{能力名}.txt`  # 有依赖才填
- slot: `input` / `output`
```

## 自检冒烟

```bash
{一条能验证能力就绪的最小命令}
```

预期：`{可见的成功结果}`。

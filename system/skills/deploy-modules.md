# Deploy Modules Skill（一键部署官方模块）

> 纯 agent 驱动。用户**说一句话**，agent 自己 `git clone` 官方模块、接线到基座、连进 wiki。
> 不写独立安装器脚本——安装逻辑就在本文件里，Codex / Claude 通用。

## 触发词

| 用户说 | 部署 |
|---|---|
| "帮我安装博客抓取" / "装 pod2wiki" / "我想抓播客和博客" | pod2wiki |
| "帮我安装日报监控" / "装 daily-watchlist" / "我要每日盯盘日报" | daily-watchlist |
| "部署官方模块" / "把模块都装上" | 逐个询问后部署 |

> 假设追踪不在此表：它是**基座自带能力**（`hypothesis/` + 复盘回写 `wiki/explorations/`），开箱即用，无需 clone。契约见 `system/integrations/hypothesis-tracker.md`。

## 模块登记表（唯一事实源）

| 友好名 | 模块 | GitHub | clone 到 | 槽位 | 接口契约 |
|---|---|---|---|---|---|
| 博客/播客抓取 | pod2wiki | `https://github.com/Benboerba620/pod2wiki` | `./pod2wiki/` | 输入 | `system/integrations/pod2wiki.md` |
| 日报监控 | daily-watchlist | `https://github.com/Benboerba620/daily-watchlist` | `./daily-watchlist/` | 输出 | `system/integrations/daily-watchlist.md` |

## 部署步骤（对每个要装的模块）

1. **确认**：告诉用户这一步会 `git clone` 一个外部 repo、可能需要回答几个配置问题、花几分钟；问一句"现在装吗？"。用户犹豫 → 提示"也可以之后再说『帮我安装{友好名}』"，不阻塞。
2. **拉取**：在 workspace 根目录执行
   ```bash
   git clone <对应 GitHub URL> <对应 clone 目录>
   ```
   - 没装 git → 引导用户安装 git 后重试。
   - 已存在同名目录 → 问用户是覆盖、跳过还是改名，不要默默 `rm`。
3. **读契约**：读该模块的 `system/integrations/{模块}.md`，按里面的"文件契约"确定它读哪、写哪。
4. **接线到基座**（关键——这步让它"连成一个系统"）：
   - 更新 `workspace/workspace-config.md` 对应条目：`status: enabled`、填 `project_path`。
   - 更新 `system/interfaces/README.md` 同一模块：`status: enabled` + 路径。
   - 确认它的**输入接 wiki**（材料落 `wiki/raw/`、`wiki/sources/`）或**输出接 wiki**（产物落 `output/`，长期结论回写 `wiki/explorations/`，证据回写 `hypothesis/`）。
5. **跑模块自带安装**：若 clone 下来的 repo 有自己的依赖（`requirements.txt` / `package.json`）或安装脚本（`install.ps1` / `INSTALL` / README 步骤），**优先按它自己的说明装**，缺依赖时引导用户，不要默认全局安装。
   - ⚠️ **以模块 installer 的实际产物为准**：有的模块 installer 会把代码搬到别的目录（如 `./tools/{模块}/`）。这种情况下，第 4 步登记的 `project_path` 要填 **installer 装好后的真实路径**，不是第 2 步的原始 clone 目录；原始 clone 若变成冗余副本，提示用户可删，别两份并存让人困惑。
   - 🔑 **需要用户提供的密钥/账号**：若模块的 config / `.env` 有 API key、cookie、token 等占位项（如 `LLM_API_KEY`），这些**必须由用户填**，agent 不许编造。把它列成"装好了，但真正使用前你需要填 X"告诉用户，并写进 active-context 续接锚点。
6. **验证**：跑该模块最小命令或 dry-run，确认产物确实落进 wiki/output 的约定路径。受限于上面的密钥项时，验证到"配置校验通过 / dry-run 通过"即可。
7. **记录**：更新 `workspace/meta/active-context.md`（含尚待用户补的密钥项）；卡住写 `workspace/meta/friction-log.md`。

## 连成系统：模块与 wiki 的关系

```text
博客/播客抓取(pod2wiki) ──→ wiki/raw + wiki/sources ──┐
                                                      ├─→ wiki(知识库)
日报监控(daily-watchlist) ←── wiki/entities + monitoring┘
        │
        └─→ output/daily-watchlist  +  证据回写 hypothesis/
                                            │
                              基座自带的假设追踪 读写 hypothesis/，复盘回写 wiki/explorations/
```

输入模块只管把材料变成 wiki 可读页面；输出模块消费 wiki 产报告、回写证据。基座（wiki + output + hypothesis）始终是中枢，模块只接口子。

## 边界

- 不改模块源码，只 clone + 接线。
- 用户想装登记表之外的东西（别的项目、自己 DIY）→ 不在本 skill 范围；引导走 `system/integrations/_template.md` 自己接。
- 任一模块缺席都不能影响基座的 note → wiki 链路独立运行。

# 知识生命周期

> 把阶段判断逐步提炼为可复用知识，并让稳定的 pattern / rule 能在后续研究中被准确调用。生命周期不是“越高越正确”，而是让每条知识都知道来源、适用范围、失效条件和下次复审时间。

## 触发

用户要求「复盘 wiki / 提炼近期研究 / 验证 exploration / 晋级 pattern / 形成 rule / 加载相关规则 / 整理知识链」时使用。研究、筛选、假设复盘开始时，也应按本文执行一次选择性加载。

## 三类知识卡

| 类型 | 位置 | 作用 | 默认状态 |
|---|---|---|---|
| exploration | `wiki/explorations/` | 跨来源的阶段判断，允许仍有缺口 | `tentative` |
| pattern | `wiki/patterns/` | 跨案例可迁移的机制和判别式 | `draft` |
| rule | `wiki/rules/` | 经过至少三个独立案例确认的决策规则 | `candidate` |

每张卡必须有稳定 ID、一句话摘要、召回信号、决策场景、复审日期和来源关系。Pattern 还必须写失效条件；Rule 必须限定适用范围和证伪信号。

## 状态生命周期

```text
exploration: tentative -> validated -> promoted
                         -> weakened -> invalidated
                         -> archived

pattern:     draft -> active -> promoted
                      -> weakened -> retired
                      -> archived

rule:        candidate -> active -> weakened -> deprecated
                         -> archived
```

- `weakened` 不是删除：新证据削弱了它，默认停止调用，等待复审。
- `invalidated / retired / deprecated` 保留历史和反例，但不进入正常研究上下文。
- `archived` 只表示不再日常使用，不删除文件。
- `supersedes / superseded_by` 用于记录新旧知识替代关系，禁止静默改写历史。

## 总结机制

三类知识各有一个短索引：

- `wiki/explorations/_index.md`
- `wiki/patterns/_index.md`
- `wiki/rules/_index.md`

索引只保留 ID、状态、一句话摘要、召回/失效信号和复审日期，不复制正文证据。新建、复盘或状态变化后运行：

```bash
python3 system/scripts/knowledge_lifecycle.py --root . rebuild-index --apply
```

Windows 只有 `python` 时用 `python`。索引由脚本生成，不手工维护；先预览时省略 `--apply`。

查看知识库存、到期复审和晋级候选：

```bash
python3 system/scripts/knowledge_lifecycle.py --root . summary
```

## 加载机制

不要每次全文读取 Wiki。先用当前研究的产业链位置、周期阶段、约束类型、催化类型和决策问题组成 `context`，再调用加载器：

```bash
python3 system/scripts/knowledge_lifecycle.py --root . load \
  --context "AI 服务器 800V 电源架构，功率器件供给瓶颈，公司映射" \
  --limit 8 --record --research-id R-20260720-01
```

加载顺序固定为 `rule -> pattern -> exploration`。只有召回信号、决策场景或结构化筛选命中才加载全文；共享宽泛关键词不算可靠命中。默认排除 `draft / weakened / invalidated / retired / deprecated / archived`，复盘这些卡时才显式增加 `--include-review`。

也可以用结构化筛选减少误召回：

```bash
python3 system/scripts/knowledge_lifecycle.py --root . load \
  --domain investing --ticker IFX.DE \
  --scenario "公司研究" --signal "电源架构升级"
```

`--record` 会把本次真正加载的知识 ID 追加到 `workspace/knowledge-usage.jsonl`。它不改变知识状态，只为以后判断“哪些规则经常被调用、哪些从未命中”保留事实记录。

Agent 在研究正文或工作笔记中必须写明：

- 本次调用了哪些 rule / pattern；
- 为什么命中；
- 适用范围和失效条件；
- 没有命中时明确写“未命中可复用知识”，不要强造类比。

## 提炼阶梯

```text
raw -> source -> entity/concept -> exploration -> pattern -> rule
                                           \-> false belief when invalidated
```

1. `source` 只总结单一来源，不下跨来源结论。
2. `exploration` 至少关联两个独立来源，验证后才能 `validated`。
3. 新验证的 exploration 只有存在跨公司、行业或主题仍成立的机制，才起草 pattern。
4. Pattern 至少有两个独立案例被归因为 `primary`，才能从 `draft` 变为 `active`。
5. Pattern 至少累计三个独立 `primary` 确认，才可提议晋级 rule。
6. Rule 必须关联来源 pattern、限定 scope、写明 invalidation signals，并有至少三个独立案例确认，才能 `active`。

`primary` 表示该机制是案例判断正确的主要原因；只提供语境时记 `supporting`，不计入晋级次数。同一来源、同一公司同一事件的重复材料不算独立案例。

## 升级与降级

所有状态变化先说明证据、反方证据和影响，再进入 `workspace/review-queue.md`；只有用户确认后才执行。命令默认只预览，使用 `--queue` 追加待确认动作，真正写入必须同时提供 `--apply --confirmed`：

```bash
python3 system/scripts/knowledge_lifecycle.py --root . transition \
  wiki/patterns/example.md --to active \
  --reason "两个独立案例确认该机制是主要原因" \
  --evidence EXP-20260701-01 --evidence EXP-20260715-01 \
  --queue
```

用户确认队列项后，复用同一命令改用 `--apply --confirmed` 执行。脚本会检查状态路径和晋级门槛，写入生命周期记录，并重建三个索引。没有用户确认、缺少来源、缺少复审日期或未达到独立案例数量时，不得绕过检查直接改 status。

出现以下情况时提议降级复审：

- 新证据直接击穿核心机制；
- 适用范围比原先窄，旧表述会误导决策；
- 召回后多次没有帮助，或常被错误套用；
- 到 `review_due` 仍没有新验证；
- 已有新卡通过 `supersedes` 更准确地覆盖它。

## 复盘顺序

1. 运行 `summary`，先看已到期知识和晋级候选。
2. 对照最新 evidence、research、hypothesis 和反例，判断保持、升级、弱化或退役。
3. 先修正适用范围、召回信号和失效条件，再决定状态，不只看预测结果对错。
4. 用户确认后执行 transition，自动更新索引。
5. 运行 `workspace_doctor.py`，检查 ID、状态、来源链、替代关系和复审字段。

## 边界

- 不根据单日价格波动判定知识已验证或失效。
- 不让调用次数代替证据质量；“常用”不等于“正确”。
- 不强迫每篇 exploration 晋级。单一对象事实可以长期留在 entity 或 exploration。
- 被证伪但可能反复诱导判断的直觉，才额外写入 `wiki/false-beliefs.md`。
- 旧 `workspace/patterns/` 和 `wiki/rules.md` 内容不会自动移动；脚本可读取旧 pattern 卡，迁移需逐条确认。

<!-- 文件说明：分层知识提炼、生命周期状态、索引总结与选择性加载协议。 -->

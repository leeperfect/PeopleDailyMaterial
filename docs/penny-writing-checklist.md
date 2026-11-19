# Penny 公众号写作清单

权威来源：`AGENTS.md`、`docs/writing-workflow.md`。  
**注意：** Trae templates 中的金句顺序已过时；文末必须先「金句集合」再「参考文章」，以 AGENTS 为准。

作者固定：`LeePerfect`。

## 开写前核对

1. 读 `data/articles/选题库.md`、`data/articles/文章索引.md`、`data/data_analysis/overview.md`（及最新运营报告）。
2. 选题 ≥3 篇人民日报支撑；切口独立；核对索引避免重复已成稿/已发表。
3. 下一编号以文章索引为准（人民日报系列数字编号 / 热点系列「热点N」）。
4. 加载本清单后再动手。

## 流水线（七步）

1. **选题确认** — 选题库 + 文章索引 + overview；≥3 篇人民日报；编号以索引为准。
2. **写稿四项产物** — 调用 `peopledaily-article-production`：成稿、小红书、教研复盘、过程稿；同步文章索引。
3. **用语预检** — `python3 scripts/check_public_wording.py "<成稿>" "<小红书>"`；「必须改写」清零。
4. **一润并送得到** — `snapshot … --stage draft` → `humanizer-zh`（≥45/50，保 YAML/事实/数字/引用/框架）→ 再预检 → `writing_workflow.py send`。长期授权：一润后直接送得到，勿再索要全文外发确认。
5. **拉回加粗配图** — `pull`（校验不过不覆盖）→ 只加粗 8–15 处 → `register-figures` / `apply-figures`；**本阶段不建平台草稿**。
6. **本地确认配图** — 工作台确认，或 `confirm-inline-figures`；确认前不得 sync。
7. **同步双平台草稿** — `dual-platform-draft-sync` + `gzh-design` zen-whitespace 小米橙 HTML（0 ERROR / 0 WARNING，见 docs/visual-spec-zen-whitespace-fresh.md）→ `sync-dual`；只建草稿，不发布、不群发。

## 成稿结构硬规则

- 标题：`NN｜《人民日报》深度分析【主题】：副题`；禁「讲/讲透/谈」。
- 开篇普通读者向；禁考生开场。
- 第六节固定：`## 六、国考省考申论面试怎么用`。
- 文末：先 `## 金句集合`，再 `## 参考文章`。

## 安全红线

- 公开成品执行 `docs/public-content-wording-safety.md`；不得谐音/拆字等绕审。
- 预检时机：四项产物后送二润前；一润后再检；拉回后同步平台前。
- **不可改写：** `data/raw/`、`data/core/`、`data/vault/`。

## 口令

| 口令 | 动作 |
|---|---|
| 写稿 | 写稿 → 预检 → 一润 → send（连续） |
| 送去二润 / 写完并送去二润 | 兼容；有稿则从 snapshot+一润起 |
| 拉回 / 我在得到改好了，拉回 | pull → 加粗 → 配图登记；停在本地 |
| 同步双平台草稿 | 确认配图后完整 sync-dual |
| 图片插好了 / Obsidian 配图完成 | 先 `confirm-inline-figures` 再同步 |
| 同步到公众号草稿箱 | 单平台重试，仍须过门槛 |

## 路径

| 产物 | 路径 |
|---|---|
| 成稿 | `data/articles/人民日报系列/` 或 `热点系列/` |
| 往期 | `data/articles/往期文章/…`（手动归档） |
| 小红书 | `data/xiaohongshu/` |
| 复盘/过程稿 | `data/analysis/` |
| 配图 | `media/` |
| 排版缓存 | `.local/gzh-out`（仅缓存） |

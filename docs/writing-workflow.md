---
type: writing_workflow
updated: 2026-07-12
scope: PeopleDailyMaterial
---

# 公众号写作、二次润色与草稿箱工作流

这套流程把 Codex 写作、Humanizer-zh、得到大脑二润、NotebookLM 配图、doocs/md 排版和公众号草稿箱连成一条线。日常只需要两条命令：“写稿”和“拉回”，不需要打开 IDE。

## 两条命令完成全流程

| 你说的话 | 自动完成的工作 | 停留位置 |
|---|---|---|
| `写稿` | 真实来源核验 → 四项文字产物 → Humanizer 一润 → 送入得到大脑 | 等待你在得到 App 完成二润 |
| `拉回` | 得到稿拉回 → 重点加粗 → NotebookLM 配图登记 → 配图托盘初排 → 排版和接口预检 → 上传公众号草稿箱 | 等待你在公众号后台检查并设置原创、赞赏和合集 |

说“拉回”前，只需把当前文章的 NotebookLM PPT 和信息图附在消息中，或者保存在 `Downloads`。流程会优先读取本轮附件；没有附件时，先复用本文已登记的素材，再从 `Downloads` 中识别与当前主题相符的最新 PPTX 和信息图。候选不唯一或主题无法确认时会停下来请你选择，不会猜测，也不会先上传无图稿。

## 日常操作

### 第一次准备

对 Codex说：

> 配置公众号写作工作流。

Codex会检查 Get笔记、固定封面和 doocs/md。doocs/md 固定在 `writing_workflow.json` 记录的版本，安装在被 Git 忽略的 `.local/doocs-md/`。

### 写稿

对 Codex说：

> 写稿。

Codex执行：

1. 调用 `peopledaily-article-production` Skill。
2. 按选题卡读取全部真实来源，补充 `Codex 教研速读`。
3. 先建立递进逻辑，再生成选题复盘、过程稿和平台要求的文字产物。
4. 成稿进入当前有效的 `data/articles/人民日报系列/` 或 `data/articles/热点系列/`，并更新统一文章索引。
5. 按 Skill 验收清单检查参考文章、金句集合、Markdown 重点和考场迁移。
6. 保存初稿快照，调用 Humanizer-zh 完成一润并通过质量检查。
7. 把一润稿送入得到大脑，记录该文章的精确 `note_id`。
8. 同步到 Notion 自媒体内容分发台账：

   ```bash
   python3 scripts/sync_articles_to_notion_distribution.py --dry-run
   python3 scripts/sync_articles_to_notion_distribution.py --delay 0.25
   ```

   为新文章创建内容库记录和 8 条分发记录（公众号文章/图文、视频号、小红书图文/视频、抖音、快手、微博）。已存在的记录不重复创建，不覆盖发布状态、发布时间和发布链接。

这一步结束时，文章已经送入得到大脑。你只需要在得到 App 中完成二润，然后说“拉回”。

### 兼容旧口令：送去二润

对 Codex说：

> 送去二润。

Codex执行：

1. 保存 `00-draft.md` 初稿快照。
2. 调用 Humanizer-zh 润色正文，保留 YAML、事实、数字、来源和教学框架。
3. 保存 `01-humanizer.md` 快照。
4. 只把标题和正文送入得到大脑，并记录真实 `note_id`。

“送去二润”和“把这篇文章写完并送去二润”继续可用；但日常直接说“写稿”就会自动完成这一段。

得到笔记标题包含 `[PD-工作流编号]`，不会靠标题猜测文章身份。

### 从得到大脑拉回

你在 App 中完成二润并准备好 NotebookLM PPT、信息图后，对 Codex说：

> 拉回。

拉回前会检查：

- 正文是否真的发生变化；
- 是否异常缩短；
- 一级标题是否丢失；
- 参考文章/资料来源栏目是否丢失；
- 原有来源链接是否丢失。

校验不通过时只保存候选稿和差异报告，不覆盖本地成稿。YAML 始终保留在本地，不参与 App 润色。

拉回成功后，Codex还会完成一次“重点加粗审查”：

- 只在得到版正文上增加 `**加粗**`，不再改写文字；
- 优先标注核心判断、总公式、章节结论、申论表达和面试关键动作；
- 避免整段加粗、普通事实加粗或每一项都加粗；
- 通常保留 8—15 处重点，按文章长度调整；
- 运行下面的校验，确认除加粗标记外文字与结构完全一致：

  ```bash
  python3 scripts/writing_workflow.py emphasis-check "<文章路径>"
  ```

重点审查通过后，流程继续自动完成：

1. 从本轮附件、本文已有清单或 `Downloads` 定位当前文章的 NotebookLM PPT 和信息图；
2. 拆分 PPT、统一命名、检查尺寸，生成配图清单和审查页；
3. 用公众号配图托盘形成初始排图方案，记录采用图片、顺序和章节位置；
4. 生成与正式发布一致的 doocs/md HTML；
5. 执行公众号接口预检和发布模拟；
6. 全部通过后创建公众号草稿，绝不自动群发。

如果得到稿校验、素材识别、图片质量、排版或公众号接口任一环节没有通过，流程会停在该环节，不会覆盖正确版本，也不会上传缺图稿。

### 预览排版

对 Codex说：

> 预览一下公众号排版。

Codex使用 doocs/md 生成只读成品页，通过仅监听 `127.0.0.1` 的临时服务在内置浏览器打开。页面带“复制公众号富文本”按钮，既可检查，也可作为接口不可用时的兜底。

默认排版：

- 经典主题；
- 无衬线字体、16px；
- 主题色 `#ff6a2a`；
- H2 默认样式、图注仅使用 alt；
- 代码主题使用截图中的 stackoverflow-light；
- Mac 代码样式开启、行号关闭；
- 外链转引用关闭；
- 首行缩进和两端对齐开启。

需要换主题时说：

> 打开完整排版编辑器。

Codex在后台启动 doocs/md 并在内置浏览器载入文章。确定后说“把这个排版保存为本文设置”，单篇设置会写入本地工作流状态；下一次预览和发布继续使用它。

如果在完整编辑器中修改了正文，点击“发布（进入下一步）”后：

- 结构检查通过：正文自动写回源 Markdown，并保存修改前快照；
- 排版修改：主题、颜色、字号、缩进等保存到本文 `wechat_layout`；
- 结构、参考文章或来源受损：只保存候选稿，暂停覆盖和草稿同步。

### 公众号配图托盘（“拉回”时自动执行）

NotebookLM 导出的 PPT 和信息图先登记为本文素材。对 Codex说：

> 登记这篇文章的 NotebookLM 配图。

登记时会拆分 PPT 页面、统一命名、检查尺寸，并生成配图清单和审查页；原图进入 `media/`，使用记录保存在文章对应的 `figure-manifest.yml`。

如需在自动初排后人工调整，可以再说：

> 开启公众号配图托盘。

完整排版编辑器顶部会出现“公众号配图托盘”按钮。托盘可以预览全部候选图、勾选实际使用的图片，并指定插在某个二级标题之前或参考文章之前。保存后会同时完成三件事：

1. 把图片引用写回公众号 Markdown；
2. 在配图清单中记录使用状态、顺序和位置；
3. 刷新编辑器预览，后续上传草稿继续使用同一组图片。

“拉回”流程会默认按文章结构生成一版初始方案。每次应用新方案前都会保存文章快照，未采用的图片继续留在候选区，不会删除。

### 同步公众号草稿箱（“拉回”时自动执行）

对 Codex说：

> 同步到公众号草稿箱。

这个旧口令继续保留，适合单独重试上传；正常情况下说“拉回”已经会自动执行。

同步过程：

1. 使用同一份 doocs/md HTML；
2. 按文章系列自动选择固定封面；
3. 上传本地正文图片并换成微信素材地址；
4. 作者固定为 `LeePerfect`；
5. 默认开启评论，且所有读者均可评论；
6. 创建草稿并记录 `media_id`；
7. 不调用群发接口；
8. 草稿创建成功后，提醒你在公众号后台手动配置以下三项（公众号后台 Vue.js 单页应用不支持自动化浏览器操作）：
   - **原创声明**：文字原创，作者 `LeePerfect`；
   - **赞赏**：确认账户为 `LeePerfect`；
   - **合集**：按文章系列选择对应合集（人民日报系列→"人民日报"，热点系列→"热点"）。

相同正文和排版已创建过草稿时，流程会停止重复同步，除非你明确要求重新创建。

公众号 API 不支持原创、赞赏和合集设置，这三项只能通过网页手动操作。草稿创建成功后，Codex会提醒你完成配置。

## 公众号接口首次启用

第一次同步时，Codex一次只引导一个步骤：

1. 在内置浏览器打开微信公众平台，等待你扫码。
2. 引导进入“设置与开发 → 基本配置”。
3. 引导找到 AppID，并启用或重置 AppSecret。
4. 打开仅监听本机的私密配置页：

   ```bash
   python3 scripts/writing_workflow.py setup-wechat
   ```

5. 你在密码框填写凭证。密钥只保存到 `.env`，不进入聊天、日志和 Git。
6. Codex查询当前公网 IP，引导加入 IP 白名单。
7. Codex验证 access_token。
8. Codex调用只读的草稿数量接口检查权限，不创建测试草稿。

若账号没有草稿接口权限，Codex改用内置浏览器登录公众号后台，自动填写标题、作者、摘要、封面和富文本正文。若公众号页面变化导致自动代填失败，则使用只读预览页的一键复制按钮。

## 固定封面

| 文章系列 | 本地文件 |
|---|---|
| 人民日报系列 | `media/images/wechat-fixed-covers/people-daily-header.png` |
| 热点系列 | `media/images/wechat-fixed-covers/hotspot-header.png` |

封面真实文件由网盘同步，不进入 Git；文字索引见 `media/_index.md`。

## 状态和版本

- 本地机器状态：`data/core/writing_workflow_state.json`，已忽略。
- access_token 缓存：`data/exports/wechat_token_cache.json`，已忽略。
- 一润稿、拉回前稿、二润候选稿、重点加粗审查和差异报告：
  `data/analysis/日期/writing-workflow/工作流编号/`。
- 临时 HTML 预览：`/tmp/peopledaily-writing-preview/`，不进入项目。

Markdown 成品稿始终是最终事实源；得到大脑只承担二润中转。

## 命令速查

通常由 Codex代为执行：

```bash
python3 scripts/writing_workflow.py doctor "<文章路径>"
python3 scripts/writing_workflow.py setup-doocs
python3 scripts/writing_workflow.py snapshot "<文章路径>" --stage draft
python3 scripts/writing_workflow.py send "<文章路径>"
python3 scripts/writing_workflow.py pull "<文章路径>"
python3 scripts/writing_workflow.py emphasis-check "<文章路径>"
python3 scripts/writing_workflow.py preview "<文章路径>"
python3 scripts/writing_workflow.py editor "<文章路径>"
python3 scripts/writing_workflow.py register-figures "<文章路径>" --pptx "<PPT路径>" --infographic "<信息图路径>" --slug "<英文主题标识>"
python3 scripts/writing_workflow.py apply-figures "<文章路径>" --initial
python3 scripts/writing_workflow.py save-layout "<文章路径>" --theme grace
python3 scripts/writing_workflow.py setup-wechat
python3 scripts/writing_workflow.py wechat-preflight
python3 scripts/writing_workflow.py publish "<文章路径>" --dry-run
python3 scripts/writing_workflow.py publish "<文章路径>"
python3 scripts/writing_workflow.py status "<文章路径>"
```

## 安全边界

- AppSecret、Get笔记密钥、access_token 不写入文章、日志或 Git。
- 不自动 Git commit。
- 不自动群发。
- 浏览器自动代填只在你明确要求“同步草稿箱”后执行。

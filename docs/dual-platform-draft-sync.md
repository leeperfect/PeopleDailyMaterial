---
type: operating_procedure
updated: 2026-08-22
scope: PeopleDailyMaterial
---

# Obsidian 配图稿同步到公众号和今日头条：固定操作方案

## 一句话口令

日常最短说法：

> 第 81 篇已经在 Obsidian 配好图片。使用 `$dual-platform-draft-sync`，登记正文图片并同步到公众号和今日头条草稿箱；只保存草稿，不发布。

如果当前 Agent 已经能够准确识别文章，也可以直接说：

> Obsidian 图片已插好，同步双平台草稿。

## 使用前提

- 得到二润稿已经拉回并通过正文、来源和结构校验；
- 重点加粗审查已经通过；
- 图片已经粘贴到正式文章 Markdown 的正确位置；
- 公众号接口配置有效；
- Chrome 已登录今日头条创作后台。

## 固定流程

### 1. 定位文章

按用户给出的文章编号或路径，只选择一个成稿：

- 人民日报系列：`data/articles/人民日报系列/`
- 热点系列：`data/articles/热点系列/`
- 已发表文章仅在用户明确要求重同步时读取 `data/articles/往期文章/`。

标题相似但编号不同的文章不能互相替代；出现多个候选时停止并请用户选择。

### 2. 登记 Obsidian 正文图片并确认配图

```bash
python3 scripts/writing_workflow.py confirm-inline-figures "<文章路径>"
```

这一步会读取 Markdown 图片链接，检查本地文件，建立或刷新 `figure-manifest.yml`，生成两个平台的共用方案，并记录正文和配图指纹。没有图片、文件缺失、位置失效或尺寸异常时停止，不创建无图稿。

### 3. 同步前检查

```bash
python3 scripts/writing_workflow.py status "<文章路径>"
```

必须确认：二润稿通过、重点加粗通过、配图清单存在、状态为 `figures_confirmed`、正文和配图在确认后没有变化。

### 4. 准备并创建双平台草稿

```bash
python3 scripts/writing_workflow.py sync-dual "<文章路径>"
```

公众号端：

1. 用 doocs/md 生成公众号 HTML；
2. 上传 Markdown 中的本地正文图片；
3. 按文章系列选择公众号固定封面；
4. 作者使用 `LeePerfect`，开启评论且不限制粉丝；
5. 只创建草稿并记录 `media_id`，不调用群发。

今日头条端：

1. 生成去除公众号专属样式的独立富文本；
2. 使用已登录 Chrome 填写标题和正文；
3. 按交接包顺序和文字锚点上传本地图片；
4. 检查有序列表、无序列表、加粗和参考文章格式；
5. 上传固定单图封面；
6. 应用固定发布选项；
7. 等待“草稿已保存”，不点击“预览并发布”。

### 5. 今日头条固定设置

| 设置项 | 固定值 |
|---|---|
| 展示封面 | 单图 |
| 封面图片 | `media/images/toutiao-fixed-covers/people-daily-cover.jpg` |
| 添加位置 | 留空 |
| 投放广告 | 投放广告赚收益 |
| 头条首发 | 不勾选 |
| 合集 | 人民日报热点 |
| 同时发布微头条 | 勾选“发布得更多收益” |
| 作品声明 | 只勾选“取材网络” |

头条可能在重新打开草稿后重置部分发布选项。因此，正文、图片和封面需要刷新验证；发布选项由本地模板在每次同步或继续发布前重新套用。

### 6. 保存后验收

- 公众号有草稿 `media_id`；
- 头条标题正确；
- 头条正文图片数量与配图清单一致；
- 没有占位符、缺图、本地文件地址或多余图注；
- 有序列表没有“1. 1.”，无序列表没有双圆点；
- 正文没有残留 `**加粗符号**`；
- 固定头图已经显示；
- 页面明确显示“草稿已保存”；
- 两个平台均未正式发布。

确认后登记：

```bash
python3 scripts/writing_workflow.py mark-toutiao-saved "<文章路径>" \
  --draft-url "<草稿页地址>" --draft-id "<草稿ID>"
```

最终状态应为 `toutiao_draft_saved`。

## Obsidian 图片保存位置

在正式文章中从 PPT 按 `Ctrl+C`/`Command+C` 复制图片，再在 Obsidian 按 `Ctrl+V`/`Command+V`，项目插件会自动保存到：

```text
media/images/YYYY-MM-DD-article-文章编号/
```

文件名依次为：

```text
fig-文章编号-01.png
fig-文章编号-02.png
fig-文章编号-03.png
```

例如第 80 篇、文章日期为 2026-08-22：

```text
media/images/2026-08-22-article-80/fig-80-01.png
```

Markdown 中自动插入：

```markdown
![第80篇配图01](media/images/2026-08-22-article-80/fig-80-01.png)
```

日期优先读取文章 YAML 的 `date`；没有有效日期时使用粘贴当天。文章编号取自文件名开头，例如 `80-文章标题.md` 或 `热点12-文章标题.md`。

如果在非正式文章中使用 Obsidian 默认附件粘贴，图片进入兜底目录：

```text
media/images/article-inbox/
```

正式文章图片不应长期放在 `article-inbox`。`media/` 中的真实图片通过网盘同步，不进入 GitHub；GitHub 只维护 `media/_index.md`。

## 失败与重试

- 公众号成功、头条失败：`sync-dual --platform toutiao`。
- 头条成功、公众号失败：`sync-dual --platform wechat`。
- 正文或图片确认后发生变化：重新执行 `confirm-inline-figures`，不能沿用旧指纹。
- 登录失效或验证码：暂停，等待用户在 Chrome 完成处理。
- 页面变化或保存状态不明：不登记成功，不猜测点击。

无论怎样重试，都不得删除或重复创建已经成功的平台草稿。

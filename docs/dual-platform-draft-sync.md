---
type: operating_procedure
updated: 2026-08-26
scope: PeopleDailyMaterial
---

# Obsidian 配图稿同步到公众号和今日头条：固定操作方案

## 一句话口令

日常最短说法：

> 第 81 篇已经在 Obsidian 配好图片。使用 `$dual-platform-draft-sync`：公众号固定调用 `$gzh-design` 的“红白色系”，今日头条固定使用 Word 文档导入；只保存草稿，不发布。

如果当前 Agent 已经能够准确识别文章，也可以直接说：

> Obsidian 图片已插好，同步双平台草稿。

## 使用前提

- 得到二润稿已经拉回并通过正文、来源和结构校验；
- 重点加粗审查已经通过；
- 图片已经粘贴到正式文章 Markdown 的正确位置；
- 公众号接口配置有效；
- Chrome 已登录今日头条创作后台。
- 全局已安装 `~/.codex/skills/gzh-design/`，且包含 `references/` 与 `scripts/`。

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

### 4. 生成公众号“红白色系”HTML

显式调用 `$gzh-design`，主题固定为“红白色系”，不再逐篇询问主题。按该 Skill 的组件库生成纯 `<section>…</section>` 正文片段，并保证原文段落、配图、金句集合和参考文章完整。

生成后强制运行：

```bash
python3 ~/.codex/skills/gzh-design/scripts/component_lint.py ~/.codex/skills/gzh-design
python3 ~/.codex/skills/gzh-design/scripts/validate_gzh_html.py "<红白色系正文HTML>"
```

组件库检查必须为 0 ERROR；最终 HTML 校验必须为 0 ERROR、0 WARNING。公众号后续上传与预览使用同一份已校验 HTML，不再以 doocs/md 为默认排版来源。

### 5. 准备并创建双平台草稿

```bash
python3 scripts/writing_workflow.py sync-dual "<文章路径>" \
  --wechat-html "<红白色系正文HTML>"
```

公众号端：

1. 读取并复验 `$gzh-design` 生成的红白色系 HTML；
2. 上传 HTML 中引用的本地正文图片；
3. 按文章系列选择公众号固定封面；
4. 作者使用 `LeePerfect`，开启评论且不限制粉丝；
5. 只创建草稿并记录 `media_id`，不调用群发。

今日头条端：

1. 调用 `scripts/build_toutiao_import_docx.py` 生成包含正文图片的 `.docx`；
2. 自动跳过 Markdown H1，避免标题重复进入正文；
3. 生成 `import-payload.json`，记录标题、Word 路径、图片数、正文及配图指纹；
4. 在已登录 Chrome 的新空白编辑页点击“文档导入”并选择该 Word；
5. 单独填写标题栏，检查章节、列表、加粗、参考文章和正文图片；
6. 上传固定单图封面并应用固定选项；
7. 等待“草稿已保存”，不点击“预览并发布”。

生成的 Word 固定保存在 `data/exports/<文章文件名>-toutiao-import.docx`，便于人工复核和失败后重试。

### 6. 今日头条 Word 导入规则与固定设置

- 文件必须是 `.docx` 且不超过 15 MB；
- 图片按 Markdown 原位置嵌入并压缩，数量必须与配图清单一致；
- H1 不导入正文，标题由浏览器单独填写；
- 有序列表、无序列表使用 Word 原生列表，加粗使用 Word 字符格式；
- 只有文档导入不可用或明确失败时，才使用旧富文本逐图上传兜底，并说明原因。

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

### 7. 保存后验收

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

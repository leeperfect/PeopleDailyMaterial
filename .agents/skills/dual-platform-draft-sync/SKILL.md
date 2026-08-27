---
name: dual-platform-draft-sync
description: 将已经在 Obsidian 成稿中插入本地图片的文章，登记配图并同步到微信公众号与今日头条草稿。公众号固定调用 gzh-design 的“红白色系”，今日头条默认生成 Word 并使用“文档导入”。用户说“图片插好了”“同步双平台草稿”或要求复用双平台发布流程时使用；不负责正式发布。
---

# 双平台草稿同步

把 Markdown 视为正文事实源。正文图片只登记一次；公众号使用 `$gzh-design` 的“红白色系”，今日头条使用包含正文图片的 `.docx` 文档导入。两个平台都只保存草稿。

## 入口判断

- 用户说“Obsidian 图片已插好”“图片我配好了”：先运行 `confirm-inline-figures`，再同步双平台。
- 状态已经是 `figures_confirmed`：直接运行 `sync-dual`。
- Markdown 中没有本地图片：停止并说明缺图，不创建无图草稿。
- 未给文章路径时，可按文章编号或当前工作流状态定位；出现多个可靠候选时请用户选择，不猜测。

完整操作方案见项目文档 [双平台草稿同步操作方案](../../../docs/dual-platform-draft-sync.md)。控制今日头条页面前，还要读取 [浏览器执行检查表](references/browser-checklist.md)。

## 固定执行顺序

1. 定位唯一的成稿 Markdown，检查正文和图片链接均存在。
2. 对 Obsidian 手动配图稿执行：

   ```bash
   python3 scripts/writing_workflow.py confirm-inline-figures "<文章路径>"
   ```

3. 用 `status` 确认二润、重点加粗、配图清单和人工确认均通过。
4. **显式调用 `$gzh-design`**，指定“红白色系”，不再询问主题。必须完整读取该 Skill 的 `theme-index.md`、`theme-red-white.md` 和 `common-components.md`，按组件库生成纯 `<section>…</section>` 正文 HTML；不得改写或遗漏正文、图片、金句集合和参考文章。
5. 对公众号产物执行双关校验：组件库检查必须为 0 ERROR；最终 HTML 必须为 0 ERROR、0 WARNING：

   ```bash
   python3 ~/.codex/skills/gzh-design/scripts/component_lint.py ~/.codex/skills/gzh-design
   python3 ~/.codex/skills/gzh-design/scripts/validate_gzh_html.py "<红白色系正文HTML>"
   ```

6. 使用已校验 HTML 执行：

   ```bash
   python3 scripts/writing_workflow.py sync-dual "<文章路径>" \
     --wechat-html "<红白色系正文HTML>"
   ```

   该命令只创建公众号草稿；同时生成今日头条导入用 `.docx` 和浏览器交接记录。公众号不得回退到 doocs/md 作为默认排版。
7. 保留公众号创建成功的 `media_id`。一个平台失败时，只重试失败平台。
8. 在已登录 Chrome 中打开**新的空白头条编辑页**，点击“文档导入”，选择交接记录中的 `docx_path`。标题单独填入标题栏，不把 Markdown H1 导入正文。
9. 等待导入完成，核对标题、章节、加粗、列表、参考文章和正文图片数量；应用固定封面及选项，只保存草稿。
10. 页面显示“草稿已保存”并刷新复核后，运行 `mark-toutiao-saved`，分别报告两个平台结果。

## 今日头条 Word 规则

- 固定转换器：`scripts/build_toutiao_import_docx.py`。
- 生成文件固定保存在 `data/exports/<文章文件名>-toutiao-import.docx`，供浏览器导入和单独重试。
- 文件必须为 `.docx` 且不超过 15 MB；图片按 Markdown 原位置嵌入并压缩。
- 图片数量必须与配图清单一致；H1 不进入正文，平台标题栏单独填写。
- 有序列表和无序列表使用 Word 原生列表；加粗使用 Word 字符格式，不得残留 `**`。
- 仅当“文档导入”不可用或明确失败时，才允许使用旧的富文本逐图上传兜底，并报告原因。

## Obsidian 图片约定

“文章配图粘贴”插件只接管 `data/articles/` 下的正式文章。PPT 中复制的图片粘贴后保存到：

```text
media/images/YYYY-MM-DD-article-文章编号/fig-文章编号-两位序号.png
```

并在 Markdown 中插入项目根目录相对链接。普通附件的兜底目录是 `media/images/article-inbox/`，但正式文章配图不应长期留在该目录。

## 安全边界

- 不点击公众号群发、头条“预览并发布”或任何正式发布动作。
- 不在已打开的其他文章草稿上执行文档导入，避免覆盖无关内容。
- 登录失效、验证码、页面字段变化、图片锚点失效或保存结果不明时立即暂停。
- 不把 AppSecret、Token 或其他凭证写入聊天、文档、日志和 Git。
- 不因重试清除另一个平台已经成功的草稿记录。

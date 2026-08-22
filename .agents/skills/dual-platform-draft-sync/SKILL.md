---
name: dual-platform-draft-sync
description: 将已经在 Obsidian 成稿中插入本地图片的文章，登记配图并同步到微信公众号与今日头条草稿。用户说“图片插好了”“同步双平台草稿”或要求复用双平台发布流程时使用；不负责正式发布。
---

# 双平台草稿同步

把文章 Markdown 视为正文事实源，把其中的本地图片一次登记后分别生成公众号和今日头条草稿。只保存草稿，绝不群发或正式发布。

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
4. 执行：

   ```bash
   python3 scripts/writing_workflow.py sync-dual "<文章路径>"
   ```

5. 保留公众号创建成功的 `media_id`。一个平台失败时，只重试失败平台，不重复创建成功平台草稿。
6. 使用已登录的 Chrome 完成今日头条正文、本地正文图、固定封面和发布选项代填；只保存草稿。
7. 页面显示“草稿已保存”后刷新验证正文、图片、封面和列表；发布选项若被头条刷新重置，则按本地模板重新套用并保留当前页面。
8. 验证无缺图、占位符、双编号、双圆点或残留 `**` 后，运行 `mark-toutiao-saved`。
9. 最终分别报告公众号与今日头条结果，并明确“均未正式发布”。

## Obsidian 图片约定

“文章配图粘贴”插件只接管 `data/articles/` 下的正式文章。PPT 中复制的图片粘贴后保存到：

```text
media/images/YYYY-MM-DD-article-文章编号/fig-文章编号-两位序号.png
```

并在 Markdown 中插入项目根目录相对链接。普通附件的兜底目录是 `media/images/article-inbox/`，但正式文章配图不应长期留在该目录。

## 安全边界

- 不点击公众号群发、头条“预览并发布”或任何正式发布动作。
- 登录失效、验证码、页面字段变化、图片锚点失效或保存结果不明时立即暂停。
- 不把 AppSecret、Token 或其他凭证写入聊天、文档、日志和 Git。
- 不因重试清除另一个平台已经成功的草稿记录。

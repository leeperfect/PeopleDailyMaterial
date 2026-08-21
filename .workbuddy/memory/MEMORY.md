# 项目长期记忆

## 公众号排版偏好（重要，长期有效）

- **排版 skill**：`gzh-design` 已安装到用户级 skills 目录（`~/.workbuddy/skills/gzh-design/`），用于把 Markdown 转成可直接粘贴进微信公众号编辑器的 HTML。
- **主题偏好**：公众号文章排版**统一使用「红白色系」**（用户 2026-08-20 明确指定，长期默认）。
  - 主色 `#DC2626` 正红，组件库 `references/theme-red-white.md`，正文下划线 CSS `border-bottom:2px solid #FECACA;font-weight:600;`。
  - 适用场景：深度分析、观点、力量感话题（经典编辑风）。
- 其它可选主题（仅当用户临时改需求时用）：摸鱼绿（默认，教程/盘点）、石墨极简风、留白禅意风、摸鱼票据风、橄榄手记。
- 校验脚本：`~/.workbuddy/skills/gzh-design/scripts/validate_gzh_html.py <html>`，ERROR 清零 + 半角标点 0 WARN 才交付。

## 公众号拉回后的流程（用户 2026-08-20 明确指定，长期有效，优先于 AGENTS.md 中「重点加粗审查」与「配图缺失时询问」的旧约定）

- **拉回后不再做任何润色或加粗审查**：从得到大脑 `pull` 成功后，跳过 humanizer 一润、重点加粗审查等一切修改动作，直接进入同步公众号草稿箱。
- **配图只认附件**：用户在本轮消息发了 PPT 或图片附件 → 才做配图（register-figures + apply-figures）；没发附件 → 直接同步草稿箱，**不要再追问图片/PPT**。
- 因此后续「拉回」的标准执行是：`pull`（校验通过）→ 有附件则配图 → `publish`（只建草稿不群发）→ 提醒设置原创声明/赞赏/合集。

## 公众号排版正式落地为 gzh-design 红白色系（用户 2026-08-20 明确，长期强制）

- **排版不再用 doocs/md 默认样式**：从得到拉回后的成稿，必须先用 gzh-design「红白色系」转成 HTML，再用这份 HTML 同步到公众号草稿箱。
- 转换脚本（项目内，可复用）：`.local/gzh_redwhite.py <md路径> <输出html路径>`；输出目录 `.local/gzh-out/`。它内置三篇的引言卡金句/导读看点/章节英文标签，后续新文章需在脚本 CONFIG 里按编号补一条配置。
- 校验：`~/.workbuddy/skills/gzh-design/scripts/validate_gzh_html.py <html>` 必须「完全合规」；预览页用 `wrap_preview.py <html>` 生成带「复制」按钮的 `_预览.html`。
- 同步方式：草稿箱 API 推送红白 HTML（`add_draft`，thumb 封面仍用 `people-daily-header.png`，作者 LeePerfect）。注意：旧 doocs 草稿的 media_id 可能已失效（用户会清掉），推送前先确认，失效则用 `add_draft` 新建而非 `update_draft`。

## 环境备注

- 系统 `python3` 缺 PyYAML，运行 `writing_workflow.py` 需用 managed venv `/Users/pf.macbookpro/.workbuddy/binaries/python/envs/default/bin/python`。
- AGENTS.md 提到的 `peopledaily-article-production` Skill 实际不存在，写稿流程按 AGENTS.md 内嵌规则执行。

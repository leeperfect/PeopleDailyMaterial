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

## 双平台同步：今日头条只生成 docx、不再智能体浏览器代填（用户 2026-08-27 明确）

- 公众号端仍走 `sync-dual --platform wechat --wechat-html <红白HTML>` 创建草稿。
- **今日头条端只生成 `.docx`，不做 sync-dual 头条部分、不装 agent-browser、不浏览器代填**：用 `python3 scripts/build_toutiao_import_docx.py <md路径> <out.docx>` 生成即可（≤15 MB、图片嵌入、有序/无序列表用 Word 原生、H1 不进入正文），用户自己在已登录头条的浏览器里点「文档导入」上传。
- 智能体角色止于「生成可手动导入的 Word 文档」，不再接管头条页面操作、登录态、验证码、固定选项套用。

## 转换脚本（`.local/gzh_redwhite.py`）已修过的两个 bug

- **有序列表项之间空行**：项与项之间留空是常见排版习惯，但会让 `parse_blocks` 把每项拆成独立 1 项列表（编号全"1"）。修复：olist 的 while 遇空行且下一行仍是 `^\d+\. ` 时跳过空行继续合并。
- **代码块围栏未闭合吞后续章节**：当作者忘记写闭合 ```，代码块会一直延伸、把 "## 参考文章" 之类的下一章都吞进金句集合。修复：代码块 while 里遇 `## ` 强制 break 且**不**执行末尾 `i += 1`，让主循环能正常处理该 ## 章节。
- 校对应顺手检查：① 有序列表编号是否从 1 开始且每个列表独立重置；② 章节标题 "金句集合 / 参考文章" 是否在 plain_text 中且有 subheading；③ 图片 src 是否与 Markdown 的 `![](...)` 一一对应。

## 环境备注

- 系统 `python3` 缺 PyYAML，运行 `writing_workflow.py` 需用 managed venv `/Users/pf.macbookpro/.workbuddy/binaries/python/envs/default/bin/python`。
- AGENTS.md 提到的 `peopledaily-article-production` Skill 实际不存在，写稿流程按 AGENTS.md 内嵌规则执行。
- 用户公网 IP 频繁变化（一天一变），每次公众号同步都可能需要更新 IP 白名单。建议用户加常用 IP 段或固定代理，否则每次都得改。

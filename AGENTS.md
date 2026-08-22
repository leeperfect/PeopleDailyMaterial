# AI 项目规则

你正在协助一名公务员培训师维护资料型项目。用户不是程序员，所有说明要尽量用“资料、检索、同步、归档、教学输出”的语言解释。

## 项目定位

**人民日报素材库**：抓取人民日报文章，沉淀为本地核心数据库、Obsidian 阅读视图、教研素材卡、公众号成品稿，并按需要同步到 Notion。

本项目的核心原则：

- `raw` 是事实留存，不轻易改。
- `core` 是机器检索和同步合同。
- `vault` 是人看的阅读视图。
- `analysis` 是教研分析和出品过程。
- `articles/人民日报系列` 和 `articles/热点系列` 是两类当前成品稿入口。
- `articles/往期文章` 是已发表文章的人工归档入口，内部按两个系列继续分类。
- `media` 是图片、课件、音视频等本地多媒体资产库，由网盘同步，不进 GitHub。
- Notion 是外部分发视图，不是本地唯一事实源。

## 当前有效结构

- `main.py`：抓取人民日报文章的主入口。
- `modules/`：抓取、解析、处理、Notion 同步、数据库、文章身份等功能模块。
- `scripts/`：重建数据库、查询、Notion 同步、维护重复页等辅助脚本。
- `data/raw/`：原始抓取 JSON，事实留存层。
- `data/processed/`：兼容旧流程的处理结果。
- `data/core/`：SQLite 核心库，稳定文章 ID 和素材资产库。
- `data/vault/`：Obsidian 阅读视图，适合人工浏览和教研标注。
- `data/analysis/`：教研复盘、选题拆解、文案、讲稿、视觉 brief。
- `data/xiaohongshu/`：小红书卡片脚本的集中入口，编号与对应公众号成稿保持一致。
- `data/data_analysis/`：自媒体后台原始数据、拆分明细、每期详细运营报告和长期运营总览，供老师直接查看。
- `data/articles/人民日报系列/`：当前可编辑、待发布的人民日报选题文章。
- `data/articles/热点系列/`：当前可编辑、待发布的热点分析文章。
- `data/articles/往期文章/人民日报系列/`：已发表的人民日报选题文章。
- `data/articles/往期文章/热点系列/`：已发表的热点分析文章。
- `data/articles/文章索引.md`：两个系列及其往期归档的统一查找入口。
- `data/exports/`：JSON/CSV/Notion 等外部同步或分发产物。
- `media/`：小红书图片、公众号配图、课件、视频、音频、压缩包等非文本资产。真实文件不进入 GitHub，只通过网盘同步；GitHub 只保留 `media/_index.md` 索引。
- `docs/`：数据库说明、内容生产流程、项目规范。
- `tests/`：自动检查。

不要把已经清掉的空占位目录当成当前结构重新创建，例如 `data/source/`、`data/index/`、`data/manifests/`、`data/checkpoints/`，除非后续确实有脚本需要它们。

## 数据和同步规则

- 不要把标题当唯一标识。涉及文章去重、同步、更新时，优先使用 `article_id` / `Article ID`。
- Notion 数据库已经有 `Article ID` 字段；同步、补齐、清理重复页时优先围绕这个字段判断。
- 公众号选题统一进入 `data/core/material_assets.sqlite` 的 `content_ideas` 表；面向用户查看的总表是 `data/articles/选题库.md`，由 `scripts/export_content_ideas.py` 生成。
- 公众号要服务日更，筛选选题时允许同一母题拆成多个不同角度和切入点，只要每个切口都有独立表达价值、明确读者收益，并且至少有 3 篇人民日报文章支撑。
- 每次形成新选题前，必须同时参考 `data/data_analysis/overview.md`、最新运营报告和既有选题库：既不能遗漏当下人民日报持续关注的政策热点，也要根据历史阅读、推荐、分享、收藏和长尾表现判断传播潜力。优先采用“考试高频母题 + 明确读者收益 + 纠正常见误区”的表达，但不能只换标题不换切口。
- 以后梳理日报、周报、月报或政经参考补充选题时，一旦形成符合标准的新选题，默认直接写入 `content_ideas` 并刷新 `data/articles/选题库.md` 和 `data/exports/content_ideas.csv`，不再等待用户二次确认。
- 本地 HTML 选题工作台由 `scripts/serve_idea_magazine.py` 启动，读取 `content_ideas`，并把精筛、备注等人工操作写入 `content_idea_notes`。
- 自媒体运营数据统一放在 `data/data_analysis/`。其中原始后台表进 `raw/`，CSV 等拆分结果进 `exports/`，分析结果进 `reports/`，长期数据链更新 `overview.md`。
- 每次用户提供新的自媒体后台数据后，必须生成一份对应批次的详细运营数据分析报告，并与上一批比较；不能只生成导入说明或只做当期孤立分析。
- 每次自媒体数据导入后必须同步更新长期运营总览，连续观察新增日期、新文章、同篇文章长尾、渠道变化和滚动周期趋势。
- 非文本成品默认进入 `media/`，不要继续散放在 `data/analysis/**/deliverables/` 里；分析目录只保留可追溯的文字稿、视觉 brief、讲稿提示和清单。
- 新增小红书图、公众号配图、课件、视频、音频后，要同步补 `media/_index.md`，记录主题、类型、本地路径和网盘位置。
- 不要为了“目录更清爽”删除 `data/raw/`、`data/core/`、`data/vault/`、`data/analysis/`、`data/articles/` 里的有效内容。
- 可以清理的通常是本地缓存、日志、`.DS_Store`、`__pycache__`、虚拟环境、空占位目录。
- `.trae/`、`api/`、`outputs/`、`node_modules/`、`docs/vercel-labsagent.md`、`未命名.base`、`未命名.canvas` 属于疑似旧工具或旧实验文件；删除前要明确取得用户确认。

## 日常常用命令

查询文章：

```bash
python3 scripts/query_articles.py --search 基层治理
python3 scripts/query_articles.py --date 2026-05-27
```

查询教研素材：

```bash
python3 scripts/query_material_assets.py --search 城市治理
python3 scripts/query_material_assets.py --topics
```

刷新公众号选题库：

```bash
python3 scripts/export_content_ideas.py
```

打开本地 HTML 选题工作台：

```bash
python3 idea_magazine.py
```

重建本地核心库：

```bash
python3 scripts/rebuild_article_database.py
```

预览 Notion 清理和补同步：

```bash
python3 scripts/notion_maintenance.py --dry-run
```

执行 Notion 重复页归档和缺失文章补齐：

```bash
python3 scripts/notion_maintenance.py --archive-duplicates --create-missing --delay 0.4
```

同步指定日期到 Notion：

```bash
python3 scripts/sync_to_notion.py 2026-05-27
```

## 写作和资料规则

- 文档使用中文；机器流程、脚本、结构化数据文件名仍使用英文。
- 基于人民日报选题形成的成稿放在 `data/articles/人民日报系列/`，沿用数字编号；下一编号同时核对系列目录文件名和 `data/articles/文章索引.md` 后确定。
- 基于近期公共热点和官媒评论形成的分析稿放在 `data/articles/热点系列/`，使用“热点1、热点2……”独立编号。
- 文章发表后由老师手动移入 `data/articles/往期文章/` 下对应系列，保留原编号，并同步更新 `data/articles/文章索引.md`。
- 做单篇文章教研标注时，优先增量补充，不删旧批注。
- 每次完成文章写作，固定生成四项：公众号成稿、小红书卡片脚本、选题教研复盘、公众号过程稿。小红书卡片脚本集中放入 `data/xiaohongshu/`；教研复盘和公众号过程稿放入 `data/analysis/`；非文本成品放入 `media/`。
- 公众号成稿文末固定先放 `## 金句集合`，再放 `## 参考文章`；金句集中在一个可一次性复制的编号 `text` 代码块中。
- 生成小红书图文、视频号封面、公众号封面等视觉成品时，初稿渲染完成后默认自动完成质量审查；发现溢出、遮挡、密度不足、引用遗漏、尺寸错误或风格不统一时，先修正并复查，再交付给用户预览，不再等待用户额外指令。
- 敏感信息不入 Git，尤其是 `config.json` 中的 Notion Token。
- 不自动提交，除非用户明确要求。
- 以后安排定时采集、同步、提醒或巡检任务时，统一使用 Codex 的“已安排”自动任务；不要再使用 macOS `launchd`、系统日历或其他本机系统级定时任务，除非用户明确要求。

## 公众号写作工作流

- 双平台草稿同步的可复用入口是项目 Skill：`.agents/skills/dual-platform-draft-sync/SKILL.md`。用户说“图片插好了”“Obsidian 配图完成”“同步双平台草稿”或要求其他 Agent 直接走完整同步流程时，必须调用该 Skill，并按 `docs/dual-platform-draft-sync.md` 执行。

- 用户说“写稿”时：按“写稿 → 送去二润”连续执行，不再等待第二条命令。必须先调用 `peopledaily-article-production` Skill，按选题卡读取真实来源、补充 `Codex 教研速读`、建立递进逻辑，并固定生成公众号成稿、小红书卡片脚本、选题教研复盘、公众号过程稿。成稿保存到 `data/articles/人民日报系列/` 或 `data/articles/热点系列/`，小红书卡片脚本保存到 `data/xiaohongshu/`，其余过程文字保存到 `data/analysis/`，同时同步 `data/articles/文章索引.md`。四项产物及来源校验通过后，立即运行 `python3 scripts/writing_workflow.py snapshot "<文章路径>" --stage draft`；再调用 `humanizer-zh` Skill 润色正文，质量评分目标不低于 45/50，且必须保留 YAML、事实、数字、引用、参考文章和教学框架；最后运行 `python3 scripts/writing_workflow.py send "<文章路径>"`，把一润稿送入得到大脑并记录精确 `note_id`。
- 用户单独说“送去二润”或“写完并送去二润”时：继续兼容。若文章尚未形成，完整执行“写稿 → 送去二润”；若已有可审查初稿，则从初稿快照和 Humanizer 一润开始执行，不重复写稿。
- 用户说“拉回”或“我在得到改好了，拉回”时：按“拉回 → 重点加粗审查 → 登记 NotebookLM 配图 → 双平台配图初排 → 打开本地双平台配图工作台”连续执行，并停在本地配图环节；不得在“拉回”阶段创建公众号或今日头条草稿。先根据当前文章运行 `python3 scripts/writing_workflow.py pull "<文章路径>"`，必须使用本地记录的精确 `note_id`；校验不通过时不得覆盖本地稿，也不得继续配图或上传草稿。拉回成功后必须继续审查重点，只在得到版原文上增加 `**加粗**`，不得改写任何文字或结构：
  - 优先突出核心判断、总公式、章节递进结论、申论可用表达、面试答题关键动作和结尾认知升级。
  - 不加粗标题、参考文章、普通事实、整段正文，也不要把每个列表项都加粗；通常保持 8—15 处，按文章长度调整。
  - 完成后运行 `python3 scripts/writing_workflow.py emphasis-check "<文章路径>"`；只有“除加粗标记外正文完全一致”时，状态才进入 `second_polish_complete`。
  - 配图素材定位顺序固定为：本轮消息附件 → 文章已有 `figure_manifest` → `~/Downloads` 中与当前主题相符且最新的 PPTX 和信息图。必须同时确认素材主题与当前文章一致；有多个无法可靠判断的候选时停止并请用户选择，不得猜测。
  - 找到素材后运行 `register-figures`，完成拆图、命名、尺寸检查、清单和审查页；已有且来源未变化的配图清单直接复用，避免重复登记。
  - 运行 `apply-figures --initial --platform shared` 形成两端共用的初始方案，再打开“双平台配图工作台”；工作台默认让公众号和今日头条共用图片、顺序和章节位置，只有确有需要时才设置平台微调。
  - 配图缺失、登记失败或初排校验不通过时，流程停在对应环节并明确说明缺少什么，不得退化为无图草稿。
  - 用户必须在本地工作台查看公众号和今日头条预览并点击“确认配图”；确认后状态进入 `figures_confirmed`。确认前不得运行任何平台同步。
- 用户说“同步双平台草稿”时：先运行 `python3 scripts/writing_workflow.py sync-dual "<文章路径>"`。统一检查得到拉回、重点加粗、配图清单、人工确认和确认后正文/配图是否变化；公众号创建草稿，今日头条生成浏览器交接包。随后必须使用已安装的 Chrome 控制能力，在用户现有登录状态中打开交接包记录的 `creator_url`，填写标题与无图富文本，按 `images` 的顺序及 `before_heading` 上传本地图片，应用已保存的头条选项模板并等待页面显示“草稿已保存”。不得点击正式发布。页面字段、选项、登录状态、验证码或保存结果无法可靠确认时立即暂停并说明原因，不得猜测点击。确认草稿保存成功后运行 `mark-toutiao-saved` 登记结果。
  - 如果用户说明图片已经在 Obsidian/Markdown 中插好，必须先运行 `python3 scripts/writing_workflow.py confirm-inline-figures "<文章路径>"`，登记正文图片、生成清单并确认配图，再运行 `sync-dual`；不得要求用户重复导入图片。
  - 今日头条固定选项为：单图、位置留空、投放广告赚收益、不勾选头条首发、合集“人民日报热点”、勾选同步微头条、作品声明只勾选“取材网络”。固定单图封面为 `media/images/toutiao-fixed-covers/people-daily-cover.jpg`。
  - 头条富文本必须检查有序列表无双编号、无序列表无双圆点、正文无残留 `**`。页面显示“草稿已保存”后刷新验证正文、图片和封面；头条刷新后可能重置发布选项，必须按本地模板重新套用并把页面保留给用户。
  - Obsidian 正式文章配图由“文章配图粘贴”插件保存到 `media/images/YYYY-MM-DD-article-文章编号/fig-文章编号-两位序号.png`，Markdown 使用项目根目录相对链接；默认附件兜底目录 `media/images/article-inbox/` 不作为正式文章配图目录。
  - 今日头条首次同步且尚无选项模板时，在页面上请用户确认一次原创、首发、封面、广告等当前可见选项；用 `save-toutiao-profile --profile-json` 保存页面上的选项名称和值。“只保存草稿、禁止正式发布”是工作流强制安全边界，不作为页面选项保存。
  - 任一平台失败时保留另一平台成功结果，并使用 `sync-dual --platform wechat` 或 `sync-dual --platform toutiao` 单独重试。
- 用户说“预览公众号排版”时：运行 `python3 scripts/writing_workflow.py preview "<文章路径>"`，再用 Codex 内置浏览器打开输出的本地预览页。预览与发布必须使用同一份 doocs/md HTML。
- 用户说“打开完整排版编辑器”时：运行 `python3 scripts/writing_workflow.py editor "<文章路径>"`，使用 Codex 内置浏览器打开本地 doocs/md；不要要求用户打开 IDE。用户在编辑器修改正文后，点击“保存本地排版”会在结构检查通过后自动写回本地 Markdown，同时保留修改前快照；主题、颜色、字号等格式同步保存为该文章的 `wechat_layout`。正文变化会撤销旧的配图确认，必须重新检查并确认配图。结构或来源受损时只保存候选稿，不覆盖源文件。
- 用户说“保存本文排版”时：把完整编辑器中确定的参数保存为该文章的 `wechat_layout` 状态，再重新生成只读预览确认。
- 用户说“同步到公众号草稿箱”时：作为单平台重试口令兼容，但仍必须通过得到拉回、重点加粗和人工配图确认门槛。先检查 `.env` 是否已经安全配置；未配置时启动 `scripts/wechat_setup.py` 本地私密配置页，并一次只引导用户完成一个步骤；不得要求用户把 AppSecret 粘贴到聊天。
- 当前账号无草稿接口权限时，使用 Codex 内置浏览器登录公众号后台代填；若页面变化导致代填失败，打开只读预览页让用户使用“一键复制公众号富文本”兜底。
- 固定作者为 `LeePerfect`。热点系列使用 `media/images/wechat-fixed-covers/hotspot-header.png`；人民日报系列使用 `media/images/wechat-fixed-covers/people-daily-header.png`。
- 公众号草稿默认开启评论，且不限制为仅粉丝评论：`need_open_comment=1`、`only_fans_can_comment=0`。
- 公众号流程只允许创建草稿，不得自动群发。相同正文和排版已建草稿时，不得重复创建，除非用户明确要求。

## Git Commit 规范

提交 Git commit 时必须遵守以下规则：

1. Commit 描述必须使用中文。
2. 禁止使用 feat、fix、docs、style、refactor、perf、test、chore 作为开头。
3. 第一行必须使用格式：`【变更类型】项目或范围：本次同步完成了什么`
4. 变更类型只能使用 `COMMIT_GUIDE.md` 中列出的中文标签。
5. 生成 commit 前必须先阅读 `PROJECT_PROFILE.md` 和 `COMMIT_GUIDE.md`。
6. 如果本次变更涉及 SQLite 数据库、FTS5 索引、Notion 同步、文章 ID，正文必须说明影响。
7. 不要写“修改代码”“更新文件”“调整内容”这类空泛描述。

当前项目的具体规则见：

- `COMMIT_GUIDE.md`
- `PROJECT_PROFILE.md`

# 人民日报素材库

这个项目不是单纯的爬虫文件夹，而是一个面向教研、写作和 AI 检索的资料库。

核心原则是：**目录服务人的阅读，数据库服务机器检索，raw 服务事实留存**。也就是说，平时不要在一堆 JSON 和数据库文件里找内容；人看文章、AI 查资料、Notion 同步，各走各的入口。

## 先看这三个入口

如果你只是想使用素材库，优先看这几个地方：

```text
data/articles/文章索引.md      # 已整理的公众号文章和成品稿
media/_index.md                         # 图片、课件、视频等网盘资产索引
data/vault/_素材库/素材库首页.md          # Obsidian 里的教研素材首页
data/core/articles.sqlite                 # AI、脚本、Notion 同步读取的核心库
```

常用查找方式：

```bash
# 查人民日报原文和文章元数据
python3 scripts/query_articles.py --search 基层治理

# 查教研素材卡、案例、框架、金句、训练题
python3 scripts/query_material_assets.py --search 城市治理

# 按日期查文章
python3 scripts/query_articles.py --date 2026-05-27

# 刷新公众号选题库总表
python3 scripts/export_content_ideas.py

# 打开本地 HTML 选题工作台
python3 scripts/serve_idea_magazine.py
```

## 当前保留的最小结构

```text
PeopleDailyMaterial/
├── README.md                     # 给使用者看的入口说明
├── AGENTS.md                     # 给 AI 助手看的项目规则
├── main.py                       # 抓取人民日报文章的主入口
├── config.json.example           # 配置示例，真实 config.json 不入库
├── modules/                      # 抓取、解析、同步、数据库等功能模块
├── scripts/                      # 重建、查询、同步、维护脚本
├── media/                        # 图片、课件、音视频等本地多媒体资产，网盘同步
├── data/
│   ├── raw/                      # 原始抓取 JSON，事实留存层
│   ├── processed/                # 兼容旧流程的处理结果
│   ├── core/                     # SQLite 核心库和可读备份
│   ├── vault/                    # Obsidian 阅读视图
│   ├── analysis/                 # 教研分析、复盘、文案和视觉 brief
│   ├── articles/                  # 公众号成品层
│   │   ├── 人民日报系列/          # 当前人民日报选题文章
│   │   ├── 热点系列/              # 当前热点分析文章
│   │   ├── 往期文章/              # 已发表文章，内部继续按两个系列分类
│   │   └── 文章索引.md            # 当前与往期文章统一入口
│   └── exports/                  # 给 Notion、表格或外部工具的导出文件
├── docs/                         # 流程说明、数据库说明、内容生产规范
└── tests/                        # 自动检查
```

## 每层分别做什么

`data/raw/` 是事实留存层。它保存原始抓取结果，尽量不人工改动。后面如果分类错了、标题变了、想重新按专题整理，都可以从这里或核心库重新生成。

`data/core/` 是机器检索层。`articles.sqlite` 保存稳定的文章身份、标题、日期、URL、正文等信息；`material_assets.sqlite` 保存教研素材卡。AI、同步脚本、批量查询优先读这里。

`data/vault/` 是人类阅读层。它适合用 Obsidian 打开，按日期、版面、专题浏览，也适合人工做教研标注。

`data/articles/` 是成品层。基于人民日报选题的当前成稿放在 `人民日报系列/`，基于近期公共热点和官媒评论的当前成稿放在 `热点系列/`；已经发表的文章由老师手动移入 `往期文章/` 下的对应系列。

人民日报系列沿用数字编号，热点系列使用“热点1、热点2……”独立编号。两个系列及其往期文章统一通过 `data/articles/文章索引.md` 查找。

其中 `data/articles/选题库.md` 是长期选题池。每次完成文章梳理后，运行 `python3 scripts/export_content_ideas.py` 刷新，就能按月份、季度、状态查看可继续精筛的选题。

`data/analysis/` 是工作过程层。复盘、选题拆解、公众号文案、小红书文案、PPT 讲稿和视觉 brief 放这里。它不是日常找原文的入口。

`media/` 是本地多媒体资产层。小红书图片、公众号配图、课件、视频、音频、压缩包都放这里，并通过网盘同步，不进入 GitHub。GitHub 只保存 `media/_index.md` 这样的文字索引，方便人和 AI 知道资产在哪里。

`data/exports/` 是分发层。CSV、JSON、Notion 辅助同步文件放这里。它可以重新生成，不是唯一事实来源。

## 多媒体资产

以后生成小红书图片、公众号配图、PPTX、视频、音频时，统一放入：

```text
media/images/       # 小红书图、公众号配图、封面图
media/courseware/   # PPTX、Keynote、PDF 课件
media/video/        # 口播、短视频、录屏
media/audio/        # 音频、配音
media/packages/     # 打包交付物
```

推荐用“日期 + 主题 + 用途”命名，例如：

```text
media/images/2026-06-06-new-quality-productivity-xhs/
media/courseware/2026-06-06-new-quality-productivity-class/
```

每生成一组资产，在 `media/_index.md` 里补一行。这样 GitHub 保持轻量，网盘负责同步大文件，本地和 AI 仍然能通过索引找到对应素材。

## Notion 同步

Notion 数据库里已经建立 `Article ID` 后，本地和 Notion 的关系会稳定很多：

- 优先用 `Article ID` 判断同一篇文章，不再只靠标题。
- 标题改名、Markdown 移动、目录重分，都不会影响同步判断。
- 本地有、Notion 没有的文章，可以按核心库批量补齐。
- Notion 里的重复页，可以先预览，再归档。

建议同步前先预览：

```bash
python3 scripts/notion_maintenance.py --dry-run
```

确认无误后再执行：

```bash
python3 scripts/notion_maintenance.py --archive-duplicates --create-missing --delay 0.4
```

只同步某一天文章：

```bash
python3 scripts/sync_to_notion.py 2026-05-27
```

同步一段日期：

```bash
python3 scripts/sync_to_notion.py --start 2026-05-01 --end 2026-05-27
```

## 重建核心库

当你大规模整理 Markdown、补了历史 JSON，或者怀疑数据库和文件不一致时，运行：

```bash
python3 scripts/rebuild_article_database.py
```

它会重新生成：

```text
data/core/articles.sqlite
data/core/articles.jsonl
data/core/rebuild_manifest.json
```

这一步不会改变 Notion；它只是把本地事实层重新整理成 AI 和脚本更容易读取的核心库。

## 刷新选题库

所有公众号选题会先进入 `data/core/material_assets.sqlite` 的 `content_ideas` 表。你平时不用打开数据库，只需要运行：

```bash
python3 scripts/export_content_ideas.py
```

它会生成：

```text
data/articles/选题库.md
data/exports/content_ideas.csv
```

Markdown 表适合直接阅读和挑选，CSV 适合以后按月、季度、年度做热点复盘。

如果你想用网页方式浏览和操作选题，运行：

```bash
python3 idea_magazine.py
```

然后打开：

```text
http://127.0.0.1:8765
```

这个页面会直接读取本地数据库，支持搜索、按优先级/状态筛选、按月份/季度筛选、加入精筛池、调整状态、写个人备注，并同步刷新 Markdown 和 CSV 选题库。原来的 `python3 scripts/serve_idea_magazine.py` 入口也继续可用。

## 抓取新文章

抓取当天文章：

```bash
python3 main.py
```

抓取指定日期：

```bash
python3 main.py --date 2026-05-27
```

抓取后，日常使用优先通过 `data/core/` 查询，通过 `data/vault/` 阅读，不建议直接翻 `data/raw/`。

## 不建议日常打开的地方

这些目录保留是为了稳定流程，不是给人每天翻的：

- `data/raw/`：原始 JSON，作为事实备份。
- `data/processed/`：旧流程兼容数据。
- `data/core/`：数据库文件，交给脚本和 AI 使用。
- `data/exports/`：同步和导出产物。
- `media/` 里的真实大文件：由网盘同步，GitHub 只保留索引。

这次已经清理掉本地缓存、日志、虚拟环境、空的占位目录和系统临时文件。还有一些疑似旧工具目录或旧实验文件仍然留着，等你确认后再删：`.trae/`、`api/`、`outputs/`、`node_modules/`、`docs/vercel-labsagent.md`、`未命名.base`、`未命名.canvas`。

## 配置提醒

真实配置文件是 `config.json`，里面可能包含 Notion Token，不要提交到 Git。项目里只保留 `config.json.example` 作为示例。

详细数据库说明见 [docs/database.md](docs/database.md)。

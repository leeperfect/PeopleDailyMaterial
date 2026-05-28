# 人民日报素材库

这个项目不是单纯的爬虫文件夹，而是一个面向教研、写作和 AI 检索的资料库。

核心原则是：**目录服务人的阅读，数据库服务机器检索，raw 服务事实留存**。也就是说，平时不要在一堆 JSON 和数据库文件里找内容；人看文章、AI 查资料、Notion 同步，各走各的入口。

## 先看这三个入口

如果你只是想使用素材库，优先看这几个地方：

```text
data/articles/公众号文章/文章索引.md      # 已整理的公众号文章和成品稿
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
├── data/
│   ├── raw/                      # 原始抓取 JSON，事实留存层
│   ├── processed/                # 兼容旧流程的处理结果
│   ├── core/                     # SQLite 核心库和可读备份
│   ├── vault/                    # Obsidian 阅读视图
│   ├── analysis/                 # 教研分析、复盘、出品包
│   ├── articles/公众号文章/       # 成品公众号文章
│   └── exports/                  # 给 Notion、表格或外部工具的导出文件
├── docs/                         # 流程说明、数据库说明、内容生产规范
└── tests/                        # 自动检查
```

## 每层分别做什么

`data/raw/` 是事实留存层。它保存原始抓取结果，尽量不人工改动。后面如果分类错了、标题变了、想重新按专题整理，都可以从这里或核心库重新生成。

`data/core/` 是机器检索层。`articles.sqlite` 保存稳定的文章身份、标题、日期、URL、正文等信息；`material_assets.sqlite` 保存教研素材卡。AI、同步脚本、批量查询优先读这里。

`data/vault/` 是人类阅读层。它适合用 Obsidian 打开，按日期、版面、专题浏览，也适合人工做教研标注。

`data/articles/公众号文章/` 是成品层。公众号稿、插图版、面向老师直接使用的文章，都放这里，文件名可以用中文标题。

`data/analysis/` 是工作过程层。复盘、选题拆解、PPT 文案、跨平台出品包放这里。它不是日常找原文的入口。

`data/exports/` 是分发层。CSV、JSON、Notion 辅助同步文件放这里。它可以重新生成，不是唯一事实来源。

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

这次已经清理掉本地缓存、日志、虚拟环境、空的占位目录和系统临时文件。还有一些疑似旧工具目录或旧实验文件仍然留着，等你确认后再删：`.trae/`、`api/`、`outputs/`、`node_modules/`、`docs/vercel-labsagent.md`、`未命名.base`、`未命名.canvas`。

## 配置提醒

真实配置文件是 `config.json`，里面可能包含 Notion Token，不要提交到 Git。项目里只保留 `config.json.example` 作为示例。

详细数据库说明见 [docs/database.md](docs/database.md)。

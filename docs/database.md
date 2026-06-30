# 人民日报素材核心库使用说明

## 当前结构

这个项目现在采用“事实留存层 + 机器检索层 + 人类阅读层 + 输出层”的结构：

```text
data/
  core/
    articles.sqlite          # 核心 SQLite 数据库
    articles.jsonl           # 可读备份，适合 AI 批量读取
    material_assets.sqlite    # 教研素材资产库
    rebuild_manifest.json    # 最近一次重建摘要
  raw/                       # 原始 JSON，事实留存层
  processed/                 # 旧处理结果，保留兼容
  vault/                     # 人类阅读视图，继续给 Obsidian 使用
  analysis/                  # 教研分析、复盘、出品过程
  articles/                   # 两类公众号成稿、往期归档和统一索引
  exports/                   # 对外导出和同步辅助文件
media/                       # 图片、课件、音视频等本地多媒体资产，网盘同步
```

核心原则：

- `data/core/articles.sqlite` 是程序和 AI 优先读取的事实索引层。
- `data/core/material_assets.sqlite` 是案例、框架、金句、题目等教研素材资产库。
- `data/vault` 是人看的阅读视图，可以按日期、专题、系列继续整理。
- `data/raw` 是原始数据留存层，保证重建和追溯能力。
- `data/articles/人民日报系列` 是人民日报选题当前成稿入口，沿用数字编号。
- `data/articles/热点系列` 是热点分析当前成稿入口，使用“热点+数字”独立编号。
- `data/articles/往期文章` 按两个系列保存老师手动归档的已发表文章。
- `data/articles/文章索引.md` 是当前成稿和往期文章的统一查找入口。
- `media` 是非文本资产层，保存小红书图、公众号配图、课件、视频、音频和打包文件。它不参与核心库重建，不进入 GitHub，只通过 `media/_index.md` 保留可检索线索。

之前预留过的 `data/source/`、`data/index/`、`data/manifests/`、`data/checkpoints/` 已不作为日常常驻目录保留；如果未来确实接入单独向量库或外部索引，再由对应脚本生成。

## 重建数据库

当你整理了旧 Markdown、补了历史 JSON，或者怀疑数据库和文件不一致时，运行：

```bash
python3 scripts/rebuild_article_database.py
```

它会读取：

- `data/raw/articles_YYYYMMDD.json`
- `data/vault/YYYY/MM/YYYY-MM-DD/.../*.md`

然后重建：

- `data/core/articles.sqlite`
- `data/core/articles.jsonl`
- `data/core/rebuild_manifest.json`

## 查询文章

按日期查：

```bash
python3 scripts/query_articles.py --date 2026-05-16
```

按关键词查：

```bash
python3 scripts/query_articles.py --search 基层治理
```

按日期范围查：

```bash
python3 scripts/query_articles.py --start 2026-05-01 --end 2026-05-16 --limit 50
```

## 查询教研素材

按关键词查素材卡：

```bash
python3 scripts/query_material_assets.py --search 城市治理
```

查看专题分布：

```bash
python3 scripts/query_material_assets.py --topics
```

查看公众号选题或训练题：

```bash
python3 scripts/query_material_assets.py --ideas
python3 scripts/query_material_assets.py --questions
```

把公众号选题导出成长期总表：

```bash
python3 scripts/export_content_ideas.py
```

默认生成：

```text
data/articles/选题库.md
data/exports/content_ideas.csv
```

`选题库.md` 给人工挑选，`content_ideas.csv` 给后续按月、季度、年度做热点复盘。

本地 HTML 选题工作台：

```bash
python3 idea_magazine.py
```

默认地址：

```text
http://127.0.0.1:8765
```

工作台读取 `content_ideas`，并把人工精筛和备注写入 `content_idea_notes`。这样选题本身仍在核心库里，人的判断也能长期保存。原来的 `python3 scripts/serve_idea_magazine.py` 入口继续可用。

APP 评论热点选题工作台：

```bash
python3 hotspot_magazine.py
```

默认地址是 `http://127.0.0.1:8766`。页面读取
`data/peopleapp_opinion/core/hotspot_topics.sqlite`，可按热点状态、优先级、媒体来源和人工精筛状态挑选话题。选题带有教研分类和核心角度；统计会排除同源同标题重复稿以及正文不足 200 字的残缺稿。精筛结果和个人备注直接保存在热点总库中，每日更新热点时会保留。

## 抓取新文章

原来的抓取方式继续可用：

```bash
python3 main.py --date 2026-05-16 --all
```

新抓取的文章仍会写入旧 JSON、Markdown 和新的 SQLite 核心库。也就是说，日常抓取后一般不需要手动重建；只有做大规模整理或迁移时再运行重建脚本。

## 同步到 Notion

默认从新核心库读取：

```bash
python3 scripts/sync_to_notion.py 2026-05-16
```

同步多个日期：

```bash
python3 scripts/sync_to_notion.py 2026-05-15 2026-05-16
```

如果要强制使用旧 JSON：

```bash
python3 scripts/sync_to_notion.py --from-raw 2026-05-16
```

如果 Notion 已有文章但你想覆盖更新：

```bash
python3 scripts/sync_to_notion.py --update-existing 2026-05-16
```

Notion 数据库中已经建立 `Article ID` 字段。同步脚本会优先用这个字段去重；如果遇到历史页面没有 `Article ID`，再降级用 URL、标题和日期判断。

清理重复页和补齐缺失文章时，先预览：

```bash
python3 scripts/notion_maintenance.py --dry-run
```

确认后再执行：

```bash
python3 scripts/notion_maintenance.py --archive-duplicates --create-missing --delay 0.4
```

## 核心 ID 规则

每篇文章都会生成稳定的 `article_id`，例如：

```text
people_daily_20260516_30157233
```

含义：

- `people_daily`：来源
- `20260516`：发布日期
- `30157233`：人民日报 URL 中的 content id

以后目录改名、Markdown 移动、专题重分，都不影响这个 ID。

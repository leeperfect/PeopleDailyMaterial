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
  articles/公众号文章/        # 公众号文章和成品稿
  exports/                   # 对外导出和同步辅助文件
```

核心原则：

- `data/core/articles.sqlite` 是程序和 AI 优先读取的事实索引层。
- `data/core/material_assets.sqlite` 是案例、框架、金句、题目等教研素材资产库。
- `data/vault` 是人看的阅读视图，可以按日期、专题、系列继续整理。
- `data/raw` 是原始数据留存层，保证重建和追溯能力。
- `data/articles/公众号文章` 是面向老师和运营使用的成品稿入口。

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

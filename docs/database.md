# 人民日报素材核心库使用说明

## 当前结构

这个项目现在采用“事实层 + 检索层 + 阅读视图层”的结构：

```text
data/
  core/
    articles.sqlite          # 核心 SQLite 数据库
    articles.jsonl           # 可读备份，适合 AI 批量读取
    rebuild_manifest.json    # 最近一次重建摘要
  source/
    people_daily/
      raw_articles/          # 预留：新版原始文章归档
      raw_html/              # 预留：原始网页证据
  index/
    fts/                     # 预留：全文索引文件
    vector/                  # 预留：向量索引文件
  vault/                     # 人类阅读视图，继续给 Obsidian 使用
  raw/                       # 旧 JSON 格式，保留兼容
  processed/                 # 旧处理结果，保留兼容
  exports/                   # 对外导出
```

核心原则：

- `data/core/articles.sqlite` 是程序和 AI 优先读取的事实索引层。
- `data/vault` 是人看的阅读视图，可以按日期、专题、系列继续整理。
- `data/raw` 暂时保留，保证旧脚本和历史数据不被破坏。

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

建议在 Notion 数据库中新增一个 `Article ID` 字段，类型用 `Text` / `Rich text`。同步脚本会优先用这个字段去重；如果暂时没加，脚本会自动降级为 URL、标题和日期去重。

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

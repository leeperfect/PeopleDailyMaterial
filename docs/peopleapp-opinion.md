# 人民日报 APP 评论库

这是一个独立资料库，用来采集人民日报 APP 网页端“评论/锐评”频道。它不进入原有人民日报电子报库，也不复用原来的 Notion 文章数据库。

## 本地资料层

- `data/peopleapp_opinion/raw/`：接口原始数据，作为事实留存。
- `data/peopleapp_opinion/core/articles.sqlite`：APP 评论库核心检索库。
- `data/peopleapp_opinion/vault/`：人工阅读版 Markdown。
- `data/peopleapp_opinion/exports/`：采集报告、同步报告、CSV/JSON 留档。
- `data/peopleapp_opinion/exports/run_logs/`：每日自动任务日志。

稳定文章 ID 格式：

```text
peopleapp_opinion_YYYYMMDD_{contentId}_{relId}
```

## 日常采集

默认回看最近 3 天，补齐漏采：

```bash
python3 scripts/crawl_peopleapp_opinion.py
```

采集指定链接：

```bash
python3 scripts/crawl_peopleapp_opinion.py --url https://www.peopleapp.com/column/30052476000-500007564442
```

只预览不写入：

```bash
python3 scripts/crawl_peopleapp_opinion.py --dry-run
```

## 本地查询

查询“停车计费”：

```bash
python3 scripts/query_peopleapp_opinion.py --search 停车计费
```

查看库概况：

```bash
python3 scripts/query_peopleapp_opinion.py --stats
```

## Notion 独立数据库

创建新的 Notion 数据库：

```bash
python3 scripts/create_peopleapp_opinion_notion_database.py
```

脚本会把新数据库 ID 写入：

```text
notion.peopleapp_opinion_database_id
```

如果数据库已经手工创建好，也可以只登记：

```bash
python3 scripts/create_peopleapp_opinion_notion_database.py --database-id <你的数据库ID>
```

同步最近 3 天到独立 Notion 评论库：

```bash
python3 scripts/sync_peopleapp_opinion_to_notion.py
```

只预览同步动作：

```bash
python3 scripts/sync_peopleapp_opinion_to_notion.py --dry-run
```

## 每天 9 点自动运行

自动任务统一放在 Codex 的“已安排”里管理，不再使用 macOS `launchd`。

手动执行一次完整每日任务：

```bash
python3 scripts/run_peopleapp_opinion_daily.py
```

自动任务执行后，日志会写入：

```text
data/peopleapp_opinion/exports/run_logs/
```

每日任务会按顺序完成三件事：

- 采集最近 3 天评论文章。
- 同步到独立 Notion 评论库。
- 更新官媒热点选题总库。

## 官媒热点梳理

默认标准：同一事件或明确母题下，至少 3 个不同来源媒体发表评论，视为热点。

选题归并先读取本地已下载正文，再使用经过人工复核的明确事件词和观点链判断。
不再用“中国”“消费者”“军事”等泛词直接聚类，未形成共同议题的文章不强行归类。
同来源、同标题的重复稿只计算一次，正文不足 200 字的跳转页或残缺稿不作为支撑。

导出最近 7 天热点：

```bash
python3 scripts/export_peopleapp_opinion_hotspots.py
```

导出全部 APP 评论库热点：

```bash
python3 scripts/export_peopleapp_opinion_hotspots.py --all
```

报告保存到：

```text
data/peopleapp_opinion/exports/hotspots/
```

## 热点选题总库

热点选题总库用于长期累计统计。每天新增文章后，脚本会重新扫描 APP 评论库全部文章，持续更新同一批热点的媒体数、文章数和时间范围。

选题分为三种状态：

- `热点`：至少 3 个不同来源媒体共同评论。
- `候选`：2 个不同来源媒体共同评论。
- `专题`：同一来源连续发表多篇、逻辑链完整，但不计作多来源热点。

每个选题另有教研分类和核心角度，便于按教育、数字治理、城市治理、公共安全、产业经济、网络生态、体育文化、国际观察等方向筛选。

更新总库：

```bash
python3 scripts/update_peopleapp_opinion_topic_library.py --all
```

机器统计库：

```text
data/peopleapp_opinion/core/hotspot_topics.sqlite
```

人工复制版选题库：

```text
data/peopleapp_opinion/hotspot_topic_library.md
```

表格导出版：

```text
data/peopleapp_opinion/exports/hotspot_topic_library.csv
```

`hotspot_topic_library.md` 里有“AI 分析材料”代码块，可以直接复制给 AI，让它写热点分析、申论素材拆解、面试答题框架或公众号选题。

## 验收口径

- APP 评论文章只出现在 `data/peopleapp_opinion/core/articles.sqlite`。
- 原人民日报库 `data/core/articles.sqlite` 不新增 `peopleapp_opinion_` 开头的文章。
- Notion 同步只写入 `notion.peopleapp_opinion_database_id` 指向的新数据库。
- 自动任务日志要能看到采集数量、跳过重复数量、同步数量和失败清单。
- 热点报告中，`已达热点标准` 的话题至少包含 3 个不同来源媒体；重复稿和残缺正文不参与支撑数量。
- 热点选题总库每天自动更新，保留历史文章参与累计统计。

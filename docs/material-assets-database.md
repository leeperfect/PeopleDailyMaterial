# 人民日报教研素材资产库说明

这份说明用于解释 `data/core/material_assets.sqlite` 的用途。它不替代原文库 `data/core/articles.sqlite`，而是在原文事实层之上，新增一层“教研转译层”。

## 一、为什么要有这个库

如果每天只生成一篇复盘文档，后续会遇到三个问题：

1. 想找某个主题时，还要重新翻多篇文档。
2. 一个好案例很难同时用于申论、面试、公众号。
3. 每天的整理结果彼此割裂，无法观察热点趋势。

所以现在把整理结果拆成结构化素材卡，沉淀到 `material_assets.sqlite`。

## 二、它和原有资料层的关系

```text
data/vault/
  人民日报原文，适合人阅读

data/core/articles.sqlite
  文章事实库，保存 article_id、标题、日期、版面、正文、来源链接

data/core/material_assets.sqlite
  教研素材库，保存文章判断、素材卡、专题、公众号选题、面试题

data/analysis/YYYY-MM-DD/
  每日结构化 JSON 和可读 Markdown 视图
```

核心原则：

- 原文事实仍以 `articles.sqlite` 为准。
- 教研判断、申论转译、面试题、公众号选题进入 `material_assets.sqlite`。
- `data/analysis/YYYY-MM-DD/*-material-assets.json` 是可重建数据库的结构化来源。
- Markdown 视图只是方便阅读，不是唯一资产。

## 三、目前的核心表

| 表 | 用途 |
|---|---|
| `article_analysis` | 每篇文章的教研判断：等级、一句话判断、申论/面试/公众号用途、复用提醒 |
| `material_cards` | 最小可复用素材卡：案例、框架、对策、观点、面试题、公众号选题、风险提醒 |
| `topics` | 稳定专题，如城市治理、稳就业、AI治理、绿色转型 |
| `card_topic_links` | 一张素材卡可以挂多个专题 |
| `daily_reviews` | 每日总判断和主线 |
| `content_ideas` | 公众号选题池 |
| `exam_questions` | 面试与申论训练题库 |

## 四、2026-05-17 试点结果

试点来源：

```text
data/vault/2026/05/2026-05-17
```

已生成：

```text
data/analysis/2026-05-17/2026-05-17-material-assets.json
data/analysis/2026-05-17/2026-05-17-material-assets-view.md
data/core/material_assets.sqlite
```

本次沉淀：

- 13 篇文章教研判断
- 28 张素材卡
- 9 个专题
- 5 个公众号选题
- 6 道训练题

## 五、日常使用方式

查看某天专题分布：

```bash
python3 scripts/query_material_assets.py --date 2026-05-17 --topics
```

查看某天某个专题的素材卡：

```bash
python3 scripts/query_material_assets.py --date 2026-05-17 --topic 城市治理
```

搜索关键词：

```bash
python3 scripts/query_material_assets.py --search AI
```

查看公众号选题池：

```bash
python3 scripts/query_material_assets.py --date 2026-05-17 --ideas
```

查看训练题：

```bash
python3 scripts/query_material_assets.py --date 2026-05-17 --questions
```

## 六、以后每天怎么跑

建议每天按这个顺序：

1. 先抓取当天人民日报文章，进入 `data/vault` 和 `articles.sqlite`。
2. 让 AI 读取当天文章，生成 `YYYY-MM-DD-material-assets.json`。
3. 运行导入脚本：

```bash
python3 scripts/import_material_assets.py data/analysis/YYYY-MM-DD/YYYY-MM-DD-material-assets.json
```

4. 自动得到：

- `data/core/material_assets.sqlite` 中的新素材卡
- `data/analysis/YYYY-MM-DD/YYYY-MM-DD-material-assets-view.md` 可读视图

这样每天新增文章后，不只是多一篇复盘，而是多一批可检索、可组合、可再加工的素材资产。


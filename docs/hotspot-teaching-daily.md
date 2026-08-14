# 热点教学日报使用说明

## 一、这个工具解决什么问题

热点教学日报不是文章目录，而是“当天拿来就能补充课堂”的教研入口。每个热点先给出 3 分钟速讲，再提供 10—15 分钟展开，包括事实、观点比较、分析框架、规范表达、案例误区、互动问题和来源依据。

页面采用三栏结构：左侧是稳定功能，中间是日报、周报和主题档案，右侧是当天教学内容。手机端会自动收起左右栏。

## 二、资料如何融合

- 人民日报 APP 评论：热点信号、媒体观点、争议观察。
- 《人民日报》正式版：政策依据、治理案例、规范表达、长期母题。
- APP 热点归并来自现有人工复核结果。
- 正式版文章按显著主题词检索，自动关联默认仍需人工审核。
- 没有可靠支撑时明确显示“暂未发现”，不做强行关联。

两个原始资料库始终只读。新工具只写入 `data/hotspot_teaching/`，不会改动原始文章和既有热点归并。

## 三、日常使用

每天完成两类文章采集后，运行：

```bash
python3 scripts/build_hotspot_teaching_daily.py
```

打开本地网页：

```bash
python3 hotspot_teaching_daily.py
```

默认地址为 `http://127.0.0.1:8767`。页面中的教学卡在人工确认前会显示“教研预览”。

列出全部教学卡：

```bash
python3 scripts/review_hotspot_teaching_card.py
```

确认某张教学卡：

```bash
python3 scripts/review_hotspot_teaching_card.py --topic-id "热点编号" --status reviewed --note "事实与来源已核对"
```

正式发布某张教学卡：

```bash
python3 scripts/review_hotspot_teaching_card.py --topic-id "热点编号" --status published --note "教研负责人确认"
```

只有同一期的全部教学卡都已发布，该期日报或周报才会显示为正式发布。

## 四、迁移与恢复

`data/hotspot_teaching/exports/` 固定生成：

- `hotspot_topics.jsonl`
- `source_articles.jsonl`
- `topic_article_links.csv`
- `teaching_cards.jsonl`
- `daily_editions.jsonl`
- `weekly_editions.jsonl`
- `manifest.json`
- `hotspot_teaching.sqlite`

`manifest.json` 记录生成时间、数量和完整性校验值。`data/hotspot_teaching/site/` 是可直接重新发布的静态网站副本。只要本地项目、迁移文件和网页源码仍由个人掌握，即使公司妙搭应用停用，也能在其他平台恢复。

## 五、妙搭的边界

一期妙搭应用不保存教师账号、个人笔记、行为数据或唯一资料，只展示最近一次审核并导出的静态副本。资料更新后重新生成并发布即可。后续如需在线审核或多人协作，再连接个人掌握的主库；届时仍以稳定热点编号和文章编号为迁移合同。

当前妙搭应用编号、访问地址和发布目录记录在 `data/hotspot_teaching/miaoda_deployment.json`。重新生成资料后，继续使用同一应用编号发布 `data/hotspot_teaching/site/`，不必重复创建应用。

## 六、当前状态说明

首批自动生成的教学卡用于验证页面和教学结构，状态统一为“教研预览”。其中重要事实、自动匹配的《人民日报》文章和教学表达仍须教师逐条确认，未经确认不能当作正式日报对外使用。

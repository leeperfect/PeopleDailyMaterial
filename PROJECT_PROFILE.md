---
title: "项目档案"
updated: 2026-06-06
---

# 项目档案

项目名称：PeopleDailyMaterial
项目类型：人民日报文章素材库 + 教研内容库 + Notion 同步视图
主要用途：自动化抓取人民日报网页版文章，存入本地 SQLite 核心库，沉淀 Obsidian 阅读视图、教研素材卡和公众号成品稿，并按需要同步到 Notion，为申论教学提供时政素材支撑

事实留存层：`data/raw/` 原始抓取数据
机器检索层：`data/core/` SQLite 核心库（稳定文章 ID、全文检索、教研素材资产库）
人类阅读层：`data/vault/` Obsidian 格式文章 Markdown + `data/articles/公众号文章/` 成品稿
过程分析层：`data/analysis/` 教研复盘、选题拆解、文案、讲稿、视觉 brief
本地媒体层：`media/` 小红书图片、公众号配图、课件、视频、音频、压缩包，由网盘同步，不进入 GitHub
外部分发层：`data/exports/` JSON/CSV 导出 + Notion 数据库视图
外部同步对象：Notion 数据库、GitHub 仓库、网盘多媒体目录

## Commit 优先标签

1. 【资料新增】— 新增抓取的人民日报文章原文
2. 【结构调整】— 调整 SQLite 核心库结构、稳定文章 ID、raw/core/vault/articles 分层
3. 【同步发布】— 刷新 Notion 同步字段、修正同步状态
4. 【检索优化】— 重建 FTS5 索引、更新关键词提取与分类
5. 【采集更新】— 修正爬虫逻辑、更新抓取策略、补采缺失日期

## 本项目 commit 描述必须强调

- 本次涉及哪些日期的文章数据变化
- 是否涉及 SQLite 数据库结构或文章 ID 变动
- 是否涉及 Notion 同步状态或字段更新
- 是否涉及 `media/` 多媒体索引或 GitHub 忽略规则
- 是否涉及爬虫脚本或采集流程的修改

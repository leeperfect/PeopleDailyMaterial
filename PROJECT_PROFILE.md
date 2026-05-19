---
title: "项目档案"
updated: 2026-05-19
---

# 项目档案

项目名称：PeopleDailyMaterial
项目类型：人民日报文章素材库 + Notion 同步视图
主要用途：自动化抓取人民日报网页版文章，存入本地 SQLite 核心库，同步到 Notion 数据库，为申论教学提供时政素材支撑

核心资料层：`data/core/` SQLite 数据库（稳定文章 ID 事实层）+ `data/raw/` 原始抓取数据
人类阅读层：`data/vault/` Obsidian 格式的文章 Markdown + Notion 数据库视图
机器检索层：`data/index/` SQLite FTS5 全文检索索引 + `data/exports/` JSON/CSV 导出
外部同步对象：Notion 数据库、GitHub 仓库

## Commit 优先标签

1. 【资料新增】— 新增抓取的人民日报文章原文
2. 【结构调整】— 调整 SQLite 核心库结构、稳定文章 ID、raw/core/index 分层
3. 【同步发布】— 刷新 Notion 同步字段、修正同步状态
4. 【检索优化】— 重建 FTS5 索引、更新关键词提取与分类
5. 【采集更新】— 修正爬虫逻辑、更新抓取策略、补采缺失日期

## 本项目 commit 描述必须强调

- 本次涉及哪些日期的文章数据变化
- 是否涉及 SQLite 数据库结构或文章 ID 变动
- 是否涉及 Notion 同步状态或字段更新
- 是否涉及爬虫脚本或采集流程的修改

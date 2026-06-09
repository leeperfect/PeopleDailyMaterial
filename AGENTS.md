# AI 项目规则

你正在协助一名公务员培训师维护资料型项目。用户不是程序员，所有说明要尽量用“资料、检索、同步、归档、教学输出”的语言解释。

## 项目定位

**人民日报素材库**：抓取人民日报文章，沉淀为本地核心数据库、Obsidian 阅读视图、教研素材卡、公众号成品稿，并按需要同步到 Notion。

本项目的核心原则：

- `raw` 是事实留存，不轻易改。
- `core` 是机器检索和同步合同。
- `vault` 是人看的阅读视图。
- `analysis` 是教研分析和出品过程。
- `articles/公众号文章` 是成品稿入口。
- `media` 是图片、课件、音视频等本地多媒体资产库，由网盘同步，不进 GitHub。
- Notion 是外部分发视图，不是本地唯一事实源。

## 当前有效结构

- `main.py`：抓取人民日报文章的主入口。
- `modules/`：抓取、解析、处理、Notion 同步、数据库、文章身份等功能模块。
- `scripts/`：重建数据库、查询、Notion 同步、维护重复页等辅助脚本。
- `data/raw/`：原始抓取 JSON，事实留存层。
- `data/processed/`：兼容旧流程的处理结果。
- `data/core/`：SQLite 核心库，稳定文章 ID 和素材资产库。
- `data/vault/`：Obsidian 阅读视图，适合人工浏览和教研标注。
- `data/analysis/`：教研复盘、选题拆解、文案、讲稿、视觉 brief。
- `data/articles/公众号文章/`：公众号文章、成品稿、面向老师人工查找的文章。
- `data/exports/`：JSON/CSV/Notion 等外部同步或分发产物。
- `media/`：小红书图片、公众号配图、课件、视频、音频、压缩包等非文本资产。真实文件不进入 GitHub，只通过网盘同步；GitHub 只保留 `media/_index.md` 索引。
- `docs/`：数据库说明、内容生产流程、项目规范。
- `tests/`：自动检查。

不要把已经清掉的空占位目录当成当前结构重新创建，例如 `data/source/`、`data/index/`、`data/manifests/`、`data/checkpoints/`，除非后续确实有脚本需要它们。

## 数据和同步规则

- 不要把标题当唯一标识。涉及文章去重、同步、更新时，优先使用 `article_id` / `Article ID`。
- Notion 数据库已经有 `Article ID` 字段；同步、补齐、清理重复页时优先围绕这个字段判断。
- 公众号选题统一进入 `data/core/material_assets.sqlite` 的 `content_ideas` 表；面向用户查看的总表是 `data/articles/公众号文章/选题库.md`，由 `scripts/export_content_ideas.py` 生成。
- 本地 HTML 选题工作台由 `scripts/serve_idea_magazine.py` 启动，读取 `content_ideas`，并把精筛、备注等人工操作写入 `content_idea_notes`。
- 非文本成品默认进入 `media/`，不要继续散放在 `data/analysis/**/deliverables/` 里；分析目录只保留可追溯的文字稿、视觉 brief、讲稿提示和清单。
- 新增小红书图、公众号配图、课件、视频、音频后，要同步补 `media/_index.md`，记录主题、类型、本地路径和网盘位置。
- 不要为了“目录更清爽”删除 `data/raw/`、`data/core/`、`data/vault/`、`data/analysis/`、`data/articles/` 里的有效内容。
- 可以清理的通常是本地缓存、日志、`.DS_Store`、`__pycache__`、虚拟环境、空占位目录。
- `.trae/`、`api/`、`outputs/`、`node_modules/`、`docs/vercel-labsagent.md`、`未命名.base`、`未命名.canvas` 属于疑似旧工具或旧实验文件；删除前要明确取得用户确认。

## 日常常用命令

查询文章：

```bash
python3 scripts/query_articles.py --search 基层治理
python3 scripts/query_articles.py --date 2026-05-27
```

查询教研素材：

```bash
python3 scripts/query_material_assets.py --search 城市治理
python3 scripts/query_material_assets.py --topics
```

刷新公众号选题库：

```bash
python3 scripts/export_content_ideas.py
```

打开本地 HTML 选题工作台：

```bash
python3 idea_magazine.py
```

重建本地核心库：

```bash
python3 scripts/rebuild_article_database.py
```

预览 Notion 清理和补同步：

```bash
python3 scripts/notion_maintenance.py --dry-run
```

执行 Notion 重复页归档和缺失文章补齐：

```bash
python3 scripts/notion_maintenance.py --archive-duplicates --create-missing --delay 0.4
```

同步指定日期到 Notion：

```bash
python3 scripts/sync_to_notion.py 2026-05-27
```

## 写作和资料规则

- 文档使用中文；机器流程、脚本、结构化数据文件名仍使用英文。
- 公众号文章、成品稿、面向老师人工查找的文章文件，统一放在 `data/articles/公众号文章/`，文件名优先使用中文标题。
- 做单篇文章教研标注时，优先增量补充，不删旧批注。
- 如果要写公众号、小红书、PPT、视觉 brief，默认按“教学可用 + 运营可用”的完整出品包理解；文字过程入 `data/analysis/`，非文本成品入 `media/`。
- 敏感信息不入 Git，尤其是 `config.json` 中的 Notion Token。
- 不自动提交，除非用户明确要求。

## Git Commit 规范

提交 Git commit 时必须遵守以下规则：

1. Commit 描述必须使用中文。
2. 禁止使用 feat、fix、docs、style、refactor、perf、test、chore 作为开头。
3. 第一行必须使用格式：`【变更类型】项目或范围：本次同步完成了什么`
4. 变更类型只能使用 `COMMIT_GUIDE.md` 中列出的中文标签。
5. 生成 commit 前必须先阅读 `PROJECT_PROFILE.md` 和 `COMMIT_GUIDE.md`。
6. 如果本次变更涉及 SQLite 数据库、FTS5 索引、Notion 同步、文章 ID，正文必须说明影响。
7. 不要写“修改代码”“更新文件”“调整内容”这类空泛描述。

当前项目的具体规则见：

- `COMMIT_GUIDE.md`
- `PROJECT_PROFILE.md`

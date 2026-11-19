# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目定位

人民日报素材库：自动抓取人民日报网页版文章，沉淀为本地 SQLite 核心库、Obsidian 阅读视图、教研素材卡、公众号成品稿，并按需同步到 Notion。用户是公务员培训师，面向申论教学提供时政素材支撑。

完整项目规则见 `AGENTS.md`，commit 规范见 `COMMIT_GUIDE.md`，项目档案见 `PROJECT_PROFILE.md`。

## 数据分层架构

项目核心是六层数据结构，每层服务不同用途：

- **raw** (`data/raw/`)：原始抓取 JSON，事实留存，不人工改动
- **core** (`data/core/`)：SQLite 核心库，稳定 `article_id` 作为唯一标识，服务机器检索和 Notion 同步
- **vault** (`data/vault/`)：Obsidian 阅读视图，按日期/版面/专题组织，适合人工浏览和教研标注
- **analysis** (`data/analysis/`)：教研复盘、选题拆解、跨平台出品包
- **articles** (`data/articles/人民日报系列/`、`data/articles/热点系列/`、`data/articles/申论方法系列/`)：三类公众号成品稿入口，已发表文章进入对应往期目录
- **exports** (`data/exports/`)：JSON/CSV/Notion 导出产物，可重新生成

数据流向：`main.py` 抓取 → `raw` → `modules/processor.py` 文本清洗 → `core`（SQLite 入库）+ `vault`（Obsidian 视图）→ `exports`/Notion。`articles` 成稿是写稿工作流的产物，不在抓取管线内。

## 代码架构

### 入口

- `main.py`：抓取人民日报文章的主入口，支持 `--date` 参数指定日期

### modules/ — 核心功能模块

| 模块 | 职责 |
|------|------|
| `crawler.py` | 人民日报网页版爬虫，含反爬机制 |
| `parser.py` | HTML 内容解析，提取标题、正文、版面信息 |
| `processor.py` | 文本清洗、关键词提取与分类（不直接写各数据层，入库和视图由 article_database / markdown_writer 完成） |
| `article_database.py` | SQLite 核心库读写（`articles.sqlite`），FTS5 全文检索 |
| `article_identity.py` | 稳定文章 ID 生成和管理，去重判断的核心 |
| `notion.py` | Notion API 同步，通过 `Article ID` 字段保持一致性 |
| `markdown_writer.py` | 生成 Obsidian 阅读视图 Markdown |
| `exporter.py` | 导出 JSON/CSV 等格式 |
| `analyzer.py` | 旧 api/ 专用的趋势分析，未接入主流程（疑似死代码，待确认清理） |
| `series_detector.py` | 系列文章检测 |
| `date_selector.py` / `web_selector.py` | 日期和版面选择工具 |
| `cache.py` | 缓存（当前零引用，待确认清理） |
| `checkpoint.py` | 抓取断点续传（`data/checkpoints/` 运行时自动创建） |
| `security.py` | zip 备份与配置加密（当前零引用，名实不符，待确认清理） |
| `utils.py` | 配置加载、日志、目录工具 |
| `parallel.py` | 并行处理 |
| `peopleapp_opinion.py` | 人民日报 APP 评论库独立采集，沉淀到 `data/peopleapp_opinion/`，不写入主核心库 |
| `wechat_api.py` | 微信公众号接口最小安全封装，不记录或输出密钥与 access_token |
| `writing_workflow.py` | 公众号写作工作流的共享规则与本地状态管理 |
| `figure_workflow.py` | 双平台配图清单、正文插入计划与人工确认门槛 |
| `platform_workflow.py` | 公众号与今日头条同步前的统一门槛 |

教研素材库（`material_assets.sqlite`，含 `content_ideas` / `content_idea_notes` 表）没有独立 modules 模块，由 `scripts/import_material_assets.py`、`query_material_assets.py`、`export_content_ideas.py`、`refine_content_ideas.py`、`serve_idea_magazine.py` 直接读写。

### scripts/ — 辅助脚本

| 脚本 | 用途 |
|------|------|
| `query_articles.py` | 按关键词或日期查询文章（`--search` / `--date`） |
| `query_material_assets.py` | 查询教研素材卡（`--search` / `--topics`） |
| `rebuild_article_database.py` | 从 raw 重建 core 数据库，生成 `articles.sqlite` + `articles.jsonl` |
| `export_content_ideas.py` | 刷新选题库，生成 `选题库.md` + `content_ideas.csv` |
| `idea_magazine.py` | 根目录启动入口，打开本地 HTML 选题工作台（`http://127.0.0.1:8765`） |
| `scripts/serve_idea_magazine.py` | 选题工作台原始脚本，支持筛选、精筛、备注 |
| `scripts/build_idea_magazine_site.py` | 把本地选题库生成成可托管的只读网页快照 |
| `scripts/sync_idea_magazine_to_miaoda.py` | 覆盖发布妙搭“人民日报选题工作台”，保持访问地址不变 |
| `hotspot_magazine.py` | 根目录启动入口，打开本地 APP 评论热点选题工作台（`http://127.0.0.1:8766`） |
| `scripts/build_hotspot_magazine_site.py` | 把 APP 评论热点库生成成可托管的只读网页快照 |
| `scripts/sync_hotspot_magazine_to_miaoda.py` | 覆盖发布妙搭“APP 评论热点选题工作台”，保持访问地址不变 |
| `sync_to_notion.py` | 同步指定日期文章到 Notion |
| `notion_maintenance.py` | Notion 重复页归档和缺失文章补齐（`--dry-run` 预览） |
| `import_material_assets.py` | 导入教研素材数据 |
| `cleanup_local_data.py` | ⚠️ 危险：按日期范围真实删除 raw/vault 数据的一次性历史脚本，必须显式传 `--keep-start/--keep-end --confirm-delete` 才执行；不是日常缓存清理工具 |
| `migrate_sync_status.py` / `rebuild_sync_status.py` | 已退役，调用只提示并退出。不能从本地下载推断远端同步成功；对账使用 `notion_maintenance.py --dry-run` |

## 关键设计决策

1. **文章标识**：不以标题为唯一标识，始终使用 `article_id`（由 `article_identity.py` 生成）。标题变更、文件移动不影响同步判断。
2. **Notion 是外部视图**：本地 core 是事实源，Notion 是分发视图。同步前用 `--dry-run` 预览。
3. **选题系统**：选题统一进入 `material_assets.sqlite` 的 `content_ideas` 表，`content_idea_notes` 存储人工精筛和备注。
4. **config.json 不入库**：含 Notion Token，仅保留 `config.json.example` 作为示例。

## 常用开发命令

```bash
# 抓取文章
python3 main.py                          # 打开日期选择界面
python3 main.py --date 2026-05-27        # 抓取指定日期

# 查询
python3 scripts/query_articles.py --search 基层治理
python3 scripts/query_articles.py --date 2026-05-27
python3 scripts/query_material_assets.py --search 城市治理

# 首次建库；已有库请用 --db-path 指定新的核验目录
python3 scripts/rebuild_article_database.py

# Notion 同步
python3 scripts/sync_to_notion.py 2026-05-27
python3 scripts/sync_to_notion.py --start 2026-05-01 --end 2026-05-27 --all   # 范围同步必须加 --all；先加 --dry-run 核对范围
python3 scripts/notion_maintenance.py --dry-run
python3 scripts/notion_maintenance.py --archive-duplicates --create-missing --delay 0.4

# 选题库
python3 scripts/export_content_ideas.py
python3 idea_magazine.py
python3 scripts/sync_idea_magazine_to_miaoda.py
python3 hotspot_magazine.py
python3 scripts/sync_hotspot_magazine_to_miaoda.py
```

## Git Commit 规范

提交前必须先读取 `COMMIT_GUIDE.md` 和 `PROJECT_PROFILE.md`。

- 禁止使用 feat/fix/docs 等英文前缀
- 格式：`【变更类型】项目或范围：本次同步完成了什么`
- 变更类型：【资料新增】【资料修订】【资料整理】【结构调整】【检索优化】【采集更新】【同步发布】【流程维护】【校验归档】【教学输出】
- 涉及 SQLite/FTS5/Notion/文章 ID 时，正文必须说明影响

## 安全

- `config.json` 包含 Notion Token，绝不提交
- `.trae/`、`api/`、`outputs/`、`node_modules/` 等疑似旧工具目录，删除前需用户确认
- 不自动提交，除非用户明确要求


## Mac 与云端 Claude 协作

协作细则和任务交接模板见 `docs/mac-cloud-collaboration.md`。这部分仅规定云端协作边界，Mac 上既有采集、写稿和发布授权继续有效。

- Mac 为资料与进度主端；人工选题、数据库、采集、外部同步及发布由 Mac 执行。
- 云端从老师指定的 Mac 工作分支及精确提交建立独立 `claude/` 任务分支，不直接推送 Mac 分支或默认分支，不强制推送。
- 云端只改任务卡列出的文件；同一篇文章同一时间只交给一端编辑。交接必须记录基准提交、文章编号或 Article ID、允许改动范围和验证结果。
- 云端写稿停在可审查的文字产物，不执行得到送稿、Notion/妙搭同步、平台草稿创建或发布；需要这些操作时交回 Mac 按原有门槛执行。
- GitHub 不包含完整人工选题和写作进度；云端不得凭仓库数据库或导出总表宣称进度为最新，也不得覆盖 Mac 的数据库或运行状态。
- 云端需要人工选题或状态时，由 Mac 提供经审查的任务摘录或私密只读快照。凭据、登录态、完整写作映射及私密备注不进入公开仓库。
- 云端修改程序时只在临时测试资料上验证，不启动真实采集、数据库重建或外部写入。合并前由 Mac 检查文件范围、来源、公开风险和冲突；有冲突时先保留双方版本，不自动选一端覆盖。

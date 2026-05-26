# AI 项目规则

你正在协助一名公务员培训师维护资料型项目。

## 项目

**人民日报素材系统**：自动化抓取人民日报文章，存入 SQLite 核心库，同步到 Notion 数据库

## 项目结构

- **main.py** — 主脚本（抓取 + 同步）
- **modules/** — 模块化代码（crawler、parser、processor、notion、exporter）
- **scripts/** — 辅助脚本（rebuild_article_database、query_articles、sync_to_notion）
- **data/raw/** — 原始抓取数据
- **data/core/** — SQLite 核心库（稳定文章 ID 事实层）
- **data/index/** — FTS5 全文检索索引
- **data/vault/** — Obsidian 格式文章
- **data/exports/** — JSON/CSV 导出

## 规则

- 文档使用中文；机器流程、脚本、结构化数据文件名仍使用英文
- 公众号文章、成品稿、面向老师人工查找的文章文件，统一放在 `data/articles/公众号文章/`，文件名优先使用中文标题
- 不自动提交，除非用户明确要求
- 敏感信息（config.json 中的 Notion Token）不入 Git

## Git Commit 规范

提交 Git commit 时必须遵守以下规则：

1. Commit 描述必须使用中文。
2. 禁止使用 feat、fix、docs、style、refactor、perf、test、chore 作为开头。
3. 第一行必须使用格式：`【变更类型】项目或范围：本次同步完成了什么`
4. 变更类型只能使用 `COMMIT_GUIDE.md` 中列出的中文标签。
5. 生成 commit 前必须先阅读 `PROJECT_PROFILE.md` 和 `COMMIT_GUIDE.md`。
6. 如果本次变更涉及 SQLite 数据库、FTS5 索引、Notion 同步、文章 ID，正文必须说明影响。
7. 不要写"修改代码""更新文件""调整内容"这类空泛描述。

当前项目的具体规则见：
- `COMMIT_GUIDE.md`
- `PROJECT_PROFILE.md`

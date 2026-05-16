# 人民日报素材系统

## 项目简介

人民日报素材系统是一个自动化工具，用于抓取《人民日报》网页版文章并同步到 Notion 数据库。该系统具有以下特点：

- **自动化抓取**：每日定时抓取人民日报网页版当天所有版面文章
- **Notion 同步**：自动同步文章到 Notion 数据库
- **数据导出**：支持导出为 JSON、CSV 格式
- **增量更新**：自动检测重复文章，支持内容变化检测
- **防反爬**：随机 User-Agent、请求间隔控制

## 项目结构

```
PeopleDailyMaterial/
├── main.py                 # 主脚本
├── requirements.txt        # 依赖包列表
├── config.json             # 配置文件（需自行创建）
├── config.json.example     # 配置文件示例
├── data/                   # 数据存储目录
│   ├── raw/                # 原始数据
│   ├── processed/          # 处理后数据
│   └── exports/            # 导出数据
└── modules/                # 模块化代码
    ├── utils.py            # 工具函数
    ├── crawler.py          # 爬虫模块
    ├── parser.py           # 解析模块
    ├── processor.py        # 数据处理模块
    ├── notion.py           # Notion API模块
    └── exporter.py         # 数据导出模块
```

## 环境要求

- Python 3.8+
- 网络连接
- Notion 账户和 API 密钥

## 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd PeopleDailyMaterial
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置文件设置**
   - 复制 `config.json.example` 为 `config.json`
   - 填写 Notion API 配置信息
   ```json
   {
     "notion": {
       "token": "YOUR_NOTION_TOKEN",
       "database_id": "YOUR_DATABASE_ID"
     },
     "crawler": {
       "request_interval": [1, 3],
       "timeout": 10,
       "max_retries": 3,
       "proxy_enabled": false,
       "proxies": []
     },
     "export": {
       "dir": "data/exports"
     },
     "logging": {
       "level": "INFO",
       "log_file": "crawler.log"
     }
   }
   ```

## Notion 配置指南

### 获取 Notion Token

1. 访问 [Notion Developers](https://www.notion.so/my-integrations)
2. 点击 "+ 新建集成"
3. 填写集成名称（如 "人民日报素材系统"）
4. 选择关联的工作区
5. 点击 "提交"
6. 复制生成的 "Internal Integration Token"

### 获取 Notion Database ID

1. 打开 Notion 数据库页面
2. 复制浏览器地址栏中的 URL
3. URL 格式：`https://www.notion.so/{workspace}/{database_id}?v={view_id}`
4. 提取 `{database_id}` 部分（32个字符）

### Notion 数据库结构

创建一个新的 Notion 数据库，并添加以下属性：

| 属性名称 | 类型 | 说明 |
|---------|------|------|
| 标题 | Title | 文章标题 |
| URL | URL | 文章原始链接 |
| 版面名称 | Select | 文章所属版面 |
| 发布日期 | Date | 文章发布日期 |
| 分类 | Select | 文章分类 |
| 关键词 | Multi-select | 文章关键词 |

### 配置数据库访问权限

1. 打开 Notion 数据库页面
2. 点击右上角 "分享" 按钮
3. 点击 "邀请"，输入集成名称
4. 选择权限级别为 "编辑"

## 使用方法

### 抓取当天文章

```bash
python main.py
```

### 抓取指定日期文章

```bash
python main.py --date 2024-01-15
```

### 抓取日期范围内的文章

```bash
python main.py --date-range 2024-01-01 2024-01-07
```

## 本地核心数据库

项目已增加 SQLite 核心库，用来作为 AI 检索、Notion 同步和后续重分类的稳定事实索引层。旧的 `data/raw` 和 `data/vault` 仍然保留，避免破坏现有流程。

常用命令：

```bash
# 重建核心库
python3 scripts/rebuild_article_database.py

# 查询文章
python3 scripts/query_articles.py --search 基层治理

# 从核心库同步到 Notion
python3 scripts/sync_to_notion.py 2026-05-16
```

详细说明见 [docs/database.md](docs/database.md)。

## 模块说明

### 1. 爬虫模块 (`modules/crawler.py`)
- 自动获取所有版面 URL
- 支持防反爬机制（随机 User-Agent、请求间隔、代理）

### 2. 解析模块 (`modules/parser.py`)
- 解析目录页获取文章链接
- 解析文章内容（标题、正文、版面名称）

### 3. 数据处理模块 (`modules/processor.py`)
- 内容清洗和标准化
- 关键词提取和摘要生成
- 文章分类
- 重复检测

### 4. Notion API模块 (`modules/notion.py`)
- 创建和更新 Notion 页面
- 获取已存在的文章

### 5. 数据导出模块 (`modules/exporter.py`)
- 支持 JSON、CSV 格式导出

## 常见问题排查

### Notion API 连接失败
- 检查 Notion Token 是否正确
- 检查数据库 ID 是否正确
- 检查数据库访问权限是否设置为 "编辑"

### 爬虫被反爬机制拦截
- 增加请求间隔时间
- 启用 IP 代理池

### 文章解析失败
- 网页结构可能发生变化，需要更新解析规则

## 许可证

本项目采用 MIT 许可证。

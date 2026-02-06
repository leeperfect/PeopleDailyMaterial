# 人民日报素材系统

## 项目简介

人民日报素材系统是一个功能强大的自动化工具，用于抓取《人民日报》网页版文章、存储数据、分析热点话题和政策趋势，并提供Web界面和API接口。该系统具有以下特点：

- **自动化抓取**：每日定时抓取人民日报网页版当天所有文章
- **多平台存储**：存储至Notion数据库和本地文件系统
- **数据分析**：实现热点话题预测、政策趋势分析和文章聚类
- **API接口**：提供标准化的API接口，支持Claude Skill调用
- **Web界面**：直观的数据可视化和管理界面
- **性能优化**：实现缓存和并行处理，提高数据处理速度
- **安全保障**：支持数据加密和备份，确保数据安全

## 项目结构

```
PeopleDailyMaterial/
├── main.py                 # 主脚本
├── requirements.txt        # 依赖包列表
├── config.json             # 配置文件
├── data/                   # 数据存储目录
│   ├── raw/                # 原始数据
│   ├── processed/          # 处理后数据
│   ├── exports/            # 导出数据
│   ├── cache/              # 缓存数据
│   └── backups/            # 备份数据
├── modules/                # 模块化代码
│   ├── utils.py            # 工具函数
│   ├── crawler.py          # 爬虫模块
│   ├── parser.py           # 解析模块
│   ├── processor.py        # 数据处理模块
│   ├── notion.py           # Notion API模块
│   ├── exporter.py         # 数据导出模块
│   ├── analyzer.py         # 数据分析模块
│   ├── cache.py            # 缓存模块
│   ├── parallel.py         # 并行处理模块
│   └── security.py         # 安全模块
├── api/                    # API接口
│   ├── claude_skill.py     # Claude skill接口
│   ├── web_app.py          # Web应用
│   └── templates/          # 模板文件
│       └── index.html      # 首页模板
├── .github/workflows/
│   └── daily_crawl.yml     # GitHub Actions工作流配置
└── README.md               # 项目说明文档
```

## 环境要求

- Python 3.8+
- 网络连接
- Notion账户和API密钥
- 可选：Git（用于版本控制）

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
   - 复制`config.json`模板文件
   - 填写Notion API配置信息
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
     "analyzer": {
       "hot_topic": {
         "topK": 10,
         "days": 7
       },
       "policy": {
         "keywords": ["政策", "法规", "条例", "办法", "意见", "通知", "决定", "规划"]
       }
     },
     "api": {
       "host": "0.0.0.0",
       "port": 5000,
       "debug": false
     },
     "logging": {
       "level": "INFO",
       "log_file": "crawler.log"
     }
   }
   ```

## Notion配置指南

### 获取Notion Token

1. 访问 [Notion Developers](https://www.notion.so/my-integrations)
2. 点击"+ 新建集成"
3. 填写集成名称（如"人民日报素材系统"）
4. 选择关联的工作区
5. 配置集成权限：
   - 内容：读取和写入
   - 评论：无
   - 其他：根据需要选择
6. 点击"提交"
7. 复制生成的"Internal Integration Token"（这就是你的Notion Token）

### 获取Notion Database ID

#### 方法一：从数据库URL直接提取

1. 打开Notion数据库页面
2. 复制浏览器地址栏中的URL
3. URL格式通常为：`https://www.notion.so/{workspace}/{database_id}?v={view_id}`
4. 提取`{database_id}`部分（32个字符的字符串）

#### 方法二：通过Notion API查询获取

```python
import requests

NOTION_TOKEN = "YOUR_NOTION_TOKEN"

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

response = requests.get("https://api.notion.com/v1/databases", headers=headers)
print(response.json())
```

### Notion数据库结构

创建一个新的Notion数据库，并添加以下属性：

| 属性名称 | 类型 | 说明 |
|---------|------|------|
| 标题 | Title | 文章标题 |
| URL | URL | 文章原始链接 |
| 版面名称 | Select | 文章所属版面 |
| 发布日期 | Date | 文章发布日期 |
| 分类 | Select | 文章分类 |
| 关键词 | Multi-select | 文章关键词 |
| 创建时间 | Created time | 自动生成 |

### 配置数据库访问权限

1. 打开Notion数据库页面
2. 点击右上角"分享"按钮
3. 在"分享"对话框中，点击"邀请"
4. 输入你的集成名称（如"人民日报素材系统"）
5. 选择权限级别为"编辑"
6. 点击"邀请"

## 使用方法

### 1. 抓取当天文章

```bash
python main.py
```

### 2. 抓取指定日期文章

```bash
python main.py --date 2023-10-01
```

### 3. 抓取日期范围内的文章

```bash
python main.py --date-range 2023-10-01 2023-10-07
```

### 4. 启动Web界面

```bash
python api/web_app.py
```

访问 `http://localhost:5000` 查看Web界面

### 5. 启动Claude Skill API

```bash
python api/claude_skill.py
```

API地址：`http://localhost:5000/api/claude`

## 模块说明

### 1. 爬虫模块 (`modules/crawler.py`)
- 实现URL生成和网页请求
- 支持防反爬机制（随机User-Agent、请求间隔、代理）

### 2. 解析模块 (`modules/parser.py`)
- 解析目录页获取文章链接
- 解析文章内容（标题、正文、版面名称）
- 支持网页结构变化检测

### 3. 数据处理模块 (`modules/processor.py`)
- 内容清洗和标准化
- 关键词提取和摘要生成
- 文章分类
- 重复检测和增量更新

### 4. Notion API模块 (`modules/notion.py`)
- 与Notion API交互
- 创建和更新Notion页面
- 获取已存在的文章

### 5. 数据导出模块 (`modules/exporter.py`)
- 支持JSON、CSV、Excel格式导出
- 为Claude Skill提供专用格式

### 6. 数据分析模块 (`modules/analyzer.py`)
- 热点话题分析和预测
- 政策趋势分析
- 文章聚类

### 7. 缓存模块 (`modules/cache.py`)
- 内存缓存和文件缓存
- 提高数据访问速度

### 8. 并行处理模块 (`modules/parallel.py`)
- 线程池和进程池支持
- 提高数据处理效率

### 9. 安全模块 (`modules/security.py`)
- 数据备份和恢复
- 数据加密和解密

## API接口文档

### Claude Skill API

#### 1. 获取文章
- **URL**: `/api/claude/articles`
- **方法**: GET
- **参数**:
  - `date` (可选): 日期，格式：YYYY-MM-DD
  - `category` (可选): 分类
- **返回**: 文章列表

#### 2. 获取热点话题
- **URL**: `/api/claude/hot-topics`
- **方法**: GET
- **参数**:
  - `days` (可选): 天数，默认：7
- **返回**: 热点话题列表

#### 3. 获取政策趋势
- **URL**: `/api/claude/policy-trends`
- **方法**: GET
- **返回**: 政策趋势列表

#### 4. 分析政策
- **URL**: `/api/claude/analyze-policy`
- **方法**: POST
- **参数**:
  - `article_id`: 文章ID
- **返回**: 政策分析结果

### Web应用 API

#### 1. 获取统计信息
- **URL**: `/api/statistics`
- **方法**: GET
- **返回**: 系统统计信息

#### 2. 获取热点话题
- **URL**: `/api/hot-topics`
- **方法**: GET
- **参数**:
  - `days` (可选): 天数，默认：7
- **返回**: 热点话题列表

#### 3. 获取政策趋势
- **URL**: `/api/policy-trends`
- **方法**: GET
- **返回**: 政策趋势列表

#### 4. 获取文章聚类
- **URL**: `/api/article-clusters`
- **方法**: GET
- **返回**: 文章聚类结果

#### 5. 获取文章
- **URL**: `/api/articles`
- **方法**: GET
- **参数**:
  - `date` (可选): 日期，格式：YYYY-MM-DD
- **返回**: 文章列表

## 部署指南

### 本地部署

1. 安装依赖
2. 配置`config.json`
3. 运行主脚本

### GitHub Actions部署

1. 打开项目GitHub仓库
2. 点击"Settings" > "Secrets and variables" > "Actions"
3. 添加以下secrets：
   - `NOTION_TOKEN`：你的Notion API令牌
   - `NOTION_DATABASE_ID`：你的Notion数据库ID
4. 工作流将在每天UTC时间0点（北京时间8点）自动运行

### 服务器部署

1. 安装Python 3.8+
2. 克隆项目并安装依赖
3. 配置`config.json`
4. 使用systemd或supervisor设置为后台服务
5. 配置Nginx反向代理（可选）

## 定时任务设置

### Windows系统

1. 打开"任务计划程序"
2. 点击"创建基本任务"
3. 填写任务名称和描述
4. 选择"每天"触发
5. 设置开始时间
6. 选择"启动程序"
7. 浏览选择python.exe，添加参数：`main.py`，起始位置设置为项目目录
8. 完成向导

### macOS系统

1. 打开"终端"
2. 编辑crontab：
   ```bash
   crontab -e
   ```
3. 添加以下行（每天8点运行）：
   ```
   0 8 * * * cd /path/to/PeopleDailyMaterial && python main.py
   ```
4. 保存并退出

### Linux系统

1. 打开"终端"
2. 编辑crontab：
   ```bash
   crontab -e
   ```
3. 添加以下行（每天8点运行）：
   ```
   0 8 * * * cd /path/to/PeopleDailyMaterial && python main.py
   ```
4. 保存并退出

## 常见问题排查

### 1. Notion API连接失败

- 检查Notion Token是否正确
- 检查数据库ID是否正确
- 检查数据库访问权限是否设置为"编辑"
- 检查网络连接是否正常

### 2. 爬虫被反爬机制拦截

- 增加请求间隔时间
- 启用IP代理池
- 检查User-Agent配置

### 3. 文章解析失败

- 网页结构可能发生变化，需要更新解析规则
- 检查网络连接是否正常

### 4. Web界面无法访问

- 检查Flask服务是否启动
- 检查端口是否被占用
- 检查防火墙设置

### 5. API接口返回错误

- 检查API服务是否启动
- 检查请求参数是否正确
- 检查日志文件获取详细错误信息

## 性能优化建议

1. **启用缓存**：在`config.json`中配置缓存参数
2. **使用并行处理**：在处理大量文章时启用
3. **合理设置请求间隔**：避免过于频繁的请求
4. **定期清理缓存**：防止缓存占用过多空间
5. **使用代理**：在需要时启用IP代理池

## 安全建议

1. **保护Notion Token**：不要将Token提交到版本控制系统
2. **定期备份数据**：使用`modules/security.py`中的备份功能
3. **使用环境变量**：对于生产环境，使用环境变量存储敏感信息
4. **限制API访问**：在生产环境中配置API访问控制

## 许可证

本项目采用MIT许可证。

## 贡献

欢迎贡献代码、报告问题或提出建议！

## 更新日志

### v2.0.0
- 重构为模块化架构
- 添加数据分析和热点预测功能
- 实现Web界面和API接口
- 优化性能和安全性

### v1.0.0
- 基本爬虫功能
- Notion存储
- 简单的数据处理

## 联系方式

如有问题或建议，请联系项目维护者。

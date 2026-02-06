# 人民日报爬虫与Notion存储实现计划

## 项目结构
```
PeopleDailyMaterial/
├── main.py                 # 主脚本
├── requirements.txt        # 依赖包列表
├── config.json             # 配置文件
├── .github/workflows/
│   └── daily_crawl.yml     # GitHub Actions工作流配置
└── README.md               # 项目说明文档
```

## 核心模块设计

### 1. URL生成模块
- 动态生成当日人民日报目录页URL
- 支持日期范围查询的URL生成
- 处理URL格式验证

### 2. 网页请求模块
- 实现随机请求间隔(1-3秒)
- 随机User-Agent池
- 请求超时处理(10秒)
- HTTP错误重试机制(最多3次)
- IP代理池支持(可选)

### 3. 内容解析模块
- 解析目录页获取所有文章链接
- 提取文章标题、正文、版面名称、URL
- 网页结构变化检测
- 内容清洗(去除广告、无关链接、冗余HTML标签)

### 4. 数据处理模块
- 数据结构化处理
- 双重数据去重(URL精确匹配 + 标题+日期模糊匹配)
- 增量更新检测

### 5. Notion API交互模块
- API身份验证
- 元数据写入(标题、URL、版面名称、发布日期、创建时间)
- 正文内容结构化写入(Page Block格式)
- 错误处理和重试机制

### 6. 日志模块
- 分级日志记录(DEBUG/INFO/WARNING/ERROR/CRITICAL)
- 包含时间戳、模块名称、详细错误信息
- 日志文件轮转

## 配置文件设计

### config.json结构
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
  "logging": {
    "level": "INFO",
    "log_file": "crawler.log"
  }
}
```

## Notion数据库结构

### 必要属性
| 属性名称 | 类型 | 说明 |
|---------|------|------|
| 标题 | Title | 文章标题 |
| URL | URL | 文章原始链接 |
| 版面名称 | Select | 文章所属版面 |
| 发布日期 | Date | 文章发布日期 |
| 创建时间 | Created time | 自动生成 |

## 高级功能实现

### GitHub Actions工作流
- 配置每日定时运行
- 环境变量设置
- 运行结果通知

### 命令行参数支持
- `--date-range` 参数支持日期范围查询
- `--config` 参数指定配置文件路径
- `--debug` 参数开启调试模式

## 实现步骤

1. 搭建基础项目结构
2. 实现配置文件加载模块
3. 实现URL生成模块
4. 实现网页请求模块
5. 实现内容解析模块
6. 实现数据处理模块
7. 实现Notion API交互模块
8. 实现日志模块
9. 编写主脚本逻辑
10. 配置GitHub Actions工作流
11. 编写详细的README文档
12. 测试完整功能

## 技术栈

- Python 3.8+
- requests (网络请求)
- beautifulsoup4 (HTML解析)
- notion-client (Notion API交互)
- argparse (命令行参数处理)
- json (配置文件解析)
- logging (日志记录)
- schedule (定时任务，可选)

## 安全考虑

- Notion Token安全存储
- 合理的请求频率控制
- 错误处理和异常捕获
- 数据去重避免重复存储

## 扩展性考虑

- 模块化设计便于维护和扩展
- 配置文件支持自定义参数
- 命令行参数支持灵活调用
- 日志系统便于问题排查
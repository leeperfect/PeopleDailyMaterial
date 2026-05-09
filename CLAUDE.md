# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 语言要求

始终使用中文与用户对话。所有回复、说明、注释建议均使用中文。

## Project Overview

People's Daily (人民日报) material collection system. Two independent workflows:

1. **Crawler** (`main.py`): Scrapes articles from paper.people.com.cn, stores to Notion database and local JSON files
2. **Material Extractor** (`extract_materials.py`): Rule-based extraction of quotes, cases, writing methods from crawled articles into an Obsidian vault

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Crawl today's articles
python main.py

# Crawl specific date
python main.py --date 2026-05-09

# Crawl date range
python main.py --date-range 2026-05-01 2026-05-09

# Extract materials from crawled data
python extract_materials.py
python extract_materials.py --date 2026-04-01
python extract_materials.py --limit 10
python extract_materials.py --collect-annotations

# Start web interface
python api/web_app.py

# Start Claude Skill API
python api/claude_skill.py
```

## Architecture

### Data Flow

```
paper.people.com.cn → crawler.py → parser.py → processor.py → notion.py (Notion DB)
                                                                ↓
                                                          data/raw/*.json
                                                          data/processed/*.json
                                                          data/exports/*

data/vault/**/*.md → extract_materials.py → data/vault/_素材库/
```

### Crawler Pipeline (`main.py`)

`PeopleDailyCrawler` → `ContentParser` → `DataProcessor` → `NotionAPI` → `DataExporter` → `HotTopicAnalyzer`

- **URL pattern**: `https://paper.people.com.cn/rmrb/pc/layout/{YYYYMM}/{DD}/node_{XX}.html` (directory pages)
- **Article URL**: `https://paper.people.com.cn/rmrb/pc/content/{YYYYMM}/{DD}/{article_id}.html`
- The crawler discovers all node IDs (版面) from page 01, then crawls each directory to find article links
- Anti-crawling: random User-Agent rotation, configurable request interval, proxy support
- Deduplication: checks existing Notion pages by title/URL before creating

### Material Extractor (`extract_materials.py`)

Standalone script (no API needed). Uses regex patterns to extract:

- **金句 (Golden Quotes)**: 9 pattern types including Xi Jinping quotes, parallel sentences, policy directives, four-character phrase chains
- **案例 (Cases)**: Paragraphs containing both location names and numerical data
- **写作方法 (Writing Methods)**: Article structure patterns, parallel sentence patterns
- **热点专题 (Hot Topics)**: Keyword-based classification into 10 major themes with subtopics

Output goes to `data/vault/_素材库/` organized by type. Also collects manual Obsidian Callout annotations (`> [!quote]`, `> [!example]`, etc.) and `==highlights==`.

### Key Modules

| Module | Responsibility |
|--------|---------------|
| `modules/crawler.py` | URL generation, HTTP requests with retry/backoff |
| `modules/parser.py` | HTML parsing for directory pages and articles (BeautifulSoup + lxml) |
| `modules/processor.py` | Content cleaning, keyword extraction (jieba), article classification |
| `modules/notion.py` | Notion API CRUD operations via `notion-client` |
| `modules/analyzer.py` | Hot topic prediction, policy trend analysis, article clustering (scikit-learn) |
| `modules/exporter.py` | JSON/CSV export, Claude-specific format |

### Configuration

`config.json` contains Notion credentials, crawler settings, and export paths. The `Config` class in `utils.py` supports dot-notation access (e.g., `config.get('notion.token')`).

**Important**: `config.json` contains secrets and should not be committed. In GitHub Actions, it's generated from repository secrets (`NOTION_TOKEN`, `NOTION_DATABASE_ID`).

### Notion Database Schema

Properties: 标题 (title), URL (url), 版面名称 (select), 发布日期 (date), 分类 (select), 关键词 (multi_select)

### Obsidian Vault Structure

`data/vault/` is an Obsidian vault with:
- `2025/`, `2026/` — crawled articles organized by date
- `_素材库/` — extracted materials (金句/, 案例/, 写作方法/, 热点专题/, 我的标注/)

## Development Notes

- Python 3.8+ required
- The project uses a virtual environment (`venv/`)
- Logs go to `crawler.log`
- No test suite exists
- `extract_materials.py` is independent from `main.py` — it reads from the vault, not from `data/raw/`
- The `modules/` imports assume running from project root directory

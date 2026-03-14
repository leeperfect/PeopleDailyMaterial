#!/usr/bin/env python3
"""
直接同步本地文章数据到 Notion
跳过爬虫和浏览器选择界面
"""
import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.utils import Config, setup_logger
from modules.notion import NotionAPI

def load_articles(date_str):
    """加载本地文章数据"""
    date_normalized = date_str.replace('-', '')  # 2026-01-03 -> 20260103
    file_path = f"data/raw/articles_{date_normalized}.json"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载 {file_path} 失败: {e}")
        return []

def sync_articles(dates):
    """同步指定日期的文章到 Notion"""
    config = Config()
    setup_logger(config)
    notion_api = NotionAPI(config)

    print(f"=== 强制重新同步 {dates} 到 Notion ===\n")

    total_synced = 0

    for date_str in dates:
        print(f"=== 正在同步 {date_str} ===")
        articles = load_articles(date_str)

        if not articles:
            print(f"  未找到 {date_str} 的数据文件")
            continue

        print(f"  找到 {len(articles)} 篇文章")

        date = datetime.strptime(date_str, '%Y-%m-%d')
        synced_count = 0

        for i, article in enumerate(articles, 1):
            title = article.get('title', '')

            if not title or title == '广告':
                continue

            notion_api.create_page(article, date)
            print(f"  [{i}/{len(articles)}] 上传成功: {title[:50]}...")
            synced_count += 1

        print(f"  {date_str} 新增 {synced_count} 篇\n")
        total_synced += synced_count

    print(f"\n✅ 同步完成！共上传 {total_synced} 篇文章")

if __name__ == '__main__':
    dates = ['2026-01-03', '2026-01-04', '2026-01-05', '2026-01-06']
    sync_articles(dates)

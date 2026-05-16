#!/usr/bin/env python3
"""
直接同步本地文章数据到 Notion
跳过爬虫和浏览器选择界面

用法:
    python sync_to_notion.py 2026-05-12          # 同步单个日期
    python sync_to_notion.py 2026-05-11 2026-05-12  # 同步多个日期
    python sync_to_notion.py                      # 无参数时同步今天
"""
import json
import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.utils import Config, setup_logger
from modules.notion import NotionAPI
from modules.processor import DataProcessor

def load_articles(date_str):
    """加载本地文章数据"""
    date_normalized = date_str.replace('-', '')  # 2026-01-03 -> 20260103
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(PROJECT_ROOT, "data", "raw", f"articles_{date_normalized}.json")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载 {file_path} 失败: {e}")
        return []

def sync_articles(dates):
    """同步指定日期的文章到 Notion（自动跳过已存在的文章）"""
    config = Config()
    setup_logger(config)
    notion_api = NotionAPI(config)
    processor = DataProcessor()

    print(f"\n{'='*60}")
    print(f"  ☁️ 同步文章到 Notion")
    print(f"  📅 日期: {', '.join(dates)}")
    print(f"{'='*60}\n")

    # 获取已有文章列表用于去重
    print("  正在获取 Notion 已有文章列表...")
    existing_articles = notion_api.get_existing_articles()
    existing_titles = {a.get('title', '') for a in existing_articles}
    print(f"  已有 {len(existing_articles)} 篇文章\n")

    total_synced = 0
    total_skipped = 0
    total_failed = 0

    for date_str in dates:
        print(f"{'='*40}")
        print(f"  📅 正在同步 {date_str}")
        print(f"{'='*40}")
        articles = load_articles(date_str)

        if not articles:
            print(f"  ⚠️ 未找到 {date_str} 的数据文件\n")
            continue

        print(f"  找到 {len(articles)} 篇文章\n")

        date = datetime.strptime(date_str, '%Y-%m-%d')
        synced_count = 0
        skipped_count = 0

        for i, article in enumerate(articles, 1):
            title = article.get('title', '')

            if not title or title == '广告':
                continue

            # 检查是否已存在
            if title in existing_titles:
                print(f"  [{i}/{len(articles)}] ⏭️ 已存在: {title[:40]}")
                skipped_count += 1
                continue

            page_id = notion_api.create_page(article, date)
            if page_id:
                print(f"  [{i}/{len(articles)}] ✅ 上传成功: {title[:40]}")
                existing_titles.add(title)
                synced_count += 1
            else:
                print(f"  [{i}/{len(articles)}] ❌ 上传失败: {title[:40]}")
                total_failed += 1

            # 短暂延迟避免 Notion API 限速
            time.sleep(0.5)

        print(f"\n  {date_str}: 新增 {synced_count} 篇, 跳过 {skipped_count} 篇\n")
        total_synced += synced_count
        total_skipped += skipped_count

    print(f"\n{'='*60}")
    print(f"  ☁️ 同步完成！")
    print(f"     新增: {total_synced} 篇")
    print(f"     跳过: {total_skipped} 篇（已存在）")
    if total_failed:
        print(f"     失败: {total_failed} 篇")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        dates = sys.argv[1:]
    else:
        dates = [datetime.now().strftime('%Y-%m-%d')]
    sync_articles(dates)


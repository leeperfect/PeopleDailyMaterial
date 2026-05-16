#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步本地文章到 Notion。

默认优先读取新的 SQLite 核心库 data/core/articles.sqlite；如果核心库尚未
建立或指定日期没有数据，则自动回退到旧的 data/raw/articles_YYYYMMDD.json。

用法:
    python scripts/sync_to_notion.py 2026-05-12
    python scripts/sync_to_notion.py 2026-05-11 2026-05-12
    python scripts/sync_to_notion.py --update-existing 2026-05-12
    python scripts/sync_to_notion.py --from-raw 2026-05-12
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Sequence

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from modules.article_database import DEFAULT_DB_PATH, ArticleStore
from modules.article_identity import normalize_date
from modules.notion import NotionAPI
from modules.utils import Config, setup_logger


def load_articles_from_raw(date_str: str) -> List[Dict]:
    date_normalized = normalize_date(date_str).replace("-", "")
    file_path = os.path.join(PROJECT_ROOT, "data", "raw", f"articles_{date_normalized}.json")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            articles = json.load(f)
    except Exception as e:
        print(f"加载旧 JSON 失败: {file_path} ({e})")
        return []

    for article in articles:
        article["date"] = normalize_date(article.get("date") or date_str)
    return articles


def load_articles_from_database(dates: Sequence[str]) -> List[Dict]:
    db_path = os.path.join(PROJECT_ROOT, DEFAULT_DB_PATH)
    if not os.path.exists(db_path):
        return []

    store = ArticleStore(db_path)
    try:
        return store.get_articles(dates=[normalize_date(d) for d in dates])
    finally:
        store.close()


def load_articles(dates: Sequence[str], force_raw: bool = False) -> List[Dict]:
    normalized_dates = [normalize_date(d) for d in dates]
    if not force_raw:
        db_articles = load_articles_from_database(normalized_dates)
        if db_articles:
            print(f"  已从核心库读取 {len(db_articles)} 篇文章")
            return db_articles

    articles: List[Dict] = []
    for date_str in normalized_dates:
        articles.extend(load_articles_from_raw(date_str))
    if articles:
        print(f"  已从旧 JSON 读取 {len(articles)} 篇文章")
    return articles


def build_existing_indexes(existing_articles: List[Dict]) -> Dict[str, Dict]:
    by_article_id = {}
    by_url = {}
    by_title_date = {}

    for article in existing_articles:
        article_id = article.get("article_id") or article.get("Article ID")
        if article_id:
            by_article_id[article_id] = article
        if article.get("url"):
            by_url[article["url"]] = article
        title = article.get("title", "")
        date = article.get("date", "")
        if title and date:
            by_title_date[(title, date)] = article

    return {
        "article_id": by_article_id,
        "url": by_url,
        "title_date": by_title_date,
    }


def find_duplicate(article: Dict, indexes: Dict[str, Dict]) -> Optional[Dict]:
    article_id = article.get("article_id")
    url = article.get("source_url") or article.get("url")
    title = article.get("title", "")
    date = article.get("date", "")

    if article_id and article_id in indexes["article_id"]:
        return indexes["article_id"][article_id]
    if url and url in indexes["url"]:
        return indexes["url"][url]
    if title and date and (title, date) in indexes["title_date"]:
        return indexes["title_date"][(title, date)]
    return None


def add_to_indexes(article: Dict, page_id: str, indexes: Dict[str, Dict]):
    record = {
        "id": page_id,
        "article_id": article.get("article_id", ""),
        "title": article.get("title", ""),
        "url": article.get("source_url") or article.get("url") or "",
        "date": article.get("date", ""),
    }
    if record["article_id"]:
        indexes["article_id"][record["article_id"]] = record
    if record["url"]:
        indexes["url"][record["url"]] = record
    if record["title"] and record["date"]:
        indexes["title_date"][(record["title"], record["date"])] = record


def sync_articles(dates: Sequence[str], force_raw: bool = False, update_existing: bool = False):
    config = Config()
    setup_logger(config)
    notion_api = NotionAPI(config)

    normalized_dates = [normalize_date(d) for d in dates]
    print(f"\n{'='*60}")
    print("  同步文章到 Notion")
    print(f"  日期: {', '.join(normalized_dates)}")
    print(f"{'='*60}\n")

    articles = load_articles(normalized_dates, force_raw=force_raw)
    if not articles:
        print("  未找到可同步文章。请先运行 scripts/rebuild_article_database.py 或检查旧 JSON。")
        return

    print("  正在获取 Notion 已有文章索引...")
    existing_articles = notion_api.get_existing_articles()
    indexes = build_existing_indexes(existing_articles)
    print(f"  Notion 已有 {len(existing_articles)} 篇文章\n")

    total_synced = 0
    total_updated = 0
    total_skipped = 0
    total_failed = 0

    for i, article in enumerate(articles, 1):
        title = article.get("title", "")
        if not title or title == "广告":
            continue

        date_str = normalize_date(article.get("date") or normalized_dates[0])
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print(f"  [{i}/{len(articles)}] 跳过日期异常文章: {title[:40]}")
            total_failed += 1
            continue

        duplicate = find_duplicate(article, indexes)
        if duplicate and not update_existing:
            print(f"  [{i}/{len(articles)}] 已存在: {title[:40]}")
            total_skipped += 1
            continue

        if duplicate and update_existing:
            ok = notion_api.update_page(duplicate["id"], article)
            if ok is False:
                print(f"  [{i}/{len(articles)}] 更新失败: {title[:40]}")
                total_failed += 1
            else:
                print(f"  [{i}/{len(articles)}] 更新成功: {title[:40]}")
                total_updated += 1
        else:
            page_id = notion_api.create_page(article, date)
            if page_id:
                print(f"  [{i}/{len(articles)}] 上传成功: {title[:40]}")
                add_to_indexes(article, page_id, indexes)
                total_synced += 1
            else:
                print(f"  [{i}/{len(articles)}] 上传失败: {title[:40]}")
                total_failed += 1

        time.sleep(0.5)

    print(f"\n{'='*60}")
    print("  Notion 同步完成")
    print(f"     新增: {total_synced} 篇")
    print(f"     更新: {total_updated} 篇")
    print(f"     跳过: {total_skipped} 篇")
    if total_failed:
        print(f"     失败: {total_failed} 篇")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="同步本地文章到 Notion")
    parser.add_argument("dates", nargs="*", help="日期，格式 YYYY-MM-DD；不填则同步今天")
    parser.add_argument("--from-raw", action="store_true", help="强制读取旧 data/raw JSON")
    parser.add_argument("--update-existing", action="store_true", help="遇到已存在文章时更新 Notion 页面")
    args = parser.parse_args()

    dates = args.dates or [datetime.now().strftime("%Y-%m-%d")]
    sync_articles(dates, force_raw=args.from_raw, update_existing=args.update_existing)


if __name__ == "__main__":
    main()

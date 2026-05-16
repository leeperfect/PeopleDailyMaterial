#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询本地核心文章库。

用法:
    python scripts/query_articles.py --search 基层治理
    python scripts/query_articles.py --date 2026-05-16
    python scripts/query_articles.py --start 2026-05-01 --end 2026-05-16 --limit 50
"""

import argparse
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from modules.article_database import DEFAULT_DB_PATH, ArticleStore


def main():
    parser = argparse.ArgumentParser(description="查询人民日报素材核心库")
    parser.add_argument("--search", help="关键词或短语")
    parser.add_argument("--date", help="指定日期 YYYY-MM-DD")
    parser.add_argument("--start", help="开始日期 YYYY-MM-DD")
    parser.add_argument("--end", help="结束日期 YYYY-MM-DD")
    parser.add_argument("--category", help="分类")
    parser.add_argument("--limit", type=int, default=20, help="最多返回条数")
    args = parser.parse_args()

    db_path = os.path.join(PROJECT_ROOT, DEFAULT_DB_PATH)
    if not os.path.exists(db_path):
        print("未找到核心库，请先运行: python scripts/rebuild_article_database.py")
        return

    store = ArticleStore(db_path)
    try:
        if args.search:
            articles = store.search(args.search, limit=args.limit)
        else:
            dates = [args.date] if args.date else None
            articles = store.get_articles(
                dates=dates,
                start_date=args.start,
                end_date=args.end,
                category=args.category,
                limit=args.limit,
            )

        stats = store.stats()
    finally:
        store.close()

    print(f"核心库: {stats['article_count']} 篇文章，{stats['chunk_count']} 个检索分块")
    print("-" * 60)
    for article in articles:
        print(f"{article['date']} | {article.get('section_name') or '-'} | {article['title']}")
        print(f"  ID: {article['article_id']}")
        if article.get("source_url"):
            print(f"  URL: {article['source_url']}")
        if article.get("markdown_path"):
            print(f"  MD: {article['markdown_path']}")


if __name__ == "__main__":
    main()

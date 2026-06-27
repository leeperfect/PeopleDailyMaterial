#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询人民日报 APP 评论库。

这个脚本只读取 data/peopleapp_opinion/core/articles.sqlite，和原人民日报库分开。
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.article_database import ArticleStore
from modules.article_identity import normalize_date
from modules.peopleapp_opinion import DB_PATH, load_articles, search_articles


def text_snippet(text: str, query: str = "", width: int = 90) -> str:
    text = " ".join((text or "").split())
    if not text:
        return ""
    if query and query in text:
        pos = max(0, text.find(query) - width // 3)
        snippet = text[pos : pos + width]
    else:
        snippet = text[:width]
    return snippet + ("..." if len(text) > len(snippet) else "")


def print_stats() -> None:
    if not DB_PATH.exists():
        print("APP 评论库尚未建立，请先运行 scripts/crawl_peopleapp_opinion.py")
        return
    store = ArticleStore(str(DB_PATH))
    try:
        stats = store.stats()
    finally:
        store.close()
    print("APP 评论库概况")
    print(f"- 本地库：{DB_PATH.relative_to(PROJECT_ROOT)}")
    print(f"- 文章数：{stats.get('article_count')}")
    print(f"- 检索分块：{stats.get('chunk_count')}")
    print(f"- 日期范围：{stats.get('start_date')} 至 {stats.get('end_date')}")


def main() -> int:
    parser = argparse.ArgumentParser(description="查询人民日报 APP 评论库")
    parser.add_argument("--search", help="关键词检索")
    parser.add_argument("--date", action="append", help="指定日期 YYYY-MM-DD，可重复传入")
    parser.add_argument("--start", help="开始日期 YYYY-MM-DD")
    parser.add_argument("--end", help="结束日期 YYYY-MM-DD")
    parser.add_argument("--limit", type=int, default=20, help="最多显示多少条，默认 20")
    parser.add_argument("--stats", action="store_true", help="只显示库概况")
    args = parser.parse_args()

    if args.stats:
        print_stats()
        return 0

    if args.search:
        articles = search_articles(args.search, limit=args.limit)
        mode = f"关键词：{args.search}"
    else:
        dates = [normalize_date(d) for d in args.date] if args.date else None
        articles = load_articles(
            dates=dates,
            start_date=normalize_date(args.start) if args.start else None,
            end_date=normalize_date(args.end) if args.end else None,
            limit=args.limit,
        )
        mode = "日期/范围查询" if dates or args.start or args.end else "最近文章"

    print(f"APP 评论库查询：{mode}")
    print(f"命中：{len(articles)} 篇\n")
    for index, article in enumerate(articles, 1):
        print(f"{index}. {article.get('title', '无标题')}")
        print(f"   日期：{article.get('date', '')}｜来源：{article.get('source_name') or article.get('source', '')}")
        print(f"   Article ID：{article.get('article_id', '')}")
        print(f"   Content ID：{article.get('content_id', '')}｜Rel ID：{article.get('rel_id', '')}")
        print(f"   URL：{article.get('source_url') or article.get('url') or ''}")
        snippet = text_snippet(article.get("content", ""), args.search or "")
        if snippet:
            print(f"   摘要：{snippet}")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

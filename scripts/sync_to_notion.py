#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步本地文章到 Notion。

默认优先读取新的 SQLite 核心库 data/core/articles.sqlite；如果核心库尚未
建立或指定日期没有数据，则自动回退到旧的 data/raw/articles_YYYYMMDD.json。

用法:
    python scripts/sync_to_notion.py 2026-05-12
    python scripts/sync_to_notion.py 2026-05-11 2026-05-12
    python scripts/sync_to_notion.py --all --update-existing --metadata-only --existing-only
    python scripts/sync_to_notion.py --all --start 2026-05-01 --end 2026-05-16 --dry-run
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
from modules.article_identity import build_article_id, normalize_date
from modules.notion_index import AmbiguousArticleMatch, add_to_indexes, build_existing_indexes, find_duplicate
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
        article["article_id"] = article.get("article_id") or build_article_id(article)
    return articles


def load_articles_from_database(
    dates: Optional[Sequence[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict]:
    db_path = os.path.join(PROJECT_ROOT, DEFAULT_DB_PATH)
    if not os.path.exists(db_path):
        return []

    store = ArticleStore(db_path, read_only=True)
    try:
        return store.get_articles(
            dates=[normalize_date(d) for d in dates] if dates else None,
            start_date=normalize_date(start_date) if start_date else None,
            end_date=normalize_date(end_date) if end_date else None,
            limit=limit,
        )
    finally:
        store.close()


def load_articles(
    dates: Optional[Sequence[str]],
    force_raw: bool = False,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict]:
    if limit is not None and limit < 1:
        raise ValueError("文章篇数上限必须大于零")
    normalized_dates = list(dict.fromkeys(normalize_date(d) for d in dates or []))
    articles: List[Dict] = []
    if not force_raw:
        db_articles = load_articles_from_database(
            dates=normalized_dates or None,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        if db_articles:
            print(f"  已从核心库读取 {len(db_articles)} 篇文章")
            articles.extend(db_articles)

    db_count = len(articles)
    covered_dates = {article.get("date") for article in articles}
    for date_str in normalized_dates:
        if limit is not None and len(articles) >= limit:
            break
        if date_str in covered_dates:
            continue
        batch = load_articles_from_raw(date_str)
        articles.extend(batch if limit is None else batch[:limit - len(articles)])
    if len(articles) > db_count:
        print(f"  已从旧 JSON 读取 {len(articles) - db_count} 篇文章")
    return articles


def sync_articles(
    dates: Optional[Sequence[str]],
    force_raw: bool = False,
    update_existing: bool = False,
    metadata_only: bool = False,
    existing_only: bool = False,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = None,
    delay: float = 0.35,
    dry_run: bool = False,
):
    config = Config()
    setup_logger(config)
    notion_api = NotionAPI(config)

    normalized_dates = [normalize_date(d) for d in dates] if dates else []
    range_label = f"{start_date or '最早'} ~ {end_date or '最新'}" if not normalized_dates else ", ".join(normalized_dates)
    print(f"\n{'='*60}")
    print("  同步文章到 Notion")
    print(f"  范围: {range_label}")
    if metadata_only:
        print("  模式: 只更新页面属性，不改正文")
    if existing_only:
        print("  模式: 只更新已有页面，不创建新页面")
    if dry_run:
        print("  模式: dry-run，仅预览不写入")
    print(f"{'='*60}\n")

    articles = load_articles(
        normalized_dates or None,
        force_raw=force_raw,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
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
    total_missing = 0
    total_failed = 0

    for i, article in enumerate(articles, 1):
        title = article.get("title", "")
        if not title or title == "广告":
            continue

        date_str = normalize_date(article.get("date") or (normalized_dates[0] if len(normalized_dates) == 1 else ""))
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print(f"  [{i}/{len(articles)}] 跳过日期异常文章: {title[:40]}")
            total_failed += 1
            continue

        try:
            duplicate = find_duplicate(article, indexes)
        except AmbiguousArticleMatch as exc:
            print(f"  [{i}/{len(articles)}] 身份待核对，未写入：{title[:40]}（{exc}）")
            total_failed += 1
            continue
        if duplicate and not update_existing:
            print(f"  [{i}/{len(articles)}] 已存在: {title[:40]}")
            total_skipped += 1
            continue

        if duplicate and update_existing:
            if dry_run:
                add_to_indexes(article, duplicate["id"], indexes)
                print(f"  [{i}/{len(articles)}] 将更新: {title[:40]}")
                total_updated += 1
                continue
            if metadata_only:
                ok = notion_api.update_page_metadata(duplicate["id"], article)
            else:
                ok = notion_api.update_page(duplicate["id"], article)
            if ok is False:
                print(f"  [{i}/{len(articles)}] 更新失败: {title[:40]}")
                total_failed += 1
            else:
                add_to_indexes(article, duplicate["id"], indexes)
                print(f"  [{i}/{len(articles)}] 更新成功: {title[:40]}")
                total_updated += 1
        else:
            if existing_only:
                print(f"  [{i}/{len(articles)}] Notion 未找到，跳过创建: {title[:40]}")
                total_missing += 1
                continue
            if dry_run:
                add_to_indexes(article, f"dry-run:{i}", indexes)
                print(f"  [{i}/{len(articles)}] 将新建: {title[:40]}")
                total_synced += 1
                continue
            page_id = notion_api.create_page(article, date)
            if page_id:
                print(f"  [{i}/{len(articles)}] 上传成功: {title[:40]}")
                add_to_indexes(article, page_id, indexes)
                total_synced += 1
            else:
                print(f"  [{i}/{len(articles)}] 上传失败: {title[:40]}")
                total_failed += 1

        if delay:
            time.sleep(delay)

    print(f"\n{'='*60}")
    print("  Notion 同步完成")
    print(f"     新增: {total_synced} 篇")
    print(f"     更新: {total_updated} 篇")
    print(f"     跳过: {total_skipped} 篇")
    if existing_only:
        print(f"     Notion 未找到: {total_missing} 篇")
    if total_failed:
        print(f"     失败: {total_failed} 篇")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="同步本地文章到 Notion")
    parser.add_argument("dates", nargs="*", help="日期，格式 YYYY-MM-DD；不填则同步今天")
    parser.add_argument("--all", action="store_true", help="同步核心库中的全部文章")
    parser.add_argument("--start", help="开始日期 YYYY-MM-DD")
    parser.add_argument("--end", help="结束日期 YYYY-MM-DD")
    parser.add_argument("--from-raw", action="store_true", help="强制读取旧 data/raw JSON")
    parser.add_argument("--update-existing", action="store_true", help="遇到已存在文章时更新 Notion 页面")
    parser.add_argument("--metadata-only", action="store_true", help="只更新 Notion 属性，不改页面正文")
    parser.add_argument("--existing-only", action="store_true", help="只更新已有页面，不创建新页面")
    parser.add_argument("--limit", type=int, help="限制处理文章数量，适合小批量试运行")
    parser.add_argument("--delay", type=float, default=0.35, help="每次写入后的等待秒数，默认 0.35")
    parser.add_argument("--dry-run", action="store_true", help="只预览将执行的操作，不写入 Notion")
    args = parser.parse_args()

    if (args.start or args.end) and not args.all:
        parser.error("按范围同步必须显式添加 --all；建议先加 --dry-run 预览")
    if args.all and (args.dates or args.from_raw):
        parser.error("--all 只用于核心库，不可与指定日期或 --from-raw 混用")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit 必须是正整数（文章篇数）")
    for value in [*args.dates, args.start, args.end]:
        if value is not None:
            try:
                normalized = normalize_date(value)
                if datetime.strptime(normalized, "%Y-%m-%d").date().isoformat() != normalized:
                    raise ValueError
            except ValueError:
                parser.error(f"无效日期：{value}，请使用 YYYY-MM-DD")
    start_date = normalize_date(args.start) if args.start else None
    end_date = normalize_date(args.end) if args.end else None
    if start_date and end_date and start_date > end_date:
        parser.error("开始日期不得晚于结束日期")
    dates = None if args.all else (args.dates or [datetime.now().strftime("%Y-%m-%d")])

    sync_articles(
        dates,
        force_raw=args.from_raw,
        update_existing=args.update_existing,
        metadata_only=args.metadata_only,
        existing_only=args.existing_only,
        start_date=start_date,
        end_date=end_date,
        limit=args.limit,
        delay=args.delay,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()

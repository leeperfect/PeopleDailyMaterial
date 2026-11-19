#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Maintain the People Daily Notion article database.

This script is intentionally conservative:
- archive only duplicate Notion pages whose Article ID already exists elsewhere;
- create only local articles that are not represented by Article ID, URL, or title+date;
- write only stable core properties on newly-created pages to avoid Notion
  schema-size failures from ever-growing select/multi-select options.
"""

import argparse
import os
import sys
import time
from datetime import date
from typing import Dict, List, Optional, Tuple


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from modules.article_database import DEFAULT_DB_PATH, ArticleStore
from modules.article_identity import normalize_date
from modules.notion import NotionAPI
from modules.notion_index import AmbiguousArticleMatch, build_existing_indexes, find_duplicate
from modules.utils import Config, setup_logger


def retry(label: str, func, attempts: int = 5, base_sleep: float = 2.0):
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            return func()
        except Exception as exc:  # Notion may raise APIResponseError or httpx errors.
            last_error = exc
            if attempt == attempts:
                raise
            sleep_for = base_sleep * attempt
            print(f"  {label} 失败，{sleep_for:.1f}s 后重试 ({attempt}/{attempts}): {exc}")
            time.sleep(sleep_for)
    raise last_error


def query_pages(notion_api: NotionAPI) -> List[Dict]:
    # 不使用工作区级搜索，也不把分页失败或多个数据源视为安全结果。
    return notion_api.get_existing_articles()


def load_local_articles(
    dates: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict]:
    store = ArticleStore(os.path.join(PROJECT_ROOT, DEFAULT_DB_PATH), read_only=True)
    try:
        articles = store.get_articles(
            dates=[normalize_date(d) for d in dates] if dates else None,
            start_date=normalize_date(start_date) if start_date else None,
            end_date=normalize_date(end_date) if end_date else None,
        )
    finally:
        store.close()
    return [a for a in articles if a.get("title") and a.get("title") != "广告"]


def article_url(article: Dict) -> str:
    return article.get("source_url") or article.get("url") or ""


def classify(pages: List[Dict], articles: List[Dict], assume_archived: Optional[set] = None, in_scope=None):
    assume_archived = assume_archived or set()
    active_pages = [p for p in pages if p["id"] not in assume_archived]
    by_url = {}
    for article in articles:
        url = article_url(article)
        if url:
            # 一个来源对应多个本地编号时不能安全归档旧页。
            by_url[url] = None if url in by_url else article

    filled_ids = {p["article_id"] for p in active_pages if p["article_id"]}
    duplicate_archive: List[Tuple[Dict, Dict]] = []
    unmatched_blank: List[Dict] = []

    for page in active_pages:
        if page["article_id"] or (in_scope and not in_scope(page)):
            continue
        article = by_url.get(page["url"])
        if article and article.get("article_id") in filled_ids:
            duplicate_archive.append((page, article))
        elif not article:
            unmatched_blank.append(page)

    planned_archives = {p["id"] for p, _ in duplicate_archive}
    remaining_pages = [p for p in active_pages if p["id"] not in planned_archives]
    indexes = build_existing_indexes(remaining_pages)
    missing_articles: List[Dict] = []
    needs_review = []
    for article in articles:
        try:
            if find_duplicate(article, indexes) is None:
                missing_articles.append(article)
        except AmbiguousArticleMatch as exc:
            needs_review.append((article, str(exc)))

    duplicate_ids = list(duplicate_id_groups(remaining_pages, in_scope))
    return {
        "duplicate_archive": duplicate_archive,
        "missing_articles": missing_articles,
        "needs_review": needs_review,
        "unmatched_blank": unmatched_blank,
        "duplicate_ids": duplicate_ids,
        "active_after_archive": remaining_pages,
    }


def minimal_properties(article: Dict) -> Dict:
    title = article.get("title", "").strip() or "无标题"
    properties = {
        "标题": {"title": [{"text": {"content": title}}]},
        "URL": {"url": article_url(article)},
        "Article ID": {"rich_text": [{"text": {"content": article.get("article_id", "")}}]},
    }

    if article.get("date"):
        properties["发布日期"] = {"date": {"start": article["date"]}}

    if article.get("series_name"):
        properties["系列"] = {"rich_text": [{"text": {"content": article["series_name"]}}]}
        if article.get("series_part") is not None:
            properties["系列序号"] = {"number": article["series_part"]}

    return properties


def duplicate_id_groups(pages: List[Dict], in_scope=None) -> Dict[str, List[Dict]]:
    groups: Dict[str, List[Dict]] = {}
    for page in pages:
        article_id = page.get("article_id")
        if not article_id:
            continue
        groups.setdefault(article_id, []).append(page)
    return {article_id: group for article_id, group in groups.items()
            if len(group) > 1 and (in_scope is None or all(in_scope(p) for p in group))}


def page_has_children(notion_api: NotionAPI, page_id: str) -> bool:
    response = retry(
        "检查重复页正文",
        lambda: notion_api.notion.blocks.children.list(block_id=page_id, page_size=1),
        attempts=3,
    )
    return bool(response.get("results"))


def duplicate_keep_score(notion_api: NotionAPI, page: Dict, article: Optional[Dict]) -> int:
    score = 0
    if article:
        if page.get("url") and page.get("url") == article_url(article):
            score += 4
        if page.get("title") and page.get("title") == article.get("title"):
            score += 2
        if page.get("date") and page.get("date") == article.get("date"):
            score += 1
    if page_has_children(notion_api, page["id"]):
        score += 8
    return score


def archive_duplicate_id_pages(notion_api: NotionAPI, pages: List[Dict], articles: List[Dict], limit: Optional[int] = None, in_scope=None) -> set:
    article_by_id = {article.get("article_id"): article for article in articles if article.get("article_id")}
    archived_ids = set()
    targets = []
    for article_id, group in duplicate_id_groups(pages, in_scope).items():
        if limit is not None and len(targets) >= limit:
            break
        article = article_by_id.get(article_id)
        ranked = sorted(
            group,
            key=lambda page: duplicate_keep_score(notion_api, page, article),
            reverse=True,
        )
        targets.extend(ranked[1:])

    if limit:
        targets = targets[:limit]

    for page in targets:
        archive_duplicate_page(notion_api, page)
        archived_ids.add(page["id"])
        print(f"  已归档重复 Article ID 页: {page.get('article_id')} {page.get('title', '')[:50]}")
    return archived_ids


def create_article_page(notion_api: NotionAPI, article: Dict) -> Optional[str]:
    # 不盲目重试新建：如对端成功但回执丢失，下次先按身份重新核对。
    # 裁剪属性以免不断扩张 select 选项，仍要求 Article ID 写入成功。
    source = notion_api._get_data_source_id()
    parent = {"data_source_id": source} if source else {"database_id": notion_api.database_id}
    page = notion_api.notion.pages.create(parent=parent, properties=minimal_properties(article),
                                         children=notion_api._body_blocks(article.get("content") or ""))
    return page["id"]


def archive_duplicate_page(notion_api: NotionAPI, page: Dict):
    retry(
        "归档 Notion 重复页",
        lambda: notion_api.notion.pages.update(page_id=page["id"], archived=True),
    )


def print_plan(plan: Dict, pages: List[Dict], articles: List[Dict]):
    print("当前盘点")
    print(f"  Notion 活跃页面: {len(pages)}")
    print(f"  本地有效文章: {len(articles)}")
    print(f"  将归档重复页: {len(plan['duplicate_archive'])}")
    print(f"  将新建缺失文章: {len(plan['missing_articles'])}")
    print(f"  空白且无法匹配页面: {len(plan['unmatched_blank'])}")
    print(f"  范围内重复 Article ID 组数: {len(plan['duplicate_ids'])}")
    print(f"  身份待人工核对（不新建）: {len(plan['needs_review'])}")
    for article, reason in plan['needs_review'][:5]:
        print(f"    {article.get('article_id')} {article.get('title', '')[:50]}：{reason}")
    if plan["duplicate_archive"]:
        print("  归档样例:")
        for page, article in plan["duplicate_archive"][:5]:
            print(f"    {page['date']} {page['title'][:60]} -> {article.get('article_id')}")
    if plan["missing_articles"]:
        print("  新建样例:")
        for article in plan["missing_articles"][:5]:
            print(f"    {article.get('date')} {article.get('title', '')[:60]} -> {article.get('article_id')}")


def main():
    parser = argparse.ArgumentParser(description="Clean duplicate Notion pages and create missing local articles.")
    parser.add_argument("--archive-duplicates", action="store_true", help="Archive duplicate blank pages whose Article ID exists elsewhere.")
    parser.add_argument("--create-missing", action="store_true", help="Create local articles missing from Notion.")
    parser.add_argument("--dry-run", action="store_true", help="Only print the plan.")
    parser.add_argument("--limit", type=int, default=None, help="Limit pages/articles changed, useful for testing.")
    parser.add_argument("--delay", type=float, default=0.35, help="Delay between Notion writes.")
    parser.add_argument("--date", action="append", help="Only maintain one date, format YYYY-MM-DD. Can be used more than once.")
    parser.add_argument("--start", help="Only maintain articles on or after this date, format YYYY-MM-DD.")
    parser.add_argument("--end", help="Only maintain articles on or before this date, format YYYY-MM-DD.")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit 必须是正整数（整次维护的页数上限）")
    dates = {normalize_date(d) for d in args.date or []}
    start, end = normalize_date(args.start), normalize_date(args.end)
    for value in [*dates, start, end]:
        if value:
            try:
                if date.fromisoformat(value).isoformat() != value:
                    raise ValueError
            except ValueError:
                parser.error(f"无效日期：{value}，请使用 YYYY-MM-DD")
    if start and end and start > end:
        parser.error("开始日期不得晚于结束日期")

    def in_scope(page):
        day = page.get("date") or ""
        if not (dates or start or end):
            return True
        return bool(day and (not dates or day in dates) and (not start or start <= day) and (not end or day <= end))

    config = Config()
    setup_logger(config)
    notion_api = NotionAPI(config)

    pages = query_pages(notion_api)
    articles = load_local_articles(dates=args.date, start_date=args.start, end_date=args.end)
    if args.date or args.start or args.end:
        scope = ", ".join(args.date or []) or f"{args.start or '最早'} ~ {args.end or '最新'}"
        print(f"本次只维护日期范围: {scope}")
    plan = classify(pages, articles, in_scope=in_scope)
    print_plan(plan, pages, articles)

    if args.dry_run or (not args.archive_duplicates and not args.create_missing):
        print("dry-run 完成，未写入 Notion。")
        return

    archived_ids = set()
    archived_count = 0
    attempts = 0
    if args.archive_duplicates:
        duplicate_id_archived_ids = archive_duplicate_id_pages(notion_api, pages, articles, args.limit, in_scope)
        archived_ids.update(duplicate_id_archived_ids)
        archived_count += len(duplicate_id_archived_ids)

        attempts += len(duplicate_id_archived_ids)
        archive_targets = plan["duplicate_archive"][:None if args.limit is None else args.limit - attempts]
        for index, (page, article) in enumerate(archive_targets, 1):
            attempts += 1
            try:
                archive_duplicate_page(notion_api, page)
                archived_ids.add(page["id"])
                archived_count += 1
                if index == 1 or index % 10 == 0:
                    print(f"  已归档 {index}/{len(archive_targets)}: {page['title'][:50]}")
            except Exception as exc:
                print(f"  归档失败: {page['id']} {page['title'][:50]} ({exc})")
            time.sleep(args.delay)

    # Reclassify against the in-memory page set so missing creation accounts for archived pages.
    refreshed_plan = classify(pages, articles, assume_archived=archived_ids, in_scope=in_scope) if archived_ids else plan
    create_targets = refreshed_plan["missing_articles"][:None if args.limit is None else args.limit - attempts]
    created_count = 0
    failed_create = 0
    if args.create_missing:
        for index, article in enumerate(create_targets, 1):
            try:
                create_article_page(notion_api, article)
                created_count += 1
                if index == 1 or index % 10 == 0:
                    print(f"  已新建 {index}/{len(create_targets)}: {article.get('title', '')[:50]}")
            except Exception as exc:
                failed_create += 1
                print(f"  新建失败: {article.get('date')} {article.get('title', '')[:50]} ({exc})")
            time.sleep(args.delay)

    print("维护完成")
    print(f"  归档重复页: {archived_count}")
    print(f"  新建文章: {created_count}")
    print(f"  新建失败: {failed_create}")


if __name__ == "__main__":
    main()

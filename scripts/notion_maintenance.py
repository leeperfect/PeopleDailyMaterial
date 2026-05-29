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
from collections import Counter
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple

from notion_client.errors import APIResponseError

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from modules.article_database import DEFAULT_DB_PATH, ArticleStore
from modules.article_identity import normalize_date
from modules.notion import NotionAPI
from modules.utils import Config, setup_logger


MAX_TEXT = 1900
MAX_BLOCKS = 90


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


def chunks(text: str, size: int = MAX_TEXT) -> Iterable[str]:
    for i in range(0, len(text), size):
        yield text[i : i + size]


def paragraph_blocks(content: str) -> List[Dict]:
    blocks: List[Dict] = []
    for paragraph in content.split("\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        for piece in chunks(paragraph):
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": piece},
                            }
                        ]
                    },
                }
            )
    if not blocks:
        blocks.append(
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "无内容"},
                        }
                    ]
                },
            }
        )
    return blocks


def page_title(page: Dict) -> str:
    props = page.get("properties", {})
    return "".join(x.get("plain_text", "") for x in props.get("标题", {}).get("title", []))


def page_record(notion_api: NotionAPI, page: Dict) -> Dict:
    props = page.get("properties", {})
    return {
        "id": page.get("id"),
        "title": page_title(page),
        "article_id": notion_api._rich_text_plain(props, "Article ID", "文章ID"),
        "url": (props.get("URL") or {}).get("url", ""),
        "date": notion_api._date_start(props, "发布日期"),
        "archived": page.get("archived", False),
    }


def get_data_source_id(notion_api: NotionAPI) -> str:
    database = retry(
        "获取 Notion data source",
        lambda: notion_api.notion.databases.retrieve(database_id=notion_api.database_id),
    )
    data_sources = database.get("data_sources") or []
    if not data_sources:
        raise RuntimeError("Notion database response does not include data_sources")
    return data_sources[0]["id"]


def query_pages(notion_api: NotionAPI) -> List[Dict]:
    data_source_id = get_data_source_id(notion_api)
    pages: List[Dict] = []
    cursor: Optional[str] = None
    while True:
        response = retry(
            "查询 Notion 页面",
            lambda: notion_api.notion.data_sources.query(
                data_source_id=data_source_id,
                start_cursor=cursor,
                page_size=100,
            ),
        )
        pages.extend(page_record(notion_api, page) for page in response.get("results", []))
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")
    return pages


def load_local_articles(
    dates: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict]:
    store = ArticleStore(os.path.join(PROJECT_ROOT, DEFAULT_DB_PATH))
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


def classify(pages: List[Dict], articles: List[Dict], assume_archived: Optional[set] = None):
    assume_archived = assume_archived or set()
    active_pages = [p for p in pages if p["id"] not in assume_archived]
    by_url = {article_url(a): a for a in articles if article_url(a)}
    by_title_date = {(a.get("title", ""), a.get("date", "")): a for a in articles if a.get("title") and a.get("date")}

    filled_ids = {p["article_id"] for p in active_pages if p["article_id"]}
    duplicate_archive: List[Tuple[Dict, Dict]] = []
    unmatched_blank: List[Dict] = []

    for page in active_pages:
        if page["article_id"]:
            continue
        article = by_url.get(page["url"]) or by_title_date.get((page["title"], page["date"]))
        if article and article.get("article_id") in filled_ids:
            duplicate_archive.append((page, article))
        elif not article:
            unmatched_blank.append(page)

    remaining_pages = [p for p in active_pages if p["id"] not in {p["id"] for p, _ in duplicate_archive}]
    existing_ids = {p["article_id"] for p in remaining_pages if p["article_id"]}
    existing_urls = {p["url"] for p in remaining_pages if p["url"]}
    existing_title_dates = {(p["title"], p["date"]) for p in remaining_pages if p["title"] and p["date"]}

    missing_articles: List[Dict] = []
    for article in articles:
        article_id = article.get("article_id")
        url = article_url(article)
        title_date = (article.get("title", ""), article.get("date", ""))
        if article_id in existing_ids:
            continue
        if url and url in existing_urls:
            continue
        if title_date in existing_title_dates:
            continue
        missing_articles.append(article)

    duplicate_ids = [article_id for article_id, count in Counter(p["article_id"] for p in remaining_pages if p["article_id"]).items() if count > 1]
    return {
        "duplicate_archive": duplicate_archive,
        "missing_articles": missing_articles,
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


def duplicate_id_groups(pages: List[Dict]) -> Dict[str, List[Dict]]:
    groups: Dict[str, List[Dict]] = {}
    for page in pages:
        article_id = page.get("article_id")
        if not article_id:
            continue
        groups.setdefault(article_id, []).append(page)
    return {article_id: group for article_id, group in groups.items() if len(group) > 1}


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


def archive_duplicate_id_pages(notion_api: NotionAPI, pages: List[Dict], articles: List[Dict], limit: Optional[int] = None) -> set:
    article_by_id = {article.get("article_id"): article for article in articles if article.get("article_id")}
    archived_ids = set()
    targets = []
    for article_id, group in duplicate_id_groups(pages).items():
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
    properties = minimal_properties(article)

    page = retry(
        "创建 Notion 页面",
        lambda: notion_api.notion.pages.create(
            parent={"database_id": notion_api.database_id},
            properties=properties,
        ),
    )
    page_id = page.get("id")
    blocks = paragraph_blocks(article.get("content", ""))
    for i in range(0, len(blocks), MAX_BLOCKS):
        batch = blocks[i : i + MAX_BLOCKS]
        retry(
            "写入 Notion 正文",
            lambda batch=batch: notion_api.notion.blocks.children.append(
                block_id=page_id,
                children=batch,
            ),
        )
    return page_id


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
    print(f"  已存在重复 Article ID: {len(plan['duplicate_ids'])}")
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

    config = Config()
    setup_logger(config)
    notion_api = NotionAPI(config)

    pages = query_pages(notion_api)
    articles = load_local_articles(dates=args.date, start_date=args.start, end_date=args.end)
    if args.date or args.start or args.end:
        scope = ", ".join(args.date or []) or f"{args.start or '最早'} ~ {args.end or '最新'}"
        print(f"本次只维护日期范围: {scope}")
    plan = classify(pages, articles)
    print_plan(plan, pages, articles)

    if args.dry_run or (not args.archive_duplicates and not args.create_missing):
        print("dry-run 完成，未写入 Notion。")
        return

    archived_ids = set()
    archived_count = 0
    archive_targets = plan["duplicate_archive"][: args.limit] if args.limit else plan["duplicate_archive"]
    if args.archive_duplicates:
        duplicate_id_archived_ids = archive_duplicate_id_pages(notion_api, pages, articles, args.limit)
        archived_ids.update(duplicate_id_archived_ids)
        archived_count += len(duplicate_id_archived_ids)

        for index, (page, article) in enumerate(archive_targets, 1):
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
    refreshed_plan = classify(pages, articles, assume_archived=archived_ids)
    create_targets = refreshed_plan["missing_articles"][: args.limit] if args.limit else refreshed_plan["missing_articles"]
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

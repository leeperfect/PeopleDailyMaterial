#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步人民日报 APP 评论库到独立 Notion 数据库。

只读取 data/peopleapp_opinion/core/articles.sqlite，只写入
notion.peopleapp_opinion_database_id 指向的 Notion 数据库。
"""

import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from notion_client import Client
from notion_client.errors import APIResponseError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SCRIPTS_ROOT))

from create_peopleapp_opinion_notion_database import DEFAULT_TITLE, ensure_peopleapp_opinion_database
from modules.article_identity import normalize_date
from modules.peopleapp_opinion import DB_PATH, EXPORT_DIR, TIMEZONE, load_articles
from modules.utils import Config

CONFIG_PATH = PROJECT_ROOT / "config.json"
REPORT_PREFIX = "peopleapp_opinion_notion_sync"


def rich_text(value: object, limit: int = 2000) -> Dict:
    text = str(value or "").strip()
    return {"rich_text": [{"text": {"content": text[:limit]}}]} if text else {"rich_text": []}


def title_property(value: object) -> Dict:
    text = str(value or "无标题").strip() or "无标题"
    return {"title": [{"text": {"content": text[:2000]}}]}


def option_name(value: object, fallback: str = "其他") -> str:
    text = str(value or "").strip()
    return (text or fallback)[:100]


def select_property(value: object, fallback: str = "其他") -> Dict:
    return {"select": {"name": option_name(value, fallback=fallback)}}


def date_property(value: object) -> Dict:
    text = str(value or "").strip()
    return {"date": {"start": text}} if text else {"date": None}


def keyword_property(keywords: Iterable[str]) -> Dict:
    options = []
    seen = set()
    for keyword in keywords or []:
        name = option_name(keyword, fallback="")
        if not name or name in seen:
            continue
        options.append({"name": name})
        seen.add(name)
        if len(options) >= 10:
            break
    return {"multi_select": options}


def article_properties(article: Dict, status: str = "已同步", title_name: str = "标题") -> Dict:
    return {
        title_name: title_property(article.get("title")),
        "Article ID": rich_text(article.get("article_id")),
        "Content ID": rich_text(article.get("content_id")),
        "Rel ID": rich_text(article.get("rel_id")),
        "发布日期": date_property(article.get("date")),
        "作者": rich_text(article.get("author")),
        "来源": select_property(article.get("source_name"), fallback="其他"),
        "栏目": select_property(article.get("section_name") or article.get("plate"), fallback="APP-锐评"),
        "URL": {"url": article.get("source_url") or article.get("url") or None},
        "摘要": rich_text(article.get("summary")),
        "关键词": keyword_property(article.get("keywords") or []),
        "正文字数": {"number": int(article.get("word_count") or len(article.get("content") or ""))},
        "同步时间": {"date": {"start": datetime.now(TIMEZONE).isoformat(timespec="seconds")}},
        "采集状态": select_property(status, fallback="已同步"),
    }


def plain_rich_text(properties: Dict, name: str) -> str:
    rich_items = (properties.get(name) or {}).get("rich_text") or []
    return "".join(item.get("plain_text", "") for item in rich_items)


def plain_title(properties: Dict, name: str = "标题") -> str:
    title_items = (properties.get(name) or {}).get("title") or []
    return "".join(item.get("plain_text", "") for item in title_items)


def get_data_source_id(notion: Client, database_id: str) -> Optional[str]:
    try:
        database = notion.databases.retrieve(database_id=database_id)
    except Exception:
        return None
    data_sources = database.get("data_sources") or []
    if data_sources:
        return data_sources[0].get("id")
    return None


def find_title_property_name(notion: Client, database_id: str, data_source_id: Optional[str]) -> str:
    try:
        if data_source_id and hasattr(notion, "data_sources"):
            schema = notion.data_sources.retrieve(data_source_id=data_source_id)
        else:
            schema = notion.databases.retrieve(database_id=database_id)
        for name, prop in (schema.get("properties") or {}).items():
            if prop.get("type") == "title":
                return name
    except Exception:
        pass
    return "标题"


def query_database_pages(notion: Client, database_id: str, data_source_id: Optional[str]) -> List[Dict]:
    pages: List[Dict] = []
    start_cursor = None
    has_more = True
    while has_more:
        if data_source_id and hasattr(notion, "data_sources"):
            response = notion.data_sources.query(
                data_source_id=data_source_id,
                start_cursor=start_cursor,
                page_size=100,
            )
        else:
            response = notion.databases.query(
                database_id=database_id,
                start_cursor=start_cursor,
                page_size=100,
            )
        pages.extend(response.get("results") or [])
        has_more = response.get("has_more", False)
        start_cursor = response.get("next_cursor")
    return pages


def build_existing_index(notion: Client, database_id: str, data_source_id: Optional[str]) -> Dict[str, Dict]:
    existing: Dict[str, Dict] = {}
    for page in query_database_pages(notion, database_id, data_source_id):
        props = page.get("properties") or {}
        article_id = plain_rich_text(props, "Article ID")
        if article_id:
            existing[article_id] = {
                "id": page.get("id"),
                "article_id": article_id,
                "title": plain_title(props),
            }
    return existing


def split_text(text: str, size: int = 1800) -> List[str]:
    text = str(text or "").strip()
    if not text:
        return []
    chunks = []
    while text:
        if len(text) <= size:
            chunks.append(text)
            break
        cut = text.rfind("。", 0, size)
        if cut < size // 2:
            cut = text.rfind("\n", 0, size)
        if cut < size // 2:
            cut = size
        chunks.append(text[: cut + 1].strip())
        text = text[cut + 1 :].strip()
    return [chunk for chunk in chunks if chunk]


def paragraph_block(text: str) -> Dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]},
    }


def build_page_blocks(article: Dict) -> List[Dict]:
    blocks: List[Dict] = []
    summary = str(article.get("summary") or "").strip()
    if summary:
        blocks.append(paragraph_block(f"摘要：{summary}"))

    content = str(article.get("content") or "").strip()
    for paragraph in content.splitlines():
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        for chunk in split_text(paragraph):
            blocks.append(paragraph_block(chunk))

    source_url = article.get("source_url") or article.get("url") or ""
    if source_url:
        blocks.append(paragraph_block(f"原文链接：{source_url}"))
    return blocks


def append_blocks(notion: Client, page_id: str, blocks: List[Dict]) -> None:
    for start in range(0, len(blocks), 100):
        notion.blocks.children.append(block_id=page_id, children=blocks[start : start + 100])


def create_page(notion: Client, database_id: str, article: Dict, title_name: str) -> str:
    page = notion.pages.create(
        parent={"database_id": database_id},
        properties=article_properties(article, title_name=title_name),
    )
    blocks = build_page_blocks(article)
    if blocks:
        append_blocks(notion, page["id"], blocks)
    return page["id"]


def update_page(notion: Client, page_id: str, article: Dict, title_name: str) -> None:
    notion.pages.update(page_id=page_id, properties=article_properties(article, title_name=title_name))


def default_range(days: int) -> tuple[str, str]:
    today = datetime.now(TIMEZONE).date()
    start = today - timedelta(days=max(1, days) - 1)
    return start.isoformat(), today.isoformat()


def select_articles(args) -> List[Dict]:
    if args.all:
        return load_articles(limit=args.limit)
    if args.date:
        dates = [normalize_date(value) for value in args.date]
        return load_articles(dates=dates, limit=args.limit)
    start = normalize_date(args.start) if args.start else None
    end = normalize_date(args.end) if args.end else None
    if not start and not end:
        start, end = default_range(args.days)
    return load_articles(start_date=start, end_date=end, limit=args.limit)


def save_sync_report(report: Dict) -> Path:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(TIMEZONE).strftime("%Y%m%d_%H%M%S")
    path = EXPORT_DIR / f"{REPORT_PREFIX}_{timestamp}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def sync_peopleapp_opinion_to_notion(args) -> Dict:
    config = Config(str(CONFIG_PATH))
    token = config.get("notion.token")
    database_id = config.get("notion.peopleapp_opinion_database_id")

    if not token:
        raise SystemExit("config.json 缺少 notion.token，无法同步 Notion。")
    if not database_id:
        if args.create_database_if_missing and not args.dry_run:
            created = ensure_peopleapp_opinion_database(title=DEFAULT_TITLE)
            database_id = created["database"]["id"]
        else:
            raise SystemExit(
                "config.json 缺少 notion.peopleapp_opinion_database_id。"
                "请先运行 scripts/create_peopleapp_opinion_notion_database.py。"
            )

    articles = select_articles(args)
    report = {
        "source": "peopleapp_opinion",
        "database_id": database_id,
        "db_path": str(DB_PATH.relative_to(PROJECT_ROOT)),
        "generated_at": datetime.now(TIMEZONE).isoformat(timespec="seconds"),
        "candidate_count": len(articles),
        "created": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "failures": [],
        "dry_run": args.dry_run,
    }

    print("人民日报 APP 评论库同步到 Notion")
    print(f"本地库：{DB_PATH.relative_to(PROJECT_ROOT)}")
    print(f"候选文章：{len(articles)}")
    if args.dry_run:
        print("运行模式：dry-run，只预览不写入")

    if not articles:
        return report

    notion = Client(auth=token)
    data_source_id = get_data_source_id(notion, database_id)
    title_name = find_title_property_name(notion, database_id, data_source_id)
    existing_index = build_existing_index(notion, database_id, data_source_id) if not args.dry_run else {}
    print(f"Notion 已有 APP 评论文章：{len(existing_index)}")

    for index, article in enumerate(articles, 1):
        title = article.get("title", "无标题")
        article_id = article.get("article_id", "")
        try:
            existing = existing_index.get(article_id)
            if existing and not args.update_existing:
                report["skipped"] += 1
                print(f"[{index}/{len(articles)}] 已存在：{title[:40]}")
                continue

            if args.dry_run:
                action = "更新" if existing else "新建"
                print(f"[{index}/{len(articles)}] 将{action}：{title[:40]}")
                if existing:
                    report["updated"] += 1
                else:
                    report["created"] += 1
                continue

            if existing:
                update_page(notion, existing["id"], article, title_name)
                report["updated"] += 1
                print(f"[{index}/{len(articles)}] 更新成功：{title[:40]}")
            else:
                page_id = create_page(notion, database_id, article, title_name)
                existing_index[article_id] = {"id": page_id, "article_id": article_id, "title": title}
                report["created"] += 1
                print(f"[{index}/{len(articles)}] 上传成功：{title[:40]}")

            if args.delay:
                time.sleep(args.delay)
        except APIResponseError as exc:
            report["failed"] += 1
            report["failures"].append(
                {"article_id": article_id, "title": title, "error": str(exc), "url": article.get("source_url", "")}
            )
            print(f"[{index}/{len(articles)}] 同步失败：{title[:40]} ({exc})")
        except Exception as exc:
            report["failed"] += 1
            report["failures"].append(
                {"article_id": article_id, "title": title, "error": str(exc), "url": article.get("source_url", "")}
            )
            print(f"[{index}/{len(articles)}] 同步失败：{title[:40]} ({exc})")

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="同步人民日报 APP 评论库到独立 Notion 数据库")
    parser.add_argument("--days", type=int, default=3, help="默认同步最近几天，默认 3 天")
    parser.add_argument("--date", action="append", help="指定日期 YYYY-MM-DD，可重复传入")
    parser.add_argument("--start", help="开始日期 YYYY-MM-DD")
    parser.add_argument("--end", help="结束日期 YYYY-MM-DD")
    parser.add_argument("--all", action="store_true", help="同步 APP 评论库全部文章")
    parser.add_argument("--limit", type=int, help="限制处理文章数量")
    parser.add_argument("--update-existing", action="store_true", help="Article ID 已存在时更新 Notion 属性")
    parser.add_argument("--create-database-if-missing", action="store_true", help="配置缺失时自动创建独立 Notion 数据库")
    parser.add_argument("--delay", type=float, default=0.35, help="写入 Notion 后等待秒数，默认 0.35")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不写入 Notion")
    args = parser.parse_args()

    report = sync_peopleapp_opinion_to_notion(args)
    report_path = save_sync_report(report)

    print("\nNotion 同步完成")
    print(f"新增：{report['created']}")
    print(f"更新：{report['updated']}")
    print(f"跳过重复：{report['skipped']}")
    print(f"失败：{report['failed']}")
    print(f"同步报告：{report_path.relative_to(PROJECT_ROOT)}")
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

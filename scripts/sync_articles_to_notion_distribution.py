#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 data/articles 中的新文章同步到 Notion 自媒体内容分发中枢。

- 内容库：一篇本地文章一条内容记录。
- 分发记录：一篇内容按 8 个发布目标生成 8 条分发记录。
- 已存在的内容和分发记录不会重复创建，也不会覆盖发布状态、发布时间、发布链接。
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Dict, List

from notion_client import Client

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.utils import Config
from scripts.create_notion_distribution_database import load_articles


DEFAULT_CONTENT_DATA_SOURCE_ID = "b250937a-59fe-4bb4-8f83-ba121aa8fd90"
DEFAULT_DISTRIBUTION_DATA_SOURCE_ID = "b66f483b-4b60-450d-ab39-feeade6bcee4"
PUBLISHING_TARGETS = [
    {"platform": "公众号", "format": "文章", "legacy_title": True},
    {"platform": "公众号", "format": "图文", "legacy_title": False},
    {"platform": "视频号", "format": "视频", "legacy_title": True},
    {"platform": "小红书", "format": "图文", "legacy_title": True},
    {"platform": "小红书", "format": "视频", "legacy_title": False},
    {"platform": "抖音", "format": "视频", "legacy_title": True},
    {"platform": "快手", "format": "视频", "legacy_title": True},
    {"platform": "微博", "format": "图文", "legacy_title": True},
]


def title_property(value: str) -> Dict:
    return {"title": [{"text": {"content": value[:2000]}}]}


def rich_text_property(value: str) -> Dict:
    if not value:
        return {"rich_text": []}
    return {"rich_text": [{"text": {"content": value[:2000]}}]}


def plain_title(properties: Dict, name: str) -> str:
    return "".join(item.get("plain_text", "") for item in (properties.get(name) or {}).get("title", []))


def query_all(notion: Client, data_source_id: str) -> List[Dict]:
    rows = []
    start_cursor = None
    has_more = True
    while has_more:
        response = notion.data_sources.query(
            data_source_id=data_source_id,
            start_cursor=start_cursor,
            page_size=100,
        )
        rows.extend(response.get("results", []))
        has_more = response.get("has_more", False)
        start_cursor = response.get("next_cursor")
    return rows


def build_content_index(notion: Client, content_data_source_id: str) -> Dict[str, str]:
    index = {}
    for page in query_all(notion, content_data_source_id):
        title = plain_title(page.get("properties") or {}, "内容标题")
        if title:
            index[title] = page["id"]
    return index


def build_distribution_index(notion: Client, distribution_data_source_id: str) -> Dict[str, Dict]:
    index = {}
    for page in query_all(notion, distribution_data_source_id):
        title = plain_title(page.get("properties") or {}, "记录标题")
        if title:
            index[title] = page
    return index


def enrich_content_index_from_distribution(content_index: Dict[str, str], distribution_index: Dict[str, Dict]):
    for record_title, page in distribution_index.items():
        if "｜" not in record_title:
            continue
        content_title = content_title_from_record(record_title)
        if content_title in content_index:
            continue
        relation = ((page.get("properties") or {}).get("关联内容") or {}).get("relation") or []
        if relation:
            content_index[content_title] = relation[0]["id"]


def article_note(article: Dict) -> str:
    local_path = str(article["path"].relative_to(PROJECT_ROOT))
    parts = []
    if article.get("topic"):
        parts.append(f"主题：{article['topic']}")
    parts.append(f"本地正文：{local_path}")
    parts.append(f"来源目录：{article.get('source_dir', '')}")
    parts.append(f"字数估算：{article.get('word_count', 0)}")
    return "；".join(parts)


def make_record_title(article_title: str, target: Dict) -> str:
    if target.get("legacy_title"):
        return f"{article_title}｜{target['platform']}"
    return f"{article_title}｜{target['platform']}｜{target['format']}"


def content_title_from_record(record_title_value: str) -> str:
    parts = record_title_value.rsplit("｜", 2)
    if len(parts) >= 2 and parts[-1] in {"文章", "图文", "视频"}:
        return parts[0]
    if "｜" in record_title_value:
        return record_title_value.rsplit("｜", 1)[0]
    return record_title_value


def create_content_page(notion: Client, data_source_id: str, article: Dict) -> str:
    properties = {
        "内容标题": title_property(article["title"]),
        "内容形式": {"multi_select": [{"name": "文章"}]},
        "选题分类": {"multi_select": [{"name": "时政热点"}, {"name": "申论"}]},
        "制作状态": {"status": {"name": "待分发"}},
        "内容摘要/备注": rich_text_property(article_note(article)),
    }
    if article.get("date"):
        properties["创作日期"] = {"date": {"start": article["date"]}}
    page = notion.pages.create(parent={"data_source_id": data_source_id}, properties=properties)
    return page["id"]


def create_distribution_page(
    notion: Client,
    data_source_id: str,
    article: Dict,
    target: Dict,
    content_page_id: str,
) -> str:
    local_path = str(article["path"].relative_to(PROJECT_ROOT))
    title = make_record_title(article["title"], target)
    properties = {
        "记录标题": title_property(title),
        "平台": {"select": {"name": target["platform"]}},
        "发布形式": {"select": {"name": target["format"]}},
        "发布状态": {"status": {"name": "待发布"}},
        "关联内容": {"relation": [{"id": content_page_id}]},
        "备注": rich_text_property(f"自动同步；本地正文：{local_path}"),
    }
    page = notion.pages.create(parent={"data_source_id": data_source_id}, properties=properties)
    return page["id"]


def sync(dry_run: bool, delay: float, content_data_source_id: str, distribution_data_source_id: str):
    articles = load_articles()
    notion = Client(auth=Config().get("notion.token"))
    content_index = build_content_index(notion, content_data_source_id)
    distribution_index = build_distribution_index(notion, distribution_data_source_id)
    enrich_content_index_from_distribution(content_index, distribution_index)

    planned_content = [article for article in articles if article["title"] not in content_index]
    planned_distribution = []
    for article in articles:
        for target in PUBLISHING_TARGETS:
            title = make_record_title(article["title"], target)
            if title not in distribution_index:
                planned_distribution.append((article, target, title))

    print(f"本地文章总数：{len(articles)}")
    print(f"待新增内容库记录：{len(planned_content)}")
    print(f"待新增分发记录：{len(planned_distribution)}")

    if dry_run:
        print("dry-run：只预览，不写入 Notion")
        for article in planned_content[:10]:
            print(f"- 内容库：{article['title']}")
        for _, _, record_title in planned_distribution[:10]:
            print(f"- 分发记录：{record_title}")
        return

    created_content = 0
    created_distribution = 0
    for article in articles:
        content_page_id = content_index.get(article["title"])
        if not content_page_id:
            content_page_id = create_content_page(notion, content_data_source_id, article)
            content_index[article["title"]] = content_page_id
            created_content += 1
            time.sleep(delay)

        related_distribution_ids = []
        for target in PUBLISHING_TARGETS:
            title = make_record_title(article["title"], target)
            distribution_page = distribution_index.get(title)
            distribution_page_id = distribution_page["id"] if distribution_page else None
            if not distribution_page_id:
                distribution_page_id = create_distribution_page(
                    notion,
                    distribution_data_source_id,
                    article,
                    target,
                    content_page_id,
                )
                distribution_index[title] = {"id": distribution_page_id}
                created_distribution += 1
                time.sleep(delay)
            related_distribution_ids.append({"id": distribution_page_id})

        notion.pages.update(
            page_id=content_page_id,
            properties={"分发记录": {"relation": related_distribution_ids}},
        )
        time.sleep(delay)

    print(f"新增内容库记录：{created_content}")
    print(f"新增分发记录：{created_distribution}")
    print("同步完成。")


def main():
    parser = argparse.ArgumentParser(description="同步本地成稿到 Notion 自媒体内容分发中枢")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不写入 Notion")
    parser.add_argument("--delay", type=float, default=0.25, help="每次写入之间的间隔秒数")
    parser.add_argument("--content-data-source-id", default=DEFAULT_CONTENT_DATA_SOURCE_ID)
    parser.add_argument("--distribution-data-source-id", default=DEFAULT_DISTRIBUTION_DATA_SOURCE_ID)
    args = parser.parse_args()
    sync(args.dry_run, args.delay, args.content_data_source_id, args.distribution_data_source_id)


if __name__ == "__main__":
    main()

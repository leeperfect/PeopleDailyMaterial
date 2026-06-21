#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建 Notion 自媒体内容分发台账。

用途：
1. 在现有 Notion 文章库所在页面旁边，新建一个“自媒体内容分发台账”数据库；
2. 扫描 data/articles 下的成稿文章；
3. 按平台初始化分发记录，方便后续核对、排期和批量发布。
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from notion_client import Client

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.utils import Config


ARTICLES_ROOT = PROJECT_ROOT / "data" / "articles"
EXPORT_PATH = PROJECT_ROOT / "data" / "exports" / "notion_distribution_database.json"

PLATFORMS = ["公众号", "视频号", "小红书", "抖音", "快手", "微博"]
DEFAULT_FORMAT = {
    "公众号": "文章",
    "视频号": "视频",
    "小红书": "图文",
    "抖音": "视频",
    "快手": "视频",
    "微博": "图文",
}
SKIP_FILENAMES = {"文章索引.md", "选题库.md", "选题库-精筛说明.md"}


def notion_color(index: int) -> str:
    colors = [
        "blue",
        "green",
        "red",
        "orange",
        "purple",
        "pink",
        "yellow",
        "gray",
        "brown",
    ]
    return colors[index % len(colors)]


def select_options(names: Iterable[str]) -> List[Dict]:
    return [{"name": name, "color": notion_color(i)} for i, name in enumerate(names)]


def database_properties() -> Dict:
    return {
        "记录名称": {"title": {}},
        "内容标题": {"rich_text": {}},
        "内容ID": {"rich_text": {}},
        "平台": {"select": {"options": select_options(PLATFORMS)}},
        "内容形式": {
            "select": {
                "options": select_options(
                    ["文章", "图文", "视频", "短视频", "直播回放", "未定"]
                )
            }
        },
        "分发状态": {
            "select": {
                "options": select_options(
                    ["待确认", "待改稿", "待配图", "待剪辑", "待发布", "已发布", "不分发", "已归档"]
                )
            }
        },
        "计划发布时间": {"date": {}},
        "实际发布时间": {"date": {}},
        "发布链接": {"url": {}},
        "账号": {"rich_text": {}},
        "主题": {"rich_text": {}},
        "来源目录": {"select": {"options": select_options(["公众号文章", "往期文章", "其他"])}},
        "本地正文路径": {"rich_text": {}},
        "素材包路径": {"rich_text": {}},
        "字数": {"number": {"format": "number"}},
        "是否需要改写": {"checkbox": {}},
        "是否已核对链接": {"checkbox": {}},
        "备注": {"rich_text": {}},
        "创建时间": {"created_time": {}},
        "最近编辑": {"last_edited_time": {}},
    }


def parse_frontmatter(text: str) -> Dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    frontmatter = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip().strip('"').strip("'")
    return frontmatter


def extract_h1(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def clean_title_from_filename(path: Path) -> str:
    title = path.stem
    title = re.sub(r"^\d+\s*[-｜|]\s*", "", title)
    return title.strip()


def content_key(title: str) -> str:
    key = re.sub(r"^\d+\s*[-｜|]\s*", "", title)
    key = key.replace("｜", "|")
    key = re.sub(r"\s+", "", key)
    return key


def content_id(path: Path, title: str) -> str:
    source = f"{path.relative_to(PROJECT_ROOT)}::{title}"
    digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:10]
    return f"media-{digest}"


def count_words(text: str) -> int:
    text_without_frontmatter = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)
    chinese_chars = re.findall(r"[\u4e00-\u9fff]", text_without_frontmatter)
    latin_words = re.findall(r"[A-Za-z0-9]+", text_without_frontmatter)
    return len(chinese_chars) + len(latin_words)


def load_articles() -> List[Dict]:
    candidates: List[Dict] = []
    for path in sorted(ARTICLES_ROOT.glob("*/*.md")):
        if path.name in SKIP_FILENAMES:
            continue
        text = path.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(text)
        title = frontmatter.get("title") or extract_h1(text) or clean_title_from_filename(path)
        topic = frontmatter.get("topic") or ""
        source_dir = path.parent.name if path.parent.name in {"公众号文章", "往期文章"} else "其他"
        candidates.append(
            {
                "title": title,
                "key": content_key(title),
                "topic": topic,
                "source_dir": source_dir,
                "path": path,
                "word_count": count_words(text),
            }
        )

    # 同名内容优先保留“公众号文章”目录中的成稿版本。
    priority = {"公众号文章": 0, "往期文章": 1, "其他": 2}
    deduped: Dict[str, Dict] = {}
    for item in candidates:
        existing = deduped.get(item["key"])
        if not existing or priority[item["source_dir"]] < priority[existing["source_dir"]]:
            deduped[item["key"]] = item
    return sorted(deduped.values(), key=lambda item: (item["source_dir"], item["title"]))


def text_property(value: str) -> Dict:
    return {"rich_text": [{"text": {"content": value[:2000]}}]} if value else {"rich_text": []}


def title_property(value: str) -> Dict:
    return {"title": [{"text": {"content": value[:2000]}}]}


def find_title_property(database: Dict) -> str:
    for name, prop in (database.get("properties") or {}).items():
        if prop.get("type") == "title":
            return name
    return "标题"


def create_entry_page(notion: Client, database: Dict, title: str) -> Dict:
    title_name = find_title_property(database)
    database_id = database["id"]
    page = notion.pages.create(
        parent={"database_id": database_id},
        properties={
            title_name: title_property(title),
        },
        children=[
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "这个页面作为自媒体内容分发台账的入口。下方数据库用于记录各平台发布状态、链接、排期和素材路径。"
                            },
                        }
                    ]
                },
            }
        ],
    )
    return page


def resolve_parent(notion: Client, existing_database: Dict, title: str) -> Dict:
    parent = existing_database.get("parent") or {}
    if parent.get("type") == "page_id":
        return parent

    entry_page = create_entry_page(notion, existing_database, f"{title}入口")
    print("现有 Notion 数据库位于工作区根目录，已创建一个入口页面承载新台账。")
    print(f"入口页面链接：{entry_page.get('url', '')}")
    return {"type": "page_id", "page_id": entry_page["id"]}


def create_database(notion: Client, parent: Dict, title: str) -> Dict:
    return notion.databases.create(
        parent=parent,
        title=[{"type": "text", "text": {"content": title}}],
        properties=database_properties(),
        description=[
            {
                "type": "text",
                "text": {
                    "content": "用于记录公众号、视频号、小红书、抖音、快手、微博等平台的内容分发状态。"
                },
            }
        ],
    )


def get_data_source_id(database: Dict) -> Optional[str]:
    data_sources = database.get("data_sources") or []
    if data_sources:
        return data_sources[0].get("id")
    return None


def ensure_data_source_schema(notion: Client, data_source_id: Optional[str]):
    if not data_source_id:
        return
    data_source = notion.data_sources.retrieve(data_source_id=data_source_id)
    existing = data_source.get("properties") or {}
    target = database_properties()
    update_props: Dict = {}

    if "记录名称" not in existing and "Name" in existing:
        update_props["Name"] = {"name": "记录名称"}

    for name, schema in target.items():
        if name == "记录名称":
            continue
        if name not in existing:
            update_props[name] = schema

    if update_props:
        notion.data_sources.update(data_source_id=data_source_id, properties=update_props)


def read_existing_distribution_keys(notion: Client, parent_id: str, parent_type: str) -> set:
    existing_keys = set()
    has_more = True
    start_cursor = None
    while has_more:
        if parent_type == "data_source_id":
            response = notion.data_sources.query(
                data_source_id=parent_id,
                start_cursor=start_cursor,
                page_size=100,
            )
        else:
            response = notion.databases.query(
                database_id=parent_id,
                start_cursor=start_cursor,
                page_size=100,
            )
        for page in response.get("results", []):
            props = page.get("properties") or {}
            content_id_items = (props.get("内容ID") or {}).get("rich_text") or []
            content_id_value = "".join(item.get("plain_text", "") for item in content_id_items)
            platform_value = ((props.get("平台") or {}).get("select") or {}).get("name", "")
            if content_id_value and platform_value:
                existing_keys.add(f"{content_id_value}|{platform_value}")
        has_more = response.get("has_more", False)
        start_cursor = response.get("next_cursor")
    return existing_keys


def create_distribution_page(notion: Client, parent_id: str, parent_type: str, article: Dict, platform: str):
    local_path = str(article["path"].relative_to(PROJECT_ROOT))
    record_title = f"{article['title']}｜{platform}"
    format_name = DEFAULT_FORMAT.get(platform, "未定")
    properties = {
        "记录名称": title_property(record_title),
        "内容标题": text_property(article["title"]),
        "内容ID": text_property(article["content_id"]),
        "平台": {"select": {"name": platform}},
        "内容形式": {"select": {"name": format_name}},
        "分发状态": {"select": {"name": "待确认"}},
        "主题": text_property(article.get("topic", "")),
        "来源目录": {"select": {"name": article.get("source_dir", "其他")}},
        "本地正文路径": text_property(local_path),
        "字数": {"number": article.get("word_count") or 0},
        "是否需要改写": {"checkbox": platform != "公众号"},
        "是否已核对链接": {"checkbox": False},
        "备注": text_property("初始化记录：请确认是否发布、计划发布时间和发布链接。"),
    }
    return notion.pages.create(parent={parent_type: parent_id}, properties=properties)


def main():
    parser = argparse.ArgumentParser(description="创建 Notion 自媒体内容分发台账")
    parser.add_argument("--title", default="自媒体内容分发台账")
    parser.add_argument("--seed", action="store_true", help="为本地文章初始化六个平台的分发记录")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不写入 Notion")
    parser.add_argument("--delay", type=float, default=0.35, help="创建记录之间的间隔秒数")
    parser.add_argument("--database-id", help="使用已经创建好的 Notion 数据库继续补记录")
    parser.add_argument("--data-source-id", help="新版 Notion data source ID；通常可自动识别")
    args = parser.parse_args()

    articles = load_articles()
    for article in articles:
        article["content_id"] = content_id(article["path"], article["title"])

    print(f"本地可初始化文章：{len(articles)} 篇")
    if args.dry_run:
        print(f"将创建数据库：{args.title}")
        print(f"将初始化记录：{len(articles) * len(PLATFORMS) if args.seed else 0} 条")
        for article in articles[:10]:
            print(f"- {article['title']} ({article['source_dir']})")
        return

    config = Config()
    token = config.get("notion.token")
    existing_database_id = config.get("notion.database_id")
    if not token or not existing_database_id:
        raise SystemExit("config.json 缺少 notion.token 或 notion.database_id")

    notion = Client(auth=token)
    if args.database_id:
        database = notion.databases.retrieve(database_id=args.database_id)
        print(f"使用已有 Notion 数据库：{args.database_id}")
    else:
        existing_database = notion.databases.retrieve(database_id=existing_database_id)
        parent = resolve_parent(notion, existing_database, args.title)
        database = create_database(notion, parent, args.title)

    database_id = database["id"]
    database_url = database.get("url", "")
    data_source_id = args.data_source_id or get_data_source_id(database)
    ensure_data_source_schema(notion, data_source_id)

    if args.database_id:
        print(f"已确认 Notion 数据库：{args.title}")
    else:
        print(f"已创建 Notion 数据库：{args.title}")
    print(f"数据库 ID：{database_id}")
    if data_source_id:
        print(f"Data source ID：{data_source_id}")
    print(f"数据库链接：{database_url}")

    created_pages = 0
    if args.seed:
        parent_id = data_source_id or database_id
        parent_type = "data_source_id" if data_source_id else "database_id"
        existing_keys = read_existing_distribution_keys(notion, parent_id, parent_type)
        total = len(articles) * len(PLATFORMS)
        print(f"开始初始化分发记录：{total} 条")
        for article in articles:
            for platform in PLATFORMS:
                key = f"{article['content_id']}|{platform}"
                if key in existing_keys:
                    continue
                create_distribution_page(notion, parent_id, parent_type, article, platform)
                created_pages += 1
                existing_keys.add(key)
                if created_pages % 20 == 0:
                    print(f"  已创建 {created_pages}/{total} 条")
                time.sleep(args.delay)
        print(f"已初始化分发记录：{created_pages} 条")

    EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    EXPORT_PATH.write_text(
        json.dumps(
            {
                "database_title": args.title,
                "database_id": database_id,
                "database_url": database_url,
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "seeded_articles": len(articles) if args.seed else 0,
                "seeded_records": created_pages,
                "platforms": PLATFORMS,
                "source": "data/articles",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"本地留档：{EXPORT_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()

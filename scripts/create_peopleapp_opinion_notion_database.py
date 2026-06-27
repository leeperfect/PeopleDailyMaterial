#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建或登记“人民日报 APP 评论库”Notion 独立数据库。

数据库 ID 会写入 config.json 的 notion.peopleapp_opinion_database_id，不影响原有
notion.database_id。
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from notion_client import Client

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.peopleapp_opinion import EXPORT_DIR
from modules.utils import Config

CONFIG_PATH = PROJECT_ROOT / "config.json"
EXPORT_PATH = EXPORT_DIR / "notion_peopleapp_opinion_database.json"
DEFAULT_TITLE = "人民日报 APP 评论库"


def notion_color(index: int) -> str:
    colors = ["blue", "green", "red", "orange", "purple", "pink", "yellow", "gray", "brown"]
    return colors[index % len(colors)]


def select_options(names: Iterable[str]) -> List[Dict]:
    return [{"name": name, "color": notion_color(index)} for index, name in enumerate(names)]


def database_properties() -> Dict:
    return {
        "标题": {"title": {}},
        "Article ID": {"rich_text": {}},
        "Content ID": {"rich_text": {}},
        "Rel ID": {"rich_text": {}},
        "发布日期": {"date": {}},
        "作者": {"rich_text": {}},
        "来源": {
            "select": {
                "options": select_options(
                    ["人民日报客户端", "人民日报", "人民日报海外版", "人民号", "光明网", "上观新闻", "其他"]
                )
            }
        },
        "栏目": {"select": {"options": select_options(["APP-锐评", "评论", "其他"])}},
        "URL": {"url": {}},
        "摘要": {"rich_text": {}},
        "关键词": {"multi_select": {"options": []}},
        "正文字数": {"number": {"format": "number"}},
        "同步时间": {"date": {}},
        "采集状态": {
            "select": {"options": select_options(["已采集", "已同步", "同步失败", "已归档"])}
        },
    }


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
    return notion.pages.create(
        parent={"database_id": database["id"]},
        properties={title_name: title_property(title)},
        children=[
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "这个页面作为“人民日报 APP 评论库”的入口，用于承载独立 Notion 数据库。"
                            },
                        }
                    ]
                },
            }
        ],
    )


def resolve_parent(notion: Client, existing_database: Dict, title: str) -> Dict:
    parent = existing_database.get("parent") or {}
    if parent.get("type") == "page_id":
        return parent

    entry_page = create_entry_page(notion, existing_database, f"{title}入口")
    print("现有 Notion 文章库不在普通页面下，已创建入口页面承载 APP 评论库。")
    print(f"入口页面：{entry_page.get('url', '')}")
    return {"type": "page_id", "page_id": entry_page["id"]}


def create_database(notion: Client, parent: Dict, title: str) -> Dict:
    return notion.databases.create(
        parent=parent,
        title=[{"type": "text", "text": {"content": title}}],
        properties=database_properties(),
        description=[
            {
                "type": "text",
                "text": {"content": "独立保存人民日报 APP 评论/锐评频道文章，不与原人民日报文章库混用。"},
            }
        ],
    )


def get_data_source_id(database: Dict) -> Optional[str]:
    data_sources = database.get("data_sources") or []
    if data_sources:
        return data_sources[0].get("id")
    return None


def ensure_data_source_schema(notion: Client, data_source_id: Optional[str]) -> None:
    if not data_source_id or not hasattr(notion, "data_sources"):
        return
    data_source = notion.data_sources.retrieve(data_source_id=data_source_id)
    existing = data_source.get("properties") or {}
    update_props: Dict = {}

    existing_title_names = [
        name for name, schema in existing.items() if schema.get("type") == "title"
    ]
    if "标题" not in existing and existing_title_names:
        update_props[existing_title_names[0]] = {"name": "标题"}

    for name, schema in database_properties().items():
        if schema.get("title") == {}:
            continue
        if name not in existing:
            update_props[name] = schema
    if update_props:
        notion.data_sources.update(data_source_id=data_source_id, properties=update_props)


def load_config_dict() -> Dict:
    if not CONFIG_PATH.exists():
        raise SystemExit("未找到 config.json，请先配置 Notion token。")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config_database_id(database_id: str) -> None:
    config = load_config_dict()
    notion_config = config.setdefault("notion", {})
    notion_config["peopleapp_opinion_database_id"] = database_id
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def export_database_info(database: Dict, data_source_id: Optional[str], title: str) -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_PATH.write_text(
        json.dumps(
            {
                "database_title": title,
                "database_id": database.get("id", ""),
                "data_source_id": data_source_id or "",
                "database_url": database.get("url", ""),
                "config_key": "notion.peopleapp_opinion_database_id",
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "source": "peopleapp_opinion",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def ensure_peopleapp_opinion_database(
    title: str = DEFAULT_TITLE,
    database_id: Optional[str] = None,
    update_config: bool = True,
) -> Dict:
    config = Config(str(CONFIG_PATH))
    token = config.get("notion.token")
    existing_database_id = config.get("notion.database_id")
    if not token:
        raise SystemExit("config.json 缺少 notion.token，无法创建 Notion 数据库。")

    notion = Client(auth=token)
    if database_id:
        database = notion.databases.retrieve(database_id=database_id)
        print(f"已确认现有 Notion 数据库：{title}")
    else:
        if not existing_database_id:
            raise SystemExit("config.json 缺少 notion.database_id，无法定位新数据库放置位置。")
        existing_database = notion.databases.retrieve(database_id=existing_database_id)
        parent = resolve_parent(notion, existing_database, title)
        database = create_database(notion, parent, title)
        print(f"已创建 Notion 数据库：{title}")

    data_source_id = get_data_source_id(database)
    ensure_data_source_schema(notion, data_source_id)

    if update_config:
        save_config_database_id(database["id"])
        print("已写入 config.json：notion.peopleapp_opinion_database_id")

    export_database_info(database, data_source_id, title)
    print(f"本地留档：{EXPORT_PATH.relative_to(PROJECT_ROOT)}")
    print(f"数据库链接：{database.get('url', '')}")
    return {"database": database, "data_source_id": data_source_id}


def main() -> int:
    parser = argparse.ArgumentParser(description="创建或登记人民日报 APP 评论库 Notion 数据库")
    parser.add_argument("--title", default=DEFAULT_TITLE, help=f"数据库名称，默认 {DEFAULT_TITLE}")
    parser.add_argument("--database-id", help="使用已经建好的 Notion 数据库，并登记到 config.json")
    parser.add_argument("--no-config-update", action="store_true", help="不写入 config.json")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不写入 Notion")
    args = parser.parse_args()

    if args.dry_run:
        print(f"将创建或登记 Notion 数据库：{args.title}")
        print("字段：")
        for name in database_properties():
            print(f"- {name}")
        print("配置位置：notion.peopleapp_opinion_database_id")
        return 0

    ensure_peopleapp_opinion_database(
        title=args.title,
        database_id=args.database_id,
        update_config=not args.no_config_update,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

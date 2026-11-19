#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把旧 Notion 库「人民日报精选」中的人工精选记录迁移到新库「人民日报素材库」。

迁移原则：
1. 以 URL 中的文章 content id 去重，新库已有的文章不重复创建；
2. 旧库人工字段尽量映射到新库现有字段，不改动新库已有数据结构；
3. 旧库页面正文一并复制到新页面正文；
4. 默认只预览（dry-run），加 --execute 才真正写入 Notion。

用法：
    python3 scripts/migrate_notion_curated_selection.py --dry-run
    python3 scripts/migrate_notion_curated_selection.py --execute --limit 3
    python3 scripts/migrate_notion_curated_selection.py --execute
"""

import argparse
import json
import re
import sqlite3
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

OLD_DB_ID = "8f8555ac34274dbb8e12b362bb79e7e1"
NEW_DB_ID = "340b143b4284475ba4b8571e1c02c301"
NOTION_VERSION = "2022-06-28"

CHECKPOINT_PATH = PROJECT_ROOT / ".local" / "notion_selection_migration.json"
INDEX_CACHE_PATH = PROJECT_ROOT / ".local" / "notion_existing_index.json"
REPORT_PATH = PROJECT_ROOT / "data" / "exports" / "notion_selection_migration_report.json"
LOCAL_DB_PATH = PROJECT_ROOT / "data" / "core" / "articles.sqlite"

# 旧库「主题类别」到新库「版面名称」的标准名
BANMIAN_ALIASES = {
    "法制": "法治",
    "执法": "法治",
    "好干部": "党建",
    "短评": "评论",
}

BANMIAN_TO_CATEGORY = {}
for _b in ["要闻", "政治", "理论", "党建", "法治", "民主政治", "国防", "文件", "两会特刊", "记者调查"]:
    BANMIAN_TO_CATEGORY[_b] = "政治"
BANMIAN_TO_CATEGORY["评论"] = "评论"
for _b in ["经济", "财经", "产经", "消费", "科技", "科技·新知"]:
    BANMIAN_TO_CATEGORY[_b] = "经济"
for _b in ["文化", "副刊", "人文", "文化遗产", "国际副刊", "视觉", "假日生活"]:
    BANMIAN_TO_CATEGORY[_b] = "文化"
for _b in ["社会", "民生", "教育", "健康", "体育", "绿色", "生态", "新农村", "综合", "各地传真", "专题", "特别报道", "读者来信", "新青年"]:
    BANMIAN_TO_CATEGORY[_b] = "社会"
for _b in ["国际", "港澳台侨"]:
    BANMIAN_TO_CATEGORY[_b] = "国际"
BANMIAN_TO_CATEGORY["广告"] = "其他"

TOPIC_FIELDS = {
    "民生": "民生",
    "社会": "社会",
    "经济": "经济",
    "财经": "财经",
    "产经": "产经",
    "消费": "消费",
    "科技": "科技",
    "教育": "教育",
    "健康": "健康",
    "体育": "体育",
    "文化": "文化",
    "人文": "人文",
    "生态": "生态",
    "城市": "城市",
    "新农村": "新农村",
}

GOVERNANCE_FIELDS = {
    "党建": "党建",
    "政治": "政治",
    "政策": "政策",
    "法治": "法治",
    "法制": "法治",
    "执法": "执法",
    "理论": "理论",
    "学术": "学术",
    "好干部": "干部建设",
    "新青年": "青年发展",
}

QUESTION_TYPE_MAP = {
    "大作文": "申论大作文",
    "应用文": "申论应用文",
    "归纳概括": "申论归纳概括",
    "面试": "面试综合分析",
    "宣传稿": "申论应用文",
    "编者按": "申论应用文",
}


def load_token():
    config = json.loads((PROJECT_ROOT / "config.json").read_text(encoding="utf-8"))
    return config["notion"]["token"]


class NotionClient:
    def __init__(self, token):
        self.token = token
        self.calls = 0

    def request(self, method, path, body=None, retries=5):
        cmd = [
            "curl", "-sS", "--retry", "3", "--retry-delay", "1",
            "-X", method,
            "-H", "Authorization: Bearer " + self.token,
            "-H", "Notion-Version: " + NOTION_VERSION,
            "-H", "Content-Type: application/json",
            "https://api.notion.com/v1" + path,
        ]
        if body is not None:
            cmd += ["-d", json.dumps(body, ensure_ascii=False)]
        last_error = None
        for attempt in range(retries):
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                last_error = proc.stderr
                time.sleep(1.5)
                continue
            try:
                data = json.loads(proc.stdout)
            except Exception:
                last_error = proc.stdout[:300]
                time.sleep(1.5)
                continue
            if data.get("object") != "error":
                self.calls += 1
                return data
            code = data.get("code")
            if code == "rate_limited" or data.get("status") == 429:
                time.sleep(2 + attempt * 2)
                last_error = data
                continue
            # 其他错误交给调用方处理
            return data
        raise RuntimeError(f"Notion 请求失败: {path}: {last_error}")

    def query_all(self, database_id, filter_body=None, page_size=100):
        results = []
        cursor = None
        while True:
            body = {"page_size": page_size}
            if filter_body:
                body["filter"] = filter_body
            if cursor:
                body["start_cursor"] = cursor
            data = self.request("POST", f"/databases/{database_id}/query", body)
            if data.get("object") == "error":
                raise RuntimeError(data)
            results.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            cursor = data["next_cursor"]
            time.sleep(0.34)
        return results

    def children(self, block_id):
        results = []
        cursor = None
        while True:
            suffix = "?page_size=100" + (f"&start_cursor={cursor}" if cursor else "")
            data = self.request("GET", f"/blocks/{block_id}/children{suffix}")
            if data.get("object") == "error":
                raise RuntimeError(data)
            results.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            cursor = data["next_cursor"]
            time.sleep(0.34)
        return results


def plain_rich_text(properties, name):
    items = (properties.get(name) or {}).get("rich_text") or []
    return "".join(item.get("plain_text", "") for item in items)


def multi_select(properties, name):
    return [item["name"] for item in (properties.get(name) or {}).get("multi_select") or []]


def select_name(properties, name):
    value = (properties.get(name) or {}).get("select")
    return value["name"] if value else ""


def page_title(properties, name="Name"):
    items = (properties.get(name) or {}).get("title") or []
    return "".join(item.get("plain_text", "") for item in items)


def content_id(url):
    match = re.search(r"content_(\d+)\.html", url or "")
    return match.group(1) if match else None


def normalize_url(url):
    if not url:
        return ""
    return url.replace("http://paper.people.com.cn/", "https://paper.people.com.cn/")


def url_date(url):
    match = re.search(r"/content/(\d{4})(\d{2})/(\d{2})/content_\d+\.html", url or "")
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    match = re.search(r"/rmrb/html/(\d{4})-(\d{2})/(\d{2})/", url or "")
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    return ""


def article_id_for(url, title, publish_date):
    cid = content_id(url)
    if cid and publish_date:
        return "people_daily_" + publish_date.replace("-", "") + "_" + cid
    # 旧版 html 链接：nw.D110000renmrb_20241014_1-05.htm → p05_01
    match = re.search(r"nw\.[A-Za-z0-9]+_(\d{8})_(\d+)-(\d+)\.htm", url or "")
    if match and publish_date:
        return f"people_daily_{publish_date.replace('-', '')}_p{match.group(3)}_0{match.group(2)}"
    if not publish_date:
        publish_date = "unknown-date"
    host = "source"
    m = re.search(r"https?://([^/]+)/", url or "")
    if m:
        host = m.group(1).split(".")[-2] if m.group(1).endswith(".cn") else m.group(1).split(".")[0]
    slug = re.sub(r"[^A-Za-z0-9]+", "_", (url or "").split("://")[-1])[:40].strip("_")
    digest = str(abs(hash((url or "") + (title or ""))) % 100000000)
    return f"{host}_{publish_date.replace('-', '')}_{slug[-20:]}_{digest}"


def parse_ai_tags(text):
    """把旧库 AI标签 的多种写法拆成词条列表。"""
    if not text:
        return []
    text = text.replace("\r", "")
    text = re.sub(r"#", "\n#", text)
    text = re.sub(r"(标签|AI标签)\s*[:：]", " ", text)
    tags = []
    for line in text.split("\n"):
        line = line.strip().lstrip("-").strip()
        if not line:
            continue
        for token in re.split(r"[,，、;；]", line):
            token = token.strip().strip("#").strip()
            token = re.sub(r"^标签[:：]\s*", "", token)
            if token and token not in ("标签", "AI标签") and len(token) <= 30:
                tags.append(token)
    seen = []
    for tag in tags:
        if tag not in seen:
            seen.append(tag)
    return seen


def load_local_articles():
    """按 content id 读取本地核心库，补 Article ID、关键词、版面。"""
    mapping = {}
    if not LOCAL_DB_PATH.exists():
        return mapping
    con = sqlite3.connect(LOCAL_DB_PATH)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT article_id, source_url, title, date, section_name, category, keywords_json, summary FROM articles"
    )
    for row in rows:
        cid = content_id(row["source_url"])
        if cid:
            mapping[cid] = dict(row)
    con.close()
    return mapping


def build_properties(old_page, local_record, vocab):
    props = old_page["properties"]
    title = page_title(props).strip() or "无标题"
    raw_url = (props.get("URL") or {}).get("url") or ""
    url = normalize_url(raw_url)

    publish_date = url_date(url)
    if not publish_date:
        date_value = (props.get("发表日期") or {}).get("date") or {}
        publish_date = (date_value.get("start") or "")[:10]
    if not publish_date:
        publish_date = plain_rich_text(props, "发文日期")[:10]

    sections = multi_select(props, "主题类别")
    section = ""
    for name in sections:
        candidate = BANMIAN_ALIASES.get(name, name)
        if candidate in vocab["版面名称"]:
            section = candidate
            break
    if not section and local_record:
        local_section = local_record.get("section_name") or ""
        if local_section in vocab["版面名称"]:
            section = local_section

    category = BANMIAN_TO_CATEGORY.get(section)
    if not category:
        for name in sections:
            candidate = BANMIAN_ALIASES.get(name, name)
            if candidate in vocab["分类"]:
                category = candidate
                break
    if not category:
        category = "其他"

    material_uses = [name for name in multi_select(props, "用途") if name in vocab["素材用途"]]

    teaching = []
    for name in multi_select(props, "题型"):
        mapped = QUESTION_TYPE_MAP.get(name)
        if mapped and mapped in vocab["教学应用场景"] and mapped not in teaching:
            teaching.append(mapped)

    topics = []
    for name in sections:
        mapped = TOPIC_FIELDS.get(name)
        if mapped and mapped not in topics:
            topics.append(mapped)

    governance = []
    for name in sections:
        mapped = GOVERNANCE_FIELDS.get(name)
        if mapped and mapped not in governance:
            governance.append(mapped)

    content_type = ""
    genre = select_name(props, "体裁")
    if genre in vocab["内容类型/体裁"]:
        content_type = genre
    else:
        for name in sections:
            if name == "短评" and "短评" in vocab["内容类型/体裁"]:
                content_type = "短评"
                break
            if name == "评论" and "评论" in vocab["内容类型/体裁"]:
                content_type = "评论"
                break
            if name == "广告" and "广告" in vocab["内容类型/体裁"]:
                content_type = "广告"
                break

    series = "、".join(multi_select(props, "系列"))[:1800]
    stars = select_name(props, "星级")
    note = plain_rich_text(props, "备注").strip()

    ai_tags = parse_ai_tags(plain_rich_text(props, "AI标签"))
    topic_tags = multi_select(props, "话题")
    meta_lines = []
    if topic_tags:
        meta_lines.append("话题：" + "、".join(topic_tags))
    if ai_tags:
        meta_lines.append("AI标签：" + "、".join(ai_tags[:20]))
    meta_text = "\n".join(meta_lines)[:1900]

    keywords = []
    if local_record and local_record.get("keywords_json"):
        try:
            raw_keywords = json.loads(local_record["keywords_json"])
        except Exception:
            raw_keywords = []
        for word in raw_keywords:
            if word in vocab["关键词"] and word not in keywords:
                keywords.append(word)
        keywords = keywords[:8]

    properties = {
        "标题": {"title": [{"type": "text", "text": {"content": title[:2000]}}]},
        "URL": {"url": url or None},
        "分类": {"select": {"name": category}},
        "发布日期": ({"date": {"start": publish_date}} if publish_date else {"date": None}),
    }
    if section:
        properties["版面名称"] = {"select": {"name": section}}
    if content_type:
        properties["内容类型/体裁"] = {"select": {"name": content_type}}
    if keywords:
        properties["关键词"] = {"multi_select": [{"name": k} for k in keywords]}
    if material_uses:
        properties["素材用途"] = {"multi_select": [{"name": k} for k in material_uses]}
    if teaching:
        properties["教学应用场景"] = {"multi_select": [{"name": k} for k in teaching]}
    if topics:
        properties["议题领域"] = {"multi_select": [{"name": k} for k in topics]}
    if governance:
        properties["治理维度"] = {"multi_select": [{"name": k} for k in governance]}
    if series:
        properties["系列"] = {"rich_text": [{"type": "text", "text": {"content": series}}]}
    if stars:
        properties["星级"] = {"rich_text": [{"type": "text", "text": {"content": stars}}]}
    if note:
        properties["备注"] = {"rich_text": [{"type": "text", "text": {"content": note[:1900]}}]}
    if meta_text:
        properties["AI 摘要/热点"] = {"rich_text": [{"type": "text", "text": {"content": meta_text}}]}
    properties["Article ID"] = {"rich_text": [{"type": "text", "text": {"content": article_id_for(url, title, publish_date)}}]}
    return properties


def convert_rich_text(items):
    output = []
    for item in items:
        item_type = item.get("type")
        annotations = item.get("annotations") or {}
        if item_type == "text":
            text = item.get("text") or {}
            entry = {
                "type": "text",
                "text": {"content": text.get("content", ""), "link": text.get("link")},
            }
            if annotations:
                entry["annotations"] = annotations
            output.append(entry)
        elif item_type == "equation":
            output.append({
                "type": "equation",
                "equation": {"expression": (item.get("equation") or {}).get("expression", "")},
            })
        else:
            output.append({
                "type": "text",
                "text": {"content": item.get("plain_text", ""), "link": None},
            })
    return output


def convert_block(block):
    block_type = block.get("type")
    payload = block.get(block_type) or {}
    rich_text = convert_rich_text(payload.get("rich_text") or [])
    color = payload.get("color", "default")

    if block_type in ("paragraph", "quote"):
        return {block_type: {"rich_text": rich_text, "color": color}}
    if block_type in ("heading_1", "heading_2", "heading_3"):
        return {block_type: {"rich_text": rich_text, "color": color, "is_toggleable": False}}
    if block_type in ("bulleted_list_item", "numbered_list_item", "to_do"):
        body = {"rich_text": rich_text, "color": color}
        if block_type == "to_do":
            body["checked"] = bool(payload.get("checked"))
        return {block_type: body}
    if block_type == "callout":
        return {"callout": {
            "rich_text": rich_text,
            "color": color,
            "icon": payload.get("icon") or {"type": "emoji", "emoji": "📌"},
        }}
    if block_type == "code":
        return {"code": {
            "rich_text": rich_text,
            "language": payload.get("language", "plain text"),
            "caption": convert_rich_text(payload.get("caption") or []),
        }}
    if block_type == "divider":
        return {"divider": {}}
    if block_type == "image":
        image = payload.get("image") or payload
        image_type = image.get("type")
        if image_type == "external":
            return {"image": {"type": "external", "external": {"url": image["external"]["url"]}}}
        url = (image.get("file") or {}).get("url")
        if url:
            return {"image": {"type": "external", "external": {"url": url}}}
        return None
    if block_type == "bookmark":
        url = payload.get("url")
        return {"bookmark": {"url": url}} if url else None
    if block_type == "toggle":
        return {"toggle": {"rich_text": rich_text, "color": color}}
    return None


def copy_children(client, source_page_id, target_page_id):
    blocks = client.children(source_page_id)
    payloads = []
    for block in blocks:
        converted = convert_block(block)
        if converted:
            payloads.append({"object": "block", **converted})
    copied = 0
    for start in range(0, len(payloads), 100):
        batch = payloads[start:start + 100]
        data = client.request("PATCH", f"/blocks/{target_page_id}/children", {"children": batch})
        if data.get("object") == "error":
            raise RuntimeError(f"写入正文失败: {data.get('message')}")
        copied += len(batch)
        time.sleep(0.34)
    return copied


def merge_existing_properties(target_props, new_props):
    """已有页面只补齐空字段，多选字段取并集，不覆盖人工已有内容。"""
    updates = {}
    for name, value in new_props.items():
        if name in ("标题", "URL", "发布日期"):
            continue
        existing = target_props.get(name)
        if not existing:
            updates[name] = value
            continue
        prop_type = existing.get("type")
        if prop_type == "rich_text":
            current = "".join(item.get("plain_text", "") for item in existing.get("rich_text") or [])
            incoming = "".join(item.get("plain_text", "") for item in value.get("rich_text") or [])
            if not current:
                updates[name] = value
            elif name == "备注" and incoming and incoming not in current:
                merged = current + "\n" + incoming
                updates[name] = {"rich_text": [{"type": "text", "text": {"content": merged[:1900]}}]}
        elif prop_type == "select":
            current = (existing.get("select") or {}).get("name")
            if not current or current == "其他":
                updates[name] = value
        elif prop_type == "multi_select":
            current = [item["name"] for item in existing.get("multi_select") or []]
            incoming = [item["name"] for item in value.get("multi_select") or []]
            merged = list(dict.fromkeys(current + incoming))
            if merged != current:
                updates[name] = {"multi_select": [{"name": item} for item in merged]}
        elif prop_type == "date":
            if not (existing.get("date") or {}).get("start"):
                updates[name] = value
        else:
            updates[name] = value
    return updates


def update_existing_pages(client, old_pages, existing, state, vocab, local_articles, dry_run=False):
    """把旧库的人工标注补到新库已有页面。"""
    updated = 0
    planned = 0
    for page in old_pages:
        props = page["properties"]
        url = normalize_url((props.get("URL") or {}).get("url") or "")
        cid = content_id(url)
        key = cid or "url:" + url
        target_id = existing.get(key) or existing.get("url:" + url)
        if not target_id:
            continue
        if key in state.get("updated", {}):
            continue
        cid_value = content_id(url)
        local_record = local_articles.get(cid_value) if cid_value else None
        new_props = build_properties(page, local_record, vocab)
        target = client.request("GET", f"/pages/{target_id}")
        if target.get("object") == "error":
            continue
        updates = merge_existing_properties(target.get("properties", {}), new_props)
        if not updates:
            continue
        planned += 1
        if dry_run:
            print("待补齐:", page_title(props)[:36], list(updates.keys()))
            continue
        result = client.request("PATCH", f"/pages/{target_id}", {"properties": updates})
        if result.get("object") == "error":
            print("补齐失败:", page_title(props)[:30], result.get("message")[:100])
            continue
        state.setdefault("updated", {})[key] = {"page_id": target_id, "fields": list(updates.keys())}
        save_checkpoint(state)
        updated += 1
        print(f"已补齐: {page_title(props)[:32]} -> {','.join(updates.keys())}")
        time.sleep(0.34)
    print(f"补齐完成：计划 {planned} 条，已更新 {updated} 条")


def load_vocab(client):
    database = client.request("GET", f"/databases/{NEW_DB_ID}")
    if database.get("object") == "error":
        raise RuntimeError(database)
    props = database["properties"]

    def options(name, prop_type):
        prop = props.get(name) or {}
        return {item["name"] for item in (prop.get(prop_type) or {}).get("options") or []}

    return {
        "版面名称": options("版面名称", "select"),
        "分类": options("分类", "select"),
        "内容类型/体裁": options("内容类型/体裁", "select"),
        "素材用途": options("素材用途", "multi_select"),
        "教学应用场景": options("教学应用场景", "multi_select"),
        "议题领域": options("议题领域", "multi_select"),
        "治理维度": options("治理维度", "multi_select"),
        "关键词": options("关键词", "multi_select"),
    }


def load_existing_index(client, refresh=False):
    """按发布日期范围读取新库已有文章，建立 content id / URL 索引（带本地缓存）。"""
    if not refresh and INDEX_CACHE_PATH.exists():
        age = time.time() - INDEX_CACHE_PATH.stat().st_mtime
        if age < 12 * 3600:
            return json.loads(INDEX_CACHE_PATH.read_text(encoding="utf-8"))
    index = {}
    for year_start, year_end in [("2024-01-01", "2024-12-31"), ("2025-01-01", "2025-12-31"), ("2026-01-01", "2026-12-31")]:
        filter_body = {"and": [
            {"property": "发布日期", "date": {"on_or_after": year_start}},
            {"property": "发布日期", "date": {"on_or_before": year_end}},
        ]}
        pages = client.query_all(NEW_DB_ID, filter_body)
        for page in pages:
            url = (page["properties"].get("URL") or {}).get("url") or ""
            cid = content_id(url)
            if cid:
                index[cid] = page["id"]
            if url:
                index["url:" + normalize_url(url)] = page["id"]
    INDEX_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_CACHE_PATH.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    return index


def load_checkpoint():
    if CHECKPOINT_PATH.exists():
        return json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
    return {"done": {}, "failed": {}}


def save_checkpoint(state):
    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def select_old_pages(old_pages):
    """按 content id 去重，保留信息更完整的一条。"""
    chosen = {}
    for page in old_pages:
        props = page["properties"]
        url = normalize_url((props.get("URL") or {}).get("url") or "")
        cid = content_id(url) or "url:" + url
        score = 0
        if select_name(props, "星级"):
            score += 2
        if multi_select(props, "用途"):
            score += 2
        if plain_rich_text(props, "备注").strip():
            score += 1
        if multi_select(props, "话题"):
            score += 1
        if plain_rich_text(props, "AI标签").strip():
            score += 1
        previous = chosen.get(cid)
        if previous is None or score > previous[1]:
            chosen[cid] = (page, score)
    return [item[0] for item in chosen.values()]


def main():
    parser = argparse.ArgumentParser(description="迁移旧 Notion 精选库到素材库")
    parser.add_argument("--dry-run", action="store_true", help="只预览不写入")
    parser.add_argument("--execute", action="store_true", help="真正写入 Notion")
    parser.add_argument("--limit", type=int, default=0, help="本次最多处理多少条")
    parser.add_argument("--no-body", action="store_true", help="不复制正文")
    parser.add_argument("--refresh-index", action="store_true", help="强制重新读取新库已有文章")
    parser.add_argument("--update-existing", action="store_true", help="只把旧库标注补到新库已有页面")
    args = parser.parse_args()
    if not args.execute:
        args.dry_run = True

    client = NotionClient(load_token())
    vocab = load_vocab(client)
    local_articles = load_local_articles()
    old_pages = client.query_all(OLD_DB_ID)
    old_pages = select_old_pages(old_pages)
    existing = load_existing_index(client, refresh=args.refresh_index)
    state = load_checkpoint()

    if args.update_existing:
        update_existing_pages(client, old_pages, existing, state, vocab, local_articles, dry_run=args.dry_run)
        return

    pending = []
    skipped_existing = 0
    for page in old_pages:
        url = normalize_url((page["properties"].get("URL") or {}).get("url") or "")
        cid = content_id(url)
        key = cid or "url:" + url
        if key in existing or "url:" + url in existing:
            skipped_existing += 1
            continue
        if key in state["done"]:
            continue
        pending.append((key, page))

    pending.sort(key=lambda item: (
        plain_rich_text(item[1]["properties"], "发文日期")[:10],
        page_title(item[1]["properties"]),
    ))
    if args.limit:
        pending = pending[: args.limit]

    print(f"旧库去重后 {len(old_pages)} 条；新库已有 {skipped_existing} 条；历史已迁移 {len(state['done'])} 条；本次待迁移 {len(pending)} 条")

    report = {"generated_at": datetime.now().isoformat(timespec="seconds"), "planned": [], "created": [], "failed": []}
    for key, page in pending:
        props = page["properties"]
        cid = content_id(normalize_url((props.get("URL") or {}).get("url") or ""))
        local_record = local_articles.get(cid) if cid else None
        properties = build_properties(page, local_record, vocab)
        title = page_title(props)
        summary = {
            "title": title,
            "url": properties["URL"]["url"],
            "date": (properties.get("发布日期") or {}).get("date", {}).get("start") if properties.get("发布日期") else None,
            "category": properties["分类"]["select"]["name"],
            "section": (properties.get("版面名称") or {}).get("select", {}).get("name"),
            "material_uses": [x["name"] for x in (properties.get("素材用途") or {}).get("multi_select", [])],
            "teaching": [x["name"] for x in (properties.get("教学应用场景") or {}).get("multi_select", [])],
            "topics": [x["name"] for x in (properties.get("议题领域") or {}).get("multi_select", [])],
            "governance": [x["name"] for x in (properties.get("治理维度") or {}).get("multi_select", [])],
            "stars": (properties.get("星级") or {}).get("rich_text", [{}])[0].get("text", {}).get("content") if properties.get("星级") else "",
            "article_id": (properties.get("Article ID") or {}).get("rich_text", [{}])[0].get("text", {}).get("content") if properties.get("Article ID") else "",
        }
        report["planned"].append(summary)

        if args.dry_run:
            continue

        created = client.request("POST", "/pages", {
            "parent": {"database_id": NEW_DB_ID},
            "properties": properties,
        })
        if created.get("object") == "error":
            report["failed"].append({**summary, "error": created.get("message")})
            state["failed"][key] = created.get("message")
            save_checkpoint(state)
            print("失败:", title[:30], created.get("message")[:120])
            continue

        blocks = 0
        if not args.no_body:
            try:
                blocks = copy_children(client, page["id"], created["id"])
            except Exception as exc:
                report["failed"].append({**summary, "error": f"正文复制失败: {exc}"})

        state["done"][key] = {"new_page_id": created["id"], "title": title, "blocks": blocks}
        save_checkpoint(state)
        report["created"].append({**summary, "new_page_id": created["id"], "blocks": blocks})
        print(f"已迁移: {summary['date']} {title[:32]} (正文 {blocks} 段)")
        time.sleep(0.34)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"预览 {len(report['planned'])} 条；已创建 {len(report['created'])} 条；失败 {len(report['failed'])} 条")
    print("报告:", REPORT_PATH)


if __name__ == "__main__":
    main()
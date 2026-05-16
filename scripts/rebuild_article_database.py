#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重建本地文章核心库。

数据来源：
1. data/raw/articles_YYYYMMDD.json：旧的完整 JSON
2. data/vault/YYYY/MM/YYYY-MM-DD/.../*.md：人类阅读视图

输出：
1. data/core/articles.sqlite：稳定事实索引库
2. data/core/articles.jsonl：可读备份与 AI 批量导入格式
3. data/core/rebuild_manifest.json：本次重建摘要
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from typing import Dict, Iterable, List, Tuple

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from modules.article_database import DEFAULT_DB_PATH, ArticleStore
from modules.article_identity import build_article_id, normalize_date


DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
VAULT_DIR = os.path.join(DATA_DIR, "vault")
CORE_DIR = os.path.join(DATA_DIR, "core")
SOURCE_DIR = os.path.join(DATA_DIR, "source", "people_daily")
INDEX_DIR = os.path.join(DATA_DIR, "index")


def relpath(path: str) -> str:
    return os.path.relpath(path, PROJECT_ROOT)


def ensure_new_layout_dirs():
    """创建新结构的核心目录，不移动旧数据。"""
    for path in [
        CORE_DIR,
        SOURCE_DIR,
        os.path.join(SOURCE_DIR, "raw_articles"),
        os.path.join(SOURCE_DIR, "raw_html"),
        INDEX_DIR,
        os.path.join(INDEX_DIR, "vector"),
        os.path.join(INDEX_DIR, "fts"),
        os.path.join(DATA_DIR, "manifests"),
        os.path.join(DATA_DIR, "manifests", "crawl_runs"),
    ]:
        os.makedirs(path, exist_ok=True)


def parse_scalar(value: str):
    value = value.strip()
    if not value:
        return ""
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1].replace('\\"', '"')
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip('"').strip("'") for item in inner.split(",") if item.strip()]
    if re.match(r"^\d+$", value):
        return int(value)
    return value


def parse_frontmatter(markdown_text: str) -> Tuple[Dict, str]:
    if not markdown_text.startswith("---"):
        return {}, markdown_text

    lines = markdown_text.splitlines()
    end_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break

    if end_index is None:
        return {}, markdown_text

    meta: Dict = {}
    current_list_key = None
    for line in lines[1:end_index]:
        if not line.strip():
            continue
        if current_list_key and line.startswith("  - "):
            meta.setdefault(current_list_key, []).append(parse_scalar(line[4:].strip()))
            continue

        current_list_key = None
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value == "":
            meta[key] = []
            current_list_key = key
        else:
            meta[key] = parse_scalar(value)

    body = "\n".join(lines[end_index + 1 :]).strip()
    return meta, body


def clean_markdown_body(body: str) -> str:
    """保留正文信息，同时去掉最常见的 YAML 后标题噪音。"""
    lines = [line.rstrip() for line in body.splitlines()]
    cleaned = []
    for line in lines:
        if line.startswith("> 系列："):
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


def scan_vault_articles() -> Dict[str, Dict]:
    records: Dict[str, Dict] = {}
    if not os.path.exists(VAULT_DIR):
        return records

    for root, _, files in os.walk(VAULT_DIR):
        if f"{os.sep}_素材库{os.sep}" in root or root.endswith(f"{os.sep}_素材库"):
            continue
        for filename in files:
            if not filename.endswith(".md"):
                continue
            path = os.path.join(root, filename)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
            except UnicodeDecodeError:
                continue

            meta, body = parse_frontmatter(text)
            title = meta.get("title") or os.path.splitext(filename)[0]
            date = normalize_date(str(meta.get("date") or ""))
            source_url = meta.get("source_url") or meta.get("url") or ""
            if not date and not source_url:
                continue

            section = str(meta.get("section") or "")
            section_match = re.search(r"(\d+)", section)
            section_no = section_match.group(1) if section_match else ""
            content = clean_markdown_body(body)
            keywords = meta.get("keywords") or []
            if isinstance(keywords, str):
                keywords = [keywords]

            article = {
                "source": "people_daily",
                "title": title,
                "date": date,
                "author": meta.get("author", ""),
                "section_no": section_no,
                "section_name": meta.get("section_name", ""),
                "plate": meta.get("section_name", ""),
                "category": meta.get("category", ""),
                "keywords": keywords,
                "word_count": meta.get("word_count") or len(content),
                "url": source_url,
                "source_url": source_url,
                "content": content,
                "markdown_body": body,
                "markdown_path": relpath(path),
                "series_int_id": meta.get("series"),
                "series_name": meta.get("series_name", ""),
                "series_part": meta.get("series_part"),
                "related_titles": meta.get("related") or [],
            }
            records[build_article_id(article)] = article

    return records


def scan_raw_articles() -> Dict[str, Dict]:
    records: Dict[str, Dict] = {}
    if not os.path.exists(RAW_DIR):
        return records

    for filename in sorted(os.listdir(RAW_DIR)):
        match = re.match(r"articles_(\d{8})\.json$", filename)
        if not match:
            continue
        date = normalize_date(match.group(1))
        path = os.path.join(RAW_DIR, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                articles = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(articles, list):
            continue

        for article in articles:
            if not isinstance(article, dict):
                continue
            item = dict(article)
            item["date"] = normalize_date(item.get("date") or date)
            item["source"] = item.get("source") or "people_daily"
            item["source_url"] = item.get("source_url") or item.get("url") or ""
            item["url"] = item.get("url") or item.get("source_url") or ""
            item["raw_path"] = relpath(path)
            records[build_article_id(item)] = item

    return records


def merge_records(vault_records: Dict[str, Dict], raw_records: Dict[str, Dict]) -> List[Dict]:
    merged = dict(vault_records)
    for article_id, raw in raw_records.items():
        existing = merged.get(article_id, {})
        item = dict(existing)
        item.update(raw)
        for key in ["markdown_path", "section_no", "section_name", "related_titles"]:
            if existing.get(key) and not raw.get(key):
                item[key] = existing[key]
        if existing.get("markdown_body") and not raw.get("markdown_body"):
            item["markdown_body"] = existing["markdown_body"]
        item["article_id"] = article_id
        merged[article_id] = item

    return sorted(
        merged.values(),
        key=lambda item: (
            item.get("date", ""),
            str(item.get("section_no", "")),
            item.get("title", ""),
        ),
    )


def write_jsonl(articles: Iterable[Dict], output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        for article in articles:
            f.write(json.dumps(article, ensure_ascii=False, sort_keys=True))
            f.write("\n")


def load_series_registry() -> Dict:
    path = os.path.join(DATA_DIR, "series_registry.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def rebuild(db_path: str, reset: bool = True) -> Dict:
    ensure_new_layout_dirs()
    full_db_path = db_path if os.path.isabs(db_path) else os.path.join(PROJECT_ROOT, db_path)
    if reset:
        for suffix in ["", "-wal", "-shm"]:
            candidate = f"{full_db_path}{suffix}"
            if os.path.exists(candidate):
                os.remove(candidate)

    vault_records = scan_vault_articles()
    raw_records = scan_raw_articles()
    articles = merge_records(vault_records, raw_records)

    store = ArticleStore(full_db_path)
    store.upsert_articles(articles)
    store.replace_series_registry(load_series_registry())
    stats = store.stats()
    store.close()

    jsonl_path = os.path.join(CORE_DIR, "articles.jsonl")
    write_jsonl(articles, jsonl_path)

    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "db_path": relpath(full_db_path),
        "jsonl_path": relpath(jsonl_path),
        "vault_records": len(vault_records),
        "raw_records": len(raw_records),
        "merged_articles": len(articles),
        "stats": stats,
        "note": "旧 data/raw 与 data/vault 未移动；新库作为核心事实索引层。",
    }
    manifest_path = os.path.join(CORE_DIR, "rebuild_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    return manifest


def main():
    parser = argparse.ArgumentParser(description="重建人民日报素材核心 SQLite 数据库")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="数据库路径，默认 data/core/articles.sqlite")
    parser.add_argument("--no-reset", action="store_true", help="不删除旧库，改为增量 upsert")
    args = parser.parse_args()

    manifest = rebuild(args.db_path, reset=not args.no_reset)
    print("=" * 60)
    print("人民日报素材核心库重建完成")
    print("=" * 60)
    print(f"数据库: {manifest['db_path']}")
    print(f"JSONL: {manifest['jsonl_path']}")
    print(f"Vault 记录: {manifest['vault_records']}")
    print(f"Raw 记录: {manifest['raw_records']}")
    print(f"合并后文章: {manifest['merged_articles']}")
    print(f"检索分块: {manifest['stats']['chunk_count']}")
    print(f"日期范围: {manifest['stats']['start_date']} ~ {manifest['stats']['end_date']}")


if __name__ == "__main__":
    main()

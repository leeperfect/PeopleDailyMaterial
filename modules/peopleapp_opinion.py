#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人民日报 APP 评论库独立采集工具。

这一套工具不写入原有 `data/core/articles.sqlite`，而是把评论频道单独沉淀到
`data/peopleapp_opinion/`，方便后续独立检索、独立同步 Notion。
"""

import csv
import html
import json
import logging
import os
import re
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from modules.article_database import ArticleStore
from modules.article_identity import content_hash
from modules.processor import DataProcessor


PEOPLEAPP_OPINION_SOURCE = "peopleapp_opinion"
CHANNEL_ID = "2003"
CHANNEL_STRATEGY = "2"
CHANNEL_NAME = "APP-锐评"
BASE_URL = "https://www.peopleapp.com"
LIST_API = "/api/rmrb-bff-display-zh/display/zh/c/pc/compInfo"
DETAIL_API = "/api/rmrb-bff-display-zh/content/zh/c/pc/content/detail"
APP_CODE = "2faaf721ed424694bc63bdaec811a580"
TIMEZONE = ZoneInfo("Asia/Shanghai")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / "data" / "peopleapp_opinion"
RAW_DIR = DATA_ROOT / "raw"
CORE_DIR = DATA_ROOT / "core"
VAULT_DIR = DATA_ROOT / "vault"
EXPORT_DIR = DATA_ROOT / "exports"
RUN_LOG_DIR = EXPORT_DIR / "run_logs"
DB_PATH = CORE_DIR / "articles.sqlite"
META_TABLE = "peopleapp_opinion_meta"


def ensure_dirs() -> None:
    for path in (RAW_DIR, CORE_DIR, VAULT_DIR, EXPORT_DIR, RUN_LOG_DIR):
        path.mkdir(parents=True, exist_ok=True)


def init_meta_schema(store: ArticleStore) -> None:
    """保存 APP 评论库专有字段，避免污染通用文章表结构。"""
    store.conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {META_TABLE} (
            article_id TEXT PRIMARY KEY,
            content_id TEXT,
            rel_id TEXT,
            source_name TEXT,
            cover_url TEXT,
            image_urls_json TEXT,
            publish_time TEXT,
            editor TEXT,
            view_count INTEGER,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(article_id) REFERENCES articles(article_id) ON DELETE CASCADE
        )
        """
    )
    store.conn.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{META_TABLE}_content_rel ON {META_TABLE}(content_id, rel_id)"
    )
    store.conn.commit()


def upsert_meta(store: ArticleStore, article: Dict) -> None:
    init_meta_schema(store)
    store.conn.execute(
        f"""
        INSERT OR REPLACE INTO {META_TABLE} (
            article_id, content_id, rel_id, source_name, cover_url,
            image_urls_json, publish_time, editor, view_count, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            article.get("article_id", ""),
            article.get("content_id", ""),
            article.get("rel_id", ""),
            article.get("source_name", ""),
            article.get("cover_url", ""),
            json.dumps(article.get("image_urls") or [], ensure_ascii=False),
            str(article.get("publish_time") or ""),
            article.get("editor", ""),
            article.get("view_count"),
            datetime.now(TIMEZONE).isoformat(timespec="seconds"),
        ),
    )
    store.conn.commit()


def _meta_table_exists(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (META_TABLE,),
    ).fetchone()
    return row is not None


def enrich_articles_with_meta(store: ArticleStore, articles: List[Dict]) -> List[Dict]:
    if not articles or not _meta_table_exists(store.conn):
        return articles

    article_ids = [article.get("article_id") for article in articles if article.get("article_id")]
    if not article_ids:
        return articles

    placeholders = ",".join("?" for _ in article_ids)
    rows = store.conn.execute(
        f"SELECT * FROM {META_TABLE} WHERE article_id IN ({placeholders})",
        article_ids,
    ).fetchall()
    meta_by_id = {row["article_id"]: dict(row) for row in rows}

    for article in articles:
        meta = meta_by_id.get(article.get("article_id"))
        if not meta:
            continue
        article.update(
            {
                "content_id": meta.get("content_id") or "",
                "rel_id": meta.get("rel_id") or "",
                "source_name": meta.get("source_name") or "",
                "cover_url": meta.get("cover_url") or "",
                "publish_time": meta.get("publish_time") or "",
                "editor": meta.get("editor") or "",
                "view_count": meta.get("view_count"),
                "image_urls": json.loads(meta.get("image_urls_json") or "[]"),
            }
        )
    return articles


def api_headers() -> Dict[str, str]:
    return {
        "Authorization": f"AppCode {APP_CODE}",
        "X-Ca-Stage": "RELEASE",
        "plat": "web",
        "system": "PC",
        "versionCode": "7422",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Referer": f"{BASE_URL}/opinion?param1={CHANNEL_ID}&param2={CHANNEL_STRATEGY}",
    }


def source_url(content_id: str, rel_id: str) -> str:
    return f"{BASE_URL}/column/{content_id}-{rel_id}"


def build_opinion_article_id(date_str: str, content_id: str, rel_id: str) -> str:
    compact_date = date_str.replace("-", "") if date_str else "undated"
    return f"{PEOPLEAPP_OPINION_SOURCE}_{compact_date}_{content_id}_{rel_id}"


def parse_peopleapp_url(url: str) -> Tuple[str, str]:
    match = re.search(r"/column/(\d+)-(\d+)", url or "")
    if not match:
        raise ValueError("链接中没有识别到 contentId-relId")
    return match.group(1), match.group(2)


def parse_timestamp(value: object) -> Optional[datetime]:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if not text:
        return None

    if re.fullmatch(r"\d{13}", text):
        return datetime.fromtimestamp(int(text) / 1000, tz=TIMEZONE)
    if re.fullmatch(r"\d{10}", text):
        return datetime.fromtimestamp(int(text), tz=TIMEZONE)

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(text, fmt)
            return parsed.replace(tzinfo=TIMEZONE)
        except ValueError:
            continue
    return None


def date_from_item(item: Dict) -> str:
    published = parse_timestamp(item.get("publishTime") or item.get("createTime"))
    return published.strftime("%Y-%m-%d") if published else ""


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]', "", name or "")
    name = re.sub(r"\s+", " ", name).strip().strip(".")
    if len(name) > 80:
        name = name[:80]
    return name or "未知标题"


def yaml_string(value: object) -> str:
    text = str(value or "").replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def html_fragment_to_markdown(fragment: str) -> Tuple[str, str, List[str]]:
    """把 APP 正文 HTML 转为 Markdown、纯文本正文和图片链接列表。"""
    soup = BeautifulSoup(html.unescape(fragment or ""), "html.parser")
    markdown_lines: List[str] = []
    text_lines: List[str] = []
    images: List[str] = []

    for tag in soup.find_all(["p", "section", "div"], recursive=True):
        if tag.find_parent(["p", "section", "div"]) is not None:
            continue

        tag_images = [img.get("src", "").strip() for img in tag.find_all("img") if img.get("src")]
        if tag_images:
            for url in tag_images:
                images.append(url)
                markdown_lines.append(f"![图片]({url})")
            continue

        text = tag.get_text(" ", strip=True)
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            continue

        md = paragraph_to_markdown(tag)
        markdown_lines.append(md)
        text_lines.append(text)

    if not markdown_lines:
        text = soup.get_text("\n", strip=True)
        text_lines = [line.strip() for line in text.splitlines() if line.strip()]
        markdown_lines = text_lines[:]

    return "\n\n".join(markdown_lines).strip(), "\n".join(text_lines).strip(), images


def paragraph_to_markdown(tag) -> str:
    parts: List[str] = []
    for child in tag.children:
        if getattr(child, "name", None) in {"strong", "b"}:
            text = child.get_text(" ", strip=True)
            if text:
                parts.append(f"**{text}**")
        elif getattr(child, "name", None) in {"em", "i"}:
            text = child.get_text(" ", strip=True)
            if text:
                parts.append(f"*{text}*")
        elif getattr(child, "name", None) == "a":
            text = child.get_text(" ", strip=True)
            href = child.get("href", "").strip()
            parts.append(f"[{text}]({href})" if href else text)
        elif getattr(child, "name", None) == "img":
            url = child.get("src", "").strip()
            if url:
                parts.append(f"![图片]({url})")
        elif getattr(child, "name", None):
            text = child.get_text(" ", strip=True)
            if text:
                parts.append(text)
        else:
            text = str(child).replace("\n", " ").strip()
            if text:
                parts.append(text)

    md = "".join(parts)
    return re.sub(r"\s+", " ", md).strip()


@dataclass
class CrawlResult:
    total_list_items: int = 0
    selected_items: int = 0
    downloaded: int = 0
    skipped_existing: int = 0
    failed: int = 0
    dry_run: bool = False
    articles: Optional[List[Dict]] = None
    failures: Optional[List[Dict]] = None

    def as_dict(self) -> Dict:
        return {
            "total_list_items": self.total_list_items,
            "selected_items": self.selected_items,
            "downloaded": self.downloaded,
            "skipped_existing": self.skipped_existing,
            "failed": self.failed,
            "dry_run": self.dry_run,
            "articles": self.articles or [],
            "failures": self.failures or [],
        }


class PeopleAppOpinionClient:
    def __init__(self, timeout: int = 20, delay: float = 0.35):
        self.session = requests.Session()
        self.session.headers.update(api_headers())
        self.timeout = timeout
        self.delay = delay

    def get_json(self, path: str, params: Dict) -> Dict:
        response = self.session.get(
            f"{BASE_URL}{path}",
            params=params,
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if str(payload.get("code")) != "0" or not payload.get("success", True):
            raise RuntimeError(payload.get("message") or f"接口返回异常: {payload}")
        return payload

    def fetch_list_page(
        self,
        page_num: int,
        page_size: int,
        refresh_time: Optional[int] = None,
    ) -> Dict:
        params = {
            "channelId": CHANNEL_ID,
            "channelStrategy": CHANNEL_STRATEGY,
            "pageNum": page_num,
            "pageSize": page_size,
        }
        if refresh_time:
            params["refreshTime"] = refresh_time
        return self.get_json(LIST_API, params).get("data") or {}

    def fetch_detail(self, content_id: str, rel_id: str) -> Dict:
        payload = self.get_json(DETAIL_API, {"contentId": content_id, "relId": rel_id})
        data = payload.get("data") or []
        if not data:
            raise RuntimeError("详情接口没有返回正文数据")
        return data[0]

    def polite_pause(self) -> None:
        if self.delay > 0:
            time.sleep(self.delay)


def list_item_key(item: Dict) -> Tuple[str, str]:
    return str(item.get("objectId") or ""), str(item.get("relId") or "")


def normalize_article(detail: Dict, list_item: Optional[Dict] = None) -> Dict:
    list_item = list_item or {}
    content_id = str(detail.get("newsId") or list_item.get("objectId") or "")
    rel_info = detail.get("reLInfo") or {}
    rel_id = str(rel_info.get("relId") or list_item.get("relId") or "")
    published = parse_timestamp(detail.get("publishTime")) or parse_timestamp(list_item.get("publishTime"))
    date_str = published.strftime("%Y-%m-%d") if published else date_from_item(list_item)
    title = detail.get("newsTitle") or list_item.get("newsTitle") or "无标题"
    source_name = detail.get("newsSourceName") or list_item.get("source") or ""
    authors = [item.get("authorName", "").strip() for item in detail.get("authorList") or list_item.get("authorList") or []]
    author = "、".join([name for name in authors if name])
    markdown_body, content, image_urls = html_fragment_to_markdown(detail.get("newsContent") or "")

    processor = DataProcessor()
    cleaned_content = processor.clean_content(content)
    keywords = processor.extract_keywords(f"{title} {cleaned_content}", topK=10)
    summary = (detail.get("newsSummary") or list_item.get("newsSummary") or processor.extract_summary(cleaned_content)).strip()

    article = {
        "article_id": build_opinion_article_id(date_str, content_id, rel_id),
        "source": PEOPLEAPP_OPINION_SOURCE,
        "source_name": source_name,
        "content_id": content_id,
        "rel_id": rel_id,
        "title": title,
        "author": author,
        "date": date_str,
        "section_no": "APP",
        "section_name": CHANNEL_NAME,
        "plate": CHANNEL_NAME,
        "category": "评论",
        "keywords": keywords,
        "summary": summary,
        "content": cleaned_content,
        "markdown_body": f"# {title}\n\n{markdown_body}".strip(),
        "url": source_url(content_id, rel_id),
        "source_url": source_url(content_id, rel_id),
        "content_hash": content_hash(cleaned_content),
        "word_count": len(cleaned_content),
        "image_urls": image_urls,
        "cover_url": detail.get("shareInfo", {}).get("shareCoverUrl")
        or list_item.get("coverUrl")
        or "",
        "publish_time": detail.get("publishTime") or list_item.get("publishTime") or "",
        "editor": detail.get("editorName", ""),
        "view_count": detail.get("viewCount"),
    }
    return article


def article_exists(store: ArticleStore, article_id: str) -> bool:
    row = store.conn.execute(
        "SELECT article_id FROM articles WHERE article_id = ?",
        (article_id,),
    ).fetchone()
    return row is not None


def save_markdown(article: Dict) -> str:
    date = datetime.strptime(article["date"], "%Y-%m-%d")
    dir_path = VAULT_DIR / date.strftime("%Y") / date.strftime("%m") / article["date"] / CHANNEL_NAME
    dir_path.mkdir(parents=True, exist_ok=True)
    path = dir_path / f"{sanitize_filename(article.get('title', '无标题'))}.md"

    image_lines = []
    for url in article.get("image_urls") or []:
        image_lines.append(f"  - {yaml_string(url)}")

    frontmatter = [
        "---",
        f"title: {yaml_string(article.get('title'))}",
        f"article_id: {yaml_string(article.get('article_id'))}",
        f"date: {article.get('date')}",
        f"source_kind: {yaml_string(PEOPLEAPP_OPINION_SOURCE)}",
        f"source_name: {yaml_string(article.get('source_name'))}",
        f"channel: {yaml_string(CHANNEL_NAME)}",
        f"author: {yaml_string(article.get('author'))}",
        f"content_id: {yaml_string(article.get('content_id'))}",
        f"rel_id: {yaml_string(article.get('rel_id'))}",
        f"source_url: {yaml_string(article.get('source_url'))}",
        f"summary: {yaml_string(article.get('summary'))}",
    ]
    if image_lines:
        frontmatter.append("image_urls:")
        frontmatter.extend(image_lines)
    else:
        frontmatter.append("image_urls: []")
    frontmatter.extend(["---", ""])
    path.write_text("\n".join(frontmatter) + article.get("markdown_body", "") + "\n", encoding="utf-8")
    return str(path)


def save_raw_by_date(raw_by_date: Dict[str, List[Dict]]) -> List[str]:
    paths = []
    for date_str, rows in sorted(raw_by_date.items()):
        path = RAW_DIR / f"peopleapp_opinion_{date_str.replace('-', '')}.json"
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        paths.append(str(path))
    return paths


def save_report(result: CrawlResult, label: str) -> Tuple[str, str]:
    timestamp = datetime.now(TIMEZONE).strftime("%Y%m%d_%H%M%S")
    json_path = EXPORT_DIR / f"peopleapp_opinion_crawl_{label}_{timestamp}.json"
    csv_path = EXPORT_DIR / f"peopleapp_opinion_crawl_{label}_{timestamp}.csv"
    payload = result.as_dict()
    payload["generated_at"] = datetime.now(TIMEZONE).isoformat(timespec="seconds")
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["article_id", "date", "title", "source_name", "url", "status"])
        for article in result.articles or []:
            writer.writerow(
                [
                    article.get("article_id", ""),
                    article.get("date", ""),
                    article.get("title", ""),
                    article.get("source_name", ""),
                    article.get("source_url", ""),
                    article.get("_status", "downloaded"),
                ]
            )
        for failure in result.failures or []:
            writer.writerow(["", "", failure.get("title", ""), "", failure.get("url", ""), failure.get("error", "")])

    return str(json_path), str(csv_path)


def collect_list_items(
    client: PeopleAppOpinionClient,
    start_date: str,
    end_date: str,
    max_pages: int,
    page_size: int,
) -> Tuple[List[Dict], int]:
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    refresh_time = None
    selected: List[Dict] = []
    seen = set()
    total = 0

    for page_num in range(1, max_pages + 1):
        page = client.fetch_list_page(page_num, page_size, refresh_time)
        refresh_time = page.get("refreshTime") or refresh_time
        items = page.get("list") or []
        if not items:
            break
        total += len(items)

        page_dates = []
        for item in items:
            content_id, rel_id = list_item_key(item)
            if not content_id or not rel_id:
                continue
            if str(item.get("objectType")) != "8":
                continue
            item_date = date_from_item(item)
            if not item_date:
                continue
            date_obj = datetime.strptime(item_date, "%Y-%m-%d").date()
            page_dates.append(date_obj)
            if start <= date_obj <= end and (content_id, rel_id) not in seen:
                selected.append(item)
                seen.add((content_id, rel_id))

        if page_dates and max(page_dates) < start and page_num > 1:
            break
        client.polite_pause()

    return selected, total


def crawl_peopleapp_opinion(
    start_date: str,
    end_date: str,
    max_pages: int = 10,
    page_size: int = 20,
    dry_run: bool = False,
    force: bool = False,
    urls: Optional[Sequence[str]] = None,
    delay: float = 0.35,
) -> CrawlResult:
    ensure_dirs()
    client = PeopleAppOpinionClient(delay=delay)
    store = ArticleStore(str(DB_PATH))
    init_meta_schema(store)
    raw_by_date: Dict[str, List[Dict]] = {}
    articles: List[Dict] = []
    failures: List[Dict] = []
    result = CrawlResult(dry_run=dry_run, articles=articles, failures=failures)

    try:
        if urls:
            list_items = []
            for url in urls:
                content_id, rel_id = parse_peopleapp_url(url)
                list_items.append({"objectId": content_id, "relId": rel_id, "newsTitle": url, "source_url": url})
            result.total_list_items = len(list_items)
        else:
            list_items, total = collect_list_items(client, start_date, end_date, max_pages, page_size)
            result.total_list_items = total

        result.selected_items = len(list_items)

        if dry_run:
            for item in list_items:
                content_id, rel_id = list_item_key(item)
                item_date = date_from_item(item)
                articles.append(
                    {
                        "article_id": build_opinion_article_id(item_date, content_id, rel_id) if item_date else "",
                        "date": item_date,
                        "title": item.get("newsTitle") or item.get("source_url", ""),
                        "source_name": item.get("source", ""),
                        "source_url": source_url(content_id, rel_id),
                        "_status": "dry-run",
                    }
                )
            return result

        for item in list_items:
            content_id, rel_id = list_item_key(item)
            item_date = date_from_item(item)
            projected_id = build_opinion_article_id(item_date, content_id, rel_id) if item_date else ""
            if projected_id and not force and article_exists(store, projected_id):
                result.skipped_existing += 1
                articles.append(
                    {
                        "article_id": projected_id,
                        "date": item_date,
                        "title": item.get("newsTitle", ""),
                        "source_name": item.get("source", ""),
                        "source_url": source_url(content_id, rel_id),
                        "_status": "skipped_existing",
                    }
                )
                continue

            try:
                detail = client.fetch_detail(content_id, rel_id)
                article = normalize_article(detail, item)
                markdown_path = save_markdown(article)
                article["markdown_path"] = markdown_path
                store.upsert_article(article)
                upsert_meta(store, article)
                raw_by_date.setdefault(article["date"], []).append({"list_item": item, "detail": detail})
                article["_status"] = "downloaded"
                articles.append(article)
                result.downloaded += 1
                client.polite_pause()
            except Exception as exc:
                result.failed += 1
                logging.exception("采集 APP 评论文章失败: %s-%s", content_id, rel_id)
                failures.append(
                    {
                        "content_id": content_id,
                        "rel_id": rel_id,
                        "title": item.get("newsTitle", ""),
                        "url": source_url(content_id, rel_id),
                        "error": str(exc),
                    }
                )

        save_raw_by_date(raw_by_date)
        return result
    finally:
        store.close()


def default_date_range(days: int) -> Tuple[str, str]:
    today = datetime.now(TIMEZONE).date()
    start = today - timedelta(days=max(1, days) - 1)
    return start.isoformat(), today.isoformat()


def load_all_articles(limit: Optional[int] = None) -> List[Dict]:
    if not DB_PATH.exists():
        return []
    store = ArticleStore(str(DB_PATH))
    try:
        articles = store.get_articles(limit=limit)
        return enrich_articles_with_meta(store, articles)
    finally:
        store.close()


def search_articles(query: str, limit: int = 20) -> List[Dict]:
    if not DB_PATH.exists():
        return []
    store = ArticleStore(str(DB_PATH))
    try:
        articles = store.search(query, limit=limit)
        return enrich_articles_with_meta(store, articles)
    finally:
        store.close()


def load_articles(
    dates: Optional[Sequence[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict]:
    if not DB_PATH.exists():
        return []
    store = ArticleStore(str(DB_PATH))
    try:
        articles = store.get_articles(
            dates=dates,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        return enrich_articles_with_meta(store, articles)
    finally:
        store.close()

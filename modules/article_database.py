#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地文章核心库。

SQLite 是知识库的事实索引层：目录可以为了阅读反复重排，Notion 可以作为
输出端变化，但这里用稳定 article_id 保存每篇文章的结构化信息和 AI 检索分块。
"""

import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Sequence

from modules.article_identity import (
    PEOPLE_DAILY_SOURCE,
    build_article_id,
    content_hash,
    normalize_date,
)


DEFAULT_DB_PATH = os.path.join("data", "core", "articles.sqlite")
SCHEMA_VERSION = 1


class ArticleStore:
    """SQLite 文章库。"""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, timeout=10)
        self.conn.row_factory = sqlite3.Row
        self.init_schema()

    def close(self):
        self.conn.close()

    def init_schema(self):
        cur = self.conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA foreign_keys=ON")

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_info (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS articles (
                article_id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                source_url TEXT,
                title TEXT NOT NULL,
                author TEXT,
                date TEXT NOT NULL,
                year INTEGER,
                month INTEGER,
                section_no TEXT,
                section_name TEXT,
                category TEXT,
                keywords_json TEXT,
                summary TEXT,
                content TEXT,
                markdown_body TEXT,
                raw_path TEXT,
                markdown_path TEXT,
                content_hash TEXT,
                word_count INTEGER,
                series_id TEXT,
                series_name TEXT,
                series_part INTEGER,
                related_titles_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS article_chunks (
                chunk_id TEXT PRIMARY KEY,
                article_id TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                text TEXT NOT NULL,
                char_start INTEGER,
                char_end INTEGER,
                token_estimate INTEGER,
                metadata_json TEXT,
                FOREIGN KEY(article_id) REFERENCES articles(article_id) ON DELETE CASCADE
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS series (
                series_id TEXT PRIMARY KEY,
                name TEXT,
                int_id INTEGER,
                created_at TEXT,
                article_count INTEGER DEFAULT 0,
                metadata_json TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS article_tags (
                article_id TEXT NOT NULL,
                tag TEXT NOT NULL,
                tag_type TEXT NOT NULL DEFAULT 'keyword',
                PRIMARY KEY(article_id, tag, tag_type),
                FOREIGN KEY(article_id) REFERENCES articles(article_id) ON DELETE CASCADE
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sync_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT,
                target TEXT NOT NULL,
                status TEXT NOT NULL,
                detail TEXT,
                created_at TEXT NOT NULL
            )
            """
        )

        cur.execute("CREATE INDEX IF NOT EXISTS idx_articles_date ON articles(date)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_articles_section ON articles(section_name)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(source_url)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_chunks_article ON article_chunks(article_id)")

        try:
            cur.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
                    article_id UNINDEXED,
                    title,
                    content,
                    summary,
                    keywords,
                    section_name,
                    category
                )
                """
            )
        except sqlite3.OperationalError:
            # 某些 SQLite 构建可能不带 FTS5；核心库仍然可用，搜索会退回 LIKE。
            pass

        cur.execute(
            "INSERT OR REPLACE INTO schema_info(key, value) VALUES (?, ?)",
            ("schema_version", str(SCHEMA_VERSION)),
        )
        self.conn.commit()

    def normalize_article(self, article: Dict) -> Dict:
        item = dict(article)
        item["source"] = item.get("source") or PEOPLE_DAILY_SOURCE
        item["date"] = normalize_date(item.get("date", ""))
        item["source_url"] = item.get("source_url") or item.get("url") or ""
        item["url"] = item.get("url") or item.get("source_url") or ""
        item["article_id"] = item.get("article_id") or build_article_id(item)

        section_no = item.get("section_no") or item.get("section_id") or item.get("section")
        if isinstance(section_no, str):
            section_no = section_no.replace("第", "").replace("版", "").strip()
        item["section_no"] = section_no or ""
        item["section_name"] = item.get("section_name") or item.get("plate") or ""
        item["plate"] = item.get("plate") or item.get("section_name") or ""

        content = item.get("content") or ""
        if not content:
            content = item.get("markdown_body") or ""
        item["content"] = content
        item["content_hash"] = item.get("content_hash") or content_hash(content)
        item["word_count"] = int(item.get("word_count") or len(content))

        return item

    def upsert_article(self, article: Dict):
        item = self.normalize_article(article)
        now = datetime.now().isoformat(timespec="seconds")
        existing = self.conn.execute(
            "SELECT created_at FROM articles WHERE article_id = ?",
            (item["article_id"],),
        ).fetchone()
        created_at = existing["created_at"] if existing else now

        year = int(item["date"][:4]) if item.get("date") and len(item["date"]) >= 4 else None
        month = int(item["date"][5:7]) if item.get("date") and len(item["date"]) >= 7 else None
        keywords = item.get("keywords") or []
        related_titles = item.get("related_titles") or []

        self.conn.execute(
            """
            INSERT OR REPLACE INTO articles (
                article_id, source, source_url, title, author, date, year, month,
                section_no, section_name, category, keywords_json, summary,
                content, markdown_body, raw_path, markdown_path, content_hash,
                word_count, series_id, series_name, series_part, related_titles_json,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item["article_id"],
                item["source"],
                item.get("source_url", ""),
                item.get("title", "") or "无标题",
                item.get("author", ""),
                item.get("date", ""),
                year,
                month,
                item.get("section_no", ""),
                item.get("section_name", ""),
                item.get("category", ""),
                json.dumps(keywords, ensure_ascii=False),
                item.get("summary", ""),
                item.get("content", ""),
                item.get("markdown_body", ""),
                item.get("raw_path", ""),
                item.get("markdown_path", ""),
                item.get("content_hash", ""),
                item.get("word_count", 0),
                item.get("series_id"),
                item.get("series_name"),
                item.get("series_part"),
                json.dumps(related_titles, ensure_ascii=False),
                created_at,
                now,
            ),
        )

        self._replace_article_tags(item["article_id"], keywords, "keyword")
        self._replace_chunks(item)
        self._upsert_fts(item)
        self.conn.commit()

    def upsert_articles(self, articles: Iterable[Dict]):
        for article in articles:
            self.upsert_article(article)

    def _replace_article_tags(self, article_id: str, tags: Sequence[str], tag_type: str):
        self.conn.execute(
            "DELETE FROM article_tags WHERE article_id = ? AND tag_type = ?",
            (article_id, tag_type),
        )
        for tag in tags:
            tag = str(tag).strip()
            if not tag:
                continue
            self.conn.execute(
                "INSERT OR IGNORE INTO article_tags(article_id, tag, tag_type) VALUES (?, ?, ?)",
                (article_id, tag, tag_type),
            )

    def _replace_chunks(self, item: Dict, size: int = 900, overlap: int = 120):
        article_id = item["article_id"]
        content = item.get("content", "") or ""
        self.conn.execute("DELETE FROM article_chunks WHERE article_id = ?", (article_id,))
        if not content.strip():
            return

        chunks = make_chunks(content, size=size, overlap=overlap)
        for index, chunk in enumerate(chunks):
            chunk_id = f"{article_id}_{index:04d}"
            metadata = {
                "title": item.get("title", ""),
                "date": item.get("date", ""),
                "section_name": item.get("section_name", ""),
                "source_url": item.get("source_url", ""),
            }
            self.conn.execute(
                """
                INSERT INTO article_chunks(
                    chunk_id, article_id, chunk_index, text, char_start,
                    char_end, token_estimate, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk_id,
                    article_id,
                    index,
                    chunk["text"],
                    chunk["char_start"],
                    chunk["char_end"],
                    max(1, len(chunk["text"]) // 2),
                    json.dumps(metadata, ensure_ascii=False),
                ),
            )

    def _upsert_fts(self, item: Dict):
        has_fts = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='articles_fts'"
        ).fetchone()
        if not has_fts:
            return

        self.conn.execute("DELETE FROM articles_fts WHERE article_id = ?", (item["article_id"],))
        self.conn.execute(
            """
            INSERT INTO articles_fts(article_id, title, content, summary, keywords, section_name, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item["article_id"],
                item.get("title", ""),
                item.get("content", ""),
                item.get("summary", ""),
                " ".join(item.get("keywords") or []),
                item.get("section_name", ""),
                item.get("category", ""),
            ),
        )

    def replace_series_registry(self, registry: Dict):
        self.conn.execute("DELETE FROM series")
        for series_id, info in registry.items():
            articles = info.get("articles", [])
            self.conn.execute(
                """
                INSERT OR REPLACE INTO series(
                    series_id, name, int_id, created_at, article_count, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    series_id,
                    info.get("name", ""),
                    info.get("int_id"),
                    info.get("created", ""),
                    len(articles),
                    json.dumps(info, ensure_ascii=False),
                ),
            )
        self.conn.commit()

    def get_articles(
        self,
        dates: Optional[Sequence[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        where = []
        params: List[object] = []

        if dates:
            normalized_dates = [normalize_date(d) for d in dates]
            placeholders = ",".join("?" for _ in normalized_dates)
            where.append(f"date IN ({placeholders})")
            params.extend(normalized_dates)
        if start_date:
            where.append("date >= ?")
            params.append(normalize_date(start_date))
        if end_date:
            where.append("date <= ?")
            params.append(normalize_date(end_date))
        if category:
            where.append("category = ?")
            params.append(category)

        sql = "SELECT * FROM articles"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY date, section_no, title"
        if limit:
            sql += " LIMIT ?"
            params.append(limit)

        return [row_to_article(row) for row in self.conn.execute(sql, params).fetchall()]

    def search(self, query: str, limit: int = 20) -> List[Dict]:
        query = (query or "").strip()
        if not query:
            return []

        has_fts = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='articles_fts'"
        ).fetchone()
        if has_fts:
            try:
                rows = self.conn.execute(
                    """
                    SELECT a.*
                    FROM articles_fts f
                    JOIN articles a ON a.article_id = f.article_id
                    WHERE articles_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (query, limit),
                ).fetchall()
                if rows:
                    return [row_to_article(row) for row in rows]
            except sqlite3.OperationalError:
                pass

        like = f"%{query}%"
        rows = self.conn.execute(
            """
            SELECT * FROM articles
            WHERE title LIKE ? OR content LIKE ? OR summary LIKE ? OR keywords_json LIKE ?
            ORDER BY date DESC
            LIMIT ?
            """,
            (like, like, like, like, limit),
        ).fetchall()
        return [row_to_article(row) for row in rows]

    def stats(self) -> Dict:
        article_count = self.conn.execute("SELECT COUNT(*) AS c FROM articles").fetchone()["c"]
        chunk_count = self.conn.execute("SELECT COUNT(*) AS c FROM article_chunks").fetchone()["c"]
        date_row = self.conn.execute("SELECT MIN(date) AS start, MAX(date) AS end FROM articles").fetchone()
        return {
            "db_path": self.db_path,
            "article_count": article_count,
            "chunk_count": chunk_count,
            "start_date": date_row["start"],
            "end_date": date_row["end"],
        }

    def record_sync_event(self, article_id: str, target: str, status: str, detail: str = ""):
        self.conn.execute(
            """
            INSERT INTO sync_events(article_id, target, status, detail, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (article_id, target, status, detail, datetime.now().isoformat(timespec="seconds")),
        )
        self.conn.commit()


def make_chunks(content: str, size: int = 900, overlap: int = 120) -> List[Dict]:
    """把正文切成适合 AI 检索的文本块。"""
    text = (content or "").strip()
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks = []
    current = ""
    start = 0
    cursor = 0

    for paragraph in paragraphs:
        candidate = f"{current}\n{paragraph}".strip() if current else paragraph
        if current and len(candidate) > size:
            end = start + len(current)
            chunks.append({"text": current, "char_start": start, "char_end": end})
            prefix = current[-overlap:] if overlap and len(current) > overlap else current
            current = f"{prefix}\n{paragraph}".strip()
            start = max(0, end - len(prefix))
        else:
            if not current:
                start = cursor
            current = candidate
        cursor += len(paragraph) + 1

    if current:
        chunks.append({"text": current, "char_start": start, "char_end": start + len(current)})
    return chunks


def row_to_article(row: sqlite3.Row) -> Dict:
    item = dict(row)
    item["url"] = item.get("source_url") or ""
    item["keywords"] = json.loads(item.pop("keywords_json") or "[]")
    item["related_titles"] = json.loads(item.pop("related_titles_json") or "[]")
    item["plate"] = item.get("section_name") or ""
    return item

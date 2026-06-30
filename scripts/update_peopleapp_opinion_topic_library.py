#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新人民日报 APP 评论热点选题总库。

用途：
1. 扫描 APP 评论库文章，按正文复核后的事件/话题规则归并；
2. 把达到“至少 3 个不同来源媒体评论”的话题标记为热点；
3. 保存 SQLite 统计总库，并导出便于复制给 AI 的 Markdown/CSV 选题库。
"""

import argparse
import csv
import hashlib
import json
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SCRIPTS_ROOT))

from export_peopleapp_opinion_hotspots import build_curated_topics
from modules.article_identity import normalize_date
from modules.peopleapp_opinion import CORE_DIR, DATA_ROOT, EXPORT_DIR, TIMEZONE, load_articles

TOPIC_DB_PATH = CORE_DIR / "hotspot_topics.sqlite"
TOPIC_MD_PATH = DATA_ROOT / "hotspot_topic_library.md"
TOPIC_CSV_PATH = EXPORT_DIR / "hotspot_topic_library.csv"


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def normalize_topic_key(topic: str) -> str:
    return "".join(str(topic or "").split()).lower()


def topic_id(topic: str) -> str:
    digest = hashlib.sha1(normalize_topic_key(topic).encode("utf-8")).hexdigest()[:10]
    return f"peopleapp_hotspot_{digest}"


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS hotspot_topics (
            topic_id TEXT PRIMARY KEY,
            topic TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT '',
            angle TEXT NOT NULL DEFAULT '',
            normalized_topic TEXT NOT NULL,
            status TEXT NOT NULL,
            priority TEXT NOT NULL,
            media_count INTEGER NOT NULL,
            article_count INTEGER NOT NULL,
            start_date TEXT,
            end_date TEXT,
            sources_json TEXT NOT NULL,
            ai_brief TEXT,
            manual_note TEXT,
            selected INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    columns = {row[1] for row in conn.execute("PRAGMA table_info(hotspot_topics)")}
    if "category" not in columns:
        conn.execute("ALTER TABLE hotspot_topics ADD COLUMN category TEXT NOT NULL DEFAULT ''")
    if "angle" not in columns:
        conn.execute("ALTER TABLE hotspot_topics ADD COLUMN angle TEXT NOT NULL DEFAULT ''")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS hotspot_topic_articles (
            topic_id TEXT NOT NULL,
            article_id TEXT NOT NULL,
            date TEXT,
            source_name TEXT,
            title TEXT,
            url TEXT,
            PRIMARY KEY(topic_id, article_id),
            FOREIGN KEY(topic_id) REFERENCES hotspot_topics(topic_id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()


def load_existing_topic_state(conn: sqlite3.Connection) -> Dict[str, sqlite3.Row]:
    ensure_schema(conn)
    rows = conn.execute("SELECT * FROM hotspot_topics").fetchall()
    return {row["topic_id"]: row for row in rows}


def status_for(item: Dict, min_media: int) -> str:
    if item["media_count"] >= min_media:
        return "热点"
    if item["media_count"] >= 2:
        return "候选"
    return "专题"


def priority_for(item: Dict, min_media: int) -> str:
    if item["media_count"] >= min_media + 2 or item["article_count"] >= 6:
        return "S"
    if item["media_count"] >= min_media:
        return "A"
    if item["media_count"] == min_media - 1 or item["article_count"] >= 4:
        return "B"
    return "C"


def article_source(article: Dict) -> str:
    return str(article.get("source_name") or article.get("source") or "未知来源").strip()


def build_ai_brief(item: Dict) -> str:
    article_lines = []
    for article in item["articles"]:
        article_lines.append(
            f"- {article.get('date', '')}｜{article_source(article)}｜"
            f"{article.get('title', '无标题')}｜{article.get('source_url') or article.get('url') or ''}"
        )

    return "\n".join(
        [
            f"选题：{item['topic']}",
            f"分类：{item['category']}",
            f"核心角度：{item['angle']}",
            f"热点判断：{item['media_count']} 家媒体、{item['article_count']} 篇评论集中讨论。",
            f"时间范围：{item['start_date']} 至 {item['end_date']}",
            f"媒体来源：{'、'.join(item['sources'])}",
            "支撑文章：",
            *article_lines,
            "",
            "请基于以上官媒评论材料，写一份热点分析：先概括事件背景，再比较不同媒体的关注角度，最后提炼对申论写作、面试答题和公众号选题的启发。",
        ]
    )


def rows_from_clusters(clusters: List[Dict], min_media: int) -> List[Dict]:
    rows = []
    for item in clusters:
        if item["article_count"] < 2:
            continue
        row = dict(item)
        row["topic_id"] = topic_id(row["topic"])
        row["normalized_topic"] = normalize_topic_key(row["topic"])
        row["status"] = status_for(row, min_media)
        row["priority"] = priority_for(row, min_media)
        row["ai_brief"] = build_ai_brief(row)
        rows.append(row)
    rows.sort(
        key=lambda item: (
            {"热点": 0, "候选": 1, "专题": 2}.get(item["status"], 9),
            {"S": 0, "A": 1, "B": 2, "C": 3}.get(item["priority"], 9),
            -item["media_count"],
            -item["article_count"],
            item["topic"],
        )
    )
    return rows


def refresh_database(conn: sqlite3.Connection, rows: List[Dict]) -> None:
    ensure_schema(conn)
    existing = load_existing_topic_state(conn)
    now = datetime.now(TIMEZONE).isoformat(timespec="seconds")
    active_topic_ids = {row["topic_id"] for row in rows}

    for row in rows:
        old = existing.get(row["topic_id"])
        created_at = old["created_at"] if old else now
        manual_note = old["manual_note"] if old else ""
        selected = old["selected"] if old else 0
        conn.execute(
            """
            INSERT OR REPLACE INTO hotspot_topics (
                topic_id, topic, category, angle, normalized_topic, status, priority, media_count,
                article_count, start_date, end_date, sources_json, ai_brief,
                manual_note, selected, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["topic_id"],
                row["topic"],
                row["category"],
                row["angle"],
                row["normalized_topic"],
                row["status"],
                row["priority"],
                row["media_count"],
                row["article_count"],
                row["start_date"],
                row["end_date"],
                json.dumps(row["sources"], ensure_ascii=False),
                row["ai_brief"],
                manual_note,
                selected,
                created_at,
                now,
            ),
        )
        conn.execute("DELETE FROM hotspot_topic_articles WHERE topic_id = ?", (row["topic_id"],))
        for article in row["articles"]:
            conn.execute(
                """
                INSERT OR REPLACE INTO hotspot_topic_articles (
                    topic_id, article_id, date, source_name, title, url
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    row["topic_id"],
                    article.get("article_id", ""),
                    article.get("date", ""),
                    article_source(article),
                    article.get("title", ""),
                    article.get("source_url") or article.get("url") or "",
                ),
            )

    if active_topic_ids:
        placeholders = ",".join("?" for _ in active_topic_ids)
        conn.execute(
            f"DELETE FROM hotspot_topic_articles WHERE topic_id NOT IN ({placeholders})",
            list(active_topic_ids),
        )
        conn.execute(
            f"DELETE FROM hotspot_topics WHERE topic_id NOT IN ({placeholders})",
            list(active_topic_ids),
        )
    else:
        conn.execute("DELETE FROM hotspot_topic_articles")
        conn.execute("DELETE FROM hotspot_topics")
    conn.commit()


def table_cell(value: object) -> str:
    text = "" if value is None else str(value)
    return " ".join(text.split()).replace("|", "｜")


def markdown_table(headers: List[str], rows: Iterable[List[object]]) -> List[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(table_cell(value) for value in row) + " |")
    return lines


def compact_titles(item: Dict) -> str:
    return "；".join(
        f"{article_source(article)}《{article.get('title', '无标题')}》"
        for article in item["articles"]
    )


def build_markdown(rows: List[Dict], min_media: int, scanned_count: int) -> str:
    generated_at = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M")
    status_counter = Counter(row["status"] for row in rows)
    priority_counter = Counter(row["priority"] for row in rows)

    lines: List[str] = [
        "# APP 评论热点选题库",
        "",
        f"> 自动生成于 {generated_at}。数据来源：`data/peopleapp_opinion/core/articles.sqlite`。",
        f"> 本次共复核 {scanned_count} 篇已下载正文。选题归并采用人工复核后的明确规则；未形成共同议题的文章不强行归类。",
        f"> 热点口径：同一事件或明确母题下，至少 {min_media} 个不同来源媒体发表评论；2 家为候选，单一来源连续评论为专题。",
        "> 统计口径：同来源、同标题的重复稿只计算一次；正文不足 200 字的跳转页或残缺稿不作为支撑；“中国”“消费者”“军事”等泛词不作为归并依据。",
        "> 使用方式：复制下方“AI 分析材料”代码块，交给 AI 写热点分析、申论素材拆解、面试答题框架或公众号选题。",
        "",
        "## 快速看板",
        "",
    ]
    lines.extend(
        markdown_table(
            ["指标", "数量"],
            [
                ["全部话题", len(rows)],
                ["已达热点标准", status_counter.get("热点", 0)],
                ["候选话题", status_counter.get("候选", 0)],
                ["单一来源专题", status_counter.get("专题", 0)],
                ["S/A/B/C", f"{priority_counter.get('S', 0)} / {priority_counter.get('A', 0)} / {priority_counter.get('B', 0)} / {priority_counter.get('C', 0)}"],
            ],
        )
    )

    category_counter = Counter(row["category"] for row in rows)
    lines.extend(["", "## 分类看板", ""])
    lines.extend(
        markdown_table(
            ["分类", "选题数", "选题"],
            [
                [
                    category,
                    count,
                    "；".join(row["topic"] for row in rows if row["category"] == category),
                ]
                for category, count in sorted(category_counter.items())
            ],
        )
    )

    lines.extend(["", "## 热点选题总表", ""])
    lines.extend(
        markdown_table(
            ["分类", "状态", "优先级", "选题", "核心角度", "媒体数", "文章数", "时间范围", "来源", "支撑文章"],
            [
                [
                    row["category"],
                    row["status"],
                    row["priority"],
                    row["topic"],
                    row["angle"],
                    row["media_count"],
                    row["article_count"],
                    f"{row['start_date']} 至 {row['end_date']}",
                    "、".join(row["sources"]),
                    compact_titles(row),
                ]
                for row in rows
            ],
        )
    )

    lines.extend(["", "## AI 分析材料", ""])
    for index, row in enumerate(rows, 1):
        lines.extend(
            [
                f"### {index}. {row['topic']}（{row['status']}｜{row['priority']}）",
                "",
                f"- 时间：{row['start_date']} 至 {row['end_date']}",
                f"- 分类：{row['category']}",
                f"- 核心角度：{row['angle']}",
                f"- 媒体数：{row['media_count']}",
                f"- 文章数：{row['article_count']}",
                f"- 来源：{'、'.join(row['sources'])}",
                "",
                "```text",
                row["ai_brief"],
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def write_csv(rows: List[Dict]) -> None:
    TOPIC_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TOPIC_CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(
            [
                "topic_id",
                "status",
                "priority",
                "topic",
                "category",
                "angle",
                "media_count",
                "article_count",
                "start_date",
                "end_date",
                "sources",
                "ai_brief",
                "article_id",
                "date",
                "source",
                "title",
                "url",
            ]
        )
        for row in rows:
            for article in row["articles"]:
                writer.writerow(
                    [
                        row["topic_id"],
                        row["status"],
                        row["priority"],
                        row["topic"],
                        row["category"],
                        row["angle"],
                        row["media_count"],
                        row["article_count"],
                        row["start_date"],
                        row["end_date"],
                        "、".join(row["sources"]),
                        row["ai_brief"],
                        article.get("article_id", ""),
                        article.get("date", ""),
                        article_source(article),
                        article.get("title", ""),
                        article.get("source_url") or article.get("url") or "",
                    ]
                )


def select_articles(args) -> List[Dict]:
    if args.all:
        return load_articles(limit=args.limit)
    return load_articles(
        start_date=normalize_date(args.start) if args.start else None,
        end_date=normalize_date(args.end) if args.end else None,
        limit=args.limit,
    )


def update_topic_library(args) -> List[Dict]:
    articles = select_articles(args)
    clusters = build_curated_topics(articles)
    rows = rows_from_clusters(clusters, args.min_media)

    conn = connect(TOPIC_DB_PATH)
    try:
        refresh_database(conn, rows)
    finally:
        conn.close()

    TOPIC_MD_PATH.write_text(
        build_markdown(rows, args.min_media, scanned_count=len(articles)),
        encoding="utf-8",
    )
    write_csv(rows)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="更新 APP 评论热点选题总库")
    parser.add_argument("--all", action="store_true", help="扫描全部 APP 评论文章；建议每日任务使用")
    parser.add_argument("--start", help="开始日期 YYYY-MM-DD；不传且不加 --all 时从最早文章开始")
    parser.add_argument("--end", help="结束日期 YYYY-MM-DD")
    parser.add_argument("--limit", type=int, help="限制参与分析的文章数量")
    parser.add_argument("--min-media", type=int, default=3, help="热点至少需要几个不同媒体，默认 3")
    parser.add_argument(
        "--min-similarity",
        type=float,
        default=0.22,
        help="兼容旧命令保留；当前使用正文复核规则，不再按相似度强行聚类",
    )
    args = parser.parse_args()

    if not args.all and not args.start and not args.end:
        args.all = True

    rows = update_topic_library(args)
    hotspot_count = sum(1 for row in rows if row["status"] == "热点")
    candidate_count = sum(1 for row in rows if row["status"] == "候选")
    print("APP 评论热点选题库已更新")
    print(f"全部话题：{len(rows)}")
    print(f"达标热点：{hotspot_count}")
    print(f"候选话题：{candidate_count}")
    print(f"SQLite 总库：{TOPIC_DB_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Markdown 选题库：{TOPIC_MD_PATH.relative_to(PROJECT_ROOT)}")
    print(f"CSV 导出：{TOPIC_CSV_PATH.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

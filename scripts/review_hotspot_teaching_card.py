#!/usr/bin/env python3
"""Review generated teaching cards without changing either source database."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime

import build_hotspot_teaching_daily as builder


def counts(conn: sqlite3.Connection) -> dict[str, int]:
    tables = {
        "topics": "hotspot_topics",
        "sources": "source_articles",
        "links": "topic_article_links",
        "cards": "teaching_cards",
        "daily_editions": "daily_editions",
        "weekly_editions": "weekly_editions",
    }
    return {
        label: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for label, table in tables.items()
    }


def refresh_edition_status(conn: sqlite3.Connection, table: str) -> None:
    rows = conn.execute(f"SELECT edition_id, topic_ids_json FROM {table}").fetchall()
    for row in rows:
        topic_ids = json.loads(row["topic_ids_json"] or "[]")
        if not topic_ids:
            continue
        placeholders = ",".join("?" for _ in topic_ids)
        statuses = {
            item[0]
            for item in conn.execute(
                f"SELECT review_status FROM teaching_cards WHERE topic_id IN ({placeholders})",
                topic_ids,
            )
        }
        status = "published" if statuses == {"published"} else "preview"
        conn.execute(
            f"UPDATE {table} SET status=?, updated_at=? WHERE edition_id=?",
            (status, datetime.now().isoformat(timespec="seconds"), row["edition_id"]),
        )


def list_cards(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        """
        SELECT t.topic_id, t.topic, t.category, c.review_status, c.version,
               t.app_article_count, t.paper_support_count
        FROM hotspot_topics t
        JOIN teaching_cards c ON c.topic_id=t.topic_id
        ORDER BY t.end_date DESC, t.priority, t.topic
        """
    ).fetchall()
    for row in rows:
        print(
            f"{row['topic_id']}\t{row['review_status']}\t{row['topic']}\t"
            f"APP {row['app_article_count']} / 人民日报 {row['paper_support_count']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="审核热点教学卡")
    parser.add_argument("--topic-id", help="稳定热点编号；不填写时只列出待审卡片")
    parser.add_argument(
        "--status",
        choices=("editorial_preview", "reviewed", "published", "rejected"),
        help="新的审核状态",
    )
    parser.add_argument("--note", default="", help="审核说明")
    args = parser.parse_args()

    conn = builder.connect_output()
    if not args.topic_id:
        list_cards(conn)
        conn.close()
        return
    if not args.status:
        parser.error("填写 --topic-id 时必须同时填写 --status")

    row = conn.execute(
        "SELECT card_id, review_status, version FROM teaching_cards WHERE topic_id=?",
        (args.topic_id,),
    ).fetchone()
    if row is None:
        raise SystemExit(f"未找到热点编号：{args.topic_id}")

    now = datetime.now().isoformat(timespec="seconds")
    published_at = now if args.status == "published" else None
    next_version = int(row["version"]) + (1 if row["review_status"] != args.status else 0)
    conn.execute(
        """
        UPDATE teaching_cards
        SET review_status=?, review_note=?, version=?, published_at=?, updated_at=?
        WHERE topic_id=?
        """,
        (args.status, args.note, next_version, published_at, now, args.topic_id),
    )
    if args.status in {"reviewed", "published"}:
        conn.execute(
            """
            UPDATE topic_article_links
            SET reviewed=1
            WHERE topic_id=? AND source_kind=?
            """,
            (args.topic_id, builder.SOURCE_KIND_PAPER),
        )
    refresh_edition_status(conn, "daily_editions")
    refresh_edition_status(conn, "weekly_editions")
    current_counts = counts(conn)
    conn.commit()
    conn.close()

    manifest = builder.export_bundle(current_counts)
    print(
        json.dumps(
            {
                "status": "complete",
                "topic_id": args.topic_id,
                "review_status": args.status,
                "version": next_version,
                "manifest_sha256": manifest["sha256"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

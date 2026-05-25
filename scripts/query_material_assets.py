#!/usr/bin/env python3
"""查询人民日报教研素材资产库。"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "data" / "core" / "material_assets.sqlite"


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def rows(conn: sqlite3.Connection, sql: str, params: Iterable[Any] = ()) -> List[sqlite3.Row]:
    return list(conn.execute(sql, tuple(params)))


def json_list(text: str | None) -> List[str]:
    if not text:
        return []
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return []
    if not isinstance(value, list):
        return [str(value)]
    return [str(item) for item in value]


def print_topics(conn: sqlite3.Connection, date: str | None) -> None:
    params: List[Any] = []
    where = ""
    if date:
        where = "WHERE c.date = ?"
        params.append(date)
    result = rows(
        conn,
        f"""
        SELECT t.name, COUNT(l.card_id) AS card_count
        FROM topics t
        JOIN card_topic_links l ON l.topic_id = t.topic_id
        JOIN material_cards c ON c.card_id = l.card_id
        {where}
        GROUP BY t.topic_id, t.name
        ORDER BY card_count DESC, t.name
        """,
        params,
    )
    print("专题分布")
    for row in result:
        print(f"- {row['name']}：{row['card_count']} 张素材卡")


def print_cards(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    params: List[Any] = []
    joins = """
        LEFT JOIN card_topic_links l ON l.card_id = c.card_id
        LEFT JOIN topics t ON t.topic_id = l.topic_id
    """
    filters: List[str] = []
    if args.date:
        filters.append("c.date = ?")
        params.append(args.date)
    if args.card_type:
        filters.append("c.card_type = ?")
        params.append(args.card_type)
    if args.topic:
        filters.append("t.name LIKE ?")
        params.append(f"%{args.topic}%")
    if args.search:
        filters.append("(c.title LIKE ? OR c.summary LIKE ? OR c.detail LIKE ? OR c.reusable_text LIKE ?)")
        term = f"%{args.search}%"
        params.extend([term, term, term, term])
    where = "WHERE " + " AND ".join(filters) if filters else ""
    result = rows(
        conn,
        f"""
        SELECT c.card_id, c.date, c.card_type, c.priority, c.title, c.summary,
               c.reusable_text, group_concat(DISTINCT t.name) AS topics
        FROM material_cards c
        {joins}
        {where}
        GROUP BY c.card_id
        ORDER BY c.date DESC,
          CASE c.priority WHEN 'A' THEN 1 WHEN 'A-' THEN 2 WHEN 'B+' THEN 3 WHEN 'B' THEN 4 ELSE 5 END,
          c.card_type, c.title
        LIMIT ?
        """,
        [*params, args.limit],
    )
    print("素材卡")
    for row in result:
        print(f"\n[{row['date']}] {row['title']}")
        print(f"  类型：{row['card_type']}｜等级：{row['priority']}｜专题：{row['topics'] or '未归类'}")
        print(f"  摘要：{row['summary']}")
        if row["reusable_text"]:
            print(f"  可复用表达：{row['reusable_text']}")


def print_ideas(conn: sqlite3.Connection, date: str | None) -> None:
    params: List[Any] = []
    where = ""
    if date:
        where = "WHERE date = ?"
        params.append(date)
    result = rows(conn, f"SELECT * FROM content_ideas {where} ORDER BY date DESC, idea_id", params)
    print("公众号选题")
    for row in result:
        print(f"\n[{row['date']}] {row['title']}（{row['status']}）")
        print(f"  平台：{row['platform']}")
        print(f"  角度：{row['angle']}")
        outline = "；".join(json_list(row["outline_json"]))
        if outline:
            print(f"  结构：{outline}")


def print_questions(conn: sqlite3.Connection, date: str | None) -> None:
    params: List[Any] = []
    where = ""
    if date:
        where = "WHERE date = ?"
        params.append(date)
    result = rows(conn, f"SELECT * FROM exam_questions {where} ORDER BY date DESC, question_id", params)
    print("训练题")
    for row in result:
        print(f"\n[{row['date']}] {row['question']}")
        print(f"  题型：{row['question_type']}")
        for point in json_list(row["answer_points_json"]):
            print(f"  - {point}")


def main() -> None:
    parser = argparse.ArgumentParser(description="查询人民日报教研素材资产库")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="素材资产库路径")
    parser.add_argument("--date", help="按日期筛选，例如 2026-05-17")
    parser.add_argument("--topic", help="按专题名称筛选，例如 城市治理")
    parser.add_argument("--card-type", help="按素材类型筛选，例如 案例、框架、公众号选题")
    parser.add_argument("--search", help="按关键词搜索素材卡")
    parser.add_argument("--topics", action="store_true", help="只显示专题分布")
    parser.add_argument("--ideas", action="store_true", help="显示公众号选题")
    parser.add_argument("--questions", action="store_true", help="显示训练题")
    parser.add_argument("--limit", type=int, default=20, help="最多显示多少张素材卡")
    args = parser.parse_args()

    conn = connect(Path(args.db_path))
    if args.topics:
        print_topics(conn, args.date)
    elif args.ideas:
        print_ideas(conn, args.date)
    elif args.questions:
        print_questions(conn, args.date)
    else:
        print_cards(conn, args)


if __name__ == "__main__":
    main()

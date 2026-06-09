#!/usr/bin/env python3
"""Export the content idea pool to a human-readable Markdown table and CSV."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ASSET_DB = ROOT / "data" / "core" / "material_assets.sqlite"
DEFAULT_ARTICLE_DB = ROOT / "data" / "core" / "articles.sqlite"
DEFAULT_MD_PATH = ROOT / "data" / "articles" / "公众号文章" / "选题库.md"
DEFAULT_CSV_PATH = ROOT / "data" / "exports" / "content_ideas.csv"
NOTE_TABLE = "content_idea_notes"


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def json_list(text: Optional[str]) -> List[str]:
    if not text:
        return []
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def table_cell(value: Any) -> str:
    text = "" if value is None else str(value)
    text = " ".join(text.split())
    return text.replace("|", "｜")


def period_parts(date_text: str) -> Dict[str, str]:
    date = datetime.strptime(date_text, "%Y-%m-%d")
    quarter = (date.month - 1) // 3 + 1
    return {
        "year": str(date.year),
        "month": f"{date.year}-{date.month:02d}",
        "quarter": f"{date.year}Q{quarter}",
    }


def fetch_ideas(conn: sqlite3.Connection, start: Optional[str], end: Optional[str]) -> List[sqlite3.Row]:
    ensure_schema(conn)
    filters: List[str] = []
    params: List[str] = []
    if start:
        filters.append("date >= ?")
        params.append(start)
    if end:
        filters.append("date <= ?")
        params.append(end)
    where = f"WHERE {' AND '.join(filters)}" if filters else ""
    return list(
        conn.execute(
            f"""
            SELECT i.*,
                   COALESCE(n.selected, 0) AS selected,
                   COALESCE(n.user_note, '') AS user_note
            FROM content_ideas i
            LEFT JOIN content_idea_notes n ON n.idea_id = i.idea_id
            {where}
            ORDER BY i.date DESC,
              CASE i.priority WHEN 'S' THEN 1 WHEN 'A' THEN 2 WHEN 'B' THEN 3 WHEN 'C' THEN 4 ELSE 5 END,
              CASE i.status WHEN '进行中' THEN 1 WHEN '备选' THEN 2 WHEN '已完成' THEN 3 WHEN '暂缓' THEN 4 ELSE 5 END,
              i.idea_id
            """,
            params,
        )
    )


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS content_ideas (
            idea_id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            title TEXT NOT NULL,
            angle TEXT,
            platform TEXT,
            support_article_ids_json TEXT,
            outline_json TEXT,
            status TEXT NOT NULL DEFAULT '备选',
            priority TEXT NOT NULL DEFAULT 'B',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(content_ideas)")}
    if "priority" not in columns:
        conn.execute("ALTER TABLE content_ideas ADD COLUMN priority TEXT NOT NULL DEFAULT 'B'")
        conn.execute("UPDATE content_ideas SET priority = 'S' WHERE status IN ('优先', '已完成')")
        conn.execute("UPDATE content_ideas SET priority = 'A' WHERE status = '进行中'")
        conn.execute("UPDATE content_ideas SET priority = 'C' WHERE status = '暂缓'")
    conn.execute("UPDATE content_ideas SET priority = 'S' WHERE status = '优先'")
    conn.execute("UPDATE content_ideas SET status = '备选' WHERE status = '优先'")
    conn.execute("UPDATE content_ideas SET status = '备选' WHERE status NOT IN ('备选', '进行中', '已完成', '暂缓')")
    conn.execute("UPDATE content_ideas SET priority = 'B' WHERE priority NOT IN ('S', 'A', 'B', 'C')")
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {NOTE_TABLE} (
            idea_id TEXT PRIMARY KEY,
            selected INTEGER NOT NULL DEFAULT 0,
            user_note TEXT,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def load_article_titles(asset_conn: sqlite3.Connection, article_db: Path) -> Dict[str, str]:
    titles: Dict[str, str] = {}
    for row in asset_conn.execute("SELECT article_id, title FROM article_analysis"):
        titles[row["article_id"]] = row["title"]

    if article_db.exists():
        article_conn = connect(article_db)
        try:
            for row in article_conn.execute("SELECT article_id, title FROM articles"):
                titles.setdefault(row["article_id"], row["title"])
        finally:
            article_conn.close()
    return titles


def idea_record(row: sqlite3.Row, article_titles: Dict[str, str]) -> Dict[str, Any]:
    parts = period_parts(row["date"])
    support_ids = json_list(row["support_article_ids_json"])
    support_titles = [article_titles.get(article_id, article_id) for article_id in support_ids]
    outline = json_list(row["outline_json"])
    return {
        "idea_id": row["idea_id"],
        "date": row["date"],
        **parts,
        "status": row["status"],
        "priority": row["priority"],
        "selected": "是" if row["selected"] else "",
        "platform": row["platform"] or "",
        "title": row["title"],
        "angle": row["angle"] or "",
        "support_article_count": len(support_ids),
        "support_article_ids": "；".join(support_ids),
        "support_article_titles": "；".join(support_titles),
        "outline": "；".join(outline),
        "user_note": row["user_note"] or "",
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def markdown_table(headers: List[str], rows: Iterable[List[Any]]) -> List[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(table_cell(value) for value in row) + " |")
    return lines


def build_markdown(records: List[Dict[str, Any]]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    status_counts = Counter(record["status"] for record in records)
    priority_counts = Counter(record["priority"] for record in records)
    month_status: Dict[str, Counter] = defaultdict(Counter)
    quarter_status: Dict[str, Counter] = defaultdict(Counter)
    month_priority: Dict[str, Counter] = defaultdict(Counter)
    quarter_priority: Dict[str, Counter] = defaultdict(Counter)
    for record in records:
        month_status[record["month"]][record["status"]] += 1
        quarter_status[record["quarter"]][record["status"]] += 1
        month_priority[record["month"]][record["priority"]] += 1
        quarter_priority[record["quarter"]][record["priority"]] += 1

    lines: List[str] = [
        "# 公众号选题库",
        "",
        f"> 自动生成于 {now}。数据来源：`data/core/material_assets.sqlite` 的 `content_ideas` 表。",
        "> 精筛口径：每个主选题至少绑定 3 篇人民日报文章；重复度高的标题已合并；素材不足的标题不进入主表。",
        "> 每次完成文章梳理后，先运行 `python3 scripts/import_analysis_content_ideas.py` 同步 analysis 选题，再运行 `python3 scripts/refine_content_ideas.py` 精筛去重并刷新本表。打开本地选题工作台时会自动同步和精筛一次。",
        "",
        "## 快速看板",
        "",
    ]
    lines.extend(
        markdown_table(
            ["指标", "数量"],
            [
                ["全部选题", len(records)],
                ["已精筛", sum(1 for record in records if record["selected"])],
                ["S级", priority_counts.get("S", 0)],
                ["A/B/C级", f"{priority_counts.get('A', 0)} / {priority_counts.get('B', 0)} / {priority_counts.get('C', 0)}"],
                ["备选", status_counts.get("备选", 0)],
                ["进行中", status_counts.get("进行中", 0)],
                ["已完成", status_counts.get("已完成", 0)],
                ["涉及月份", "、".join(sorted(month_status.keys(), reverse=True))],
            ],
        )
    )

    lines.extend(["", "## 按月统计", ""])
    lines.extend(
        markdown_table(
            ["月份", "全部", "S", "A", "B", "C", "备选", "进行中", "已完成", "暂缓"],
            [
                [
                    month,
                    sum(counter.values()),
                    month_priority[month].get("S", 0),
                    month_priority[month].get("A", 0),
                    month_priority[month].get("B", 0),
                    month_priority[month].get("C", 0),
                    counter.get("备选", 0),
                    counter.get("进行中", 0),
                    counter.get("已完成", 0),
                    counter.get("暂缓", 0),
                ]
                for month, counter in sorted(month_status.items(), reverse=True)
            ],
        )
    )

    lines.extend(["", "## 按季度统计", ""])
    lines.extend(
        markdown_table(
            ["季度", "全部", "S", "A", "B", "C", "备选", "进行中", "已完成", "暂缓"],
            [
                [
                    quarter,
                    sum(counter.values()),
                    quarter_priority[quarter].get("S", 0),
                    quarter_priority[quarter].get("A", 0),
                    quarter_priority[quarter].get("B", 0),
                    quarter_priority[quarter].get("C", 0),
                    counter.get("备选", 0),
                    counter.get("进行中", 0),
                    counter.get("已完成", 0),
                    counter.get("暂缓", 0),
                ]
                for quarter, counter in sorted(quarter_status.items(), reverse=True)
            ],
        )
    )

    lines.extend(["", "## 选题总表", ""])
    lines.extend(
        markdown_table(
            ["日期", "月份", "季度", "精筛", "优先级", "状态", "平台", "选题", "切入角度", "支撑文章数", "支撑文章", "大纲", "备注"],
            [
                [
                    record["date"],
                    record["month"],
                    record["quarter"],
                    record["selected"],
                    record["priority"],
                    record["status"],
                    record["platform"],
                    record["title"],
                    record["angle"],
                    record["support_article_count"],
                    record["support_article_titles"],
                    record["outline"],
                    record["user_note"],
                ]
                for record in records
            ],
        )
    )
    lines.append("")
    return "\n".join(lines)


def write_csv(path: Path, records: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "idea_id",
        "date",
        "year",
        "month",
        "quarter",
        "selected",
        "priority",
        "status",
        "platform",
        "title",
        "angle",
        "support_article_count",
        "support_article_ids",
        "support_article_titles",
        "outline",
        "user_note",
        "created_at",
        "updated_at",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def write_markdown(path: Path, records: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_markdown(records), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="导出公众号选题库 Markdown 和 CSV")
    parser.add_argument("--db-path", default=str(DEFAULT_ASSET_DB), help="素材资产库路径")
    parser.add_argument("--article-db", default=str(DEFAULT_ARTICLE_DB), help="文章核心库路径")
    parser.add_argument("--md-path", default=str(DEFAULT_MD_PATH), help="Markdown 选题库输出路径")
    parser.add_argument("--csv-path", default=str(DEFAULT_CSV_PATH), help="CSV 选题库输出路径")
    parser.add_argument("--start", help="开始日期，例如 2026-05-01")
    parser.add_argument("--end", help="结束日期，例如 2026-05-31")
    args = parser.parse_args()

    db_path = Path(args.db_path)
    if not db_path.exists():
        raise SystemExit(f"未找到素材资产库: {db_path}")

    conn = connect(db_path)
    try:
        article_titles = load_article_titles(conn, Path(args.article_db))
        records = [idea_record(row, article_titles) for row in fetch_ideas(conn, args.start, args.end)]
    finally:
        conn.close()

    write_markdown(Path(args.md_path), records)
    write_csv(Path(args.csv_path), records)
    print(f"已导出 {len(records)} 个选题")
    print(f"Markdown: {args.md_path}")
    print(f"CSV: {args.csv_path}")


if __name__ == "__main__":
    main()

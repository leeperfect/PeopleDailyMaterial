#!/usr/bin/env python3
"""导入人民日报教研素材卡，生成可复用的素材资产库。

这个脚本不修改原有的 data/core/articles.sqlite。它把 AI/老师整理出的
结构化 JSON 写入 data/core/material_assets.sqlite，并导出一份 Markdown
视图，方便在 Obsidian 或普通编辑器里阅读。
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = ROOT / "data" / "core" / "material_assets.sqlite"


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def dumps(value: Any) -> str:
    return json.dumps(value if value is not None else [], ensure_ascii=False)


def as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
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
        CREATE TABLE IF NOT EXISTS article_analysis (
            analysis_id TEXT PRIMARY KEY,
            article_id TEXT NOT NULL,
            date TEXT NOT NULL,
            title TEXT NOT NULL,
            section_no TEXT,
            section_name TEXT,
            source_url TEXT,
            priority TEXT NOT NULL,
            one_sentence TEXT,
            core_facts_json TEXT,
            governance_logic TEXT,
            essay_use TEXT,
            interview_use TEXT,
            content_use TEXT,
            reuse_warning TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS topics (
            topic_id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS material_cards (
            card_id TEXT PRIMARY KEY,
            article_id TEXT,
            date TEXT NOT NULL,
            card_type TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT 'B',
            title TEXT NOT NULL,
            summary TEXT,
            detail TEXT,
            reusable_text TEXT,
            source_evidence TEXT,
            source_url TEXT,
            metadata_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS card_topic_links (
            card_id TEXT NOT NULL,
            topic_id TEXT NOT NULL,
            relation_note TEXT,
            PRIMARY KEY (card_id, topic_id),
            FOREIGN KEY(card_id) REFERENCES material_cards(card_id) ON DELETE CASCADE,
            FOREIGN KEY(topic_id) REFERENCES topics(topic_id) ON DELETE CASCADE
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_reviews (
            date TEXT PRIMARY KEY,
            source_dir TEXT,
            article_count INTEGER,
            one_sentence TEXT,
            main_lines_json TEXT,
            high_value_articles_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
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
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS exam_questions (
            question_id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            question_type TEXT,
            question TEXT NOT NULL,
            answer_points_json TEXT,
            support_article_ids_json TEXT,
            topics_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_article_analysis_date ON article_analysis(date)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_cards_date ON material_cards(date)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_cards_article ON material_cards(article_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_cards_type ON material_cards(card_type)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_card_topic_topic ON card_topic_links(topic_id)")
    try:
        cur.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS material_cards_fts USING fts5(
                card_id UNINDEXED,
                title,
                summary,
                detail,
                reusable_text,
                source_evidence
            )
            """
        )
    except sqlite3.OperationalError:
        pass
    cur.execute(
        "INSERT OR REPLACE INTO schema_info(key, value) VALUES (?, ?)",
        ("schema_version", "1"),
    )
    conn.commit()


def upsert_topics(conn: sqlite3.Connection, topics: Iterable[Dict[str, Any]]) -> None:
    stamp = now()
    for topic in topics:
        conn.execute(
            """
            INSERT INTO topics(topic_id, name, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(topic_id) DO UPDATE SET
                name=excluded.name,
                description=excluded.description,
                updated_at=excluded.updated_at
            """,
            (
                topic["topic_id"],
                topic["name"],
                topic.get("description", ""),
                stamp,
                stamp,
            ),
        )


def upsert_daily_review(conn: sqlite3.Connection, payload: Dict[str, Any]) -> None:
    stamp = now()
    review = payload["daily_review"]
    conn.execute(
        """
        INSERT INTO daily_reviews(
            date, source_dir, article_count, one_sentence, main_lines_json,
            high_value_articles_json, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(date) DO UPDATE SET
            source_dir=excluded.source_dir,
            article_count=excluded.article_count,
            one_sentence=excluded.one_sentence,
            main_lines_json=excluded.main_lines_json,
            high_value_articles_json=excluded.high_value_articles_json,
            updated_at=excluded.updated_at
        """,
        (
            payload["date"],
            payload.get("source_dir", ""),
            payload.get("article_count", 0),
            review.get("one_sentence", ""),
            dumps(review.get("main_lines", [])),
            dumps(review.get("high_value_articles", [])),
            stamp,
            stamp,
        ),
    )


def upsert_article_analysis(conn: sqlite3.Connection, payload: Dict[str, Any]) -> None:
    stamp = now()
    for item in payload.get("article_analysis", []):
        conn.execute(
            """
            INSERT INTO article_analysis(
                analysis_id, article_id, date, title, section_no, section_name, source_url,
                priority, one_sentence, core_facts_json, governance_logic, essay_use,
                interview_use, content_use, reuse_warning, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(analysis_id) DO UPDATE SET
                article_id=excluded.article_id,
                date=excluded.date,
                title=excluded.title,
                section_no=excluded.section_no,
                section_name=excluded.section_name,
                source_url=excluded.source_url,
                priority=excluded.priority,
                one_sentence=excluded.one_sentence,
                core_facts_json=excluded.core_facts_json,
                governance_logic=excluded.governance_logic,
                essay_use=excluded.essay_use,
                interview_use=excluded.interview_use,
                content_use=excluded.content_use,
                reuse_warning=excluded.reuse_warning,
                updated_at=excluded.updated_at
            """,
            (
                item["analysis_id"],
                item["article_id"],
                item["date"],
                item["title"],
                item.get("section_no", ""),
                item.get("section_name", ""),
                item.get("source_url", ""),
                item["priority"],
                item.get("one_sentence", ""),
                dumps(item.get("core_facts", [])),
                item.get("governance_logic", ""),
                item.get("essay_use", ""),
                item.get("interview_use", ""),
                item.get("content_use", ""),
                item.get("reuse_warning", ""),
                stamp,
                stamp,
            ),
        )


def upsert_cards(conn: sqlite3.Connection, payload: Dict[str, Any]) -> None:
    stamp = now()
    for card in payload.get("material_cards", []):
        conn.execute(
            """
            INSERT INTO material_cards(
                card_id, article_id, date, card_type, priority, title, summary,
                detail, reusable_text, source_evidence, source_url, metadata_json,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(card_id) DO UPDATE SET
                article_id=excluded.article_id,
                date=excluded.date,
                card_type=excluded.card_type,
                priority=excluded.priority,
                title=excluded.title,
                summary=excluded.summary,
                detail=excluded.detail,
                reusable_text=excluded.reusable_text,
                source_evidence=excluded.source_evidence,
                source_url=excluded.source_url,
                metadata_json=excluded.metadata_json,
                updated_at=excluded.updated_at
            """,
            (
                card["card_id"],
                card.get("article_id", ""),
                card["date"],
                card["card_type"],
                card.get("priority", "B"),
                card["title"],
                card.get("summary", ""),
                card.get("detail", ""),
                card.get("reusable_text", ""),
                card.get("source_evidence", ""),
                card.get("source_url", ""),
                dumps(card.get("metadata", {})),
                stamp,
                stamp,
            ),
        )
        conn.execute("DELETE FROM card_topic_links WHERE card_id = ?", (card["card_id"],))
        for topic_id in as_list(card.get("topic_ids", [])):
            conn.execute(
                """
                INSERT OR REPLACE INTO card_topic_links(card_id, topic_id, relation_note)
                VALUES (?, ?, ?)
                """,
                (card["card_id"], topic_id, card.get("topic_note", "")),
            )
        try:
            conn.execute("DELETE FROM material_cards_fts WHERE card_id = ?", (card["card_id"],))
            conn.execute(
                """
                INSERT INTO material_cards_fts(
                    card_id, title, summary, detail, reusable_text, source_evidence
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    card["card_id"],
                    card["title"],
                    card.get("summary", ""),
                    card.get("detail", ""),
                    card.get("reusable_text", ""),
                    card.get("source_evidence", ""),
                ),
            )
        except sqlite3.OperationalError:
            pass


def upsert_content_ideas(conn: sqlite3.Connection, payload: Dict[str, Any]) -> None:
    stamp = now()
    for idea in payload.get("content_ideas", []):
        conn.execute(
            """
            INSERT INTO content_ideas(
                idea_id, date, title, angle, platform, support_article_ids_json,
                outline_json, status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(idea_id) DO UPDATE SET
                title=excluded.title,
                angle=excluded.angle,
                platform=excluded.platform,
                support_article_ids_json=excluded.support_article_ids_json,
                outline_json=excluded.outline_json,
                status=excluded.status,
                updated_at=excluded.updated_at
            """,
            (
                idea["idea_id"],
                payload["date"],
                idea["title"],
                idea.get("angle", ""),
                idea.get("platform", ""),
                dumps(idea.get("support_article_ids", [])),
                dumps(idea.get("outline", [])),
                idea.get("status", "备选"),
                stamp,
                stamp,
            ),
        )


def upsert_exam_questions(conn: sqlite3.Connection, payload: Dict[str, Any]) -> None:
    stamp = now()
    for question in payload.get("exam_questions", []):
        conn.execute(
            """
            INSERT INTO exam_questions(
                question_id, date, question_type, question, answer_points_json,
                support_article_ids_json, topics_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(question_id) DO UPDATE SET
                question_type=excluded.question_type,
                question=excluded.question,
                answer_points_json=excluded.answer_points_json,
                support_article_ids_json=excluded.support_article_ids_json,
                topics_json=excluded.topics_json,
                updated_at=excluded.updated_at
            """,
            (
                question["question_id"],
                payload["date"],
                question.get("question_type", ""),
                question["question"],
                dumps(question.get("answer_points", [])),
                dumps(question.get("support_article_ids", [])),
                dumps(question.get("topics", [])),
                stamp,
                stamp,
            ),
        )


def import_payload(conn: sqlite3.Connection, payload: Dict[str, Any]) -> None:
    upsert_topics(conn, payload.get("topics", []))
    upsert_daily_review(conn, payload)
    upsert_article_analysis(conn, payload)
    upsert_cards(conn, payload)
    upsert_content_ideas(conn, payload)
    upsert_exam_questions(conn, payload)
    conn.commit()


def rows(conn: sqlite3.Connection, sql: str, params: Iterable[Any] = ()) -> List[sqlite3.Row]:
    return list(conn.execute(sql, tuple(params)))


def json_list(text: str | None) -> List[Any]:
    if not text:
        return []
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return []
    return value if isinstance(value, list) else [value]


def export_markdown(conn: sqlite3.Connection, date: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    review = rows(conn, "SELECT * FROM daily_reviews WHERE date = ?", (date,))
    if not review:
        raise SystemExit(f"未找到 {date} 的每日复盘数据")
    review_row = review[0]
    topic_rows = rows(
        conn,
        """
        SELECT t.name, t.topic_id, COUNT(l.card_id) AS card_count
        FROM topics t
        JOIN card_topic_links l ON l.topic_id = t.topic_id
        JOIN material_cards c ON c.card_id = l.card_id
        WHERE c.date = ?
        GROUP BY t.topic_id, t.name
        ORDER BY card_count DESC, t.name
        """,
        (date,),
    )
    article_rows = rows(
        conn,
        """
        SELECT title, priority, one_sentence, essay_use, interview_use, content_use, reuse_warning
        FROM article_analysis
        WHERE date = ?
        ORDER BY
          CASE priority WHEN 'A' THEN 1 WHEN 'A-' THEN 2 WHEN 'B+' THEN 3 WHEN 'B' THEN 4 ELSE 5 END,
          title
        """,
        (date,),
    )
    card_rows = rows(
        conn,
        """
        SELECT c.card_id, c.card_type, c.priority, c.title, c.summary, c.reusable_text,
               c.source_evidence, group_concat(t.name, ' / ') AS topics
        FROM material_cards c
        LEFT JOIN card_topic_links l ON l.card_id = c.card_id
        LEFT JOIN topics t ON t.topic_id = l.topic_id
        WHERE c.date = ?
        GROUP BY c.card_id
        ORDER BY
          CASE c.priority WHEN 'A' THEN 1 WHEN 'A-' THEN 2 WHEN 'B+' THEN 3 WHEN 'B' THEN 4 ELSE 5 END,
          c.card_type, c.title
        """,
        (date,),
    )
    idea_rows = rows(conn, "SELECT * FROM content_ideas WHERE date = ? ORDER BY idea_id", (date,))
    question_rows = rows(conn, "SELECT * FROM exam_questions WHERE date = ? ORDER BY question_id", (date,))

    lines: List[str] = [
        "---",
        "type: material_assets_view",
        f"date: {date}",
        f"source: data/core/material_assets.sqlite",
        "---",
        "",
        f"# {date} 人民日报结构化教研素材库视图",
        "",
        "## 一句话总判断",
        "",
        review_row["one_sentence"],
        "",
        "## 热点专题仪表盘",
        "",
        "| 专题 | 素材卡数量 |",
        "|---|---:|",
    ]
    for topic in topic_rows:
        lines.append(f"| {topic['name']} | {topic['card_count']} |")

    lines.extend(["", "## 高价值文章教研判断", "", "| 等级 | 文章 | 一句话判断 | 申论可用 | 面试可用 |", "|---|---|---|---|---|"])
    for article in article_rows:
        lines.append(
            f"| {article['priority']} | 《{article['title']}》 | {article['one_sentence']} | "
            f"{article['essay_use']} | {article['interview_use']} |"
        )

    lines.extend(["", "## 素材卡片", ""])
    for card in card_rows:
        lines.extend(
            [
                f"### {card['title']}",
                "",
                f"- 类型：{card['card_type']}",
                f"- 等级：{card['priority']}",
                f"- 专题：{card['topics'] or '未归类'}",
                f"- 摘要：{card['summary']}",
            ]
        )
        if card["reusable_text"]:
            lines.append(f"- 可复用表达：{card['reusable_text']}")
        if card["source_evidence"]:
            lines.append(f"- 来源依据：{card['source_evidence']}")
        lines.append("")

    lines.extend(["## 公众号选题池", ""])
    for idea in idea_rows:
        support = "、".join(json_list(idea["support_article_ids_json"]))
        outline = "；".join(json_list(idea["outline_json"]))
        lines.extend(
            [
                f"### {idea['title']}",
                "",
                f"- 平台：{idea['platform']}",
                f"- 角度：{idea['angle']}",
                f"- 支撑文章 ID：{support}",
                f"- 展开结构：{outline}",
                f"- 状态：{idea['status']}",
                "",
            ]
        )

    lines.extend(["## 面试与申论训练题", ""])
    for question in question_rows:
        lines.extend([f"### {question['question']}", "", f"- 题型：{question['question_type']}"])
        for point in json_list(question["answer_points_json"]):
            lines.append(f"- {point}")
        lines.append("")

    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def summarize(conn: sqlite3.Connection, date: str) -> Dict[str, int]:
    result: Dict[str, int] = {}
    for key, table in {
        "article_analysis": "article_analysis",
        "material_cards": "material_cards",
        "content_ideas": "content_ideas",
        "exam_questions": "exam_questions",
    }.items():
        row = conn.execute(f"SELECT COUNT(*) AS count FROM {table} WHERE date = ?", (date,)).fetchone()
        result[key] = int(row["count"])
    row = conn.execute(
        """
        SELECT COUNT(DISTINCT l.topic_id) AS count
        FROM card_topic_links l
        JOIN material_cards c ON c.card_id = l.card_id
        WHERE c.date = ?
        """,
        (date,),
    ).fetchone()
    result["linked_topics"] = int(row["count"])
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="导入人民日报教研素材卡数据库")
    parser.add_argument("payload", help="结构化素材 JSON 文件")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="素材资产库路径")
    parser.add_argument("--export-md", default="", help="导出的 Markdown 视图路径")
    args = parser.parse_args()

    payload_path = Path(args.payload)
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    conn = connect(Path(args.db_path))
    init_schema(conn)
    import_payload(conn, payload)

    export_md = Path(args.export_md) if args.export_md else payload_path.with_name(
        payload_path.name.replace("-material-assets.json", "-material-assets-view.md")
    )
    export_markdown(conn, payload["date"], export_md)
    summary = summarize(conn, payload["date"])
    print(json.dumps({"date": payload["date"], "db_path": str(args.db_path), "export_md": str(export_md), **summary}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

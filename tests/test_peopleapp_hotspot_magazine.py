#!/usr/bin/env python3

import importlib.util
import json
import sqlite3
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "serve_peopleapp_hotspot_magazine.py"
SPEC = importlib.util.spec_from_file_location("serve_peopleapp_hotspot_magazine_test", SCRIPT)
assert SPEC and SPEC.loader
magazine = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(magazine)


def build_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE hotspot_topics (
            topic_id TEXT PRIMARY KEY, topic TEXT, category TEXT, angle TEXT, normalized_topic TEXT,
            status TEXT, priority TEXT, media_count INTEGER, article_count INTEGER,
            start_date TEXT, end_date TEXT, sources_json TEXT, ai_brief TEXT,
            manual_note TEXT, selected INTEGER, created_at TEXT, updated_at TEXT
        );
        CREATE TABLE hotspot_topic_articles (
            topic_id TEXT, article_id TEXT, date TEXT, source_name TEXT,
            title TEXT, url TEXT, PRIMARY KEY(topic_id, article_id)
        );
        """
    )
    conn.execute(
        """
        INSERT INTO hotspot_topics VALUES
        ('topic-1', '停车计费规则', '城市治理与公共服务', '收费规则要透明',
         '停车计费规则', '热点', 'A', 3, 4,
         '2026-06-24', '2026-06-26', ?, '选题分析材料', '', 0, 'now', 'now')
        """,
        (json.dumps(["人民日报客户端", "光明网"], ensure_ascii=False),),
    )
    conn.execute(
        """
        INSERT INTO hotspot_topic_articles VALUES
        ('topic-1', 'article-1', '2026-06-26', '人民日报客户端',
         '停车计费，就该分秒必争', 'https://example.com/1')
        """
    )
    conn.commit()
    conn.close()


def test_payload_and_manual_selection_are_persistent(tmp_path, monkeypatch):
    db_path = tmp_path / "hotspot_topics.sqlite"
    build_db(db_path)
    monkeypatch.setattr(magazine, "TOPIC_DB", db_path)

    payload = magazine.topic_payload()
    assert payload["stats"]["hotspots"] == 1
    assert payload["topics"][0]["articles"][0]["title"] == "停车计费，就该分秒必争"

    magazine.update_topic("topic-1", {"selected": True, "manual_note": "适合城市治理课程"})
    updated = magazine.topic_payload()["topics"][0]
    assert updated["selected"] is True
    assert updated["manual_note"] == "适合城市治理课程"


def test_batch_update_changes_selected_state(tmp_path, monkeypatch):
    db_path = tmp_path / "hotspot_topics.sqlite"
    build_db(db_path)
    monkeypatch.setattr(magazine, "TOPIC_DB", db_path)

    result = magazine.batch_update({"topic_ids": ["topic-1"], "selected": True})
    assert result["updated"] == 1
    assert magazine.topic_payload()["stats"]["selected"] == 1

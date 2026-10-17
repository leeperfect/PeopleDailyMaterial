"""Source-checked lesson overlays. Original article and reviewed card rows stay intact."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDITORIAL = ROOT / "data/hotspot_teaching/editorial/lesson-pilots.json"
SNAPSHOT = ROOT / "data/hotspot_teaching/editorial/source-snapshot.json"
SOURCES = (ROOT / "data/core/articles.sqlite", ROOT / "data/peopleapp_opinion/core/articles.sqlite")


def load_lessons(editorial: Path = EDITORIAL, snapshot: Path = SNAPSHOT,
                 source_paths: tuple[Path, ...] = SOURCES) -> dict:
    if not editorial.exists():
        return {}
    lessons = json.loads(editorial.read_text(encoding="utf-8"))["lessons"]
    reviews = {}
    if editorial == EDITORIAL:
        library = editorial.with_name('lesson-library.json')
        if library.exists():
            lessons += json.loads(library.read_text(encoding='utf-8'))['lessons']
        review_path = editorial.with_name('source-review.json')
        if review_path.exists():
            reviews = json.loads(review_path.read_text(encoding='utf-8'))
    pinned = json.loads(snapshot.read_text(encoding="utf-8")) if snapshot.exists() else {}
    wanted = {aid for item in lessons for aid in item["source_ids"]}
    sources = {}
    for path in source_paths:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        for aid in wanted:
            row = conn.execute("SELECT article_id,title,date,source,source_url,content FROM articles WHERE article_id=?", (aid,)).fetchone()
            if row:
                rec = dict(row)
                rec["sha256"] = hashlib.sha256(rec.pop("content").encode("utf-8")).hexdigest()
                sources[aid] = rec
        conn.close()
    result = {}
    for item in lessons:
        if item['topic_id'] in result:
            raise ValueError(f"重复授课编号：{item['topic_id']}")
        ids = set(item["source_ids"])
        if ids - sources.keys():
            raise ValueError(f"教学样板缺少来源：{sorted(ids - sources.keys())}")
        for fact in item["facts"]:
            if not fact["source_ids"] or not set(fact["source_ids"]) <= ids:
                raise ValueError(f"事实缺少有效出处：{item['title']}")
        for view in item["viewpoints"]:
            if view["source_id"] not in ids:
                raise ValueError(f"媒体观点缺少有效出处：{item['title']}")
        if sum(s["minutes"] for s in item["segments"]) != 10:
            raise ValueError("展开讲解的分段时长应合计10分钟")
        if not item["exercises"] or any(not e["answer"] or not e["points"] for e in item["exercises"]):
            raise ValueError("模拟练习必须配参考答案和观察要点")
        changed = [aid for aid in ids if pinned.get(aid) != sources[aid]["sha256"]]
        result[item["topic_id"]] = {
            **item,
            "sources": [{**sources[aid], 'source_review':reviews.get(aid)} for aid in item["source_ids"]],
            "source_cautions": [reviews[aid] for aid in item['source_ids'] if aid in reviews],
            "basis_until": max(sources[aid]["date"] for aid in ids),
            "source_check": "changed" if changed else "matched",
            "changed_source_ids": changed,
            "review_status": "source_changed" if changed else item["review_status"],
            "teaching_note": "依据所列历史材料编写，模拟题与分析由教研整理，需教师试讲确认。",
        }
    return result

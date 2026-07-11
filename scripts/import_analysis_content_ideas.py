#!/usr/bin/env python3
"""Import content ideas from analysis packages into the central idea pool."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ANALYSIS_DIR = ROOT / "data" / "analysis"
DEFAULT_ASSET_DB = ROOT / "data" / "core" / "material_assets.sqlite"
DEFAULT_MD_PATH = ROOT / "data" / "articles" / "选题库.md"
DEFAULT_CSV_PATH = ROOT / "data" / "exports" / "content_ideas.csv"

STATUS_RANK = {
    "进行中": 4,
    "已完成": 3,
    "备选": 2,
    "暂缓": 1,
}
PRIORITY_RANK = {
    "S": 4,
    "A": 3,
    "B": 2,
    "C": 1,
}


@dataclass
class IdeaCandidate:
    idea_id: str
    date: str
    title: str
    angle: str = ""
    platform: str = "公众号"
    support_article_ids: List[str] = field(default_factory=list)
    outline: List[str] = field(default_factory=list)
    status: str = "备选"
    priority: str = "B"
    source_path: str = ""
    source_kind: str = ""


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


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
        """
        CREATE TABLE IF NOT EXISTS content_idea_notes (
            idea_id TEXT PRIMARY KEY,
            selected INTEGER NOT NULL DEFAULT 0,
            user_note TEXT,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def text_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def json_text_list(value: Any) -> List[str]:
    if not value:
        return []
    if isinstance(value, list):
        return text_list(value)
    try:
        return text_list(json.loads(str(value)))
    except json.JSONDecodeError:
        return text_list(value)


def clean_title(title: str) -> str:
    title = title.strip()
    pairs = {"《": "》", "「": "」", "“": "”", '"': '"'}
    if len(title) >= 2 and title[0] in pairs and title[-1] == pairs[title[0]]:
        title = title[1:-1]
    return title.strip()


def title_key(title: str) -> str:
    return re.sub(r"\s+", "", clean_title(title)).lower()


def normalize_period_label(value: Any, fallback: str) -> str:
    if isinstance(value, dict):
        start = value.get("start") or value.get("from") or fallback
        end = value.get("end") or value.get("to")
        return f"{start}_to_{end}" if end else str(start)
    if value:
        return str(value)
    return fallback


def date_from_period(period: str) -> str:
    match = re.search(r"20\d{2}-\d{2}-\d{2}", period)
    if match:
        return match.group(0)
    match = re.search(r"(20\d{2})-(\d{2})", period)
    if match:
        return f"{match.group(1)}-{match.group(2)}-01"
    return datetime.now().strftime("%Y-%m-%d")


def period_from_payload(payload: Dict[str, Any], source_path: Path) -> Tuple[str, str]:
    fallback = source_path.parent.name
    label = normalize_period_label(
        payload.get("date")
        or payload.get("period")
        or payload.get("date_range")
        or payload.get("dateRange"),
        fallback,
    )
    return label, date_from_period(label)


def period_from_markdown(text: str, source_path: Path) -> Tuple[str, str]:
    frontmatter = text.split("---", 2)
    header = frontmatter[1] if len(frontmatter) >= 3 and text.startswith("---") else ""
    period = ""
    for line in header.splitlines():
        if line.startswith("period:"):
            period = line.split(":", 1)[1].strip()
            break
        if line.startswith("date:"):
            period = line.split(":", 1)[1].strip()
            break
    if not period:
        period = source_path.parent.name
    return period, date_from_period(period)


def stable_idea_id(period: str, title: str, index: int) -> str:
    digest = hashlib.sha1(f"{period}|{title}|{index}".encode("utf-8")).hexdigest()[:10]
    digits = re.sub(r"\D", "", period)[:8] or "analysis"
    return f"idea_{digits}_{digest}"


def status_from_text(explicit_status: str = "") -> str:
    status = explicit_status.strip()
    if status == "优先":
        return "备选"
    return status if status in STATUS_RANK else "备选"


def priority_from_text(priority: str, explicit_status: str = "") -> str:
    text = priority.strip().upper()
    if text.startswith("S"):
        return "S"
    if text.startswith("A"):
        return "A"
    if text.startswith("B"):
        return "B"
    if text.startswith("C"):
        return "C"
    status = explicit_status.strip()
    if status in {"优先", "已完成"}:
        return "S"
    if status == "进行中":
        return "A"
    if status == "暂缓":
        return "C"
    return "B"


def make_angle(*parts: str) -> str:
    return "；".join(part.strip() for part in parts if part and part.strip())


def candidates_from_json(path: Path) -> List[IdeaCandidate]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    period, date = period_from_payload(payload, path)
    candidates: List[IdeaCandidate] = []

    for index, idea in enumerate(payload.get("content_ideas") or [], start=1):
        title = clean_title(str(idea.get("title", "")))
        if not title:
            continue
        priority = str(idea.get("priority", ""))
        angle = make_angle(str(idea.get("angle", "")), str(idea.get("core_argument", "")))
        outline = text_list(idea.get("outline"))
        if not outline and idea.get("core_argument"):
            outline = [str(idea["core_argument"])]
        candidates.append(
            IdeaCandidate(
                idea_id=str(idea.get("idea_id") or stable_idea_id(period, title, index)),
                date=date,
                title=title,
                angle=angle,
                platform=str(idea.get("platform") or "公众号"),
                support_article_ids=text_list(idea.get("support_article_ids")),
                outline=outline,
                status=status_from_text(str(idea.get("status", ""))),
                priority=priority_from_text(priority, str(idea.get("status", ""))),
                source_path=str(path.relative_to(ROOT)),
                source_kind="content_ideas",
            )
        )

    offset = len(candidates)
    for index, idea in enumerate(payload.get("recommended_articles") or [], start=1):
        title = clean_title(str(idea.get("title", "")))
        if not title:
            continue
        priority = str(idea.get("priority", ""))
        reason = str(idea.get("reason", ""))
        candidates.append(
            IdeaCandidate(
                idea_id=stable_idea_id(period, title, offset + index),
                date=date,
                title=title,
                angle=reason,
                platform="公众号",
                outline=text_list(reason),
                status="备选",
                priority=priority_from_text(priority),
                source_path=str(path.relative_to(ROOT)),
                source_kind="recommended_articles",
            )
        )
    return candidates


def candidates_from_theme_shortlist(path: Path) -> List[IdeaCandidate]:
    text = path.read_text(encoding="utf-8")
    period, date = period_from_markdown(text, path)
    lines = text.splitlines()
    candidates: List[IdeaCandidate] = []
    priority_section = ""
    pending: Optional[IdeaCandidate] = None

    def flush() -> None:
        nonlocal pending
        if pending and title_key(pending.title):
            candidates.append(pending)
        pending = None

    for line in lines:
        section_match = re.match(r"^##\s+优先级\s+([A-Z][+-]?)", line)
        if section_match:
            priority_section = section_match.group(1)
            flush()
            continue

        heading_match = re.match(r"^###\s+\d+[.、]\s*(.+)$", line)
        topic_match = re.match(r"^##\s+选题\s*\d+[：:]\s*(.+)$", line)
        if heading_match or topic_match:
            flush()
            raw_title = heading_match.group(1) if heading_match else topic_match.group(1)
            title = clean_title(raw_title)
            pending = IdeaCandidate(
                idea_id=stable_idea_id(period, title, len(candidates) + 1),
                date=date,
                title=title,
                platform="公众号",
                status="备选",
                priority=priority_from_text(priority_section),
                source_path=str(path.relative_to(ROOT)),
                source_kind="theme_shortlist",
            )
            continue

        if not pending:
            continue

        priority_match = re.search(r"优先级[：:]\s*([A-Z][+-]?)", line)
        if priority_match:
            pending.priority = priority_from_text(priority_match.group(1))
            continue

        angle_match = re.match(r"[-*]\s*核心角度[：:]\s*(.+)$", line)
        if angle_match:
            pending.angle = make_angle(pending.angle, angle_match.group(1))
            continue

        article_match = re.match(r"[-*]\s*`?(.+?)`?\s*$", line)
        if article_match and "关键原文" not in line and "可用材料" not in line:
            text_item = article_match.group(1).strip()
            if text_item.startswith("《") and text_item.endswith("》"):
                pending.outline.append(f"支撑材料：{text_item}")

    flush()
    return candidates


def candidates_from_view_list(path: Path) -> List[IdeaCandidate]:
    text = path.read_text(encoding="utf-8")
    period, date = period_from_markdown(text, path)
    lines = text.splitlines()
    candidates: List[IdeaCandidate] = []
    in_section = False

    for line in lines:
        if re.match(r"^##\s+.*最值得开发.*公众号选题", line):
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section:
            continue
        match = re.match(r"^\d+[.、]\s*(.+?)\s*$", line)
        if not match:
            continue
        title = clean_title(match.group(1))
        if not title:
            continue
        candidates.append(
            IdeaCandidate(
                idea_id=stable_idea_id(period, title, len(candidates) + 1),
                date=date,
                title=title,
                platform="公众号",
                status="备选",
                source_path=str(path.relative_to(ROOT)),
                source_kind="material_assets_view",
            )
        )
    return candidates


def merge_candidates(candidates: Iterable[IdeaCandidate]) -> List[IdeaCandidate]:
    merged: Dict[str, IdeaCandidate] = {}
    for candidate in candidates:
        key = title_key(candidate.title)
        if not key:
            continue
        current = merged.get(key)
        if not current:
            merged[key] = candidate
            continue
        if not current.angle and candidate.angle:
            current.angle = candidate.angle
        elif candidate.angle and len(candidate.angle) > len(current.angle):
            current.angle = candidate.angle
        if current.platform == "公众号" and candidate.platform != "公众号":
            current.platform = candidate.platform
        for article_id in candidate.support_article_ids:
            if article_id not in current.support_article_ids:
                current.support_article_ids.append(article_id)
        for item in candidate.outline:
            if item not in current.outline:
                current.outline.append(item)
        if STATUS_RANK.get(candidate.status, 0) > STATUS_RANK.get(current.status, 0):
            current.status = candidate.status
        if PRIORITY_RANK.get(candidate.priority, 0) > PRIORITY_RANK.get(current.priority, 0):
            current.priority = candidate.priority
        if candidate.source_kind in {"content_ideas", "recommended_articles"} and current.source_kind not in {
            "content_ideas",
            "recommended_articles",
        }:
            current.idea_id = candidate.idea_id
            current.source_kind = candidate.source_kind
            current.source_path = candidate.source_path
    return list(merged.values())


def load_candidates(analysis_dir: Path) -> List[IdeaCandidate]:
    candidates: List[IdeaCandidate] = []
    for path in sorted(analysis_dir.glob("**/*material-assets.json")):
        candidates.extend(candidates_from_json(path))
    for path in sorted(analysis_dir.glob("**/*theme-shortlist.md")):
        candidates.extend(candidates_from_theme_shortlist(path))
    for path in sorted(analysis_dir.glob("**/*material-assets-view.md")):
        candidates.extend(candidates_from_view_list(path))
    return merge_candidates(candidates)


def upsert_candidates(conn: sqlite3.Connection, candidates: Iterable[IdeaCandidate], dry_run: bool = False) -> Dict[str, int]:
    ensure_schema(conn)
    now = datetime.now().isoformat(timespec="seconds")
    existing_by_id = {row["idea_id"]: row for row in conn.execute("SELECT * FROM content_ideas")}
    existing_by_title = {title_key(row["title"]): row for row in existing_by_id.values()}
    rejected_keys = rejected_title_keys(conn)
    inserted = 0
    updated = 0
    unchanged = 0
    skipped = 0

    for candidate in candidates:
        key = title_key(candidate.title)
        existing = existing_by_id.get(candidate.idea_id) or existing_by_title.get(key)
        if key in rejected_keys and not existing:
            skipped += 1
            continue
        if rejected_keys and existing and len(json_text_list(existing["support_article_ids_json"])) >= 3:
            unchanged += 1
            continue
        idea_id = existing["idea_id"] if existing else candidate.idea_id
        status = existing["status"] if existing else candidate.status
        priority = existing["priority"] if existing and "priority" in existing.keys() else candidate.priority
        outline = candidate.outline
        if candidate.source_path:
            outline = [*outline, f"来源分析包：{candidate.source_path}"]
        values = (
            idea_id,
            candidate.date,
            candidate.title,
            candidate.angle,
            candidate.platform,
            dumps(candidate.support_article_ids),
            dumps(outline),
            status,
            priority,
            now,
            now,
        )
        if existing:
            next_angle = str(existing["angle"] or "")
            if not next_angle or (candidate.angle and len(candidate.angle) > len(next_angle)):
                next_angle = candidate.angle
            next_platform = str(existing["platform"] or candidate.platform)
            existing_support = json_text_list(existing["support_article_ids_json"])
            existing_outline = json_text_list(existing["outline_json"])
            next_support = existing_support or candidate.support_article_ids
            next_outline = existing_outline or outline
            next_values = {
                "date": candidate.date,
                "title": candidate.title,
                "angle": next_angle,
                "platform": next_platform,
                "support_article_ids_json": dumps(next_support),
                "outline_json": dumps(next_outline),
            }
            changed = (
                str(existing["date"] or "") != next_values["date"]
                or str(existing["title"] or "") != next_values["title"]
                or str(existing["angle"] or "") != next_values["angle"]
                or str(existing["platform"] or "") != next_values["platform"]
                or existing_support != next_support
                or existing_outline != next_outline
            )
            if not changed:
                unchanged += 1
                continue
            if dry_run:
                updated += 1
                continue
            conn.execute(
                """
                UPDATE content_ideas
                SET date = ?,
                    title = ?,
                    angle = ?,
                    platform = ?,
                    support_article_ids_json = ?,
                    outline_json = ?,
                    updated_at = ?
                WHERE idea_id = ?
                """,
                (
                    next_values["date"],
                    next_values["title"],
                    next_values["angle"],
                    next_values["platform"],
                    next_values["support_article_ids_json"],
                    next_values["outline_json"],
                    now,
                    idea_id,
                ),
            )
            updated += 1
        else:
            if dry_run:
                inserted += 1
                continue
            conn.execute(
                """
                INSERT INTO content_ideas(
                    idea_id, date, title, angle, platform, support_article_ids_json,
                    outline_json, status, priority, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values,
            )
            inserted += 1
        existing_by_id[idea_id] = conn.execute("SELECT * FROM content_ideas WHERE idea_id = ?", (idea_id,)).fetchone()
        existing_by_title[title_key(candidate.title)] = existing_by_id[idea_id]

    if not dry_run:
        conn.commit()
    return {"inserted": inserted, "updated": updated, "unchanged": unchanged, "skipped": skipped}


def rejected_title_keys(conn: sqlite3.Connection) -> set[str]:
    table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'content_idea_rejected_keys'"
    ).fetchone()
    if not table:
        return set()
    return {row["title_key"] for row in conn.execute("SELECT title_key FROM content_idea_rejected_keys")}


def refresh_exports() -> None:
    try:
        from . import export_content_ideas
    except ImportError:
        import export_content_ideas

    conn = export_content_ideas.connect(export_content_ideas.DEFAULT_ASSET_DB)
    try:
        article_titles = export_content_ideas.load_article_titles(conn, export_content_ideas.DEFAULT_ARTICLE_DB)
        records = [
            export_content_ideas.idea_record(row, article_titles)
            for row in export_content_ideas.fetch_ideas(conn, None, None)
        ]
    finally:
        conn.close()
    export_content_ideas.write_markdown(DEFAULT_MD_PATH, records)
    export_content_ideas.write_csv(DEFAULT_CSV_PATH, records)


def sync_analysis_content_ideas(
    analysis_dir: Path = DEFAULT_ANALYSIS_DIR,
    db_path: Path = DEFAULT_ASSET_DB,
    dry_run: bool = False,
    refresh: bool = True,
) -> Dict[str, int]:
    candidates = load_candidates(analysis_dir)
    conn = connect(db_path)
    try:
        result = upsert_candidates(conn, candidates, dry_run=dry_run)
    finally:
        conn.close()
    result["candidates"] = len(candidates)
    if refresh and not dry_run:
        refresh_exports()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="把 analysis 历史分析包里的公众号选题导入统一选题库")
    parser.add_argument("--analysis-dir", default=str(DEFAULT_ANALYSIS_DIR), help="analysis 目录")
    parser.add_argument("--db-path", default=str(DEFAULT_ASSET_DB), help="素材资产库路径")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不写入")
    parser.add_argument("--no-refresh", action="store_true", help="不刷新 Markdown/CSV 总表")
    args = parser.parse_args()

    result = sync_analysis_content_ideas(
        analysis_dir=Path(args.analysis_dir),
        db_path=Path(args.db_path),
        dry_run=args.dry_run,
        refresh=not args.no_refresh,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

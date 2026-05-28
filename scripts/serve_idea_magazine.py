#!/usr/bin/env python3
"""Serve a local magazine-style browser for the content idea database."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
ASSET_DB = ROOT / "data" / "core" / "material_assets.sqlite"
ARTICLE_DB = ROOT / "data" / "core" / "articles.sqlite"
SCRIPT_DIR = ROOT / "scripts"
STATUS_OPTIONS = ["优先", "备选", "进行中", "已完成", "暂缓"]

sys.path.insert(0, str(SCRIPT_DIR))


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


def period_parts(date_text: str) -> Dict[str, str]:
    date = datetime.strptime(date_text, "%Y-%m-%d")
    quarter = (date.month - 1) // 3 + 1
    return {
        "year": str(date.year),
        "month": f"{date.year}-{date.month:02d}",
        "quarter": f"{date.year}Q{quarter}",
    }


def ensure_note_table(conn: sqlite3.Connection) -> None:
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


def load_article_map(asset_conn: sqlite3.Connection) -> Dict[str, Dict[str, str]]:
    articles: Dict[str, Dict[str, str]] = {}
    for row in asset_conn.execute("SELECT article_id, title, source_url FROM article_analysis"):
        articles[row["article_id"]] = {
            "article_id": row["article_id"],
            "title": row["title"] or row["article_id"],
            "url": row["source_url"] or "",
            "markdown_path": "",
            "date": row["date"] if "date" in row.keys() else "",
        }

    if ARTICLE_DB.exists():
        article_conn = connect(ARTICLE_DB)
        try:
            for row in article_conn.execute(
                "SELECT article_id, title, source_url, markdown_path, date, section_name FROM articles"
            ):
                articles[row["article_id"]] = {
                    "article_id": row["article_id"],
                    "title": row["title"] or row["article_id"],
                    "url": row["source_url"] or "",
                    "markdown_path": row["markdown_path"] or "",
                    "date": row["date"] or "",
                    "section_name": row["section_name"] or "",
                }
        finally:
            article_conn.close()
    return articles


def row_to_idea(row: sqlite3.Row, article_map: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    support_ids = json_list(row["support_article_ids_json"])
    support_articles = [
        article_map.get(article_id, {"article_id": article_id, "title": article_id, "url": "", "markdown_path": ""})
        for article_id in support_ids
    ]
    outline = json_list(row["outline_json"])
    parts = period_parts(row["date"])
    searchable = " ".join(
        [
            row["title"] or "",
            row["angle"] or "",
            row["platform"] or "",
            row["status"] or "",
            " ".join(outline),
            " ".join(article["title"] for article in support_articles),
            row["user_note"] or "",
        ]
    )
    return {
        "idea_id": row["idea_id"],
        "date": row["date"],
        **parts,
        "title": row["title"],
        "angle": row["angle"] or "",
        "platform": row["platform"] or "",
        "status": row["status"],
        "selected": bool(row["selected"]),
        "user_note": row["user_note"] or "",
        "outline": outline,
        "support_articles": support_articles,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "searchable": searchable.lower(),
    }


def idea_payload() -> Dict[str, Any]:
    if not ASSET_DB.exists():
        raise FileNotFoundError(f"未找到素材资产库: {ASSET_DB}")
    conn = connect(ASSET_DB)
    try:
        ensure_note_table(conn)
        article_map = load_article_map(conn)
        rows = list(
            conn.execute(
                """
                SELECT i.*,
                       COALESCE(n.selected, 0) AS selected,
                       COALESCE(n.user_note, '') AS user_note
                FROM content_ideas i
                LEFT JOIN content_idea_notes n ON n.idea_id = i.idea_id
                ORDER BY i.date DESC,
                  CASE i.status WHEN '优先' THEN 1 WHEN '进行中' THEN 2 WHEN '已完成' THEN 3 WHEN '备选' THEN 4 ELSE 5 END,
                  i.idea_id
                """
            )
        )
    finally:
        conn.close()

    ideas = [row_to_idea(row, article_map) for row in rows]
    status_counts: Dict[str, int] = {}
    month_counts: Dict[str, int] = {}
    quarter_counts: Dict[str, int] = {}
    platforms = set()
    for idea in ideas:
        status_counts[idea["status"]] = status_counts.get(idea["status"], 0) + 1
        month_counts[idea["month"]] = month_counts.get(idea["month"], 0) + 1
        quarter_counts[idea["quarter"]] = quarter_counts.get(idea["quarter"], 0) + 1
        for platform in idea["platform"].replace("，", "+").replace("/", "+").split("+"):
            platform = platform.strip()
            if platform:
                platforms.add(platform)

    return {
        "ideas": ideas,
        "stats": {
            "total": len(ideas),
            "selected": sum(1 for idea in ideas if idea["selected"]),
            "status_counts": status_counts,
            "month_counts": month_counts,
            "quarter_counts": quarter_counts,
        },
        "filters": {
            "statuses": STATUS_OPTIONS,
            "months": sorted(month_counts.keys(), reverse=True),
            "quarters": sorted(quarter_counts.keys(), reverse=True),
            "platforms": sorted(platforms),
        },
    }


def article_search(query: str, limit: int = 40) -> Dict[str, Any]:
    if not ARTICLE_DB.exists():
        return {"articles": []}
    params: List[Any] = []
    where = ""
    if query:
        where = "WHERE title LIKE ? OR summary LIKE ? OR content LIKE ? OR section_name LIKE ?"
        term = f"%{query}%"
        params.extend([term, term, term, term])
    params.append(limit)
    conn = connect(ARTICLE_DB)
    try:
        rows = list(
            conn.execute(
                f"""
                SELECT article_id, title, date, section_name, summary, source_url, markdown_path
                FROM articles
                {where}
                ORDER BY date DESC
                LIMIT ?
                """,
                params,
            )
        )
    finally:
        conn.close()
    return {
        "articles": [
            {
                "article_id": row["article_id"],
                "title": row["title"],
                "date": row["date"],
                "section_name": row["section_name"] or "",
                "summary": row["summary"] or "",
                "url": row["source_url"] or "",
                "markdown_path": row["markdown_path"] or "",
            }
            for row in rows
        ]
    }


def update_idea(idea_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    status = payload.get("status")
    selected = payload.get("selected")
    user_note = payload.get("user_note")
    now = datetime.now().isoformat(timespec="seconds")

    conn = connect(ASSET_DB)
    try:
        ensure_note_table(conn)
        exists = conn.execute("SELECT idea_id FROM content_ideas WHERE idea_id = ?", (idea_id,)).fetchone()
        if not exists:
            raise KeyError(f"未找到选题: {idea_id}")
        if status is not None:
            if status not in STATUS_OPTIONS:
                raise ValueError(f"状态不支持: {status}")
            conn.execute("UPDATE content_ideas SET status = ?, updated_at = ? WHERE idea_id = ?", (status, now, idea_id))

        current = conn.execute("SELECT * FROM content_idea_notes WHERE idea_id = ?", (idea_id,)).fetchone()
        next_selected = int(bool(selected)) if selected is not None else (int(current["selected"]) if current else 0)
        next_note = str(user_note) if user_note is not None else (current["user_note"] if current else "")
        conn.execute(
            """
            INSERT INTO content_idea_notes(idea_id, selected, user_note, updated_at)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(idea_id) DO UPDATE SET
              selected = excluded.selected,
              user_note = excluded.user_note,
              updated_at = excluded.updated_at
            """,
            (idea_id, next_selected, next_note, now),
        )
        conn.commit()
    finally:
        conn.close()
    refresh_exports()
    return {"success": True, "idea_id": idea_id}


def refresh_exports() -> None:
    try:
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
        export_content_ideas.write_markdown(export_content_ideas.DEFAULT_MD_PATH, records)
        export_content_ideas.write_csv(export_content_ideas.DEFAULT_CSV_PATH, records)
    except Exception as exc:
        print(f"刷新 Markdown/CSV 失败: {exc}", file=sys.stderr)


def json_response(handler: BaseHTTPRequestHandler, data: Dict[str, Any], status: int = 200) -> None:
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def html_response(handler: BaseHTTPRequestHandler, html: str) -> None:
    body = html.encode("utf-8")
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class IdeaMagazineHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/":
                html_response(self, HTML)
                return
            if parsed.path == "/api/ideas":
                json_response(self, idea_payload())
                return
            if parsed.path == "/api/articles":
                qs = parse_qs(parsed.query)
                query = qs.get("q", [""])[0].strip()
                limit = int(qs.get("limit", ["40"])[0])
                json_response(self, article_search(query, limit))
                return
            json_response(self, {"error": "Not found"}, HTTPStatus.NOT_FOUND)
        except Exception as exc:
            json_response(self, {"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8") if length else "{}"
            payload = json.loads(body or "{}")
            if parsed.path.startswith("/api/ideas/"):
                idea_id = unquote(parsed.path.removeprefix("/api/ideas/"))
                json_response(self, update_idea(idea_id, payload))
                return
            if parsed.path == "/api/export":
                refresh_exports()
                json_response(self, {"success": True})
                return
            json_response(self, {"error": "Not found"}, HTTPStatus.NOT_FOUND)
        except Exception as exc:
            json_response(self, {"error": str(exc)}, HTTPStatus.BAD_REQUEST)


HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>人民日报选题工作台</title>
  <style>
    :root {
      --paper: #f4efe6;
      --paper-deep: #e6dccb;
      --ink: #17130f;
      --muted: #786f63;
      --line: #c8bca8;
      --accent: #9d1f22;
      --accent-soft: #ead0c9;
      --green: #2f6f58;
      --shadow: 0 18px 44px rgba(48, 35, 21, .12);
      --radius: 6px;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--ink);
      background:
        linear-gradient(90deg, rgba(80, 57, 31, .04) 1px, transparent 1px),
        linear-gradient(var(--paper), var(--paper));
      background-size: 24px 24px, 100% 100%;
      font-family: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
      letter-spacing: 0;
    }
    button, input, select, textarea { font: inherit; letter-spacing: 0; }
    a { color: inherit; }
    .page { min-height: 100vh; padding: 28px clamp(16px, 3vw, 40px) 44px; }
    .masthead {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 24px;
      align-items: end;
      border-bottom: 2px solid var(--ink);
      padding-bottom: 18px;
    }
    .issue {
      display: flex;
      gap: 14px;
      align-items: center;
      color: var(--muted);
      font-size: 13px;
      text-transform: uppercase;
    }
    .issue span { border-top: 1px solid var(--line); padding-top: 6px; }
    h1 {
      margin: 8px 0 0;
      font-family: "Noto Serif SC", "Songti SC", "STSong", serif;
      font-size: clamp(36px, 7vw, 86px);
      line-height: .94;
      font-weight: 800;
    }
    .deck {
      max-width: 440px;
      color: var(--muted);
      line-height: 1.7;
      font-size: 14px;
      border-left: 1px solid var(--line);
      padding-left: 18px;
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      border-bottom: 1px solid var(--ink);
      margin: 18px 0 22px;
    }
    .stat {
      min-height: 86px;
      border-right: 1px solid var(--line);
      padding: 12px 18px 14px 0;
    }
    .stat:last-child { border-right: 0; }
    .stat strong {
      display: block;
      font-family: "Noto Serif SC", "Songti SC", serif;
      font-size: 34px;
      line-height: 1;
      margin-bottom: 8px;
    }
    .stat span { color: var(--muted); font-size: 13px; }
    .toolbar {
      display: grid;
      grid-template-columns: minmax(260px, 1.4fr) repeat(4, minmax(120px, .55fr)) auto;
      gap: 10px;
      align-items: stretch;
      margin-bottom: 22px;
    }
    .field, .action {
      border: 1px solid var(--line);
      background: rgba(255,255,255,.35);
      min-height: 42px;
      border-radius: var(--radius);
      color: var(--ink);
    }
    .field {
      width: 100%;
      padding: 0 12px;
    }
    .action {
      padding: 0 14px;
      cursor: pointer;
    }
    .action:hover, .status-button:hover { border-color: var(--ink); }
    .layout {
      display: grid;
      grid-template-columns: minmax(0, 1.25fr) minmax(340px, .75fr);
      gap: 24px;
      align-items: start;
    }
    .ideas {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }
    .card {
      position: relative;
      min-height: 260px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: rgba(255,255,255,.44);
      padding: 18px;
      cursor: pointer;
      box-shadow: 0 8px 22px rgba(48, 35, 21, .05);
      transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;
    }
    .card:hover, .card.active {
      transform: translateY(-2px);
      border-color: var(--ink);
      box-shadow: var(--shadow);
    }
    .card.active::before {
      content: "";
      position: absolute;
      inset: 0 auto 0 0;
      width: 5px;
      background: var(--accent);
      border-radius: var(--radius) 0 0 var(--radius);
    }
    .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 14px;
    }
    .tag {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      border: 1px solid var(--line);
      padding: 2px 8px;
      border-radius: 999px;
      background: rgba(255,255,255,.38);
      color: var(--muted);
      font-size: 12px;
    }
    .tag.priority { color: var(--accent); border-color: var(--accent-soft); background: rgba(157,31,34,.06); }
    .tag.done { color: var(--green); border-color: rgba(47,111,88,.25); }
    .tag.selected { color: var(--ink); border-color: var(--ink); }
    .card h2 {
      margin: 0 0 12px;
      font-family: "Noto Serif SC", "Songti SC", serif;
      font-size: clamp(21px, 2.3vw, 30px);
      line-height: 1.18;
      font-weight: 800;
    }
    .angle {
      margin: 0 0 16px;
      color: #4d453b;
      line-height: 1.7;
      font-size: 14px;
    }
    .support {
      border-top: 1px solid var(--line);
      padding-top: 12px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.6;
    }
    .panel {
      position: sticky;
      top: 18px;
      border: 1px solid var(--ink);
      border-radius: var(--radius);
      background: rgba(250, 247, 240, .92);
      box-shadow: var(--shadow);
      overflow: hidden;
    }
    .panel-head {
      padding: 18px 18px 16px;
      border-bottom: 1px solid var(--line);
      background: rgba(157,31,34,.06);
    }
    .panel-kicker {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 10px;
    }
    .panel h3 {
      margin: 0;
      font-family: "Noto Serif SC", "Songti SC", serif;
      font-size: 31px;
      line-height: 1.18;
    }
    .panel-body { padding: 18px; }
    .section-title {
      margin: 18px 0 8px;
      font-size: 13px;
      color: var(--accent);
      font-weight: 700;
      letter-spacing: 0;
    }
    .outline {
      margin: 0;
      padding-left: 18px;
      line-height: 1.75;
      color: #3f382f;
    }
    .article-list {
      display: grid;
      gap: 8px;
      margin-top: 8px;
    }
    .article {
      display: block;
      text-decoration: none;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 10px 12px;
      background: rgba(255,255,255,.38);
    }
    .article:hover { border-color: var(--ink); }
    .article small { display: block; color: var(--muted); margin-top: 4px; }
    .ops {
      display: grid;
      gap: 12px;
      margin-top: 16px;
      padding-top: 16px;
      border-top: 1px solid var(--line);
    }
    .status-grid {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 6px;
    }
    .status-button {
      min-height: 34px;
      border: 1px solid var(--line);
      background: rgba(255,255,255,.4);
      border-radius: var(--radius);
      cursor: pointer;
      color: var(--ink);
      font-size: 13px;
    }
    .status-button.active {
      background: var(--ink);
      border-color: var(--ink);
      color: var(--paper);
    }
    .checkline {
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      font-size: 14px;
    }
    textarea {
      width: 100%;
      min-height: 86px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: rgba(255,255,255,.42);
      padding: 10px 12px;
      color: var(--ink);
      line-height: 1.6;
    }
    .save-row {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: center;
    }
    .toast { color: var(--muted); font-size: 13px; min-height: 18px; }
    .empty {
      grid-column: 1 / -1;
      min-height: 260px;
      border: 1px dashed var(--line);
      display: grid;
      place-items: center;
      color: var(--muted);
      border-radius: var(--radius);
      background: rgba(255,255,255,.3);
    }
    .article-search {
      margin-top: 18px;
      padding-top: 16px;
      border-top: 1px solid var(--line);
    }
    .article-results {
      max-height: 230px;
      overflow: auto;
      display: grid;
      gap: 8px;
      margin-top: 10px;
      padding-right: 4px;
    }
    @media (max-width: 1080px) {
      .layout { grid-template-columns: 1fr; }
      .panel { position: static; }
      .toolbar { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .toolbar .search { grid-column: 1 / -1; }
    }
    @media (max-width: 760px) {
      .masthead { grid-template-columns: 1fr; }
      .deck { border-left: 0; padding-left: 0; }
      .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .ideas { grid-template-columns: 1fr; }
      .toolbar { grid-template-columns: 1fr; }
      .status-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    }
  </style>
</head>
<body>
  <main class="page">
    <header class="masthead">
      <div>
        <div class="issue"><span>People Daily Material</span><span id="issueDate">Idea Desk</span></div>
        <h1>选题工作台</h1>
      </div>
      <p class="deck">从人民日报素材库中抽取公众号选题，按月份、季度、状态和平台统一筛选。</p>
    </header>

    <section class="stats" aria-label="选题统计">
      <div class="stat"><strong id="statTotal">0</strong><span>全部选题</span></div>
      <div class="stat"><strong id="statSelected">0</strong><span>精筛保留</span></div>
      <div class="stat"><strong id="statPriority">0</strong><span>优先推进</span></div>
      <div class="stat"><strong id="statDone">0</strong><span>已完成</span></div>
    </section>

    <section class="toolbar" aria-label="筛选">
      <input class="field search" id="searchInput" placeholder="搜索选题、角度、文章、大纲" autocomplete="off">
      <select class="field" id="statusFilter"><option value="">全部状态</option></select>
      <select class="field" id="monthFilter"><option value="">全部月份</option></select>
      <select class="field" id="quarterFilter"><option value="">全部季度</option></select>
      <select class="field" id="platformFilter"><option value="">全部平台</option></select>
      <button class="action" id="exportButton">刷新总表</button>
    </section>

    <section class="layout">
      <div class="ideas" id="ideas"></div>
      <aside class="panel" id="detail"></aside>
    </section>
  </main>

  <script>
    const state = {
      ideas: [],
      filters: { statuses: [], months: [], quarters: [], platforms: [] },
      activeId: null,
      pendingStatus: null,
      pendingSelected: false,
      pendingNote: ""
    };

    const $ = (id) => document.getElementById(id);
    const today = new Date();
    $("issueDate").textContent = `${today.getFullYear()}.${String(today.getMonth()+1).padStart(2, "0")}.${String(today.getDate()).padStart(2, "0")}`;

    function tagClass(status) {
      if (status === "优先") return "priority";
      if (status === "已完成") return "done";
      return "";
    }

    function escapeHtml(text) {
      return String(text || "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
      })[char]);
    }

    function fillSelect(id, values) {
      const node = $(id);
      const first = node.firstElementChild;
      node.innerHTML = "";
      node.appendChild(first);
      values.forEach((value) => {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        node.appendChild(option);
      });
    }

    async function load() {
      const response = await fetch("/api/ideas");
      const payload = await response.json();
      state.ideas = payload.ideas || [];
      state.filters = payload.filters || state.filters;
      state.activeId = state.activeId || (state.ideas[0] && state.ideas[0].idea_id);
      fillSelect("statusFilter", state.filters.statuses || []);
      fillSelect("monthFilter", state.filters.months || []);
      fillSelect("quarterFilter", state.filters.quarters || []);
      fillSelect("platformFilter", state.filters.platforms || []);
      updateStats(payload.stats || {});
      render();
    }

    function updateStats(stats) {
      $("statTotal").textContent = stats.total || 0;
      $("statSelected").textContent = stats.selected || 0;
      $("statPriority").textContent = (stats.status_counts || {})["优先"] || 0;
      $("statDone").textContent = (stats.status_counts || {})["已完成"] || 0;
    }

    function filteredIdeas() {
      const q = $("searchInput").value.trim().toLowerCase();
      const status = $("statusFilter").value;
      const month = $("monthFilter").value;
      const quarter = $("quarterFilter").value;
      const platform = $("platformFilter").value;
      return state.ideas.filter((idea) => {
        if (q && !idea.searchable.includes(q)) return false;
        if (status && idea.status !== status) return false;
        if (month && idea.month !== month) return false;
        if (quarter && idea.quarter !== quarter) return false;
        if (platform && !idea.platform.includes(platform)) return false;
        return true;
      });
    }

    function render() {
      const list = filteredIdeas();
      const container = $("ideas");
      if (!list.length) {
        container.innerHTML = '<div class="empty">没有匹配的选题</div>';
        renderDetail(null);
        return;
      }
      if (!list.some((idea) => idea.idea_id === state.activeId)) {
        state.activeId = list[0].idea_id;
      }
      container.innerHTML = list.map((idea) => {
        const articles = idea.support_articles.slice(0, 2).map((article) => article.title).join("；");
        return `
          <article class="card ${idea.idea_id === state.activeId ? "active" : ""}" data-id="${escapeHtml(idea.idea_id)}">
            <div class="meta">
              <span>${escapeHtml(idea.date)}</span>
              <span class="tag ${tagClass(idea.status)}">${escapeHtml(idea.status)}</span>
              ${idea.selected ? '<span class="tag selected">精筛</span>' : ""}
              <span class="tag">${escapeHtml(idea.platform || "未标平台")}</span>
            </div>
            <h2>${escapeHtml(idea.title)}</h2>
            <p class="angle">${escapeHtml(idea.angle)}</p>
            <div class="support">${escapeHtml(articles || "暂无支撑文章")}</div>
          </article>
        `;
      }).join("");
      container.querySelectorAll(".card").forEach((card) => {
        card.addEventListener("click", () => {
          state.activeId = card.dataset.id;
          render();
        });
      });
      renderDetail(state.ideas.find((idea) => idea.idea_id === state.activeId));
    }

    function renderDetail(idea) {
      const panel = $("detail");
      if (!idea) {
        panel.innerHTML = '<div class="panel-body">请选择一个选题</div>';
        return;
      }
      state.pendingStatus = idea.status;
      state.pendingSelected = idea.selected;
      state.pendingNote = idea.user_note || "";
      panel.innerHTML = `
        <div class="panel-head">
          <div class="panel-kicker">
            <span class="tag">${escapeHtml(idea.date)}</span>
            <span class="tag">${escapeHtml(idea.month)}</span>
            <span class="tag">${escapeHtml(idea.quarter)}</span>
            <span class="tag ${tagClass(idea.status)}">${escapeHtml(idea.status)}</span>
          </div>
          <h3>${escapeHtml(idea.title)}</h3>
        </div>
        <div class="panel-body">
          <div class="section-title">切入角度</div>
          <p class="angle">${escapeHtml(idea.angle)}</p>
          <div class="section-title">大纲</div>
          <ol class="outline">${idea.outline.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ol>
          <div class="section-title">支撑文章</div>
          <div class="article-list">
            ${idea.support_articles.map((article) => `
              <a class="article" href="${escapeHtml(article.url || "#")}" target="_blank" rel="noreferrer">
                ${escapeHtml(article.title)}
                <small>${escapeHtml(article.date || article.article_id)} ${escapeHtml(article.section_name || "")}</small>
              </a>
            `).join("") || '<div class="article">暂无支撑文章</div>'}
          </div>
          <div class="ops">
            <div class="status-grid">
              ${state.filters.statuses.map((status) => `
                <button class="status-button ${status === idea.status ? "active" : ""}" data-status="${escapeHtml(status)}">${escapeHtml(status)}</button>
              `).join("")}
            </div>
            <label class="checkline"><input type="checkbox" id="selectedInput" ${idea.selected ? "checked" : ""}> 加入精筛池</label>
            <textarea id="noteInput" placeholder="我的判断、适合的课程、后续处理">${escapeHtml(idea.user_note || "")}</textarea>
            <div class="save-row">
              <button class="action" id="saveButton">保存操作</button>
              <span class="toast" id="toast"></span>
            </div>
          </div>
          <div class="article-search">
            <div class="section-title">文章库搜索</div>
            <input class="field" id="articleSearch" placeholder="搜索原文标题、版面、摘要">
            <div class="article-results" id="articleResults"></div>
          </div>
        </div>
      `;
      panel.querySelectorAll(".status-button").forEach((button) => {
        button.addEventListener("click", () => {
          state.pendingStatus = button.dataset.status;
          panel.querySelectorAll(".status-button").forEach((item) => item.classList.remove("active"));
          button.classList.add("active");
        });
      });
      $("selectedInput").addEventListener("change", (event) => {
        state.pendingSelected = event.target.checked;
      });
      $("saveButton").addEventListener("click", saveActive);
      $("articleSearch").addEventListener("input", debounce(searchArticles, 260));
    }

    async function saveActive() {
      const idea = state.ideas.find((item) => item.idea_id === state.activeId);
      if (!idea) return;
      const response = await fetch(`/api/ideas/${encodeURIComponent(idea.idea_id)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          status: state.pendingStatus,
          selected: $("selectedInput").checked,
          user_note: $("noteInput").value
        })
      });
      const payload = await response.json();
      if (!response.ok || payload.error) {
        $("toast").textContent = payload.error || "保存失败";
        return;
      }
      $("toast").textContent = "已保存";
      state.activeId = idea.idea_id;
      await load();
    }

    async function searchArticles() {
      const q = $("articleSearch").value.trim();
      if (!q) {
        $("articleResults").innerHTML = "";
        return;
      }
      const response = await fetch(`/api/articles?q=${encodeURIComponent(q)}&limit=20`);
      const payload = await response.json();
      $("articleResults").innerHTML = (payload.articles || []).map((article) => `
        <a class="article" href="${escapeHtml(article.url || "#")}" target="_blank" rel="noreferrer">
          ${escapeHtml(article.title)}
          <small>${escapeHtml(article.date)} ${escapeHtml(article.section_name)} ${escapeHtml(article.summary).slice(0, 72)}</small>
        </a>
      `).join("") || '<div class="article">没有找到文章</div>';
    }

    function debounce(fn, wait) {
      let timer;
      return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), wait);
      };
    }

    ["searchInput", "statusFilter", "monthFilter", "quarterFilter", "platformFilter"].forEach((id) => {
      $(id).addEventListener("input", render);
      $(id).addEventListener("change", render);
    });
    $("exportButton").addEventListener("click", async () => {
      $("exportButton").textContent = "刷新中";
      await fetch("/api/export", { method: "POST" });
      $("exportButton").textContent = "已刷新";
      setTimeout(() => $("exportButton").textContent = "刷新总表", 1200);
    });

    load();
  </script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="启动人民日报选题工作台")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址")
    parser.add_argument("--port", type=int, default=8765, help="监听端口")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), IdeaMagazineHandler)
    print(f"选题工作台已启动: http://{args.host}:{args.port}")
    print("按 Ctrl+C 停止。")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

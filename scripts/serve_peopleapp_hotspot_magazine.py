#!/usr/bin/env python3
"""Serve a local browser workbench for APP opinion hotspot topics."""

from __future__ import annotations

import argparse
import json
import socket
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
TOPIC_DB = ROOT / "data" / "peopleapp_opinion" / "core" / "hotspot_topics.sqlite"
STATUS_OPTIONS = ["热点", "候选"]
PRIORITY_OPTIONS = ["S", "A", "B", "C"]


def connect(path: Path | None = None) -> sqlite3.Connection:
    path = path or TOPIC_DB
    conn = sqlite3.connect(str(path), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=10000")
    return conn


def json_list(text: str | None) -> list[str]:
    if not text:
        return []
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return []
    return [str(item) for item in value] if isinstance(value, list) else []


def topic_payload() -> dict[str, Any]:
    if not TOPIC_DB.exists():
        raise FileNotFoundError(
            "未找到 APP 评论热点总库，请先运行 "
            "python3 scripts/update_peopleapp_opinion_topic_library.py --all"
        )

    conn = connect()
    try:
        topic_rows = list(
            conn.execute(
                """
                SELECT *
                FROM hotspot_topics
                ORDER BY
                  CASE status WHEN '热点' THEN 1 ELSE 2 END,
                  CASE priority WHEN 'S' THEN 1 WHEN 'A' THEN 2 WHEN 'B' THEN 3 ELSE 4 END,
                  media_count DESC, article_count DESC, end_date DESC, topic
                """
            )
        )
        article_rows = list(
            conn.execute(
                """
                SELECT *
                FROM hotspot_topic_articles
                ORDER BY date DESC, source_name, title
                """
            )
        )
    finally:
        conn.close()

    articles_by_topic: dict[str, list[dict[str, str]]] = {}
    for row in article_rows:
        articles_by_topic.setdefault(row["topic_id"], []).append(
            {
                "article_id": row["article_id"] or "",
                "date": row["date"] or "",
                "source_name": row["source_name"] or "",
                "title": row["title"] or "",
                "url": row["url"] or "",
            }
        )

    topics: list[dict[str, Any]] = []
    sources: set[str] = set()
    for row in topic_rows:
        topic_sources = json_list(row["sources_json"])
        sources.update(topic_sources)
        articles = articles_by_topic.get(row["topic_id"], [])
        searchable = " ".join(
            [
                row["topic"] or "",
                row["status"] or "",
                row["priority"] or "",
                row["manual_note"] or "",
                row["ai_brief"] or "",
                " ".join(topic_sources),
                " ".join(article["title"] for article in articles),
            ]
        ).lower()
        topics.append(
            {
                "topic_id": row["topic_id"],
                "topic": row["topic"],
                "status": row["status"],
                "priority": row["priority"],
                "media_count": row["media_count"],
                "article_count": row["article_count"],
                "start_date": row["start_date"] or "",
                "end_date": row["end_date"] or "",
                "sources": topic_sources,
                "ai_brief": row["ai_brief"] or "",
                "manual_note": row["manual_note"] or "",
                "selected": bool(row["selected"]),
                "articles": articles,
                "searchable": searchable,
            }
        )

    status_counts = Counter(topic["status"] for topic in topics)
    priority_counts = Counter(topic["priority"] for topic in topics)
    return {
        "topics": topics,
        "stats": {
            "total": len(topics),
            "selected": sum(1 for topic in topics if topic["selected"]),
            "hotspots": status_counts["热点"],
            "candidates": status_counts["候选"],
            "priority_counts": dict(priority_counts),
        },
        "filters": {
            "statuses": STATUS_OPTIONS,
            "priorities": PRIORITY_OPTIONS,
            "sources": sorted(sources),
        },
    }


def update_topic(topic_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    allowed = {"selected", "manual_note"}
    if not any(key in payload for key in allowed):
        raise ValueError("没有需要保存的人工判断")

    conn = connect()
    try:
        current = conn.execute(
            "SELECT selected, manual_note FROM hotspot_topics WHERE topic_id = ?",
            (topic_id,),
        ).fetchone()
        if current is None:
            raise KeyError(f"未找到热点选题: {topic_id}")
        selected = int(bool(payload["selected"])) if "selected" in payload else int(current["selected"])
        manual_note = (
            str(payload["manual_note"]).strip()
            if "manual_note" in payload
            else (current["manual_note"] or "")
        )
        conn.execute(
            """
            UPDATE hotspot_topics
            SET selected = ?, manual_note = ?, updated_at = ?
            WHERE topic_id = ?
            """,
            (selected, manual_note, datetime.now().isoformat(timespec="seconds"), topic_id),
        )
        conn.commit()
    finally:
        conn.close()
    return {"success": True, "topic_id": topic_id}


def batch_update(payload: dict[str, Any]) -> dict[str, Any]:
    topic_ids = payload.get("topic_ids")
    if not isinstance(topic_ids, list) or not topic_ids:
        raise ValueError("请选择至少一个热点选题")
    if "selected" not in payload:
        raise ValueError("请选择加入或移出精筛池")

    selected = int(bool(payload["selected"]))
    now = datetime.now().isoformat(timespec="seconds")
    conn = connect()
    try:
        updated = 0
        for topic_id in topic_ids:
            cursor = conn.execute(
                "UPDATE hotspot_topics SET selected = ?, updated_at = ? WHERE topic_id = ?",
                (selected, now, str(topic_id)),
            )
            updated += cursor.rowcount
        conn.commit()
    finally:
        conn.close()
    return {"success": True, "updated": updated}


def json_response(handler: BaseHTTPRequestHandler, data: dict[str, Any], status: int = 200) -> None:
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def html_response(handler: BaseHTTPRequestHandler) -> None:
    body = HTML.encode("utf-8")
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class HotspotMagazineHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_GET(self) -> None:
        try:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                html_response(self)
                return
            if parsed.path == "/api/topics":
                json_response(self, topic_payload())
                return
            json_response(self, {"error": "Not found"}, HTTPStatus.NOT_FOUND)
        except Exception as exc:
            json_response(self, {"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self) -> None:
        try:
            parsed = urlparse(self.path)
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            if parsed.path.startswith("/api/topics/"):
                topic_id = unquote(parsed.path.removeprefix("/api/topics/"))
                json_response(self, update_topic(topic_id, payload))
                return
            if parsed.path == "/api/batch":
                json_response(self, batch_update(payload))
                return
            json_response(self, {"error": "Not found"}, HTTPStatus.NOT_FOUND)
        except Exception as exc:
            json_response(self, {"error": str(exc)}, HTTPStatus.BAD_REQUEST)


HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>APP 评论热点选题工作台</title>
  <style>
    :root {
      --paper:#f4efe6; --ink:#17130f; --muted:#786f63; --line:#c8bca8;
      --accent:#9d1f22; --accent-soft:#ead0c9; --green:#2f6f58;
      --shadow:0 18px 44px rgba(48,35,21,.12); --radius:6px;
    }
    *{box-sizing:border-box}
    body{margin:0;color:var(--ink);background:linear-gradient(90deg,rgba(80,57,31,.04) 1px,transparent 1px),var(--paper);background-size:24px 24px;font-family:"Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif}
    button,input,select,textarea{font:inherit} a{color:inherit}
    .page{min-height:100vh;padding:28px clamp(16px,3vw,40px) 48px}
    .masthead{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:24px;align-items:end;border-bottom:2px solid var(--ink);padding-bottom:18px}
    .issue{display:flex;gap:14px;color:var(--muted);font-size:13px}.issue span{border-top:1px solid var(--line);padding-top:6px}
    h1{margin:8px 0 0;font-family:"Noto Serif SC","Songti SC",serif;font-size:clamp(38px,7vw,82px);line-height:.96}
    .deck{max-width:450px;color:var(--muted);line-height:1.7;font-size:14px;border-left:1px solid var(--line);padding-left:18px}
    .stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border-bottom:1px solid var(--ink);margin:18px 0 22px}
    .stat{min-height:86px;border-right:1px solid var(--line);padding:12px 18px 14px 0}.stat:last-child{border:0}
    .stat strong{display:block;font-family:"Noto Serif SC","Songti SC",serif;font-size:34px;line-height:1;margin-bottom:8px}.stat span{color:var(--muted);font-size:13px}
    .toolbar{display:grid;grid-template-columns:minmax(260px,1.5fr) repeat(4,minmax(118px,.55fr)) auto;gap:10px;margin-bottom:22px}
    .field,.action{min-height:42px;border:1px solid var(--line);border-radius:var(--radius);background:rgba(255,255,255,.4);color:var(--ink)}
    .field{width:100%;padding:0 12px}.action{padding:0 14px;cursor:pointer}.action:hover{border-color:var(--ink)}
    .layout{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(350px,.75fr);gap:24px;align-items:start}
    .topics{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
    .card{position:relative;min-height:250px;border:1px solid var(--line);border-radius:var(--radius);background:rgba(255,255,255,.46);padding:18px;cursor:pointer;box-shadow:0 8px 22px rgba(48,35,21,.05);transition:.16s}
    .card:hover,.card.active{transform:translateY(-2px);border-color:var(--ink);box-shadow:var(--shadow)}
    .card.active:before{content:"";position:absolute;inset:0 auto 0 0;width:5px;background:var(--accent)}
    .meta,.panel-kicker{display:flex;flex-wrap:wrap;gap:8px;align-items:center;color:var(--muted);font-size:12px;margin-bottom:14px}
    .tag{display:inline-flex;align-items:center;min-height:24px;border:1px solid var(--line);padding:2px 8px;border-radius:999px;background:rgba(255,255,255,.38)}
    .tag.hot{color:var(--accent);border-color:var(--accent-soft);background:rgba(157,31,34,.06)}.tag.selected{color:var(--green);border-color:rgba(47,111,88,.35)}
    .card h2{margin:0 0 14px;font-family:"Noto Serif SC","Songti SC",serif;font-size:clamp(23px,2.3vw,32px);line-height:1.2}
    .metrics{display:grid;grid-template-columns:repeat(2,1fr);border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:10px 0;margin-bottom:12px}
    .metrics span{color:var(--muted);font-size:13px}.metrics strong{color:var(--ink);font-size:20px;margin-right:4px}
    .support{color:var(--muted);font-size:13px;line-height:1.65}
    .panel{position:sticky;top:18px;border:1px solid var(--ink);border-radius:var(--radius);background:rgba(250,247,240,.94);box-shadow:var(--shadow);overflow:hidden}
    .panel-head{padding:18px;border-bottom:1px solid var(--line);background:rgba(157,31,34,.06)}.panel h3{margin:0;font:800 31px/1.18 "Noto Serif SC","Songti SC",serif}
    .panel-body{padding:18px}.section-title{margin:18px 0 8px;color:var(--accent);font-size:13px;font-weight:700}
    .source-line{color:var(--muted);line-height:1.65;font-size:14px}.article-list{display:grid;gap:8px}
    .article{display:block;text-decoration:none;border:1px solid var(--line);border-radius:var(--radius);padding:10px 12px;background:rgba(255,255,255,.4)}
    .article:hover{border-color:var(--ink)}.article small{display:block;color:var(--muted);margin-top:4px}
    .ops{display:grid;gap:12px;margin-top:16px;padding-top:16px;border-top:1px solid var(--line)}
    .checkline{display:flex;gap:8px;align-items:center;color:var(--muted);font-size:14px}
    textarea{width:100%;min-height:100px;resize:vertical;border:1px solid var(--line);border-radius:var(--radius);background:rgba(255,255,255,.42);padding:10px 12px;line-height:1.6}
    .save-row{display:flex;justify-content:space-between;gap:10px;align-items:center}.toast{color:var(--green);font-size:13px;min-height:18px}
    .batch-bar{position:sticky;bottom:0;z-index:100;display:none;align-items:center;gap:10px;padding:12px 16px;background:rgba(23,19,15,.94);color:#eee;border-radius:var(--radius);margin-top:16px}
    .batch-bar.visible{display:flex}.batch-bar button{min-height:36px;border:1px solid rgba(255,255,255,.25);border-radius:var(--radius);background:rgba(255,255,255,.1);color:#fff;padding:0 12px;cursor:pointer}
    .batch-check{position:absolute;top:12px;right:12px;width:22px;height:22px;border:2px solid var(--line);border-radius:4px;background:#fff;display:none}
    body.batch-mode .batch-check{display:grid}.card.batch-selected{border-color:var(--accent)}.card.batch-selected .batch-check{background:var(--accent);border-color:var(--accent)}.card.batch-selected .batch-check:after{content:"✓";color:#fff;text-align:center;font-weight:700}
    .empty{grid-column:1/-1;min-height:240px;border:1px dashed var(--line);display:grid;place-items:center;color:var(--muted)}
    @media(max-width:1050px){.layout{grid-template-columns:1fr}.panel{position:static}.toolbar{grid-template-columns:repeat(2,1fr)}.search{grid-column:1/-1}}
    @media(max-width:720px){.masthead{grid-template-columns:1fr}.deck{border:0;padding:0}.stats{grid-template-columns:repeat(2,1fr)}.topics,.toolbar{grid-template-columns:1fr}.search{grid-column:auto}}
  </style>
</head>
<body>
<main class="page">
  <header class="masthead">
    <div><div class="issue"><span>People Daily APP</span><span id="issueDate">Hotspot Desk</span></div><h1>热点选题工作台</h1></div>
    <p class="deck">集中查看多家官媒共同关注的话题，筛出适合申论、面试和公众号继续加工的热点选题。</p>
  </header>
  <section class="stats">
    <div class="stat"><strong id="statTotal">0</strong><span>全部话题</span></div>
    <div class="stat"><strong id="statHotspot">0</strong><span>达标热点</span></div>
    <div class="stat"><strong id="statSelected">0</strong><span>人工精筛</span></div>
    <div class="stat"><strong id="statCandidate">0</strong><span>候选话题</span></div>
  </section>
  <section class="toolbar">
    <input class="field search" id="searchInput" placeholder="搜索热点、来源、文章或备注">
    <select class="field" id="statusFilter"><option value="">全部状态</option></select>
    <select class="field" id="priorityFilter"><option value="">全部优先级</option></select>
    <select class="field" id="sourceFilter"><option value="">全部来源</option></select>
    <select class="field" id="selectedFilter"><option value="">全部精筛状态</option><option value="yes">已精筛</option><option value="no">未精筛</option></select>
    <button class="action" id="batchToggle">批量选择</button>
  </section>
  <section class="layout">
    <div class="topics" id="topics"></div>
    <aside class="panel" id="detail"></aside>
  </section>
  <div class="batch-bar" id="batchBar">
    <span>已选 <strong id="batchCount">0</strong> 项</span>
    <button id="batchAll">全选当前</button>
    <button id="batchKeep">加入精筛池</button>
    <button id="batchRemove">移出精筛池</button>
    <button id="batchCancel">退出批量</button>
    <span id="batchToast"></span>
  </div>
</main>
<script>
const state={topics:[],filters:{statuses:[],priorities:[],sources:[]},activeId:null,batchMode:false,batchIds:new Set(),firstLoad:true};
const $=id=>document.getElementById(id);
const today=new Date();$("issueDate").textContent=`${today.getFullYear()}.${String(today.getMonth()+1).padStart(2,"0")}.${String(today.getDate()).padStart(2,"0")}`;
function escapeHtml(text){return String(text||"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]))}
function fillSelect(id,values){const n=$(id),old=n.value,first=n.firstElementChild;n.innerHTML="";n.appendChild(first);values.forEach(v=>{const o=document.createElement("option");o.value=v;o.textContent=v;n.appendChild(o)});if([...n.options].some(o=>o.value===old))n.value=old}
async function load(){const r=await fetch("/api/topics"),p=await r.json();if(!r.ok||p.error){$("topics").innerHTML=`<div class="empty">${escapeHtml(p.error||"读取失败")}</div>`;return}state.topics=p.topics||[];state.filters=p.filters||state.filters;state.activeId=state.activeId||(state.topics[0]&&state.topics[0].topic_id);fillSelect("statusFilter",state.filters.statuses||[]);fillSelect("priorityFilter",state.filters.priorities||[]);fillSelect("sourceFilter",state.filters.sources||[]);if(state.firstLoad){$("statusFilter").value="热点";state.firstLoad=false}$("statTotal").textContent=p.stats.total||0;$("statHotspot").textContent=p.stats.hotspots||0;$("statSelected").textContent=p.stats.selected||0;$("statCandidate").textContent=p.stats.candidates||0;render()}
function filtered(){const q=$("searchInput").value.trim().toLowerCase(),status=$("statusFilter").value,priority=$("priorityFilter").value,source=$("sourceFilter").value,selected=$("selectedFilter").value;return state.topics.filter(t=>(!q||t.searchable.includes(q))&&(!status||t.status===status)&&(!priority||t.priority===priority)&&(!source||t.sources.includes(source))&&(!selected||(selected==="yes")===t.selected))}
function render(){const list=filtered(),box=$("topics");if(!list.length){box.innerHTML='<div class="empty">没有匹配的热点选题</div>';renderDetail(null);return}if(!list.some(t=>t.topic_id===state.activeId))state.activeId=list[0].topic_id;box.innerHTML=list.map(t=>{const titles=t.articles.slice(0,2).map(a=>a.title).join("；");return `<article class="card ${t.topic_id===state.activeId?"active":""} ${state.batchIds.has(t.topic_id)?"batch-selected":""}" data-id="${escapeHtml(t.topic_id)}"><div class="batch-check"></div><div class="meta"><span class="tag ${t.status==="热点"?"hot":""}">${escapeHtml(t.status)}</span><span class="tag">${escapeHtml(t.priority)}级</span>${t.selected?'<span class="tag selected">已精筛</span>':""}<span>${escapeHtml(t.end_date)}</span></div><h2>${escapeHtml(t.topic)}</h2><div class="metrics"><span><strong>${t.media_count}</strong>家媒体</span><span><strong>${t.article_count}</strong>篇评论</span></div><div class="support">${escapeHtml(titles||"暂无支撑文章")}</div></article>`}).join("");box.querySelectorAll(".card").forEach(card=>card.addEventListener("click",()=>{if(state.batchMode){toggleBatch(card.dataset.id);return}state.activeId=card.dataset.id;render()}));updateBatch();renderDetail(state.topics.find(t=>t.topic_id===state.activeId))}
function renderDetail(t){const panel=$("detail");if(!t){panel.innerHTML='<div class="panel-body">请选择一个热点选题</div>';return}panel.innerHTML=`<div class="panel-head"><div class="panel-kicker"><span class="tag ${t.status==="热点"?"hot":""}">${escapeHtml(t.status)}</span><span class="tag">${escapeHtml(t.priority)}级</span><span class="tag">${escapeHtml(t.start_date)} 至 ${escapeHtml(t.end_date)}</span></div><h3>${escapeHtml(t.topic)}</h3></div><div class="panel-body"><div class="section-title">关注规模</div><div class="source-line">${t.media_count} 家媒体、${t.article_count} 篇评论集中讨论</div><div class="section-title">媒体来源</div><div class="source-line">${escapeHtml(t.sources.join("、"))}</div><div class="section-title">支撑文章</div><div class="article-list">${t.articles.map(a=>`<a class="article" href="${escapeHtml(a.url||"#")}" target="_blank" rel="noreferrer">${escapeHtml(a.title)}<small>${escapeHtml(a.date)}｜${escapeHtml(a.source_name)}</small></a>`).join("")||'<div class="article">暂无文章</div>'}</div><div class="ops"><button class="action" id="copyButton">复制 AI 分析材料</button><label class="checkline"><input type="checkbox" id="selectedInput" ${t.selected?"checked":""}> 加入热点精筛池</label><textarea id="noteInput" placeholder="记录教学价值、传播角度或后续处理">${escapeHtml(t.manual_note)}</textarea><div class="save-row"><button class="action" id="saveButton">保存判断</button><span class="toast" id="toast"></span></div></div></div>`;$("saveButton").addEventListener("click",saveActive);$("copyButton").addEventListener("click",()=>copyText(t.ai_brief))}
async function saveActive(){const t=state.topics.find(x=>x.topic_id===state.activeId);if(!t)return;const r=await fetch(`/api/topics/${encodeURIComponent(t.topic_id)}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({selected:$("selectedInput").checked,manual_note:$("noteInput").value})}),p=await r.json();if(!r.ok||p.error){$("toast").textContent=p.error||"保存失败";return}await load();if($("toast"))$("toast").textContent="已保存"}
async function copyText(text){if(navigator.clipboard&&window.isSecureContext)await navigator.clipboard.writeText(text);else{const n=document.createElement("textarea");n.value=text;document.body.appendChild(n);n.select();document.execCommand("copy");n.remove()}$("toast").textContent="已复制"}
function toggleBatch(id){state.batchIds.has(id)?state.batchIds.delete(id):state.batchIds.add(id);render()}
function updateBatch(){$("batchCount").textContent=state.batchIds.size;$("batchBar").classList.toggle("visible",state.batchMode&&state.batchIds.size>0)}
function toggleBatchMode(){state.batchMode=!state.batchMode;if(!state.batchMode)state.batchIds.clear();document.body.classList.toggle("batch-mode",state.batchMode);$("batchToggle").textContent=state.batchMode?"退出批量":"批量选择";render()}
async function applyBatch(selected){if(!state.batchIds.size)return;const r=await fetch("/api/batch",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({topic_ids:[...state.batchIds],selected})}),p=await r.json();$("batchToast").textContent=p.error||`已更新 ${p.updated} 项`;if(!p.error){state.batchIds.clear();await load()}}
["searchInput","statusFilter","priorityFilter","sourceFilter","selectedFilter"].forEach(id=>{$(id).addEventListener("input",render);$(id).addEventListener("change",render)});
$("batchToggle").addEventListener("click",toggleBatchMode);$("batchCancel").addEventListener("click",toggleBatchMode);$("batchKeep").addEventListener("click",()=>applyBatch(true));$("batchRemove").addEventListener("click",()=>applyBatch(false));$("batchAll").addEventListener("click",()=>{const list=filtered(),all=list.every(t=>state.batchIds.has(t.topic_id));list.forEach(t=>all?state.batchIds.delete(t.topic_id):state.batchIds.add(t.topic_id));render()});
load();
</script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="启动 APP 评论热点选题工作台")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址")
    parser.add_argument("--port", type=int, default=8766, help="监听端口")
    args = parser.parse_args()

    port = args.port
    server = None
    for _ in range(20):
        try:
            server = ThreadingHTTPServer((args.host, port), HotspotMagazineHandler)
            server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            break
        except OSError as exc:
            if exc.errno == 48 or "Address already in use" in str(exc):
                port += 1
                continue
            raise
    if server is None:
        print(f"无法找到可用端口（从 {args.port} 开始已尝试 20 个端口）。")
        sys.exit(1)

    print(f"热点选题工作台已启动: http://{args.host}:{port}")
    print("按 Ctrl+C 停止。")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

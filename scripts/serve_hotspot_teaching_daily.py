#!/usr/bin/env python3
"""Serve the read-only hotspot teaching daily and portable JSON API."""

from __future__ import annotations

import argparse
import importlib.util
import json
import socket
import sys
import webbrowser
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = ROOT / "data" / "hotspot_teaching" / "site"
DATA_FILE = SITE_ROOT / "data.json"
BUILD_SCRIPT = ROOT / "scripts" / "build_hotspot_teaching_daily.py"


def build_data() -> None:
    spec = importlib.util.spec_from_file_location("build_hotspot_teaching_daily_runtime", BUILD_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载数据生成脚本：{BUILD_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    topics = module.load_topics()
    counts = module.refresh_database(topics, module.load_paper_articles())
    module.export_bundle(counts)


def load_payload() -> dict:
    if not DATA_FILE.exists():
        build_data()
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def topic_by_id(payload: dict, topic_id: str) -> dict | None:
    return next((item for item in payload.get("topics", []) if item.get("topic_id") == topic_id), None)


def edition_payload(payload: dict, table: str, key: str, value: str) -> dict | None:
    edition = next((item for item in payload.get(table, []) if item.get(key) == value), None)
    if not edition:
        return None
    topics = [topic_by_id(payload, topic_id) for topic_id in edition.get("topic_ids", [])]
    return {**edition, "topics": [item for item in topics if item]}


class TeachingDailyHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory: str | None = None, **kwargs):
        super().__init__(*args, directory=directory or str(SITE_ROOT), **kwargs)

    def log_message(self, format: str, *args) -> None:
        return

    def json_response(self, data: object, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/"):
            if parsed.path == "/":
                self.path = "/index.html"
            return super().do_GET()

        try:
            payload = load_payload()
            if parsed.path == "/api/bootstrap":
                self.json_response(payload)
                return
            if parsed.path == "/api/hotspots":
                self.json_response({"topics": payload.get("topics", []), "stats": payload.get("stats", {})})
                return
            if parsed.path.startswith("/api/hotspots/"):
                topic_id = unquote(parsed.path.removeprefix("/api/hotspots/"))
                topic = topic_by_id(payload, topic_id)
                self.json_response(topic or {"error": "未找到热点"}, HTTPStatus.OK if topic else HTTPStatus.NOT_FOUND)
                return
            if parsed.path.startswith("/api/daily/"):
                issue_date = unquote(parsed.path.removeprefix("/api/daily/"))
                edition = edition_payload(payload, "daily_editions", "edition_date", issue_date)
                self.json_response(edition or {"error": "未找到日报"}, HTTPStatus.OK if edition else HTTPStatus.NOT_FOUND)
                return
            if parsed.path.startswith("/api/weekly/"):
                week_start = unquote(parsed.path.removeprefix("/api/weekly/"))
                edition = edition_payload(payload, "weekly_editions", "week_start", week_start)
                self.json_response(edition or {"error": "未找到周报"}, HTTPStatus.OK if edition else HTTPStatus.NOT_FOUND)
                return
            self.json_response({"error": "Not found"}, HTTPStatus.NOT_FOUND)
        except Exception as exc:
            self.json_response({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)


def choose_port(host: str, preferred: int) -> int:
    for port in range(preferred, preferred + 20):
        with socket.socket() as sock:
            try:
                sock.bind((host, port))
            except OSError:
                continue
            return port
    raise RuntimeError("没有找到可用端口")


def main() -> None:
    parser = argparse.ArgumentParser(description="打开热点教学日报")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8767)
    parser.add_argument("--rebuild", action="store_true", help="启动前刷新双库融合数据")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    args = parser.parse_args()

    if args.rebuild or not DATA_FILE.exists():
        build_data()
    port = choose_port(args.host, args.port)
    url = f"http://{args.host}:{port}"
    server = ThreadingHTTPServer(
        (args.host, port), partial(TeachingDailyHandler, directory=str(SITE_ROOT))
    )
    print(f"热点教学日报已启动：{url}")
    print("按 Control+C 停止。")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

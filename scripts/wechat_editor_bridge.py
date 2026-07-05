#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""承接 doocs/md 的“发布”按钮：保存排版、预览并进入草稿同步步骤。"""

from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from modules.writing_workflow import (
    article_state,
    atomic_write_text,
    body_hash,
    join_frontmatter,
    load_public_config,
    load_state,
    project_path,
    save_snapshot,
    save_state,
    split_frontmatter,
    structural_issues,
    workflow_id,
)
from publish_wechat_draft import publish
from render_wechat_html import render_article, save_layout


class EditorWorkflow:
    def __init__(self, article: str, port: int) -> None:
        self.config = load_public_config()
        self.article_path = project_path(article).resolve()
        if not self.article_path.exists():
            raise RuntimeError(f"文章不存在：{self.article_path}")
        self.workflow_id = workflow_id(self.article_path)
        self.port = port
        self.last_result: dict[str, object] = {}
        self.restore_last_result()

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def restore_last_result(self) -> None:
        state = load_state(self.config)
        entry = article_state(state, self.article_path)
        if not entry or not entry.get("layout_saved_at"):
            return
        rendered = render_article(str(self.article_path))
        self.last_result = {
            "saved": True,
            "content_changed": bool(entry.get("editor_content_changed")),
            "content_synced": bool(entry.get("editor_content_synced")),
            "sync_blocked": bool(entry.get("editor_sync_blocked")),
            "sync_issues": list(entry.get("editor_sync_issues") or []),
            "candidate_path": str(entry.get("editor_candidate") or ""),
            "layout": dict(entry.get("wechat_layout") or {}),
            "preview_path": rendered["preview_path"],
            "saved_at": entry["layout_saved_at"],
            "media_id": entry.get("wechat_draft_media_id"),
        }

    def save_handoff(self, payload: dict[str, object]) -> dict[str, object]:
        if str(payload.get("workflow_id") or "") != self.workflow_id:
            raise RuntimeError("文章工作流标识不匹配，已停止保存")

        source = self.article_path.read_text(encoding="utf-8")
        frontmatter, body, metadata = split_frontmatter(source)
        editor_markdown = str(payload.get("markdown") or "").strip()
        if not editor_markdown:
            raise RuntimeError("编辑器正文为空，已停止保存")

        layout_payload = payload.get("layout")
        if not isinstance(layout_payload, dict):
            raise RuntimeError("编辑器没有返回排版参数")

        allowed = set(self.config["doocs"]["default_layout"])
        layout_updates = {
            key: value
            for key, value in layout_payload.items()
            if key in allowed
        }
        layout = save_layout(str(self.article_path), layout_updates)

        content_changed = editor_markdown.strip() != body.strip()
        content_synced = False
        sync_blocked = False
        sync_issues: list[str] = []
        candidate_path: Path | None = None
        before_sync_path: Path | None = None
        if content_changed:
            candidate_path = save_snapshot(
                self.article_path,
                metadata,
                "04-editor-candidate.md",
                join_frontmatter(frontmatter, editor_markdown),
            )
            sync_issues = structural_issues(body, editor_markdown)
            if sync_issues:
                sync_blocked = True
            else:
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
                before_sync_path = save_snapshot(
                    self.article_path,
                    metadata,
                    f"04-before-editor-sync-{timestamp}.md",
                    source,
                )
                atomic_write_text(
                    self.article_path,
                    join_frontmatter(frontmatter, editor_markdown),
                )
                content_synced = True

        rendered = render_article(str(self.article_path))
        state = load_state(self.config)
        entry = article_state(state, self.article_path, create=True)
        assert entry is not None
        entry.update(
            {
                "status": (
                    "editor_sync_blocked" if sync_blocked else "layout_saved"
                ),
                "layout_saved_at": datetime.now().isoformat(timespec="seconds"),
                "editor_content_changed": content_changed,
                "editor_content_synced": content_synced,
                "editor_sync_blocked": sync_blocked,
                "editor_sync_issues": sync_issues,
                "editor_body_hash": body_hash(
                    editor_markdown if content_synced else body
                ),
                "editor_candidate": (
                    str(candidate_path.relative_to(PROJECT_ROOT))
                    if candidate_path
                    else None
                ),
                "before_editor_sync_snapshot": (
                    str(before_sync_path.relative_to(PROJECT_ROOT))
                    if before_sync_path
                    else None
                ),
            }
        )
        save_state(state, self.config)

        self.last_result = {
            "saved": True,
            "content_changed": content_changed,
            "content_synced": content_synced,
            "sync_blocked": sync_blocked,
            "sync_issues": sync_issues,
            "candidate_path": str(candidate_path) if candidate_path else "",
            "layout": layout,
            "preview_path": rendered["preview_path"],
            "saved_at": entry["layout_saved_at"],
        }
        return {
            **self.last_result,
            "next_url": "/pd-workflow/result",
        }

    def publish_draft(self) -> str:
        if self.last_result.get("sync_blocked"):
            raise RuntimeError(
                "编辑器正文未通过结构检查，已保存为候选稿；"
                "请先检查提示的问题，再同步草稿箱"
            )
        media_id = publish(str(self.article_path))
        if not media_id:
            raise RuntimeError("公众号接口没有返回草稿 media_id")
        self.last_result["media_id"] = media_id
        self.last_result["published_at"] = datetime.now().isoformat(timespec="seconds")
        state = load_state(self.config)
        entry = article_state(state, self.article_path, create=True)
        assert entry is not None
        entry.update(
            {
                "status": "wechat_draft_created",
                "wechat_draft_media_id": media_id,
                "wechat_draft_created_at": self.last_result["published_at"],
            }
        )
        save_state(state, self.config)
        return media_id

    def result_html(self, message: str = "", error: str = "") -> str:
        result = self.last_result
        layout = result.get("layout") if isinstance(result.get("layout"), dict) else {}
        content_synced = bool(result.get("content_synced"))
        sync_blocked = bool(result.get("sync_blocked"))
        sync_issues = result.get("sync_issues")
        if not isinstance(sync_issues, list):
            sync_issues = []
        if sync_blocked:
            status = "正文未通过结构检查，已保存候选稿，暂不允许同步。"
        elif content_synced:
            status = "正文已同步回源文件，排版设置已保存，最终预览已生成。"
        else:
            status = "正文无变化，排版设置已保存，最终预览已生成。"
        details = [
            ("主题", str(layout.get("theme", ""))),
            ("主题色", str(layout.get("primaryColor", ""))),
            ("字号", str(layout.get("fontSize", ""))),
            ("首行缩进", "开启" if layout.get("isUseIndent") else "关闭"),
            ("两端对齐", "开启" if layout.get("isUseJustify") else "关闭"),
            (
                "源文件",
                "暂停同步"
                if sync_blocked
                else ("已联动" if content_synced else "无需变更"),
            ),
        ]
        detail_html = "".join(
            f"<li><span>{html.escape(label)}</span><strong>{html.escape(value)}</strong></li>"
            for label, value in details
        )
        notice = ""
        if message:
            notice = f'<div class="notice success">{html.escape(message)}</div>'
        if error:
            notice = f'<div class="notice error">{html.escape(error)}</div>'
        if sync_issues:
            issue_items = "".join(
                f"<li>{html.escape(str(issue))}</li>" for issue in sync_issues
            )
            notice += f'<div class="notice error"><strong>需要检查：</strong><ul>{issue_items}</ul></div>'
        disabled = "disabled" if sync_blocked or result.get("media_id") else ""
        button_text = "草稿已创建" if result.get("media_id") else "同步到公众号草稿箱（只创建草稿）"
        editor_url = (
            "http://127.0.0.1:8800/md/"
            f"?pdWorkflow={self.workflow_id}"
        )
        return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>公众号工作流下一步</title>
<style>
body{{margin:0;background:#f4f5f7;color:#1f2937;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}}
.shell{{max-width:1080px;margin:0 auto;padding:28px}}
.card{{background:#fff;border-radius:16px;padding:24px;box-shadow:0 10px 35px #11182712}}
h1{{margin:0 0 8px;font-size:25px}}p{{line-height:1.75}}
ul{{list-style:none;padding:0;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}}
li{{padding:12px;background:#fff7f2;border-radius:10px}}li span,li strong{{display:block}}li span{{font-size:12px;color:#6b7280}}li strong{{margin-top:4px}}
.actions{{display:flex;gap:12px;margin:20px 0;flex-wrap:wrap}}
button,a.button{{border:0;border-radius:9px;padding:11px 16px;text-decoration:none;cursor:pointer;font-size:15px}}
button{{background:#ff6a2a;color:#fff}}button:disabled{{opacity:.45;cursor:not-allowed}}
a.button{{background:#111827;color:#fff}}
.notice{{padding:12px 14px;border-radius:9px;margin:14px 0}}.success{{background:#ecfdf5;color:#047857}}.error{{background:#fef2f2;color:#b91c1c}}
iframe{{width:100%;height:72vh;border:1px solid #e5e7eb;border-radius:12px;background:#fff}}
@media(max-width:760px){{.shell{{padding:12px}}ul{{grid-template-columns:1fr 1fr}}}}
</style>
</head>
<body>
<main class="shell">
  <section class="card">
    <h1>排版已进入下一步</h1>
    <p>{html.escape(status)}</p>
    {notice}
    <ul>{detail_html}</ul>
    <div class="actions">
      <a class="button" href="{html.escape(editor_url)}">返回排版编辑器</a>
      <form method="post" action="/pd-workflow/publish">
        <button type="submit" {disabled}>{html.escape(button_text)}</button>
      </form>
    </div>
    <iframe src="/pd-workflow/preview" title="最终公众号预览"></iframe>
  </section>
</main>
</body>
</html>"""


def make_handler(workflow: EditorWorkflow):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *_args: object) -> None:
            return

        def send_bytes(
            self,
            data: bytes,
            *,
            status: int = 200,
            content_type: str = "text/html; charset=utf-8",
        ) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:8800")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
            self.end_headers()
            self.wfile.write(data)

        def send_json(self, payload: dict[str, object], status: int = 200) -> None:
            self.send_bytes(
                json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                status=status,
                content_type="application/json; charset=utf-8",
            )

        def do_OPTIONS(self) -> None:
            self.send_bytes(b"", status=204)

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/status":
                self.send_json(
                    {
                        "ready": True,
                        "workflow_id": workflow.workflow_id,
                        "article": str(workflow.article_path),
                    }
                )
                return
            if path == "/article":
                source = workflow.article_path.read_text(encoding="utf-8")
                _, body, _ = split_frontmatter(source)
                self.send_json({"markdown": body})
                return
            if path == "/preview":
                preview_path = str(workflow.last_result.get("preview_path") or "")
                preview = Path(preview_path)
                if not preview.exists():
                    self.send_bytes("预览尚未生成".encode("utf-8"), status=404)
                    return
                self.send_bytes(preview.read_bytes())
                return
            if path in {"/", "/result"}:
                self.send_bytes(workflow.result_html().encode("utf-8"))
                return
            self.send_bytes("页面不存在".encode("utf-8"), status=404)

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            if path == "/handoff":
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if length <= 0 or length > 2_000_000:
                        raise RuntimeError("排版数据大小异常")
                    payload = json.loads(self.rfile.read(length).decode("utf-8"))
                    if not isinstance(payload, dict):
                        raise RuntimeError("排版数据格式异常")
                    self.send_json(workflow.save_handoff(payload))
                except Exception as error:
                    self.send_json({"error": str(error)}, status=400)
                return
            if path == "/publish":
                try:
                    media_id = workflow.publish_draft()
                    page = workflow.result_html(
                        message=f"公众号草稿创建成功；media_id：{media_id}"
                    )
                    self.send_bytes(page.encode("utf-8"))
                except Exception as error:
                    self.send_bytes(
                        workflow.result_html(error=str(error)).encode("utf-8"),
                        status=400,
                    )
                return
            self.send_bytes("页面不存在".encode("utf-8"), status=404)

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description="doocs/md 与公众号工作流本地桥接")
    parser.add_argument("--article", required=True)
    parser.add_argument("--port", type=int, default=8788)
    args = parser.parse_args()
    try:
        workflow = EditorWorkflow(args.article, args.port)
        server = ThreadingHTTPServer(
            ("127.0.0.1", args.port),
            make_handler(workflow),
        )
        print(
            f"排版工作流桥接：{workflow.base_url}/status",
            flush=True,
        )
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    except Exception as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

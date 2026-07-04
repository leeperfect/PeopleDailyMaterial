#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公众号接口首次启用向导与只读权限体检。"""

from __future__ import annotations

import argparse
import html
import os
import re
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.wechat_api import WechatApiError, draft_count, get_access_token, public_ip
from modules.writing_workflow import (
    atomic_write_json,
    atomic_write_text,
    load_public_config,
    project_path,
)


def save_credentials(app_id: str, app_secret: str) -> None:
    app_id = app_id.strip()
    app_secret = app_secret.strip()
    if not re.fullmatch(r"wx[A-Za-z0-9]{16}", app_id):
        raise ValueError("AppID 格式不正确，应以 wx 开头并包含 18 个字符")
    if not re.fullmatch(r"[A-Za-z0-9]{32,64}", app_secret):
        raise ValueError("AppSecret 格式不正确，请复制完整密钥")
    path = PROJECT_ROOT / ".env"
    existing = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    retained = [
        line
        for line in existing
        if not re.match(r"^\s*(?:WECHAT_APPID|WECHAT_APPSECRET)\s*=", line)
    ]
    if not retained:
        retained.append("# 本文件含敏感信息，已被 Git 忽略；不要复制到文章、聊天或提交记录。")
    lines = [*retained, f"WECHAT_APPID={app_id}", f"WECHAT_APPSECRET={app_secret}", ""]
    atomic_write_text(path, "\n".join(lines))
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def page(message: str = "", *, success: bool = False) -> str:
    tone = "#047857" if success else "#b45309"
    notice = (
        f'<div class="notice" style="border-color:{tone};color:{tone}">{html.escape(message)}</div>'
        if message
        else ""
    )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>公众号接口首次启用</title>
<style>
body{{margin:0;background:#f5f6f8;color:#202124;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}}
main{{max-width:720px;margin:36px auto;padding:30px;background:#fff;border-radius:16px;box-shadow:0 8px 32px #11182712}}
h1{{margin-top:0}} ol{{line-height:1.9}} label{{display:block;margin:18px 0 6px;font-weight:650}}
input{{width:100%;box-sizing:border-box;padding:12px;border:1px solid #cbd5e1;border-radius:8px;font-size:16px}}
button{{margin-top:20px;border:0;border-radius:9px;padding:12px 18px;background:#ff6a2a;color:#fff;font-size:16px;cursor:pointer}}
.notice{{margin:16px 0;padding:12px 14px;border:1px solid;border-radius:8px}} .small{{font-size:13px;color:#64748b}}
</style></head><body><main>
<h1>公众号接口首次启用</h1>
<p>Codex 会陪你逐步完成。当前页面只负责安全保存凭证，不会在页面或聊天中回显完整密钥。</p>
<ol>
<li>登录微信公众平台。</li>
<li>进入“设置与开发 → 基本配置”，找到 AppID，并启用或重置 AppSecret。</li>
<li>将两项填在下方；保存后回到 Codex，说“凭证已保存”。</li>
</ol>
{notice}
<form method="post" action="/save">
<label for="appid">AppID</label><input id="appid" name="appid" autocomplete="off" required>
<label for="secret">AppSecret</label><input id="secret" name="secret" type="password" autocomplete="new-password" required>
<button type="submit">安全保存到本机</button>
</form>
<p class="small">保存位置：项目根目录 .env；权限设为仅本机当前用户可读写；Git 已忽略该文件。</p>
</main></body></html>"""


class SetupHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        content = page()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/save":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        values = parse_qs(self.rfile.read(length).decode("utf-8"))
        try:
            save_credentials(values.get("appid", [""])[0], values.get("secret", [""])[0])
            content = page("凭证已安全保存。请回到 Codex 继续下一步。", success=True)
            status = 200
        except ValueError as error:
            content = page(str(error))
            status = 400
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def log_message(self, _format: str, *_args: object) -> None:
        # 禁止把表单请求写进访问日志。
        return


def serve(port: int) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", port), SetupHandler)
    print(f"本地私密配置页：http://127.0.0.1:{port}/")
    print("页面只监听本机；按 Ctrl+C 可停止。")
    server.serve_forever()


def preflight() -> None:
    config = load_public_config()
    ip = public_ip()
    print(f"当前公网 IP：{ip}")
    print("请确认该 IP 已加入公众号后台白名单。")
    get_access_token(force=True)
    print("AppID、AppSecret 与 IP 白名单验证通过。")
    try:
        count = draft_count()
    except WechatApiError as error:
        if error.code == 48001:
            atomic_write_json(
                project_path(config["wechat"]["setup_status"]),
                {
                    "status": "browser_fallback",
                    "public_ip": ip,
                    "checked_at": datetime.now().isoformat(timespec="seconds"),
                },
            )
        raise
    atomic_write_json(
        project_path(config["wechat"]["setup_status"]),
        {
            "status": "api_ready",
            "public_ip": ip,
            "draft_count": count,
            "checked_at": datetime.now().isoformat(timespec="seconds"),
        },
    )
    print(f"草稿箱只读权限验证通过；当前草稿数量：{count}")


def main() -> int:
    parser = argparse.ArgumentParser(description="公众号接口首次启用向导")
    subparsers = parser.add_subparsers(dest="command", required=True)
    serve_parser = subparsers.add_parser("serve", help="启动本地私密配置页")
    serve_parser.add_argument("--port", type=int, default=8788)
    subparsers.add_parser("public-ip", help="查询需要加入白名单的公网 IP")
    subparsers.add_parser("preflight", help="验证凭证、白名单和草稿权限")
    args = parser.parse_args()
    try:
        if args.command == "serve":
            serve(args.port)
        elif args.command == "public-ip":
            print(public_ip())
        else:
            preflight()
    except KeyboardInterrupt:
        return 0
    except WechatApiError as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

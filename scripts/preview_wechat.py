#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""启动完整 doocs/md 编辑器，或输出已生成的只读预览地址。"""

from __future__ import annotations

import argparse
import functools
import socket
import shutil
import subprocess
import sys
import time
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.writing_workflow import load_public_config, project_path, workflow_id


def editor_url(port: int) -> str:
    return f"http://127.0.0.1:{port}/md/"


def wait_until_ready(url: str, timeout: float = 20.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1):
                return True
        except Exception:
            time.sleep(0.5)
    return False


def stop_process(process: subprocess.Popen | None) -> None:
    if not process or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def port_is_in_use(port: int) -> bool:
    with socket.socket() as probe:
        probe.settimeout(0.3)
        return probe.connect_ex(("127.0.0.1", port)) == 0


def start_editor(
    article: str | None = None,
) -> tuple[str, subprocess.Popen, subprocess.Popen | None]:
    config = load_public_config()
    repo = project_path(config["doocs"]["local_dir"])
    if not (repo / ".peopledaily-revision").exists():
        raise RuntimeError("请先运行 python3 scripts/setup_doocs_md.py")
    if not shutil.which("pnpm"):
        raise RuntimeError("未找到 pnpm，无法启动 doocs/md")
    port = int(config["doocs"]["editor_port"])
    if port_is_in_use(port):
        raise RuntimeError(
            f"本地端口 {port} 已被旧编辑器占用，请先关闭旧编辑器再重试"
        )
    log_dir = project_path(".local/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = (log_dir / "doocs-md.log").open("a", encoding="utf-8")
    process = subprocess.Popen(
        [
            "pnpm",
            "--dir",
            str(repo),
            "--filter",
            "@md/web",
            "dev",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=repo,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    url = editor_url(port)
    if not wait_until_ready(url):
        stop_process(process)
        raise RuntimeError(f"doocs/md 未能启动，请查看 {log_file.name}")
    bridge_process: subprocess.Popen | None = None
    if article:
        article_path = project_path(article).resolve()
        bridge_port = int(config["doocs"].get("editor_bridge_port", 8810))
        if port_is_in_use(bridge_port):
            stop_process(process)
            raise RuntimeError(
                f"本地端口 {bridge_port} 已被旧桥接服务占用，"
                "请先关闭旧编辑器再重试"
            )
        bridge_log = (log_dir / "wechat-editor-bridge.log").open(
            "a",
            encoding="utf-8",
        )
        bridge_process = subprocess.Popen(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "wechat_editor_bridge.py"),
                "--article",
                str(article_path),
                "--port",
                str(bridge_port),
            ],
            cwd=PROJECT_ROOT,
            stdout=bridge_log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        bridge_url = f"http://127.0.0.1:{bridge_port}"
        if not wait_until_ready(f"{bridge_url}/status", timeout=10):
            stop_process(bridge_process)
            stop_process(process)
            raise RuntimeError(
                f"排版工作流桥接未能启动，请查看 {bridge_log.name}"
            )
        if bridge_process.poll() is not None:
            stop_process(process)
            raise RuntimeError(
                f"排版工作流桥接启动后异常退出，请查看 {bridge_log.name}"
            )
        url = (
            f"{url}?pdWorkflow={workflow_id(article_path)}"
        )
    return url, process, bridge_process


def free_port(preferred: int = 8790) -> int:
    for port in range(preferred, preferred + 20):
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("没有找到可用的本地预览端口")


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, _format: str, *_args: object) -> None:
        return


def serve_html(html_path: Path) -> None:
    port = free_port()
    handler = functools.partial(
        QuietStaticHandler,
        directory=str(html_path.parent),
    )
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    url = f"http://127.0.0.1:{port}/{quote(html_path.name)}"
    print(f"只读成品预览：{url}", flush=True)
    print("Codex 会保持该会话运行；预览结束后关闭即可。", flush=True)
    server.serve_forever()


def main() -> int:
    parser = argparse.ArgumentParser(description="公众号排版预览")
    parser.add_argument("--doocs", action="store_true", help="启动完整编辑器")
    parser.add_argument("--html", help="输出已有预览页地址")
    parser.add_argument("--article", help="完整编辑器准备载入的文章路径")
    args = parser.parse_args()
    try:
        if args.doocs:
            url, process, bridge_process = start_editor(args.article)
            print(f"完整 doocs/md 编辑器：{url}")
            print(f"运行进程：{process.pid}")
            if args.article:
                print(f"待载入文章：{project_path(args.article).resolve()}")
                print("“发布”按钮已接入保存排版与草稿同步的下一步。")
            print("Codex 可在内置浏览器中打开并导入文章，无需 IDE。")
            try:
                process.wait()
            finally:
                stop_process(bridge_process)
                stop_process(process)
        elif args.html:
            path = project_path(args.html).resolve()
            if not path.exists():
                raise RuntimeError(f"预览文件不存在：{path}")
            serve_html(path)
        else:
            parser.error("请选择 --doocs 或 --html")
    except KeyboardInterrupt:
        return 0
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

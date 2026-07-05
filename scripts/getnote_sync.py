#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把公众号文章送入得到大脑二润，并按精确 note_id 安全拉回。"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.writing_workflow import (
    article_state,
    body_hash,
    join_frontmatter,
    load_public_config,
    load_state,
    project_path,
    save_snapshot,
    save_state,
    split_frontmatter,
    structural_issues,
    title_from_article,
    unified_diff,
    workflow_id,
)


def getnote_executable() -> str:
    executable = shutil.which("getnote")
    if executable:
        return executable
    fallback = Path.home() / ".npm-global" / "bin" / "getnote"
    if fallback.exists():
        return str(fallback)
    raise RuntimeError("未找到 Get笔记 CLI，请先安装 @getnote/cli")


def run_getnote(arguments: list[str], timeout: int = 90) -> str:
    command = [getnote_executable(), *arguments]
    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("Get笔记请求超时，请稍后重试") from error
    if result.returncode != 0:
        message = (result.stderr or result.stdout).strip()
        if "会员" in message or "OpenAPI" in message:
            raise RuntimeError("得到大脑 OpenAPI 仅对会员开放")
        if "auth" in message.lower() or "login" in message.lower():
            raise RuntimeError("Get笔记登录状态失效，请重新登录")
        raise RuntimeError(f"Get笔记操作失败：{message}")
    return result.stdout


def parse_json_output(output: str) -> dict[str, Any]:
    try:
        data = json.loads(output)
    except json.JSONDecodeError as error:
        raise RuntimeError("Get笔记返回了无法识别的数据") from error
    if not isinstance(data, dict):
        raise RuntimeError("Get笔记返回结构异常")
    return data


def find_note(data: dict[str, Any]) -> dict[str, Any]:
    candidates = [
        data,
        data.get("data"),
        (data.get("data") or {}).get("note") if isinstance(data.get("data"), dict) else None,
        data.get("note"),
    ]
    for candidate in candidates:
        if isinstance(candidate, dict) and (
            candidate.get("note_id") or candidate.get("id")
        ):
            return candidate
    raise RuntimeError("Get笔记响应中没有真实 note_id")


def note_id_from_output(output: str) -> str:
    try:
        note = find_note(parse_json_output(output))
        return str(note.get("note_id") or note["id"])
    except RuntimeError:
        match = re.search(r'"(?:note_id|id)"\s*:\s*"?(\d{10,})"?', output)
        if match:
            return match.group(1)
        raise


def push(article: str, *, force: bool = False) -> str:
    config = load_public_config()
    article_path = project_path(article).resolve()
    if not article_path.exists():
        raise RuntimeError(f"文章不存在：{article_path}")

    original = article_path.read_text(encoding="utf-8")
    frontmatter, body, metadata = split_frontmatter(original)
    if not body.strip():
        raise RuntimeError("文章正文为空，不能送入得到大脑")

    state = load_state(config)
    entry = article_state(state, article_path, create=True)
    assert entry is not None
    current_hash = body_hash(body)
    if (
        not force
        and entry.get("note_id")
        and entry.get("pushed_body_hash") == current_hash
    ):
        print("这份正文已经送入得到大脑，没有重复创建笔记。")
        print(f"note_id: {entry['note_id']}")
        return str(entry["note_id"])

    title = title_from_article(article_path, metadata, body)
    note_title = (
        f"{config['getnote']['title_prefix']}"
        f"[PD-{workflow_id(article_path)}] {title}"
    )
    arguments = ["save", body, "--title", note_title]
    for tag in config["getnote"]["tags_waiting"]:
        arguments.extend(["--tag", tag])
    arguments.extend(["-o", "json"])

    output = run_getnote(arguments)
    note_id = note_id_from_output(output)
    detail = find_note(parse_json_output(run_getnote(["note", note_id, "-o", "json"])))

    snapshot = save_snapshot(
        article_path,
        metadata,
        "01-humanizer.md",
        join_frontmatter(frontmatter, body),
    )
    entry.update(
        {
            "note_id": str(note_id),
            "note_title": note_title,
            "pushed_at": datetime.now().isoformat(timespec="seconds"),
            "note_updated_at_at_push": detail.get("updated_at"),
            "pushed_body_hash": current_hash,
            "status": "awaiting_second_polish",
            "humanizer_snapshot": str(snapshot.relative_to(PROJECT_ROOT)),
        }
    )
    save_state(state, config)

    print("已送入得到大脑，等待二次润色。")
    print(f"标题：{note_title}")
    print(f"note_id：{note_id}")
    print("完成后对 Codex 说：“我在得到改好了，拉回。”")
    return str(note_id)


def pull(article: str, *, accept_risk: bool = False) -> None:
    config = load_public_config()
    article_path = project_path(article).resolve()
    if not article_path.exists():
        raise RuntimeError(f"文章不存在：{article_path}")

    state = load_state(config)
    entry = article_state(state, article_path)
    if not entry or not entry.get("note_id"):
        raise RuntimeError("没有找到这篇文章的 note_id，请先送入得到大脑")

    note = find_note(
        parse_json_output(
            run_getnote(["note", str(entry["note_id"]), "-o", "json"])
        )
    )
    new_body = str(note.get("content") or "").strip()
    if not new_body:
        raise RuntimeError("得到大脑返回的正文为空，已停止拉回")

    original = article_path.read_text(encoding="utf-8")
    frontmatter, old_body, metadata = split_frontmatter(original)
    new_hash = body_hash(new_body)
    if new_hash == entry.get("pushed_body_hash"):
        raise RuntimeError("得到大脑中的正文尚未变化，可能还没有完成二次润色")
    if new_hash == body_hash(old_body):
        raise RuntimeError("得到大脑内容与本地完全一致，无需覆盖")

    before_path = save_snapshot(
        article_path,
        metadata,
        "02-before-getnote-pull.md",
        original,
    )
    candidate = join_frontmatter(frontmatter, new_body)
    candidate_path = save_snapshot(
        article_path,
        metadata,
        "03-getnote-candidate.md",
        candidate,
    )
    diff_path = save_snapshot(
        article_path,
        metadata,
        "getnote-diff.patch",
        unified_diff(old_body, new_body),
    )

    issues = structural_issues(old_body, new_body)
    if issues and not accept_risk:
        details = "\n".join(f"- {issue}" for issue in issues)
        raise RuntimeError(
            "拉回校验未通过，未覆盖本地文章：\n"
            f"{details}\n"
            f"候选稿：{candidate_path}\n"
            f"差异报告：{diff_path}"
        )

    article_path.write_text(candidate, encoding="utf-8")
    entry.update(
        {
            "last_pulled_at": datetime.now().isoformat(timespec="seconds"),
            "note_updated_at_at_pull": note.get("updated_at"),
            "pulled_body_hash": new_hash,
            "status": "second_polish_pending_emphasis",
            "before_pull_snapshot": str(before_path.relative_to(PROJECT_ROOT)),
            "getnote_snapshot": str(candidate_path.relative_to(PROJECT_ROOT)),
            "diff_report": str(diff_path.relative_to(PROJECT_ROOT)),
            "validation_warnings": issues,
        }
    )
    save_state(state, config)

    tags = ",".join(config["getnote"]["tags_completed"])
    try:
        run_getnote(
            ["note", "update", str(entry["note_id"]), "--tag", tags, "-o", "json"],
            timeout=30,
        )
    except RuntimeError:
        # 标签更新失败不应撤销已经安全落地的正文。
        pass

    print("二润稿已安全拉回。")
    print(f"本地文章：{article_path}")
    print(f"拉回前快照：{before_path}")
    print(f"差异报告：{diff_path}")
    print("下一步：审查核心判断、公式和考场表达，只增加 Markdown 加粗标记。")
    if issues:
        print("已按明确授权接受以下风险：")
        for issue in issues:
            print(f"- {issue}")


def show_status(article: str | None) -> None:
    state = load_state()
    articles = state.get("articles", {})
    if article:
        path = project_path(article).resolve()
        entry = article_state(state, path)
        if not entry:
            print("这篇文章还没有进入写作工作流。")
            return
        print(json.dumps(entry, ensure_ascii=False, indent=2))
        return
    if not articles:
        print("暂无写作工作流记录。")
        return
    for path, entry in articles.items():
        print(f"{entry.get('status', 'unknown'):>24}  {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="得到大脑二润往返")
    subparsers = parser.add_subparsers(dest="command", required=True)
    push_parser = subparsers.add_parser("push", help="送入得到大脑")
    push_parser.add_argument("article")
    push_parser.add_argument("--force", action="store_true")
    pull_parser = subparsers.add_parser("pull", help="从得到大脑安全拉回")
    pull_parser.add_argument("article")
    pull_parser.add_argument("--accept-risk", action="store_true")
    status_parser = subparsers.add_parser("status", help="查看工作流状态")
    status_parser.add_argument("article", nargs="?")
    # 兼容旧入口。
    subparsers.add_parser("list", help="列出全部工作流记录")
    args = parser.parse_args()
    try:
        if args.command == "push":
            push(args.article, force=args.force)
        elif args.command == "pull":
            pull(args.article, accept_risk=args.accept_risk)
        elif args.command == "status":
            show_status(args.article)
        else:
            show_status(None)
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

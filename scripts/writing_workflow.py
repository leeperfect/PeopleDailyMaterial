#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公众号写作工作流统一入口；日常优先由 Codex 自然语言调用。"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.writing_workflow import (
    article_state,
    bold_phrases,
    cover_for_article,
    emphasis_only_issues,
    load_dotenv_values,
    load_public_config,
    load_state,
    project_path,
    save_snapshot,
    save_state,
    split_frontmatter,
)


def run_script(name: str, arguments: list[str]) -> int:
    process = subprocess.Popen(
        [sys.executable, str(PROJECT_ROOT / "scripts" / name), *arguments],
        cwd=PROJECT_ROOT,
    )
    try:
        return process.wait()
    except KeyboardInterrupt:
        if process.poll() is None:
            process.terminate()
        return 130


def doctor(article: str | None = None) -> int:
    config = load_public_config()
    checks: list[tuple[str, bool, str]] = []
    getnote = shutil.which("getnote") or str(Path.home() / ".npm-global/bin/getnote")
    checks.append(("Get笔记 CLI", Path(getnote).exists(), getnote))
    repo = project_path(config["doocs"]["local_dir"])
    revision_file = repo / ".peopledaily-revision"
    doocs_ok = (
        revision_file.exists()
        and revision_file.read_text(encoding="utf-8").strip()
        == config["doocs"]["revision"]
        and (repo / "packages/mcp-server/node_modules").exists()
    )
    checks.append(("doocs/md", doocs_ok, str(repo)))
    env = load_dotenv_values()
    wechat_ok = bool(env.get("WECHAT_APPID") and env.get("WECHAT_APPSECRET"))
    checks.append(("公众号接口凭证", wechat_ok, ".env"))
    for series, path in config["covers"].items():
        cover = project_path(path)
        checks.append((f"{series} 固定封面", cover.exists(), str(cover)))
    if article:
        article_path = project_path(article).resolve()
        checks.append(("文章文件", article_path.exists(), str(article_path)))
        if article_path.exists():
            _, _, metadata = split_frontmatter(article_path.read_text(encoding="utf-8"))
            try:
                cover_for_article(article_path, metadata, config)
                checks.append(("文章系列识别", True, "已匹配固定封面"))
            except Exception as error:
                checks.append(("文章系列识别", False, str(error)))
    for label, passed, detail in checks:
        symbol = "✓" if passed else "○"
        print(f"{symbol} {label}：{detail}")
    return 0 if all(item[1] for item in checks if item[0] != "公众号接口凭证") else 1


def status(article: str | None) -> None:
    state = load_state()
    if not article:
        articles = state.get("articles", {})
        if not articles:
            print("暂无写作工作流记录。")
            return
        for path, entry in articles.items():
            print(f"{entry.get('status', 'unknown'):>24}  {path}")
        return
    path = project_path(article).resolve()
    entry = article_state(state, path)
    if not entry:
        print("这篇文章还没有进入写作工作流。")
        return
    safe = dict(entry)
    # 状态中不应有密钥；仍明确只输出文章工作流字段。
    print(json.dumps(safe, ensure_ascii=False, indent=2))


def snapshot(article: str, stage: str) -> None:
    article_path = project_path(article).resolve()
    if not article_path.exists():
        raise RuntimeError(f"文章不存在：{article_path}")
    content = article_path.read_text(encoding="utf-8")
    _, _, metadata = split_frontmatter(content)
    filename = "00-draft.md" if stage == "draft" else "01-humanizer.md"
    path = save_snapshot(article_path, metadata, filename, content)
    print(f"已保存{stage}快照：{path}")


def emphasis_check(article: str) -> None:
    config = load_public_config()
    article_path = project_path(article).resolve()
    if not article_path.exists():
        raise RuntimeError(f"文章不存在：{article_path}")
    state = load_state(config)
    entry = article_state(state, article_path)
    if not entry or not entry.get("getnote_snapshot"):
        raise RuntimeError("没有找到二润拉回候选稿，不能校验重点加粗")

    baseline_path = project_path(str(entry["getnote_snapshot"])).resolve()
    if not baseline_path.exists():
        raise RuntimeError(f"二润拉回候选稿不存在：{baseline_path}")
    current = article_path.read_text(encoding="utf-8")
    baseline = baseline_path.read_text(encoding="utf-8")
    _, current_body, metadata = split_frontmatter(current)
    _, baseline_body, _ = split_frontmatter(baseline)
    issues = emphasis_only_issues(baseline_body, current_body)
    if issues:
        raise RuntimeError("；".join(issues))

    before = set(bold_phrases(baseline_body))
    after = bold_phrases(current_body)
    added = [phrase for phrase in after if phrase not in before]
    snapshot_path = save_snapshot(
        article_path,
        metadata,
        "04-emphasis-reviewed.md",
        current,
    )
    report = "\n".join(
        [
            "# 二润重点加粗审查",
            "",
            f"- 审查时间：{datetime.now().isoformat(timespec='seconds')}",
            f"- 新增加粗：{len(added)} 处",
            "- 校验结果：除 Markdown 加粗标记外，正文文字与结构未变化。",
            "",
            "## 新增加粗内容",
            "",
            *[f"- {phrase}" for phrase in added],
            "",
        ]
    )
    report_path = save_snapshot(
        article_path,
        metadata,
        "emphasis-review.md",
        report,
    )
    entry.update(
        {
            "status": "second_polish_complete",
            "emphasis_reviewed_at": datetime.now().isoformat(timespec="seconds"),
            "emphasis_snapshot": str(snapshot_path.relative_to(PROJECT_ROOT)),
            "emphasis_report": str(report_path.relative_to(PROJECT_ROOT)),
            "emphasis_added_phrases": added,
        }
    )
    save_state(state, config)
    print(f"重点加粗审查通过：新增 {len(added)} 处加粗。")
    print(f"审查快照：{snapshot_path}")
    print(f"审查报告：{report_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="公众号写作工作流")
    subparsers = parser.add_subparsers(dest="command", required=True)
    doctor_parser = subparsers.add_parser("doctor", help="检查本地能力")
    doctor_parser.add_argument("article", nargs="?")
    setup_parser = subparsers.add_parser("setup-doocs", help="安装固定 doocs/md")
    setup_parser.add_argument("--force", action="store_true")
    send_parser = subparsers.add_parser("send", help="把 Humanizer 后稿件送去二润")
    send_parser.add_argument("article")
    send_parser.add_argument("--force", action="store_true")
    snapshot_parser = subparsers.add_parser("snapshot", help="保存初稿或一润稿")
    snapshot_parser.add_argument("article")
    snapshot_parser.add_argument("--stage", choices=["draft", "humanizer"], required=True)
    pull_parser = subparsers.add_parser("pull", help="从得到大脑拉回")
    pull_parser.add_argument("article")
    emphasis_parser = subparsers.add_parser(
        "emphasis-check",
        help="校验二润稿只新增重点加粗，没有改动文字",
    )
    emphasis_parser.add_argument("article")
    preview_parser = subparsers.add_parser("preview", help="生成 doocs/md 只读预览")
    preview_parser.add_argument("article")
    layout_parser = subparsers.add_parser("save-layout", help="保存本文排版设置")
    layout_parser.add_argument("article")
    layout_parser.add_argument("layout_args", nargs=argparse.REMAINDER)
    editor_parser = subparsers.add_parser("editor", help="启动完整 doocs/md")
    editor_parser.add_argument("article", nargs="?")
    setup_wechat_parser = subparsers.add_parser("setup-wechat", help="启动私密配置页")
    setup_wechat_parser.add_argument("--port", default="8788")
    subparsers.add_parser("wechat-preflight", help="验证公众号接口")
    publish_parser = subparsers.add_parser("publish", help="同步公众号草稿箱")
    publish_parser.add_argument("article")
    publish_parser.add_argument("--dry-run", action="store_true")
    publish_parser.add_argument("--force", action="store_true")
    status_parser = subparsers.add_parser("status", help="查看状态")
    status_parser.add_argument("article", nargs="?")
    args = parser.parse_args()

    if args.command == "doctor":
        return doctor(args.article)
    if args.command == "setup-doocs":
        return run_script(
            "setup_doocs_md.py",
            ["--force"] if args.force else [],
        )
    if args.command == "send":
        return run_script(
            "getnote_sync.py",
            ["push", args.article, *(["--force"] if args.force else [])],
        )
    if args.command == "snapshot":
        try:
            snapshot(args.article, args.stage)
        except RuntimeError as error:
            print(str(error), file=sys.stderr)
            return 1
        return 0
    if args.command == "pull":
        return run_script("getnote_sync.py", ["pull", args.article])
    if args.command == "emphasis-check":
        try:
            emphasis_check(args.article)
        except RuntimeError as error:
            print(str(error), file=sys.stderr)
            return 1
        return 0
    if args.command == "preview":
        from render_wechat_html import render_article

        try:
            result = render_article(args.article)
        except RuntimeError as error:
            print(str(error), file=sys.stderr)
            return 1
        return run_script("preview_wechat.py", ["--html", result["preview_path"]])
    if args.command == "save-layout":
        return run_script(
            "render_wechat_html.py",
            ["save-layout", args.article, *args.layout_args],
        )
    if args.command == "editor":
        arguments = ["--doocs"]
        if args.article:
            arguments.extend(["--article", args.article])
        return run_script("preview_wechat.py", arguments)
    if args.command == "setup-wechat":
        return run_script("wechat_setup.py", ["serve", "--port", args.port])
    if args.command == "wechat-preflight":
        return run_script("wechat_setup.py", ["preflight"])
    if args.command == "publish":
        arguments = [args.article]
        if args.dry_run:
            arguments.append("--dry-run")
        if args.force:
            arguments.append("--force")
        return run_script("publish_wechat_draft.py", arguments)
    status(args.article)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

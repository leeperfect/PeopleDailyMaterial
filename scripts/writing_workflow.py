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
    PROJECT_ROOT,
    ExternalDraftMode,
    article_state,
    atomic_write_text,
    body_hash,
    bold_phrases,
    cover_for_article,
    emphasis_only_issues,
    file_sha256,
    join_frontmatter,
    load_dotenv_values,
    load_public_config,
    load_state,
    project_path,
    save_snapshot,
    save_state,
    split_frontmatter,
    unified_diff,
    validate_external_candidate_import,
    validate_external_draft_registration,
    workflow_id,
)
from typing import Any


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
                checks.append(("文章系列识别", True, "已匹配本篇或本系列封面"))
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


def _get_emphasis_baseline(entry: dict[str, Any]) -> tuple[str, str]:
    """获取重点加粗审查的基准快照路径和来源标签。

    支持两种基准：
    1. getnote_snapshot: 从得到大脑拉回的二润稿（标准流程）
    2. external_draft_snapshot: 外部成稿登记的用户源稿（免二润入口）

    Returns:
        (快照路径, 来源标签)
    """
    # 路径 1：标准得到大脑拉回
    if entry.get("getnote_snapshot"):
        return str(entry["getnote_snapshot"]), "二润拉回候选稿"

    # 路径 2：外部成稿登记
    external = entry.get("external_draft_registration")
    if isinstance(external, dict) and external.get("baseline_snapshot"):
        mode_label = external.get("mode_label", "外部成稿")
        return str(external["baseline_snapshot"]), f"{mode_label}基准稿"

    return "", ""


def register_external_draft(
    article: str,
    *,
    source_hash: str,
    reason: str,
    platform: str,
    mode: str,
    candidate: str | None = None,
    source_evidence: str | None = None,
    accept_structure_risk: bool = False,
) -> dict[str, Any]:
    """登记外部成稿或导入外部二润候选稿。

    这是"免二润"的正式可审计入口，支持两种场景：

    场景 A（无候选稿）：用户提供的现成稿
    - 源文件本身就是最终稿
    - 记录源 hash、授权、单篇作用域
    - 基准快照指向源文件

    场景 B（有候选稿）：外部二润候选导入
    - 用户在得到官方网页等渠道完成润色
    - 手动取回候选稿到本地
    - 校验并覆盖原文，记录来源证据
    - 基准快照指向导入后的候选稿

    两种场景都：
    - 不伪造 getnote pull 记录
    - 保留完整的校验链（emphasis-check、figures、readiness）
    - 记录单篇、单平台、当次授权
    """
    config = load_public_config()
    article_path = project_path(article).resolve()

    # 场景 A：用户提供的现成稿（无候选稿）
    if not candidate:
        validation = validate_external_draft_registration(
            article_path,
            expected_hash=source_hash,
            authorization_reason=reason,
            target_platform=platform,
            mode=mode,
        )
        if not validation["ok"]:
            raise RuntimeError("外部成稿校验未通过：\n" + "\n".join(f"- {issue}" for issue in validation["issues"]))

        source = article_path.read_text(encoding="utf-8")
        frontmatter, body, metadata = split_frontmatter(source)
        now = datetime.now().isoformat(timespec="seconds")

        baseline_snapshot = save_snapshot(
            article_path,
            metadata,
            "00-external-draft-baseline.md",
            source,
        )

        state = load_state(config)
        entry = article_state(state, article_path, create=True)
        assert entry is not None

        registration = {
            "mode": mode,
            "mode_label": validation["mode_label"],
            "registered_at": now,
            "source_file_hash": validation["actual_hash"],
            "source_body_hash": validation["body_hash"],
            "authorization_reason": reason,
            "target_platform": platform,
            "baseline_snapshot": str(baseline_snapshot.relative_to(PROJECT_ROOT)),
            "candidate_imported": False,
        }
        entry["external_draft_registration"] = registration
        entry["status"] = "external_draft_registered"
        save_state(state, config)

        print(f"外部成稿登记成功：{validation['mode_label']}")
        print(f"源稿 SHA256：{validation['actual_hash']}")
        print(f"授权理由：{reason}")
        print(f"目标平台：{platform}")
        print(f"基准快照：{baseline_snapshot}")
        print("下一步：审查重点加粗（emphasis-check）")

        return {
            "ok": True,
            "scenario": "user_provided_draft",
            "registration": registration,
        }

    # 场景 B：外部二润候选导入
    if not source_evidence:
        raise RuntimeError("导入外部候选稿必须提供来源证据（--source-evidence）")

    candidate_path = project_path(candidate).resolve()
    validation = validate_external_candidate_import(
        article_path,
        candidate_path,
        source_evidence=source_evidence,
    )

    # 检查源稿 hash 是否匹配
    if validation.get("original_file_hash") != source_hash:
        raise RuntimeError(
            f"原稿 SHA256 不匹配：\n"
            f"  预期：{source_hash}\n"
            f"  实际：{validation.get('original_file_hash')}\n"
            f"请确认文章未被修改"
        )

    structure_issues = validation.get("structure_issues", [])
    if structure_issues and not accept_structure_risk:
        raise RuntimeError(
            "候选稿结构校验未通过（与标准 pull 相同检查）：\n"
            + "\n".join(f"- {issue}" for issue in structure_issues)
            + "\n如确认接受风险，请加 --accept-structure-risk"
        )

    if not validation["ok"]:
        non_structure_issues = [issue for issue in validation["issues"] if issue not in structure_issues]
        if non_structure_issues:
            raise RuntimeError("外部候选稿校验未通过：\n" + "\n".join(f"- {issue}" for issue in non_structure_issues))

    # 读取原稿和候选稿
    original_source = article_path.read_text(encoding="utf-8")
    frontmatter, original_body, metadata = split_frontmatter(original_source)
    candidate_source = candidate_path.read_text(encoding="utf-8")
    _, candidate_body, _ = split_frontmatter(candidate_source)

    now = datetime.now().isoformat(timespec="seconds")

    # 保存导入前快照
    before_import_snapshot = save_snapshot(
        article_path,
        metadata,
        "02-before-external-import.md",
        original_source,
    )

    # 合并：保留原 YAML，使用候选正文
    merged = join_frontmatter(frontmatter, candidate_body)
    merged_snapshot = save_snapshot(
        article_path,
        metadata,
        "03-external-candidate.md",
        merged,
    )

    # 保存差异报告
    diff_report = unified_diff(original_body, candidate_body)
    diff_path = save_snapshot(
        article_path,
        metadata,
        "external-candidate-diff.patch",
        diff_report,
    )

    # 覆盖原文
    atomic_write_text(article_path, merged)

    # 更新状态
    state = load_state(config)
    entry = article_state(state, article_path, create=True)
    assert entry is not None

    registration = {
        "mode": mode,
        "mode_label": ExternalDraftMode.label(mode),
        "registered_at": now,
        "source_file_hash": source_hash,
        "source_body_hash": validation["original_hash"],
        "authorization_reason": reason,
        "target_platform": platform,
        "candidate_imported": True,
        "candidate_source_path": str(candidate_path),
        "candidate_file_hash": validation["candidate_file_hash"],
        "candidate_body_hash": validation["candidate_hash"],
        "source_evidence": source_evidence,
        "before_import_snapshot": str(before_import_snapshot.relative_to(PROJECT_ROOT)),
        "baseline_snapshot": str(merged_snapshot.relative_to(PROJECT_ROOT)),
        "diff_report": str(diff_path.relative_to(PROJECT_ROOT)),
        "structure_warnings": structure_issues,
        "structure_risk_accepted": accept_structure_risk and bool(structure_issues),
    }
    entry["external_draft_registration"] = registration
    entry["status"] = "external_draft_registered"
    save_state(state, config)

    print(f"外部候选稿导入成功：{ExternalDraftMode.label(mode)}")
    print(f"来源证据：{source_evidence}")
    print(f"原稿 SHA256：{source_hash}")
    print(f"候选稿 SHA256：{validation['candidate_file_hash']}")
    print(f"导入前快照：{before_import_snapshot}")
    print(f"候选稿快照：{merged_snapshot}")
    print(f"差异报告：{diff_path}")
    if structure_issues:
        print("已接受的结构警告：")
        for issue in structure_issues:
            print(f"  - {issue}")
    print("下一步：审查重点加粗（emphasis-check）")

    return {
        "ok": True,
        "scenario": "external_candidate_import",
        "registration": registration,
    }


def emphasis_check(article: str) -> None:
    config = load_public_config()
    article_path = project_path(article).resolve()
    if not article_path.exists():
        raise RuntimeError(f"文章不存在：{article_path}")
    state = load_state(config)
    entry = article_state(state, article_path)
    if not entry:
        raise RuntimeError("没有找到这篇文章的工作流记录")

    baseline_snapshot, baseline_label = _get_emphasis_baseline(entry)
    if not baseline_snapshot:
        raise RuntimeError(
            "没有找到重点加粗审查的基准稿：\n"
            "- 标准流程需要先从得到大脑拉回二润稿\n"
            "- 免二润入口需要先登记外部成稿"
        )

    baseline_path = project_path(baseline_snapshot).resolve()
    if not baseline_path.exists():
        raise RuntimeError(f"{baseline_label}不存在：{baseline_path}")
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

    # 外部成稿登记（免二润入口）
    external_parser = subparsers.add_parser(
        "register-external-draft",
        help="登记外部成稿或导入外部二润候选稿（免二润入口）",
    )
    external_parser.add_argument("article", help="文章路径")
    external_parser.add_argument(
        "--source-hash",
        required=True,
        help="源稿 SHA256 哈希值（64位十六进制）",
    )
    external_parser.add_argument(
        "--reason",
        required=True,
        help="授权理由：为什么本篇可跳过得到大脑二润",
    )
    external_parser.add_argument(
        "--platform",
        choices=["wechat", "toutiao", "wechat_only"],
        default="wechat_only",
        help="目标平台（默认仅公众号）",
    )
    external_parser.add_argument(
        "--mode",
        choices=list(ExternalDraftMode.VALID_MODES),
        default=ExternalDraftMode.POLISH_COMPLETED_EXTERNALLY,
        help="外部成稿模式：polish_completed_externally（外部二润已完成）或 polish_not_applicable（二润不适用）",
    )
    external_parser.add_argument(
        "--candidate",
        help="外部二润候选稿路径（提供时会校验并覆盖原文）",
    )
    external_parser.add_argument(
        "--source-evidence",
        help='候选稿来源证据（如"得到官方网页@润色一下 2026-11-22"）',
    )
    external_parser.add_argument(
        "--accept-structure-risk",
        action="store_true",
        help="明确接受候选稿的结构校验警告",
    )

    preview_parser = subparsers.add_parser("preview", help="生成 doocs/md 只读预览")
    preview_parser.add_argument("article")
    layout_parser = subparsers.add_parser("save-layout", help="保存本文排版设置")
    layout_parser.add_argument("article")
    layout_parser.add_argument("layout_args", nargs=argparse.REMAINDER)
    editor_parser = subparsers.add_parser("editor", help="启动完整 doocs/md")
    editor_parser.add_argument("article", nargs="?")
    figures_parser = subparsers.add_parser(
        "register-figures",
        help="登记NotebookLM PPT和信息图",
    )
    figures_parser.add_argument("article")
    figures_parser.add_argument("--pptx", required=True)
    figures_parser.add_argument("--infographic", required=True)
    figures_parser.add_argument("--slug", required=True)
    apply_figures_parser = subparsers.add_parser(
        "apply-figures",
        help="应用共用或单个平台配图方案",
    )
    apply_figures_parser.add_argument("article")
    apply_figures_parser.add_argument("--initial", action="store_true")
    apply_figures_parser.add_argument(
        "--platform",
        choices=["shared", "wechat", "toutiao"],
        default="shared",
    )
    confirm_figures_parser = subparsers.add_parser(
        "confirm-figures",
        help="确认本地双平台配图",
    )
    confirm_figures_parser.add_argument("article")
    confirm_inline_parser = subparsers.add_parser(
        "confirm-inline-figures",
        help="登记并确认 Obsidian 正文内手动插入的双平台配图",
    )
    confirm_inline_parser.add_argument("article")
    toutiao_preview_parser = subparsers.add_parser(
        "preview-toutiao",
        help="生成今日头条预览和浏览器交接包",
    )
    toutiao_preview_parser.add_argument("article")
    setup_wechat_parser = subparsers.add_parser("setup-wechat", help="启动私密配置页")
    setup_wechat_parser.add_argument("--port", default="8788")
    subparsers.add_parser("wechat-preflight", help="验证公众号接口")
    publish_parser = subparsers.add_parser("publish", help="同步公众号草稿箱")
    publish_parser.add_argument("article")
    publish_parser.add_argument("--dry-run", action="store_true")
    publish_parser.add_argument("--force", action="store_true")
    publish_parser.add_argument(
        "--wechat-html",
        help="gzh-design 生成并通过校验的公众号正文 HTML（新稿 zen-whitespace 小米橙）",
    )
    dual_parser = subparsers.add_parser(
        "sync-dual",
        help="同步公众号草稿并准备今日头条 Word 导入",
    )
    dual_parser.add_argument("article")
    dual_parser.add_argument("--platform", choices=["both", "wechat", "toutiao"], default="both")
    dual_parser.add_argument("--dry-run", action="store_true")
    dual_parser.add_argument("--force-wechat", action="store_true")
    dual_parser.add_argument(
        "--wechat-html",
        help="gzh-design 生成并通过校验的公众号正文 HTML（新稿 zen-whitespace 小米橙）",
    )
    dual_parser.add_argument(
        "--no-figures",
        action="store_true",
        help="无图文章模式：正文确无图片时豁免配图门槛（如热点系列）",
    )
    saved_parser = subparsers.add_parser(
        "mark-toutiao-saved",
        help="浏览器保存成功后登记今日头条草稿",
    )
    saved_parser.add_argument("article")
    saved_parser.add_argument("--draft-url", default="")
    saved_parser.add_argument("--draft-id", default="")
    profile_parser = subparsers.add_parser(
        "save-toutiao-profile",
        help="保存首次确认的今日头条常用选项",
    )
    profile_parser.add_argument("--profile-json", required=True)
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
    if args.command == "register-external-draft":
        try:
            result = register_external_draft(
                args.article,
                source_hash=args.source_hash,
                reason=args.reason,
                platform=args.platform,
                mode=args.mode,
                candidate=args.candidate,
                source_evidence=args.source_evidence,
                accept_structure_risk=args.accept_structure_risk,
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
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
    if args.command == "register-figures":
        return run_script(
            "register_notebooklm_assets.py",
            [
                args.article,
                "--pptx",
                args.pptx,
                "--infographic",
                args.infographic,
                "--slug",
                args.slug,
            ],
        )
    if args.command == "apply-figures":
        arguments = [args.article, "--platform", args.platform]
        if args.initial:
            arguments.append("--initial")
        return run_script("apply_figure_plan.py", arguments)
    if args.command == "confirm-figures":
        from modules.figure_workflow import confirm_figures
        from render_toutiao_html import render_toutiao
        from render_wechat_html import render_article

        try:
            article_path = project_path(args.article).resolve()
            render_article(str(article_path))
            render_toutiao(str(article_path))
            result = confirm_figures(article_path)
        except RuntimeError as error:
            print(str(error), file=sys.stderr)
            return 1
        print(f"双平台配图已确认：{result['confirmed_at']}")
        return 0
    if args.command == "confirm-inline-figures":
        from modules.figure_workflow import confirm_figures, import_inline_markdown_figures
        from render_toutiao_html import render_toutiao
        from render_wechat_html import render_article

        try:
            article_path = project_path(args.article).resolve()
            imported = import_inline_markdown_figures(article_path)
            render_article(str(article_path))
            render_toutiao(str(article_path))
            result = confirm_figures(article_path)
        except RuntimeError as error:
            print(str(error), file=sys.stderr)
            return 1
        print(f"已登记正文配图：{imported['figure_count']} 张")
        print(f"双平台配图已确认：{result['confirmed_at']}")
        return 0
    if args.command == "preview-toutiao":
        return run_script("render_toutiao_html.py", [args.article])
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
        if args.wechat_html:
            arguments.extend(["--wechat-html", args.wechat_html])
        return run_script("publish_wechat_draft.py", arguments)
    if args.command == "sync-dual":
        arguments = ["prepare", args.article, "--platform", args.platform]
        if args.dry_run:
            arguments.append("--dry-run")
        if args.force_wechat:
            arguments.append("--force-wechat")
        if args.wechat_html:
            arguments.extend(["--wechat-html", args.wechat_html])
        if args.no_figures:
            arguments.append("--no-figures")
        return run_script("sync_dual_drafts.py", arguments)
    if args.command == "mark-toutiao-saved":
        arguments = ["mark-toutiao-saved", args.article]
        if args.draft_url:
            arguments.extend(["--draft-url", args.draft_url])
        if args.draft_id:
            arguments.extend(["--draft-id", args.draft_id])
        return run_script("sync_dual_drafts.py", arguments)
    if args.command == "save-toutiao-profile":
        return run_script(
            "sync_dual_drafts.py",
            ["save-toutiao-profile", "--profile-json", args.profile_json],
        )
    status(args.article)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

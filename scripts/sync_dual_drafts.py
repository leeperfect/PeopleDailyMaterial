#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""编排红白色系公众号草稿与今日头条 Word 导入草稿，绝不正式发布。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from modules.platform_workflow import require_publication_ready  # noqa: E402
from modules.writing_workflow import (  # noqa: E402
    atomic_write_json,
    article_state,
    body_hash,
    load_public_config,
    load_state,
    project_path,
    save_state,
    split_frontmatter,
    workflow_id,
)
from build_toutiao_import_docx import build as build_toutiao_docx  # noqa: E402
from publish_wechat_draft import publication_fingerprint, publish  # noqa: E402
from publish_wechat_draft import load_gzh_design_html  # noqa: E402
from render_toutiao_html import toutiao_title  # noqa: E402


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def prepare(
    article: str,
    *,
    platform: str = "both",
    dry_run: bool = False,
    force_wechat: bool = False,
    wechat_html: str | None = None,
) -> dict[str, Any]:
    config = load_public_config()
    article_path = project_path(article).resolve()
    if not article_path.exists():
        raise RuntimeError(f"文章不存在：{article_path}")
    readiness = require_publication_ready(article_path)
    figure_fingerprint = str(readiness["figure_check"]["fingerprint"])

    state = load_state(config)
    entry = article_state(state, article_path, create=True)
    assert entry is not None
    result: dict[str, Any] = {
        "article": str(article_path),
        "mode": "draft_only",
        "figure_fingerprint": figure_fingerprint,
        "wechat": {"status": "not_requested"},
        "toutiao": {"status": "not_requested"},
    }

    if platform in ("both", "wechat"):
        try:
            if not wechat_html:
                raise RuntimeError(
                    "公众号同步必须先调用 gzh-design Skill 生成“红白色系”HTML，"
                    "再通过 --wechat-html 传入；不再默认使用 doocs/md"
                )
            _, article_body, _ = split_frontmatter(article_path.read_text(encoding="utf-8"))
            wechat_rendered = load_gzh_design_html(wechat_html, article_path, article_body)
            current_wechat_fingerprint = publication_fingerprint(
                wechat_rendered["article_hash"],
                wechat_rendered["layout"],
                figure_fingerprint,
            )
            previous = entry.get("wechat_draft") or {}
            if not force_wechat and previous.get("fingerprint") == current_wechat_fingerprint:
                result["wechat"] = {
                    "status": "reused",
                    "media_id": previous.get("media_id"),
                }
            elif dry_run:
                publish(
                    str(article_path),
                    dry_run=True,
                    force=force_wechat,
                    wechat_html=wechat_html,
                )
                result["wechat"] = {"status": "preflight_passed"}
            else:
                media_id = publish(
                    str(article_path),
                    force=force_wechat,
                    wechat_html=wechat_html,
                )
                result["wechat"] = {"status": "created", "media_id": media_id}
        except Exception as error:
            result["wechat"] = {"status": "failed", "error": str(error)}

    # 公众号发布函数会独立保存状态；重新读取，避免后续头条记录覆盖公众号结果。
    state = load_state(config)
    entry = article_state(state, article_path, create=True)
    assert entry is not None

    if platform in ("both", "toutiao"):
        try:
            source = article_path.read_text(encoding="utf-8")
            _, article_body, metadata = split_frontmatter(source)
            output_dir = Path(config["preview_root"]) / workflow_id(article_path) / "toutiao"
            output_dir.mkdir(parents=True, exist_ok=True)
            docx_path = PROJECT_ROOT / "data" / "exports" / f"{article_path.stem}-toutiao-import.docx"
            docx_result = build_toutiao_docx(article_path, docx_path, PROJECT_ROOT)
            payload_path = output_dir / "import-payload.json"
            title = toutiao_title(article_path, metadata, article_body)
            saved_profile = state.get("toutiao_option_profile")
            options = dict(config["toutiao"]["default_options"])
            if isinstance(saved_profile, dict):
                options.update(saved_profile)
            payload = {
                "platform": "toutiao",
                "mode": "document_import",
                "creator_url": config["toutiao"]["creator_url"],
                "drafts_url": config["toutiao"]["drafts_url"],
                "title": title,
                "docx_path": str(docx_path),
                "docx_size_bytes": docx_result["size_bytes"],
                "image_count": docx_result["image_count"],
                "heading_count": docx_result["heading_count"],
                "ordered_item_count": docx_result["ordered_item_count"],
                "bullet_item_count": docx_result["bullet_item_count"],
                "figure_fingerprint": figure_fingerprint,
                "article_hash": body_hash(article_body),
                "options": options,
                "cover_path": str(project_path(config["toutiao"]["fixed_cover"])),
            }
            atomic_write_json(payload_path, payload)
            previous = entry.get("toutiao_draft") or {}
            if (
                previous.get("figure_fingerprint") == figure_fingerprint
                and previous.get("article_hash") == payload["article_hash"]
                and previous.get("title") == title
                and previous.get("status") == "draft_only"
            ):
                result["toutiao"] = {
                    "status": "reused",
                    "draft_url": previous.get("draft_url"),
                }
            else:
                result["toutiao"] = {
                    "status": "preflight_passed" if dry_run else "browser_pending",
                    "payload_path": str(payload_path),
                    "docx_path": str(docx_path),
                    "creator_url": payload["creator_url"],
                    "image_count": payload["image_count"],
                }
                if not dry_run:
                    entry["toutiao_pending"] = {
                        "payload_path": str(payload_path),
                        "docx_path": str(docx_path),
                        "figure_fingerprint": figure_fingerprint,
                        "article_hash": payload["article_hash"],
                        "prepared_at": _now(),
                        "status": "browser_pending",
                    }
                    entry["status"] = "toutiao_draft_pending_browser"
        except Exception as error:
            result["toutiao"] = {"status": "failed", "error": str(error)}

    if not dry_run:
        stored_dual = entry.get("dual_sync") if isinstance(entry.get("dual_sync"), dict) else {}
        wechat_record = result["wechat"]
        toutiao_record = result["toutiao"]
        if wechat_record.get("status") == "not_requested":
            previous_wechat = stored_dual.get("wechat") if isinstance(stored_dual, dict) else None
            if isinstance(previous_wechat, dict) and previous_wechat.get("status") not in (None, "not_requested"):
                wechat_record = previous_wechat
            elif isinstance(entry.get("wechat_draft"), dict):
                wechat_record = {
                    "status": "preserved",
                    "media_id": entry["wechat_draft"].get("media_id"),
                }
        if toutiao_record.get("status") == "not_requested":
            previous_toutiao = stored_dual.get("toutiao") if isinstance(stored_dual, dict) else None
            if isinstance(previous_toutiao, dict) and previous_toutiao.get("status") not in (None, "not_requested"):
                toutiao_record = previous_toutiao
            elif isinstance(entry.get("toutiao_draft"), dict):
                toutiao_record = {
                    "status": "preserved",
                    "draft_url": entry["toutiao_draft"].get("draft_url"),
                }
        entry["dual_sync"] = {
            "prepared_at": _now(),
            "figure_fingerprint": figure_fingerprint,
            "wechat": wechat_record,
            "toutiao": toutiao_record,
        }
        save_state(state, config)
    return result


def mark_toutiao_saved(article: str, *, draft_url: str = "", draft_id: str = "") -> dict[str, Any]:
    config = load_public_config()
    article_path = project_path(article).resolve()
    state = load_state(config)
    entry = article_state(state, article_path)
    if not entry or not isinstance(entry.get("toutiao_pending"), dict):
        raise RuntimeError("没有待浏览器保存的今日头条草稿记录")
    pending = dict(entry["toutiao_pending"])
    payload_path = Path(str(pending.get("payload_path") or ""))
    if not payload_path.exists():
        raise RuntimeError("今日头条浏览器交接包不存在，无法登记保存结果")
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    if payload.get("figure_fingerprint") != pending.get("figure_fingerprint"):
        raise RuntimeError("今日头条交接包与当前待保存记录不一致")
    now = _now()
    record = {
        "status": "draft_only",
        "draft_id": draft_id or None,
        "draft_url": draft_url or None,
        "title": payload.get("title"),
        "article_hash": pending.get("article_hash"),
        "figure_fingerprint": pending.get("figure_fingerprint"),
        "saved_at": now,
    }
    entry["toutiao_draft"] = record
    entry["toutiao_pending"] = None
    entry["status"] = "toutiao_draft_saved"
    dual = entry.get("dual_sync")
    if isinstance(dual, dict):
        dual["toutiao"] = {"status": "saved", "draft_url": draft_url or None}
    save_state(state, config)
    return record


def save_toutiao_profile(profile_json: str) -> dict[str, Any]:
    try:
        profile = json.loads(profile_json)
    except json.JSONDecodeError as error:
        raise RuntimeError("今日头条选项模板不是有效 JSON") from error
    if not isinstance(profile, dict) or not profile:
        raise RuntimeError("今日头条选项模板不能为空")
    if any(not isinstance(key, str) or not isinstance(value, (str, bool, int, float)) for key, value in profile.items()):
        raise RuntimeError("今日头条选项模板只允许保存选项名称和简单值")
    if profile.get("auto_publish") is True:
        raise RuntimeError("安全限制：今日头条模板不能开启自动正式发布")
    # 这两个键是工作流安全边界，不是头条页面上的可点击选项。
    profile.pop("auto_publish", None)
    profile.pop("save_as_draft", None)
    if not profile:
        raise RuntimeError("请至少保存一个头条页面上实际可见的常用选项")
    config = load_public_config()
    state = load_state(config)
    state["toutiao_option_profile"] = profile
    save_state(state, config)
    return profile


def main() -> int:
    parser = argparse.ArgumentParser(description="同步公众号与今日头条草稿")
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare", help="创建红白公众号草稿并准备头条 Word 导入")
    prepare_parser.add_argument("article")
    prepare_parser.add_argument("--platform", choices=["both", "wechat", "toutiao"], default="both")
    prepare_parser.add_argument("--dry-run", action="store_true")
    prepare_parser.add_argument("--force-wechat", action="store_true")
    prepare_parser.add_argument("--wechat-html")
    saved_parser = subparsers.add_parser("mark-toutiao-saved", help="浏览器确认保存后登记头条草稿")
    saved_parser.add_argument("article")
    saved_parser.add_argument("--draft-url", default="")
    saved_parser.add_argument("--draft-id", default="")
    profile_parser = subparsers.add_parser("save-toutiao-profile", help="保存首次确认的头条常用选项")
    profile_parser.add_argument("--profile-json", required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = prepare(
                args.article,
                platform=args.platform,
                dry_run=args.dry_run,
                force_wechat=args.force_wechat,
                wechat_html=args.wechat_html,
            )
        elif args.command == "mark-toutiao-saved":
            result = mark_toutiao_saved(
                args.article,
                draft_url=args.draft_url,
                draft_id=args.draft_id,
            )
        else:
            result = save_toutiao_profile(args.profile_json)
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""双平台配图清单、正文插入计划与人工确认门槛。"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from modules.writing_workflow import (
    PROJECT_ROOT,
    article_state,
    atomic_write_text,
    body_hash,
    load_public_config,
    load_state,
    save_snapshot,
    save_state,
    split_frontmatter,
)


PLATFORMS = ("shared", "wechat", "toutiao")


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _heading_from_position(value: str) -> str:
    value = value.strip()
    if value.endswith("之前"):
        value = value[:-2]
    return value.strip()


def _legacy_plan(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    selected = [
        figure
        for figure in manifest.get("figures", [])
        if figure.get("used_in_wechat") or figure.get("wechat_status") == "selected"
    ]
    selected.sort(key=lambda item: int(item.get("article_order") or 10_000))
    plan: list[dict[str, Any]] = []
    for figure in selected:
        heading = _heading_from_position(str(figure.get("article_position") or ""))
        if heading.startswith("## "):
            plan.append({"id": str(figure.get("id") or ""), "before_heading": heading})
    return plan


def normalize_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """在内存中把旧公众号清单补成双平台结构，不破坏旧字段。"""
    manifest.setdefault("figures", [])
    plans = manifest.get("plans")
    if not isinstance(plans, dict):
        plans = {}
        manifest["plans"] = plans
    shared = plans.get("shared")
    if not isinstance(shared, dict):
        shared = {"items": _legacy_plan(manifest), "updated_at": None}
        plans["shared"] = shared
    shared.setdefault("items", [])
    for platform in ("wechat", "toutiao"):
        record = plans.get(platform)
        if not isinstance(record, dict):
            record = {"inherit": "shared", "items": None, "updated_at": None}
            plans[platform] = record
        record.setdefault("inherit", "shared")
        record.setdefault("items", None)
    confirmation = manifest.get("confirmation")
    if not isinstance(confirmation, dict):
        manifest["confirmation"] = {
            "status": "editing",
            "confirmed_at": None,
            "body_hash": None,
            "plan_fingerprint": None,
        }
    manifest["schema_version"] = max(int(manifest.get("schema_version") or 1), 2)
    return manifest


def load_manifest(article_path: Path) -> tuple[Path, dict[str, Any]]:
    source = article_path.read_text(encoding="utf-8")
    _, _, metadata = split_frontmatter(source)
    raw_path = str(metadata.get("figure_manifest") or "").strip()
    if not raw_path:
        raise RuntimeError("这篇文章尚未登记配图清单")
    path = (PROJECT_ROOT / raw_path).resolve()
    if not path.exists():
        raise RuntimeError(f"配图清单不存在：{path}")
    manifest = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(manifest, dict) or not isinstance(manifest.get("figures"), list):
        raise RuntimeError("配图清单格式异常")
    return path, normalize_manifest(manifest)


def save_manifest(path: Path, manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = _now()
    atomic_write_text(
        path,
        yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False, width=1000),
    )


def article_headings(body: str) -> list[dict[str, str]]:
    headings = re.findall(r"^##\s+(.+)$", body, re.M)
    result: list[dict[str, str]] = []
    for heading in headings:
        exact = f"## {heading}"
        if heading == "参考文章":
            label = "正文结尾、参考文章之前"
        elif heading == "金句集合":
            label = "金句集合之前"
        else:
            label = f"“{heading}”之前"
        result.append({"value": exact, "label": label})
    return result


def _normalized_context(value: str) -> str:
    value = re.sub(r"!\[[^\]]*]\([^)]*\)", "", value)
    value = re.sub(r"\s+", "", value)
    return value[:80]


def heading_context(body: str, heading: str) -> str:
    position = body.find(heading)
    if position < 0:
        return ""
    following = body[position + len(heading):]
    next_heading = re.search(r"^##\s+", following, re.M)
    if next_heading:
        following = following[: next_heading.start()]
    return _normalized_context(following)


def figure_by_id(manifest: dict[str, Any], figure_id: str) -> dict[str, Any]:
    for item in manifest["figures"]:
        if str(item.get("id")) == figure_id:
            return item
    raise RuntimeError(f"配图编号不存在：{figure_id}")


def strip_managed_figures(body: str, manifest: dict[str, Any]) -> str:
    cleaned = body
    for figure in manifest["figures"]:
        raw_path = str(figure.get("file") or "")
        if not raw_path:
            continue
        path = re.escape(raw_path)
        pattern = rf"\n*!\[[^\n]*]\({path}\)\s*\n*"
        cleaned = re.sub(pattern, "\n\n", cleaned)
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


def normalize_plan(
    plan: list[dict[str, Any]],
    manifest: dict[str, Any],
    body: str | None = None,
) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in plan:
        if not isinstance(item, dict):
            continue
        figure_id = str(item.get("id") or "").strip()
        heading = str(item.get("before_heading") or "").strip()
        if not figure_id or not heading or figure_id in seen:
            continue
        figure_by_id(manifest, figure_id)
        record = {"id": figure_id, "before_heading": heading}
        context = str(item.get("context_after") or "").strip()
        if body is not None:
            context = heading_context(body, heading)
        if context:
            record["context_after"] = context
        normalized.append(record)
        seen.add(figure_id)
    return normalized


def effective_plan(manifest: dict[str, Any], platform: str) -> list[dict[str, Any]]:
    if platform not in ("wechat", "toutiao"):
        raise RuntimeError(f"不支持的发布平台：{platform}")
    normalize_manifest(manifest)
    record = manifest["plans"][platform]
    items = record.get("items")
    if items is None:
        items = manifest["plans"]["shared"].get("items") or []
    return [dict(item) for item in items if isinstance(item, dict)]


def _validate_plan(
    body: str,
    plan: list[dict[str, Any]],
    manifest: dict[str, Any],
    platform_label: str,
) -> list[str]:
    issues: list[str] = []
    headings = {item["value"] for item in article_headings(body)}
    seen: set[str] = set()
    for item in plan:
        figure_id = str(item.get("id") or "")
        heading = str(item.get("before_heading") or "")
        if figure_id in seen:
            issues.append(f"{platform_label}重复使用配图 {figure_id}")
            continue
        seen.add(figure_id)
        try:
            figure = figure_by_id(manifest, figure_id)
        except RuntimeError as error:
            issues.append(f"{platform_label}{error}")
            continue
        file_path = PROJECT_ROOT / str(figure.get("file") or "")
        if not file_path.exists():
            issues.append(f"{platform_label}配图文件不存在：{figure_id}")
        if int(figure.get("width_px") or 0) <= 0 or int(figure.get("height_px") or 0) <= 0:
            issues.append(f"{platform_label}配图尺寸异常：{figure_id}")
        if heading not in headings:
            issues.append(f"{platform_label}正文中找不到插图位置：{heading or figure_id}")
            continue
        stored_context = str(item.get("context_after") or "")
        current_context = heading_context(body, heading)
        if stored_context and current_context != stored_context:
            issues.append(
                f"{platform_label}“{heading.removeprefix('## ')}”附近文字已经变化，请重新确认配图位置"
            )
    if not plan:
        issues.append(f"{platform_label}尚未选择任何正文配图")
    return issues


def apply_plan_to_body(
    body: str,
    plan: list[dict[str, Any]],
    manifest: dict[str, Any],
) -> str:
    clean_body = strip_managed_figures(body, manifest)
    normalized = normalize_plan(plan, manifest)
    issues = _validate_plan(clean_body, normalized, manifest, "")
    if issues:
        raise RuntimeError("；".join(issues))
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in normalized:
        groups.setdefault(item["before_heading"], []).append(
            figure_by_id(manifest, item["id"])
        )
    updated = clean_body
    for heading in [item["value"] for item in article_headings(clean_body)]:
        figures = groups.get(heading, [])
        if not figures:
            continue
        blocks = [
            f"![{figure.get('caption') or figure.get('title') or figure['id']}]({figure['file']})"
            for figure in figures
        ]
        block = "\n\n".join(blocks)
        updated = updated.replace(heading, f"{block}\n\n{heading}", 1)
    return updated.rstrip()


def invalidate_confirmation(manifest: dict[str, Any]) -> None:
    manifest["confirmation"] = {
        "status": "editing",
        "confirmed_at": None,
        "body_hash": None,
        "plan_fingerprint": None,
    }


def invalidate_article_confirmation(article_path: Path) -> None:
    """正文在编辑器发生变化后，撤销旧的人工配图确认。"""
    manifest_path, manifest = load_manifest(article_path)
    invalidate_confirmation(manifest)
    save_manifest(manifest_path, manifest)
    config = load_public_config()
    state = load_state(config)
    entry = article_state(state, article_path, create=True)
    assert entry is not None
    entry.update(
        {
            "status": "figures_editing",
            "figures_editing_at": _now(),
            "figures_confirmed_at": None,
            "figure_plan_fingerprint": None,
        }
    )
    save_state(state, config)


def apply_plan(
    article_path: Path,
    plan: list[dict[str, Any]],
    *,
    platform: str = "shared",
) -> dict[str, Any]:
    if platform not in PLATFORMS:
        raise RuntimeError(f"不支持的配图方案：{platform}")
    manifest_path, manifest = load_manifest(article_path)
    source = article_path.read_text(encoding="utf-8")
    frontmatter, body, metadata = split_frontmatter(source)
    clean_body = strip_managed_figures(body, manifest)
    normalized = normalize_plan(plan, manifest, clean_body)
    issues = _validate_plan(clean_body, normalized, manifest, "")
    if issues:
        raise RuntimeError("；".join(issues))

    record = manifest["plans"][platform]
    record["items"] = normalized
    record["updated_at"] = _now()
    if platform in ("wechat", "toutiao"):
        record["inherit"] = None
    invalidate_confirmation(manifest)

    before_plan_path: Path | None = None
    if platform in ("shared", "wechat"):
        wechat_plan = normalized if platform == "wechat" else effective_plan(manifest, "wechat")
        updated = apply_plan_to_body(clean_body, wechat_plan, manifest)
        if updated.strip() != body.strip():
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            before_plan_path = save_snapshot(
                article_path,
                metadata,
                f"05-before-figure-plan-{timestamp}.md",
                source,
            )
            atomic_write_text(article_path, f"{frontmatter}\n\n{updated}\n")

    sync_usage(article_path, manifest_path=manifest_path, manifest=manifest)
    save_manifest(manifest_path, manifest)
    config = load_public_config()
    state = load_state(config)
    entry = article_state(state, article_path, create=True)
    assert entry is not None
    entry.update(
        {
            "status": "figures_editing",
            "figures_editing_at": _now(),
            "figures_confirmed_at": None,
            "figure_plan_fingerprint": None,
        }
    )
    save_state(state, config)
    return {
        "manifest_path": str(manifest_path.relative_to(PROJECT_ROOT)),
        "used_count": len(normalized),
        "figure_count": len(manifest["figures"]),
        "platform": platform,
        "before_plan_snapshot": (
            str(before_plan_path.relative_to(PROJECT_ROOT)) if before_plan_path else ""
        ),
    }


def reset_platform_override(article_path: Path, platform: str) -> dict[str, Any]:
    if platform not in ("wechat", "toutiao"):
        raise RuntimeError("只有公众号或今日头条可以恢复共用方案")
    manifest_path, manifest = load_manifest(article_path)
    manifest["plans"][platform] = {
        "inherit": "shared",
        "items": None,
        "updated_at": _now(),
    }
    invalidate_confirmation(manifest)
    save_manifest(manifest_path, manifest)
    if platform == "wechat":
        return apply_plan(
            article_path,
            list(manifest["plans"]["shared"].get("items") or []),
            platform="shared",
        )
    config = load_public_config()
    state = load_state(config)
    entry = article_state(state, article_path, create=True)
    assert entry is not None
    entry.update(
        {
            "status": "figures_editing",
            "figures_confirmed_at": None,
            "figure_plan_fingerprint": None,
        }
    )
    save_state(state, config)
    return {
        "manifest_path": str(manifest_path.relative_to(PROJECT_ROOT)),
        "used_count": len(effective_plan(manifest, platform)),
        "figure_count": len(manifest["figures"]),
        "platform": platform,
        "before_plan_snapshot": "",
    }


def sync_usage(
    article_path: Path,
    body: str | None = None,
    *,
    manifest_path: Path | None = None,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if manifest_path is None or manifest is None:
        manifest_path, manifest = load_manifest(article_path)
    if body is None:
        _, body, _ = split_frontmatter(article_path.read_text(encoding="utf-8"))
    selected = {str(item.get("id")): item for item in effective_plan(manifest, "wechat")}
    positions: list[tuple[int, dict[str, Any]]] = []
    for figure in manifest["figures"]:
        figure_id = str(figure.get("id") or "")
        item = selected.get(figure_id)
        used = item is not None
        figure["used_in_wechat"] = used
        figure["wechat_status"] = "selected" if used else "candidate"
        figure["article_position"] = None
        figure["article_order"] = None
        if used:
            heading = str(item.get("before_heading") or "")
            figure["article_position"] = f"{heading}之前"
            marker = f"]({figure.get('file')})"
            positions.append((body.find(marker), figure))
    for order, (_, figure) in enumerate(sorted(positions, key=lambda item: item[0]), 1):
        figure["article_order"] = order
    save_manifest(manifest_path, manifest)
    return {
        "manifest_path": str(manifest_path.relative_to(PROJECT_ROOT)),
        "used_count": len(positions),
        "figure_count": len(manifest["figures"]),
    }


def body_for_platform(article_path: Path, platform: str) -> str:
    _, manifest = load_manifest(article_path)
    _, body, _ = split_frontmatter(article_path.read_text(encoding="utf-8"))
    clean_body = strip_managed_figures(body, manifest)
    return apply_plan_to_body(clean_body, effective_plan(manifest, platform), manifest)


def plan_fingerprint(article_path: Path, manifest: dict[str, Any]) -> str:
    _, body, _ = split_frontmatter(article_path.read_text(encoding="utf-8"))
    clean_body = strip_managed_figures(body, manifest)
    payload = {
        "body_hash": body_hash(clean_body),
        "wechat": effective_plan(manifest, "wechat"),
        "toutiao": effective_plan(manifest, "toutiao"),
        "assets": [
            {"id": item.get("id"), "sha256": item.get("sha256"), "file": item.get("file")}
            for item in manifest["figures"]
        ],
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def preflight_figures(article_path: Path, *, require_confirmed: bool = True) -> dict[str, Any]:
    manifest_path, manifest = load_manifest(article_path)
    _, body, _ = split_frontmatter(article_path.read_text(encoding="utf-8"))
    clean_body = strip_managed_figures(body, manifest)
    issues: list[str] = []
    expected_article = str(manifest.get("article") or "")
    actual_article = str(article_path.relative_to(PROJECT_ROOT))
    if expected_article and expected_article != actual_article:
        issues.append("配图清单登记的文章与当前文章不一致")
    for platform, label in (("wechat", "公众号："), ("toutiao", "今日头条：")):
        issues.extend(
            _validate_plan(clean_body, effective_plan(manifest, platform), manifest, label)
        )
    fingerprint = plan_fingerprint(article_path, manifest)
    confirmation = manifest.get("confirmation") or {}
    if require_confirmed:
        if confirmation.get("status") != "confirmed":
            issues.append("本地配图尚未人工确认")
        elif confirmation.get("plan_fingerprint") != fingerprint:
            issues.append("正文或配图方案在确认后发生变化，请重新确认")
    return {
        "ok": not issues,
        "issues": issues,
        "manifest_path": str(manifest_path.relative_to(PROJECT_ROOT)),
        "fingerprint": fingerprint,
    }


def confirm_figures(article_path: Path) -> dict[str, Any]:
    manifest_path, manifest = load_manifest(article_path)
    result = preflight_figures(article_path, require_confirmed=False)
    if result["issues"]:
        raise RuntimeError("；".join(result["issues"]))
    _, body, _ = split_frontmatter(article_path.read_text(encoding="utf-8"))
    now = _now()
    manifest["confirmation"] = {
        "status": "confirmed",
        "confirmed_at": now,
        "body_hash": body_hash(strip_managed_figures(body, manifest)),
        "plan_fingerprint": result["fingerprint"],
    }
    save_manifest(manifest_path, manifest)
    config = load_public_config()
    state = load_state(config)
    entry = article_state(state, article_path, create=True)
    assert entry is not None
    entry.update(
        {
            "status": "figures_confirmed",
            "figures_confirmed_at": now,
            "figure_plan_fingerprint": result["fingerprint"],
            "figure_manifest": str(manifest_path.relative_to(PROJECT_ROOT)),
        }
    )
    save_state(state, config)
    return {**result, "ok": True, "confirmed_at": now}


def editor_markdown(article_path: Path, body: str) -> str:
    try:
        _, manifest = load_manifest(article_path)
    except RuntimeError:
        return body
    result = body
    for figure in manifest["figures"]:
        path = str(figure.get("file") or "")
        if path:
            result = result.replace(f"]({path})", f"](/pd-workflow/asset/{figure['id']})")
    return result


def canonical_markdown(article_path: Path, body: str) -> str:
    try:
        _, manifest = load_manifest(article_path)
    except RuntimeError:
        return body
    result = body
    for figure in manifest["figures"]:
        result = result.replace(
            f"](/pd-workflow/asset/{figure['id']})",
            f"]({figure['file']})",
        )
    return result


def initial_plan(article_path: Path) -> list[dict[str, str]]:
    _, manifest = load_manifest(article_path)
    _, body, _ = split_frontmatter(article_path.read_text(encoding="utf-8"))
    clean_body = strip_managed_figures(body, manifest)
    headings = [item["value"] for item in article_headings(clean_body)]
    number = str(manifest.get("article_number") or "").strip()
    preferred = [
        (f"fig-{number}-03", 0),
        (f"fig-{number}-04", 1),
        (f"fig-{number}-05", 2),
        (f"fig-{number}-06", 3),
        (f"fig-{number}-07", 4),
        (f"fig-{number}-08", 5),
        (f"fig-{number}-09", 6),
        (f"fig-{number}-10", -2),
    ]
    known = {str(item.get("id")) for item in manifest["figures"]}
    plan: list[dict[str, str]] = []
    for figure_id, heading_index in preferred:
        if figure_id not in known or not headings:
            continue
        try:
            heading = headings[heading_index]
        except IndexError:
            continue
        plan.append(
            {
                "id": figure_id,
                "before_heading": heading,
                "context_after": heading_context(clean_body, heading),
            }
        )
    return plan

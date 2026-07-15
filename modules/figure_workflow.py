#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公众号配图清单、正文插入计划与编辑器本地预览映射。"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from modules.writing_workflow import (
    PROJECT_ROOT,
    atomic_write_text,
    save_snapshot,
    split_frontmatter,
)


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
    return path, manifest


def save_manifest(path: Path, manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
    atomic_write_text(
        path,
        yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False, width=1000),
    )


def article_headings(body: str) -> list[dict[str, str]]:
    headings = re.findall(r"^##\s+(.+)$", body, re.M)
    result: list[dict[str, str]] = []
    for heading in headings:
        exact = f"## {heading}"
        if heading == "一、不求“小而全”：先回答“这个地方为什么能做”":
            label = "引言之后"
        elif heading == "参考文章":
            label = "正文结尾、参考文章之前"
        elif heading == "金句集合":
            label = "参考文章之后"
        else:
            label = f"“{heading}”之前"
        result.append({"value": exact, "label": label})
    return result


def figure_by_id(manifest: dict[str, Any], figure_id: str) -> dict[str, Any]:
    for item in manifest["figures"]:
        if str(item.get("id")) == figure_id:
            return item
    raise RuntimeError(f"配图编号不存在：{figure_id}")


def strip_managed_figures(body: str, manifest: dict[str, Any]) -> str:
    cleaned = body
    for figure in manifest["figures"]:
        path = re.escape(str(figure.get("file") or ""))
        if not path:
            continue
        pattern = rf"\n*![^\n]*\({path}\)\s*\n*"
        cleaned = re.sub(pattern, "\n\n", cleaned)
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


def normalize_plan(plan: list[dict[str, Any]], manifest: dict[str, Any]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in plan:
        figure_id = str(item.get("id") or "").strip()
        heading = str(item.get("before_heading") or "").strip()
        if not figure_id or not heading or figure_id in seen:
            continue
        figure_by_id(manifest, figure_id)
        normalized.append({"id": figure_id, "before_heading": heading})
        seen.add(figure_id)
    return normalized


def apply_plan(article_path: Path, plan: list[dict[str, Any]]) -> dict[str, Any]:
    manifest_path, manifest = load_manifest(article_path)
    source = article_path.read_text(encoding="utf-8")
    frontmatter, body, metadata = split_frontmatter(source)
    clean_body = strip_managed_figures(body, manifest)
    normalized = normalize_plan(plan, manifest)
    valid_headings = {item["value"] for item in article_headings(clean_body)}
    invalid = [item["before_heading"] for item in normalized if item["before_heading"] not in valid_headings]
    if invalid:
        raise RuntimeError(f"正文中找不到插图位置：{'；'.join(invalid)}")

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

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    snapshot = save_snapshot(
        article_path,
        metadata,
        f"05-before-figure-plan-{timestamp}.md",
        source,
    )
    atomic_write_text(article_path, f"{frontmatter}\n\n{updated.rstrip()}\n")
    usage = sync_usage(article_path, updated, manifest_path=manifest_path, manifest=manifest)
    usage["before_plan_snapshot"] = str(snapshot.relative_to(PROJECT_ROOT))
    return usage


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
    positions: list[tuple[int, dict[str, Any]]] = []
    for figure in manifest["figures"]:
        path = str(figure.get("file") or "")
        position = body.find(f"]({path})")
        used = position >= 0
        figure["used_in_wechat"] = used
        figure["wechat_status"] = "selected" if used else "candidate"
        figure["article_position"] = None
        figure["article_order"] = None
        if used:
            following = body[position:].splitlines()
            next_heading = next((line for line in following if line.startswith("## ")), "正文结尾")
            figure["article_position"] = f"{next_heading}之前" if next_heading != "正文结尾" else next_heading
            positions.append((position, figure))
    for order, (_, figure) in enumerate(sorted(positions, key=lambda item: item[0]), 1):
        figure["article_order"] = order
    save_manifest(manifest_path, manifest)
    return {
        "manifest_path": str(manifest_path.relative_to(PROJECT_ROOT)),
        "used_count": len(positions),
        "figure_count": len(manifest["figures"]),
    }


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
    headings = [item["value"] for item in article_headings(body)]
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
        plan.append(
            {
                "id": figure_id,
                "before_heading": headings[heading_index],
            }
        )
    return plan

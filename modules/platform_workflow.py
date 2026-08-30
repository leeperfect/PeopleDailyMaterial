#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公众号与今日头条同步前的统一门槛。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from modules.figure_workflow import MARKDOWN_IMAGE_RE, preflight_figures
from modules.writing_workflow import article_state, load_public_config, load_state

NO_FIGURES_FINGERPRINT = "no-figures"


def publication_readiness(
    article_path: Path,
    *,
    allow_no_figures: bool = False,
) -> dict[str, Any]:
    config = load_public_config()
    state = load_state(config)
    entry = article_state(state, article_path) or {}
    issues: list[str] = []
    if not entry.get("last_pulled_at"):
        issues.append("尚未从得到大脑安全拉回二润稿")
    if not entry.get("emphasis_reviewed_at"):
        issues.append("重点加粗审查尚未通过")
    source = article_path.read_text(encoding="utf-8")
    has_inline_images = bool(MARKDOWN_IMAGE_RE.search(source))
    if allow_no_figures and not has_inline_images:
        # 为什么单独放行：热点系列等无图文章由用户明确豁免配图，
        # 用固定指纹替代配图指纹，正文变化仍由 article_hash 兜底校验。
        figure_check = {
            "ok": True,
            "issues": [],
            "fingerprint": NO_FIGURES_FINGERPRINT,
        }
    else:
        try:
            figure_check = preflight_figures(article_path, require_confirmed=True)
            issues.extend(str(issue) for issue in figure_check["issues"])
        except RuntimeError as error:
            figure_check = {"ok": False, "issues": [str(error)], "fingerprint": ""}
            issues.append(str(error))
    return {
        "ok": not issues,
        "issues": issues,
        "entry": entry,
        "figure_check": figure_check,
    }


def require_publication_ready(
    article_path: Path,
    *,
    allow_no_figures: bool = False,
) -> dict[str, Any]:
    result = publication_readiness(article_path, allow_no_figures=allow_no_figures)
    if result["issues"]:
        details = "\n".join(f"- {issue}" for issue in result["issues"])
        raise RuntimeError(f"双平台同步前检查未通过：\n{details}")
    return result

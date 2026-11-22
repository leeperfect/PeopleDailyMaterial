#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公众号与今日头条同步前的统一门槛。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from modules.figure_workflow import MARKDOWN_IMAGE_RE, preflight_figures
from modules.writing_workflow import (
    ExternalDraftMode,
    article_state,
    body_hash,
    file_sha256,
    load_public_config,
    load_state,
    split_frontmatter,
)

NO_FIGURES_FINGERPRINT = "no-figures"


def _check_polish_readiness(entry: dict[str, Any]) -> tuple[bool, str]:
    """检查二润完成状态：得到大脑拉回 或 外部成稿登记。

    Returns:
        (通过, 阻断原因)。通过时原因为空。
    """
    # 路径 1：标准得到大脑往返
    if entry.get("last_pulled_at"):
        return True, ""

    # 路径 2：外部成稿登记（免二润入口）
    external = entry.get("external_draft_registration")
    if isinstance(external, dict) and external.get("registered_at"):
        mode = external.get("mode", "")
        if mode in ExternalDraftMode.VALID_MODES:
            return True, ""
        return False, f"外部成稿登记模式不正确：{mode}"

    return False, "尚未从得到大脑安全拉回二润稿，也没有外部成稿登记"


def _verify_external_registration_integrity(
    article_path: Path,
    entry: dict[str, Any],
    target_platform: str,
) -> list[str]:
    """【安全检查】验证外部成稿登记在消费时的完整性。

    在 sync 入口重新校验，防止登记后修改内容或跨平台滥用。

    Args:
        article_path: 当前文章路径
        entry: 文章工作流状态
        target_platform: 本次同步的目标平台

    Returns:
        校验问题列表，空列表表示通过。
    """
    issues: list[str] = []
    external = entry.get("external_draft_registration")
    if not isinstance(external, dict) or not external.get("registered_at"):
        return issues  # 不是外部登记，跳过此检查

    # 【安全检查 1】：登记后正文是否变化
    registered_body_hash = external.get("source_body_hash")
    if external.get("candidate_imported"):
        # 场景 B：候选导入后，使用候选的 body hash
        registered_body_hash = external.get("candidate_body_hash")

    if registered_body_hash:
        source = article_path.read_text(encoding="utf-8")
        _, current_body, _ = split_frontmatter(source)
        current_body_hash = body_hash(current_body)
        if current_body_hash != registered_body_hash:
            issues.append(
                "外部成稿登记后正文已被修改，必须重新登记或使用标准二润流程"
            )

    # 【安全检查 2】：平台绑定
    registered_platform = external.get("target_platform", "")
    if registered_platform == "wechat_only":
        if target_platform in ("toutiao", "both"):
            issues.append(
                f"外部成稿仅授权公众号（wechat_only），不能同步到今日头条"
            )
    elif registered_platform == "toutiao":
        if target_platform in ("wechat", "both"):
            issues.append(
                f"外部成稿仅授权今日头条，不能同步到公众号"
            )
    # "wechat" 和空值允许双平台

    return issues


def publication_readiness(
    article_path: Path,
    *,
    allow_no_figures: bool = False,
    target_platform: str = "wechat",
) -> dict[str, Any]:
    config = load_public_config()
    state = load_state(config)
    entry = article_state(state, article_path) or {}
    issues: list[str] = []

    # 二润完成检查：得到大脑拉回 或 外部成稿登记
    polish_ok, polish_issue = _check_polish_readiness(entry)
    if not polish_ok:
        issues.append(polish_issue)

    # 【安全检查】外部成稿登记的消费时完整性校验
    integrity_issues = _verify_external_registration_integrity(
        article_path, entry, target_platform
    )
    issues.extend(integrity_issues)

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
    target_platform: str = "wechat",
) -> dict[str, Any]:
    result = publication_readiness(
        article_path,
        allow_no_figures=allow_no_figures,
        target_platform=target_platform,
    )
    if result["issues"]:
        details = "\n".join(f"- {issue}" for issue in result["issues"])
        raise RuntimeError(f"双平台同步前检查未通过：\n{details}")
    return result

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公众号写作工作流的共享规则与本地状态管理。"""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_CONFIG_PATH = PROJECT_ROOT / "writing_workflow.json"


def load_public_config() -> dict[str, Any]:
    with PUBLIC_CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def project_path(value: str | os.PathLike[str]) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def split_frontmatter(markdown_text: str) -> tuple[str, str, dict[str, Any]]:
    """返回带分隔符的 YAML、正文和解析后的 YAML。"""
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n)?", markdown_text, re.S)
    if not match:
        return "", markdown_text, {}
    raw_yaml = match.group(1)
    parsed = yaml.safe_load(raw_yaml) or {}
    if not isinstance(parsed, dict):
        parsed = {}
    frontmatter = f"---\n{raw_yaml}\n---"
    return frontmatter, markdown_text[match.end():].lstrip("\r\n"), parsed


def join_frontmatter(frontmatter: str, body: str) -> str:
    prefix = f"{frontmatter}\n\n" if frontmatter else ""
    return prefix + body.rstrip() + "\n"


def body_hash(body: str) -> str:
    normalized = body.replace("\r\n", "\n").strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def article_key(article_path: Path) -> str:
    relative = article_path.resolve().relative_to(PROJECT_ROOT)
    return str(relative)


def workflow_id(article_path: Path) -> str:
    return hashlib.sha256(article_key(article_path).encode("utf-8")).hexdigest()[:12]


def state_path(config: dict[str, Any] | None = None) -> Path:
    config = config or load_public_config()
    return project_path(config["workflow_state"])


def load_state(config: dict[str, Any] | None = None) -> dict[str, Any]:
    path = state_path(config)
    if not path.exists():
        return {"schema_version": 1, "articles": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"schema_version": 1, "articles": {}}
    data.setdefault("schema_version", 1)
    data.setdefault("articles", {})
    return data


def save_state(state: dict[str, Any], config: dict[str, Any] | None = None) -> None:
    atomic_write_json(state_path(config), state)


def article_state(
    state: dict[str, Any],
    article_path: Path,
    *,
    create: bool = False,
) -> dict[str, Any] | None:
    key = article_key(article_path)
    if create:
        return state.setdefault("articles", {}).setdefault(
            key,
            {
                "workflow_id": workflow_id(article_path),
                "article_path": key,
                "created_at": datetime.now().isoformat(timespec="seconds"),
            },
        )
    return state.get("articles", {}).get(key)


def detect_series(article_path: Path, metadata: dict[str, Any]) -> str:
    candidates = " ".join(
        str(metadata.get(key, ""))
        for key in ("series", "series_no", "topic", "title")
    )
    path_text = str(article_path)
    if "热点系列" in path_text or "热点系列" in candidates or metadata.get("series_no", "").startswith("热点"):
        return "hotspot"
    if "人民日报系列" in path_text or "人民日报" in candidates:
        return "people_daily"
    raise ValueError("无法判断文章属于“人民日报系列”还是“热点系列”")


def cover_for_article(
    article_path: Path,
    metadata: dict[str, Any],
    config: dict[str, Any],
) -> Path:
    series = detect_series(article_path, metadata)
    cover = project_path(config["covers"][series])
    if not cover.exists():
        raise FileNotFoundError(f"固定封面不存在：{cover}")
    return cover


def effective_layout(
    metadata: dict[str, Any],
    config: dict[str, Any] | None = None,
    article_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = config or load_public_config()
    layout = dict(config["doocs"]["default_layout"])
    override = metadata.get("wechat_layout") or {}
    if isinstance(override, dict):
        for key, value in override.items():
            if key in layout:
                layout[key] = value
    if isinstance(article_override, dict):
        for key, value in article_override.items():
            if key in layout:
                layout[key] = value
    return layout


def title_from_article(article_path: Path, metadata: dict[str, Any], body: str) -> str:
    for key in ("wechat_title", "title"):
        value = metadata.get(key)
        if value:
            return str(value).strip()
    match = re.search(r"^#\s+(.+)$", body, re.M)
    if match:
        return match.group(1).strip()
    name = article_path.stem.replace("【R】", "")
    return re.sub(r"^(?:热点)?\d+-", "", name).strip()


def digest_from_article(metadata: dict[str, Any], body: str, limit: int = 120) -> str:
    if metadata.get("digest"):
        return str(metadata["digest"]).strip()[:limit]
    cleaned = re.sub(r"```.*?```", "", body, flags=re.S)
    for block in re.split(r"\n\s*\n", cleaned):
        text = block.strip()
        if not text or text.startswith(("#", "-", "*", ">", "|", "---")):
            continue
        text = re.sub(r"!\[[^\]]*]\([^)]*\)", "", text)
        text = re.sub(r"\[([^\]]+)]\([^)]*\)", r"\1", text)
        text = re.sub(r"[*_`#>]", "", text).strip()
        if text:
            return text[:limit]
    return ""


def snapshot_directory(article_path: Path, metadata: dict[str, Any]) -> Path:
    article_date = str(metadata.get("date") or date.today().isoformat())
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", article_date):
        article_date = date.today().isoformat()
    return (
        PROJECT_ROOT
        / "data"
        / "analysis"
        / article_date
        / "writing-workflow"
        / workflow_id(article_path)
    )


def save_snapshot(
    article_path: Path,
    metadata: dict[str, Any],
    filename: str,
    content: str,
) -> Path:
    path = snapshot_directory(article_path, metadata) / filename
    atomic_write_text(path, content)
    return path


def structural_issues(old_body: str, new_body: str) -> list[str]:
    issues: list[str] = []
    old_length = len(old_body.strip())
    new_length = len(new_body.strip())
    if old_length and new_length < old_length * 0.65:
        issues.append(
            f"二润稿仅为原正文的 {new_length / old_length:.0%}，疑似大段内容丢失"
        )
    if re.search(r"^#\s+", old_body, re.M) and not re.search(r"^#\s+", new_body, re.M):
        issues.append("二润稿丢失一级标题")
    reference_pattern = r"^##\s*(?:参考文章|参考资料|资料来源)"
    if re.search(reference_pattern, old_body, re.M) and not re.search(reference_pattern, new_body, re.M):
        issues.append("二润稿丢失参考文章/资料来源栏目")
    old_urls = set(re.findall(r"https?://[^\s)>]+", old_body))
    new_urls = set(re.findall(r"https?://[^\s)>]+", new_body))
    missing_urls = sorted(old_urls - new_urls)
    if missing_urls:
        issues.append(f"二润稿丢失 {len(missing_urls)} 个来源链接")
    return issues


def unified_diff(old_body: str, new_body: str) -> str:
    lines = difflib.unified_diff(
        old_body.splitlines(),
        new_body.splitlines(),
        fromfile="before-getnote",
        tofile="after-getnote",
        lineterm="",
    )
    return "\n".join(lines) + "\n"


def load_dotenv_values() -> dict[str, str]:
    """读取项目 .env；不会输出任何值。"""
    path = PROJECT_ROOT / ".env"
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values

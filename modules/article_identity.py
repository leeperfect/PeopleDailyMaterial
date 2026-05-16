#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文章身份与内容指纹工具。

本模块只负责生成稳定 ID 和 hash，不关心文章保存在哪里。这样目录
结构调整时，Notion、SQLite、Markdown 之间仍然能靠同一个 article_id 对齐。
"""

import hashlib
import re
from typing import Dict, Optional


PEOPLE_DAILY_SOURCE = "people_daily"


def normalize_date(date_str: str) -> str:
    """把常见日期格式规范为 YYYY-MM-DD。无法识别时原样返回。"""
    if not date_str:
        return ""

    date_str = str(date_str).strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return date_str
    if re.match(r"^\d{8}$", date_str):
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    return date_str


def compact_date(date_str: str) -> str:
    """返回 YYYYMMDD，用于 ID。"""
    normalized = normalize_date(date_str)
    return normalized.replace("-", "") if normalized else "undated"


def extract_people_daily_content_id(url: str) -> Optional[str]:
    """从人民日报 URL 中提取 content id。"""
    if not url:
        return None
    match = re.search(r"content_(\d+)\.html", url)
    if match:
        return match.group(1)
    return None


def stable_short_hash(*parts: str, length: int = 12) -> str:
    """基于多个文本片段生成短 hash。"""
    text = "\n".join(str(part or "") for part in parts)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]


def build_article_id(article: Dict) -> str:
    """生成稳定 article_id。

    优先使用人民日报 URL 中的 content id；如果没有 URL 或 URL 不规范，
    再退回到 source/date/title/content 的短 hash。
    """
    source = article.get("source") or PEOPLE_DAILY_SOURCE
    date_key = compact_date(article.get("date", ""))
    url = article.get("url") or article.get("source_url") or ""

    content_id = extract_people_daily_content_id(url)
    if source == PEOPLE_DAILY_SOURCE and content_id:
        return f"{source}_{date_key}_{content_id}"

    fallback_hash = stable_short_hash(
        source,
        article.get("date", ""),
        article.get("title", ""),
        url,
        article.get("content", ""),
    )
    return f"{source}_{date_key}_{fallback_hash}"


def content_hash(content: str) -> str:
    """生成正文内容指纹。"""
    normalized = re.sub(r"\s+", "\n", (content or "").strip())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

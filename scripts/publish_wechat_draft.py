#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""使用 doocs/md 的同一份 HTML 创建公众号草稿；绝不自动群发。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from modules.wechat_api import (
    WechatApiError,
    add_draft,
    draft_count,
    file_hash,
    upload_content_image,
    upload_permanent_image,
    upload_remote_content_image,
)
from modules.writing_workflow import (
    article_state,
    body_hash,
    cover_for_article,
    detect_series,
    digest_from_article,
    load_public_config,
    load_state,
    project_path,
    save_state,
    split_frontmatter,
    title_from_article,
)
from render_wechat_html import render_article


def local_image_path(source: str, article_path: Path) -> Path | None:
    parsed = urlparse(source)
    if parsed.scheme in ("http", "https", "data"):
        return None
    raw_path = unquote(parsed.path)
    candidate = Path(raw_path).expanduser()
    candidates = (
        [candidate]
        if candidate.is_absolute()
        else [article_path.parent / candidate, PROJECT_ROOT / candidate]
    )
    for path in candidates:
        if path.exists() and path.is_file():
            return path.resolve()
    raise RuntimeError(f"正文图片不存在：{source}")


def upload_body_images(fragment: str, article_path: Path) -> str:
    soup = BeautifulSoup(fragment, "html.parser")
    for image in soup.find_all("img"):
        source = str(image.get("src") or "").strip()
        if not source:
            continue
        parsed = urlparse(source)
        if parsed.scheme in ("http", "https"):
            image["src"] = upload_remote_content_image(source)
            continue
        if parsed.scheme == "data":
            raise RuntimeError("正文包含 data: 内嵌图片，请先保存为本地图片文件")
        local = local_image_path(source, article_path)
        if local:
            image["src"] = upload_content_image(local)
    return str(soup)


def cover_media_id(
    article_path: Path,
    metadata: dict,
    config: dict,
    state: dict,
) -> tuple[str, Path]:
    cover = cover_for_article(article_path, metadata, config)
    digest = file_hash(cover)
    cache = state.setdefault("wechat_cover_media", {})
    cached = cache.get(digest)
    if cached and cached.get("media_id"):
        return str(cached["media_id"]), cover
    media_id = upload_permanent_image(cover)
    cache[digest] = {
        "media_id": media_id,
        "path": str(cover.relative_to(PROJECT_ROOT)),
        "uploaded_at": datetime.now().isoformat(timespec="seconds"),
    }
    return media_id, cover


def publication_fingerprint(article_hash: str, layout: dict) -> str:
    payload = article_hash + json.dumps(layout, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def publish(article: str, *, dry_run: bool = False, force: bool = False) -> str | None:
    config = load_public_config()
    article_path = project_path(article).resolve()
    if not article_path.exists():
        raise RuntimeError(f"文章不存在：{article_path}")
    source = article_path.read_text(encoding="utf-8")
    _, body, metadata = split_frontmatter(source)
    title = title_from_article(article_path, metadata, body)
    if len(title) > 64:
        raise RuntimeError(
            f"公众号标题共 {len(title)} 字，超过 64 字；请先设置精简的 wechat_title"
        )
    digest = digest_from_article(metadata, body)
    rendered = render_article(str(article_path), fragment_only=True)
    series = detect_series(article_path, metadata)
    cover = cover_for_article(article_path, metadata, config)
    fingerprint = publication_fingerprint(rendered["article_hash"], rendered["layout"])

    state = load_state(config)
    entry = article_state(state, article_path, create=True)
    assert entry is not None
    previous = entry.get("wechat_draft") or {}
    if not force and previous.get("fingerprint") == fingerprint:
        raise RuntimeError(
            "相同正文和排版已经创建过草稿，已停止重复同步。\n"
            f"已有 media_id：{previous.get('media_id', '未知')}"
        )

    if dry_run:
        print("草稿同步预检（未调用公众号接口）")
        print(f"标题：{title}")
        print(f"作者：{config['author']}")
        print(f"摘要：{digest}")
        print(f"系列：{series}")
        print(f"固定封面：{cover}")
        print(f"主题：{rendered['layout']['theme']}")
        print(f"主题色：{rendered['layout']['primaryColor']}")
        print(f"HTML 长度：{len(rendered['html'])}")
        return None

    thumb_media_id, cover_path = cover_media_id(
        article_path,
        metadata,
        config,
        state,
    )
    content = upload_body_images(rendered["html"], article_path)
    media_id = add_draft(
        {
            "title": title,
            "author": config["author"],
            "digest": digest,
            "content": content,
            "content_source_url": str(metadata.get("content_source_url", "")),
            "thumb_media_id": thumb_media_id,
            "need_open_comment": 0,
            "only_fans_can_comment": 0,
        }
    )
    entry["wechat_draft"] = {
        "media_id": media_id,
        "fingerprint": fingerprint,
        "article_hash": body_hash(body),
        "layout": rendered["layout"],
        "cover": str(cover_path.relative_to(PROJECT_ROOT)),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "status": "draft_only",
    }
    entry["status"] = "wechat_draft_created"
    save_state(state, config)
    print("公众号草稿创建成功；没有执行群发。")
    print(f"media_id：{media_id}")
    return media_id


def main() -> int:
    parser = argparse.ArgumentParser(description="同步到公众号草稿箱")
    parser.add_argument("article", nargs="?")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="明确允许重复创建草稿")
    parser.add_argument("--preflight", action="store_true", help="只读检查草稿箱权限")
    # 保留旧参数但不再把 Get笔记拉回和发布绑成不可审查的一步。
    parser.add_argument("--pull-from-getnote", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--title", help=argparse.SUPPRESS)
    parser.add_argument("--thumb-media-id", help=argparse.SUPPRESS)
    parser.add_argument("--author", help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        if args.preflight:
            print(f"草稿箱权限正常；当前草稿数量：{draft_count()}")
            return 0
        if not args.article:
            parser.error("请提供文章路径")
        if args.pull_from_getnote:
            raise RuntimeError("请先单独执行“拉回”并检查差异，再同步草稿箱")
        publish(args.article, dry_run=args.dry_run, force=args.force)
    except (RuntimeError, WechatApiError) as error:
        print(str(error), file=sys.stderr)
        if isinstance(error, WechatApiError) and error.code == 48001:
            print(
                "当前账号无草稿接口权限；请改用 Codex 内置浏览器代填，"
                "或打开只读预览的一键复制按钮。",
                file=sys.stderr,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

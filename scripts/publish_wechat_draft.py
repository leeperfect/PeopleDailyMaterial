#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""使用已校验 HTML 创建公众号草稿；双平台流程固定采用 gzh-design 红白色系。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
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
    get_draft,
    update_draft,
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
from modules.platform_workflow import require_publication_ready


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


def publication_fingerprint(
    article_hash: str,
    layout: dict,
    figure_fingerprint: str = "",
) -> str:
    payload = (
        article_hash
        + json.dumps(layout, ensure_ascii=False, sort_keys=True)
        + figure_fingerprint
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def truncate_utf8(text: str, max_bytes: int) -> str:
    result: list[str] = []
    size = 0
    for character in text:
        character_size = len(character.encode("utf-8"))
        if size + character_size > max_bytes:
            break
        result.append(character)
        size += character_size
    return "".join(result)


def validated_title(metadata: dict, body: str, article_path: Path) -> str:
    title = title_from_article(article_path, metadata, body)
    title_bytes = len(title.encode("utf-8"))
    if title_bytes > 32:
        raise RuntimeError(
            f"公众号标题共 {len(title)} 个字符、占 {title_bytes} 字节，"
            "超过接口的 32 字节限制；请先设置精简的 wechat_title"
        )
    return title


def draft_article_payload(
    *,
    title: str,
    author: str,
    digest: str,
    content: str,
    metadata: dict,
    thumb_media_id: str,
) -> dict:
    return {
        "title": title,
        "author": author,
        "digest": digest,
        "content": content,
        "content_source_url": str(metadata.get("content_source_url", "")),
        "thumb_media_id": thumb_media_id,
        "need_open_comment": 1,
        "only_fans_can_comment": 0,
    }


def load_gzh_design_html(html_path: str, article_path: Path, body: str) -> dict:
    path = project_path(html_path).resolve()
    if not path.exists() or path.suffix.lower() != ".html":
        raise RuntimeError(f"红白色系公众号 HTML 不存在或格式不正确：{path}")
    skill_root = Path.home() / ".codex" / "skills" / "gzh-design"
    component_lint = skill_root / "scripts" / "component_lint.py"
    validator = skill_root / "scripts" / "validate_gzh_html.py"
    theme = skill_root / "references" / "theme-red-white.md"
    for required in (component_lint, validator, theme):
        if not required.exists():
            raise RuntimeError(
                "gzh-design Skill 安装不完整，请重新安装后再同步公众号草稿"
            )
    lint = subprocess.run(
        [sys.executable, str(component_lint), str(skill_root)],
        capture_output=True,
        text=True,
        check=False,
    )
    if lint.returncode != 0:
        raise RuntimeError(f"gzh-design 组件库校验失败：\n{lint.stdout}{lint.stderr}")
    validation = subprocess.run(
        [sys.executable, str(validator), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    report = f"{validation.stdout}{validation.stderr}"
    if validation.returncode != 0 or "WARNING" in report:
        raise RuntimeError(
            "红白色系公众号 HTML 未通过零错误、零警告校验：\n" + report
        )
    fragment = path.read_text(encoding="utf-8").strip()
    if not fragment.startswith("<section") or "<html" in fragment.lower():
        raise RuntimeError("公众号 HTML 必须是从全局 <section> 开始的纯正文片段")
    if "#DC2626" not in fragment or "#FECACA" not in fragment:
        raise RuntimeError("公众号 HTML 未检测到“红白色系”的固定主色与标记色")
    soup = BeautifulSoup(fragment, "html.parser")
    markdown_images = re.findall(r"!\[[^]]*\]\(([^)]+)\)", body)
    html_images = [str(image.get("src") or "") for image in soup.find_all("img")]
    if markdown_images != html_images:
        raise RuntimeError(
            "红白色系 HTML 的图片数量、顺序或路径与 Markdown 不一致："
            f"Markdown {len(markdown_images)} 张，HTML {len(html_images)} 张"
        )
    plain_text = soup.get_text(" ", strip=True)
    missing_headings = [
        heading
        for heading in re.findall(r"^#{2,3}\s+(.+?)\s*$", body, re.M)
        if re.sub(r"[*_`]+", "", heading).strip() not in plain_text
    ]
    if missing_headings:
        raise RuntimeError(
            "红白色系 HTML 遗漏章节标题：" + "、".join(missing_headings[:5])
        )
    return {
        "article_hash": body_hash(body),
        "layout": {
            "engine": "gzh-design",
            "theme": "红白色系",
            "theme_id": "red-white",
            "primaryColor": "#DC2626",
            "html_sha256": hashlib.sha256(fragment.encode("utf-8")).hexdigest(),
        },
        "html": fragment,
        "html_path": str(path),
    }


def publish(
    article: str,
    *,
    dry_run: bool = False,
    force: bool = False,
    wechat_html: str | None = None,
) -> str | None:
    config = load_public_config()
    article_path = project_path(article).resolve()
    if not article_path.exists():
        raise RuntimeError(f"文章不存在：{article_path}")
    readiness = require_publication_ready(article_path)
    source = article_path.read_text(encoding="utf-8")
    _, body, metadata = split_frontmatter(source)
    title = validated_title(metadata, body, article_path)
    digest = truncate_utf8(digest_from_article(metadata, body), 120)
    if not wechat_html:
        raise RuntimeError(
            "公众号同步必须先调用 gzh-design Skill 生成“红白色系”HTML，"
            "并通过 --wechat-html 传入"
        )
    rendered = load_gzh_design_html(wechat_html, article_path, body)
    series = detect_series(article_path, metadata)
    cover = cover_for_article(article_path, metadata, config)
    fingerprint = publication_fingerprint(
        rendered["article_hash"],
        rendered["layout"],
        str(readiness["figure_check"]["fingerprint"]),
    )

    state = load_state(config)
    entry = article_state(state, article_path, create=True)
    assert entry is not None
    previous = entry.get("wechat_draft") or {}
    if not force and previous.get("fingerprint") == fingerprint:
        previous_media_id = str(previous.get("media_id") or "")
        try:
            if previous_media_id:
                get_draft(previous_media_id)
        except WechatApiError as error:
            if error.code != 40007:
                raise
        else:
            raise RuntimeError(
                "相同正文和排版已经创建过草稿，已停止重复同步。\n"
                f"已有 media_id：{previous_media_id or '未知'}"
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
        draft_article_payload(
            title=title,
            author=config["author"],
            digest=digest,
            content=content,
            metadata=metadata,
            thumb_media_id=thumb_media_id,
        )
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


def replace_draft(article: str, media_id: str, *, wechat_html: str | None = None) -> str:
    config = load_public_config()
    article_path = project_path(article).resolve()
    if not article_path.exists():
        raise RuntimeError(f"文章不存在：{article_path}")
    readiness = require_publication_ready(article_path)
    source = article_path.read_text(encoding="utf-8")
    _, body, metadata = split_frontmatter(source)
    title = validated_title(metadata, body, article_path)
    digest = truncate_utf8(digest_from_article(metadata, body), 120)
    if not wechat_html:
        raise RuntimeError(
            "公众号同步必须先调用 gzh-design Skill 生成“红白色系”HTML，"
            "并通过 --wechat-html 传入"
        )
    rendered = load_gzh_design_html(wechat_html, article_path, body)
    fingerprint = publication_fingerprint(
        rendered["article_hash"],
        rendered["layout"],
        str(readiness["figure_check"]["fingerprint"]),
    )

    state = load_state(config)
    entry = article_state(state, article_path, create=True)
    assert entry is not None
    thumb_media_id, cover_path = cover_media_id(
        article_path,
        metadata,
        config,
        state,
    )
    content = upload_body_images(rendered["html"], article_path)
    update_draft(
        media_id,
        draft_article_payload(
            title=title,
            author=config["author"],
            digest=digest,
            content=content,
            metadata=metadata,
            thumb_media_id=thumb_media_id,
        ),
    )

    now = datetime.now().isoformat(timespec="seconds")
    draft_record = dict(entry.get("wechat_draft") or {})
    draft_record.update(
        {
            "media_id": media_id,
            "fingerprint": fingerprint,
            "article_hash": body_hash(body),
            "layout": rendered["layout"],
            "cover": str(cover_path.relative_to(PROJECT_ROOT)),
            "updated_at": now,
            "status": "draft_only",
        }
    )
    draft_record.setdefault("created_at", now)
    entry.update(
        {
            "wechat_draft": draft_record,
            "wechat_draft_media_id": media_id,
            "wechat_draft_updated_at": now,
            "status": "wechat_draft_created",
        }
    )
    save_state(state, config)
    print("公众号草稿已原位更新；没有执行群发。")
    print(f"media_id：{media_id}")
    return media_id


def main() -> int:
    parser = argparse.ArgumentParser(description="同步到公众号草稿箱")
    parser.add_argument("article", nargs="?")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="明确允许重复创建草稿")
    parser.add_argument(
        "--wechat-html",
        help="由 gzh-design 红白色系生成并通过校验的公众号正文 HTML",
    )
    parser.add_argument("--preflight", action="store_true", help="只读检查草稿箱权限")
    parser.add_argument(
        "--replace-media-id",
        help="原位更新指定草稿，不新建第二篇",
    )
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
        if args.replace_media_id:
            replace_draft(args.article, args.replace_media_id, wechat_html=args.wechat_html)
        else:
            publish(
                args.article,
                dry_run=args.dry_run,
                force=args.force,
                wechat_html=args.wechat_html,
            )
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

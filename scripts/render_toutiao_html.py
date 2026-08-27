#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从共用文章与头条配图方案生成今日头条富文本和浏览器交接包。"""

from __future__ import annotations

import argparse
import base64
import html
import json
import mimetypes
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup, NavigableString

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from modules.figure_workflow import (  # noqa: E402
    body_for_platform,
    effective_plan,
    figure_by_id,
    load_manifest,
    plan_fingerprint,
)
from modules.writing_workflow import (  # noqa: E402
    atomic_write_json,
    atomic_write_text,
    body_hash,
    load_public_config,
    load_state,
    project_path,
    split_frontmatter,
    title_from_article,
    workflow_id,
)
from render_wechat_html import render_with_doocs  # noqa: E402


ALLOWED_TAGS = {
    "p", "h1", "h2", "h3", "strong", "em", "blockquote", "ul", "ol", "li",
    "img", "a", "br", "hr", "pre", "code",
}


def toutiao_title(article_path: Path, metadata: dict[str, Any], body: str) -> str:
    value = metadata.get("toutiao_title")
    if not value:
        match = re.search(r"^#\s+(.+)$", body, re.M)
        value = match.group(1).strip() if match else metadata.get("title")
    if not value:
        neutral_metadata = {key: item for key, item in metadata.items() if key != "wechat_title"}
        value = title_from_article(article_path, neutral_metadata, body)
    title = str(value).strip()
    return re.sub(r"^(?:热点)?\d+-?【R】\s*[｜|]?\s*", "", title).strip()


def neutral_layout(config: dict[str, Any]) -> dict[str, Any]:
    layout = dict(config["doocs"]["default_layout"])
    layout.update(
        {
            "theme": "simple",
            "customCSS": "",
            "isUseIndent": False,
            "isUseJustify": False,
            "citeStatus": False,
        }
    )
    return layout


def sanitize_fragment(fragment: str) -> str:
    soup = BeautifulSoup(fragment, "html.parser")
    # doocs/md 会为 Markdown 图片生成图注；头条正文上传原图时不重复显示文件说明。
    for caption in soup.find_all("figcaption"):
        caption.decompose()
    # 公众号成稿中的“金句集合”使用编号 text 代码块，doocs/md 会把它输出为
    # pre/code。头条编辑器会再给代码块显示行号，形成“1. 1.”的双编号。
    # 只有当代码块的每一行都明确带编号时，才转换为真正的有序列表；
    # 普通代码示例继续保留 pre/code，避免误伤。
    for pre in list(soup.find_all("pre")):
        code = pre.find("code")
        if code is None:
            continue
        lines = [line.strip() for line in code.get_text("\n").splitlines() if line.strip()]
        numbered = [re.match(r"^\d+\s*[.、]\s*(.+)$", line) for line in lines]
        if not lines or not all(numbered):
            continue
        ordered = soup.new_tag("ol")
        for match in numbered:
            item = soup.new_tag("li")
            item.string = match.group(1).strip()
            ordered.append(item)
        pre.replace_with(ordered)
    # 图片紧跟引用段落时，doocs/md 偶尔会把图片包进 blockquote。
    # 头条会丢弃引用框内部的图片，因此把它们移到引用框之后，位置不变。
    for quote in list(soup.find_all("blockquote")):
        anchor = quote
        for image in list(quote.find_all("img")):
            previous = image.previous_sibling
            if getattr(previous, "name", None) == "br":
                previous.extract()
            image.extract()
            anchor.insert_after(image)
            anchor = image
    # doocs/md 的复制稿会把列表符号同时写进 li 文本；头条再渲染一次列表标记后，
    # 会出现“1. 1.”或“双圆点”。这里只移除 li 开头的冗余文本标记。
    for list_node in soup.find_all(["ol", "ul"]):
        pattern = r"^\s*\d+\s*[.、]\s*" if list_node.name == "ol" else r"^\s*[•●▪◦]\s*"
        for item in list_node.find_all("li", recursive=False):
            for text_node in item.descendants:
                if not isinstance(text_node, NavigableString) or not str(text_node).strip():
                    continue
                original = str(text_node)
                cleaned = re.sub(pattern, "", original, count=1)
                if cleaned != original:
                    text_node.replace_with(cleaned)
                break
    # 少数相邻段落在 doocs/md 输出中仍会残留 Markdown 加粗标记；
    # 头条不会再次解析 Markdown，因此在纯文本节点中补转为 strong。
    for text_node in list(soup.find_all(string=re.compile(r"\*\*[^*\n]+\*\*"))):
        if text_node.parent and text_node.parent.name in {"code", "pre"}:
            continue
        parts = re.split(r"(\*\*[^*\n]+\*\*)", str(text_node))
        replacements = []
        for part in parts:
            if not part:
                continue
            if part.startswith("**") and part.endswith("**"):
                strong = soup.new_tag("strong")
                strong.string = part[2:-2]
                replacements.append(strong)
            else:
                replacements.append(NavigableString(part))
        text_node.replace_with(*replacements)
    for tag in list(soup.find_all(True)):
        if tag.name not in ALLOWED_TAGS:
            tag.unwrap()
            continue
        allowed = {"href", "title"} if tag.name == "a" else ({"src", "alt"} if tag.name == "img" else set())
        for attribute in list(tag.attrs):
            if attribute not in allowed:
                del tag.attrs[attribute]
        if tag.name == "a":
            href = str(tag.get("href") or "")
            if not re.match(r"^https?://", href):
                tag.unwrap()
    return "".join(str(node) for node in soup.contents).strip()


def fragment_without_lead_title(fragment: str) -> str:
    """今日头条已有独立标题输入框，正文不重复保留首个 H1。"""
    soup = BeautifulSoup(fragment, "html.parser")
    first = next((node for node in soup.contents if getattr(node, "name", None)), None)
    if first is not None and first.name == "h1":
        first.decompose()
    return "".join(str(node) for node in soup.contents).strip()


def fragment_without_images(fragment: str) -> str:
    soup = BeautifulSoup(fragment, "html.parser")
    for image in soup.find_all("img"):
        image.decompose()
    return "".join(str(node) for node in soup.contents).strip()


def preview_images_as_data(fragment: str) -> str:
    soup = BeautifulSoup(fragment, "html.parser")
    for image in soup.find_all("img"):
        source = str(image.get("src") or "")
        parsed = urlparse(source)
        if parsed.scheme in ("http", "https", "data"):
            continue
        candidate = project_path(unquote(parsed.path)).resolve()
        if not candidate.exists() or not candidate.is_file():
            continue
        mime = mimetypes.guess_type(candidate.name)[0] or "image/png"
        encoded = base64.b64encode(candidate.read_bytes()).decode("ascii")
        image["src"] = f"data:{mime};base64,{encoded}"
    return "".join(str(node) for node in soup.contents).strip()


def preview_document(title: str, fragment: str, fingerprint: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><style>
body{{margin:0;background:#f2f4f7;color:#222;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}}
.toolbar{{position:sticky;top:0;display:flex;gap:14px;align-items:center;padding:12px 18px;background:#1667ff;color:white}}
.toolbar strong{{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}.toolbar button{{border:0;border-radius:8px;padding:9px 14px;cursor:pointer}}
article{{box-sizing:border-box;width:min(100%,760px);margin:18px auto;padding:30px 28px 60px;background:white;line-height:1.8}}
article img{{display:block;max-width:100%;height:auto;margin:22px auto}}article h1{{font-size:28px}}article h2{{font-size:22px;margin-top:32px}}
.meta{{font-size:12px;opacity:.8}}@media(max-width:780px){{article{{margin:0;padding:22px 18px 48px}}}}
</style></head><body><div class="toolbar"><strong>今日头条预览｜{html.escape(title)}</strong>
<span class="meta">配图指纹 {fingerprint[:10]}</span><button id="copy">复制头条富文本</button></div>
<article id="article">{fragment}</article><script>
document.getElementById('copy').addEventListener('click',async()=>{{const article=document.getElementById('article');
try{{await navigator.clipboard.write([new ClipboardItem({{'text/html':new Blob([article.innerHTML],{{type:'text/html'}}),'text/plain':new Blob([article.innerText],{{type:'text/plain'}})}})]);document.getElementById('copy').textContent='已复制';}}
catch(_){{const range=document.createRange();range.selectNodeContents(article);const selection=window.getSelection();selection.removeAllRanges();selection.addRange(range);}}}});
</script></body></html>"""


def render_toutiao(article: str) -> dict[str, Any]:
    config = load_public_config()
    article_path = project_path(article).resolve()
    if not article_path.exists():
        raise RuntimeError(f"文章不存在：{article_path}")
    source = article_path.read_text(encoding="utf-8")
    _, original_body, metadata = split_frontmatter(source)
    body = body_for_platform(article_path, "toutiao")
    rendered = render_with_doocs(body, neutral_layout(config), config)
    fragment = fragment_without_lead_title(sanitize_fragment(str(rendered["html"])))
    title = toutiao_title(article_path, metadata, original_body)
    manifest_path, manifest = load_manifest(article_path)
    plan = effective_plan(manifest, "toutiao")
    assets: list[dict[str, Any]] = []
    for order, item in enumerate(plan, 1):
        figure = figure_by_id(manifest, str(item["id"]))
        local_path = project_path(str(figure["file"])).resolve()
        assets.append(
            {
                "order": order,
                "id": figure["id"],
                "path": str(local_path),
                "before_heading": item["before_heading"],
                "anchor_before": item.get("anchor_before"),
                "anchor_after": item.get("anchor_after"),
                "inline_marker": item.get("inline_marker"),
                "sha256": figure.get("sha256"),
            }
        )
    fingerprint = plan_fingerprint(article_path, manifest)
    output_dir = Path(config["preview_root"]) / workflow_id(article_path) / "toutiao"
    output_dir.mkdir(parents=True, exist_ok=True)
    preview_path = output_dir / "index.html"
    payload_path = output_dir / "draft-payload.json"
    state = load_state(config)
    saved_profile = state.get("toutiao_option_profile")
    profile = saved_profile if isinstance(saved_profile, dict) else {}
    options = dict(config["toutiao"]["default_options"])
    options.update(profile)
    result = {
        "schema_version": 1,
        "platform": "toutiao",
        "mode": "save_draft_only",
        "article_path": str(article_path),
        "title": title,
        "html": fragment,
        "plain_text": BeautifulSoup(fragment, "html.parser").get_text("\n", strip=True),
        "article_hash": body_hash(body),
        "figure_fingerprint": fingerprint,
        "figure_manifest": str(manifest_path.relative_to(PROJECT_ROOT)),
        "images": assets,
        "creator_url": config["toutiao"]["creator_url"],
        "drafts_url": config["toutiao"]["drafts_url"],
        "options": options,
        "option_profile_configured": bool(profile),
        "browser_steps": [
            "打开 creator_url，并确认当前为文章编辑页；登录或验证码出现时暂停",
            "填写 title，并用 html_without_images 填入正文",
            "按照 images 的 order 上传本地图片；优先用 anchor_before/anchor_after 还原正文内位置，before_heading 仅作章节核对",
            "option_profile_configured 为 false 时请用户确认一次页面常用选项；否则逐项应用 options",
            "页面找不到已保存的选项名称或值时暂停，不猜测替代选项",
            "只点击保存草稿，随后在 drafts_url 核对标题和保存状态",
        ],
        "safety": {
            "allow_save_draft": True,
            "allow_publish": False,
            "stop_on_unknown_page": True,
        },
    }
    result["html_without_images"] = fragment_without_images(fragment)
    preview_fragment = preview_images_as_data(fragment)
    atomic_write_text(preview_path, preview_document(title, preview_fragment, fingerprint))
    result["preview_path"] = str(preview_path)
    result["payload_path"] = str(payload_path)
    atomic_write_json(payload_path, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="生成今日头条富文本和浏览器交接包")
    parser.add_argument("article")
    args = parser.parse_args()
    try:
        result = render_toutiao(args.article)
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"今日头条预览：{result['preview_path']}")
    print(f"浏览器交接包：{result['payload_path']}")
    print(f"正文图片：{len(result['images'])} 张")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

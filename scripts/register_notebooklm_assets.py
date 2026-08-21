#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""登记 NotebookLM PPT 和信息图，形成公众号与出版可追溯的素材包。"""

from __future__ import annotations

import argparse
import hashlib
import html
import io
import os
import posixpath
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import yaml
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.writing_workflow import (  # noqa: E402
    article_state,
    atomic_write_text,
    load_public_config,
    load_state,
    project_path,
    save_state,
    split_frontmatter,
)

REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PRESENTATION_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bytes_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def copy_original(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if file_hash(source) != file_hash(target):
            raise RuntimeError(f"原始素材已存在且内容不同，已停止覆盖：{target}")
        return
    shutil.copy2(source, target)


def write_extracted(data: bytes, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if bytes_hash(data) != file_hash(target):
            raise RuntimeError(f"已提取图片内容不同，已停止覆盖：{target}")
        return
    target.write_bytes(data)


def presentation_slide_members(archive: ZipFile) -> list[str]:
    presentation = ET.fromstring(archive.read("ppt/presentation.xml"))
    rels = ET.fromstring(archive.read("ppt/_rels/presentation.xml.rels"))
    targets = {
        rel.attrib["Id"]: posixpath.normpath(
            posixpath.join("ppt", rel.attrib.get("Target", ""))
        )
        for rel in rels.findall(f"{{{REL_NS}}}Relationship")
    }
    result: list[str] = []
    slide_list = presentation.find(f"{{{PRESENTATION_NS}}}sldIdLst")
    if slide_list is None:
        return result
    for slide_id in list(slide_list):
        rel_id = slide_id.attrib.get(f"{{{DOC_REL_NS}}}id", "")
        member = targets.get(rel_id)
        if member and member.startswith("ppt/slides/slide"):
            result.append(member)
    return result


def slide_image_members(archive: ZipFile, slide_member: str) -> list[str]:
    slide_path = Path(slide_member)
    rel_member = posixpath.join(
        str(slide_path.parent),
        "_rels",
        f"{slide_path.name}.rels",
    )
    rels = ET.fromstring(archive.read(rel_member))
    members: list[str] = []
    for rel in rels.findall(f"{{{REL_NS}}}Relationship"):
        if not rel.attrib.get("Type", "").endswith("/image"):
            continue
        target = rel.attrib.get("Target", "")
        member = posixpath.normpath(
            posixpath.join(posixpath.dirname(slide_member), target)
        )
        if member in archive.namelist():
            members.append(member)
    return members


def image_dimensions(data: bytes) -> tuple[int, int, str]:
    with Image.open(io.BytesIO(data)) as image:
        return image.width, image.height, str(image.format or "").lower()


def select_largest_image(archive: ZipFile, members: list[str]) -> tuple[str, bytes]:
    candidates: list[tuple[int, str, bytes]] = []
    for member in members:
        data = archive.read(member)
        width, height, _ = image_dimensions(data)
        candidates.append((width * height, member, data))
    if not candidates:
        raise RuntimeError("幻灯片中没有找到可提取的图片")
    _, member, data = max(candidates, key=lambda item: item[0])
    return member, data


def slide_editability(archive: ZipFile, slide_member: str) -> dict[str, Any]:
    root = ET.fromstring(archive.read(slide_member))
    text_nodes = root.findall(f".//{{{DRAWING_NS}}}t")
    pictures = root.findall(f".//{{{PRESENTATION_NS}}}pic")
    return {
        "native_text_nodes": len(text_nodes),
        "picture_nodes": len(pictures),
        "editable": bool(text_nodes),
    }


def extract_ppt_images(pptx: Path, output_dir: Path, article_number: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with ZipFile(pptx) as archive:
        slides = presentation_slide_members(archive)
        if not slides:
            raise RuntimeError("PPT中没有找到幻灯片")
        for order, slide_member in enumerate(slides, 1):
            members = slide_image_members(archive, slide_member)
            media_member, data = select_largest_image(archive, members)
            width, height, image_format = image_dimensions(data)
            if image_format != "png":
                with Image.open(io.BytesIO(data)) as source:
                    converted = io.BytesIO()
                    source.convert("RGBA").save(converted, format="PNG")
                    data = converted.getvalue()
            target = output_dir / f"fig-{article_number}-{order:02d}.png"
            write_extracted(data, target)
            records.append(
                {
                    "id": f"fig-{article_number}-{order:02d}",
                    "kind": "ppt_slide",
                    "source_slide": order,
                    "source_member": media_member,
                    "file": str(target.relative_to(PROJECT_ROOT)),
                    "width_px": width,
                    "height_px": height,
                    "sha256": bytes_hash(data),
                    **slide_editability(archive, slide_member),
                }
            )
    return records


def article_number(article_path: Path) -> str:
    match = re.match(r"^(?:热点)?(\d+)-", article_path.name)
    if not match:
        raise RuntimeError(f"无法从文章文件名识别编号：{article_path.name}")
    return match.group(1)


def outline_titles(metadata: dict[str, Any]) -> dict[int, str]:
    raw_path = str(metadata.get("ppt_outline") or "").strip()
    if not raw_path:
        return {}
    path = project_path(raw_path)
    if not path.exists():
        return {}
    titles: dict[int, str] = {}
    pattern = re.compile(r"^##\s*第(\d+)页｜(.+)$", re.M)
    for number, title in pattern.findall(path.read_text(encoding="utf-8")):
        titles[int(number)] = title.strip()
    return titles


def print_assessment(width: int, height: int, *, dense: bool = False) -> dict[str, Any]:
    width_mm = round(width / 300 * 25.4, 1)
    height_mm = round(height / 300 * 25.4, 1)
    if dense:
        publication_status = "review_required"
        assessment = "清晰度足够；信息密度较高，纸书建议拆图或横向跨页"
    elif width >= 1800:
        publication_status = "review_required"
        assessment = "可作为整页候选；出版前仍需检查小字和NotebookLM标识"
    else:
        publication_status = "needs_redraw"
        assessment = "公众号可用；纸书半页可评估，整页建议重绘"
    return {
        "print_width_mm_at_300dpi": width_mm,
        "print_height_mm_at_300dpi": height_mm,
        "publication_status": publication_status,
        "print_assessment": assessment,
    }


def merge_human_fields(record: dict[str, Any], existing: dict[str, Any] | None) -> dict[str, Any]:
    if not existing:
        return record
    for key in (
        "title",
        "caption",
        "wechat_status",
        "publication_status",
        "used_in_wechat",
        "article_position",
        "notes",
    ):
        if key in existing:
            record[key] = existing[key]
    return record


def upsert_article_manifest(article_path: Path, manifest_path: Path) -> None:
    source = article_path.read_text(encoding="utf-8")
    frontmatter, body, _ = split_frontmatter(source)
    relative = str(manifest_path.relative_to(PROJECT_ROOT))
    line = f"figure_manifest: {relative}"
    if re.search(r"^figure_manifest:\s*.*$", frontmatter, re.M):
        frontmatter = re.sub(r"^figure_manifest:\s*.*$", line, frontmatter, count=1, flags=re.M)
    else:
        anchor = re.search(r"^platform:\s*.*$", frontmatter, re.M)
        if anchor:
            frontmatter = frontmatter[: anchor.start()] + line + "\n" + frontmatter[anchor.start():]
        else:
            frontmatter = frontmatter[:-3].rstrip() + "\n" + line + "\n---"
    atomic_write_text(article_path, f"{frontmatter}\n\n{body.rstrip()}\n")


def load_existing_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def create_contact_sheet(records: list[dict[str, Any]], target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    thumb_width, thumb_height = 440, 246
    label_height, gap, columns = 42, 20, 2
    rows = (len(records) + columns - 1) // columns
    canvas = Image.new(
        "RGB",
        (
            gap + columns * (thumb_width + gap),
            gap + rows * (thumb_height + label_height + gap),
        ),
        "#f3f4f6",
    )
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    for index, record in enumerate(records):
        row, column = divmod(index, columns)
        x = gap + column * (thumb_width + gap)
        y = gap + row * (thumb_height + label_height + gap)
        with Image.open(PROJECT_ROOT / record["file"]) as image:
            preview = image.convert("RGB")
            preview.thumbnail((thumb_width, thumb_height))
            px = x + (thumb_width - preview.width) // 2
            py = y + (thumb_height - preview.height) // 2
            canvas.paste(preview, (px, py))
        draw.rectangle((x, y, x + thumb_width, y + thumb_height), outline="#cbd5e1", width=2)
        draw.text((x, y + thumb_height + 10), record["id"], fill="#111827", font=font)
    canvas.save(target, format="PNG")


def gallery_html(records: list[dict[str, Any]], title: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    cards = []
    for record in records:
        relative = os.path.relpath(PROJECT_ROOT / record["file"], target.parent)
        cards.append(
            "<article><img src=\"{}\" alt=\"{}\"><h2>{}</h2>"
            "<p>{}×{}｜{}｜{}</p></article>".format(
                html.escape(relative),
                html.escape(record["title"]),
                html.escape(record["title"]),
                record["width_px"],
                record["height_px"],
                html.escape(record["wechat_status"]),
                html.escape(record["publication_status"]),
            )
        )
    document = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{}</title>
<style>body{{margin:0;background:#f3f4f6;color:#111827;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}}
main{{max-width:1280px;margin:auto;padding:24px}}h1{{font-size:26px}}.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}
article{{background:white;padding:14px;border-radius:14px;box-shadow:0 5px 20px #0f172a12}}img{{width:100%;display:block;border:1px solid #e5e7eb}}
h2{{font-size:17px;margin:12px 0 5px}}p{{color:#64748b;margin:0;font-size:13px}}@media(max-width:760px){{.grid{{grid-template-columns:1fr}}}}</style>
</head><body><main><h1>{}</h1><section class="grid">{}</section></main></body></html>""".format(
        html.escape(title), html.escape(title), "".join(cards)
    )
    target.write_text(document, encoding="utf-8")


def review_markdown(manifest: dict[str, Any], target: Path) -> None:
    source = manifest["source"]
    lines = [
        "---",
        "type: notebooklm_figure_review",
        f"date: {manifest['date']}",
        f"article: {manifest['article']}",
        f"manifest: {manifest['manifest_path']}",
        "---",
        "",
        f"# NotebookLM配图登记｜{manifest['topic']}",
        "",
        "## 登记结论",
        "",
        f"- PPT共{source['ppt_slide_count']}页，已按真实幻灯片顺序提取原始图片。",
        f"- PPT结构：{source['ppt_editability_label']}。",
        f"- 独立信息图：{source['infographic_width_px']}×{source['infographic_height_px']}。",
        "- 公众号使用：全部进入候选配图托盘，尚未写入正文。",
        "- 出版使用：PPT页保留内容与位置，但整页印刷默认建议重绘；独立信息图需检查小字密度后再决定整页或拆图。",
        "- 来源提醒：图片由NotebookLM生成，正式发布前需要核对图中文字、事实和标识。",
        "",
        "## 配图清单",
        "",
        "| 编号 | 标题 | 尺寸 | 300 DPI宽度 | 公众号 | 出版 | 文件 |",
        "|---|---|---:|---:|---|---|---|",
    ]
    for record in manifest["figures"]:
        lines.append(
            "| {id} | {title} | {width_px}×{height_px} | {print_width_mm_at_300dpi}mm | {wechat_status} | {publication_status} | `{file}` |".format(
                **record
            )
        )
    lines.extend(
        [
            "",
            "## 后续使用",
            "",
            "1. 打开完整排版编辑器时，由配图托盘读取本清单。",
            "2. 插入或删除图片后，按最终正文重新计算 `used_in_wechat` 与顺序。",
            "3. 结集出版时，只导出 `publication_status` 不是 `wechat_only` 的图片，并附本清单交给编辑。",
            "",
        ]
    )
    atomic_write_text(target, "\n".join(lines))


def update_media_index(manifest: dict[str, Any]) -> None:
    index_path = PROJECT_ROOT / "media" / "_index.md"
    text = index_path.read_text(encoding="utf-8")
    asset_root = manifest["asset_root"]
    if asset_root in text:
        return
    row = (
        f"| {manifest['date']} | {manifest['topic']} | NotebookLM PPT / 信息图 / 公众号配图 | "
        f"`{asset_root}/` | 待上传 | `{manifest['article']}`；"
        f"含{manifest['source']['ppt_slide_count']}页PPT原图和1张独立信息图，已生成出版登记清单 |\n"
    )
    marker = "\n## 类型写法\n"
    if marker not in text:
        raise RuntimeError("media/_index.md 缺少“类型写法”定位标记")
    atomic_write_text(index_path, text.replace(marker, "\n" + row + marker, 1))


def register(article: str, pptx: str, infographic: str, slug: str) -> dict[str, Any]:
    article_path = project_path(article).resolve()
    pptx_path = Path(pptx).expanduser().resolve()
    infographic_path = Path(infographic).expanduser().resolve()
    for path in (article_path, pptx_path, infographic_path):
        if not path.exists() or not path.is_file():
            raise RuntimeError(f"文件不存在：{path}")

    source_text = article_path.read_text(encoding="utf-8")
    _, _, metadata = split_frontmatter(source_text)
    date_text = str(metadata.get("date") or datetime.now().date().isoformat())
    number = article_number(article_path)
    topic = str(metadata.get("topic") or article_path.stem)
    asset_root = PROJECT_ROOT / "media" / "images" / f"{date_text}-{slug}-notebooklm"
    source_dir = asset_root / "source"
    wechat_dir = asset_root / "wechat"
    preview_dir = asset_root / "preview"
    analysis_dir = PROJECT_ROOT / "data" / "analysis" / date_text / f"notebooklm-{slug}"
    manifest_path = analysis_dir / "figure-manifest.yml"
    review_path = analysis_dir / "figure-review.md"

    copy_original(pptx_path, source_dir / "notebooklm-slides.pptx")
    copy_original(infographic_path, source_dir / "notebooklm-infographic.png")

    records = extract_ppt_images(pptx_path, wechat_dir, number)
    titles = outline_titles(metadata)
    existing_manifest = load_existing_manifest(manifest_path)
    existing_by_id = {
        str(item.get("id")): item
        for item in existing_manifest.get("figures", [])
        if isinstance(item, dict)
    }
    for record in records:
        order = int(record["source_slide"])
        record.update(
            {
                "title": titles.get(order, f"NotebookLM幻灯片第{order:02d}页"),
                "caption": titles.get(order, f"NotebookLM幻灯片第{order:02d}页"),
                "wechat_status": "candidate",
                "used_in_wechat": False,
                "article_position": None,
                "source_tool": "NotebookLM",
                "watermark_present": True,
                **print_assessment(record["width_px"], record["height_px"]),
            }
        )
        merge_human_fields(record, existing_by_id.get(record["id"]))

    infographic_target = wechat_dir / f"fig-{number}-infographic.png"
    copy_original(infographic_path, infographic_target)
    with Image.open(infographic_target) as image:
        info_width, info_height = image.size
    info_record = {
        "id": f"fig-{number}-infographic",
        "kind": "infographic",
        "source_slide": None,
        "source_member": None,
        "file": str(infographic_target.relative_to(PROJECT_ROOT)),
        "width_px": info_width,
        "height_px": info_height,
        "sha256": file_hash(infographic_target),
        "native_text_nodes": 0,
        "picture_nodes": 1,
        "editable": False,
        "title": infographic_path.stem,
        "caption": infographic_path.stem,
        "wechat_status": "candidate",
        "used_in_wechat": False,
        "article_position": None,
        "source_tool": "NotebookLM",
        "watermark_present": True,
        **print_assessment(info_width, info_height, dense=True),
    }
    merge_human_fields(info_record, existing_by_id.get(info_record["id"]))
    records.append(info_record)

    ppt_raster_only = all(not record["editable"] for record in records if record["kind"] == "ppt_slide")
    existing_plans = existing_manifest.get("plans")
    if not isinstance(existing_plans, dict):
        legacy_items = [
            {
                "id": str(item["id"]),
                "before_heading": str(item.get("article_position") or "").removesuffix("之前"),
            }
            for item in records
            if item.get("used_in_wechat")
            and str(item.get("article_position") or "").startswith("## ")
        ]
        existing_plans = {
            "shared": {"items": legacy_items, "updated_at": None},
            "wechat": {"inherit": "shared", "items": None, "updated_at": None},
            "toutiao": {"inherit": "shared", "items": None, "updated_at": None},
        }
    manifest = {
        "schema_version": 2,
        "type": "notebooklm_figure_manifest",
        "date": date_text,
        "registered_at": datetime.now().isoformat(timespec="seconds"),
        "article": str(article_path.relative_to(PROJECT_ROOT)),
        "topic": topic,
        "article_number": number,
        "asset_root": str(asset_root.relative_to(PROJECT_ROOT)),
        "manifest_path": str(manifest_path.relative_to(PROJECT_ROOT)),
        "review_path": str(review_path.relative_to(PROJECT_ROOT)),
        "preview_contact_sheet": str((preview_dir / "contact-sheet.png").relative_to(PROJECT_ROOT)),
        "preview_gallery": str((analysis_dir / "gallery.html").relative_to(PROJECT_ROOT)),
        "source": {
            "pptx": str((source_dir / "notebooklm-slides.pptx").relative_to(PROJECT_ROOT)),
            "pptx_sha256": file_hash(pptx_path),
            "ppt_slide_count": len(records) - 1,
            "ppt_editability": "raster_only" if ppt_raster_only else "partly_editable",
            "ppt_editability_label": "每页为整页位图，PPT文字和图形不可单独编辑" if ppt_raster_only else "含部分可编辑元素",
            "infographic": str((source_dir / "notebooklm-infographic.png").relative_to(PROJECT_ROOT)),
            "infographic_sha256": file_hash(infographic_path),
            "infographic_width_px": info_width,
            "infographic_height_px": info_height,
        },
        "plans": existing_plans,
        "confirmation": {
            "status": "editing",
            "confirmed_at": None,
            "body_hash": None,
            "plan_fingerprint": None,
        },
        "figures": records,
    }

    analysis_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_text(
        manifest_path,
        yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False, width=1000),
    )
    review_markdown(manifest, review_path)
    create_contact_sheet(records, preview_dir / "contact-sheet.png")
    gallery_html(records, f"第{number}篇NotebookLM配图", analysis_dir / "gallery.html")
    upsert_article_manifest(article_path, manifest_path)
    update_media_index(manifest)

    config = load_public_config()
    state = load_state(config)
    entry = article_state(state, article_path, create=True)
    assert entry is not None
    entry.update(
        {
            "status": "figures_editing",
            "figure_manifest": str(manifest_path.relative_to(PROJECT_ROOT)),
            "figure_asset_root": str(asset_root.relative_to(PROJECT_ROOT)),
            "figures_registered_at": manifest["registered_at"],
            "figures_count": len(records),
        }
    )
    save_state(state, config)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="登记NotebookLM PPT和信息图")
    parser.add_argument("article")
    parser.add_argument("--pptx", required=True)
    parser.add_argument("--infographic", required=True)
    parser.add_argument("--slug", required=True)
    args = parser.parse_args()
    try:
        manifest = register(args.article, args.pptx, args.infographic, args.slug)
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"NotebookLM素材登记完成：{len(manifest['figures'])}项")
    print(f"素材目录：{PROJECT_ROOT / manifest['asset_root']}")
    print(f"登记清单：{PROJECT_ROOT / manifest['manifest_path']}")
    print(f"审查页面：{PROJECT_ROOT / manifest['review_path']}")
    print(f"配图总览：{PROJECT_ROOT / manifest['preview_contact_sheet']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

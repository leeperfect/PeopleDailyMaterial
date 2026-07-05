#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""使用固定版本 doocs/md 生成公众号 HTML 和 Codex 内只读预览。"""

from __future__ import annotations

import argparse
import html
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.writing_workflow import (
    article_state,
    body_hash,
    effective_layout,
    load_public_config,
    load_state,
    project_path,
    save_state,
    split_frontmatter,
    title_from_article,
    workflow_id,
)


def doocs_ready(config: dict[str, Any]) -> Path:
    repo = project_path(config["doocs"]["local_dir"])
    revision_file = repo / ".peopledaily-revision"
    expected = config["doocs"]["revision"]
    if not revision_file.exists() or revision_file.read_text(encoding="utf-8").strip() != expected:
        raise RuntimeError(
            "doocs/md 尚未准备好，请先运行：python3 scripts/setup_doocs_md.py"
        )
    if not (repo / "packages" / "mcp-server" / "node_modules").exists():
        raise RuntimeError(
            "doocs/md 依赖尚未安装，请运行：python3 scripts/setup_doocs_md.py"
        )
    return repo


def layout_for_article(
    article_path: Path,
    metadata: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    state = load_state(config)
    entry = article_state(state, article_path) or {}
    layout = effective_layout(metadata, config, entry.get("wechat_layout"))
    code_theme_path = project_path(config["doocs"]["code_theme_css"])
    if code_theme_path.exists():
        code_theme_css = code_theme_path.read_text(encoding="utf-8")
        layout["customCSS"] = "\n".join(
            part for part in (code_theme_css, layout.get("customCSS", "")) if part
        )
    # doocs/md 的 MCP 渲染结果使用 section.container，不包含编辑器里的
    # #output 外层容器；原生缩进和两端对齐规则因此不会命中。把同一排版参数
    # 显式写入导出片段，确保只读预览和公众号草稿使用完全一致的最终 HTML。
    paragraph_rules: list[str] = []
    if layout.get("isUseIndent"):
        paragraph_rules.append("text-indent: 2em !important;")
    if layout.get("isUseJustify"):
        paragraph_rules.append("text-align: justify !important;")
    if paragraph_rules:
        paragraph_css = (
            "section.container p {\n  "
            + "\n  ".join(paragraph_rules)
            + "\n}"
        )
        layout["customCSS"] = "\n".join(
            part for part in (layout.get("customCSS", ""), paragraph_css) if part
        )
    return layout


def render_with_doocs(markdown: str, layout: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    repo = doocs_ready(config)
    payload = json.dumps(
        {"repo": str(repo), "markdown": markdown, "options": layout},
        ensure_ascii=False,
    )
    result = subprocess.run(
        ["node", str(PROJECT_ROOT / "scripts" / "doocs_bridge.mjs")],
        input=payload,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        check=False,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"doocs/md 渲染失败：{result.stderr.strip()}")
    try:
        rendered = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError("doocs/md 返回了无法识别的渲染结果") from error
    if not rendered.get("html"):
        raise RuntimeError("doocs/md 没有生成 HTML")
    return rendered


def preview_document(title: str, fragment: str, article_hash: str) -> str:
    safe_title = html.escape(title)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{safe_title}</title>
<style>
body {{ margin:0; background:#eef1f5; color:#202124; font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif; }}
.toolbar {{ position:sticky; top:0; z-index:5; display:flex; gap:12px; align-items:center; padding:12px 18px; background:#111827; color:white; }}
.toolbar strong {{ flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
.toolbar button {{ border:0; border-radius:8px; padding:9px 14px; background:#ff6a2a; color:white; cursor:pointer; }}
.phone {{ width:min(100%, 720px); min-height:calc(100vh - 72px); box-sizing:border-box; margin:18px auto; padding:28px 24px 60px; background:white; box-shadow:0 8px 32px #1f29371a; }}
.meta {{ font-size:12px; opacity:.72; }}
@media (max-width:760px) {{ .phone {{ margin:0; box-shadow:none; padding:22px 18px 48px; }} }}
</style>
</head>
<body>
<div class="toolbar">
  <strong>{safe_title}</strong>
  <span class="meta">正文指纹 {article_hash[:10]}</span>
  <button id="copy">复制公众号富文本</button>
</div>
<main id="article" class="phone">{fragment}</main>
<script>
document.getElementById("copy").addEventListener("click", async () => {{
  const article = document.getElementById("article");
  const rich = article.innerHTML;
  const plain = article.innerText;
  try {{
    await navigator.clipboard.write([
      new ClipboardItem({{
        "text/html": new Blob([rich], {{type:"text/html"}}),
        "text/plain": new Blob([plain], {{type:"text/plain"}})
      }})
    ]);
    document.getElementById("copy").textContent = "已复制";
  }} catch (_) {{
    const range = document.createRange();
    range.selectNodeContents(article);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
  }}
}});
</script>
</body>
</html>
"""


def render_article(article: str, *, fragment_only: bool = False) -> dict[str, Any]:
    config = load_public_config()
    article_path = project_path(article).resolve()
    if not article_path.exists():
        raise RuntimeError(f"文章不存在：{article_path}")
    source = article_path.read_text(encoding="utf-8")
    _, body, metadata = split_frontmatter(source)
    layout = layout_for_article(article_path, metadata, config)
    rendered = render_with_doocs(body, layout, config)
    title = title_from_article(article_path, metadata, body)
    digest = {
        "article_path": str(article_path),
        "article_hash": body_hash(body),
        "layout": layout,
        "html": rendered["html"],
        "title": title,
        "reading_time": rendered.get("readingTime", {}),
    }
    if fragment_only:
        return digest

    output_dir = Path(config["preview_root"]) / workflow_id(article_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    preview_path = output_dir / "index.html"
    preview_path.write_text(
        preview_document(title, rendered["html"], digest["article_hash"]),
        encoding="utf-8",
    )
    (output_dir / "render.json").write_text(
        json.dumps(digest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    digest["preview_path"] = str(preview_path)
    digest["preview_url"] = preview_path.as_uri()
    return digest


def save_layout(article: str, updates: dict[str, Any]) -> dict[str, Any]:
    config = load_public_config()
    article_path = project_path(article).resolve()
    if not article_path.exists():
        raise RuntimeError(f"文章不存在：{article_path}")
    _, _, metadata = split_frontmatter(article_path.read_text(encoding="utf-8"))
    allowed = set(config["doocs"]["default_layout"])
    unknown = set(updates) - allowed
    if unknown:
        raise RuntimeError(f"不支持的排版参数：{', '.join(sorted(unknown))}")
    state = load_state(config)
    entry = article_state(state, article_path, create=True)
    assert entry is not None
    current = dict(entry.get("wechat_layout") or {})
    current.update(updates)
    entry["wechat_layout"] = current
    save_state(state, config)
    return effective_layout(metadata, config, current)


def main() -> int:
    parser = argparse.ArgumentParser(description="用 doocs/md 渲染公众号文章")
    subparsers = parser.add_subparsers(dest="command", required=True)
    render_parser = subparsers.add_parser("render", help="生成只读成品预览")
    render_parser.add_argument("article")
    layout_parser = subparsers.add_parser("save-layout", help="保存本文排版设置")
    layout_parser.add_argument("article")
    layout_parser.add_argument("--theme", choices=["default", "grace", "simple"])
    layout_parser.add_argument("--primary-color")
    layout_parser.add_argument("--font-family")
    layout_parser.add_argument("--font-size")
    layout_parser.add_argument(
        "--legend",
        choices=["title-alt", "alt-title", "title", "alt", "filename", "none"],
    )
    layout_parser.add_argument("--mac-code", choices=["on", "off"])
    layout_parser.add_argument("--line-numbers", choices=["on", "off"])
    layout_parser.add_argument("--cite-links", choices=["on", "off"])
    layout_parser.add_argument("--indent", choices=["on", "off"])
    layout_parser.add_argument("--justify", choices=["on", "off"])
    layout_parser.add_argument(
        "--h2-style",
        choices=["default", "color-only", "border-bottom", "border-left", "custom"],
    )
    layout_parser.add_argument("--custom-css")
    arguments = sys.argv[1:]
    if arguments and arguments[0] not in {"render", "save-layout"}:
        arguments.insert(0, "render")
    args = parser.parse_args(arguments)
    try:
        if args.command == "save-layout":
            updates: dict[str, Any] = {}
            if args.theme:
                updates["theme"] = args.theme
            if args.primary_color:
                updates["primaryColor"] = args.primary_color
            if args.font_family:
                updates["fontFamily"] = args.font_family
            if args.font_size:
                updates["fontSize"] = args.font_size
            if args.legend:
                updates["legend"] = args.legend
            if args.mac_code:
                updates["isMacCodeBlock"] = args.mac_code == "on"
            if args.line_numbers:
                updates["isShowLineNumber"] = args.line_numbers == "on"
            if args.cite_links:
                updates["citeStatus"] = args.cite_links == "on"
            if args.indent:
                updates["isUseIndent"] = args.indent == "on"
            if args.justify:
                updates["isUseJustify"] = args.justify == "on"
            if args.h2_style:
                updates["headingStyles"] = {"h2": args.h2_style}
            if args.custom_css is not None:
                updates["customCSS"] = args.custom_css
            layout = save_layout(args.article, updates)
            print(json.dumps(layout, ensure_ascii=False, indent=2))
        else:
            result = render_article(args.article)
            print(f"预览文件：{result['preview_path']}")
            print("请由 writing_workflow.py preview 启动 Codex 内可访问的本地预览。")
            print("该文件与公众号草稿使用同一份 doocs/md HTML。")
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

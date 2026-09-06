#!/usr/bin/env python3
"""Build a self-contained, read-only idea magazine for static hosting."""

from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SCRIPT = ROOT / "scripts" / "serve_idea_magazine.py"
DEFAULT_OUTPUT = ROOT / "data" / "exports" / "idea_magazine_site" / "index.html"


def load_source_module() -> Any:
    spec = importlib.util.spec_from_file_location("serve_idea_magazine_static", SOURCE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载选题工作台：{SOURCE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def script_safe_json(value: Any) -> str:
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )


def build_site(output_path: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    module = load_source_module()
    payload = module.idea_payload()
    generated_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")
    payload["meta"] = {
        "generated_at": generated_at,
        "data_role": "只读展示副本；本地素材资产库仍是唯一事实源",
    }

    marker = "  <script>\n    const EMBEDDED_PAYLOAD"
    if marker not in module.HTML:
        raise RuntimeError("选题工作台页面缺少静态数据注入位置")
    bootstrap = (
        "  <script>window.__IDEA_MAGAZINE_PAYLOAD__="
        + script_safe_json(payload)
        + ";</script>\n"
    )
    html = module.HTML.replace(marker, bootstrap + marker, 1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return {
        "output": str(output_path.relative_to(ROOT)),
        "generated_at": generated_at,
        "idea_count": len(payload.get("ideas", [])),
        "size_bytes": output_path.stat().st_size,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="生成可发布到妙搭的只读选题网页")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="输出 index.html 路径")
    args = parser.parse_args()
    result = build_site(Path(args.output))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

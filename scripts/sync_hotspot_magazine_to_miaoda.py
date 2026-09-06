#!/usr/bin/env python3
"""Build and publish the APP opinion hotspot magazine to Miaoda."""

from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Any

import build_hotspot_magazine_site


ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "data" / "peopleapp_opinion" / "site"
CONFIG_PATH = ROOT / "data" / "peopleapp_opinion" / "miaoda_deployment.json"
HTML_LIMIT = 10 * 1024 * 1024
ARCHIVE_LIMIT = 20 * 1024 * 1024
TOTAL_LIMIT = 200 * 1024 * 1024


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def measure_site() -> dict[str, int]:
    files = [path for path in SITE_DIR.rglob("*") if path.is_file()]
    html_sizes = [path.stat().st_size for path in files if path.suffix.lower() == ".html"]
    archive_buffer = io.BytesIO()
    with tarfile.open(fileobj=archive_buffer, mode="w:gz") as archive:
        for path in files:
            archive.add(path, arcname=str(path.relative_to(SITE_DIR)))
    return {
        "largest_html_bytes": max(html_sizes, default=0),
        "archive_bytes": archive_buffer.tell(),
        "total_bytes": sum(path.stat().st_size for path in files),
    }


def assert_publishable(sizes: dict[str, int]) -> None:
    failures = []
    if sizes["largest_html_bytes"] > HTML_LIMIT:
        failures.append("单个 HTML 超过 10MB")
    if sizes["archive_bytes"] > ARCHIVE_LIMIT:
        failures.append("压缩包超过 20MB")
    if sizes["total_bytes"] > TOTAL_LIMIT:
        failures.append("未压缩文件总量超过 200MB")
    if failures:
        raise RuntimeError("；".join(failures))


def run_cli(arguments: list[str]) -> dict[str, Any]:
    environment = os.environ.copy()
    environment["LARKSUITE_CLI_NO_UPDATE_NOTIFIER"] = "1"
    environment["LARKSUITE_CLI_NO_SKILLS_NOTIFIER"] = "1"
    completed = subprocess.run(
        ["lark-cli", *arguments, "--as", "user", "--json"],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    raw = completed.stdout.strip() or completed.stderr.strip()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(raw or "妙搭命令没有返回结果") from exc
    if completed.returncode != 0 or not payload.get("ok"):
        error = payload.get("error") or {}
        raise RuntimeError(error.get("hint") or error.get("message") or "妙搭同步失败")
    return payload


def write_config(config: dict[str, Any]) -> None:
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sync(app_id: str | None = None, build_only: bool = False) -> dict[str, Any]:
    build_result = build_hotspot_magazine_site.build_site(SITE_DIR / "index.html")
    sizes = measure_site()
    assert_publishable(sizes)
    if build_only:
        return {"build": build_result, "sizes": sizes, "published": False}

    config = load_config()
    resolved_app_id = app_id or config.get("app_id")
    if not resolved_app_id:
        raise RuntimeError("尚未登记妙搭应用 ID，请先创建应用或使用 --app-id 指定")
    published = run_cli(
        [
            "apps",
            "+html-publish",
            "--app-id",
            str(resolved_app_id),
            "--path",
            str(SITE_DIR.relative_to(ROOT)),
        ]
    )
    data = published.get("data", {})
    if not data.get("url"):
        raise RuntimeError("妙搭尚未返回发布地址，请稍后重试")
    next_config = {
        **config,
        "app_name": config.get("app_name") or "APP 评论热点选题工作台",
        "app_id": str(resolved_app_id),
        "app_type": "html",
        "access_scope": config.get("access_scope") or "specific",
        "published_url": data["url"],
        "management_url": f"https://miaoda.feishu.cn/app/{resolved_app_id}",
        "published_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_directory": str(SITE_DIR.relative_to(ROOT)),
        "data_role": "只读展示副本，唯一资料仍保存在本地 APP 评论热点库",
    }
    write_config(next_config)
    return {
        "build": build_result,
        "sizes": sizes,
        "published": True,
        "app_id": str(resolved_app_id),
        "url": data["url"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="把 APP 评论热点选题工作台同步到妙搭")
    parser.add_argument("--app-id", help="首次发布时指定妙搭 HTML 应用 ID")
    parser.add_argument("--build-only", action="store_true", help="只生成并检查网页，不发布")
    args = parser.parse_args()
    print(json.dumps(sync(app_id=args.app_id, build_only=args.build_only), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人民日报 APP 评论库每日任务。

执行顺序：
1. 采集最近 N 天 APP 评论文章；
2. 同步到独立 Notion 评论库；
3. 写入当天运行日志。
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.peopleapp_opinion import RUN_LOG_DIR, TIMEZONE


def run_step(command: List[str], log_lines: List[str]) -> int:
    log_lines.append(f"$ {' '.join(command)}")
    process = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    output = process.stdout or ""
    if output:
        log_lines.append(output.rstrip())
    log_lines.append(f"退出码：{process.returncode}")
    return process.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="执行人民日报 APP 评论库每日采集与同步")
    parser.add_argument("--days", type=int, default=3, help="回看最近几天，默认 3 天")
    parser.add_argument("--delay", type=float, default=0.35, help="采集请求间隔秒数，默认 0.35")
    parser.add_argument("--sync-delay", type=float, default=0.35, help="Notion 写入间隔秒数，默认 0.35")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不写入本地库或 Notion")
    args = parser.parse_args()

    RUN_LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(TIMEZONE).strftime("%Y%m%d_%H%M%S")
    log_path = RUN_LOG_DIR / f"peopleapp_opinion_daily_{timestamp}.log"
    log_lines: List[str] = [
        "人民日报 APP 评论库每日任务",
        f"开始时间：{datetime.now(TIMEZONE).isoformat(timespec='seconds')}",
        f"回看天数：{args.days}",
        "",
    ]

    python = sys.executable
    crawl_command = [
        python,
        str(PROJECT_ROOT / "scripts" / "crawl_peopleapp_opinion.py"),
        "--days",
        str(args.days),
        "--delay",
        str(args.delay),
    ]
    sync_command = [
        python,
        str(PROJECT_ROOT / "scripts" / "sync_peopleapp_opinion_to_notion.py"),
        "--days",
        str(args.days),
        "--delay",
        str(args.sync_delay),
    ]
    hotspot_command = [
        python,
        str(PROJECT_ROOT / "scripts" / "update_peopleapp_opinion_topic_library.py"),
        "--all",
    ]
    if args.dry_run:
        crawl_command.append("--dry-run")
        sync_command.append("--dry-run")

    crawl_code = run_step(crawl_command, log_lines)
    sync_code = 0
    hotspot_code = 0
    if crawl_code == 0:
        log_lines.append("")
        sync_code = run_step(sync_command, log_lines)
    else:
        log_lines.append("采集失败，已跳过 Notion 同步。")

    if crawl_code == 0:
        log_lines.append("")
        hotspot_code = run_step(hotspot_command, log_lines)
    else:
        log_lines.append("采集失败，已跳过热点梳理。")

    exit_code = crawl_code or sync_code or hotspot_code
    log_lines.extend(
        [
            "",
            f"结束时间：{datetime.now(TIMEZONE).isoformat(timespec='seconds')}",
            f"最终退出码：{exit_code}",
        ]
    )
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")

    print(f"每日任务完成，退出码：{exit_code}")
    print(f"运行日志：{log_path.relative_to(PROJECT_ROOT)}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
采集人民日报 APP 评论/锐评频道。

默认回看最近 3 天，只写入 data/peopleapp_opinion/，不会进入原有人民日报核心库。
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.peopleapp_opinion import (
    DB_PATH,
    crawl_peopleapp_opinion,
    default_date_range,
    save_report,
)


def rel(path: str) -> str:
    try:
        return str(Path(path).resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return path


def main() -> int:
    parser = argparse.ArgumentParser(description="采集人民日报 APP 评论库")
    parser.add_argument("--days", type=int, default=3, help="默认回看最近几天，默认 3 天")
    parser.add_argument("--start-date", help="开始日期 YYYY-MM-DD")
    parser.add_argument("--end-date", help="结束日期 YYYY-MM-DD")
    parser.add_argument("--pages", type=int, default=10, help="最多翻页数，默认 10 页")
    parser.add_argument("--page-size", type=int, default=20, help="每页条数，默认 20")
    parser.add_argument("--url", action="append", help="指定 APP 文章链接，可重复传入")
    parser.add_argument("--force", action="store_true", help="已存在文章也重新抓取并覆盖")
    parser.add_argument("--dry-run", action="store_true", help="只预览，不写入本地库")
    parser.add_argument("--delay", type=float, default=0.35, help="接口请求间隔秒数，默认 0.35")
    args = parser.parse_args()

    if args.start_date or args.end_date:
        start_date = args.start_date or args.end_date
        end_date = args.end_date or args.start_date
    else:
        start_date, end_date = default_date_range(args.days)

    print("人民日报 APP 评论库采集")
    print(f"本地核心库：{DB_PATH.relative_to(PROJECT_ROOT)}")
    if args.url:
        print(f"指定链接：{len(args.url)} 条")
    else:
        print(f"采集范围：{start_date} 至 {end_date}，最多 {args.pages} 页")
    if args.dry_run:
        print("运行模式：dry-run，只预览不写入")

    result = crawl_peopleapp_opinion(
        start_date=start_date,
        end_date=end_date,
        max_pages=args.pages,
        page_size=args.page_size,
        dry_run=args.dry_run,
        force=args.force,
        urls=args.url,
        delay=args.delay,
    )

    label = "dry_run" if args.dry_run else "daily"
    json_path, csv_path = save_report(result, label=label)

    print("\n采集完成")
    print(f"频道列表条数：{result.total_list_items}")
    print(f"本次候选文章：{result.selected_items}")
    print(f"新增/更新文章：{result.downloaded}")
    print(f"跳过重复文章：{result.skipped_existing}")
    print(f"失败文章：{result.failed}")
    print(f"采集报告：{rel(json_path)}")
    print(f"CSV 留档：{rel(csv_path)}")

    if result.failures:
        print("\n失败清单：")
        for item in result.failures:
            print(f"- {item.get('title') or item.get('url')}: {item.get('error')}")

    return 1 if result.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

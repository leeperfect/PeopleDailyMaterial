#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为文章应用共用或单个平台配图计划。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.figure_workflow import apply_plan, initial_plan  # noqa: E402
from modules.writing_workflow import project_path  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="应用双平台配图计划")
    parser.add_argument("article")
    parser.add_argument("--initial", action="store_true")
    parser.add_argument("--plan-json")
    parser.add_argument(
        "--platform",
        choices=["shared", "wechat", "toutiao"],
        default="shared",
    )
    args = parser.parse_args()
    article = project_path(args.article).resolve()
    try:
        if args.initial:
            plan = initial_plan(article)
        elif args.plan_json:
            plan = json.loads(args.plan_json)
            if not isinstance(plan, list):
                raise RuntimeError("配图计划必须是列表")
        else:
            parser.error("请选择 --initial 或 --plan-json")
        result = apply_plan(article, plan, platform=args.platform)
    except (RuntimeError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"{result['platform']} 配图计划已应用：{result['used_count']}张")
    print(f"登记清单：{PROJECT_ROOT / result['manifest_path']}")
    if result["before_plan_snapshot"]:
        print(f"变更前快照：{PROJECT_ROOT / result['before_plan_snapshot']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

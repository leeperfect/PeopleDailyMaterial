#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重建 sync_status.json - 根据 vault / raw / exports 中的已有数据
自动标记已有文章数据的日期为"已同步"
"""

import os
import json
import re
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYNC_STATUS_FILE = os.path.join(BASE_DIR, 'data', 'sync_status.json')


def scan_all_dates():
    """扫描所有数据源，找出有文章数据的日期"""
    dates = set()

    # 1. vault 目录
    vault_dir = os.path.join(BASE_DIR, 'data', 'vault')
    if os.path.exists(vault_dir):
        for root, dirs, files in os.walk(vault_dir):
            for d in dirs:
                if re.match(r'^\d{4}-\d{2}-\d{2}$', d):
                    date_path = os.path.join(root, d)
                    has_md = any(
                        f.endswith('.md')
                        for _, _, fnames in os.walk(date_path)
                        for f in fnames
                    )
                    if has_md:
                        dates.add(d)
                        print(f"  vault: {d} ✅")

    # 2. raw 目录
    raw_dir = os.path.join(BASE_DIR, 'data', 'raw')
    if os.path.exists(raw_dir):
        for fname in os.listdir(raw_dir):
            m = re.match(r'articles_(\d{8})\.json', fname)
            if m:
                ds = m.group(1)
                date_str = f"{ds[:4]}-{ds[4:6]}-{ds[6:8]}"
                if date_str not in dates:
                    print(f"  raw: {date_str} ✅")
                dates.add(date_str)

    # 3. exports 目录
    exports_dir = os.path.join(BASE_DIR, 'data', 'exports')
    if os.path.exists(exports_dir):
        for fname in os.listdir(exports_dir):
            m = re.match(r'articles_(\d{8})\.json', fname)
            if m:
                ds = m.group(1)
                date_str = f"{ds[:4]}-{ds[4:6]}-{ds[6:8]}"
                if date_str not in dates:
                    print(f"  exports: {date_str} ✅")
                dates.add(date_str)

    return dates


def main():
    print("=" * 50)
    print("  🔄 重建 sync_status.json")
    print("=" * 50)

    # 加载现有状态
    existing = set()
    if os.path.exists(SYNC_STATUS_FILE):
        with open(SYNC_STATUS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            existing = set(data.get('synced_dates', []))
        print(f"\n  现有同步记录: {sorted(existing)}")

    # 扫描所有数据源
    print(f"\n  扫描数据目录中...")
    all_dates = scan_all_dates()

    # 合并
    merged = existing | all_dates
    print(f"\n  合并后: {sorted(merged)}")

    # 保存
    os.makedirs(os.path.dirname(SYNC_STATUS_FILE), exist_ok=True)
    with open(SYNC_STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'synced_dates': sorted(merged)}, f, ensure_ascii=False, indent=2)

    new_dates = merged - existing
    if new_dates:
        print(f"\n  ✅ 新增 {len(new_dates)} 个日期: {sorted(new_dates)}")
    else:
        print(f"\n  ℹ️ 无新增日期")

    print(f"  📁 已保存到 {SYNC_STATUS_FILE}")
    print("=" * 50)


if __name__ == '__main__':
    main()

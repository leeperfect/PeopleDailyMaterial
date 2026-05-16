#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一次性脚本：将已有的 data/raw/articles_YYYYMMDD.json 文件中的日期
标记为已同步状态，写入 data/sync_status.json。

这些文件是之前已经下载并同步到 Notion 的，需要回溯标记。
运行一次即可，之后由 main.py 自动维护。
"""

import os
import sys
import json

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.date_selector import load_synced_dates, save_synced_dates, get_downloaded_dates


def main():
    downloaded = get_downloaded_dates()
    existing_synced = load_synced_dates()
    
    new_dates = downloaded - existing_synced
    all_dates = existing_synced | downloaded
    
    if not new_dates:
        print(f"已有 {len(existing_synced)} 个日期标记为已同步，无需更新。")
        return
    
    save_synced_dates(all_dates)
    print(f"✅ 已标记 {len(new_dates)} 个新日期为已同步状态：")
    for d in sorted(new_dates):
        print(f"   {d}")
    print(f"\n总计 {len(all_dates)} 个日期已标记。")


if __name__ == '__main__':
    main()

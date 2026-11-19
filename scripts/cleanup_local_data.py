#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按日期范围删除本地文章数据的一次性历史脚本（危险，非常规维护工具）

功能：
1. 只保留 --keep-start 至 --keep-end 范围内的数据
2. 删除范围外全部 raw/processed/vault 文章数据
3. 同步改写 sync_status.json 和 series_registry.json

警告：本脚本会真实删除 data/raw 与 data/vault 内容，违反项目
"不轻易删改事实留存层" 原则，仅限老师明确要求的整库裁剪场景。
必须显式传入日期范围和 --confirm-delete 才会执行；不带参数运行
只会显示本警告并退出。日常清理缓存请用手动方式或清理类垃圾文件，
不要运行本脚本。
"""

import os
import sys
import json
import shutil
import argparse
import re
from datetime import datetime


def get_date_from_filename(filename):
    """从文件名中提取日期字符串 (YYYYMMDD 格式)"""
    # 文件名格式: articles_YYYYMMDD.json
    match = re.fullmatch(r'articles_([0-9]{8})\.json', filename)
    if match:
        try:
            datetime.strptime(match[1], '%Y%m%d')
        except ValueError:
            return None
        return match[1]
    return None


def is_date_in_range(date_str, start_date, end_date):
    """检查日期是否在指定范围内
    
    Args:
        date_str: 日期字符串 (YYYYMMDD 或 YYYY-MM-DD 格式)
        start_date: 开始日期 (datetime)
        end_date: 结束日期 (datetime)
    """
    try:
        if '-' in date_str:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        else:
            date_obj = datetime.strptime(date_str, '%Y%m%d')
        return start_date <= date_obj <= end_date
    except (ValueError, TypeError):
        return False


def cleanup_json_files(directory, start_date, end_date):
    """清理指定目录下的 JSON 文章文件
    
    Args:
        directory: 目录路径
        start_date: 开始日期 (datetime)
        end_date: 结束日期 (datetime)
    """
    if not os.path.isdir(directory) or os.path.islink(directory):
        return
    
    deleted_count = 0
    kept_count = 0
    
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if not os.path.isfile(file_path) or os.path.islink(file_path):
            continue
        date_str = get_date_from_filename(filename)
        if not date_str:
            continue
        
        if is_date_in_range(date_str, start_date, end_date):
            kept_count += 1
        else:
            os.remove(file_path)
            deleted_count += 1
            print(f"  删除: {file_path}")
    
    print(f"\n📁 {directory}")
    print(f"   保留: {kept_count} 个文件")
    print(f"   删除: {deleted_count} 个文件")


def cleanup_vault(directory, start_date, end_date):
    """清理 vault 目录下的文章
    
    Args:
        directory: vault 目录路径
        start_date: 开始日期 (datetime)
        end_date: 结束日期 (datetime)
    """
    if not os.path.isdir(directory) or os.path.islink(directory):
        return
    
    deleted_count = 0
    kept_count = 0
    
    # 遍历年份目录
    for year_dir in os.listdir(directory):
        year_path = os.path.join(directory, year_dir)
        if not re.fullmatch(r'[0-9]{4}', year_dir) or not os.path.isdir(year_path) or os.path.islink(year_path):
            continue
        
        # 遍历月份目录
        for month_dir in os.listdir(year_path):
            month_path = os.path.join(year_path, month_dir)
            if not re.fullmatch(r'0[1-9]|1[0-2]', month_dir) or not os.path.isdir(month_path) or os.path.islink(month_path):
                continue
            
            # 遍历日期目录
            for date_dir in os.listdir(month_path):
                date_path = os.path.join(month_path, date_dir)
                if not os.path.isdir(date_path) or os.path.islink(date_path):
                    continue
                if not re.fullmatch(rf'{year_dir}-{month_dir}-[0-9]{{2}}', date_dir):
                    continue
                try:
                    datetime.strptime(date_dir, '%Y-%m-%d')
                except ValueError:
                    continue
                
                # 检查日期目录名 (YYYY-MM-DD)
                if is_date_in_range(date_dir, start_date, end_date):
                    kept_count += 1
                else:
                    shutil.rmtree(date_path)
                    deleted_count += 1
                    print(f"  删除: {date_path}")
    
    print(f"\n📁 {directory}")
    print(f"   保留: {kept_count} 个日期目录")
    print(f"   删除: {deleted_count} 个日期目录")


def update_sync_status(file_path, start_date, end_date):
    """更新同步状态文件
    
    Args:
        file_path: sync_status.json 文件路径
        start_date: 开始日期 (datetime)
        end_date: 结束日期 (datetime)
    """
    if not os.path.exists(file_path):
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    original_count = len(data.get('synced_dates', []))
    
    # 过滤日期
    filtered_dates = []
    for date_str in data.get('synced_dates', []):
        if is_date_in_range(date_str, start_date, end_date):
            filtered_dates.append(date_str)
    
    data['synced_dates'] = filtered_dates
    
    # 保存更新
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 {file_path}")
    print(f"   原同步日期数: {original_count}")
    print(f"   保留同步日期数: {len(filtered_dates)}")


def cleanup_series_registry(file_path, start_date, end_date):
    """清理系列注册表，只保留范围内日期的系列
    
    Args:
        file_path: series_registry.json 文件路径
        start_date: 开始日期 (datetime)
        end_date: 结束日期 (datetime)
    """
    if not os.path.exists(file_path):
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    original_count = len(data)
    filtered_data = {}
    
    # 检查每个系列的文章日期
    for series_id, series_info in data.items():
        articles = series_info.get('articles', [])
        # 检查系列中是否有至少一篇文章在范围内
        has_valid_article = False
        for article in articles:
            article_date = article.get('date', '')
            if is_date_in_range(article_date, start_date, end_date):
                has_valid_article = True
                break
        
        if has_valid_article:
            filtered_data[series_id] = series_info
    
    # 保存更新
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(filtered_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 {file_path}")
    print(f"   原系列数: {original_count}")
    print(f"   保留系列数: {len(filtered_data)}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='危险：按日期范围删除 raw/processed/vault 文章数据。必须显式指定保留范围并加 --confirm-delete。')
    parser.add_argument('--keep-start', metavar='YYYY-MM-DD', help='保留范围的开始日期')
    parser.add_argument('--keep-end', metavar='YYYY-MM-DD', help='保留范围的结束日期')
    parser.add_argument('--confirm-delete', action='store_true',
                        help='确认执行真实删除（缺少此参数时只提示、不删除）')
    args = parser.parse_args()

    if not (args.keep_start and args.keep_end and args.confirm_delete):
        print("=" * 60)
        print("  ⚠️  本脚本会删除保留范围之外的全部 raw/vault 文章数据！")
        print("  它是一次性历史裁剪工具，不是日常缓存清理工具。")
        print("  如确需使用，请显式指定范围并确认，例如：")
        print("    python3 scripts/cleanup_local_data.py \\")
        print("        --keep-start 2026-01-01 --keep-end 2026-01-09 --confirm-delete")
        print("  本次未执行任何删除。")
        print("=" * 60)
        sys.exit(1)

    start_date = datetime.strptime(args.keep_start, '%Y-%m-%d')
    end_date = datetime.strptime(args.keep_end, '%Y-%m-%d')
    if start_date > end_date:
        parser.error('保留开始日期不得晚于结束日期，未执行删除。')

    print("=" * 60)
    print("  🗑️  本地数据清理工具（真实删除）")
    print("=" * 60)
    print(f"\n保留日期范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    print("\n开始清理...\n")
    
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 清理 raw 目录
    cleanup_json_files(os.path.join(PROJECT_ROOT, 'data', 'raw'), start_date, end_date)
    
    # 清理 processed 目录
    cleanup_json_files(os.path.join(PROJECT_ROOT, 'data', 'processed'), start_date, end_date)
    
    # 清理 vault 目录
    cleanup_vault(os.path.join(PROJECT_ROOT, 'data', 'vault'), start_date, end_date)
    
    # 更新 sync_status.json
    update_sync_status(os.path.join(PROJECT_ROOT, 'data', 'sync_status.json'), start_date, end_date)
    
    # 清理 series_registry.json
    cleanup_series_registry(os.path.join(PROJECT_ROOT, 'data', 'series_registry.json'), start_date, end_date)
    
    print(f"\n{'='*60}")
    print("  ✅ 清理完成！")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()

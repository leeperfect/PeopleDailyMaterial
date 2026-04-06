#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理本地数据脚本

功能：
1. 保留 2026-01-01 至 2026-01-09 的数据
2. 删除其他日期的文章数据
3. 更新同步状态和系列注册表
"""

import os
import json
import shutil
from datetime import datetime, timedelta


def get_date_from_filename(filename):
    """从文件名中提取日期字符串 (YYYYMMDD 格式)"""
    # 文件名格式: articles_YYYYMMDD.json
    if filename.startswith('articles_') and filename.endswith('.json'):
        date_part = filename[9:17]  # articles_YYYYMMDD.json
        return date_part
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
    if not os.path.exists(directory):
        return
    
    deleted_count = 0
    kept_count = 0
    
    for filename in os.listdir(directory):
        if not filename.startswith('articles_') or not filename.endswith('.json'):
            continue
        
        date_str = get_date_from_filename(filename)
        if not date_str:
            continue
        
        if is_date_in_range(date_str, start_date, end_date):
            kept_count += 1
        else:
            file_path = os.path.join(directory, filename)
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
    if not os.path.exists(directory):
        return
    
    deleted_count = 0
    kept_count = 0
    
    # 遍历年份目录
    for year_dir in os.listdir(directory):
        year_path = os.path.join(directory, year_dir)
        if not os.path.isdir(year_path):
            continue
        
        # 遍历月份目录
        for month_dir in os.listdir(year_path):
            month_path = os.path.join(year_path, month_dir)
            if not os.path.isdir(month_path):
                continue
            
            # 遍历日期目录
            for date_dir in os.listdir(month_path):
                date_path = os.path.join(month_path, date_dir)
                if not os.path.isdir(date_path):
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
    print("=" * 60)
    print("  🗑️  本地数据清理工具")
    print("=" * 60)
    
    # 定义保留的日期范围
    start_date = datetime(2026, 1, 1)
    end_date = datetime(2026, 1, 9)
    
    print(f"\n保留日期范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    print("\n开始清理...\n")
    
    # 清理 raw 目录
    cleanup_json_files('data/raw', start_date, end_date)
    
    # 清理 processed 目录
    cleanup_json_files('data/processed', start_date, end_date)
    
    # 清理 vault 目录
    cleanup_vault('data/vault', start_date, end_date)
    
    # 更新 sync_status.json
    update_sync_status('data/sync_status.json', start_date, end_date)
    
    # 清理 series_registry.json
    cleanup_series_registry('data/series_registry.json', start_date, end_date)
    
    print(f"\n{'='*60}")
    print("  ✅ 清理完成！")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()

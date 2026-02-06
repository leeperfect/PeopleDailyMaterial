#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据导出模块
"""

import os
import json
import csv
import logging
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
from modules.utils import ensure_directory, safe_json_dump


class DataExporter:
    """数据导出类"""
    def __init__(self, config: Dict):
        self.config = config
        self.export_dir = self.config.get('export.dir', 'data/exports')
        ensure_directory(self.export_dir)
    
    def export_to_json(self, articles: List[Dict], filename: Optional[str] = None) -> str:
        """导出为JSON格式"""
        try:
            if not filename:
                filename = f"articles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            filepath = os.path.join(self.export_dir, filename)
            
            # 确保目录存在
            ensure_directory(os.path.dirname(filepath))
            
            # 导出数据
            success = safe_json_dump(articles, filepath)
            if success:
                logging.info(f"成功导出 {len(articles)} 篇文章到 {filepath}")
                return filepath
            else:
                logging.error("导出JSON失败")
                return ""
        except Exception as e:
            logging.error(f"导出JSON失败: {str(e)}")
            return ""
    
    def export_to_csv(self, articles: List[Dict], filename: Optional[str] = None) -> str:
        """导出为CSV格式"""
        try:
            if not filename:
                filename = f"articles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            filepath = os.path.join(self.export_dir, filename)
            
            # 确保目录存在
            ensure_directory(os.path.dirname(filepath))
            
            # 转换为DataFrame
            df = pd.DataFrame(articles)
            
            # 导出数据
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            logging.info(f"成功导出 {len(articles)} 篇文章到 {filepath}")
            return filepath
        except Exception as e:
            logging.error(f"导出CSV失败: {str(e)}")
            return ""
    
    def export_to_excel(self, articles: List[Dict], filename: Optional[str] = None) -> str:
        """导出为Excel格式"""
        try:
            if not filename:
                filename = f"articles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            filepath = os.path.join(self.export_dir, filename)
            
            # 确保目录存在
            ensure_directory(os.path.dirname(filepath))
            
            # 转换为DataFrame
            df = pd.DataFrame(articles)
            
            # 导出数据
            df.to_excel(filepath, index=False)
            
            logging.info(f"成功导出 {len(articles)} 篇文章到 {filepath}")
            return filepath
        except Exception as e:
            logging.error(f"导出Excel失败: {str(e)}")
            return ""
    
    def export_for_claude(self, articles: List[Dict], filename: Optional[str] = None) -> str:
        """导出为Claude Skill使用的格式"""
        try:
            if not filename:
                filename = f"claude_articles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            filepath = os.path.join(self.export_dir, filename)
            
            # 确保目录存在
            ensure_directory(os.path.dirname(filepath))
            
            # 转换为Claude格式
            claude_data = []
            for article in articles:
                claude_item = {
                    'title': article.get('title', ''),
                    'content': article.get('content', ''),
                    'url': article.get('url', ''),
                    'date': article.get('date', ''),
                    'category': article.get('category', ''),
                    'keywords': article.get('keywords', []),
                    'summary': article.get('summary', '')
                }
                claude_data.append(claude_item)
            
            # 导出数据
            success = safe_json_dump(claude_data, filepath)
            if success:
                logging.info(f"成功导出 {len(articles)} 篇文章到 {filepath} (Claude格式)")
                return filepath
            else:
                logging.error("导出Claude格式失败")
                return ""
        except Exception as e:
            logging.error(f"导出Claude格式失败: {str(e)}")
            return ""

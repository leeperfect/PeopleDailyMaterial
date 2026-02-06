#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据处理模块
"""

import logging
import re
import jieba
import jieba.analyse
from typing import List, Dict, Optional


class DataProcessor:
    """数据处理类"""
    def __init__(self):
        pass
    
    def clean_content(self, content: str) -> str:
        """清洗内容"""
        # 去除多余空白字符
        content = '\n'.join([line.strip() for line in content.split('\n') if line.strip()])
        # 去除特殊字符
        content = re.sub(r'[\r\t]+', '', content)
        # 去除多余的换行
        content = re.sub(r'\n{3,}', '\n\n', content)
        return content
    
    def detect_duplicate(self, article: Dict, existing_articles: List[Dict]) -> Optional[Dict]:
        """检测重复"""
        # URL精确匹配
        for existing in existing_articles:
            if existing.get('url') == article.get('url'):
                return existing
        
        # 标题+日期模糊匹配
        article_title = article.get('title', '').strip()
        article_date = article.get('date', '')
        if article_title and article_date:
            for existing in existing_articles:
                existing_title = existing.get('title', '').strip()
                existing_date = existing.get('date', '')
                if existing_title == article_title and existing_date == article_date:
                    return existing
        
        return None
    
    def detect_content_change(self, article: Dict, existing_article: Dict) -> bool:
        """检测内容变化"""
        return article.get('content', '') != existing_article.get('content', '')
    
    def extract_keywords(self, text: str, topK: int = 10) -> List[str]:
        """提取关键词"""
        try:
            keywords = jieba.analyse.extract_tags(text, topK=topK, withWeight=False)
            return keywords
        except Exception as e:
            logging.error(f"提取关键词失败: {str(e)}")
            return []
    
    def extract_summary(self, text: str, sentences: int = 3) -> str:
        """提取摘要"""
        try:
            # 简单的摘要提取，取前几个句子
            lines = text.split('\n')
            summary_lines = lines[:sentences]
            summary = '\n'.join(summary_lines)
            return summary
        except Exception as e:
            logging.error(f"提取摘要失败: {str(e)}")
            return ""
    
    def classify_article(self, article: Dict) -> str:
        """文章分类"""
        # 简单的分类逻辑，基于版面名称和关键词
        plate = article.get('plate', '').lower()
        content = article.get('content', '')
        title = article.get('title', '')
        
        # 政治类
        political_keywords = ['政策', '政府', '国家', '政治', '党建', '总书记', '主席', '总理']
        for keyword in political_keywords:
            if keyword in title or keyword in content:
                return '政治'
        
        # 经济类
        economic_keywords = ['经济', '金融', '市场', '企业', '贸易', '投资', 'GDP', '财政']
        for keyword in economic_keywords:
            if keyword in title or keyword in content:
                return '经济'
        
        # 社会类
        social_keywords = ['社会', '民生', '教育', '医疗', '住房', '就业', '社保', '环保']
        for keyword in social_keywords:
            if keyword in title or keyword in content:
                return '社会'
        
        # 国际类
        international_keywords = ['国际', '外交', '外国', '全球', '世界', '合作', '关系']
        for keyword in international_keywords:
            if keyword in title or keyword in content:
                return '国际'
        
        # 文化类
        cultural_keywords = ['文化', '艺术', '体育', '教育', '科技', '历史', '传统']
        for keyword in cultural_keywords:
            if keyword in title or keyword in content:
                return '文化'
        
        # 默认分类
        if '评论' in plate or '理论' in plate:
            return '评论'
        elif '经济' in plate:
            return '经济'
        elif '国际' in plate:
            return '国际'
        elif '社会' in plate:
            return '社会'
        elif '文化' in plate:
            return '文化'
        else:
            return '其他'

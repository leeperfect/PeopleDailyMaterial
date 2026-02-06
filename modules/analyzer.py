#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据分析模块
"""

import os
import logging
import jieba
import jieba.analyse
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns


class HotTopicAnalyzer:
    """热点话题分析器"""
    def __init__(self, config: Dict):
        self.config = config
        self.vectorizer = TfidfVectorizer()
    
    def analyze_keywords(self, articles: List[Dict], topK: int = 20) -> List[Tuple[str, int]]:
        """分析关键词热度"""
        try:
            # 提取所有文章的关键词
            all_keywords = []
            for article in articles:
                content = article.get('content', '')
                title = article.get('title', '')
                text = title + ' ' + content
                keywords = jieba.analyse.extract_tags(text, topK=10, withWeight=False)
                all_keywords.extend(keywords)
            
            # 统计关键词频率
            keyword_freq = {}
            for keyword in all_keywords:
                keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
            
            # 排序
            sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:topK]
            
            return sorted_keywords
        except Exception as e:
            logging.error(f"分析关键词热度失败: {str(e)}")
            return []
    
    def predict_hot_topics(self, articles: List[Dict], days: int = 7) -> List[Dict]:
        """预测热点话题"""
        try:
            # 按日期分组
            date_groups = {}
            for article in articles:
                date = article.get('date', '')
                if date:
                    if date not in date_groups:
                        date_groups[date] = []
                    date_groups[date].append(article)
            
            # 分析每天的关键词热度
            daily_keywords = {}
            for date, date_articles in date_groups.items():
                keywords = self.analyze_keywords(date_articles, topK=10)
                daily_keywords[date] = keywords
            
            # 预测热点
            hot_topics = []
            for date, keywords in daily_keywords.items():
                for keyword, freq in keywords[:5]:  # 取每天前5个关键词
                    topic = {
                        'keyword': keyword,
                        'frequency': freq,
                        'date': date,
                        'score': self.calculate_hot_score(keyword, freq, date, daily_keywords)
                    }
                    hot_topics.append(topic)
            
            # 排序
            hot_topics.sort(key=lambda x: x['score'], reverse=True)
            
            return hot_topics[:10]  # 返回前10个热点话题
        except Exception as e:
            logging.error(f"预测热点话题失败: {str(e)}")
            return []
    
    def calculate_hot_score(self, keyword: str, freq: int, date: str, daily_keywords: Dict) -> float:
        """计算热点评分"""
        # 基础分数
        base_score = freq
        
        # 时间衰减因子
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        today = datetime.now().date()
        days_diff = (today - date_obj.date()).days
        time_factor = max(0.1, 1.0 - days_diff * 0.1)
        
        # 趋势因子
        trend_factor = 1.0
        dates = sorted(daily_keywords.keys())
        if date in dates:
            date_idx = dates.index(date)
            if date_idx > 0:
                prev_date = dates[date_idx - 1]
                prev_keywords = dict(daily_keywords.get(prev_date, []))
                prev_freq = prev_keywords.get(keyword, 0)
                if prev_freq > 0:
                    trend_factor = freq / prev_freq
        
        # 综合评分
        score = base_score * time_factor * trend_factor
        
        return score
    
    def cluster_articles(self, articles: List[Dict], n_clusters: int = 5) -> List[Dict]:
        """文章聚类"""
        try:
            # 提取文本
            texts = []
            article_ids = []
            for i, article in enumerate(articles):
                content = article.get('content', '')
                title = article.get('title', '')
                text = title + ' ' + content
                texts.append(text)
                article_ids.append(i)
            
            # 向量化
            X = self.vectorizer.fit_transform(texts)
            
            # 聚类
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(X)
            
            # 结果
            cluster_result = {}
            for i, cluster_id in enumerate(clusters):
                if cluster_id not in cluster_result:
                    cluster_result[cluster_id] = []
                cluster_result[cluster_id].append(articles[article_ids[i]])
            
            # 分析每个聚类的主题
            cluster_topics = []
            for cluster_id, cluster_articles in cluster_result.items():
                keywords = self.analyze_keywords(cluster_articles, topK=5)
                topic = {
                    'cluster_id': cluster_id,
                    'size': len(cluster_articles),
                    'keywords': [kw[0] for kw in keywords],
                    'articles': cluster_articles[:3]  # 每个聚类取3篇文章作为示例
                }
                cluster_topics.append(topic)
            
            return cluster_topics
        except Exception as e:
            logging.error(f"文章聚类失败: {str(e)}")
            return []


class PolicyAnalyzer:
    """政策分析器"""
    def __init__(self, config: Dict):
        self.config = config
    
    def analyze_policy_trends(self, articles: List[Dict]) -> List[Dict]:
        """分析政策趋势"""
        try:
            # 筛选政策相关文章
            policy_articles = []
            policy_keywords = ['政策', '法规', '条例', '办法', '意见', '通知', '决定', '规划']
            
            for article in articles:
                title = article.get('title', '')
                content = article.get('content', '')
                text = title + ' ' + content
                
                for keyword in policy_keywords:
                    if keyword in text:
                        policy_articles.append(article)
                        break
            
            # 按日期分组
            date_groups = {}
            for article in policy_articles:
                date = article.get('date', '')
                if date:
                    if date not in date_groups:
                        date_groups[date] = []
                    date_groups[date].append(article)
            
            # 分析趋势
            trends = []
            for date, date_articles in date_groups.items():
                trend = {
                    'date': date,
                    'policy_count': len(date_articles),
                    'articles': date_articles
                }
                trends.append(trend)
            
            # 排序
            trends.sort(key=lambda x: x['date'], reverse=True)
            
            return trends
        except Exception as e:
            logging.error(f"分析政策趋势失败: {str(e)}")
            return []
    
    def analyze_policy_impact(self, article: Dict) -> Dict:
        """分析政策影响"""
        try:
            content = article.get('content', '')
            title = article.get('title', '')
            
            # 简单的影响分析
            impact_keywords = {
                '经济': ['经济', '发展', '增长', '企业', '市场'],
                '社会': ['社会', '民生', '教育', '医疗', '就业'],
                '环境': ['环境', '环保', '绿色', '生态', '可持续'],
                '科技': ['科技', '创新', '技术', '数字', '智能'],
                '国际': ['国际', '外交', '合作', '全球', '贸易']
            }
            
            impact_scores = {}
            for category, keywords in impact_keywords.items():
                score = 0
                for keyword in keywords:
                    if keyword in content or keyword in title:
                        score += 1
                impact_scores[category] = score
            
            # 主要影响领域
            main_impact = max(impact_scores.items(), key=lambda x: x[1])
            
            return {
                'article_title': title,
                'impact_scores': impact_scores,
                'main_impact': main_impact[0] if main_impact[1] > 0 else '无明显影响',
                'impact_level': self.calculate_impact_level(impact_scores)
            }
        except Exception as e:
            logging.error(f"分析政策影响失败: {str(e)}")
            return {}
    
    def calculate_impact_level(self, impact_scores: Dict) -> str:
        """计算影响程度"""
        total_score = sum(impact_scores.values())
        if total_score >= 10:
            return '高'
        elif total_score >= 5:
            return '中'
        else:
            return '低'

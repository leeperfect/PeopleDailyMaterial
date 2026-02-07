#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人民日报爬虫与Notion存储脚本

功能：
1. 每日定时抓取人民日报网页版当天所有文章
2. 存储至Notion数据库
3. 支持日期范围查询
4. 实现防反爬机制
5. 数据去重和增量更新
6. 数据分析和热点预测
7. Claude Skill接口支持
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
from typing import List, Dict

# 导入模块
from modules.utils import Config, setup_logger, ensure_directory, safe_json_dump
from modules.crawler import PeopleDailyCrawler
from modules.parser import ContentParser
from modules.processor import DataProcessor
from modules.notion import NotionAPI
from modules.exporter import DataExporter
from modules.analyzer import HotTopicAnalyzer, PolicyAnalyzer


class PeopleDailyMaterialSystem:
    """人民日报素材系统"""
    def __init__(self):
        # 加载配置
        self.config = Config()
        
        # 初始化日志
        setup_logger(self.config)
        
        # 确保数据目录存在
        ensure_directory('data/raw')
        ensure_directory('data/processed')
        ensure_directory('data/exports')
        
        # 初始化模块
        self.crawler = PeopleDailyCrawler(self.config)
        self.parser = ContentParser()
        self.processor = DataProcessor()
        self.notion_api = NotionAPI(self.config)
        self.exporter = DataExporter(self.config.get('export', {}))
        self.hot_topic_analyzer = HotTopicAnalyzer(self.config.get('analyzer', {}))
        self.policy_analyzer = PolicyAnalyzer(self.config.get('analyzer', {}))
    
    def crawl_single_date(self, date: datetime):
        """抓取单个日期的文章"""
        logging.info(f"开始抓取 {date.strftime('%Y-%m-%d')} 的人民日报文章")
        
        # 抓取目录页
        result = self.crawler.crawl_directory(date)
        if not result:
            logging.error(f"无法获取目录页")
            return []
        
        url, html = result
        logging.info(f"目录页URL: {url}")
        
        # 解析目录页
        articles_info = self.parser.parse_directory(html)
        logging.info(f"找到 {len(articles_info)} 篇文章")
        
        # 获取已存在的文章
        existing_articles = self.notion_api.get_existing_articles()
        
        # 处理每篇文章
        processed_articles = []
        for article_info in articles_info:
            # 构建完整URL
            if article_info['href'].startswith('http'):
                # 完整URL，直接使用
                article_url = article_info['href']
            else:
                # 相对路径，构建完整URL
                # 从目录页URL中提取日期信息
                url_parts = url.split('/')
                if len(url_parts) >= 8:
                    # 目录页URL格式: https://paper.people.com.cn/rmrb/pc/layout/202602/08/node_01.html
                    year_month = url_parts[-3]  # 202602
                    day = url_parts[-2]       # 08
                    # 构建正确的内容URL
                    article_url = f"https://paper.people.com.cn/rmrb/pc/content/{year_month}/{day}/{article_info['href']}"
                else:
                    # 回退到原始方法
                    base_url = url.rsplit('/', 1)[0]  # 提取基础URL
                    article_url = f"{base_url}/{article_info['href']}"
            
            # 抓取文章页
            article_html = self.crawler.crawl_article(article_url)
            if not article_html:
                logging.error(f"无法获取文章: {article_url}")
                continue
            
            # 解析文章
            article = self.parser.parse_article(article_html, article_url)
            if not article:
                logging.error(f"无法解析文章: {article_url}")
                continue
            
            # 处理文章
            article['content'] = self.processor.clean_content(article['content'])
            article['date'] = date.strftime('%Y-%m-%d')
            article['keywords'] = self.processor.extract_keywords(article['content'] + ' ' + article['title'])
            article['summary'] = self.processor.extract_summary(article['content'])
            article['category'] = self.processor.classify_article(article)
            
            # 检测重复
            duplicate = self.processor.detect_duplicate(article, existing_articles)
            if duplicate:
                # 检测内容变化
                if self.processor.detect_content_change(article, duplicate):
                    logging.info(f"文章内容发生变化，更新: {article['title']}")
                    self.notion_api.update_page(duplicate['id'], article)
                else:
                    logging.info(f"文章已存在，跳过: {article['title']}")
            else:
                logging.info(f"创建新文章: {article['title']}")
                self.notion_api.create_page(article, date)
            
            processed_articles.append(article)
        
        # 保存本地
        self.save_articles_local(processed_articles, date)
        
        # 导出数据
        self.export_articles(processed_articles, date)
        
        # 分析数据
        self.analyze_articles(processed_articles, date)
        
        return processed_articles
    
    def crawl_date_range(self, start_date: datetime, end_date: datetime):
        """抓取日期范围内的文章"""
        all_articles = []
        current_date = start_date
        while current_date <= end_date:
            articles = self.crawl_single_date(current_date)
            all_articles.extend(articles)
            current_date += timedelta(days=1)
        
        # 导出汇总数据
        if all_articles:
            self.export_articles(all_articles, start_date, end_date)
            self.analyze_articles(all_articles, start_date, end_date)
        
        return all_articles
    
    def save_articles_local(self, articles: List[Dict], date: datetime):
        """保存文章到本地"""
        try:
            # 保存原始数据
            raw_file = f"data/raw/articles_{date.strftime('%Y%m%d')}.json"
            safe_json_dump(articles, raw_file)
            logging.info(f"成功保存 {len(articles)} 篇文章到本地")
            
            # 保存处理后的数据
            processed_file = f"data/processed/articles_{date.strftime('%Y%m%d')}.json"
            processed_articles = []
            for article in articles:
                processed_article = {
                    'title': article.get('title', ''),
                    'url': article.get('url', ''),
                    'date': article.get('date', ''),
                    'category': article.get('category', ''),
                    'keywords': article.get('keywords', []),
                    'summary': article.get('summary', ''),
                    'plate': article.get('plate', '')
                }
                processed_articles.append(processed_article)
            safe_json_dump(processed_articles, processed_file)
        except Exception as e:
            logging.error(f"保存文章到本地失败: {str(e)}")
    
    def export_articles(self, articles: List[Dict], start_date: datetime, end_date: Optional[datetime] = None):
        """导出文章"""
        if not articles:
            return
        
        # 导出为JSON
        if end_date:
            filename = f"articles_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
        else:
            filename = f"articles_{start_date.strftime('%Y%m%d')}.json"
        self.exporter.export_to_json(articles, filename)
        
        # 导出为CSV
        if end_date:
            filename = f"articles_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
        else:
            filename = f"articles_{start_date.strftime('%Y%m%d')}.csv"
        self.exporter.export_to_csv(articles, filename)
        
        # 导出为Claude格式
        if end_date:
            filename = f"claude_articles_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
        else:
            filename = f"claude_articles_{start_date.strftime('%Y%m%d')}.json"
        self.exporter.export_for_claude(articles, filename)
    
    def analyze_articles(self, articles: List[Dict], start_date: datetime, end_date: Optional[datetime] = None):
        """分析文章"""
        if not articles:
            return
        
        # 分析热点话题
        hot_topics = self.hot_topic_analyzer.predict_hot_topics(articles)
        logging.info(f"预测到 {len(hot_topics)} 个热点话题")
        
        # 保存热点话题
        if end_date:
            filename = f"hot_topics_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
        else:
            filename = f"hot_topics_{start_date.strftime('%Y%m%d')}.json"
        safe_json_dump(hot_topics, f"data/processed/{filename}")
        
        # 分析政策趋势
        policy_trends = self.policy_analyzer.analyze_policy_trends(articles)
        logging.info(f"分析到 {len(policy_trends)} 条政策趋势")
        
        # 保存政策趋势
        if end_date:
            filename = f"policy_trends_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
        else:
            filename = f"policy_trends_{start_date.strftime('%Y%m%d')}.json"
        safe_json_dump(policy_trends, f"data/processed/{filename}")
        
        # 文章聚类
        clusters = self.hot_topic_analyzer.cluster_articles(articles)
        logging.info(f"文章聚类为 {len(clusters)} 个主题")
        
        # 保存聚类结果
        if end_date:
            filename = f"article_clusters_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
        else:
            filename = f"article_clusters_{start_date.strftime('%Y%m%d')}.json"
        safe_json_dump(clusters, f"data/processed/{filename}")


# 修复类型注解
from typing import Optional


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='人民日报爬虫与Notion存储脚本')
    parser.add_argument('--date-range', nargs=2, metavar=('START_DATE', 'END_DATE'),
                        help='日期范围，格式: YYYY-MM-DD YYYY-MM-DD')
    parser.add_argument('--date', metavar='DATE',
                        help='单个日期，格式: YYYY-MM-DD')
    parser.add_argument('--export', action='store_true',
                        help='导出数据')
    parser.add_argument('--analyze', action='store_true',
                        help='分析数据')
    
    args = parser.parse_args()
    
    # 初始化系统
    system = PeopleDailyMaterialSystem()
    
    # 处理命令行参数
    if args.date_range:
        try:
            start_date = datetime.strptime(args.date_range[0], '%Y-%m-%d')
            end_date = datetime.strptime(args.date_range[1], '%Y-%m-%d')
            system.crawl_date_range(start_date, end_date)
        except ValueError:
            logging.error("日期格式错误，请使用 YYYY-MM-DD 格式")
            sys.exit(1)
    elif args.date:
        try:
            date = datetime.strptime(args.date, '%Y-%m-%d')
            system.crawl_single_date(date)
        except ValueError:
            logging.error("日期格式错误，请使用 YYYY-MM-DD 格式")
            sys.exit(1)
    else:
        # 默认抓取当天
        today = datetime.now()
        system.crawl_single_date(today)


if __name__ == '__main__':
    main()

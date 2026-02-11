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
from modules.series_detector import SeriesDetector


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
        self.series_detector = SeriesDetector()
    
    def crawl_single_date(self, date: datetime):
        """抓取单个日期的文章（交互式：浏览器界面选择下载）"""
        logging.info(f"开始抓取 {date.strftime('%Y-%m-%d')} 的人民日报文章")
        
        # ====== 第一步：抓取所有版面目录 ======
        print(f"\n{'='*60}")
        print(f"  📰 人民日报 {date.strftime('%Y-%m-%d')} 版面目录")
        print(f"{'='*60}")
        print("正在获取版面目录，请稍候...\n")
        
        directories = self.crawler.crawl_all_directories(date)
        if not directories:
            logging.error("无法获取目录页")
            return []
        
        # 解析所有版面目录，按版面分组
        import re
        all_articles_info = []
        articles_by_section = []
        article_index = 1
        
        for url, html in directories:
            articles_info, section_name = self.parser.parse_directory(html)
            
            node_match = re.search(r'node_(\d+)', url)
            node_id = node_match.group(1) if node_match else '??'
            
            if not articles_info:
                continue
            
            section_articles = []
            skip_titles = ['图片报道', '导读', '征集', '本版责编', '一版责编']
            
            for article in articles_info:
                article['source_url'] = url
                article['index'] = article_index
                article['section_id'] = node_id
                article['section_name'] = section_name or f'第{node_id}版'
                article['auto_skip'] = any(skip in article.get('title', '') for skip in skip_titles)
                
                all_articles_info.append(article)
                section_articles.append(article)
                article_index += 1
            
            articles_by_section.append({
                'section_id': node_id,
                'section_name': section_name or f'第{node_id}版',
                'articles': section_articles
            })
        
        total = len(all_articles_info)
        available = len([a for a in all_articles_info if not a.get('auto_skip')])
        print(f"  ✅ 获取完成：{len(articles_by_section)} 个版面，{total} 篇文章（{available} 篇可选）")
        
        # ====== 系列文章检测 ======
        self.series_detector.detect_and_register(all_articles_info)
        series_summary = self.series_detector.get_summary()
        if '检测到' in series_summary:
            print(f"\n  {series_summary}")
        
        # ====== 第二步：打开浏览器选择 ======
        from modules.web_selector import ArticleSelector
        selector = ArticleSelector(date.strftime('%Y-%m-%d'), articles_by_section)
        selected_indices = selector.show_and_wait()
        
        # 处理手动编组
        for group in selector.manual_groups:
            self.series_detector.manual_group(
                all_articles_info, group['name'], group['article_indices']
            )
        
        # 过滤出用户选择的文章
        selected_articles = [a for a in all_articles_info if a['index'] in selected_indices]
        
        if not selected_articles:
            print("\n未选择任何文章，退出。")
            return []
        
        print(f"\n✅ 已选择 {len(selected_articles)} 篇文章，开始下载...\n")
        
        # ====== 第三步：下载选中的文章 ======
        from modules.markdown_writer import MarkdownWriter
        md_writer = MarkdownWriter()
        md_saved_count = 0
        
        existing_articles = self.notion_api.get_existing_articles()
        processed_articles = []
        
        for i, article_info in enumerate(selected_articles, 1):
            # 构建完整URL
            source_url = article_info.get('source_url', '')
            url_parts = source_url.split('/')
            if len(url_parts) >= 8:
                year_month = url_parts[-3]
                day = url_parts[-2]
                article_url = f"https://paper.people.com.cn/rmrb/pc/content/{year_month}/{day}/{article_info['href']}"
            else:
                base_url = source_url.rsplit('/', 1)[0]
                article_url = f"{base_url}/{article_info['href']}"
            
            print(f"  [{i}/{len(selected_articles)}] 正在下载: {article_info['title'][:40]}...")
            
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
            
            # 传递系列信息
            article['series_id'] = article_info.get('series_id')
            article['series_name'] = article_info.get('series_name')
            article['series_part'] = article_info.get('series_part')
            article['related_titles'] = self.series_detector.get_related_titles(article_info)
            
            # 检测重复
            duplicate = self.processor.detect_duplicate(article, existing_articles)
            if duplicate:
                if self.processor.detect_content_change(article, duplicate):
                    logging.info(f"文章内容发生变化，更新: {article['title']}")
                    self.notion_api.update_page(duplicate['id'], article)
                else:
                    logging.info(f"文章已存在，跳过: {article['title']}")
            else:
                logging.info(f"创建新文章: {article['title']}")
                self.notion_api.create_page(article, date)
            
            # 保存 Markdown 文件
            md_path = md_writer.save_article(
                article, date,
                section_id=article_info.get('section_id', ''),
                section_name=article_info.get('section_name', '')
            )
            if md_path:
                md_saved_count += 1
            
            processed_articles.append(article)
            print(f"         ✅ 完成")
        
        # 保存系列注册表
        self.series_detector.save_registry()
        
        # 保存本地
        self.save_articles_local(processed_articles, date)
        
        # 导出数据
        self.export_articles(processed_articles, date)
        
        print(f"\n{'='*60}")
        print(f"  🎉 下载完成！共处理 {len(processed_articles)} 篇文章")
        print(f"  📁 Markdown 已保存 {md_saved_count} 篇到 data/vault/")
        print(f"{'='*60}\n")
        
        return processed_articles
    
    def crawl_date_range(self, start_date: datetime, end_date: datetime):
        """抓取日期范围内的文章（多日合并展示，一次性选择）"""
        import re
        logging.info(f"开始抓取日期范围: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        
        # ====== 第一步：预先获取所有日期的目录 ======
        all_articles_info = []   # 所有文章的平铺列表
        dates_info = []          # 按日期分组（给 web_selector 用）
        article_index = 1
        
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            print(f"\n{'='*60}")
            print(f"  📰 人民日报 {date_str} 版面目录")
            print(f"{'='*60}")
            print("正在获取版面目录，请稍候...\n")
            
            directories = self.crawler.crawl_all_directories(current_date)
            if not directories:
                logging.error(f"无法获取 {date_str} 的目录页")
                current_date += timedelta(days=1)
                continue
            
            articles_by_section = []
            skip_titles = ['图片报道', '导读', '征集', '本版责编', '一版责编']
            
            for url, html in directories:
                articles_info, section_name = self.parser.parse_directory(html)
                node_match = re.search(r'node_(\d+)', url)
                node_id = node_match.group(1) if node_match else '??'
                
                if not articles_info:
                    continue
                
                section_articles = []
                for article in articles_info:
                    article['source_url'] = url
                    article['index'] = article_index
                    article['section_id'] = node_id
                    article['section_name'] = section_name or f'第{node_id}版'
                    article['auto_skip'] = any(skip in article.get('title', '') for skip in skip_titles)
                    article['_date'] = current_date  # 记录所属日期
                    
                    all_articles_info.append(article)
                    section_articles.append(article)
                    article_index += 1
                
                articles_by_section.append({
                    'section_id': node_id,
                    'section_name': section_name or f'第{node_id}版',
                    'articles': section_articles
                })
            
            total = len([a for a in all_articles_info if a['_date'] == current_date])
            available = len([a for a in all_articles_info if a['_date'] == current_date and not a.get('auto_skip')])
            print(f"  ✅ 获取完成：{len(articles_by_section)} 个版面，{total} 篇文章（{available} 篇可选）")
            
            dates_info.append({
                'date_str': date_str,
                'articles_by_section': articles_by_section
            })
            current_date += timedelta(days=1)
        
        if not dates_info:
            print("\n未获取到任何文章目录，退出。")
            return []
        
        # ====== 系列文章检测 ======
        self.series_detector.detect_and_register(all_articles_info)
        series_summary = self.series_detector.get_summary()
        if '检测到' in series_summary:
            print(f"\n  {series_summary}")
        
        # ====== 第二步：统一展示选择器（所有日期合并为一页） ======
        from modules.web_selector import ArticleSelector
        selector = ArticleSelector(dates_info=dates_info)
        selected_indices = selector.show_and_wait()
        
        # 处理手动编组
        for group in selector.manual_groups:
            self.series_detector.manual_group(
                all_articles_info, group['name'], group['article_indices']
            )
        
        selected_articles = [a for a in all_articles_info if a['index'] in selected_indices]
        
        if not selected_articles:
            print("\n未选择任何文章，退出。")
            return []
        
        print(f"\n✅ 已选择 {len(selected_articles)} 篇文章，开始下载...\n")
        
        # ====== 第三步：批量下载选中的文章 ======
        from modules.markdown_writer import MarkdownWriter
        md_writer = MarkdownWriter()
        md_saved_count = 0
        
        existing_articles = self.notion_api.get_existing_articles()
        processed_articles = []
        
        for i, article_info in enumerate(selected_articles, 1):
            date = article_info['_date']  # 使用文章所属的日期
            
            # 构建完整URL
            source_url = article_info.get('source_url', '')
            url_parts = source_url.split('/')
            if len(url_parts) >= 8:
                year_month = url_parts[-3]
                day = url_parts[-2]
                article_url = f"https://paper.people.com.cn/rmrb/pc/content/{year_month}/{day}/{article_info['href']}"
            else:
                base_url = source_url.rsplit('/', 1)[0]
                article_url = f"{base_url}/{article_info['href']}"
            
            print(f"  [{i}/{len(selected_articles)}] ({date.strftime('%m-%d')}) 正在下载: {article_info['title'][:40]}...")
            
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
            
            # 传递系列信息
            article['series_id'] = article_info.get('series_id')
            article['series_name'] = article_info.get('series_name')
            article['series_part'] = article_info.get('series_part')
            article['related_titles'] = self.series_detector.get_related_titles(article_info)
            
            # 检测重复
            duplicate = self.processor.detect_duplicate(article, existing_articles)
            if duplicate:
                if self.processor.detect_content_change(article, duplicate):
                    logging.info(f"文章内容发生变化，更新: {article['title']}")
                    self.notion_api.update_page(duplicate['id'], article)
                else:
                    logging.info(f"文章已存在，跳过: {article['title']}")
            else:
                logging.info(f"创建新文章: {article['title']}")
                self.notion_api.create_page(article, date)
            
            # 保存 Markdown 文件
            md_path = md_writer.save_article(
                article, date,
                section_id=article_info.get('section_id', ''),
                section_name=article_info.get('section_name', '')
            )
            if md_path:
                md_saved_count += 1
            
            processed_articles.append(article)
            print(f"         ✅ 完成")
        
        # 保存系列注册表
        self.series_detector.save_registry()
        
        # 按日期分组保存本地数据
        from collections import defaultdict
        by_date = defaultdict(list)
        for art in processed_articles:
            by_date[art['date']].append(art)
        for d_str, arts in by_date.items():
            dt = datetime.strptime(d_str, '%Y-%m-%d')
            self.save_articles_local(arts, dt)
        
        # 导出汇总数据
        if processed_articles:
            self.export_articles(processed_articles, start_date, end_date)
        
        print(f"\n{'='*60}")
        print(f"  🎉 全部完成！共处理 {len(processed_articles)} 篇文章")
        print(f"  📁 Markdown 已保存 {md_saved_count} 篇到 data/vault/")
        print(f"{'='*60}\n")
        
        return processed_articles
    
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
    
    args = parser.parse_args()
    
    # 初始化系统
    system = PeopleDailyMaterialSystem()
    
    try:
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
    finally:
        # 确保关闭浏览器
        system.crawler.close()
        logging.info("程序结束，浏览器已关闭")


if __name__ == '__main__':
    main()

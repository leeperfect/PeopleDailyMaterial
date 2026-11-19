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

import sys
import logging
import json
from pathlib import Path
from collections import defaultdict
import argparse
import subprocess
import platform
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# 导入模块
from modules.utils import Config, setup_logger, ensure_directory, safe_json_dump
from modules.crawler import PeopleDailyCrawler
from modules.parser import ContentParser
from modules.processor import DataProcessor
from modules.notion import NotionAPI
from modules.exporter import DataExporter
from modules.series_detector import SeriesDetector
from modules.date_selector import mark_date_synced
from modules.checkpoint import Checkpoint
from modules.article_database import ArticleStore
from modules.article_identity import build_article_id
from modules.notion_index import AmbiguousArticleMatch, build_existing_indexes, find_duplicate, add_to_indexes


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
        ensure_directory('data/core')
        
        # 初始化模块
        self.crawler = PeopleDailyCrawler(self.config)
        self.parser = ContentParser()
        self.processor = DataProcessor()
        self.notion_api = NotionAPI(self.config)
        self.exporter = DataExporter(self.config.get('export', {}))
        self.series_detector = SeriesDetector()
        self.article_store = ArticleStore()
    
    def crawl_single_date(self, date: datetime, auto_select: bool = False):
        """单日与跨日共用落盘、续传和同步判定。"""
        return self.crawl_date_range(date, date, auto_select=auto_select)

    def crawl_date_range(self, start_date: datetime, end_date: datetime, auto_select: bool = False, sync_after_download: bool = True):
        """抓取日期范围内的文章（多日合并展示，一次性选择）

        Args:
            start_date: 开始日期
            end_date: 结束日期
            auto_select: 是否自动选择所有可用文章
            sync_after_download: 是否在下载完成后统一同步到 Notion
        """
        import re
        logging.info(f"开始抓取日期范围: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        
        # ====== 第一步：预先获取所有日期的目录 ======
        if end_date < start_date:
            raise ValueError('结束日期不能早于开始日期')
        all_articles_info = []   # 所有文章的平铺列表
        dates_info = []          # 按日期分组（给 web_selector 用）
        article_index = 1
        
        failed_dates = set()
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            print(f"\n{'='*60}")
            print(f"  📰 人民日报 {date_str} 版面目录")
            print(f"{'='*60}")
            print("正在获取版面目录，请稍候...\n")
            
            directories = self.crawler.crawl_all_directories(current_date)
            if not directories:
                failed_dates.add(date_str)
                logging.error(f"无法获取 {date_str} 的目录页")
                current_date += timedelta(days=1)
                continue
            
            articles_by_section = []
            skip_titles = ['图片报道', '导读', '征集', '本版责编', '一版责编', '欢迎赐稿']
            
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
            
            total = sum(len(section['articles']) for section in articles_by_section)
            available = sum(not a['auto_skip'] for section in articles_by_section for a in section['articles'])
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
        
        if auto_select:
            selected_indices = {a['index'] for a in all_articles_info if not a.get('auto_skip')}
            print(f"\n  🤖 自动模式：已选择所有 {len(selected_indices)} 篇可用文章")
        else:
            # ====== 第二步：统一展示选择器（所有日期合并为一页） ======
            from modules.web_selector import ArticleSelector
            selector = ArticleSelector(**dates_info[0]) if start_date == end_date else ArticleSelector(dates_info=dates_info)
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

        # ====== 第三步：批量下载选中的文章（支持断点续传） ======
        from modules.markdown_writer import MarkdownWriter
        md_writer = MarkdownWriter()
        md_saved_count = 0

        # 初始化断点续传
        checkpoint = Checkpoint(start_date, end_date)
        if checkpoint.has_checkpoint():
            print(f"  🔄 发现未完成的任务（{checkpoint.get_summary()}），将自动跳过已完成文章")

        # 先下载所有文章，不立即同步到 Notion
        processed_articles = []
        download_failed = []
        recovered_by_date = {}
        pending = defaultdict(list)

        def flush_pending():
            for day, batch in pending.items():
                self.save_articles_local(batch, datetime.strptime(day, '%Y-%m-%d'))
                checkpoint.mark_batch_completed([a for a in batch if a.get('markdown_path')])
            pending.clear()

        skipped_count = 0

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

            # 断点续传：跳过已完成的文章
            day = date.strftime('%Y-%m-%d')
            if checkpoint.is_completed(article_url):
                # 旧版可能先记“已完成”而正文还只在内存里：必须查到原始资料才能跳过。
                if day not in recovered_by_date:
                    recovered_by_date[day] = {
                        (a.get('url') or a.get('source_url')): a for a in self._daily_raw(date)
                    }
                cached = recovered_by_date[day].get(article_url)
                if cached and cached.get('content') and Path(cached.get('markdown_path') or '').is_file():
                    article = dict(cached)
                    article.setdefault('article_id', build_article_id(article))
                    processed_articles.append(article)
                    skipped_count += 1
                    continue

            print(f"  [{i}/{len(selected_articles)}] ({date.strftime('%m-%d')}) 正在下载: {article_info['title'][:40]}...")

            # 抓取文章页
            article_html = self.crawler.crawl_article(article_url)
            if not article_html:
                logging.error(f"无法获取文章: {article_url}")
                failed_dates.add(day)
                download_failed.append(article_info['title'])
                checkpoint.mark_failed(article_url, article_info.get('title', ''), '无法获取页面')
                continue

            # 解析文章
            article = self.parser.parse_article(article_html, article_url)
            if not article:
                logging.error(f"无法解析文章: {article_url}")
                failed_dates.add(day)
                download_failed.append(article_info['title'])
                checkpoint.mark_failed(article_url, article_info.get('title', ''), '解析失败')
                continue

            # 处理文章
            article['content'] = self.processor.clean_content(article['content'])
            article['date'] = date.strftime('%Y-%m-%d')
            article['article_id'] = build_article_id(article)
            article['keywords'] = self.processor.extract_keywords(article['content'] + ' ' + article['title'])
            article['summary'] = self.processor.extract_summary(article['content'])
            article['category'] = self.processor.classify_article(article)

            # 传递系列信息
            article['series_id'] = article_info.get('series_id')
            article['series_int_id'] = article_info.get('series_int_id')
            article['series_name'] = article_info.get('series_name')
            article['series_part'] = article_info.get('series_part')
            article['related_titles'] = self.series_detector.get_related_titles(article_info)

            # 保存 Markdown 文件
            md_path = md_writer.save_article(
                article, date,
                section_id=article_info.get('section_id', ''),
                section_name=article_info.get('section_name', '')
            )
            if md_path:
                article['markdown_path'] = md_path
                md_saved_count += 1
            else:
                failed_dates.add(day)
                download_failed.append(article_info['title'])
                checkpoint.mark_failed(article_url, article_info.get('title', ''), '阅读视图未保存')
            article['section_no'] = article_info.get('section_id', '')
            article['section_name'] = article_info.get('section_name', '')

            processed_articles.append(article)
            
            pending[day].append(article)
            if len(pending[day]) >= 10 or i == len(selected_articles) or selected_articles[i]['_date'] != date:
                flush_pending()

        flush_pending()
        self.series_detector.save_registry()
        self.export_articles(processed_articles, start_date, end_date if end_date != start_date else None)

        print(f"\n{'='*60}")
        print(f"  📥 下载完成！共下载 {len(processed_articles)} 篇文章")
        if skipped_count > 0:
            print(f"  ⏭️ 断点续传跳过 {skipped_count} 篇已完成文章")
        print(f"  📁 Markdown 已保存 {md_saved_count} 篇到 data/vault/")
        if download_failed:
            print(f"  ⚠️ 下载失败 {len(download_failed)} 篇")
        print(f"{'='*60}\n")

        # ====== 第四步：统一同步到 Notion ======
        if sync_after_download and processed_articles:
            print(f"\n{'='*60}")
            print(f"  ☁️ 开始同步到 Notion...")
            print(f"{'='*60}\n")

            indexes = build_existing_indexes(self.notion_api.get_existing_articles())
            sync_count = skip_count = failed_count = 0
            eligible_dates = set()
            for article in processed_articles:
                if not article.get('title') or article['title'] == '广告':
                    continue
                day = article['date']
                eligible_dates.add(day)
                try:
                    duplicate = find_duplicate(article, indexes)
                except AmbiguousArticleMatch as error:
                    failed_dates.add(day)
                    failed_count += 1
                    logging.warning('文章身份需人工复核：%s；%s', article['title'], error)
                    continue
                if duplicate:
                    # 页面清单不含正文，不能把“没读取”当作“内容变化”而清空重写。
                    # 正文更新由显式的 --update-existing 流程执行。
                    skip_count += 1
                    continue
                page_id = self.notion_api.create_page(article, datetime.strptime(day, '%Y-%m-%d'))
                if page_id:
                    add_to_indexes(article, page_id, indexes)
                    sync_count += 1
                else:
                    failed_dates.add(day)
                    failed_count += 1
            for day in sorted(eligible_dates - failed_dates):
                mark_date_synced(day)
            print(f"  ☁️ Notion：新增 {sync_count} 篇，已有 {skip_count} 篇，失败 {failed_count} 篇")

        if not failed_dates:
            checkpoint.finish()
        else:
            print('  ⚠️ 有未完成任务，已保留断点。')

        return processed_articles
    
    @staticmethod
    def _daily_raw(date):
        path = Path(f"data/raw/articles_{date:%Y%m%d}.json")
        if not path.exists():
            return []
        with path.open(encoding='utf-8') as f:
            records = json.load(f)
        if not isinstance(records, list) or not all(isinstance(record, dict) for record in records):
            raise ValueError(f'当日原始资料格式异常，未覆盖：{path}')
        return records

    def save_articles_local(self, articles: List[Dict], date: datetime):
        """同一天分次选取时，只增加或更新本批文章，不丢弃先前下载的资料。"""
        if not articles:
            return
        records = self._daily_raw(date)
        positions = {a.get('article_id') or build_article_id(a): i for i, a in enumerate(records)}
        for article in articles:
            article_id = article.get('article_id') or build_article_id(article)
            if article_id in positions:
                i = positions[article_id]
                records[i] = {**records[i], **article}
            else:
                positions[article_id] = len(records)
                records.append(article)
        raw_file = f"data/raw/articles_{date:%Y%m%d}.json"
        if not safe_json_dump(records, raw_file):
            raise OSError(f'原始资料保存失败：{raw_file}')
        fields = ('title', 'url', 'date', 'category', 'keywords', 'summary', 'plate')
        processed = [{k: a.get(k, [] if k == 'keywords' else '') for k in fields} for a in records]
        processed_file = f"data/processed/articles_{date:%Y%m%d}.json"
        if not safe_json_dump(processed, processed_file):
            raise OSError(f'兼容资料保存失败：{processed_file}')
        self.article_store.upsert_articles(articles)

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


class SleepPreventer:
    """macOS 防休眠上下文管理器，使用 caffeinate 阻止系统息屏/休眠"""
    
    def __init__(self):
        self.process = None
    
    def __enter__(self):
        if platform.system() == 'Darwin':
            try:
                # -di: 阻止系统空闲休眠(-i)和显示器休眠(-d)
                self.process = subprocess.Popen(
                    ['caffeinate', '-di'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                logging.info("已启用 caffeinate 防休眠（系统将保持唤醒直到爬虫结束）")
            except Exception as e:
                logging.warning(f"启动 caffeinate 失败: {e}（程序仍会继续运行）")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                logging.info("已关闭 caffeinate 防休眠")
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
        return False


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='人民日报爬虫与Notion存储脚本')
    parser.add_argument('--date-range', nargs=2, metavar=('START_DATE', 'END_DATE'),
                        help='日期范围，格式: YYYY-MM-DD YYYY-MM-DD（跳过日期选择界面）')
    parser.add_argument('--date', metavar='DATE',
                        help='单个日期，格式: YYYY-MM-DD（跳过日期选择界面）')
    parser.add_argument('--export', action='store_true',
                        help='导出数据（现已默认执行，此参数仅为兼容保留）')
    parser.add_argument('--all', action='store_true',
                        help='自动选择所有可用文章，跳过文章选择界面')
    
    args = parser.parse_args()
    
    # 初始化系统
    system = PeopleDailyMaterialSystem()
    
    try:
        with SleepPreventer():
            if args.date_range:
                # 命令行直接指定了日期范围
                try:
                    start_date = datetime.strptime(args.date_range[0], '%Y-%m-%d')
                    end_date = datetime.strptime(args.date_range[1], '%Y-%m-%d')
                except ValueError:
                    logging.error("日期格式错误，请使用 YYYY-MM-DD 格式")
                    sys.exit(1)
                if start_date > end_date:
                    parser.error("结束日期不能早于开始日期")
                system.crawl_date_range(start_date, end_date, auto_select=args.all)
            elif args.date:
                # 命令行直接指定了单个日期
                try:
                    date = datetime.strptime(args.date, '%Y-%m-%d')
                except ValueError:
                    logging.error("日期格式错误，请使用 YYYY-MM-DD 格式")
                    sys.exit(1)
                system.crawl_single_date(date, auto_select=args.all)
            else:
                # ====== 默认模式：弹出日期选择界面 ======
                from modules.date_selector import DateSelector
                
                print(f"\n{'='*60}")
                print(f"  📰 人民日报素材系统")
                print(f"{'='*60}")
                print(f"  正在打开日期选择界面...\n")
                
                date_selector = DateSelector()
                start_date, end_date = date_selector.show_and_wait()
                
                if not start_date:
                    print("\n未选择任何日期，退出。")
                    sys.exit(0)
                
                if end_date and end_date != start_date:
                    # 用户选择了日期范围
                    print(f"\n  📅 已选择日期范围: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
                    system.crawl_date_range(start_date, end_date, auto_select=args.all)
                else:
                    # 用户选择了单个日期
                    print(f"\n  📅 已选择日期: {start_date.strftime('%Y-%m-%d')}")
                    system.crawl_single_date(start_date, auto_select=args.all)
    finally:
        # 确保关闭浏览器
        system.crawler.close()
        system.article_store.close()
        logging.info("程序结束，浏览器已关闭")


if __name__ == '__main__':
    main()

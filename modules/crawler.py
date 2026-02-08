#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫模块
"""

import time
import random
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from modules.utils import Config

# 默认User-Agent池
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
]


class URLGenerator:
    """URL生成类"""
    def __init__(self):
        self.base_url = "https://paper.people.com.cn/rmrb/pc/layout/{date_str}/node_{node_id}.html"
    
    def generate_url(self, date: datetime, node_id: str = "01") -> str:
        """生成指定日期和版面的人民日报目录页URL"""
        date_str = date.strftime("%Y%m/%d")
        return self.base_url.format(date_str=date_str, node_id=node_id)
    
    def generate_all_node_urls(self, date: datetime, node_ids: List[str]) -> List[str]:
        """生成指定日期所有版面的URL"""
        return [self.generate_url(date, node_id) for node_id in node_ids]
    
    def generate_urls_for_date_range(self, start_date: datetime, end_date: datetime) -> List[Tuple[datetime, str]]:
        """生成日期范围内的所有URL（仅第一版）"""
        urls = []
        current_date = start_date
        while current_date <= end_date:
            urls.append((current_date, self.generate_url(current_date)))
            current_date += timedelta(days=1)
        return urls


class WebRequestor:
    """网页请求类"""
    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.timeout = self.config.get('crawler.timeout', 10)
        self.max_retries = self.config.get('crawler.max_retries', 3)
        self.request_interval = self.config.get('crawler.request_interval', [1, 3])
        self.proxy_enabled = self.config.get('crawler.proxy_enabled', False)
        self.proxies = self.config.get('crawler.proxies', [])
    
    def get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        return random.choice(USER_AGENTS)
    
    def get_random_proxy(self) -> Optional[Dict]:
        """获取随机代理"""
        if self.proxy_enabled and self.proxies:
            return random.choice(self.proxies)
        return None
    
    def request(self, url: str) -> Optional[requests.Response]:
        """发送请求"""
        retries = 0
        while retries < self.max_retries:
            try:
                # 随机休眠
                time.sleep(random.uniform(*self.request_interval))
                
                headers = {
                    'User-Agent': self.get_random_user_agent(),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Connection': 'keep-alive'
                }
                
                proxies = self.get_random_proxy()
                response = self.session.get(
                    url,
                    headers=headers,
                    proxies=proxies,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                # 强制使用UTF-8编码
                response.encoding = 'utf-8'
                return response
            except requests.RequestException as e:
                retries += 1
                logging.warning(f"请求 {url} 失败，第 {retries} 次重试: {str(e)}")
                if retries >= self.max_retries:
                    logging.error(f"请求 {url} 失败，已达到最大重试次数")
                    return None
        return None


class PeopleDailyCrawler:
    """人民日报爬虫类"""
    def __init__(self, config: Config):
        self.config = config
        self.url_generator = URLGenerator()
        self.web_requestor = WebRequestor(config)
    
    def get_all_nodes(self, date: datetime) -> List[str]:
        """获取指定日期的所有版面节点ID"""
        import re
        # 先获取第一版来解析所有版面链接
        url = self.url_generator.generate_url(date, "01")
        response = self.web_requestor.request(url)
        if not response:
            return ["01"]  # 默认返回第一版
        
        # 使用正则提取所有 node_XX.html 链接
        node_pattern = re.compile(r'node_(\d+)\.html')
        matches = node_pattern.findall(response.text)
        
        # 去重并排序
        node_ids = sorted(list(set(matches)))
        if not node_ids:
            return ["01"]
        
        logging.info(f"找到 {len(node_ids)} 个版面")
        return node_ids
    
    def crawl_directory(self, date: datetime) -> Optional[Tuple[str, str]]:
        """抓取单个目录页（第一版）"""
        url = self.url_generator.generate_url(date, "01")
        response = self.web_requestor.request(url)
        if not response:
            return None
        return url, response.text
    
    def crawl_all_directories(self, date: datetime) -> List[Tuple[str, str]]:
        """抓取所有版面的目录页"""
        node_ids = self.get_all_nodes(date)
        results = []
        
        for node_id in node_ids:
            url = self.url_generator.generate_url(date, node_id)
            response = self.web_requestor.request(url)
            if response:
                results.append((url, response.text))
                logging.info(f"成功抓取版面 {node_id}")
            else:
                logging.warning(f"抓取版面 {node_id} 失败")
        
        return results
    
    def crawl_article(self, article_url: str) -> Optional[str]:
        """抓取文章页"""
        response = self.web_requestor.request(article_url)
        if not response:
            return None
        return response.text


# 导入日志模块
import logging

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫模块 - 双模式：requests（目录页快速抓取）+ Selenium（文章页反爬）
"""

import re
import time
import random
import logging
import requests
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from modules.utils import Config


# User-Agent 池
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
]


class URLGenerator:
    """URL生成类"""
    def __init__(self):
        self.base_url = "https://paper.people.com.cn/rmrb/pc/layout/{date_str}/node_{node_id}.html"
    
    def generate_url(self, date: datetime, node_id: str = "01") -> str:
        date_str = date.strftime("%Y%m/%d")
        return self.base_url.format(date_str=date_str, node_id=node_id)


class RequestsFetcher:
    """requests 快速抓取器（用于目录页）"""
    
    def __init__(self, config: Config):
        self.session = requests.Session()
        self.max_retries = config.get('crawler.max_retries', 3)
        self.request_count = 0
        # 目录页不需要长间隔，固定 2-5 秒即可
        self.request_interval = [2, 5]
        
        # 预热 session
        self._warmup()
    
    def _warmup(self):
        """用 session 预热，建立 cookie"""
        try:
            headers = self._get_headers()
            self.session.get('https://paper.people.com.cn/', headers=headers, timeout=10)
            time.sleep(random.uniform(1, 2))
            logging.info("requests session 预热完成")
        except Exception as e:
            logging.warning(f"requests 预热失败: {e}")
    
    def _get_headers(self):
        return {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://paper.people.com.cn/rmrb/pc/',
            'Cache-Control': 'max-age=0',
        }
    
    def get_page(self, url: str) -> Optional[str]:
        """快速获取页面内容"""
        retries = 0
        while retries < self.max_retries:
            try:
                self.request_count += 1
                # 目录页间隔短一些（2-5秒）
                sleep_time = random.uniform(*self.request_interval)
                time.sleep(sleep_time)
                
                response = self.session.get(url, headers=self._get_headers(), timeout=15)
                
                if response.status_code == 200:
                    response.encoding = 'utf-8'
                    return response.text
                elif response.status_code == 403:
                    retries += 1
                    wait = 10 * retries
                    logging.warning(f"requests 收到 403，等待 {wait}s 后重试...")
                    time.sleep(wait)
                    self._warmup()
                    continue
                else:
                    logging.warning(f"请求返回 {response.status_code}: {url}")
                    retries += 1
                    
            except Exception as e:
                retries += 1
                logging.warning(f"requests 请求失败 ({retries}/{self.max_retries}): {e}")
                time.sleep(5 * retries)
        
        return None


class SeleniumBrowser:
    """Selenium 浏览器管理类（延迟初始化，仅在需要时启动）"""
    
    def __init__(self, config: Config):
        self.config = config
        self.request_interval = config.get('crawler.request_interval', [8, 15])
        self.max_retries = config.get('crawler.max_retries', 5)
        self.request_count = 0
        self.driver = None  # 延迟初始化
    
    def _ensure_browser(self):
        """确保浏览器已启动（延迟初始化）"""
        if self.driver is not None:
            return
        
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        
        logging.info("正在启动 Chrome 浏览器（用于文章下载）...")
        
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--lang=zh-CN')
        prefs = {
            'profile.managed_default_content_settings.images': 2,
            'profile.default_content_setting_values.notifications': 2
        }
        options.add_experimental_option('prefs', prefs)
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
        except Exception:
            logging.info("尝试使用系统 chromedriver...")
            self.driver = webdriver.Chrome(options=options)
        
        # 隐藏 webdriver 特征
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
            '''
        })
        
        self.driver.set_page_load_timeout(30)
        self._warmup()
        logging.info("Chrome 浏览器启动成功")
    
    def _warmup(self):
        """预热浏览器"""
        try:
            self.driver.get('https://paper.people.com.cn/')
            time.sleep(random.uniform(3, 5))
            self.driver.get('https://paper.people.com.cn/rmrb/pc/')
            time.sleep(random.uniform(3, 5))
        except Exception as e:
            logging.warning(f"浏览器预热失败: {e}")
    
    def get_page(self, url: str) -> Optional[str]:
        """获取页面内容（Selenium）"""
        self._ensure_browser()
        retries = 0
        
        while retries < self.max_retries:
            try:
                self.request_count += 1
                if self.request_count > 1 and self.request_count % 10 == 0:
                    rest_time = random.uniform(20, 40)
                    logging.info(f"已请求 {self.request_count} 次，休息 {rest_time:.0f} 秒...")
                    time.sleep(rest_time)
                
                sleep_time = random.uniform(*self.request_interval)
                logging.info(f"等待 {sleep_time:.0f}s 后请求: {url.split('/')[-1]}")
                time.sleep(sleep_time)
                
                self.driver.get(url)
                time.sleep(random.uniform(2, 4))
                
                # 模拟滚动
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.3);")
                time.sleep(random.uniform(0.5, 1.5))
                
                page_source = self.driver.page_source
                
                if self._is_blocked(page_source):
                    retries += 1
                    wait_time = 60 * retries
                    logging.warning(f"检测到反爬虫拦截，等待 {wait_time}s 后重试...")
                    time.sleep(wait_time)
                    self._warmup()
                    continue
                
                return page_source
                
            except Exception as e:
                retries += 1
                extra_delay = retries * 15
                logging.warning(f"请求失败，等待 {extra_delay}s 后第 {retries} 次重试: {e}")
                time.sleep(extra_delay)
                
                if retries >= self.max_retries:
                    logging.error(f"请求 {url} 失败，已达到最大重试次数")
                    return None
        
        return None
    
    def _is_blocked(self, text: str) -> bool:
        if not text or len(text) < 500:
            return True
        if '403' in text[:500] and 'Forbidden' in text[:500]:
            return True
        return False
    
    def close(self):
        if self.driver:
            try:
                self.driver.quit()
                logging.info("浏览器已关闭")
            except Exception:
                pass


class PeopleDailyCrawler:
    """人民日报爬虫类 - 双模式"""
    
    def __init__(self, config: Config):
        self.config = config
        self.url_generator = URLGenerator()
        # requests 用于快速获取目录页
        self.requests_fetcher = RequestsFetcher(config)
        # Selenium 延迟初始化，仅在下载文章时启动
        self.selenium_browser = SeleniumBrowser(config)
    
    def get_all_nodes(self, date: datetime) -> List[str]:
        """获取指定日期的所有版面节点ID（使用 requests 快速获取）"""
        url = self.url_generator.generate_url(date, "01")
        page_source = self.requests_fetcher.get_page(url)
        if not page_source:
            return ["01"]
        
        node_pattern = re.compile(r'node_(\d+)\.html')
        matches = node_pattern.findall(page_source)
        
        node_ids = sorted(list(set(matches)))
        if not node_ids:
            return ["01"]
        
        logging.info(f"找到 {len(node_ids)} 个版面")
        return node_ids
    
    def crawl_all_directories(self, date: datetime) -> List[Tuple[str, str]]:
        """抓取所有版面的目录页（使用 requests 快速获取）"""
        node_ids = self.get_all_nodes(date)
        results = []
        
        for node_id in node_ids:
            url = self.url_generator.generate_url(date, node_id)
            page_source = self.requests_fetcher.get_page(url)
            if page_source:
                results.append((url, page_source))
            else:
                logging.warning(f"抓取版面 {node_id} 失败")
        
        return results
    
    def crawl_article(self, article_url: str) -> Optional[str]:
        """抓取文章页（使用 Selenium 绕过反爬）"""
        return self.selenium_browser.get_page(article_url)
    
    def close(self):
        """关闭爬虫"""
        self.selenium_browser.close()

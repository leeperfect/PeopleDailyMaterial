#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫模块 - 使用 Selenium 模拟真实浏览器
"""

import time
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from modules.utils import Config

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


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


class SeleniumBrowser:
    """Selenium 浏览器管理类"""
    
    def __init__(self, config: Config):
        self.config = config
        self.request_interval = config.get('crawler.request_interval', [8, 15])
        self.max_retries = config.get('crawler.max_retries', 5)
        self.request_count = 0
        self.driver = None
        self._init_browser()
    
    def _init_browser(self):
        """初始化 Chrome 浏览器"""
        logging.info("正在启动 Chrome 浏览器...")
        
        options = Options()
        # 无头模式（不显示浏览器窗口）
        options.add_argument('--headless=new')
        # 禁用 GPU（无头模式下推荐）
        options.add_argument('--disable-gpu')
        # 设置窗口大小（模拟正常浏览器）
        options.add_argument('--window-size=1920,1080')
        # 禁用自动化标识
        options.add_argument('--disable-blink-features=AutomationControlled')
        # 禁用开发者模式扩展
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        # 设置语言
        options.add_argument('--lang=zh-CN')
        # 禁用图片加载（加速）
        prefs = {
            'profile.managed_default_content_settings.images': 2,
            'profile.default_content_setting_values.notifications': 2
        }
        options.add_experimental_option('prefs', prefs)
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
        except Exception:
            # 如果 webdriver-manager 失败，尝试系统自带的 chromedriver
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
        
        # 设置页面加载超时
        self.driver.set_page_load_timeout(30)
        
        # 预热：先访问首页
        self._warmup()
        
        logging.info("Chrome 浏览器启动成功")
    
    def _warmup(self):
        """预热浏览器，像真人一样先浏览首页"""
        try:
            logging.info("正在预热浏览器...")
            self.driver.get('https://paper.people.com.cn/')
            time.sleep(random.uniform(3, 5))
            self.driver.get('https://paper.people.com.cn/rmrb/pc/')
            time.sleep(random.uniform(3, 5))
            logging.info("浏览器预热完成")
        except Exception as e:
            logging.warning(f"浏览器预热失败: {e}")
    
    def get_page(self, url: str) -> Optional[str]:
        """获取页面内容，带反爬策略"""
        retries = 0
        
        while retries < self.max_retries:
            try:
                # 请求计数和定期休息
                self.request_count += 1
                if self.request_count > 1 and self.request_count % 10 == 0:
                    rest_time = random.uniform(20, 40)
                    logging.info(f"已请求 {self.request_count} 次，休息 {rest_time:.0f} 秒...")
                    time.sleep(rest_time)
                
                # 随机等待（模拟人类阅读时间）
                sleep_time = random.uniform(*self.request_interval)
                logging.info(f"等待 {sleep_time:.0f}s 后请求: {url.split('/')[-1]}")
                time.sleep(sleep_time)
                
                # 访问页面
                self.driver.get(url)
                
                # 等待页面加载完成
                time.sleep(random.uniform(2, 4))
                
                # 模拟滚动（像真人一样）
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.3);")
                time.sleep(random.uniform(0.5, 1.5))
                
                page_source = self.driver.page_source
                
                # 检查是否被拦截
                if self._is_blocked(page_source):
                    retries += 1
                    wait_time = 60 * retries
                    logging.warning(f"检测到反爬虫拦截，等待 {wait_time}s 后重试...")
                    time.sleep(wait_time)
                    # 重新预热
                    self._warmup()
                    continue
                
                return page_source
                
            except Exception as e:
                retries += 1
                extra_delay = retries * 15
                logging.warning(f"请求 {url} 失败，等待 {extra_delay}s 后第 {retries} 次重试: {e}")
                time.sleep(extra_delay)
                
                if retries >= self.max_retries:
                    logging.error(f"请求 {url} 失败，已达到最大重试次数")
                    return None
        
        return None
    
    def _is_blocked(self, text: str) -> bool:
        """检测是否被反爬虫拦截"""
        if not text or len(text) < 500:
            return True
        # 检查是否返回 403/错误页面
        if '403' in text[:500] and 'Forbidden' in text[:500]:
            return True
        return False
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
                logging.info("浏览器已关闭")
            except Exception:
                pass


class PeopleDailyCrawler:
    """人民日报爬虫类"""
    def __init__(self, config: Config):
        self.config = config
        self.url_generator = URLGenerator()
        self.browser = SeleniumBrowser(config)
    
    def get_all_nodes(self, date: datetime) -> List[str]:
        """获取指定日期的所有版面节点ID"""
        import re
        url = self.url_generator.generate_url(date, "01")
        page_source = self.browser.get_page(url)
        if not page_source:
            return ["01"]
        
        node_pattern = re.compile(r'node_(\d+)\.html')
        matches = node_pattern.findall(page_source)
        
        node_ids = sorted(list(set(matches)))
        if not node_ids:
            return ["01"]
        
        logging.info(f"找到 {len(node_ids)} 个版面")
        return node_ids
    
    def crawl_directory(self, date: datetime) -> Optional[Tuple[str, str]]:
        """抓取单个目录页（第一版）"""
        url = self.url_generator.generate_url(date, "01")
        page_source = self.browser.get_page(url)
        if not page_source:
            return None
        return url, page_source
    
    def crawl_all_directories(self, date: datetime) -> List[Tuple[str, str]]:
        """抓取所有版面的目录页"""
        node_ids = self.get_all_nodes(date)
        results = []
        
        for node_id in node_ids:
            url = self.url_generator.generate_url(date, node_id)
            page_source = self.browser.get_page(url)
            if page_source:
                results.append((url, page_source))
                logging.info(f"成功抓取版面 {node_id}")
            else:
                logging.warning(f"抓取版面 {node_id} 失败")
        
        return results
    
    def crawl_article(self, article_url: str) -> Optional[str]:
        """抓取文章页"""
        return self.browser.get_page(article_url)
    
    def close(self):
        """关闭爬虫（关闭浏览器）"""
        self.browser.close()

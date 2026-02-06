#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容解析模块
"""

import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Optional


class ContentParser:
    """内容解析类"""
    def __init__(self):
        pass
    
    def parse_directory(self, html: str) -> List[Dict]:
        """解析目录页获取所有文章链接"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # 检测网页结构变化
            if not soup.find('div', class_='newsbox'):
                logging.warning("网页结构可能发生变化，目录解析可能失败")
            
            articles = []
            # 查找所有文章链接
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href and 'nw.D110000renmrb_' in href:
                    title = link.get_text(strip=True)
                    if title:
                        articles.append({
                            'title': title,
                            'href': href
                        })
            
            return articles
        except Exception as e:
            logging.error(f"解析目录页失败: {str(e)}")
            return []
    
    def parse_article(self, html: str, url: str) -> Optional[Dict]:
        """解析文章内容"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # 检测网页结构变化
            if not soup.find('div', class_='article'):
                logging.warning(f"网页结构可能发生变化，文章 {url} 解析可能失败")
            
            # 提取标题
            title_elem = soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # 提取版面名称
            plate_elem = soup.find('div', class_='position')
            plate = ""
            if plate_elem:
                plate_text = plate_elem.get_text(strip=True)
                # 提取版面名称
                if '>' in plate_text:
                    plate_parts = plate_text.split('>')
                    if len(plate_parts) >= 2:
                        plate = plate_parts[1].strip()
            
            # 提取正文
            content_elem = soup.find('div', class_='article')
            content = ""
            if content_elem:
                # 移除广告和无关元素
                for ad in content_elem.find_all(class_=['ad', 'advertisement', 'related']):
                    ad.decompose()
                # 移除脚本和样式
                for script in content_elem.find_all(['script', 'style']):
                    script.decompose()
                # 提取文本
                content = '\n'.join([p.get_text(strip=True) for p in content_elem.find_all('p') if p.get_text(strip=True)])
            
            return {
                'title': title,
                'content': content,
                'plate': plate,
                'url': url
            }
        except Exception as e:
            logging.error(f"解析文章 {url} 失败: {str(e)}")
            return None

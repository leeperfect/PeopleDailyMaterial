#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容解析模块
"""

import re
import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Optional


class ContentParser:
    """内容解析类"""
    def __init__(self):
        pass
    
    def parse_directory(self, html: str) -> tuple:
        """解析目录页获取文章链接和版面名称
        
        Returns:
            (articles_list, section_name)
        """
        try:
            soup = BeautifulSoup(html, 'lxml')
            articles = []
            
            # 提取版面名称（如：第01版：要闻 → 要闻）
            section_name = ""
            page_text = soup.get_text()
            match = re.search(r'第\s*\d+\s*版[：:]\s*([^\n\r\s]+)', page_text)
            if match:
                section_name = match.group(1).strip()
            
            # 只在 div.news 容器中查找文章链接
            news_div = soup.find('div', class_='news')
            if not news_div:
                logging.warning("未找到 div.news 容器，尝试全文搜索 content_ 链接")
                search_scope = soup
            else:
                search_scope = news_div
            
            # 只提取包含 content_ 的链接（真正的文章链接）
            for link in search_scope.find_all('a', href=True):
                href = link.get('href', '')
                title = link.get_text(strip=True)
                
                if not title or not href:
                    continue
                
                if 'content_' not in href:
                    continue
                
                match = re.search(r'(content_\d+\.html)', href)
                if match:
                    articles.append({
                        'title': title,
                        'href': match.group(1)
                    })
            
            logging.info(f"目录页解析到 {len(articles)} 篇文章，版面：{section_name}")
            return articles, section_name
        except Exception as e:
            logging.error(f"解析目录页失败: {str(e)}")
            return [], ""
    
    def parse_article(self, html: str, url: str) -> Optional[Dict]:
        """解析文章内容"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # === 提取标题 ===
            title = ""
            article_div = soup.find('div', class_='article')
            
            # 方法1（最可靠）: 从 div.article 内的 <h1> 标签提取
            if article_div:
                h1 = article_div.find('h1')
                if h1:
                    title = h1.get_text(strip=True)
            
            # 方法2: 从全局 <h1> 提取
            if not title:
                h1 = soup.find('h1')
                if h1:
                    title = h1.get_text(strip=True)
            
            # 方法3: 从 <title> 标签提取（排除通用标题）
            if not title:
                title_elem = soup.find('title')
                if title_elem:
                    title_text = title_elem.get_text(strip=True)
                    if title_text and '人民日报-人民网' not in title_text:
                        title = title_text
            
            # === 提取版面名称 ===
            plate = ""
            try:
                page_text = soup.get_text()
                match = re.search(r'(?:第\s*)?\d+\s*版[：:]\s*([^\n\r\s]+)', page_text)
                if match:
                    plate = match.group(1).strip()
            except Exception as e:
                logging.warning(f"提取版面名称失败: {str(e)}")
            
            # === 提取正文 ===
            content = ""
            try:
                # 移除包含"本版责编"的元素
                for elem in soup.find_all(['a', 'p', 'div', 'span']):
                    if elem.string and '本版责编' in elem.get_text():
                        elem.decompose()
                
                # 优先从 div.article 内提取正文
                if article_div:
                    # 移除 script 和 style
                    for tag in article_div.find_all(['script', 'style']):
                        tag.decompose()
                    
                    # 获取正文内容的 div（正文通常在 div.article 内部的 div 中）
                    content_div = article_div.find('div')
                    if content_div:
                        paragraphs = [p.get_text(strip=True) for p in content_div.find_all('p') if p.get_text(strip=True)]
                        content = '\n'.join(paragraphs)
                    
                    # 如果 div 中没有内容，从 article 的 <p> 中提取（跳过作者署名）
                    if not content:
                        all_p = article_div.find_all('p')
                        paragraphs = []
                        for p in all_p:
                            text = p.get_text(strip=True)
                            # 跳过作者署名行（包含《人民日报》和年月日）
                            if '《人民日报》' in text and '版' in text:
                                continue
                            # 跳过 class=sec 的段落（通常是作者署名）
                            if p.get('class') and 'sec' in p.get('class', []):
                                continue
                            if text:
                                paragraphs.append(text)
                        content = '\n'.join(paragraphs)
                
                # 备用方案
                if not content:
                    article_elem = soup.find('article')
                    if article_elem:
                        for script in article_elem.find_all(['script', 'style']):
                            script.decompose()
                        content = '\n'.join([p.get_text(strip=True) for p in article_elem.find_all('p') if p.get_text(strip=True)])
                
                if not content:
                    all_p = soup.find_all('p')
                    content = '\n'.join([p.get_text(strip=True) for p in all_p if p.get_text(strip=True)])
                    
            except Exception as e:
                logging.warning(f"提取内容失败: {str(e)}")
            
            if not title or not content:
                logging.warning(f"文章 {url} 解析可能不完整 (标题: {'有' if title else '无'}, 正文: {'有' if content else '无'})")
            
            # 过滤无关内容
            if content:
                content = re.split(r'本版责编[：:]?', content)[0].strip()
                content = re.split(r'(?:©|Copyright|人\s*民\s*网\s*版\s*权)', content)[0].strip()
            
            if title:
                title = title.strip()
            
            return {
                'title': title,
                'content': content,
                'plate': plate,
                'url': url
            }
        except Exception as e:
            logging.error(f"解析文章 {url} 失败: {str(e)}")
            return None

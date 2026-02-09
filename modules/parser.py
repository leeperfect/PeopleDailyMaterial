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
    
    def parse_directory(self, html: str) -> List[Dict]:
        """解析目录页获取所有文章链接"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            articles = []
            
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
                
                # 只处理包含 content_ 的链接（文章页）
                if 'content_' not in href:
                    continue
                
                # 提取相对路径中的文件名部分
                # 格式: ../../../content/202602/02/content_30137423.html
                match = re.search(r'(content_\d+\.html)', href)
                if match:
                    articles.append({
                        'title': title,
                        'href': match.group(1)
                    })
            
            logging.info(f"目录页解析到 {len(articles)} 篇文章")
            return articles
        except Exception as e:
            logging.error(f"解析目录页失败: {str(e)}")
            return []
    
    def parse_article(self, html: str, url: str) -> Optional[Dict]:
        """解析文章内容"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # === 提取标题 ===
            title = ""
            
            # 方法1: 从 div.article 内的 <p> 标签中提取标题
            # 人民日报文章页结构: div.article 中第1个 <p> 是副标题，第2个 <p> 是主标题
            article_div = soup.find('div', class_='article')
            if article_div:
                p_tags = article_div.find_all('p', recursive=False)
                # 尝试第2个 <p>（通常是主标题）
                if len(p_tags) >= 2:
                    candidate = p_tags[1].get_text(strip=True)
                    if candidate and len(candidate) < 100:
                        title = candidate
                # 如果第2个 <p> 不合适，尝试第1个
                if not title and len(p_tags) >= 1:
                    candidate = p_tags[0].get_text(strip=True)
                    if candidate and len(candidate) < 100:
                        title = candidate
            
            # 方法2: 从 <title> 标签提取（但排除通用标题）
            if not title:
                title_elem = soup.find('title')
                if title_elem:
                    title_text = title_elem.get_text(strip=True)
                    # 排除通用的页面标题
                    if title_text and title_text != '人民日报-人民网' and '人民网' not in title_text:
                        title = title_text
            
            # 方法3: 从 <h1> 提取
            if not title:
                h1_elem = soup.find('h1')
                if h1_elem:
                    p_in_h1 = h1_elem.find('p')
                    title = (p_in_h1 or h1_elem).get_text(strip=True)
            
            # === 提取版面名称 ===
            plate = ""
            try:
                page_text = soup.get_text()
                match = re.search(r'(?:第\s*)?\d+\s*版[：:]\s*([^\n\r\s]+)', page_text)
                if match:
                    plate = match.group(1).strip()
                
                if not plate:
                    plate_elem = soup.find('div', attrs={'class': 'position'}) or soup.find('div', attrs={'class': 'channel'})
                    if plate_elem:
                        plate_text = plate_elem.get_text(strip=True)
                        match = re.search(r'(?:第\s*)?\d+\s*版[：:]\s*([^\n\r\s]+)', plate_text)
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
                
                # 优先从 div.article 提取正文
                if article_div:
                    # 移除 script 和 style
                    for tag in article_div.find_all(['script', 'style']):
                        tag.decompose()
                    
                    # 获取正文内容的 div（跳过标题 <p> 标签）
                    content_div = article_div.find('div')
                    if content_div:
                        paragraphs = [p.get_text(strip=True) for p in content_div.find_all('p') if p.get_text(strip=True)]
                        content = '\n'.join(paragraphs)
                    
                    # 如果 div 中没有内容，从 article 的所有 <p> 中提取（跳过前两个标题 p）
                    if not content:
                        all_p = article_div.find_all('p')
                        # 跳过前面的标题段落
                        start_idx = 0
                        for i, p in enumerate(all_p):
                            text = p.get_text(strip=True)
                            # 找到记者署名行后，后面的才是正文
                            if '本报记者' in text or '《人民日报》' in text:
                                start_idx = i + 1
                                break
                            # 或者找到较长的段落（大于50字）认为是正文开始
                            if len(text) > 50:
                                start_idx = i
                                break
                        
                        paragraphs = [p.get_text(strip=True) for p in all_p[start_idx:] if p.get_text(strip=True)]
                        content = '\n'.join(paragraphs)
                
                # 备用方案：从 <article> 标签提取
                if not content:
                    article_elem = soup.find('article')
                    if article_elem:
                        for script in article_elem.find_all(['script', 'style']):
                            script.decompose()
                        content = '\n'.join([p.get_text(strip=True) for p in article_elem.find_all('p') if p.get_text(strip=True)])
                
                # 最后备用方案
                if not content:
                    all_p = soup.find_all('p')
                    content = '\n'.join([p.get_text(strip=True) for p in all_p if p.get_text(strip=True)])
                    
            except Exception as e:
                logging.warning(f"提取内容失败: {str(e)}")
            
            # 检测解析完整性
            if not title or not content:
                logging.warning(f"文章 {url} 解析可能不完整 (标题: {'有' if title else '无'}, 正文: {'有' if content else '无'})")
            
            # 过滤无关内容
            if content:
                content = re.split(r'本版责编[：:]?', content)[0].strip()
                content = re.split(r'(?:©|Copyright|人\s*民\s*网\s*版\s*权)', content)[0].strip()
            
            # 过滤标题中的多余信息
            if title:
                # 去掉标题末尾可能包含的空格
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

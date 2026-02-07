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
            if not soup.find('div', class_='newsbox') and not soup.find('div', class_='layout'):
                logging.warning("网页结构可能发生变化，目录解析可能失败")
            
            articles = []
            # 查找所有文章链接
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                title = link.get_text(strip=True)
                
                # 过滤掉无效链接
                if not href or not title:
                    continue
                
                # 过滤掉节点链接（node_*.html）
                if href.startswith('node_') and href.endswith('.html'):
                    continue
                
                # 过滤掉pad版链接
                if 'pad/layout' in href:
                    continue
                
                # 适配新的链接格式
                if ('nw.D110000renmrb_' in href or href.endswith('.html')):
                    # 处理完整URL
                    if href.startswith('http'):
                        # 提取内容链接
                        if 'content' in href:
                            # 从完整URL中提取相对路径
                            import re
                            match = re.search(r'content/(.*\.html)', href)
                            if match:
                                href = match.group(1)
                            else:
                                continue
                    # 处理相对路径
                    elif not href.startswith('http'):
                        # 相对路径，直接使用
                        pass
                    
                    if href and title:
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
            
            # 提取标题（支持多种标签和结构）
            title = ""
            
            # 优先从 <title> 标签提取标题（人民日报网页的标题通常在这里）
            try:
                title_elem = soup.find('title')
                if title_elem:
                    title = title_elem.get_text(strip=True)
            except Exception as e:
                logging.warning(f"从title标签提取标题失败: {str(e)}")
            
            # 如果 <title> 标签提取失败或为空，尝试从 <h1> 标签提取
            if not title:
                try:
                    h1_elem = soup.find('h1')
                    if h1_elem:
                        # h1 可能嵌套了 <p> 标签，需要处理
                        p_in_h1 = h1_elem.find('p')
                        if p_in_h1:
                            title = p_in_h1.get_text(strip=True)
                        else:
                            title = h1_elem.get_text(strip=True)
                except Exception as e:
                    logging.warning(f"从h1标签提取标题失败: {str(e)}")
            
            # 最后尝试从 meta 标签提取
            if not title:
                try:
                    meta_title = soup.find('meta', attrs={'property': 'og:title'}) or soup.find('meta', attrs={'name': 'title'})
                    if meta_title:
                        title = meta_title.get('content', '').strip()
                except Exception as e:
                    logging.warning(f"从meta标签提取标题失败: {str(e)}")
            
            # 提取版面名称
            plate = ""
            try:
                # 优先从 meta name="author" 标签提取（人民日报使用此标签存储版面信息）
                meta_author = soup.find('meta', attrs={'name': 'author'})
                if meta_author:
                    plate = meta_author.get('content', '').strip()
                
                # 如果 meta 标签提取失败，尝试从 div 提取
                if not plate:
                    plate_elem = soup.find('div', attrs={'class': 'position'})
                    if not plate_elem:
                        plate_elem = soup.find('div', attrs={'class': 'channel'})
                    if plate_elem:
                        plate_text = plate_elem.get_text(strip=True)
                        # 提取版面名称
                        if '>' in plate_text:
                            plate_parts = plate_text.split('>')
                            if len(plate_parts) >= 2:
                                plate = plate_parts[1].strip()
                        else:
                            plate = plate_text.strip()
                
                # 从页面中提取版面格式（如 "第01版：要闻"）
                if not plate:
                    import re
                    # 查找类似 "第01版：要闻" 的文本
                    page_text = soup.get_text()
                    match = re.search(r'第\s*(\d+)\s*版[：:]\s*(.+?)[\n\r]', page_text)
                    if match:
                        plate = f"第{match.group(1)}版：{match.group(2).strip()}"
            except Exception as e:
                logging.warning(f"提取版面名称失败: {str(e)}")
            
            # 提取正文
            content = ""
            try:
                # 尝试从article标签提取
                article_elem = soup.find('article')
                if article_elem:
                    # 移除广告和无关元素
                    for script in article_elem.find_all(['script', 'style']):
                        script.decompose()
                    content = '\n'.join([p.get_text(strip=True) for p in article_elem.find_all('p') if p.get_text(strip=True)])
                
                # 如果article标签提取失败，尝试从所有p标签提取
                if not content:
                    all_p = soup.find_all('p')
                    content = '\n'.join([p.get_text(strip=True) for p in all_p if p.get_text(strip=True)])
            except Exception as e:
                logging.warning(f"提取内容失败: {str(e)}")
            
            # 如果内容为空，尝试从所有div标签提取
            if not content:
                try:
                    all_div = soup.find_all('div')
                    text_parts = [div.get_text(strip=True) for div in all_div if div.get_text(strip=True) and len(div.get_text(strip=True)) > 50]
                    content = '\n'.join(text_parts)
                except Exception as e:
                    logging.warning(f"从div标签提取内容失败: {str(e)}")
            
            # 检测网页结构变化
            if not title or not content:
                logging.warning(f"网页结构可能发生变化，文章 {url} 解析可能不完整")
            
            return {
                'title': title,
                'content': content,
                'plate': plate,
                'url': url
            }
        except Exception as e:
            logging.error(f"解析文章 {url} 失败: {str(e)}")
            return None

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
        """解析文章内容，提取标题、作者、正文，并生成 Markdown 格式正文"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            article_div = soup.find('div', class_='article')
            
            title = ""
            author = ""
            plate = ""
            content = ""         # 纯文本正文
            markdown_body = ""   # Markdown 格式正文
            
            if not article_div:
                logging.warning(f"未找到 div.article: {url}")
                return None
            
            # 移除 script 和 style
            for tag in article_div.find_all(['script', 'style']):
                tag.decompose()
            
            # === 遍历 div.article 的直接子元素，构建 Markdown ===
            md_lines = []
            content_paragraphs = []
            
            for child in article_div.children:
                if not hasattr(child, 'name') or not child.name:
                    continue
                
                tag = child.name
                text = child.get_text(strip=True)
                classes = child.get('class', [])
                
                if not text:
                    continue
                
                # <h3> = 引题（肩题）
                if tag == 'h3':
                    md_lines.append(f"### {text}")
                    md_lines.append("")
                
                # <h1> = 主标题
                elif tag == 'h1':
                    title = text
                    md_lines.append(f"# {text}")
                    md_lines.append("")
                
                # <h2> = 副标题
                elif tag == 'h2':
                    md_lines.append(f"## {text}")
                    md_lines.append("")
                
                # <p class="sec"> = 作者署名
                elif tag == 'p' and 'sec' in classes:
                    # 提取作者名（去掉《人民日报》及之后的部分）
                    author_match = re.match(r'(.+?)《人民日报》', text)
                    if author_match:
                        author = author_match.group(1).strip()
                        # 清理 "本报记者" 等前缀
                        author = re.sub(r'^(本报记者|本报通讯员|记者)\s*', '', author).strip()
                    md_lines.append(f"> {text}")
                    md_lines.append("")
                
                # <p> = 可能是目录标题行或其他（非正文div内的p）
                elif tag == 'p':
                    # 有些文章在 <p> 中放标题（没有 h1）
                    if not title and len(text) < 100 and '《人民日报》' not in text:
                        title = text
                        md_lines.append(f"# {text}")
                        md_lines.append("")
                
                # <div> = 正文容器
                elif tag == 'div':
                    for p in child.find_all('p'):
                        p_text = p.get_text(strip=True)
                        if not p_text:
                            continue
                        # 跳过署名行
                        if '《人民日报》' in p_text and '版' in p_text:
                            continue
                        if '本版责编' in p_text:
                            continue
                        
                        # 处理加粗
                        md_p = self._convert_paragraph_to_markdown(p)
                        md_lines.append(md_p)
                        md_lines.append("")
                        content_paragraphs.append(p_text)
            
            markdown_body = '\n'.join(md_lines).strip()
            content = '\n'.join(content_paragraphs)
            
            # 后备标题提取
            if not title:
                h1 = article_div.find('h1')
                if h1:
                    title = h1.get_text(strip=True)
            if not title:
                h1 = soup.find('h1')
                if h1:
                    title = h1.get_text(strip=True)
            
            # 提取版面名称
            try:
                page_text = soup.get_text()
                match = re.search(r'(?:第\s*)?\d+\s*版[：:]\s*([^\n\r\s]+)', page_text)
                if match:
                    plate = match.group(1).strip()
            except Exception:
                pass
            
            # 过滤无关内容
            if content:
                content = re.split(r'本版责编[：:]?', content)[0].strip()
                content = re.split(r'(?:©|Copyright|人\s*民\s*网\s*版\s*权)', content)[0].strip()
            
            return {
                'title': title.strip() if title else '',
                'content': content,
                'markdown_body': markdown_body,
                'author': author,
                'plate': plate,
                'url': url
            }
        except Exception as e:
            logging.error(f"解析文章 {url} 失败: {str(e)}")
            return None
    
    def _convert_paragraph_to_markdown(self, p_tag) -> str:
        """将一个 <p> 标签转换为 Markdown，保留加粗等格式"""
        parts = []
        for child in p_tag.children:
            if hasattr(child, 'name') and child.name in ('b', 'strong'):
                text = child.get_text(strip=True)
                if text:
                    parts.append(f"**{text}**")
            elif hasattr(child, 'name') and child.name == 'em':
                text = child.get_text(strip=True)
                if text:
                    parts.append(f"*{text}*")
            elif hasattr(child, 'name') and child.name == 'a':
                text = child.get_text(strip=True)
                href = child.get('href', '')
                if text and href:
                    parts.append(f"[{text}]({href})")
                elif text:
                    parts.append(text)
            else:
                text = str(child) if not hasattr(child, 'name') else child.get_text()
                text = text.replace('\n', ' ').replace('\r', '')
                if text.strip():
                    parts.append(text.strip())
        
        return ''.join(parts)


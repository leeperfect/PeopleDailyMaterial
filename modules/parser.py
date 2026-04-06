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
            series_name = ""     # 系列名称
            
            if not article_div:
                logging.warning(f"未找到 div.article: {url}")
                return None
            
            # 移除 script 和 style
            for tag in article_div.find_all(['script', 'style']):
                tag.decompose()
            
            # === 遍历 div.article 的直接子元素，构建 Markdown ===
            md_lines = []
            content_paragraphs = []
            
            # 处理特殊结构：h3/h1 标签后跟着 p 标签的情况
            children = list(article_div.children)
            i = 0
            while i < len(children):
                child = children[i]
                if not hasattr(child, 'name') or not child.name:
                    i += 1
                    continue
                
                tag = child.name
                text = child.get_text(strip=True)
                classes = child.get('class', [])
                
                # 处理 h3 标签（可能是空的，下一个兄弟是 p 标签）
                if tag == 'h3':
                    # 检查下一个兄弟节点是否是 p 标签
                    if i + 1 < len(children):
                        next_child = children[i + 1]
                        if next_child.name == 'p':
                            h3_text = next_child.get_text(strip=True)
                            if h3_text:
                                md_lines.append(f"### {h3_text}")
                                md_lines.append("")
                            i += 1  # 跳过下一个 p 标签
                    i += 1
                    continue
                
                # 处理 h1 标签（可能是空的，下一个兄弟是 p 标签）
                elif tag == 'h1':
                    # 检查下一个兄弟节点是否是 p 标签
                    if i + 1 < len(children):
                        next_child = children[i + 1]
                        if next_child.name == 'p':
                            h1_text = next_child.get_text(strip=True)
                            if h1_text:
                                # 处理标题，提取主标题和系列名称
                                title_parts = self._extract_title_and_series(h1_text)
                                title = title_parts['main_title']
                                series_name = title_parts['series_name']
                                md_lines.append(f"# {title}")
                                if series_name:
                                    md_lines.append(f"> 系列：{series_name}")
                                md_lines.append("")
                            i += 1  # 跳过下一个 p 标签
                    i += 1
                    continue
                
                # 处理 h2 标签（可能是空的，下一个兄弟是 p 标签）
                elif tag == 'h2':
                    # 检查下一个兄弟节点是否是 p 标签
                    h2_text = text
                    if i + 1 < len(children):
                        next_child = children[i + 1]
                        if next_child.name == 'p':
                            h2_text = next_child.get_text(strip=True)
                            if h2_text:
                                md_lines.append(f"## {h2_text}")
                                md_lines.append("")
                                # 尝试从 h2 文本中提取系列名称
                                if not series_name:
                                    # 清理 h2 文本，去除破折号等前缀
                                    cleaned_h2 = h2_text.lstrip('—').strip()
                                    # 检查是否符合系列名称模式
                                    if self._is_series_name(cleaned_h2):
                                        # 提取系列名称，去除序号
                                        series_name = re.sub(r'[①②③④⑤⑥⑦⑧⑨⑩\d]+$', '', cleaned_h2).strip()
                            i += 1  # 跳过下一个 p 标签
                    elif text:
                        # 如果 h2 标签本身有文本
                        md_lines.append(f"## {text}")
                        md_lines.append("")
                        # 尝试从 h2 文本中提取系列名称
                        if not series_name:
                            # 清理 h2 文本，去除破折号等前缀
                            cleaned_h2 = text.lstrip('—').strip()
                            # 检查是否符合系列名称模式
                            if self._is_series_name(cleaned_h2):
                                # 提取系列名称，去除序号
                                series_name = re.sub(r'[①②③④⑤⑥⑦⑧⑨⑩\d]+$', '', cleaned_h2).strip()
                    i += 1
                    continue
                
                # 处理 p 标签
                elif tag == 'p':
                    # <p class="sec"> = 作者署名
                    if 'sec' in classes:
                        # 提取作者名（去掉《人民日报》及之后的部分）
                        author_match = re.match(r'(.+?)《人民日报》', text)
                        if author_match:
                            author = author_match.group(1).strip()
                            # 清理 "本报记者" 等前缀
                            author = re.sub(r'^(本报记者|本报通讯员|记者)\s*', '', author).strip()
                        md_lines.append(f"> {text}")
                        md_lines.append("")
                    # 普通 p 标签，不作为标题处理（避免将肩题作为主标题）
                    else:
                        pass
                    i += 1
                    continue
                
                # 处理 div 标签（正文容器）
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
                    i += 1
                    continue
                
                # 其他标签
                else:
                    i += 1
                    continue
            
            markdown_body = '\n'.join(md_lines).strip()
            content = '\n'.join(content_paragraphs)
            
            # 后备标题提取 - 确保优先使用h1标签作为主标题
            if not title:
                # 查找 h1 标签及其后续的 p 标签
                h1 = article_div.find('h1')
                if h1:
                    # 查找 h1 后的第一个 p 标签
                    next_p = h1.find_next_sibling('p')
                    if next_p:
                        text = next_p.get_text(strip=True)
                        if text:
                            title_parts = self._extract_title_and_series(text)
                            title = title_parts['main_title']
                            series_name = title_parts['series_name']
                    # 如果没有找到 p 标签，尝试直接从 h1 获取
                    if not title:
                        text = h1.get_text(strip=True)
                        if text:
                            title_parts = self._extract_title_and_series(text)
                            title = title_parts['main_title']
                            series_name = title_parts['series_name']
            
            # 最后尝试从 soup 中查找
            if not title:
                h1 = soup.find('h1')
                if h1:
                    next_p = h1.find_next_sibling('p')
                    if next_p:
                        text = next_p.get_text(strip=True)
                        if text:
                            title_parts = self._extract_title_and_series(text)
                            title = title_parts['main_title']
                            series_name = title_parts['series_name']
                    if not title:
                        text = h1.get_text(strip=True)
                        if text:
                            title_parts = self._extract_title_and_series(text)
                            title = title_parts['main_title']
                            series_name = title_parts['series_name']
            
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
                'series_name': series_name,
                'url': url
            }
        except Exception as e:
            logging.error(f"解析文章 {url} 失败: {str(e)}")
            return None
    
    def _extract_title_and_series(self, text: str) -> Dict:
        """提取主标题和系列名称
        
        Args:
            text: 原始标题文本
            
        Returns:
            Dict: 包含主标题和系列名称的字典
        """
        main_title = text
        series_name = ""
        
        # 1. 处理破折号，优先提取主标题（破折号之后的内容）
        if '——' in text:
            parts = text.split('——')
            if len(parts) >= 2:
                main_title = parts[1].strip()
        
        # 2. 提取系列名称（从括号中提取）
        # 匹配括号中的内容
        series_patterns = [
            r'\(([^)]+)\)',  # 匹配中文或英文括号中的内容
            r'\（([^）]+)\）',  # 匹配中文括号中的内容
        ]
        
        for pattern in series_patterns:
            matches = re.findall(pattern, main_title)
            for match in matches:
                series_candidate = match.strip()
                # 检查是否符合系列名称模式
                if self._is_series_name(series_candidate):
                    series_name = series_candidate
                    # 从主标题中移除系列名称
                    main_title = main_title.replace(f"({series_candidate})", "").replace(f"（{series_candidate}）", "").strip()
                    break
            if series_name:
                break
        
        return {
            'main_title': main_title,
            'series_name': series_name
        }
    
    def _is_series_name(self, text: str) -> bool:
        """判断文本是否为系列名称
        
        Args:
            text: 待判断的文本
            
        Returns:
            bool: 是否为系列名称
        """
        # 系列名称模式
        series_patterns = [
            r'.*[①②③④⑤⑥⑦⑧⑨⑩]',  # 带圆圈序号
            r'.*\(\d+\)',  # 带数字序号
            r'.*\（\d+\）',  # 带中文数字序号
            r'.*\（[一二三四五六七八九十]+\）',  # 带中文数字
            r'.*\（[上下中下]+\）',  # 带上中下
            r'.*之\d+',  # 带之X
            r'.*之[一二三四五六七八九十]+',  # 带之中文数字
            r'透过.*看.*\d+',  # 透过X看X系列（如：透过数据看潜能②）
            r'追梦人.*',  # 特殊系列
            r'人文对话',  # 特殊系列
            r'记者手记',  # 特殊系列
            r'青年观',  # 特殊系列
            r'深阅读',  # 特殊系列
        ]
        
        for pattern in series_patterns:
            if re.match(pattern, text):
                return True
        
        return False
    
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


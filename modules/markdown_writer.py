#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown 文件写入模块 - 将文章保存为结构化 Markdown + YAML frontmatter
"""

import os
import re
import logging
from datetime import datetime
from typing import Dict, Optional


class MarkdownWriter:
    """将文章写入 Markdown 文件（Obsidian Vault 格式）"""
    
    def __init__(self, vault_dir: str = "data/vault"):
        self.vault_dir = vault_dir
    
    def save_article(self, article: Dict, date: datetime,
                     section_id: str = "", section_name: str = "") -> Optional[str]:
        """
        保存文章为 Markdown 文件
        
        Args:
            article: 包含 title, content, markdown_body, author, plate,
                     keywords, category, summary, url 等字段
            date: 文章日期
            section_id: 版面编号 (如 "01")
            section_name: 版面名称 (如 "要闻")
        
        Returns:
            保存的文件路径，失败返回 None
        """
        try:
            title = article.get('title', '未知标题').strip()
            if not title:
                title = '未知标题'
            
            # 构建目录路径: vault/2026/02/2026-02-02/01-要闻/
            date_str = date.strftime('%Y-%m-%d')
            year = date.strftime('%Y')
            month = date.strftime('%m')
            
            section_dir = f"{section_id}-{section_name}" if section_id and section_name else "其他"
            
            dir_path = os.path.join(self.vault_dir, year, month, date_str, section_dir)
            os.makedirs(dir_path, exist_ok=True)
            
            # 文件名：清理标题中的非法字符
            safe_title = self._sanitize_filename(title)
            # 限制文件名长度（含路径不超过系统限制）
            if len(safe_title) > 80:
                safe_title = safe_title[:80]
            
            filepath = os.path.join(dir_path, f"{safe_title}.md")
            
            # 生成 YAML frontmatter
            frontmatter = self._build_frontmatter(article, date, section_id, section_name)
            
            # 获取格式化的正文
            markdown_body = article.get('markdown_body', '')
            if not markdown_body:
                # 如果没有 markdown_body，用纯文本 content 做后备
                markdown_body = article.get('content', '')
            
            # 组合完整内容
            full_content = f"{frontmatter}\n{markdown_body}\n"
            
            # 写入文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            logging.info(f"Markdown 已保存: {filepath}")
            return filepath
            
        except Exception as e:
            logging.error(f"保存 Markdown 失败: {str(e)}")
            return None
    
    def _build_frontmatter(self, article: Dict, date: datetime,
                           section_id: str, section_name: str) -> str:
        """构建 YAML frontmatter"""
        title = article.get('title', '').replace('"', '\\"')
        author = article.get('author', '').replace('"', '\\"')
        plate = article.get('plate', section_name)
        category = article.get('category', '')
        keywords = article.get('keywords', [])
        word_count = len(article.get('content', ''))
        url = article.get('url', '')
        summary = article.get('summary', '').replace('"', '\\"')
        
        # 系列信息
        series_name = article.get('series_name', '') or ''
        series_int_id = article.get('series_int_id')
        series_part = article.get('series_part')
        related_titles = article.get('related_titles', [])
        
        # 关键词列表
        if keywords:
            kw_str = ', '.join(keywords[:8])
            kw_line = f"keywords: [{kw_str}]"
        else:
            kw_line = "keywords: []"
        
        lines = [
            "---",
            f'title: "{title}"',
            f"date: {date.strftime('%Y-%m-%d')}",
            f'section: "第{section_id}版"' if section_id else 'section: ""',
            f'section_name: "{plate}"',
            f'author: "{author}"',
            f'category: "{category}"',
            kw_line,
            f"word_count: {word_count}",
            f'source_url: "{url}"',
        ]
        
        # 系列字段（仅在有系列时添加）
        if series_int_id:
            lines.append(f"series: {series_int_id}")
            if series_name:
                lines.append(f'series_name: "{series_name}"')
            if series_part is not None:
                lines.append(f"series_part: {series_part}")
        
        # 关联文章（Obsidian wiki-link 格式）
        if related_titles:
            lines.append("related:")
            for rt in related_titles:
                lines.append(f'  - "[[{rt}]]"')
        
        lines.append("---")
        lines.append("")
        
        return '\n'.join(lines)
    
    def _sanitize_filename(self, name: str) -> str:
        """清理文件名中的非法字符"""
        # 替换非法字符
        name = re.sub(r'[\\/:*?"<>|]', '', name)
        # 替换空白为空格
        name = re.sub(r'\s+', ' ', name).strip()
        # 移除前导/尾随点号
        name = name.strip('.')
        return name or '未知标题'

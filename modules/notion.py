#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion API交互模块
"""

import logging
import sys
from datetime import datetime
from typing import List, Dict, Optional
from notion_client import Client
from notion_client.errors import APIResponseError
from modules.utils import Config


class NotionAPI:
    """Notion API交互类"""
    def __init__(self, config: Config):
        self.config = config
        self.token = self.config.get('notion.token')
        self.database_id = self.config.get('notion.database_id')
        if not self.token or not self.database_id:
            logging.error("Notion API配置不完整")
            sys.exit(1)
        
        self.notion = Client(auth=self.token)
    
    def get_existing_articles(self) -> List[Dict]:
        """获取已存在的文章"""
        try:
            existing_articles = []
            has_more = True
            start_cursor = None
            
            while has_more:
                response = self.notion.databases.query(
                    database_id=self.database_id,
                    start_cursor=start_cursor
                )
                
                for page in response.get('results', []):
                    properties = page.get('properties', {})
                    article = {
                        'id': page.get('id'),
                        'title': properties.get('标题', {}).get('title', [{}])[0].get('plain_text', ''),
                        'url': properties.get('URL', {}).get('url', ''),
                        'plate': properties.get('版面名称', {}).get('select', {}).get('name', ''),
                        'date': properties.get('发布日期', {}).get('date', {}).get('start', ''),
                        'content': ''  # 内容需要单独获取
                    }
                    existing_articles.append(article)
                
                has_more = response.get('has_more', False)
                start_cursor = response.get('next_cursor')
            
            return existing_articles
        except APIResponseError as e:
            logging.error(f"获取Notion数据库内容失败: {str(e)}")
            return []
    
    def create_page(self, article: Dict, date: datetime):
        """创建Notion页面"""
        try:
            # 创建页面元数据
            properties = {
                '标题': {
                    'title': [
                        {
                            'text': {
                                'content': article.get('title', '')
                            }
                        }
                    ]
                },
                'URL': {
                    'url': article.get('url', '')
                },
                '版面名称': {
                    'select': {
                        'name': article.get('plate', '其他')
                    }
                },
                '发布日期': {
                    'date': {
                        'start': date.strftime('%Y-%m-%d')
                    }
                },
                '分类': {
                    'select': {
                        'name': article.get('category', '其他')
                    }
                },
                '关键词': {
                    'multi_select': [{'name': keyword} for keyword in article.get('keywords', [])[:5]]
                }
            }
            
            # 创建页面
            page = self.notion.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            
            # 添加内容
            content = article.get('content', '')
            if content:
                blocks = []
                for paragraph in content.split('\n'):
                    if paragraph.strip():
                        blocks.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {
                                            "content": paragraph.strip()
                                        }
                                    }
                                ]
                            }
                        })
                
                if blocks:
                    self.notion.blocks.children.append(
                        block_id=page.get('id'),
                        children=blocks
                    )
            
            logging.info(f"成功创建Notion页面: {article.get('title', '')}")
        except APIResponseError as e:
            logging.error(f"创建Notion页面失败: {str(e)}")
    
    def update_page(self, page_id: str, article: Dict):
        """更新Notion页面"""
        try:
            # 更新页面元数据
            properties = {
                '标题': {
                    'title': [
                        {
                            'text': {
                                'content': article.get('title', '')
                            }
                        }
                    ]
                },
                'URL': {
                    'url': article.get('url', '')
                },
                '版面名称': {
                    'select': {
                        'name': article.get('plate', '其他')
                    }
                },
                '分类': {
                    'select': {
                        'name': article.get('category', '其他')
                    }
                },
                '关键词': {
                    'multi_select': [{'name': keyword} for keyword in article.get('keywords', [])[:5]]
                }
            }
            
            # 更新页面
            self.notion.pages.update(
                page_id=page_id,
                properties=properties
            )
            
            # 更新内容
            content = article.get('content', '')
            if content:
                # 清除现有内容
                blocks = self.notion.blocks.children.list(block_id=page_id)
                for block in blocks.get('results', []):
                    self.notion.blocks.delete(block_id=block.get('id'))
                
                # 添加新内容
                new_blocks = []
                for paragraph in content.split('\n'):
                    if paragraph.strip():
                        new_blocks.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {
                                            "content": paragraph.strip()
                                        }
                                    }
                                ]
                            }
                        })
                
                if new_blocks:
                    self.notion.blocks.children.append(
                        block_id=page_id,
                        children=new_blocks
                    )
            
            logging.info(f"成功更新Notion页面: {article.get('title', '')}")
        except APIResponseError as e:
            logging.error(f"更新Notion页面失败: {str(e)}")

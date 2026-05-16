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
import httpx
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

    def _rich_text_plain(self, properties: Dict, *names: str) -> str:
        """读取 rich_text 属性，兼容英文和中文字段名。"""
        for name in names:
            prop = properties.get(name, {})
            rich_text = prop.get('rich_text', [])
            if rich_text:
                return ''.join(part.get('plain_text', '') for part in rich_text)
        return ''

    def _create_page_with_fallback(self, properties: Dict):
        """创建页面；如果 Notion 数据库还没加新字段，自动降级。"""
        while True:
            try:
                return self.notion.pages.create(
                    parent={"database_id": self.database_id},
                    properties=properties
                )
            except APIResponseError as e:
                message = str(e)
                if 'Article ID' in message and 'Article ID' in properties:
                    logging.warning("Notion 数据库缺少 Article ID 字段，本次同步将降级为 URL/标题去重")
                    properties.pop('Article ID', None)
                    continue
                if 'schema has exceeded the maximum size' in message and '关键词' in properties:
                    logging.warning("Notion schema 过大，去掉关键词后重试")
                    properties.pop('关键词', None)
                    continue
                raise

    def _update_page_with_fallback(self, page_id: str, properties: Dict):
        """更新页面；如果 Notion 数据库还没加新字段，自动降级。"""
        while True:
            try:
                return self.notion.pages.update(
                    page_id=page_id,
                    properties=properties
                )
            except APIResponseError as e:
                message = str(e)
                if 'Article ID' in message and 'Article ID' in properties:
                    logging.warning("Notion 数据库缺少 Article ID 字段，本次更新将跳过该字段")
                    properties.pop('Article ID', None)
                    continue
                if 'schema has exceeded the maximum size' in message and '关键词' in properties:
                    logging.warning("Notion schema 过大，去掉关键词后重试")
                    properties.pop('关键词', None)
                    continue
                raise
    
    def get_existing_articles(self) -> List[Dict]:
        """获取已存在的文章"""
        try:
            existing_articles = []
            has_more = True
            start_cursor = None
            
            while has_more:
                # 使用search API查询数据库中的内容
                response = self.notion.search(
                    filter={
                        "property": "object",
                        "value": "page"
                    },
                    start_cursor=start_cursor
                )
                
                for page in response.get('results', []):
                    # 检查页面是否属于目标数据库
                    parent = page.get('parent', {})
                    if parent.get('type') == 'database_id' and parent.get('database_id') == self.database_id:
                        properties = page.get('properties', {})
                        article = {
                            'id': page.get('id'),
                            'article_id': self._rich_text_plain(properties, 'Article ID', '文章ID'),
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
        except httpx.RequestError as e:
            logging.error(f"Notion API网络连接失败: {str(e)}")
            return []
        except Exception as e:
            logging.error(f"获取Notion数据库内容时发生未知错误: {str(e)}")
            return []
    
    def create_page(self, article: Dict, date: datetime):
        """创建Notion页面"""
        try:
            # 检查标题和内容是否为空
            title = article.get('title', '').strip()
            content = article.get('content', '').strip()
            
            # 如果标题和内容都为空，跳过创建
            if not title and not content:
                logging.warning(f"跳过创建页面：标题和内容都为空 - URL: {article.get('url', '')}")
                return
            
            # 如果只有标题为空，使用默认标题
            if not title:
                title = "无标题"
                logging.warning(f"使用默认标题创建页面 - URL: {article.get('url', '')}")
            
            # 创建页面元数据
            properties = {
                '标题': {
                    'title': [
                        {
                            'text': {
                                'content': title
                            }
                        }
                    ]
                },
                'URL': {
                    'url': article.get('url', '')
                },
                '版面名称': {
                    'select': {
                        'name': article.get('plate') or '其他'
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

            article_id = article.get('article_id')
            if article_id:
                properties['Article ID'] = {
                    'rich_text': [{'text': {'content': article_id}}]
                }
            
            # 系列信息（仅在有系列时添加）
            series_name = article.get('series_name')
            if series_name:
                properties['系列'] = {
                    'rich_text': [{'text': {'content': series_name}}]
                }
                series_part = article.get('series_part')
                if series_part is not None:
                    properties['系列序号'] = {
                        'number': series_part
                    }
            
            # 创建页面（带 schema 大小降级重试）
            page = self._create_page_with_fallback(properties)
            
            # 添加内容
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
            else:
                # 添加默认内容提示
                blocks = [{
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "无内容"
                                }
                            }
                        ]
                    }
                }]
                self.notion.blocks.children.append(
                    block_id=page.get('id'),
                    children=blocks
                )
            
            logging.info(f"成功创建Notion页面: {title}")
            return page.get('id')
        except APIResponseError as e:
            logging.error(f"创建Notion页面失败: {str(e)}")
            return None
        except httpx.RequestError as e:
            logging.error(f"Notion API网络连接失败: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"创建Notion页面时发生未知错误: {str(e)}")
            return None
    
    def update_page(self, page_id: str, article: Dict):
        """更新Notion页面"""
        try:
            # 检查标题和内容是否为空
            title = article.get('title', '').strip()
            content = article.get('content', '').strip()
            
            # 如果只有标题为空，使用默认标题
            if not title:
                title = "无标题"
                logging.warning(f"使用默认标题更新页面 - URL: {article.get('url', '')}")
            
            # 更新页面元数据
            properties = {
                '标题': {
                    'title': [
                        {
                            'text': {
                                'content': title
                            }
                        }
                    ]
                },
                'URL': {
                    'url': article.get('url', '')
                },
                '版面名称': {
                    'select': {
                        'name': article.get('plate') or '其他'
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

            article_id = article.get('article_id')
            if article_id:
                properties['Article ID'] = {
                    'rich_text': [{'text': {'content': article_id}}]
                }
            
            # 更新页面
            self._update_page_with_fallback(page_id, properties)
            
            # 清除现有内容
            blocks = self.notion.blocks.children.list(block_id=page_id)
            for block in blocks.get('results', []):
                self.notion.blocks.delete(block_id=block.get('id'))
            
            # 更新内容
            if content:
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
            else:
                # 添加默认内容提示
                blocks = [{
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "无内容"
                                }
                            }
                        ]
                    }
                }]
                self.notion.blocks.children.append(
                    block_id=page_id,
                    children=blocks
                )
            
            logging.info(f"成功更新Notion页面: {title}")
            return True
        except APIResponseError as e:
            logging.error(f"更新Notion页面失败: {str(e)}")
            return False
        except httpx.RequestError as e:
            logging.error(f"Notion API网络连接失败: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"更新Notion页面时发生未知错误: {str(e)}")
            return False

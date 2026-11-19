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
        self._data_source_id = None

    def _rich_text_plain(self, properties: Dict, *names: str) -> str:
        """读取 rich_text 属性，兼容英文和中文字段名。"""
        for name in names:
            prop = properties.get(name) or {}
            rich_text = prop.get('rich_text', [])
            if rich_text:
                return ''.join(part.get('plain_text', '') for part in rich_text)
        return ''

    def _select_name(self, properties: Dict, name: str) -> str:
        prop = properties.get(name) or {}
        selected = prop.get('select') or {}
        return selected.get('name', '')

    def _date_start(self, properties: Dict, name: str) -> str:
        prop = properties.get(name) or {}
        date_value = prop.get('date') or {}
        return date_value.get('start', '')

    def _create_page_with_fallback(self, properties: Dict, children: List[Dict]):
        """创建页面；如果 Notion 数据库还没加新字段，自动降级。"""
        while True:
            try:
                return self.notion.pages.create(
                    parent=({"data_source_id": self._data_source_id} if self._data_source_id else {"database_id": self.database_id}),
                    children=children, properties=properties
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

    def _get_data_source_id(self) -> Optional[str]:
        """新版 Notion API 中，数据库查询需要 data_source_id。"""
        if self._data_source_id:
            return self._data_source_id
        database = self.notion.databases.retrieve(database_id=self.database_id)
        data_sources = database.get('data_sources') or []
        if len(data_sources) == 1:
            self._data_source_id = data_sources[0]['id']
        elif len(data_sources) > 1:
            raise RuntimeError('目标 Notion 库含多个数据源，无法安全选择；已停止同步')
        return self._data_source_id

    def get_existing_articles(self) -> List[Dict]:
        """只在目标库内查询；读取失败不可当作空库继续写入。"""
        existing_articles = []
        data_source_id = self._get_data_source_id()
        if data_source_id:
            query = self.notion.data_sources.query
            params = {'data_source_id': data_source_id}
        elif hasattr(self.notion.databases, 'query'):
            query = self.notion.databases.query
            params = {'database_id': self.database_id}
        else:
            raise RuntimeError('未获取目标 Notion 数据源，已停止同步')

        while True:
            response = query(**params, page_size=100)
            for page in response['results']:
                properties = page['properties']
                title_items = properties.get('标题', {}).get('title', [])
                existing_articles.append({
                    'id': page['id'],
                    'article_id': self._rich_text_plain(properties, 'Article ID', '文章ID'),
                    'title': ''.join(item.get('plain_text', '') for item in title_items),
                    'url': (properties.get('URL') or {}).get('url', ''),
                    'plate': self._select_name(properties, '版面名称'),
                    'date': self._date_start(properties, '发布日期'),
                })
            if not response['has_more']:
                return existing_articles
            cursor = response.get('next_cursor')
            if not cursor or cursor == params.get('start_cursor'):
                raise RuntimeError('目标库分页不完整，已停止同步')
            params['start_cursor'] = cursor

    @staticmethod
    def _body_blocks(content: str) -> List[Dict]:
        paragraphs = [s.strip() for s in content.splitlines() if s.strip()] or ['无内容']
        # 单次请求至多 100 个块。保留换行，长段拆为合法长度的富文本。
        group = (len(paragraphs) + 99) // 100
        blocks = []
        for i in range(0, len(paragraphs), group):
            text = '\n'.join(paragraphs[i:i + group])
            runs = [{'type': 'text', 'text': {'content': text[j:j + 1000]}}
                    for j in range(0, len(text), 1000)]
            if len(runs) > 100:
                raise ValueError('正文超出单次安全写入上限，未截断正文')
            blocks.append({'object': 'block', 'type': 'paragraph', 'paragraph': {'rich_text': runs}})
        return blocks

    def create_page(self, article: Dict, date: datetime):
        """标题与正文随一次创建请求提交，避免留下仅有标题的页面。"""
        try:
            if not (article.get('title') or '').strip() and not (article.get('content') or '').strip():
                logging.warning('标题与正文均为空，跳过创建')
                return None
            properties = self.build_page_properties(article, date)
            blocks = self._body_blocks(article.get('content') or '')
            page = self._create_page_with_fallback(properties, blocks)
            return page['id']
        except Exception as e:
            logging.error('创建 Notion 页面失败：%s', e)
            return None

    def update_page(self, page_id: str, article: Dict):
        """显式替换正文：新内容写入成功前，绝不删除旧正文。"""
        try:
            if not (article.get('content') or '').strip():
                raise ValueError('本地正文为空，保留 Notion 原正文；只改属性请使用 metadata-only')
            new_blocks = self._body_blocks(article['content'])
            old_ids = []
            params = {'block_id': page_id}
            while True:
                response = self.notion.blocks.children.list(**params)
                old_ids.extend(block['id'] for block in response['results'])
                if not response['has_more']:
                    break
                cursor = response.get('next_cursor')
                if not cursor or cursor == params.get('start_cursor'):
                    raise RuntimeError('旧正文分页不完整，已停止替换')
                params['start_cursor'] = cursor
            self._update_page_with_fallback(page_id, self.build_page_properties(article))
            self.notion.blocks.children.append(block_id=page_id, children=new_blocks)
            for block_id in old_ids:
                self.notion.blocks.delete(block_id=block_id)
            return True
        except Exception as e:
            logging.error('更新 Notion 页面失败：%s', e)
            return False

    def build_page_properties(self, article: Dict, date: Optional[datetime] = None) -> Dict:
        """构建 Notion 页面属性。"""
        title = article.get('title', '').strip() or "无标题"
        url = article.get('url') or article.get('source_url') or ''
        plate = article.get('plate') or article.get('section_name') or '其他'

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
                'url': url
            },
            '版面名称': {
                'select': {
                    'name': plate
                }
            },
            '分类': {
                'select': {
                    'name': article.get('category', '其他') or '其他'
                }
            },
            '关键词': {
                'multi_select': [{'name': keyword} for keyword in article.get('keywords', [])[:5]]
            }
        }

        date_str = article.get('date', '')
        if date:
            date_str = date.strftime('%Y-%m-%d')
        if date_str:
            properties['发布日期'] = {
                'date': {
                    'start': date_str
                }
            }

        article_id = article.get('article_id')
        if article_id:
            properties['Article ID'] = {
                'rich_text': [{'text': {'content': article_id}}]
            }

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

        return properties

    def update_page_metadata(self, page_id: str, article: Dict) -> bool:
        """只更新 Notion 页面属性，不改正文。适合批量回填 Article ID。"""
        try:
            properties = self.build_page_properties(article)
            self._update_page_with_fallback(page_id, properties)
            logging.info(f"成功更新Notion页面属性: {article.get('title', '')}")
            return True
        except APIResponseError as e:
            logging.error(f"更新Notion页面属性失败: {str(e)}")
            return False
        except httpx.RequestError as e:
            logging.error(f"Notion API网络连接失败: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"更新Notion页面属性时发生未知错误: {str(e)}")
            return False

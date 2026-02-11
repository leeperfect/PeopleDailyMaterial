#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系列文章检测与注册表管理模块

功能：
1. 通过标题正则匹配，自动检测系列文章（跨日连载、上中下篇等）
2. 管理持久化注册表 (series_registry.json)，支持跨批次关联
3. 为文章添加 series_id / series_name / series_part 字段
"""

import os
import re
import json
import logging
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime


# ============================================================
#  标题模式匹配规则
# ============================================================

# 中文数字→阿拉伯数字映射
_CN_NUM = {
    '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15,
    '十六': 16, '十七': 17, '十八': 18, '十九': 19, '二十': 20,
}

_POSITIONAL = {'上': 1, '中': 2, '下': 3}

# 匹配规则列表 (pattern, group_index_for_part)
_SERIES_PATTERNS = [
    # （一）（二）（三）—— 最常见
    (re.compile(r'[（(]([一二三四五六七八九十]{1,3})[）)]'), 'cn_num'),
    # （上）（中）（下）
    (re.compile(r'[（(]([上中下])[）)]'), 'positional'),
    # 之一、之二
    (re.compile(r'之([一二三四五六七八九十]{1,3})'), 'cn_num'),
    # 之1、之2（阿拉伯数字）
    (re.compile(r'之(\d+)'), 'arabic'),
    # ①②③
    (re.compile(r'([①②③④⑤⑥⑦⑧⑨⑩])'), 'circled'),
    # (1) (2) 或 （1）（2）
    (re.compile(r'[（(](\d+)[）)]'), 'arabic'),
]

_CIRCLED_NUMS = {'①': 1, '②': 2, '③': 3, '④': 4, '⑤': 5,
                 '⑥': 6, '⑦': 7, '⑧': 8, '⑨': 9, '⑩': 10}


class SeriesDetector:
    """系列文章检测器"""

    def __init__(self, registry_path: str = "data/series_registry.json"):
        self.registry_path = registry_path
        self.registry: Dict[str, Dict] = {}
        self._load_registry()

    # ============================================================
    #  注册表读写
    # ============================================================

    def _load_registry(self):
        """从磁盘加载注册表"""
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    self.registry = json.load(f)
                
                # 迁移：确保所有系列都有 int_id
                max_id = 0
                # 先找出已有的最大ID
                for info in self.registry.values():
                    if 'int_id' in info:
                        max_id = max(max_id, info['int_id'])
                
                # 为缺失ID的系列补全
                migrated_count = 0
                for sid, info in self.registry.items():
                    if 'int_id' not in info:
                        max_id += 1
                        info['int_id'] = max_id
                        migrated_count += 1
                
                if migrated_count > 0:
                    logging.info(f"已迁移系列注册表：为 {migrated_count} 个系列补充了编号")
                    self.save_registry()

                logging.info(f"已加载系列注册表：{len(self.registry)} 个系列 (Max ID: {max_id})")
            except Exception as e:
                logging.warning(f"加载系列注册表失败: {e}")
                self.registry = {}
        else:
            self.registry = {}

    def save_registry(self):
        """保存注册表到磁盘"""
        os.makedirs(os.path.dirname(self.registry_path) or '.', exist_ok=True)
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, ensure_ascii=False, indent=2)
        logging.info(f"系列注册表已保存：{len(self.registry)} 个系列")

    def _get_next_int_id(self) -> int:
        """获取下一个可用的整数ID"""
        max_id = 0
        for info in self.registry.values():
            if 'int_id' in info:
                max_id = max(max_id, info['int_id'])
        return max_id + 1

    # ============================================================
    #  标题模式检测
    # ============================================================

    @staticmethod
    def detect_series_from_title(title: str) -> Optional[Tuple[str, int]]:
        """
        检测标题是否属于系列文章。

        Returns:
            (series_name, part_number) 或 None
            series_name: 系列名称（标题去除序号部分）
            part_number: 序号（1, 2, 3...）
        """
        for pattern, num_type in _SERIES_PATTERNS:
            match = pattern.search(title)
            if match:
                raw_part = match.group(1)

                # 解析序号
                if num_type == 'cn_num':
                    part = _CN_NUM.get(raw_part)
                    if part is None:
                        continue
                elif num_type == 'positional':
                    part = _POSITIONAL.get(raw_part)
                    if part is None:
                        continue
                elif num_type == 'arabic':
                    part = int(raw_part)
                elif num_type == 'circled':
                    part = _CIRCLED_NUMS.get(raw_part)
                    if part is None:
                        continue
                else:
                    continue

                # 系列名 = 标题去除匹配到的序号部分，再清理
                series_name = pattern.sub('', title).strip()
                # 去除结尾可能残留的标点
                series_name = re.sub(r'[：:——\-·\s]+$', '', series_name).strip()
                series_name = re.sub(r'^[：:——\-·\s]+', '', series_name).strip()

                if len(series_name) >= 2:  # 系列名至少2个字
                    return series_name, part

        return None

    @staticmethod
    def _make_series_id(series_name: str) -> str:
        """为系列名生成稳定的 ID"""
        h = hashlib.md5(series_name.encode('utf-8')).hexdigest()[:8]
        return f"series_{h}"

    # ============================================================
    #  批量检测与注册
    # ============================================================

    def detect_and_register(self, articles: List[Dict]) -> List[Dict]:
        """
        对一组文章进行系列检测。

        为每篇文章添加：
            article['series_id']   - 系列唯一标识（series_md5）
            article['series_int_id'] - 系列整数编号（自动递增，用于 Obsidian）
            article['series_name'] - 系列名称
            article['series_part'] - 序号
        
        同时更新内存中的注册表。

        Args:
            articles: 文章列表，每篇需有 'title', 'index' 字段

        Returns:
            原列表（已就地修改）
        """
        # 第一轮：自动检测
        detected_groups: Dict[str, List[Dict]] = {}  # series_name → [articles]

        for art in articles:
            title = art.get('title', '')
            result = self.detect_series_from_title(title)

            if result:
                series_name, part = result
                art['series_name'] = series_name
                art['series_part'] = part
                art['series_id'] = self._make_series_id(series_name)
                # int_id 稍后统一处理

                if series_name not in detected_groups:
                    detected_groups[series_name] = []
                detected_groups[series_name].append(art)
            else:
                art['series_name'] = None
                art['series_part'] = None
                art['series_id'] = None
                art['series_int_id'] = None

        # 第二轮：过滤掉只有一篇的"系列"（单篇不算系列）
        # 但如果注册表中已有该系列，保留（跨批次）
        for series_name, group in detected_groups.items():
            sid = self._make_series_id(series_name)
            if len(group) < 2 and sid not in self.registry:
                # 只有1篇且注册表中没有历史记录，取消标记
                for art in group:
                    art['series_name'] = None
                    art['series_part'] = None
                    art['series_id'] = None
                    art['series_int_id'] = None

        # 第三轮：匹配注册表中的已知系列（跨批次）
        for art in articles:
            if art.get('series_id'):
                continue  # 已检测到
            title = art.get('title', '')
            for sid, info in self.registry.items():
                existing_name = info.get('name', '')
                # 如果标题包含已知系列名（模糊匹配）
                if existing_name and len(existing_name) >= 4 and existing_name in title:
                    # 尝试提取序号
                    result = self.detect_series_from_title(title)
                    if result:
                        _, part = result
                    else:
                        part = None
                    art['series_id'] = sid
                    art['series_name'] = existing_name
                    art['series_part'] = part
                    break

        # 更新注册表并回填 int_id
        for art in articles:
            sid = art.get('series_id')
            if not sid:
                continue

            # 如果是新系列，注册并分配 int_id
            if sid not in self.registry:
                self.registry[sid] = {
                    'name': art['series_name'],
                    'int_id': self._get_next_int_id(),
                    'created': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'articles': []
                }
            
            # 确保 article 对象有 int_id
            art['series_int_id'] = self.registry[sid].get('int_id')

            # 避免重复添加文章记录（通过 title+date 去重）
            entry = {
                'title': art.get('title', ''),
                'date': art.get('_date', datetime.now()).strftime('%Y-%m-%d')
                        if hasattr(art.get('_date', ''), 'strftime')
                        else str(art.get('date', '')),
                'index': art.get('index'),
                'part': art.get('series_part'),
            }
            existing_titles = [a['title'] for a in self.registry[sid]['articles']]
            if entry['title'] not in existing_titles:
                self.registry[sid]['articles'].append(entry)

        return articles

    def manual_group(self, articles: List[Dict], group_name: str, indices: List[int]):
        """
        手动编组：将指定 index 的文章归入同一系列。

        Args:
            articles: 文章列表
            group_name: 用户指定的组名
            indices: 要编组的文章 index 列表
        """
        sid = self._make_series_id(group_name)

        # 确保系列已注册
        if sid not in self.registry:
            self.registry[sid] = {
                'name': group_name,
                'int_id': self._get_next_int_id(),
                'created': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'articles': [],
                'manual': True,
            }
        
        series_int_id = self.registry[sid]['int_id']

        for art in articles:
            if art.get('index') in indices:
                art['series_id'] = sid
                art['series_name'] = group_name
                art['series_int_id'] = series_int_id
                
                # 如果已有序号保留，否则按顺序编号
                if not art.get('series_part'):
                    art['series_part'] = indices.index(art['index']) + 1

        # 更新注册表中的文章列表
        for art in articles:
            if art.get('series_id') == sid:
                entry = {
                    'title': art.get('title', ''),
                    'date': art.get('_date', datetime.now()).strftime('%Y-%m-%d')
                            if hasattr(art.get('_date', ''), 'strftime')
                            else str(art.get('date', '')),
                    'index': art.get('index'),
                    'part': art.get('series_part'),
                }
                existing_titles = [a['title'] for a in self.registry[sid]['articles']]
                if entry['title'] not in existing_titles:
                    self.registry[sid]['articles'].append(entry)

    def get_series_articles(self, series_id: str) -> List[Dict]:
        """获取注册表中某系列的所有文章"""
        if series_id in self.registry:
            return self.registry[series_id].get('articles', [])
        return []

    def get_related_titles(self, article: Dict) -> List[str]:
        """获取与某篇文章同系列的其他文章标题（用于 Obsidian wiki-link）"""
        sid = article.get('series_id')
        if not sid or sid not in self.registry:
            return []

        my_title = article.get('title', '')
        return [
            a['title'] for a in self.registry[sid]['articles']
            if a['title'] != my_title
        ]

    def get_summary(self) -> str:
        """获取检测结果摘要"""
        if not self.registry:
            return "未检测到系列文章"

        lines = [f"检测到 {len(self.registry)} 个系列："]
        for sid, info in self.registry.items():
            n = len(info.get('articles', []))
            lines.append(f"  🔗 {info['name']} ({n}篇)")
        return '\n'.join(lines)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
断点续传模块 - 记录下载进度，支持中断恢复

功能：
1. 在文章下载过程中实时记录已完成的文章
2. 中断后（Ctrl+C、休眠、崩溃）重新运行时自动跳过已下载的文章
3. 任务完成后自动清理检查点文件
4. 支持单日模式和日期范围模式
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set

# 检查点文件保存目录
CHECKPOINT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'checkpoints')


def _ensure_checkpoint_dir():
    """确保检查点目录存在"""
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)


def _get_checkpoint_path(task_id: str) -> str:
    """获取检查点文件路径"""
    return os.path.join(CHECKPOINT_DIR, f'{task_id}.json')


def _generate_task_id(start_date: datetime, end_date: Optional[datetime] = None) -> str:
    """根据日期生成任务 ID
    
    单日模式: task_20260501
    范围模式: task_20260501_20260510
    """
    start_str = start_date.strftime('%Y%m%d')
    if end_date and end_date != start_date:
        end_str = end_date.strftime('%Y%m%d')
        return f'task_{start_str}_{end_str}'
    return f'task_{start_str}'


class Checkpoint:
    """断点续传管理器
    
    使用方法：
        cp = Checkpoint(start_date)
        
        # 检查是否需要恢复
        if cp.has_checkpoint():
            print(f"发现未完成的任务，已完成 {cp.completed_count()} 篇")
        
        # 检查某篇文章是否已下载
        if cp.is_completed(article_url):
            continue  # 跳过
        
        # 标记完成
        cp.mark_completed(article_url, article_data)
        
        # 任务全部完成后清理
        cp.finish()
    """
    
    def __init__(self, start_date: datetime, end_date: Optional[datetime] = None):
        _ensure_checkpoint_dir()
        self.task_id = _generate_task_id(start_date, end_date)
        self.checkpoint_path = _get_checkpoint_path(self.task_id)
        self._data = self._load()
    
    def _load(self) -> Dict:
        """加载检查点数据"""
        if os.path.exists(self.checkpoint_path):
            try:
                with open(self.checkpoint_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logging.info(f"已加载检查点: {self.task_id}，已完成 {len(data.get('completed', {}))} 篇")
                return data
            except (json.JSONDecodeError, IOError) as e:
                logging.warning(f"检查点文件损坏，将重新开始: {e}")
        
        return {
            'task_id': self.task_id,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'completed': {},    # url -> {title, date, saved_at}
            'failed': {},       # url -> {title, error, attempted_at}
        }
    
    def _save(self):
        """保存检查点数据到磁盘"""
        self._data['updated_at'] = datetime.now().isoformat()
        try:
            with open(self.checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            logging.error(f"保存检查点失败: {e}")
    
    def has_checkpoint(self) -> bool:
        """是否存在未完成的检查点"""
        return os.path.exists(self.checkpoint_path) and len(self._data.get('completed', {})) > 0
    
    def completed_count(self) -> int:
        """已完成的文章数"""
        return len(self._data.get('completed', {}))
    
    def failed_count(self) -> int:
        """失败的文章数"""
        return len(self._data.get('failed', {}))
    
    def get_completed_urls(self) -> Set[str]:
        """获取所有已完成的 URL 集合"""
        return set(self._data.get('completed', {}).keys())
    
    def is_completed(self, url: str) -> bool:
        """检查某个 URL 是否已完成"""
        return url in self._data.get('completed', {})
    
    def mark_completed(self, url: str, title: str = '', date_str: str = ''):
        """标记一篇文章已完成并立即保存
        
        每完成一篇就写盘，确保崩溃时不丢失进度。
        """
        self._data['completed'][url] = {
            'title': title,
            'date': date_str,
            'saved_at': datetime.now().isoformat(),
        }
        self._save()
    
    def mark_failed(self, url: str, title: str = '', error: str = ''):
        """标记一篇文章下载失败"""
        self._data['failed'][url] = {
            'title': title,
            'error': error,
            'attempted_at': datetime.now().isoformat(),
        }
        self._save()
    
    def get_failed_articles(self) -> Dict:
        """获取所有失败的文章"""
        return self._data.get('failed', {})
    
    def finish(self):
        """任务完成，清理检查点文件"""
        try:
            if os.path.exists(self.checkpoint_path):
                os.remove(self.checkpoint_path)
                logging.info(f"任务完成，检查点已清理: {self.task_id}")
        except IOError as e:
            logging.warning(f"清理检查点文件失败: {e}")
    
    def get_summary(self) -> str:
        """获取检查点摘要"""
        completed = self.completed_count()
        failed = self.failed_count()
        if completed == 0 and failed == 0:
            return "无历史进度"
        parts = []
        if completed > 0:
            parts.append(f"已完成 {completed} 篇")
        if failed > 0:
            parts.append(f"失败 {failed} 篇")
        return "，".join(parts)


def list_pending_checkpoints() -> List[Dict]:
    """列出所有未完成的检查点任务"""
    _ensure_checkpoint_dir()
    pending = []
    
    for fname in os.listdir(CHECKPOINT_DIR):
        if not fname.endswith('.json'):
            continue
        fpath = os.path.join(CHECKPOINT_DIR, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            pending.append({
                'task_id': data.get('task_id', fname),
                'completed': len(data.get('completed', {})),
                'failed': len(data.get('failed', {})),
                'created_at': data.get('created_at', ''),
                'updated_at': data.get('updated_at', ''),
            })
        except Exception:
            continue
    
    return pending

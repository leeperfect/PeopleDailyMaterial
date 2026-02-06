#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存模块
"""

import os
import json
import logging
import pickle
from datetime import datetime, timedelta
from typing import Any, Optional, Dict


class CacheManager:
    """缓存管理器"""
    def __init__(self, cache_dir: str = 'data/cache', default_ttl: int = 86400):
        """初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录
            default_ttl: 默认缓存过期时间（秒）
        """
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def get_cache_key(self, key: str) -> str:
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f"{key.replace('/', '_').replace('\\', '_')}.json")
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            cache_file = self.get_cache_key(key)
            if not os.path.exists(cache_file):
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检查是否过期
            timestamp = data.get('timestamp', 0)
            ttl = data.get('ttl', self.default_ttl)
            if datetime.now().timestamp() - timestamp > ttl:
                # 缓存过期，删除
                os.remove(cache_file)
                return None
            
            return data.get('data')
        except Exception as e:
            logging.error(f"获取缓存失败: {str(e)}")
            return None
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存"""
        try:
            cache_file = self.get_cache_key(key)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            
            # 准备缓存数据
            cache_data = {
                'timestamp': datetime.now().timestamp(),
                'ttl': ttl or self.default_ttl,
                'data': data
            }
            
            # 写入缓存
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            logging.error(f"设置缓存失败: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            cache_file = self.get_cache_key(key)
            if os.path.exists(cache_file):
                os.remove(cache_file)
            return True
        except Exception as e:
            logging.error(f"删除缓存失败: {str(e)}")
            return False
    
    def clear(self) -> bool:
        """清空所有缓存"""
        try:
            for file in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            return True
        except Exception as e:
            logging.error(f"清空缓存失败: {str(e)}")
            return False
    
    def get_cache_size(self) -> int:
        """获取缓存大小"""
        try:
            size = 0
            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    size += os.path.getsize(file_path)
            return size
        except Exception as e:
            logging.error(f"获取缓存大小失败: {str(e)}")
            return 0


class MemoryCache:
    """内存缓存"""
    def __init__(self, default_ttl: int = 3600):
        """初始化内存缓存
        
        Args:
            default_ttl: 默认缓存过期时间（秒）
        """
        self.cache = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            if key not in self.cache:
                return None
            
            item = self.cache[key]
            timestamp = item.get('timestamp', 0)
            ttl = item.get('ttl', self.default_ttl)
            
            if datetime.now().timestamp() - timestamp > ttl:
                # 缓存过期，删除
                del self.cache[key]
                return None
            
            return item.get('data')
        except Exception as e:
            logging.error(f"获取内存缓存失败: {str(e)}")
            return None
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存"""
        try:
            self.cache[key] = {
                'timestamp': datetime.now().timestamp(),
                'ttl': ttl or self.default_ttl,
                'data': data
            }
            return True
        except Exception as e:
            logging.error(f"设置内存缓存失败: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            if key in self.cache:
                del self.cache[key]
            return True
        except Exception as e:
            logging.error(f"删除内存缓存失败: {str(e)}")
            return False
    
    def clear(self) -> bool:
        """清空所有缓存"""
        try:
            self.cache.clear()
            return True
        except Exception as e:
            logging.error(f"清空内存缓存失败: {str(e)}")
            return False
    
    def get_cache_size(self) -> int:
        """获取缓存大小"""
        try:
            return len(self.cache)
        except Exception as e:
            logging.error(f"获取内存缓存大小失败: {str(e)}")
            return 0


# 全局缓存实例
file_cache = CacheManager()
memory_cache = MemoryCache()


def get_cache(key: str, use_memory: bool = True) -> Optional[Any]:
    """获取缓存
    
    Args:
        key: 缓存键
        use_memory: 是否使用内存缓存
    """
    if use_memory:
        # 先尝试内存缓存
        value = memory_cache.get(key)
        if value is not None:
            return value
    
    # 再尝试文件缓存
    return file_cache.get(key)


def set_cache(key: str, value: Any, ttl: Optional[int] = None, use_memory: bool = True) -> bool:
    """设置缓存
    
    Args:
        key: 缓存键
        value: 缓存值
        ttl: 过期时间（秒）
        use_memory: 是否使用内存缓存
    """
    success = True
    
    if use_memory:
        # 设置内存缓存
        success = memory_cache.set(key, value, ttl)
    
    # 设置文件缓存
    file_cache.set(key, value, ttl)
    
    return success


def delete_cache(key: str) -> bool:
    """删除缓存"""
    memory_cache.delete(key)
    return file_cache.delete(key)


def clear_cache() -> bool:
    """清空缓存"""
    memory_cache.clear()
    return file_cache.clear()

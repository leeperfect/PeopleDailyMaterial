#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具函数模块
"""

import os
import sys
import json
import logging
from typing import Optional, Dict, Any


class Config:
    """配置管理类"""
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"配置文件 {self.config_file} 不存在")
            sys.exit(1)
        except json.JSONDecodeError:
            logging.error(f"配置文件 {self.config_file} 格式错误")
            sys.exit(1)
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value


def setup_logger(config: Config):
    """设置日志"""
    log_level = getattr(logging, config.get('logging.level', 'INFO').upper())
    log_file = config.get('logging.log_file', 'crawler.log')
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


def ensure_directory(directory: str):
    """确保目录存在"""
    if not os.path.exists(directory):
        os.makedirs(directory)


def get_project_root() -> str:
    """获取项目根目录"""
    return os.path.dirname(os.path.abspath(__file__))


def safe_json_dump(data: Any, file_path: str):
    """安全地将数据写入JSON文件"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logging.error(f"写入JSON文件失败: {str(e)}")
        return False


def safe_json_load(file_path: str) -> Optional[Any]:
    """安全地从JSON文件加载数据"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"读取JSON文件失败: {str(e)}")
        return None

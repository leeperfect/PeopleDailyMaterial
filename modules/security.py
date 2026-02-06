#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全模块
"""

import os
import json
import logging
import shutil
import zipfile
from datetime import datetime
from typing import Optional, Dict, Any


class SecurityManager:
    """安全管理器"""
    def __init__(self, backup_dir: str = 'data/backups'):
        """初始化安全管理器
        
        Args:
            backup_dir: 备份目录
        """
        self.backup_dir = backup_dir
        
        # 确保备份目录存在
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def backup_data(self, data_dir: str = 'data', backup_name: Optional[str] = None) -> str:
        """备份数据
        
        Args:
            data_dir: 要备份的数据目录
            backup_name: 备份文件名
        
        Returns:
            备份文件路径
        """
        try:
            if not os.path.exists(data_dir):
                logging.error(f"数据目录不存在: {data_dir}")
                return ""
            
            # 生成备份文件名
            if not backup_name:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f"backup_{timestamp}.zip"
            
            backup_file = os.path.join(self.backup_dir, backup_name)
            
            # 创建备份文件
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 遍历目录
                for root, dirs, files in os.walk(data_dir):
                    for file in files:
                        if file.endswith(('.json', '.csv', '.xlsx')):
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, data_dir)
                            zipf.write(file_path, arcname)
            
            logging.info(f"成功备份数据到: {backup_file}")
            return backup_file
        except Exception as e:
            logging.error(f"备份数据失败: {str(e)}")
            return ""
    
    def restore_backup(self, backup_file: str, restore_dir: str = 'data') -> bool:
        """恢复备份
        
        Args:
            backup_file: 备份文件路径
            restore_dir: 恢复目录
        
        Returns:
            是否恢复成功
        """
        try:
            if not os.path.exists(backup_file):
                logging.error(f"备份文件不存在: {backup_file}")
                return False
            
            # 确保恢复目录存在
            os.makedirs(restore_dir, exist_ok=True)
            
            # 解压备份文件
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                zipf.extractall(restore_dir)
            
            logging.info(f"成功从备份恢复数据: {backup_file}")
            return True
        except Exception as e:
            logging.error(f"恢复备份失败: {str(e)}")
            return False
    
    def list_backups(self) -> List[str]:
        """列出所有备份
        
        Returns:
            备份文件列表
        """
        try:
            backups = []
            for file in os.listdir(self.backup_dir):
                if file.endswith('.zip'):
                    backups.append(os.path.join(self.backup_dir, file))
            
            # 按时间排序
            backups.sort(key=os.path.getmtime, reverse=True)
            return backups
        except Exception as e:
            logging.error(f"列出备份失败: {str(e)}")
            return []
    
    def cleanup_backups(self, keep_days: int = 7) -> bool:
        """清理过期备份
        
        Args:
            keep_days: 保留天数
        
        Returns:
            是否清理成功
        """
        try:
            cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 3600)
            
            for file in os.listdir(self.backup_dir):
                file_path = os.path.join(self.backup_dir, file)
                if os.path.getmtime(file_path) < cutoff_time:
                    os.remove(file_path)
                    logging.info(f"删除过期备份: {file}")
            
            return True
        except Exception as e:
            logging.error(f"清理备份失败: {str(e)}")
            return False


# 修复类型注解
from typing import List


class EncryptionManager:
    """加密管理器"""
    def __init__(self):
        """初始化加密管理器"""
        pass
    
    def encrypt_data(self, data: Any, key: str) -> Optional[str]:
        """加密数据
        
        Args:
            data: 待加密的数据
            key: 加密密钥
        
        Returns:
            加密后的字符串
        """
        try:
            # 简单的加密实现（实际生产环境应使用更安全的加密算法）
            import base64
            import hashlib
            from cryptography.fernet import Fernet
            
            # 生成密钥
            key_hash = hashlib.sha256(key.encode()).digest()
            cipher_suite = Fernet(base64.urlsafe_b64encode(key_hash))
            
            # 序列化数据
            data_str = json.dumps(data, ensure_ascii=False)
            
            # 加密
            encrypted_data = cipher_suite.encrypt(data_str.encode())
            
            return encrypted_data.decode()
        except Exception as e:
            logging.error(f"加密数据失败: {str(e)}")
            return None
    
    def decrypt_data(self, encrypted_data: str, key: str) -> Optional[Any]:
        """解密数据
        
        Args:
            encrypted_data: 加密的数据
            key: 解密密钥
        
        Returns:
            解密后的数据
        """
        try:
            # 简单的解密实现（实际生产环境应使用更安全的加密算法）
            import base64
            import hashlib
            from cryptography.fernet import Fernet
            
            # 生成密钥
            key_hash = hashlib.sha256(key.encode()).digest()
            cipher_suite = Fernet(base64.urlsafe_b64encode(key_hash))
            
            # 解密
            decrypted_data = cipher_suite.decrypt(encrypted_data.encode())
            
            # 反序列化
            data = json.loads(decrypted_data.decode())
            
            return data
        except Exception as e:
            logging.error(f"解密数据失败: {str(e)}")
            return None


# 全局实例
security_manager = SecurityManager()
encryption_manager = EncryptionManager()


def backup_data(data_dir: str = 'data', backup_name: Optional[str] = None) -> str:
    """备份数据的便捷函数"""
    return security_manager.backup_data(data_dir, backup_name)


def restore_data(backup_file: str, restore_dir: str = 'data') -> bool:
    """恢复数据的便捷函数"""
    return security_manager.restore_backup(backup_file, restore_dir)


def encrypt_config(config: Dict, key: str) -> Optional[str]:
    """加密配置的便捷函数"""
    return encryption_manager.encrypt_data(config, key)


def decrypt_config(encrypted_config: str, key: str) -> Optional[Dict]:
    """解密配置的便捷函数"""
    return encryption_manager.decrypt_data(encrypted_config, key)

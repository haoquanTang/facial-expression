#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据仓库模块

提供数据持久化存储功能，负责数据的加密保存和读取
"""

import os
import json
import shutil
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from core.models import DataStore, PasswordEntry, MasterConfig, AppSettings
from security.crypto import CryptoService


class DataRepository:
    """
    数据仓库类
    
    负责数据的持久化存储，包括加密保存和读取功能
    """
    
    def __init__(self, data_file_path: str):
        """
        初始化数据仓库
        
        Args:
            data_file_path (str): 数据文件路径
        """
        self.data_file_path = Path(data_file_path)
        self.backup_dir = self.data_file_path.parent / "backup"
        self.temp_dir = self.data_file_path.parent / "temp"
        
        # 创建必要的目录
        self.data_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        self.crypto_service = CryptoService()
        self._data_store: Optional[DataStore] = None
        self._master_password: Optional[str] = None
    
    def initialize_new_database(self, master_password: str) -> bool:
        """
        初始化新的数据库
        
        Args:
            master_password (str): 主密码
            
        Returns:
            bool: 是否初始化成功
        """
        try:
            # 创建新的数据存储
            self._data_store = DataStore()
            
            # 创建主配置
            hash_info = self.crypto_service.hash_password(master_password)
            master_config = MasterConfig(
                password_hash=hash_info['hash'],
                salt=hash_info['salt']
            )
            self._data_store.master_config = master_config
            
            # 保存主密码
            self._master_password = master_password
            
            # 保存到文件
            return self._save_to_file()
            
        except Exception as e:
            print(f"初始化数据库失败: {e}")
            return False
    
    def load_database(self, master_password: str) -> bool:
        """
        加载数据库
        
        Args:
            master_password (str): 主密码
            
        Returns:
            bool: 是否加载成功
        """
        try:
            if not self.data_file_path.exists():
                return False
            
            # 读取加密文件
            with open(self.data_file_path, 'r', encoding='utf-8') as f:
                encrypted_data = json.load(f)
            
            # 解密数据
            decrypted_json = self.crypto_service.decrypt_data(
                encrypted_data, master_password
            )
            
            if decrypted_json is None:
                return False
            
            # 解析JSON数据
            data_dict = json.loads(decrypted_json)
            
            # 创建数据存储对象
            self._data_store = DataStore.from_dict(data_dict)
            
            # 验证主密码
            if self._data_store.master_config:
                is_valid = self.crypto_service.verify_password(
                    master_password,
                    self._data_store.master_config.password_hash,
                    self._data_store.master_config.salt
                )
                if not is_valid:
                    return False
            
            # 保存主密码
            self._master_password = master_password
            
            return True
            
        except Exception as e:
            print(f"加载数据库失败: {e}")
            return False
    
    def save_database(self) -> bool:
        """
        保存数据库
        
        Returns:
            bool: 是否保存成功
        """
        if self._data_store is None or self._master_password is None:
            return False
        
        return self._save_to_file()
    
    def _save_to_file(self) -> bool:
        """
        保存数据到文件
        
        Returns:
            bool: 是否保存成功
        """
        try:
            # 转换为JSON字符串
            data_json = json.dumps(
                self._data_store.to_dict(),
                ensure_ascii=False,
                indent=2
            )
            
            # 加密数据
            encrypted_data = self.crypto_service.encrypt_data(
                data_json, self._master_password
            )
            
            # 写入临时文件
            temp_file = self.temp_dir / f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.enc"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(encrypted_data, f, ensure_ascii=False, indent=2)
            
            # 备份现有文件
            if self.data_file_path.exists():
                backup_file = self.backup_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.enc"
                shutil.copy2(self.data_file_path, backup_file)
            
            # 移动临时文件到目标位置
            shutil.move(str(temp_file), str(self.data_file_path))
            
            return True
            
        except Exception as e:
            print(f"保存数据库失败: {e}")
            return False
    
    def is_database_exists(self) -> bool:
        """
        检查数据库文件是否存在
        
        Returns:
            bool: 数据库文件是否存在
        """
        return self.data_file_path.exists()
    
    def is_loaded(self) -> bool:
        """
        检查数据库是否已加载
        
        Returns:
            bool: 数据库是否已加载
        """
        return self._data_store is not None and self._master_password is not None
    
    def get_data_store(self) -> Optional[DataStore]:
        """
        获取数据存储对象
        
        Returns:
            Optional[DataStore]: 数据存储对象
        """
        return self._data_store
    
    def add_password_entry(self, platform: str, username: str, 
                          password: str, notes: str = "") -> bool:
        """
        添加密码条目
        
        Args:
            platform (str): 平台名称
            username (str): 用户名
            password (str): 密码（明文）
            notes (str): 备注信息
            
        Returns:
            bool: 是否添加成功
        """
        if not self.is_loaded():
            return False
        
        try:
            # 加密密码
            encrypted_info = self.crypto_service.encrypt_data(
                password, self._master_password
            )
            encrypted_password = json.dumps(encrypted_info)
            
            # 创建密码条目
            entry = PasswordEntry(
                platform=platform,
                username=username,
                encrypted_password=encrypted_password,
                notes=notes
            )
            
            # 添加到数据存储
            success = self._data_store.add_entry(entry)
            
            if success:
                # 自动保存
                self.save_database()
            
            return success
            
        except Exception as e:
            print(f"添加密码条目失败: {e}")
            return False
    
    def get_password_entries(self, search_term: str = "") -> List[PasswordEntry]:
        """
        获取密码条目列表
        
        Args:
            search_term (str): 搜索关键词
            
        Returns:
            List[PasswordEntry]: 密码条目列表
        """
        if not self.is_loaded():
            return []
        
        return self._data_store.search_entries(search_term)
    
    def get_password_entry_by_id(self, entry_id: str) -> Optional[PasswordEntry]:
        """
        根据ID获取密码条目
        
        Args:
            entry_id (str): 条目ID
            
        Returns:
            Optional[PasswordEntry]: 密码条目
        """
        if not self.is_loaded():
            return None
        
        return self._data_store.get_entry_by_id(entry_id)
    
    def decrypt_password(self, entry: PasswordEntry) -> Optional[str]:
        """
        解密密码条目中的密码
        
        Args:
            entry (PasswordEntry): 密码条目
            
        Returns:
            Optional[str]: 解密后的密码
        """
        if not self.is_loaded():
            return None
        
        try:
            # 解析加密信息
            encrypted_info = json.loads(entry.encrypted_password)
            
            # 解密密码
            decrypted_password = self.crypto_service.decrypt_data(
                encrypted_info, self._master_password
            )
            
            return decrypted_password
            
        except Exception as e:
            print(f"解密密码失败: {e}")
            return None
    
    def update_password_entry(self, entry_id: str, platform: str, 
                            username: str, password: str, notes: str = "") -> bool:
        """
        更新密码条目
        
        Args:
            entry_id (str): 条目ID
            platform (str): 平台名称
            username (str): 用户名
            password (str): 密码（明文）
            notes (str): 备注信息
            
        Returns:
            bool: 是否更新成功
        """
        if not self.is_loaded():
            return False
        
        try:
            # 加密密码
            encrypted_info = self.crypto_service.encrypt_data(
                password, self._master_password
            )
            encrypted_password = json.dumps(encrypted_info)
            
            # 创建更新后的条目
            updated_entry = PasswordEntry(
                platform=platform,
                username=username,
                encrypted_password=encrypted_password,
                notes=notes
            )
            
            # 更新数据存储
            success = self._data_store.update_entry(entry_id, updated_entry)
            
            if success:
                # 自动保存
                self.save_database()
            
            return success
            
        except Exception as e:
            print(f"更新密码条目失败: {e}")
            return False
    
    def delete_password_entry(self, entry_id: str) -> bool:
        """
        删除密码条目
        
        Args:
            entry_id (str): 条目ID
            
        Returns:
            bool: 是否删除成功
        """
        if not self.is_loaded():
            return False
        
        success = self._data_store.delete_entry(entry_id)
        
        if success:
            # 自动保存
            self.save_database()
        
        return success
    
    def change_master_password(self, old_password: str, new_password: str) -> bool:
        """
        修改主密码
        
        Args:
            old_password (str): 旧密码
            new_password (str): 新密码
            
        Returns:
            bool: 是否修改成功
        """
        if not self.is_loaded():
            return False
        
        # 验证旧密码
        if old_password != self._master_password:
            return False
        
        try:
            # 重新加密所有密码条目
            for entry in self._data_store.entries:
                # 解密旧密码
                old_encrypted_info = json.loads(entry.encrypted_password)
                decrypted_password = self.crypto_service.decrypt_data(
                    old_encrypted_info, old_password
                )
                
                if decrypted_password is None:
                    return False
                
                # 用新密码重新加密
                new_encrypted_info = self.crypto_service.encrypt_data(
                    decrypted_password, new_password
                )
                entry.encrypted_password = json.dumps(new_encrypted_info)
                entry.update_timestamp()
            
            # 更新主配置
            hash_info = self.crypto_service.hash_password(new_password)
            self._data_store.master_config.password_hash = hash_info['hash']
            self._data_store.master_config.salt = hash_info['salt']
            self._data_store.master_config.update_timestamp()
            
            # 更新主密码
            self._master_password = new_password
            
            # 保存数据
            return self.save_database()
            
        except Exception as e:
            print(f"修改主密码失败: {e}")
            return False
    
    def get_expired_entries(self) -> List[PasswordEntry]:
        """
        获取已过期的密码条目
        
        Returns:
            List[PasswordEntry]: 已过期的条目列表
        """
        if not self.is_loaded():
            return []
        
        return self._data_store.get_expired_entries()
    
    def get_expiring_soon_entries(self, days: int = 7) -> List[PasswordEntry]:
        """
        获取即将过期的密码条目
        
        Args:
            days (int): 多少天内过期算作即将过期
            
        Returns:
            List[PasswordEntry]: 即将过期的条目列表
        """
        if not self.is_loaded():
            return []
        
        return self._data_store.get_expiring_soon_entries(days)
    
    def get_app_settings(self) -> Optional[AppSettings]:
        """
        获取应用设置
        
        Returns:
            Optional[AppSettings]: 应用设置
        """
        if not self.is_loaded():
            return None
        
        return self._data_store.app_settings
    
    def update_app_settings(self, settings: AppSettings) -> bool:
        """
        更新应用设置
        
        Args:
            settings (AppSettings): 新的应用设置
            
        Returns:
            bool: 是否更新成功
        """
        if not self.is_loaded():
            return False
        
        settings.update_timestamp()
        self._data_store.app_settings = settings
        
        return self.save_database()
    
    def cleanup_temp_files(self):
        """
        清理临时文件
        """
        try:
            for temp_file in self.temp_dir.glob("temp_*.enc"):
                temp_file.unlink()
        except Exception as e:
            print(f"清理临时文件失败: {e}")
    
    def cleanup_old_backups(self, keep_days: int = 30):
        """
        清理旧的备份文件
        
        Args:
            keep_days (int): 保留多少天的备份
        """
        try:
            cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 3600)
            
            for backup_file in self.backup_dir.glob("backup_*.enc"):
                if backup_file.stat().st_mtime < cutoff_time:
                    backup_file.unlink()
        except Exception as e:
            print(f"清理备份文件失败: {e}")
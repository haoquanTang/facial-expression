#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型模块

定义应用程序中使用的数据模型和结构
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
import json


@dataclass
class PasswordEntry:
    """
    密码条目数据模型
    
    表示一个密码条目的所有信息
    """
    platform: str
    username: str
    encrypted_password: str
    notes: str = ""
    id: str = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        """
        初始化后处理，设置默认值
        """
        if self.id is None:
            self.id = str(uuid.uuid4())
        
        current_time = datetime.now()
        if self.created_at is None:
            self.created_at = current_time
        
        if self.updated_at is None:
            self.updated_at = current_time
        
        # 默认密码90天后过期
        if self.expires_at is None:
            self.expires_at = current_time + timedelta(days=90)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            Dict[str, Any]: 字典格式的数据
        """
        data = asdict(self)
        
        # 转换datetime为ISO格式字符串
        for field in ['created_at', 'updated_at', 'expires_at']:
            if data[field] is not None:
                data[field] = data[field].isoformat()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PasswordEntry':
        """
        从字典创建PasswordEntry实例
        
        Args:
            data (Dict[str, Any]): 字典格式的数据
            
        Returns:
            PasswordEntry: 创建的实例
        """
        # 转换ISO格式字符串为datetime
        for field in ['created_at', 'updated_at', 'expires_at']:
            if field in data and data[field] is not None:
                if isinstance(data[field], str):
                    data[field] = datetime.fromisoformat(data[field])
        
        return cls(**data)
    
    def is_expired(self) -> bool:
        """
        检查密码是否已过期
        
        Returns:
            bool: 是否已过期
        """
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def days_until_expiry(self) -> Optional[int]:
        """
        计算距离过期还有多少天
        
        Returns:
            Optional[int]: 剩余天数，如果已过期返回负数，如果没有设置过期时间返回None
        """
        if self.expires_at is None:
            return None
        
        delta = self.expires_at - datetime.now()
        return delta.days
    
    def update_timestamp(self):
        """
        更新修改时间戳
        """
        self.updated_at = datetime.now()


@dataclass
class MasterConfig:
    """
    主配置数据模型
    
    存储主密码哈希和应用配置信息
    """
    password_hash: str
    salt: str
    clipboard_timeout: int = 10  # 剪贴板清空超时时间（秒）
    password_expiry_days: int = 90  # 密码过期天数
    auto_backup: bool = True  # 是否自动备份
    backup_interval: int = 7  # 备份间隔（天）
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """
        初始化后处理，设置默认值
        """
        current_time = datetime.now()
        if self.created_at is None:
            self.created_at = current_time
        
        if self.updated_at is None:
            self.updated_at = current_time
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            Dict[str, Any]: 字典格式的数据
        """
        data = asdict(self)
        
        # 转换datetime为ISO格式字符串
        for field in ['created_at', 'updated_at']:
            if data[field] is not None:
                data[field] = data[field].isoformat()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MasterConfig':
        """
        从字典创建MasterConfig实例
        
        Args:
            data (Dict[str, Any]): 字典格式的数据
            
        Returns:
            MasterConfig: 创建的实例
        """
        # 转换ISO格式字符串为datetime
        for field in ['created_at', 'updated_at']:
            if field in data and data[field] is not None:
                if isinstance(data[field], str):
                    data[field] = datetime.fromisoformat(data[field])
        
        return cls(**data)
    
    def update_timestamp(self):
        """
        更新修改时间戳
        """
        self.updated_at = datetime.now()


@dataclass
class AppSettings:
    """
    应用设置数据模型
    
    存储应用程序的各种设置
    """
    theme: str = "default"  # 主题
    window_width: int = 800  # 窗口宽度
    window_height: int = 600  # 窗口高度
    window_x: int = 100  # 窗口X位置
    window_y: int = 100  # 窗口Y位置
    auto_lock_timeout: int = 300  # 自动锁定超时时间（秒）
    show_password_strength: bool = True  # 是否显示密码强度
    confirm_delete: bool = True  # 删除时是否确认
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """
        初始化后处理，设置默认值
        """
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            Dict[str, Any]: 字典格式的数据
        """
        data = asdict(self)
        
        # 转换datetime为ISO格式字符串
        if data['updated_at'] is not None:
            data['updated_at'] = data['updated_at'].isoformat()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppSettings':
        """
        从字典创建AppSettings实例
        
        Args:
            data (Dict[str, Any]): 字典格式的数据
            
        Returns:
            AppSettings: 创建的实例
        """
        # 转换ISO格式字符串为datetime
        if 'updated_at' in data and data['updated_at'] is not None:
            if isinstance(data['updated_at'], str):
                data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data)
    
    def update_timestamp(self):
        """
        更新修改时间戳
        """
        self.updated_at = datetime.now()


class DataStore:
    """
    数据存储容器
    
    包含所有应用程序数据的容器类
    """
    
    def __init__(self):
        """
        初始化数据存储
        """
        self.entries: List[PasswordEntry] = []
        self.master_config: Optional[MasterConfig] = None
        self.app_settings: AppSettings = AppSettings()
        self.version: str = "1.0.0"
    
    def add_entry(self, entry: PasswordEntry) -> bool:
        """
        添加密码条目
        
        Args:
            entry (PasswordEntry): 要添加的密码条目
            
        Returns:
            bool: 是否添加成功
        """
        # 检查是否已存在相同的平台和用户名
        for existing_entry in self.entries:
            if (existing_entry.platform == entry.platform and 
                existing_entry.username == entry.username):
                return False
        
        self.entries.append(entry)
        return True
    
    def get_entry_by_id(self, entry_id: str) -> Optional[PasswordEntry]:
        """
        根据ID获取密码条目
        
        Args:
            entry_id (str): 条目ID
            
        Returns:
            Optional[PasswordEntry]: 找到的条目，如果不存在返回None
        """
        for entry in self.entries:
            if entry.id == entry_id:
                return entry
        return None
    
    def update_entry(self, entry_id: str, updated_entry: PasswordEntry) -> bool:
        """
        更新密码条目
        
        Args:
            entry_id (str): 要更新的条目ID
            updated_entry (PasswordEntry): 更新后的条目数据
            
        Returns:
            bool: 是否更新成功
        """
        for i, entry in enumerate(self.entries):
            if entry.id == entry_id:
                updated_entry.id = entry_id
                updated_entry.created_at = entry.created_at
                updated_entry.update_timestamp()
                self.entries[i] = updated_entry
                return True
        return False
    
    def delete_entry(self, entry_id: str) -> bool:
        """
        删除密码条目
        
        Args:
            entry_id (str): 要删除的条目ID
            
        Returns:
            bool: 是否删除成功
        """
        for i, entry in enumerate(self.entries):
            if entry.id == entry_id:
                del self.entries[i]
                return True
        return False
    
    def search_entries(self, search_term: str) -> List[PasswordEntry]:
        """
        搜索密码条目
        
        Args:
            search_term (str): 搜索关键词
            
        Returns:
            List[PasswordEntry]: 匹配的条目列表
        """
        if not search_term:
            return self.entries.copy()
        
        search_term = search_term.lower()
        results = []
        
        for entry in self.entries:
            if (search_term in entry.platform.lower() or 
                search_term in entry.username.lower() or 
                search_term in entry.notes.lower()):
                results.append(entry)
        
        return results
    
    def get_expired_entries(self) -> List[PasswordEntry]:
        """
        获取已过期的密码条目
        
        Returns:
            List[PasswordEntry]: 已过期的条目列表
        """
        return [entry for entry in self.entries if entry.is_expired()]
    
    def get_expiring_soon_entries(self, days: int = 7) -> List[PasswordEntry]:
        """
        获取即将过期的密码条目
        
        Args:
            days (int): 多少天内过期算作即将过期
            
        Returns:
            List[PasswordEntry]: 即将过期的条目列表
        """
        results = []
        for entry in self.entries:
            days_left = entry.days_until_expiry()
            if days_left is not None and 0 <= days_left <= days:
                results.append(entry)
        return results
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            Dict[str, Any]: 字典格式的数据
        """
        return {
            'version': self.version,
            'entries': [entry.to_dict() for entry in self.entries],
            'master_config': self.master_config.to_dict() if self.master_config else None,
            'app_settings': self.app_settings.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataStore':
        """
        从字典创建DataStore实例
        
        Args:
            data (Dict[str, Any]): 字典格式的数据
            
        Returns:
            DataStore: 创建的实例
        """
        store = cls()
        
        if 'version' in data:
            store.version = data['version']
        
        if 'entries' in data:
            store.entries = [PasswordEntry.from_dict(entry_data) 
                           for entry_data in data['entries']]
        
        if 'master_config' in data and data['master_config']:
            store.master_config = MasterConfig.from_dict(data['master_config'])
        
        if 'app_settings' in data:
            store.app_settings = AppSettings.from_dict(data['app_settings'])
        
        return store
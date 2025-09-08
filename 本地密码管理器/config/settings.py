#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用配置模块

管理应用程序的配置信息和常量
"""

import os
from pathlib import Path
from typing import Optional


class AppConfig:
    """
    应用配置类
    
    管理应用程序的配置信息
    """
    
    def __init__(self):
        """
        初始化应用配置
        """
        # 应用信息
        self.app_name = "本地密码管理器"
        self.app_version = "1.0.0"
        self.app_author = "开发团队"
        
        # 获取应用数据目录
        self.app_data_dir = self._get_app_data_dir()
        
        # 数据文件路径
        self.data_file_path = self.app_data_dir / "passwords.enc"
        self.config_file_path = self.app_data_dir / "config.json"
        self.log_file_path = self.app_data_dir / "logs" / "app.log"
        
        # 创建必要的目录
        self._create_directories()
        
        # 窗口配置
        self.default_window_width = 800
        self.default_window_height = 600
        self.min_window_width = 600
        self.min_window_height = 400
        
        # 安全配置
        self.default_clipboard_timeout = 10  # 秒
        self.default_password_expiry_days = 90  # 天
        self.default_auto_lock_timeout = 300  # 秒
        self.max_login_attempts = 3
        
        # 备份配置
        self.default_backup_interval = 7  # 天
        self.max_backup_files = 10
        self.backup_cleanup_days = 30
        
        # 密码生成配置
        self.default_password_length = 12
        self.min_password_length = 4
        self.max_password_length = 128
        
        # UI配置
        self.available_themes = ["default", "dark", "light"]
        self.default_theme = "default"
        
        # 文件配置
        self.temp_file_cleanup_hours = 24
        self.log_file_max_size = 10 * 1024 * 1024  # 10MB
        self.log_file_backup_count = 5
    
    def _get_app_data_dir(self) -> Path:
        """
        获取应用数据目录
        
        Returns:
            Path: 应用数据目录路径
        """
        # 根据操作系统确定数据目录
        if os.name == 'nt':  # Windows
            base_dir = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
        elif os.name == 'posix':  # macOS/Linux
            if 'darwin' in os.sys.platform:  # macOS
                base_dir = Path.home() / 'Library' / 'Application Support'
            else:  # Linux
                base_dir = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local' / 'share'))
        else:
            # 默认使用用户主目录
            base_dir = Path.home()
        
        return base_dir / 'PasswordManager'
    
    def _create_directories(self):
        """
        创建必要的目录
        """
        directories = [
            self.app_data_dir,
            self.app_data_dir / "backup",
            self.app_data_dir / "temp",
            self.app_data_dir / "logs"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_backup_dir(self) -> Path:
        """
        获取备份目录
        
        Returns:
            Path: 备份目录路径
        """
        return self.app_data_dir / "backup"
    
    def get_temp_dir(self) -> Path:
        """
        获取临时目录
        
        Returns:
            Path: 临时目录路径
        """
        return self.app_data_dir / "temp"
    
    def get_logs_dir(self) -> Path:
        """
        获取日志目录
        
        Returns:
            Path: 日志目录路径
        """
        return self.app_data_dir / "logs"
    
    def is_valid_theme(self, theme: str) -> bool:
        """
        检查主题是否有效
        
        Args:
            theme (str): 主题名称
            
        Returns:
            bool: 主题是否有效
        """
        return theme in self.available_themes
    
    def is_valid_password_length(self, length: int) -> bool:
        """
        检查密码长度是否有效
        
        Args:
            length (int): 密码长度
            
        Returns:
            bool: 密码长度是否有效
        """
        return self.min_password_length <= length <= self.max_password_length
    
    def is_valid_window_size(self, width: int, height: int) -> bool:
        """
        检查窗口大小是否有效
        
        Args:
            width (int): 窗口宽度
            height (int): 窗口高度
            
        Returns:
            bool: 窗口大小是否有效
        """
        return (width >= self.min_window_width and 
                height >= self.min_window_height)
    
    def get_display_name(self) -> str:
        """
        获取应用显示名称
        
        Returns:
            str: 应用显示名称
        """
        return f"{self.app_name} v{self.app_version}"
    
    def get_about_text(self) -> str:
        """
        获取关于信息文本
        
        Returns:
            str: 关于信息文本
        """
        return f"""{self.app_name}
版本: {self.app_version}
作者: {self.app_author}

一款安全的本地密码管理工具，采用AES-256加密算法保护您的密码安全。
所有数据完全存储在本地，无网络传输，确保隐私安全。

主要功能：
• 密码安全存储和管理
• 强密码生成器
• 密码过期提醒
• 一键复制到剪贴板
• 数据备份和恢复
• 搜索和分类管理

© 2024 {self.app_author}. 保留所有权利。"""
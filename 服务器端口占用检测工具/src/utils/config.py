#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块

负责应用程序配置文件的读取、写入和管理，支持默认配置和用户自定义配置。
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import asdict

from ..models.data_models import RemoteConfig


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """初始化配置管理器
        
        Args:
            config_dir: 配置目录路径，如果为None则使用默认路径
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # 使用项目根目录下的config目录
            project_root = Path(__file__).parent.parent.parent
            self.config_dir = project_root / "config"
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "settings.json"
        self.remote_config_file = self.config_dir / "remote_servers.json"
        
        # 加载配置
        self._load_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置
        
        Returns:
            默认配置字典
        """
        return {
            "scan_timeout": 5,
            "max_port_range": 1000,
            "log_level": "INFO",
            "thread_count": 50,
            "auto_save_results": True,
            "default_protocols": ["TCP", "UDP"],
            "window_width": 900,
            "window_height": 700,
            "theme": "default",
            "font_size": 12,
            "auto_refresh": False,
            "refresh_interval": 30,
            "connection_timeout": 10,
            "command_timeout": 30,
            "max_retries": 3,
            "retry_delay": 1,
            "log_file": "logs/port_scanner.log",
            "max_file_size": 10485760,
            "backup_count": 5,
            "console_output": True
        }
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                print(f"配置文件加载成功: {self.config_file}")
            else:
                # 如果配置文件不存在，创建默认配置
                self._config = self.get_default_config()
                self._save_config(self._config)
                print(f"创建默认配置文件: {self.config_file}")
        except Exception as e:
            print(f"加载配置文件失败: {e}，使用默认配置")
            self._config = self.get_default_config()
    
    def _merge_config(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并默认配置和用户配置
        
        Args:
            default: 默认配置
            user: 用户配置
        
        Returns:
            Dict[str, Any]: 合并后的配置
        """
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _save_config(self, config: Dict[str, Any]) -> bool:
        """
        保存配置到文件
        
        Args:
            config: 要保存的配置
        
        Returns:
            bool: 是否保存成功
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"保存配置文件失败: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键，如 'ui_settings.window_width'
            default: 默认值
        
        Returns:
            Any: 配置值
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """
        设置配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        
        Returns:
            bool: 是否设置成功
        """
        keys = key.split('.')
        config = self._config
        
        # 导航到目标位置
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
        
        # 保存配置
        return self._save_config(self._config)
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        获取配置节
        
        Args:
            section: 节名称
        
        Returns:
            Dict[str, Any]: 配置节内容
        """
        return self._config.get(section, {})
    
    def update_section(self, section: str, values: Dict[str, Any]) -> bool:
        """
        更新配置节
        
        Args:
            section: 节名称
            values: 要更新的值
        
        Returns:
            bool: 是否更新成功
        """
        if section not in self._config:
            self._config[section] = {}
        
        self._config[section].update(values)
        return self._save_config(self._config)
    
    def reset_to_default(self) -> bool:
        """
        重置为默认配置
        
        Returns:
            bool: 是否重置成功
        """
        self._config = self._default_config.copy()
        return self._save_config(self._config)
    
    def load_remote_configs(self) -> List[RemoteConfig]:
        """
        加载远程服务器配置列表
        
        Returns:
            List[RemoteConfig]: 远程配置列表
        """
        try:
            if self.remote_config_file.exists():
                with open(self.remote_config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                configs = []
                for item in data.get('remote_servers', []):
                    try:
                        config = RemoteConfig(**item)
                        configs.append(config)
                    except (TypeError, ValueError) as e:
                        print(f"加载远程配置失败: {e}")
                        continue
                
                return configs
            else:
                return []
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载远程配置文件失败: {e}")
            return []
    
    def save_remote_configs(self, configs: List[RemoteConfig]) -> bool:
        """
        保存远程服务器配置列表
        
        Args:
            configs: 远程配置列表
        
        Returns:
            bool: 是否保存成功
        """
        try:
            # 转换为字典列表，但不保存密码
            config_dicts = []
            for config in configs:
                config_dict = asdict(config)
                # 出于安全考虑，不保存密码到配置文件
                config_dict['password'] = ''
                config_dicts.append(config_dict)
            
            data = {'remote_servers': config_dicts}
            
            with open(self.remote_config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except IOError as e:
            print(f"保存远程配置文件失败: {e}")
            return False
    
    def add_remote_config(self, config: RemoteConfig) -> bool:
        """
        添加远程配置
        
        Args:
            config: 远程配置
        
        Returns:
            bool: 是否添加成功
        """
        configs = self.load_remote_configs()
        
        # 检查是否已存在相同的配置
        for existing in configs:
            if existing.host == config.host and existing.username == config.username:
                # 更新现有配置
                existing.password = config.password
                existing.private_key_path = config.private_key_path
                existing.port = config.port
                existing.timeout = config.timeout
                existing.name = config.name
                return self.save_remote_configs(configs)
        
        # 添加新配置
        configs.append(config)
        return self.save_remote_configs(configs)
    
    def remove_remote_config(self, host: str, username: str) -> bool:
        """
        删除远程配置
        
        Args:
            host: 主机地址
            username: 用户名
        
        Returns:
            bool: 是否删除成功
        """
        configs = self.load_remote_configs()
        
        # 查找并删除匹配的配置
        for i, config in enumerate(configs):
            if config.host == host and config.username == username:
                configs.pop(i)
                return self.save_remote_configs(configs)
        
        return False
    
    @property
    def config_file_path(self) -> str:
        """获取配置文件路径"""
        return str(self.config_file)
    
    @property
    def remote_config_file_path(self) -> str:
        """获取远程配置文件路径"""
        return str(self.remote_config_file)


# 全局配置管理器实例
_config_manager = None


def get_config_manager() -> ConfigManager:
    """
    获取全局配置管理器实例
    
    Returns:
        ConfigManager: 配置管理器实例
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config(key: str, default: Any = None) -> Any:
    """
    获取配置值的便捷函数
    
    Args:
        key: 配置键
        default: 默认值
    
    Returns:
        Any: 配置值
    """
    return get_config_manager().get(key, default)


def set_config(key: str, value: Any) -> bool:
    """
    设置配置值的便捷函数
    
    Args:
        key: 配置键
        value: 配置值
    
    Returns:
        bool: 是否设置成功
    """
    return get_config_manager().set(key, value)
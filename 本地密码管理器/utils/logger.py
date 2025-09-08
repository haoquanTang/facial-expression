#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理模块

提供应用程序日志记录功能
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

from config.constants import (
    LOG_MAX_FILE_SIZE, LOG_BACKUP_COUNT, 
    FONT_SIZE_NORMAL
)


class SecurityFilter(logging.Filter):
    """
    安全过滤器
    
    过滤日志中的敏感信息
    """
    
    def __init__(self):
        """
        初始化安全过滤器
        """
        super().__init__()
        # 敏感关键词列表
        self.sensitive_keywords = [
            'password', 'passwd', 'pwd', 'secret', 'key', 'token',
            '密码', '口令', '秘钥', '令牌'
        ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        过滤日志记录
        
        Args:
            record (logging.LogRecord): 日志记录
            
        Returns:
            bool: 是否允许记录
        """
        # 检查消息中是否包含敏感信息
        message = record.getMessage().lower()
        
        for keyword in self.sensitive_keywords:
            if keyword in message:
                # 替换敏感信息
                record.msg = self._mask_sensitive_info(str(record.msg))
                break
        
        return True
    
    def _mask_sensitive_info(self, message: str) -> str:
        """
        遮蔽敏感信息
        
        Args:
            message (str): 原始消息
            
        Returns:
            str: 遮蔽后的消息
        """
        # 简单的遮蔽策略，实际应用中可以更复杂
        for keyword in self.sensitive_keywords:
            if keyword in message.lower():
                return message + " [敏感信息已遮蔽]"
        return message


class AppLogger:
    """
    应用程序日志记录器
    
    提供统一的日志记录功能
    """
    
    def __init__(self, name: str = "PasswordManager", log_file: Optional[Path] = None):
        """
        初始化日志记录器
        
        Args:
            name (str): 日志记录器名称
            log_file (Optional[Path]): 日志文件路径
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers(log_file)
    
    def _setup_handlers(self, log_file: Optional[Path]):
        """
        设置日志处理器
        
        Args:
            log_file (Optional[Path]): 日志文件路径
        """
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(SecurityFilter())
        self.logger.addHandler(console_handler)
        
        # 文件处理器
        if log_file:
            # 确保日志目录存在
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 使用RotatingFileHandler进行日志轮转
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=LOG_MAX_FILE_SIZE,
                backupCount=LOG_BACKUP_COUNT,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            file_handler.addFilter(SecurityFilter())
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str, *args, **kwargs):
        """
        记录调试信息
        
        Args:
            message (str): 日志消息
        """
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """
        记录信息
        
        Args:
            message (str): 日志消息
        """
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """
        记录警告信息
        
        Args:
            message (str): 日志消息
        """
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """
        记录错误信息
        
        Args:
            message (str): 日志消息
        """
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """
        记录严重错误信息
        
        Args:
            message (str): 日志消息
        """
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """
        记录异常信息（包含堆栈跟踪）
        
        Args:
            message (str): 日志消息
        """
        self.logger.exception(message, *args, **kwargs)
    
    def log_user_action(self, action: str, details: str = ""):
        """
        记录用户操作
        
        Args:
            action (str): 操作类型
            details (str): 操作详情
        """
        message = f"用户操作: {action}"
        if details:
            message += f" - {details}"
        self.info(message)
    
    def log_security_event(self, event: str, details: str = ""):
        """
        记录安全事件
        
        Args:
            event (str): 事件类型
            details (str): 事件详情
        """
        message = f"安全事件: {event}"
        if details:
            message += f" - {details}"
        self.warning(message)
    
    def log_system_event(self, event: str, details: str = ""):
        """
        记录系统事件
        
        Args:
            event (str): 事件类型
            details (str): 事件详情
        """
        message = f"系统事件: {event}"
        if details:
            message += f" - {details}"
        self.info(message)
    
    def set_level(self, level: str):
        """
        设置日志级别
        
        Args:
            level (str): 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        if level.upper() in level_map:
            self.logger.setLevel(level_map[level.upper()])
        else:
            self.warning(f"未知的日志级别: {level}")


# 全局日志记录器实例
_app_logger: Optional[AppLogger] = None


def setup_logger(log_file: Optional[Path] = None) -> AppLogger:
    """
    设置全局日志记录器
    
    Args:
        log_file (Optional[Path]): 日志文件路径
        
    Returns:
        AppLogger: 日志记录器实例
    """
    global _app_logger
    
    if _app_logger is None:
        _app_logger = AppLogger(log_file=log_file)
        _app_logger.info("应用程序日志系统初始化完成")
    
    return _app_logger


def get_logger() -> Optional[AppLogger]:
    """
    获取全局日志记录器
    
    Returns:
        Optional[AppLogger]: 日志记录器实例
    """
    return _app_logger


def log_debug(message: str, *args, **kwargs):
    """
    记录调试信息（便捷函数）
    
    Args:
        message (str): 日志消息
    """
    if _app_logger:
        _app_logger.debug(message, *args, **kwargs)


def log_info(message: str, *args, **kwargs):
    """
    记录信息（便捷函数）
    
    Args:
        message (str): 日志消息
    """
    if _app_logger:
        _app_logger.info(message, *args, **kwargs)


def log_warning(message: str, *args, **kwargs):
    """
    记录警告信息（便捷函数）
    
    Args:
        message (str): 日志消息
    """
    if _app_logger:
        _app_logger.warning(message, *args, **kwargs)


def log_error(message: str, *args, **kwargs):
    """
    记录错误信息（便捷函数）
    
    Args:
        message (str): 日志消息
    """
    if _app_logger:
        _app_logger.error(message, *args, **kwargs)


def log_exception(message: str, *args, **kwargs):
    """
    记录异常信息（便捷函数）
    
    Args:
        message (str): 日志消息
    """
    if _app_logger:
        _app_logger.exception(message, *args, **kwargs)


def log_user_action(action: str, details: str = ""):
    """
    记录用户操作（便捷函数）
    
    Args:
        action (str): 操作类型
        details (str): 操作详情
    """
    if _app_logger:
        _app_logger.log_user_action(action, details)


def log_security_event(event: str, details: str = ""):
    """
    记录安全事件（便捷函数）
    
    Args:
        event (str): 事件类型
        details (str): 事件详情
    """
    if _app_logger:
        _app_logger.log_security_event(event, details)


def log_system_event(event: str, details: str = ""):
    """
    记录系统事件（便捷函数）
    
    Args:
        event (str): 事件类型
        details (str): 事件详情
    """
    if _app_logger:
        _app_logger.log_system_event(event, details)
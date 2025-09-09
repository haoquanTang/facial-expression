#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理模块

提供统一的日志记录功能，支持文件日志和控制台日志，包含日志轮转和格式化。
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from .config import get_config


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器（用于控制台输出）"""
    
    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
        'RESET': '\033[0m'      # 重置
    }
    
    def format(self, record):
        """格式化日志记录"""
        # 获取原始格式化结果
        log_message = super().format(record)
        
        # 添加颜色
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        return f"{color}{log_message}{reset}"


class LogManager:
    """日志管理器"""
    
    def __init__(self, name: str = "port_scanner"):
        """
        初始化日志管理器
        
        Args:
            name: 日志器名称
        """
        self.logger_name = name
        self.logger = logging.getLogger(name)
        self._initialized = False
        
        # 初始化日志配置
        self._setup_logger()
    
    def _setup_logger(self):
        """
        设置日志器配置
        """
        if self._initialized:
            return
        
        # 清除现有的处理器
        self.logger.handlers.clear()
        
        # 获取配置
        log_level = get_config('logging.log_level', 'INFO')
        log_file = get_config('logging.log_file', 'logs/port_scanner.log')
        max_file_size = get_config('logging.max_file_size', 10485760)  # 10MB
        backup_count = get_config('logging.backup_count', 5)
        console_output = get_config('logging.console_output', True)
        
        # 设置日志级别
        level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # 创建日志目录
        log_path = Path(log_file)
        if not log_path.is_absolute():
            # 相对路径，基于项目根目录
            project_root = Path(__file__).parent.parent.parent
            log_path = project_root / log_file
        
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 文件日志格式
        file_formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台日志格式
        console_formatter = ColoredFormatter(
            fmt='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # 添加文件处理器（带轮转）
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                filename=str(log_path),
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(level)
            self.logger.addHandler(file_handler)
        except (OSError, IOError) as e:
            print(f"创建文件日志处理器失败: {e}")
        
        # 添加控制台处理器
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(console_formatter)
            console_handler.setLevel(level)
            self.logger.addHandler(console_handler)
        
        # 防止日志传播到根日志器
        self.logger.propagate = False
        
        self._initialized = True
    
    def get_logger(self) -> logging.Logger:
        """
        获取日志器实例
        
        Returns:
            logging.Logger: 日志器实例
        """
        return self.logger
    
    def debug(self, message: str, *args, **kwargs):
        """记录调试日志"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """记录信息日志"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """记录警告日志"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """记录错误日志"""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """记录严重错误日志"""
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """记录异常日志（包含堆栈跟踪）"""
        self.logger.exception(message, *args, **kwargs)
    
    def log_scan_start(self, scan_type: str, port_count: int, target: str = "localhost"):
        """
        记录扫描开始日志
        
        Args:
            scan_type: 扫描类型
            port_count: 端口数量
            target: 扫描目标
        """
        self.info(f"开始{scan_type}扫描 - 目标: {target}, 端口数量: {port_count}")
    
    def log_scan_result(self, scan_type: str, total_ports: int, occupied_ports: int, 
                       duration: float, target: str = "localhost"):
        """
        记录扫描结果日志
        
        Args:
            scan_type: 扫描类型
            total_ports: 总端口数
            occupied_ports: 占用端口数
            duration: 扫描耗时
            target: 扫描目标
        """
        self.info(
            f"{scan_type}扫描完成 - 目标: {target}, "
            f"总端口: {total_ports}, 占用: {occupied_ports}, "
            f"耗时: {duration:.2f}秒"
        )
    
    def log_process_kill(self, pid: int, port: int, success: bool, process_name: str = ""):
        """
        记录进程终止日志
        
        Args:
            pid: 进程ID
            port: 端口号
            success: 是否成功
            process_name: 进程名称
        """
        status = "成功" if success else "失败"
        process_info = f"({process_name})" if process_name else ""
        self.info(f"终止进程{status} - PID: {pid}, 端口: {port} {process_info}")
    
    def log_remote_connection(self, host: str, username: str, success: bool, error: str = ""):
        """
        记录远程连接日志
        
        Args:
            host: 主机地址
            username: 用户名
            success: 是否成功
            error: 错误信息
        """
        if success:
            self.info(f"远程连接成功 - {username}@{host}")
        else:
            self.error(f"远程连接失败 - {username}@{host}: {error}")
    
    def log_config_change(self, key: str, old_value: str, new_value: str):
        """
        记录配置变更日志
        
        Args:
            key: 配置键
            old_value: 旧值
            new_value: 新值
        """
        self.info(f"配置变更 - {key}: {old_value} -> {new_value}")
    
    def set_level(self, level: str):
        """
        设置日志级别
        
        Args:
            level: 日志级别字符串
        """
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        
        # 更新所有处理器的级别
        for handler in self.logger.handlers:
            handler.setLevel(log_level)
        
        self.info(f"日志级别已设置为: {level.upper()}")
    
    def reload_config(self):
        """
        重新加载日志配置
        """
        self._initialized = False
        self._setup_logger()
        self.info("日志配置已重新加载")


# 全局日志管理器实例
_log_manager = None


def get_logger(name: Optional[str] = None) -> LogManager:
    """
    获取日志管理器实例
    
    Args:
        name: 日志器名称，如果为None则使用默认名称
    
    Returns:
        LogManager: 日志管理器实例
    """
    global _log_manager
    if _log_manager is None or (name and name != _log_manager.logger_name):
        _log_manager = LogManager(name or "port_scanner")
    return _log_manager


# 便捷函数
def debug(message: str, *args, **kwargs):
    """记录调试日志的便捷函数"""
    get_logger().debug(message, *args, **kwargs)


def info(message: str, *args, **kwargs):
    """记录信息日志的便捷函数"""
    get_logger().info(message, *args, **kwargs)


def warning(message: str, *args, **kwargs):
    """记录警告日志的便捷函数"""
    get_logger().warning(message, *args, **kwargs)


def error(message: str, *args, **kwargs):
    """记录错误日志的便捷函数"""
    get_logger().error(message, *args, **kwargs)


def critical(message: str, *args, **kwargs):
    """记录严重错误日志的便捷函数"""
    get_logger().critical(message, *args, **kwargs)


def exception(message: str, *args, **kwargs):
    """记录异常日志的便捷函数"""
    get_logger().exception(message, *args, **kwargs)
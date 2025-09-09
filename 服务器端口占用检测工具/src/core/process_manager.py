#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进程管理模块

提供进程查询、终止和管理功能。
"""

import os
import signal
import time
from typing import List, Optional, Dict, Any, Tuple

try:
    import psutil
except ImportError:
    psutil = None

from ..models.data_models import ProcessInfo, Protocol
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ProcessManager:
    """进程管理器
    
    提供进程查询、终止和管理功能。
    """
    
    def __init__(self):
        """初始化进程管理器"""
        self.logger = get_logger(self.__class__.__name__)
        
        # 检查psutil是否可用
        if psutil is None:
            self.logger.warning("psutil模块未安装，某些功能可能不可用")
    
    def get_process_info(self, pid: int) -> Optional[ProcessInfo]:
        """获取进程信息
        
        Args:
            pid: 进程ID
            
        Returns:
            进程信息对象，如果进程不存在则返回None
        """
        if psutil is None:
            self.logger.error("psutil模块未安装")
            return None
        
        try:
            process = psutil.Process(pid)
            
            # 获取进程信息
            process_info = ProcessInfo(
                pid=process.pid,
                name=process.name(),
                executable=process.exe() if hasattr(process, 'exe') else None,
                command_line=' '.join(process.cmdline()) if process.cmdline() else None,
                status=process.status(),
                create_time=process.create_time(),
                memory_usage=process.memory_info().rss if hasattr(process, 'memory_info') else None,
                cpu_percent=process.cpu_percent() if hasattr(process, 'cpu_percent') else None
            )
            
            return process_info
            
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            self.logger.debug(f"获取进程信息失败 (PID: {pid}): {e}")
            return None
        except Exception as e:
            self.logger.error(f"获取进程信息时发生错误 (PID: {pid}): {e}")
            return None
    
    def terminate_process(self, pid: int, force: bool = False) -> Tuple[bool, str]:
        """终止进程
        
        Args:
            pid: 进程ID
            force: 是否强制终止
            
        Returns:
            (成功标志, 消息)
        """
        if psutil is None:
            return False, "psutil模块未安装"
        
        try:
            process = psutil.Process(pid)
            process_name = process.name()
            
            if force:
                process.kill()
                return True, f"成功强制终止进程 {process_name} (PID: {pid})"
            else:
                process.terminate()
                return True, f"成功终止进程 {process_name} (PID: {pid})"
        
        except psutil.NoSuchProcess:
            return False, f"进程 {pid} 不存在"
        except psutil.AccessDenied:
            return False, f"没有权限终止进程 {pid}"
        except Exception as e:
            return False, f"终止进程失败: {e}"
    
    def has_permission(self) -> bool:
        """检查是否有足够的权限进行进程管理"""
        try:
            current_pid = os.getpid()
            process_info = self.get_process_info(current_pid)
            return process_info is not None
        except Exception:
            return False
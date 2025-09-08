#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪贴板操作模块

提供安全的剪贴板操作功能
"""

import threading
import time
from typing import Optional, Callable

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False
    print("警告: pyperclip 模块未安装，剪贴板功能将不可用")


class ClipboardManager:
    """
    剪贴板管理器
    
    提供安全的剪贴板操作功能，包括自动清空功能
    """
    
    def __init__(self):
        """
        初始化剪贴板管理器
        """
        self._clear_timer: Optional[threading.Timer] = None
        self._last_copied_text: Optional[str] = None
        self._callback: Optional[Callable] = None
    
    def is_available(self) -> bool:
        """
        检查剪贴板功能是否可用
        
        Returns:
            bool: 剪贴板功能是否可用
        """
        return PYPERCLIP_AVAILABLE
    
    def copy_text(self, text: str, auto_clear_seconds: int = 0, 
                  callback: Optional[Callable] = None) -> bool:
        """
        复制文本到剪贴板
        
        Args:
            text (str): 要复制的文本
            auto_clear_seconds (int): 自动清空时间（秒），0表示不自动清空
            callback (Optional[Callable]): 清空后的回调函数
            
        Returns:
            bool: 是否复制成功
        """
        if not self.is_available():
            return False
        
        try:
            # 取消之前的清空定时器
            self._cancel_clear_timer()
            
            # 复制文本到剪贴板
            pyperclip.copy(text)
            self._last_copied_text = text
            self._callback = callback
            
            # 设置自动清空定时器
            if auto_clear_seconds > 0:
                self._clear_timer = threading.Timer(
                    auto_clear_seconds, 
                    self._auto_clear_clipboard
                )
                self._clear_timer.start()
            
            return True
            
        except Exception as e:
            print(f"复制到剪贴板失败: {e}")
            return False
    
    def get_text(self) -> Optional[str]:
        """
        从剪贴板获取文本
        
        Returns:
            Optional[str]: 剪贴板中的文本，获取失败返回None
        """
        if not self.is_available():
            return None
        
        try:
            return pyperclip.paste()
        except Exception as e:
            print(f"从剪贴板获取文本失败: {e}")
            return None
    
    def clear_clipboard(self) -> bool:
        """
        清空剪贴板
        
        Returns:
            bool: 是否清空成功
        """
        if not self.is_available():
            return False
        
        try:
            # 取消自动清空定时器
            self._cancel_clear_timer()
            
            # 清空剪贴板
            pyperclip.copy("")
            self._last_copied_text = None
            
            return True
            
        except Exception as e:
            print(f"清空剪贴板失败: {e}")
            return False
    
    def _auto_clear_clipboard(self):
        """
        自动清空剪贴板（内部方法）
        """
        try:
            # 检查剪贴板内容是否仍然是我们复制的内容
            current_text = self.get_text()
            if current_text == self._last_copied_text:
                pyperclip.copy("")
            
            # 执行回调函数
            if self._callback:
                self._callback()
            
        except Exception as e:
            print(f"自动清空剪贴板失败: {e}")
        finally:
            self._last_copied_text = None
            self._callback = None
            self._clear_timer = None
    
    def _cancel_clear_timer(self):
        """
        取消清空定时器（内部方法）
        """
        if self._clear_timer and self._clear_timer.is_alive():
            self._clear_timer.cancel()
            self._clear_timer = None
    
    def is_auto_clear_active(self) -> bool:
        """
        检查自动清空是否激活
        
        Returns:
            bool: 自动清空是否激活
        """
        return self._clear_timer is not None and self._clear_timer.is_alive()
    
    def get_remaining_clear_time(self) -> Optional[float]:
        """
        获取剩余的自动清空时间
        
        Returns:
            Optional[float]: 剩余时间（秒），如果没有激活自动清空返回None
        """
        if not self.is_auto_clear_active():
            return None
        
        # 这是一个近似值，因为Timer对象没有直接获取剩余时间的方法
        return getattr(self._clear_timer, 'interval', None)
    
    def copy_password_safely(self, password: str, clear_seconds: int = 10,
                           callback: Optional[Callable] = None) -> bool:
        """
        安全地复制密码到剪贴板
        
        Args:
            password (str): 密码
            clear_seconds (int): 自动清空时间（秒）
            callback (Optional[Callable]): 清空后的回调函数
            
        Returns:
            bool: 是否复制成功
        """
        if not password:
            return False
        
        return self.copy_text(password, clear_seconds, callback)
    
    def __del__(self):
        """
        析构函数，确保清理定时器
        """
        self._cancel_clear_timer()


# 全局剪贴板管理器实例
_clipboard_manager = ClipboardManager()


def copy_to_clipboard(text: str, auto_clear_seconds: int = 0, 
                     callback: Optional[Callable] = None) -> bool:
    """
    复制文本到剪贴板（便捷函数）
    
    Args:
        text (str): 要复制的文本
        auto_clear_seconds (int): 自动清空时间（秒）
        callback (Optional[Callable]): 清空后的回调函数
        
    Returns:
        bool: 是否复制成功
    """
    return _clipboard_manager.copy_text(text, auto_clear_seconds, callback)


def get_from_clipboard() -> Optional[str]:
    """
    从剪贴板获取文本（便捷函数）
    
    Returns:
        Optional[str]: 剪贴板中的文本
    """
    return _clipboard_manager.get_text()


def clear_clipboard() -> bool:
    """
    清空剪贴板（便捷函数）
    
    Returns:
        bool: 是否清空成功
    """
    return _clipboard_manager.clear_clipboard()


def copy_password_safely(password: str, clear_seconds: int = 10,
                        callback: Optional[Callable] = None) -> bool:
    """
    安全地复制密码到剪贴板（便捷函数）
    
    Args:
        password (str): 密码
        clear_seconds (int): 自动清空时间（秒）
        callback (Optional[Callable]): 清空后的回调函数
        
    Returns:
        bool: 是否复制成功
    """
    return _clipboard_manager.copy_password_safely(password, clear_seconds, callback)


def is_clipboard_available() -> bool:
    """
    检查剪贴板功能是否可用（便捷函数）
    
    Returns:
        bool: 剪贴板功能是否可用
    """
    return _clipboard_manager.is_available()
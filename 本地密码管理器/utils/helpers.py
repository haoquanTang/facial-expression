#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
辅助函数模块

提供通用的辅助函数
"""

import os
import re
import hashlib
import platform
from datetime import datetime, timedelta
from typing import str, bool, Optional, List, Dict, Any
from pathlib import Path


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes (int): 文件大小（字节）
        
    Returns:
        str: 格式化后的文件大小
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化日期时间
    
    Args:
        dt (datetime): 日期时间对象
        format_str (str): 格式字符串
        
    Returns:
        str: 格式化后的日期时间字符串
    """
    if dt is None:
        return "未知"
    
    return dt.strftime(format_str)


def format_time_ago(dt: datetime) -> str:
    """
    格式化相对时间（多久之前）
    
    Args:
        dt (datetime): 日期时间对象
        
    Returns:
        str: 相对时间字符串
    """
    if dt is None:
        return "未知"
    
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days}天前"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours}小时前"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes}分钟前"
    else:
        return "刚刚"


def format_expiry_status(expires_at: Optional[datetime]) -> str:
    """
    格式化过期状态
    
    Args:
        expires_at (Optional[datetime]): 过期时间
        
    Returns:
        str: 过期状态字符串
    """
    if expires_at is None:
        return "永不过期"
    
    now = datetime.now()
    if now > expires_at:
        return "已过期"
    
    diff = expires_at - now
    if diff.days > 30:
        return f"{diff.days}天后过期"
    elif diff.days > 0:
        return f"{diff.days}天后过期（即将过期）"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours}小时后过期（即将过期）"
    else:
        return "即将过期"


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    截断文本
    
    Args:
        text (str): 原始文本
        max_length (int): 最大长度
        suffix (str): 后缀
        
    Returns:
        str: 截断后的文本
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除非法字符
    
    Args:
        filename (str): 原始文件名
        
    Returns:
        str: 清理后的文件名
    """
    # 移除或替换非法字符
    illegal_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(illegal_chars, '_', filename)
    
    # 移除首尾空格和点
    sanitized = sanitized.strip(' .')
    
    # 确保文件名不为空
    if not sanitized:
        sanitized = "untitled"
    
    return sanitized


def generate_unique_filename(base_path: Path, filename: str) -> Path:
    """
    生成唯一的文件名
    
    Args:
        base_path (Path): 基础路径
        filename (str): 原始文件名
        
    Returns:
        Path: 唯一的文件路径
    """
    file_path = base_path / filename
    
    if not file_path.exists():
        return file_path
    
    # 分离文件名和扩展名
    stem = file_path.stem
    suffix = file_path.suffix
    
    counter = 1
    while True:
        new_filename = f"{stem}_{counter}{suffix}"
        new_path = base_path / new_filename
        
        if not new_path.exists():
            return new_path
        
        counter += 1


def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> Optional[str]:
    """
    计算文件哈希值
    
    Args:
        file_path (Path): 文件路径
        algorithm (str): 哈希算法
        
    Returns:
        Optional[str]: 文件哈希值
    """
    if not file_path.exists():
        return None
    
    try:
        hash_obj = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
        
    except Exception:
        return None


def is_valid_email(email: str) -> bool:
    """
    验证邮箱地址格式
    
    Args:
        email (str): 邮箱地址
        
    Returns:
        bool: 是否为有效的邮箱地址
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_valid_url(url: str) -> bool:
    """
    验证URL格式
    
    Args:
        url (str): URL地址
        
    Returns:
        bool: 是否为有效的URL
    """
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return re.match(pattern, url) is not None


def get_system_info() -> Dict[str, str]:
    """
    获取系统信息
    
    Returns:
        Dict[str, str]: 系统信息字典
    """
    return {
        "操作系统": platform.system(),
        "系统版本": platform.release(),
        "架构": platform.machine(),
        "Python版本": platform.python_version(),
        "用户名": os.environ.get('USER', os.environ.get('USERNAME', '未知'))
    }


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """
    安全除法，避免除零错误
    
    Args:
        a (float): 被除数
        b (float): 除数
        default (float): 默认值
        
    Returns:
        float: 除法结果
    """
    try:
        return a / b if b != 0 else default
    except (TypeError, ZeroDivisionError):
        return default


def clamp(value: float, min_value: float, max_value: float) -> float:
    """
    将值限制在指定范围内
    
    Args:
        value (float): 原始值
        min_value (float): 最小值
        max_value (float): 最大值
        
    Returns:
        float: 限制后的值
    """
    return max(min_value, min(value, max_value))


def parse_time_duration(duration_str: str) -> Optional[timedelta]:
    """
    解析时间持续时间字符串
    
    Args:
        duration_str (str): 时间字符串，如 "1d", "2h", "30m", "45s"
        
    Returns:
        Optional[timedelta]: 时间间隔对象
    """
    if not duration_str:
        return None
    
    # 匹配数字和单位
    match = re.match(r'^(\d+)([dhms])$', duration_str.lower())
    if not match:
        return None
    
    value, unit = match.groups()
    value = int(value)
    
    unit_map = {
        'd': 'days',
        'h': 'hours',
        'm': 'minutes',
        's': 'seconds'
    }
    
    if unit in unit_map:
        kwargs = {unit_map[unit]: value}
        return timedelta(**kwargs)
    
    return None


def create_backup_filename(original_name: str, timestamp: Optional[datetime] = None) -> str:
    """
    创建备份文件名
    
    Args:
        original_name (str): 原始文件名
        timestamp (Optional[datetime]): 时间戳
        
    Returns:
        str: 备份文件名
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    # 分离文件名和扩展名
    path = Path(original_name)
    stem = path.stem
    suffix = path.suffix
    
    # 生成时间戳字符串
    time_str = timestamp.strftime("%Y%m%d_%H%M%S")
    
    return f"{stem}_backup_{time_str}{suffix}"


def ensure_directory_exists(directory: Path) -> bool:
    """
    确保目录存在
    
    Args:
        directory (Path): 目录路径
        
    Returns:
        bool: 是否成功创建或已存在
    """
    try:
        directory.mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def get_available_disk_space(path: Path) -> Optional[int]:
    """
    获取可用磁盘空间
    
    Args:
        path (Path): 路径
        
    Returns:
        Optional[int]: 可用空间（字节）
    """
    try:
        if hasattr(os, 'statvfs'):  # Unix/Linux/macOS
            statvfs = os.statvfs(path)
            return statvfs.f_frsize * statvfs.f_bavail
        elif hasattr(os, 'GetDiskFreeSpaceEx'):  # Windows
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(str(path)),
                ctypes.pointer(free_bytes),
                None,
                None
            )
            return free_bytes.value
    except Exception:
        pass
    
    return None


def is_port_available(port: int, host: str = 'localhost') -> bool:
    """
    检查端口是否可用
    
    Args:
        port (int): 端口号
        host (str): 主机地址
        
    Returns:
        bool: 端口是否可用
    """
    import socket
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return result != 0
    except Exception:
        return False


def generate_random_string(length: int = 8, charset: str = None) -> str:
    """
    生成随机字符串
    
    Args:
        length (int): 字符串长度
        charset (str): 字符集
        
    Returns:
        str: 随机字符串
    """
    import random
    import string
    
    if charset is None:
        charset = string.ascii_letters + string.digits
    
    return ''.join(random.choice(charset) for _ in range(length))
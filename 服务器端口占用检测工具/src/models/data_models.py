#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型定义模块

定义了端口扫描工具中使用的所有数据结构，包括端口信息、远程配置、扫描结果等。
"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PortStatus(Enum):
    """端口状态枚举"""
    LISTEN = "LISTEN"          # 监听状态
    ESTABLISHED = "ESTABLISHED"  # 已建立连接
    CLOSED = "CLOSED"          # 关闭状态
    TIME_WAIT = "TIME_WAIT"    # 等待状态
    UNKNOWN = "UNKNOWN"        # 未知状态


class Protocol(Enum):
    """协议类型枚举"""
    TCP = "TCP"
    UDP = "UDP"


class ScanType(Enum):
    """扫描类型枚举"""
    LOCAL = "local"    # 本地扫描
    REMOTE = "remote"  # 远程扫描


@dataclass
class ProcessInfo:
    """进程信息数据类"""
    pid: int
    name: str
    executable: Optional[str] = None  # 可执行文件路径
    exe_path: Optional[str] = None
    command_line: Optional[str] = None
    status: Optional[str] = None
    create_time: Optional[float] = None
    memory_usage: Optional[int] = None  # 内存使用量(字节)
    cpu_percent: Optional[float] = None

    @property
    def cmdline(self) -> Optional[List[str]]:
        """命令行参数列表（兼容性属性）"""
        if self.command_line:
            return self.command_line.split()
        return None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.create_time:
            # 计算运行时间
            import time
            self.runtime_seconds = time.time() - self.create_time


@dataclass
class PortInfo:
    """端口信息数据类"""
    port: int                           # 端口号
    status: PortStatus                  # 端口状态
    protocol: Protocol                  # 协议类型
    local_address: str                  # 本地地址
    remote_address: str = ""            # 远程地址
    pid: Optional[int] = None           # 占用进程ID
    process_name: Optional[str] = None  # 进程名称
    process_info: Optional[ProcessInfo] = None  # 详细进程信息

    def __post_init__(self):
        """初始化后处理"""
        # 确保状态是PortStatus枚举类型
        if isinstance(self.status, str):
            try:
                self.status = PortStatus(self.status)
            except ValueError:
                self.status = PortStatus.UNKNOWN
        
        # 确保协议是Protocol枚举类型
        if isinstance(self.protocol, str):
            try:
                self.protocol = Protocol(self.protocol.upper())
            except ValueError:
                self.protocol = Protocol.TCP

    @property
    def is_occupied(self) -> bool:
        """判断端口是否被占用"""
        return self.status in [PortStatus.LISTEN, PortStatus.ESTABLISHED]

    @property
    def display_status(self) -> str:
        """获取显示用的状态字符串"""
        return "占用" if self.is_occupied else "空闲"


@dataclass
class RemoteConfig:
    """远程连接配置数据类"""
    host: str                    # 远程主机IP或域名
    username: str                # SSH用户名
    password: str = ""           # SSH密码
    private_key_path: str = ""   # 私钥文件路径
    port: int = 22              # SSH端口，默认22
    timeout: int = 10           # 连接超时时间（秒）
    name: str = ""              # 配置名称

    def __post_init__(self):
        """初始化后处理"""
        if not self.name:
            self.name = f"{self.username}@{self.host}"
        
        # 验证端口范围
        if not (1 <= self.port <= 65535):
            raise ValueError(f"无效的SSH端口号: {self.port}")
        
        # 验证超时时间
        if self.timeout <= 0:
            self.timeout = 10

    @property
    def has_password_auth(self) -> bool:
        """是否使用密码认证"""
        return bool(self.password)

    @property
    def has_key_auth(self) -> bool:
        """是否使用密钥认证"""
        return bool(self.private_key_path)

    def validate(self) -> bool:
        """验证配置是否有效"""
        if not self.host or not self.username:
            return False
        return self.has_password_auth or self.has_key_auth


@dataclass
class ScanResult:
    """扫描结果数据类"""
    scan_time: datetime              # 扫描时间
    scan_type: ScanType             # 扫描类型
    port_info_list: List[PortInfo]  # 端口信息列表
    success: bool                   # 扫描是否成功
    error_message: str = ""         # 错误信息
    scan_duration: float = 0.0      # 扫描耗时（秒）
    total_ports: int = 0            # 总扫描端口数
    occupied_ports: int = 0         # 被占用端口数
    remote_config: Optional[RemoteConfig] = None  # 远程配置（远程扫描时使用）

    def __post_init__(self):
        """初始化后处理"""
        # 确保扫描类型是ScanType枚举
        if isinstance(self.scan_type, str):
            try:
                self.scan_type = ScanType(self.scan_type)
            except ValueError:
                self.scan_type = ScanType.LOCAL
        
        # 计算统计信息
        self.total_ports = len(self.port_info_list)
        self.occupied_ports = sum(1 for port in self.port_info_list if port.is_occupied)

    @property
    def free_ports(self) -> int:
        """空闲端口数"""
        return self.total_ports - self.occupied_ports

    @property
    def occupation_rate(self) -> float:
        """端口占用率"""
        if self.total_ports == 0:
            return 0.0
        return (self.occupied_ports / self.total_ports) * 100

    def get_occupied_ports(self) -> List[PortInfo]:
        """获取被占用的端口列表"""
        return [port for port in self.port_info_list if port.is_occupied]

    def get_free_ports(self) -> List[PortInfo]:
        """获取空闲的端口列表"""
        return [port for port in self.port_info_list if not port.is_occupied]


@dataclass
class ScanConfig:
    """扫描配置数据类"""
    port_range: List[int]           # 端口范围列表
    scan_type: ScanType = ScanType.LOCAL  # 扫描类型
    timeout: float = 1.0            # 单个端口扫描超时时间
    max_threads: int = 50           # 最大线程数
    protocols: List[Protocol] = None  # 要扫描的协议列表
    remote_config: Optional[RemoteConfig] = None  # 远程配置

    def __post_init__(self):
        """初始化后处理"""
        if self.protocols is None:
            self.protocols = [Protocol.TCP, Protocol.UDP]
        
        # 验证端口范围
        valid_ports = []
        for port in self.port_range:
            if 1 <= port <= 65535:
                valid_ports.append(port)
        self.port_range = sorted(list(set(valid_ports)))  # 去重并排序
        
        # 验证线程数
        if self.max_threads <= 0:
            self.max_threads = 50
        elif self.max_threads > 200:
            self.max_threads = 200
        
        # 验证超时时间
        if self.timeout <= 0:
            self.timeout = 1.0

    @classmethod
    def from_port_string(cls, port_string: str, **kwargs) -> 'ScanConfig':
        """从端口字符串创建扫描配置
        
        Args:
            port_string: 端口字符串，支持格式：
                - 单个端口: "80"
                - 端口列表: "80,443,8080"
                - 端口范围: "8000-9000"
                - 混合格式: "80,443,8000-8010"
        
        Returns:
            ScanConfig: 扫描配置对象
        """
        ports = []
        
        # 分割逗号分隔的部分
        parts = [part.strip() for part in port_string.split(',')]
        
        for part in parts:
            if '-' in part:
                # 处理端口范围
                try:
                    start, end = map(int, part.split('-', 1))
                    if start <= end:
                        ports.extend(range(start, end + 1))
                except ValueError:
                    continue
            else:
                # 处理单个端口
                try:
                    port = int(part)
                    ports.append(port)
                except ValueError:
                    continue
        
        return cls(port_range=ports, **kwargs)

    @property
    def port_count(self) -> int:
        """获取端口总数"""
        return len(self.port_range)

    def validate(self) -> tuple[bool, str]:
        """验证配置是否有效
        
        Returns:
            tuple: (是否有效, 错误信息)
        """
        if not self.port_range:
            return False, "端口范围不能为空"
        
        if self.port_count > 10000:
            return False, "端口数量过多，请限制在10000个以内"
        
        if self.scan_type == ScanType.REMOTE:
            if not self.remote_config:
                return False, "远程扫描需要提供远程配置"
            if not self.remote_config.validate():
                return False, "远程配置无效"
        
        return True, ""


# 导出所有数据类和枚举
__all__ = [
    'PortStatus', 'Protocol', 'ScanType',
    'ProcessInfo', 'PortInfo', 'RemoteConfig', 
    'ScanResult', 'ScanConfig'
]
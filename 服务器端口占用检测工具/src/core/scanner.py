#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端口扫描核心模块

负责本地和远程端口扫描功能，支持TCP和UDP协议，多线程扫描提高效率。
"""

import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Tuple, Union
from datetime import datetime

import psutil

from ..models.data_models import (
    PortInfo, PortStatus, Protocol, ScanResult, ScanType, 
    ScanConfig, ProcessInfo, RemoteConfig
)
from ..utils.logger import get_logger
from ..utils.config import get_config


class PortScanner:
    """端口扫描器"""
    
    def __init__(self):
        """
        初始化端口扫描器
        """
        self.logger = get_logger()
        self._stop_scan = False
        self._scan_lock = threading.Lock()
    
    def scan_ports(self, config: ScanConfig) -> ScanResult:
        """
        执行端口扫描
        
        Args:
            config: 扫描配置
        
        Returns:
            ScanResult: 扫描结果
        """
        start_time = datetime.now()
        self._stop_scan = False
        
        # 验证配置
        is_valid, error_msg = config.validate()
        if not is_valid:
            return ScanResult(
                scan_time=start_time,
                scan_type=config.scan_type,
                port_info_list=[],
                success=False,
                error_message=error_msg
            )
        
        self.logger.log_scan_start(
            config.scan_type.value,
            config.port_count,
            config.remote_config.host if config.remote_config else "localhost"
        )
        
        try:
            if config.scan_type == ScanType.LOCAL:
                port_info_list = self._scan_local_ports(config)
            else:
                port_info_list = self._scan_remote_ports(config)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = ScanResult(
                scan_time=start_time,
                scan_type=config.scan_type,
                port_info_list=port_info_list,
                success=True,
                scan_duration=duration,
                remote_config=config.remote_config
            )
            
            self.logger.log_scan_result(
                config.scan_type.value,
                result.total_ports,
                result.occupied_ports,
                duration,
                config.remote_config.host if config.remote_config else "localhost"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"端口扫描失败: {e}")
            return ScanResult(
                scan_time=start_time,
                scan_type=config.scan_type,
                port_info_list=[],
                success=False,
                error_message=str(e),
                remote_config=config.remote_config
            )
    
    def _scan_local_ports(self, config: ScanConfig) -> List[PortInfo]:
        """
        扫描本地端口
        
        Args:
            config: 扫描配置
        
        Returns:
            List[PortInfo]: 端口信息列表
        """
        port_info_list = []
        
        # 获取系统网络连接信息
        connections = self._get_system_connections()
        
        # 使用线程池进行并发扫描
        with ThreadPoolExecutor(max_workers=config.max_threads) as executor:
            # 提交扫描任务
            future_to_port = {}
            
            for port in config.port_range:
                if self._stop_scan:
                    break
                
                for protocol in config.protocols:
                    future = executor.submit(
                        self._scan_single_port,
                        "localhost",
                        port,
                        protocol,
                        config.timeout,
                        connections
                    )
                    future_to_port[future] = (port, protocol)
            
            # 收集结果
            for future in as_completed(future_to_port):
                if self._stop_scan:
                    break
                
                try:
                    port_info = future.result()
                    if port_info:
                        port_info_list.append(port_info)
                except Exception as e:
                    port, protocol = future_to_port[future]
                    self.logger.debug(f"扫描端口 {port}/{protocol.value} 失败: {e}")
        
        return port_info_list
    
    def _scan_remote_ports(self, config: ScanConfig) -> List[PortInfo]:
        """
        扫描远程端口
        
        Args:
            config: 扫描配置
        
        Returns:
            List[PortInfo]: 端口信息列表
        """
        # 远程扫描需要通过SSH连接执行
        # 这里先实现基本的网络连通性检测
        port_info_list = []
        
        with ThreadPoolExecutor(max_workers=config.max_threads) as executor:
            future_to_port = {}
            
            for port in config.port_range:
                if self._stop_scan:
                    break
                
                for protocol in config.protocols:
                    future = executor.submit(
                        self._scan_remote_single_port,
                        config.remote_config.host,
                        port,
                        protocol,
                        config.timeout
                    )
                    future_to_port[future] = (port, protocol)
            
            # 收集结果
            for future in as_completed(future_to_port):
                if self._stop_scan:
                    break
                
                try:
                    port_info = future.result()
                    if port_info:
                        port_info_list.append(port_info)
                except Exception as e:
                    port, protocol = future_to_port[future]
                    self.logger.debug(f"扫描远程端口 {port}/{protocol.value} 失败: {e}")
        
        return port_info_list
    
    def _scan_single_port(self, host: str, port: int, protocol: Protocol, 
                         timeout: float, connections: dict) -> Optional[PortInfo]:
        """
        扫描单个端口
        
        Args:
            host: 主机地址
            port: 端口号
            protocol: 协议类型
            timeout: 超时时间
            connections: 系统连接信息
        
        Returns:
            Optional[PortInfo]: 端口信息，如果端口关闭则返回None
        """
        try:
            if protocol == Protocol.TCP:
                return self._scan_tcp_port(host, port, timeout, connections)
            elif protocol == Protocol.UDP:
                return self._scan_udp_port(host, port, timeout, connections)
        except Exception as e:
            self.logger.debug(f"扫描端口 {port}/{protocol.value} 异常: {e}")
        
        return None
    
    def _scan_tcp_port(self, host: str, port: int, timeout: float, 
                      connections: dict) -> Optional[PortInfo]:
        """
        扫描TCP端口
        
        Args:
            host: 主机地址
            port: 端口号
            timeout: 超时时间
            connections: 系统连接信息
        
        Returns:
            Optional[PortInfo]: 端口信息
        """
        # 检查系统连接信息中是否有此端口
        connection_key = (port, Protocol.TCP)
        if connection_key in connections:
            conn_info = connections[connection_key]
            return PortInfo(
                port=port,
                status=PortStatus.LISTEN,
                protocol=Protocol.TCP,
                local_address=conn_info['local_address'],
                remote_address=conn_info.get('remote_address', ''),
                pid=conn_info.get('pid'),
                process_name=conn_info.get('process_name'),
                process_info=conn_info.get('process_info')
            )
        
        # 尝试连接端口
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            
            if result == 0:
                # 端口开放，但没有在系统连接中找到，可能是外部服务
                return PortInfo(
                    port=port,
                    status=PortStatus.ESTABLISHED,
                    protocol=Protocol.TCP,
                    local_address=f"{host}:{port}"
                )
        except Exception:
            pass
        finally:
            if sock:
                sock.close()
        
        return None
    
    def _scan_udp_port(self, host: str, port: int, timeout: float, 
                      connections: dict) -> Optional[PortInfo]:
        """
        扫描UDP端口
        
        Args:
            host: 主机地址
            port: 端口号
            timeout: 超时时间
            connections: 系统连接信息
        
        Returns:
            Optional[PortInfo]: 端口信息
        """
        # UDP端口扫描主要依赖系统连接信息
        connection_key = (port, Protocol.UDP)
        if connection_key in connections:
            conn_info = connections[connection_key]
            return PortInfo(
                port=port,
                status=PortStatus.LISTEN,
                protocol=Protocol.UDP,
                local_address=conn_info['local_address'],
                pid=conn_info.get('pid'),
                process_name=conn_info.get('process_name'),
                process_info=conn_info.get('process_info')
            )
        
        return None
    
    def _scan_remote_single_port(self, host: str, port: int, protocol: Protocol, 
                                timeout: float) -> Optional[PortInfo]:
        """
        扫描远程单个端口
        
        Args:
            host: 远程主机地址
            port: 端口号
            protocol: 协议类型
            timeout: 超时时间
        
        Returns:
            Optional[PortInfo]: 端口信息
        """
        if protocol == Protocol.TCP:
            sock = None
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                result = sock.connect_ex((host, port))
                
                if result == 0:
                    return PortInfo(
                        port=port,
                        status=PortStatus.ESTABLISHED,
                        protocol=Protocol.TCP,
                        local_address=f"{host}:{port}"
                    )
            except Exception:
                pass
            finally:
                if sock:
                    sock.close()
        
        return None
    
    def _get_system_connections(self) -> dict:
        """
        获取系统网络连接信息
        
        Returns:
            dict: 连接信息字典，键为(端口, 协议)元组
        """
        connections = {}
        
        try:
            # 获取所有网络连接
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr:
                    port = conn.laddr.port
                    protocol = Protocol.TCP if conn.type == socket.SOCK_STREAM else Protocol.UDP
                    
                    # 获取进程信息
                    process_info = None
                    process_name = None
                    
                    if conn.pid:
                        try:
                            process = psutil.Process(conn.pid)
                            process_name = process.name()
                            process_info = ProcessInfo(
                                pid=conn.pid,
                                name=process_name,
                                status=process.status(),
                                cpu_percent=process.cpu_percent(),
                                memory_percent=process.memory_percent(),
                                create_time=process.create_time(),
                                cmdline=process.cmdline()
                            )
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    
                    # 构建连接信息
                    conn_info = {
                        'local_address': f"{conn.laddr.ip}:{conn.laddr.port}",
                        'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else '',
                        'pid': conn.pid,
                        'process_name': process_name,
                        'process_info': process_info,
                        'status': conn.status
                    }
                    
                    connections[(port, protocol)] = conn_info
        
        except Exception as e:
            self.logger.error(f"获取系统连接信息失败: {e}")
        
        return connections
    
    def scan_single_port(self, host: str, port: int, protocol: Protocol = Protocol.TCP, 
                        timeout: float = 1.0) -> Optional[PortInfo]:
        """
        扫描单个端口的公共接口
        
        Args:
            host: 主机地址
            port: 端口号
            protocol: 协议类型
            timeout: 超时时间
        
        Returns:
            Optional[PortInfo]: 端口信息
        """
        if host in ['localhost', '127.0.0.1', '0.0.0.0']:
            connections = self._get_system_connections()
            return self._scan_single_port(host, port, protocol, timeout, connections)
        else:
            return self._scan_remote_single_port(host, port, protocol, timeout)
    
    def get_process_by_port(self, port: int, protocol: Protocol = Protocol.TCP) -> Optional[ProcessInfo]:
        """
        根据端口号获取占用进程信息
        
        Args:
            port: 端口号
            protocol: 协议类型
        
        Returns:
            Optional[ProcessInfo]: 进程信息
        """
        try:
            for conn in psutil.net_connections(kind='inet'):
                if (conn.laddr and conn.laddr.port == port and 
                    ((protocol == Protocol.TCP and conn.type == socket.SOCK_STREAM) or
                     (protocol == Protocol.UDP and conn.type == socket.SOCK_DGRAM))):
                    
                    if conn.pid:
                        try:
                            process = psutil.Process(conn.pid)
                            return ProcessInfo(
                                pid=conn.pid,
                                name=process.name(),
                                status=process.status(),
                                cpu_percent=process.cpu_percent(),
                                memory_percent=process.memory_percent(),
                                create_time=process.create_time(),
                                cmdline=process.cmdline()
                            )
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
        
        except Exception as e:
            self.logger.error(f"获取端口 {port} 进程信息失败: {e}")
        
        return None
    
    def check_port_status(self, host: str, port: int, protocol: Protocol = Protocol.TCP) -> bool:
        """
        检查端口是否开放
        
        Args:
            host: 主机地址
            port: 端口号
            protocol: 协议类型
        
        Returns:
            bool: 端口是否开放
        """
        port_info = self.scan_single_port(host, port, protocol)
        return port_info is not None and port_info.is_occupied
    
    def stop_scan(self):
        """
        停止当前扫描
        """
        with self._scan_lock:
            self._stop_scan = True
            self.logger.info("扫描已停止")
    
    def is_scanning(self) -> bool:
        """
        检查是否正在扫描
        
        Returns:
            bool: 是否正在扫描
        """
        with self._scan_lock:
            return not self._stop_scan


# 便捷函数
def scan_ports(port_range: Union[int, List[int]], host: str = "localhost", 
              protocols: List[Protocol] = None, timeout: float = 1.0, 
              max_threads: int = 50) -> ScanResult:
    """
    扫描端口的便捷函数
    
    Args:
        port_range: 端口范围
        host: 主机地址
        protocols: 协议列表
        timeout: 超时时间
        max_threads: 最大线程数
    
    Returns:
        ScanResult: 扫描结果
    """
    if isinstance(port_range, int):
        port_range = [port_range]
    
    if protocols is None:
        protocols = [Protocol.TCP]
    
    scan_type = ScanType.LOCAL if host in ['localhost', '127.0.0.1'] else ScanType.REMOTE
    
    config = ScanConfig(
        port_range=port_range,
        scan_type=scan_type,
        timeout=timeout,
        max_threads=max_threads,
        protocols=protocols
    )
    
    scanner = PortScanner()
    return scanner.scan_ports(config)


def check_port(host: str, port: int, protocol: Protocol = Protocol.TCP, timeout: float = 1.0) -> bool:
    """
    检查单个端口是否开放的便捷函数
    
    Args:
        host: 主机地址
        port: 端口号
        protocol: 协议类型
        timeout: 超时时间
    
    Returns:
        bool: 端口是否开放
    """
    scanner = PortScanner()
    return scanner.check_port_status(host, port, protocol)
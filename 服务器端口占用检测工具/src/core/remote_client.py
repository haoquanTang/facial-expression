#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
远程连接模块

负责SSH连接和远程命令执行，支持密码和密钥认证，包含连接池管理和错误重试机制。
"""

import io
import socket
import threading
import time
from typing import Dict, List, Optional, Tuple, Any
from contextlib import contextmanager

try:
    import paramiko
except ImportError:
    paramiko = None

from ..models.data_models import RemoteConfig, PortInfo, PortStatus, Protocol, ProcessInfo
from ..utils.logger import get_logger
from ..utils.config import get_config


class SSHConnectionError(Exception):
    """SSH连接异常"""
    pass


class RemoteCommandError(Exception):
    """远程命令执行异常"""
    pass


class RemoteClient:
    """远程SSH客户端"""
    
    def __init__(self, config: RemoteConfig):
        """
        初始化远程客户端
        
        Args:
            config: 远程连接配置
        """
        if paramiko is None:
            raise ImportError("paramiko库未安装，请运行: pip install paramiko")
        
        self.config = config
        self.logger = get_logger()
        self._client = None
        self._connected = False
        self._lock = threading.Lock()
        
        # 重试配置
        self.max_retries = get_config('remote_settings.max_retries', 3)
        self.retry_delay = get_config('remote_settings.retry_delay', 1)
    
    def connect(self) -> bool:
        """
        建立SSH连接
        
        Returns:
            bool: 是否连接成功
        """
        with self._lock:
            if self._connected and self._client:
                return True
            
            try:
                self._client = paramiko.SSHClient()
                self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # 连接参数
                connect_kwargs = {
                    'hostname': self.config.host,
                    'port': self.config.port,
                    'username': self.config.username,
                    'timeout': self.config.timeout,
                    'allow_agent': False,
                    'look_for_keys': False
                }
                
                # 认证方式
                if self.config.has_key_auth:
                    connect_kwargs['key_filename'] = self.config.private_key_path
                elif self.config.has_password_auth:
                    connect_kwargs['password'] = self.config.password
                else:
                    raise SSHConnectionError("未提供有效的认证方式")
                
                self.logger.info(f"正在连接到 {self.config.username}@{self.config.host}:{self.config.port}")
                
                self._client.connect(**connect_kwargs)
                self._connected = True
                
                self.logger.log_remote_connection(self.config.host, self.config.username, True)
                return True
            
            except Exception as e:
                error_msg = str(e)
                self.logger.log_remote_connection(self.config.host, self.config.username, False, error_msg)
                self._connected = False
                if self._client:
                    self._client.close()
                    self._client = None
                return False
    
    def disconnect(self):
        """
        断开SSH连接
        """
        with self._lock:
            if self._client:
                try:
                    self._client.close()
                except:
                    pass
                finally:
                    self._client = None
                    self._connected = False
                    self.logger.info(f"已断开与 {self.config.host} 的连接")
    
    def is_connected(self) -> bool:
        """
        检查是否已连接
        
        Returns:
            bool: 是否已连接
        """
        with self._lock:
            if not self._connected or not self._client:
                return False
            
            try:
                # 发送一个简单的命令来测试连接
                transport = self._client.get_transport()
                return transport and transport.is_active()
            except:
                self._connected = False
                return False
    
    def execute_command(self, command: str, timeout: Optional[float] = None) -> Tuple[str, str, int]:
        """
        执行远程命令
        
        Args:
            command: 要执行的命令
            timeout: 命令超时时间
        
        Returns:
            Tuple[str, str, int]: (标准输出, 标准错误, 退出码)
        
        Raises:
            RemoteCommandError: 命令执行失败
        """
        if not self.is_connected():
            if not self.connect():
                raise RemoteCommandError("无法建立SSH连接")
        
        if timeout is None:
            timeout = get_config('remote_settings.command_timeout', 30)
        
        try:
            self.logger.debug(f"执行远程命令: {command}")
            
            stdin, stdout, stderr = self._client.exec_command(
                command, 
                timeout=timeout,
                get_pty=False
            )
            
            # 读取输出
            stdout_data = stdout.read().decode('utf-8', errors='ignore')
            stderr_data = stderr.read().decode('utf-8', errors='ignore')
            exit_code = stdout.channel.recv_exit_status()
            
            # 关闭通道
            stdin.close()
            stdout.close()
            stderr.close()
            
            self.logger.debug(f"命令执行完成，退出码: {exit_code}")
            
            return stdout_data, stderr_data, exit_code
        
        except Exception as e:
            raise RemoteCommandError(f"执行命令失败: {e}")
    
    def scan_remote_ports(self, port_range: List[int], protocols: List[Protocol] = None) -> List[PortInfo]:
        """
        扫描远程端口
        
        Args:
            port_range: 端口范围列表
            protocols: 协议列表
        
        Returns:
            List[PortInfo]: 端口信息列表
        """
        if protocols is None:
            protocols = [Protocol.TCP, Protocol.UDP]
        
        port_info_list = []
        
        try:
            # 获取远程系统的网络连接信息
            connections = self._get_remote_connections()
            
            for port in port_range:
                for protocol in protocols:
                    port_info = self._check_remote_port(port, protocol, connections)
                    if port_info:
                        port_info_list.append(port_info)
        
        except Exception as e:
            self.logger.error(f"远程端口扫描失败: {e}")
        
        return port_info_list
    
    def _get_remote_connections(self) -> Dict[Tuple[int, Protocol], Dict[str, Any]]:
        """
        获取远程系统的网络连接信息
        
        Returns:
            Dict: 连接信息字典
        """
        connections = {}
        
        try:
            # 使用netstat命令获取网络连接信息
            commands = [
                "netstat -tlnp 2>/dev/null | grep LISTEN",  # TCP监听端口
                "netstat -ulnp 2>/dev/null"  # UDP端口
            ]
            
            for i, cmd in enumerate(commands):
                protocol = Protocol.TCP if i == 0 else Protocol.UDP
                
                try:
                    stdout, stderr, exit_code = self.execute_command(cmd)
                    
                    if exit_code == 0:
                        connections.update(self._parse_netstat_output(stdout, protocol))
                except RemoteCommandError:
                    continue
            
            # 如果netstat不可用，尝试使用ss命令
            if not connections:
                try:
                    stdout, stderr, exit_code = self.execute_command("ss -tlnp")
                    if exit_code == 0:
                        connections.update(self._parse_ss_output(stdout, Protocol.TCP))
                    
                    stdout, stderr, exit_code = self.execute_command("ss -ulnp")
                    if exit_code == 0:
                        connections.update(self._parse_ss_output(stdout, Protocol.UDP))
                except RemoteCommandError:
                    pass
        
        except Exception as e:
            self.logger.error(f"获取远程连接信息失败: {e}")
        
        return connections
    
    def _parse_netstat_output(self, output: str, protocol: Protocol) -> Dict[Tuple[int, Protocol], Dict[str, Any]]:
        """
        解析netstat命令输出
        
        Args:
            output: netstat命令输出
            protocol: 协议类型
        
        Returns:
            Dict: 解析后的连接信息
        """
        connections = {}
        
        for line in output.strip().split('\n'):
            if not line.strip():
                continue
            
            parts = line.split()
            if len(parts) < 4:
                continue
            
            try:
                # 解析地址和端口
                local_address = parts[3]
                if ':' in local_address:
                    addr_parts = local_address.rsplit(':', 1)
                    if len(addr_parts) == 2:
                        port = int(addr_parts[1])
                        
                        # 解析进程信息
                        pid = None
                        process_name = None
                        
                        if len(parts) > 6 and '/' in parts[6]:
                            pid_name = parts[6].split('/', 1)
                            if len(pid_name) == 2 and pid_name[0].isdigit():
                                pid = int(pid_name[0])
                                process_name = pid_name[1]
                        
                        connections[(port, protocol)] = {
                            'local_address': local_address,
                            'pid': pid,
                            'process_name': process_name,
                            'status': 'LISTEN' if protocol == Protocol.TCP else 'OPEN'
                        }
            
            except (ValueError, IndexError):
                continue
        
        return connections
    
    def _parse_ss_output(self, output: str, protocol: Protocol) -> Dict[Tuple[int, Protocol], Dict[str, Any]]:
        """
        解析ss命令输出
        
        Args:
            output: ss命令输出
            protocol: 协议类型
        
        Returns:
            Dict: 解析后的连接信息
        """
        connections = {}
        
        for line in output.strip().split('\n'):
            if not line.strip() or line.startswith('State'):
                continue
            
            parts = line.split()
            if len(parts) < 5:
                continue
            
            try:
                # 解析地址和端口
                local_address = parts[4]
                if ':' in local_address:
                    addr_parts = local_address.rsplit(':', 1)
                    if len(addr_parts) == 2:
                        port = int(addr_parts[1])
                        
                        # 解析进程信息
                        pid = None
                        process_name = None
                        
                        if len(parts) > 5:
                            process_info = ' '.join(parts[5:])
                            if 'pid=' in process_info:
                                # 提取PID和进程名
                                import re
                                pid_match = re.search(r'pid=(\d+)', process_info)
                                if pid_match:
                                    pid = int(pid_match.group(1))
                                
                                name_match = re.search(r'"([^"]+)"', process_info)
                                if name_match:
                                    process_name = name_match.group(1)
                        
                        connections[(port, protocol)] = {
                            'local_address': local_address,
                            'pid': pid,
                            'process_name': process_name,
                            'status': parts[0] if len(parts) > 0 else 'UNKNOWN'
                        }
            
            except (ValueError, IndexError):
                continue
        
        return connections
    
    def _check_remote_port(self, port: int, protocol: Protocol, 
                          connections: Dict[Tuple[int, Protocol], Dict[str, Any]]) -> Optional[PortInfo]:
        """
        检查远程端口状态
        
        Args:
            port: 端口号
            protocol: 协议类型
            connections: 连接信息字典
        
        Returns:
            Optional[PortInfo]: 端口信息
        """
        connection_key = (port, protocol)
        
        if connection_key in connections:
            conn_info = connections[connection_key]
            
            # 获取进程信息
            process_info = None
            if conn_info.get('pid'):
                process_info = self._get_remote_process_info(conn_info['pid'])
            
            return PortInfo(
                port=port,
                status=PortStatus.LISTEN,
                protocol=protocol,
                local_address=conn_info['local_address'],
                pid=conn_info.get('pid'),
                process_name=conn_info.get('process_name'),
                process_info=process_info
            )
        
        return None
    
    def _get_remote_process_info(self, pid: int) -> Optional[ProcessInfo]:
        """
        获取远程进程信息
        
        Args:
            pid: 进程ID
        
        Returns:
            Optional[ProcessInfo]: 进程信息
        """
        try:
            # 使用ps命令获取进程信息
            cmd = f"ps -p {pid} -o pid,comm,stat,%cpu,%mem,etime,args --no-headers"
            stdout, stderr, exit_code = self.execute_command(cmd)
            
            if exit_code == 0 and stdout.strip():
                parts = stdout.strip().split(None, 6)
                if len(parts) >= 6:
                    return ProcessInfo(
                        pid=pid,
                        name=parts[1],
                        status=parts[2],
                        cpu_percent=float(parts[3]) if parts[3].replace('.', '').isdigit() else 0.0,
                        memory_percent=float(parts[4]) if parts[4].replace('.', '').isdigit() else 0.0,
                        cmdline=parts[6].split() if len(parts) > 6 else []
                    )
        
        except Exception as e:
            self.logger.debug(f"获取远程进程 {pid} 信息失败: {e}")
        
        return None
    
    def kill_remote_process(self, pid: int, force: bool = False) -> Tuple[bool, str]:
        """
        终止远程进程
        
        Args:
            pid: 进程ID
            force: 是否强制终止
        
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            # 首先检查进程是否存在
            check_cmd = f"ps -p {pid} --no-headers"
            stdout, stderr, exit_code = self.execute_command(check_cmd)
            
            if exit_code != 0 or not stdout.strip():
                return False, f"远程进程 {pid} 不存在"
            
            # 终止进程
            if force:
                kill_cmd = f"kill -9 {pid}"
            else:
                kill_cmd = f"kill -15 {pid}"
            
            stdout, stderr, exit_code = self.execute_command(kill_cmd)
            
            if exit_code == 0:
                # 等待一段时间后检查进程是否已终止
                time.sleep(1)
                stdout, stderr, exit_code = self.execute_command(check_cmd)
                
                if exit_code != 0 or not stdout.strip():
                    return True, f"远程进程 {pid} 已成功终止"
                else:
                    return False, f"远程进程 {pid} 终止失败，进程仍在运行"
            else:
                return False, f"终止远程进程 {pid} 失败: {stderr}"
        
        except Exception as e:
            return False, f"终止远程进程失败: {e}"
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        测试连接
        
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            if self.connect():
                # 执行一个简单的命令来测试
                stdout, stderr, exit_code = self.execute_command("echo 'connection_test'")
                
                if exit_code == 0 and 'connection_test' in stdout:
                    return True, "连接测试成功"
                else:
                    return False, "连接测试失败：命令执行异常"
            else:
                return False, "无法建立SSH连接"
        
        except Exception as e:
            return False, f"连接测试失败: {e}"
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()


class RemoteClientPool:
    """远程客户端连接池"""
    
    def __init__(self, max_connections: int = 5):
        """
        初始化连接池
        
        Args:
            max_connections: 最大连接数
        """
        self.max_connections = max_connections
        self.connections: Dict[str, RemoteClient] = {}
        self.lock = threading.Lock()
        self.logger = get_logger()
    
    def get_client(self, config: RemoteConfig) -> RemoteClient:
        """
        获取远程客户端
        
        Args:
            config: 远程配置
        
        Returns:
            RemoteClient: 远程客户端实例
        """
        key = f"{config.username}@{config.host}:{config.port}"
        
        with self.lock:
            if key in self.connections:
                client = self.connections[key]
                if client.is_connected():
                    return client
                else:
                    # 连接已断开，移除并重新创建
                    del self.connections[key]
            
            # 检查连接数限制
            if len(self.connections) >= self.max_connections:
                # 移除最旧的连接
                oldest_key = next(iter(self.connections))
                self.connections[oldest_key].disconnect()
                del self.connections[oldest_key]
            
            # 创建新连接
            client = RemoteClient(config)
            self.connections[key] = client
            
            return client
    
    def close_all(self):
        """
        关闭所有连接
        """
        with self.lock:
            for client in self.connections.values():
                client.disconnect()
            self.connections.clear()
            self.logger.info("已关闭所有远程连接")
    
    def __del__(self):
        """析构函数"""
        self.close_all()


# 全局连接池实例
_connection_pool = None


def get_remote_client(config: RemoteConfig) -> RemoteClient:
    """
    获取远程客户端的便捷函数
    
    Args:
        config: 远程配置
    
    Returns:
        RemoteClient: 远程客户端实例
    """
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = RemoteClientPool()
    
    return _connection_pool.get_client(config)


@contextmanager
def remote_connection(config: RemoteConfig):
    """
    远程连接上下文管理器
    
    Args:
        config: 远程配置
    
    Yields:
        RemoteClient: 远程客户端实例
    """
    client = get_remote_client(config)
    try:
        if not client.connect():
            raise SSHConnectionError("无法建立SSH连接")
        yield client
    finally:
        # 不在这里断开连接，由连接池管理
        pass
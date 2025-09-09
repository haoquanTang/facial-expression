#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令行接口模块

提供命令行模式的端口扫描和进程管理功能，支持多种输出格式。
"""

import json
import csv
import sys
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
from io import StringIO

from ..models.data_models import (
    ScanConfig, ScanType, Protocol, RemoteConfig, 
    PortInfo, ScanResult, ProcessInfo
)
from ..core.scanner import PortScanner
from ..core.process_manager import ProcessManager
from ..core.remote_client import get_remote_client
from ..utils.logger import get_logger
from ..utils.config import get_config


class CommandLineInterface:
    """命令行接口类"""
    
    def __init__(self):
        """
        初始化命令行接口
        """
        self.logger = get_logger()
        self.scanner = PortScanner()
        self.process_manager = ProcessManager()
    
    def run(self, args) -> int:
        """
        运行命令行接口
        
        Args:
            args: 命令行参数
        
        Returns:
            int: 退出码
        """
        try:
            # 处理进程终止操作
            if args.kill:
                return self._handle_kill_process(args)
            
            # 处理端口扫描操作
            if args.port or args.range or args.ports:
                return self._handle_port_scan(args)
            
            # 如果没有指定具体操作，显示帮助信息
            print("错误: 请指定要执行的操作")
            print("使用 --help 查看帮助信息")
            return 1
        
        except KeyboardInterrupt:
            print("\n操作被用户中断")
            return 130
        except Exception as e:
            self.logger.error(f"命令行操作失败: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            else:
                print(f"错误: {e}")
            return 1
    
    def _handle_kill_process(self, args) -> int:
        """
        处理进程终止操作
        
        Args:
            args: 命令行参数
        
        Returns:
            int: 退出码
        """
        port = args.kill
        protocol = self._parse_protocol(args.protocol)
        
        if not args.quiet:
            print(f"正在查找占用端口 {port}/{protocol[0].value} 的进程...")
        
        # 检查是否为远程操作
        if args.remote:
            return self._handle_remote_kill(args, port, protocol[0])
        
        # 本地进程终止
        success, message = self.process_manager.kill_process_by_port(
            port, protocol[0], force=False
        )
        
        if success:
            if not args.quiet:
                print(f"✓ {message}")
            return 0
        else:
            print(f"✗ {message}")
            return 1
    
    def _handle_remote_kill(self, args, port: int, protocol: Protocol) -> int:
        """
        处理远程进程终止
        
        Args:
            args: 命令行参数
            port: 端口号
            protocol: 协议类型
        
        Returns:
            int: 退出码
        """
        # 创建远程配置
        remote_config = self._create_remote_config(args)
        if not remote_config:
            return 1
        
        try:
            client = get_remote_client(remote_config)
            
            if not client.connect():
                print(f"✗ 无法连接到远程主机 {args.remote}")
                return 1
            
            # 先扫描端口找到进程
            port_info_list = client.scan_remote_ports([port], [protocol])
            
            if not port_info_list:
                print(f"✗ 端口 {port}/{protocol.value} 未被占用")
                return 1
            
            port_info = port_info_list[0]
            if not port_info.pid:
                print(f"✗ 无法获取占用端口 {port} 的进程信息")
                return 1
            
            # 终止远程进程
            success, message = client.kill_remote_process(port_info.pid)
            
            if success:
                if not args.quiet:
                    print(f"✓ {message}")
                return 0
            else:
                print(f"✗ {message}")
                return 1
        
        except Exception as e:
            print(f"✗ 远程操作失败: {e}")
            return 1
    
    def _handle_port_scan(self, args) -> int:
        """
        处理端口扫描操作
        
        Args:
            args: 命令行参数
        
        Returns:
            int: 退出码
        """
        # 解析端口范围
        port_range = self._parse_port_range(args)
        if not port_range:
            print("错误: 无效的端口范围")
            return 1
        
        # 解析协议
        protocols = self._parse_protocol(args.protocol)
        
        # 创建扫描配置
        scan_config = self._create_scan_config(args, port_range, protocols)
        if not scan_config:
            return 1
        
        # 执行扫描
        if not args.quiet:
            target = args.remote if args.remote else "localhost"
            print(f"正在扫描 {target} 的 {len(port_range)} 个端口...")
        
        start_time = time.time()
        result = self.scanner.scan_ports(scan_config)
        end_time = time.time()
        
        if not result.success:
            print(f"✗ 扫描失败: {result.error_message}")
            return 1
        
        # 输出结果
        self._output_scan_result(result, args, end_time - start_time)
        
        return 0
    
    def _parse_port_range(self, args) -> Optional[List[int]]:
        """
        解析端口范围
        
        Args:
            args: 命令行参数
        
        Returns:
            Optional[List[int]]: 端口列表
        """
        try:
            if args.port:
                return [args.port]
            
            elif args.range:
                if '-' in args.range:
                    start, end = map(int, args.range.split('-', 1))
                    if start > end or start < 1 or end > 65535:
                        return None
                    return list(range(start, end + 1))
                else:
                    port = int(args.range)
                    return [port] if 1 <= port <= 65535 else None
            
            elif args.ports:
                ports = []
                for port_str in args.ports.split(','):
                    port_str = port_str.strip()
                    if '-' in port_str:
                        start, end = map(int, port_str.split('-', 1))
                        if start <= end and 1 <= start <= 65535 and 1 <= end <= 65535:
                            ports.extend(range(start, end + 1))
                    else:
                        port = int(port_str)
                        if 1 <= port <= 65535:
                            ports.append(port)
                
                return sorted(list(set(ports))) if ports else None
        
        except ValueError:
            return None
        
        return None
    
    def _parse_protocol(self, protocol_str: str) -> List[Protocol]:
        """
        解析协议类型
        
        Args:
            protocol_str: 协议字符串
        
        Returns:
            List[Protocol]: 协议列表
        """
        if protocol_str.lower() == 'tcp':
            return [Protocol.TCP]
        elif protocol_str.lower() == 'udp':
            return [Protocol.UDP]
        else:  # both
            return [Protocol.TCP, Protocol.UDP]
    
    def _create_remote_config(self, args) -> Optional[RemoteConfig]:
        """
        创建远程配置
        
        Args:
            args: 命令行参数
        
        Returns:
            Optional[RemoteConfig]: 远程配置
        """
        if not args.remote:
            return None
        
        if not args.user:
            print("错误: 远程连接需要指定用户名 (--user)")
            return None
        
        if not args.password and not args.key:
            print("错误: 远程连接需要指定密码 (--password) 或私钥文件 (--key)")
            return None
        
        try:
            config = RemoteConfig(
                host=args.remote,
                username=args.user,
                password=args.password or '',
                private_key_path=args.key or '',
                port=args.ssh_port,
                timeout=10
            )
            
            if not config.validate():
                print("错误: 远程配置无效")
                return None
            
            return config
        
        except Exception as e:
            print(f"错误: 创建远程配置失败: {e}")
            return None
    
    def _create_scan_config(self, args, port_range: List[int], protocols: List[Protocol]) -> Optional[ScanConfig]:
        """
        创建扫描配置
        
        Args:
            args: 命令行参数
            port_range: 端口范围
            protocols: 协议列表
        
        Returns:
            Optional[ScanConfig]: 扫描配置
        """
        try:
            scan_type = ScanType.REMOTE if args.remote else ScanType.LOCAL
            remote_config = self._create_remote_config(args) if args.remote else None
            
            config = ScanConfig(
                port_range=port_range,
                scan_type=scan_type,
                timeout=args.timeout,
                max_threads=args.threads,
                protocols=protocols,
                remote_config=remote_config
            )
            
            is_valid, error_msg = config.validate()
            if not is_valid:
                print(f"错误: {error_msg}")
                return None
            
            return config
        
        except Exception as e:
            print(f"错误: 创建扫描配置失败: {e}")
            return None
    
    def _output_scan_result(self, result: ScanResult, args, duration: float):
        """
        输出扫描结果
        
        Args:
            result: 扫描结果
            args: 命令行参数
            duration: 扫描耗时
        """
        if args.format == 'json':
            self._output_json(result, args)
        elif args.format == 'csv':
            self._output_csv(result, args)
        else:  # table
            self._output_table(result, args, duration)
    
    def _output_table(self, result: ScanResult, args, duration: float):
        """
        输出表格格式
        
        Args:
            result: 扫描结果
            args: 命令行参数
            duration: 扫描耗时
        """
        output = StringIO()
        
        # 统计信息
        if not args.quiet:
            target = args.remote if args.remote else "localhost"
            output.write(f"\n扫描目标: {target}\n")
            output.write(f"扫描时间: {result.scan_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            output.write(f"扫描耗时: {duration:.2f} 秒\n")
            output.write(f"总端口数: {result.total_ports}\n")
            output.write(f"占用端口: {result.occupied_ports}\n")
            output.write(f"空闲端口: {result.free_ports}\n")
            output.write(f"占用率: {result.occupation_rate:.1f}%\n")
            output.write("\n")
        
        # 端口信息表格
        occupied_ports = result.get_occupied_ports()
        
        if occupied_ports:
            # 表头
            headers = ['端口', '协议', '状态', '进程ID', '进程名称', '本地地址']
            if args.verbose:
                headers.extend(['CPU%', '内存%', '命令行'])
            
            # 计算列宽
            col_widths = [len(h) for h in headers]
            
            for port_info in occupied_ports:
                row_data = [
                    str(port_info.port),
                    port_info.protocol.value,
                    port_info.display_status,
                    str(port_info.pid) if port_info.pid else 'N/A',
                    port_info.process_name or 'Unknown',
                    port_info.local_address
                ]
                
                if args.verbose and port_info.process_info:
                    row_data.extend([
                        f"{port_info.process_info.cpu_percent:.1f}",
                        f"{port_info.process_info.memory_percent:.1f}",
                        ' '.join(port_info.process_info.cmdline[:3]) + ('...' if len(port_info.process_info.cmdline) > 3 else '')
                    ])
                elif args.verbose:
                    row_data.extend(['N/A', 'N/A', 'N/A'])
                
                for i, data in enumerate(row_data):
                    col_widths[i] = max(col_widths[i], len(data))
            
            # 输出表格
            separator = '+' + '+'.join('-' * (w + 2) for w in col_widths) + '+'
            
            output.write(separator + '\n')
            
            # 表头
            header_row = '|'
            for i, header in enumerate(headers):
                header_row += f" {header:<{col_widths[i]}} |"
            output.write(header_row + '\n')
            output.write(separator + '\n')
            
            # 数据行
            for port_info in occupied_ports:
                row_data = [
                    str(port_info.port),
                    port_info.protocol.value,
                    port_info.display_status,
                    str(port_info.pid) if port_info.pid else 'N/A',
                    port_info.process_name or 'Unknown',
                    port_info.local_address
                ]
                
                if args.verbose and port_info.process_info:
                    row_data.extend([
                        f"{port_info.process_info.cpu_percent:.1f}",
                        f"{port_info.process_info.memory_percent:.1f}",
                        ' '.join(port_info.process_info.cmdline[:3]) + ('...' if len(port_info.process_info.cmdline) > 3 else '')
                    ])
                elif args.verbose:
                    row_data.extend(['N/A', 'N/A', 'N/A'])
                
                data_row = '|'
                for i, data in enumerate(row_data):
                    data_row += f" {data:<{col_widths[i]}} |"
                output.write(data_row + '\n')
            
            output.write(separator + '\n')
        
        else:
            output.write("未发现占用的端口\n")
        
        # 输出到文件或控制台
        content = output.getvalue()
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(content)
            if not args.quiet:
                print(f"结果已保存到: {args.output}")
        else:
            print(content)
    
    def _output_json(self, result: ScanResult, args):
        """
        输出JSON格式
        
        Args:
            result: 扫描结果
            args: 命令行参数
        """
        data = {
            'scan_time': result.scan_time.isoformat(),
            'scan_type': result.scan_type.value,
            'success': result.success,
            'total_ports': result.total_ports,
            'occupied_ports': result.occupied_ports,
            'free_ports': result.free_ports,
            'occupation_rate': result.occupation_rate,
            'scan_duration': result.scan_duration,
            'ports': []
        }
        
        for port_info in result.port_info_list:
            port_data = {
                'port': port_info.port,
                'protocol': port_info.protocol.value,
                'status': port_info.status.value,
                'is_occupied': port_info.is_occupied,
                'local_address': port_info.local_address,
                'remote_address': port_info.remote_address,
                'pid': port_info.pid,
                'process_name': port_info.process_name
            }
            
            if args.verbose and port_info.process_info:
                port_data['process_info'] = {
                    'cpu_percent': port_info.process_info.cpu_percent,
                    'memory_percent': port_info.process_info.memory_percent,
                    'status': port_info.process_info.status,
                    'cmdline': port_info.process_info.cmdline
                }
            
            data['ports'].append(port_data)
        
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(json_str)
            if not args.quiet:
                print(f"结果已保存到: {args.output}")
        else:
            print(json_str)
    
    def _output_csv(self, result: ScanResult, args):
        """
        输出CSV格式
        
        Args:
            result: 扫描结果
            args: 命令行参数
        """
        output = StringIO()
        writer = csv.writer(output)
        
        # CSV表头
        headers = ['端口', '协议', '状态', '占用', '本地地址', '远程地址', '进程ID', '进程名称']
        if args.verbose:
            headers.extend(['CPU使用率', '内存使用率', '进程状态', '命令行'])
        
        writer.writerow(headers)
        
        # 数据行
        for port_info in result.port_info_list:
            row = [
                port_info.port,
                port_info.protocol.value,
                port_info.status.value,
                '是' if port_info.is_occupied else '否',
                port_info.local_address,
                port_info.remote_address,
                port_info.pid or '',
                port_info.process_name or ''
            ]
            
            if args.verbose:
                if port_info.process_info:
                    row.extend([
                        port_info.process_info.cpu_percent,
                        port_info.process_info.memory_percent,
                        port_info.process_info.status,
                        ' '.join(port_info.process_info.cmdline)
                    ])
                else:
                    row.extend(['', '', '', ''])
            
            writer.writerow(row)
        
        csv_content = output.getvalue()
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8', newline='') as f:
                f.write(csv_content)
            if not args.quiet:
                print(f"结果已保存到: {args.output}")
        else:
            print(csv_content)
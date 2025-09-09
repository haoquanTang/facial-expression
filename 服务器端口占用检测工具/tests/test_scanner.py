#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端口扫描器测试模块

测试端口扫描功能的各种场景。
"""

import unittest
import socket
import threading
import time
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.data_models import ScanConfig, ScanType, Protocol, PortInfo
from src.core.scanner import PortScanner


class TestPortScanner(unittest.TestCase):
    """端口扫描器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.scanner = PortScanner()
        self.test_port = 18888  # 使用一个不常用的端口进行测试
    
    def tearDown(self):
        """测试后清理"""
        pass
    
    def test_scan_config_creation(self):
        """测试扫描配置创建"""
        # 测试基本配置
        config = ScanConfig(
            port_range=[80, 443, 8080],
            scan_type=ScanType.LOCAL,
            protocols=[Protocol.TCP]
        )
        
        self.assertEqual(config.port_count, 3)
        self.assertEqual(config.scan_type, ScanType.LOCAL)
        self.assertIn(Protocol.TCP, config.protocols)
        
        # 测试配置验证
        is_valid, error_msg = config.validate()
        self.assertTrue(is_valid)
        self.assertEqual(error_msg, "")
    
    def test_scan_config_from_string(self):
        """测试从字符串创建扫描配置"""
        # 测试单个端口
        config = ScanConfig.from_port_string("80")
        self.assertEqual(config.port_range, [80])
        
        # 测试端口列表
        config = ScanConfig.from_port_string("80,443,8080")
        self.assertEqual(sorted(config.port_range), [80, 443, 8080])
        
        # 测试端口范围
        config = ScanConfig.from_port_string("8000-8002")
        self.assertEqual(config.port_range, [8000, 8001, 8002])
        
        # 测试混合格式
        config = ScanConfig.from_port_string("80,443,8000-8002")
        expected = sorted([80, 443, 8000, 8001, 8002])
        self.assertEqual(sorted(config.port_range), expected)
    
    def test_scan_config_validation(self):
        """测试扫描配置验证"""
        # 测试空端口范围
        config = ScanConfig(port_range=[])
        is_valid, error_msg = config.validate()
        self.assertFalse(is_valid)
        self.assertIn("端口范围不能为空", error_msg)
        
        # 测试端口数量过多
        large_range = list(range(1, 10002))  # 10001个端口
        config = ScanConfig(port_range=large_range)
        is_valid, error_msg = config.validate()
        self.assertFalse(is_valid)
        self.assertIn("端口数量过多", error_msg)
    
    def test_check_port_status_closed(self):
        """测试检查关闭端口状态"""
        # 测试一个应该关闭的端口
        result = self.scanner.check_port_status("127.0.0.1", self.test_port)
        self.assertFalse(result)
    
    def test_scan_single_port_closed(self):
        """测试扫描关闭的单个端口"""
        port_info = self.scanner.scan_single_port("127.0.0.1", self.test_port)
        # 关闭的端口应该返回None
        self.assertIsNone(port_info)
    
    def test_scan_with_mock_server(self):
        """测试使用模拟服务器进行扫描"""
        # 创建一个临时的TCP服务器
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind(('127.0.0.1', self.test_port))
            server_socket.listen(1)
            
            # 在后台线程中运行服务器
            def server_worker():
                try:
                    server_socket.settimeout(2)
                    conn, addr = server_socket.accept()
                    conn.close()
                except socket.timeout:
                    pass
                except Exception:
                    pass
            
            server_thread = threading.Thread(target=server_worker)
            server_thread.daemon = True
            server_thread.start()
            
            # 等待服务器启动
            time.sleep(0.1)
            
            # 测试端口扫描
            result = self.scanner.check_port_status("127.0.0.1", self.test_port)
            self.assertTrue(result)
            
            # 测试单个端口扫描
            port_info = self.scanner.scan_single_port("127.0.0.1", self.test_port)
            self.assertIsNotNone(port_info)
            self.assertEqual(port_info.port, self.test_port)
            self.assertEqual(port_info.protocol, Protocol.TCP)
            
        finally:
            server_socket.close()
    
    @patch('src.core.scanner.psutil.net_connections')
    def test_get_system_connections(self, mock_net_connections):
        """测试获取系统连接信息"""
        # 模拟psutil.net_connections的返回值
        mock_connection = MagicMock()
        mock_connection.laddr.port = 80
        mock_connection.laddr.ip = '0.0.0.0'
        mock_connection.raddr = None
        mock_connection.pid = 1234
        mock_connection.type = socket.SOCK_STREAM
        mock_connection.status = 'LISTEN'
        
        mock_net_connections.return_value = [mock_connection]
        
        # 调用私有方法进行测试
        connections = self.scanner._get_system_connections()
        
        # 验证结果
        self.assertIn((80, Protocol.TCP), connections)
        conn_info = connections[(80, Protocol.TCP)]
        self.assertEqual(conn_info['pid'], 1234)
        self.assertEqual(conn_info['local_address'], '0.0.0.0:80')
    
    def test_scan_local_ports_empty_range(self):
        """测试扫描空端口范围"""
        config = ScanConfig(
            port_range=[],
            scan_type=ScanType.LOCAL,
            protocols=[Protocol.TCP]
        )
        
        result = self.scanner.scan_ports(config)
        self.assertFalse(result.success)
        self.assertIn("端口范围不能为空", result.error_message)
    
    def test_scan_local_ports_valid_range(self):
        """测试扫描有效端口范围"""
        config = ScanConfig(
            port_range=[self.test_port, self.test_port + 1],
            scan_type=ScanType.LOCAL,
            protocols=[Protocol.TCP],
            timeout=0.5,
            max_threads=2
        )
        
        result = self.scanner.scan_ports(config)
        self.assertTrue(result.success)
        self.assertEqual(result.scan_type, ScanType.LOCAL)
        self.assertGreaterEqual(result.total_ports, 0)
    
    def test_stop_scan(self):
        """测试停止扫描"""
        # 测试停止扫描功能
        self.assertFalse(self.scanner._stop_scan)
        
        self.scanner.stop_scan()
        self.assertTrue(self.scanner._stop_scan)
    
    def test_port_info_properties(self):
        """测试端口信息属性"""
        from src.models.data_models import PortStatus
        
        # 测试占用端口
        port_info = PortInfo(
            port=80,
            status=PortStatus.LISTEN,
            protocol=Protocol.TCP,
            local_address="0.0.0.0:80"
        )
        
        self.assertTrue(port_info.is_occupied)
        self.assertEqual(port_info.display_status, "占用")
        
        # 测试关闭端口
        port_info_closed = PortInfo(
            port=8080,
            status=PortStatus.CLOSED,
            protocol=Protocol.TCP,
            local_address="127.0.0.1:8080"
        )
        
        self.assertFalse(port_info_closed.is_occupied)
        self.assertEqual(port_info_closed.display_status, "空闲")


class TestScanResult(unittest.TestCase):
    """扫描结果测试类"""
    
    def test_scan_result_statistics(self):
        """测试扫描结果统计"""
        from src.models.data_models import ScanResult, PortStatus
        from datetime import datetime
        
        # 创建测试端口信息
        port_info_list = [
            PortInfo(
                port=80,
                status=PortStatus.LISTEN,
                protocol=Protocol.TCP,
                local_address="0.0.0.0:80"
            ),
            PortInfo(
                port=443,
                status=PortStatus.LISTEN,
                protocol=Protocol.TCP,
                local_address="0.0.0.0:443"
            ),
            PortInfo(
                port=8080,
                status=PortStatus.CLOSED,
                protocol=Protocol.TCP,
                local_address="127.0.0.1:8080"
            )
        ]
        
        # 创建扫描结果
        result = ScanResult(
            scan_time=datetime.now(),
            scan_type=ScanType.LOCAL,
            port_info_list=port_info_list,
            success=True
        )
        
        # 验证统计信息
        self.assertEqual(result.total_ports, 3)
        self.assertEqual(result.occupied_ports, 2)
        self.assertEqual(result.free_ports, 1)
        self.assertAlmostEqual(result.occupation_rate, 66.7, places=1)
        
        # 测试获取占用端口
        occupied_ports = result.get_occupied_ports()
        self.assertEqual(len(occupied_ports), 2)
        
        # 测试获取空闲端口
        free_ports = result.get_free_ports()
        self.assertEqual(len(free_ports), 1)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
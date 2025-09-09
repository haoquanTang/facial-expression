#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进程管理器测试模块

测试进程管理功能的各种场景。
"""

import unittest
import os
import time
import subprocess
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.data_models import ProcessInfo, Protocol
from src.core.process_manager import ProcessManager


class TestProcessManager(unittest.TestCase):
    """进程管理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.process_manager = ProcessManager()
    
    def tearDown(self):
        """测试后清理"""
        pass
    
    @patch('src.core.process_manager.psutil.process_iter')
    def test_get_process_info_by_pid(self, mock_process_iter):
        """测试根据PID获取进程信息"""
        # 模拟进程对象
        mock_process = MagicMock()
        mock_process.pid = 1234
        mock_process.name.return_value = "test_process"
        mock_process.exe.return_value = "/usr/bin/test_process"
        mock_process.cmdline.return_value = ["test_process", "--arg1", "--arg2"]
        mock_process.status.return_value = "running"
        mock_process.create_time.return_value = time.time() - 3600  # 1小时前创建
        mock_process.memory_info.return_value.rss = 1024 * 1024  # 1MB
        mock_process.cpu_percent.return_value = 5.5
        
        mock_process_iter.return_value = [mock_process]
        
        # 测试获取进程信息
        process_info = self.process_manager.get_process_info(1234)
        
        self.assertIsNotNone(process_info)
        self.assertEqual(process_info.pid, 1234)
        self.assertEqual(process_info.name, "test_process")
        self.assertEqual(process_info.executable, "/usr/bin/test_process")
        self.assertEqual(process_info.status, "running")
    
    @patch('src.core.process_manager.psutil.process_iter')
    def test_get_process_info_not_found(self, mock_process_iter):
        """测试获取不存在的进程信息"""
        mock_process_iter.return_value = []
        
        # 测试获取不存在的进程
        process_info = self.process_manager.get_process_info(99999)
        self.assertIsNone(process_info)
    
    @patch('src.core.process_manager.psutil.net_connections')
    def test_get_processes_by_port(self, mock_net_connections):
        """测试根据端口获取进程列表"""
        # 模拟网络连接
        mock_connection = MagicMock()
        mock_connection.laddr.port = 80
        mock_connection.pid = 1234
        mock_connection.type = 1  # SOCK_STREAM
        
        mock_net_connections.return_value = [mock_connection]
        
        # 模拟进程信息
        with patch.object(self.process_manager, 'get_process_info') as mock_get_process:
            mock_process_info = ProcessInfo(
                pid=1234,
                name="nginx",
                executable="/usr/sbin/nginx",
                command_line="nginx -g daemon off;",
                status="running",
                create_time=time.time() - 3600,
                memory_usage=1024 * 1024,
                cpu_percent=2.5
            )
            mock_get_process.return_value = mock_process_info
            
            # 测试获取端口进程
            processes = self.process_manager.get_processes_by_port(80, Protocol.TCP)
            
            self.assertEqual(len(processes), 1)
            self.assertEqual(processes[0].pid, 1234)
            self.assertEqual(processes[0].name, "nginx")
    
    @patch('src.core.process_manager.psutil.process_iter')
    def test_find_processes_by_name(self, mock_process_iter):
        """测试根据名称查找进程"""
        # 模拟多个进程
        mock_process1 = MagicMock()
        mock_process1.pid = 1234
        mock_process1.name.return_value = "nginx"
        
        mock_process2 = MagicMock()
        mock_process2.pid = 1235
        mock_process2.name.return_value = "nginx"
        
        mock_process3 = MagicMock()
        mock_process3.pid = 1236
        mock_process3.name.return_value = "apache2"
        
        mock_process_iter.return_value = [mock_process1, mock_process2, mock_process3]
        
        # 模拟get_process_info方法
        def mock_get_process_info(pid):
            if pid == 1234:
                return ProcessInfo(pid=1234, name="nginx", executable="/usr/sbin/nginx")
            elif pid == 1235:
                return ProcessInfo(pid=1235, name="nginx", executable="/usr/sbin/nginx")
            return None
        
        with patch.object(self.process_manager, 'get_process_info', side_effect=mock_get_process_info):
            # 测试查找nginx进程
            processes = self.process_manager.find_processes_by_name("nginx")
            
            self.assertEqual(len(processes), 2)
            self.assertEqual(processes[0].pid, 1234)
            self.assertEqual(processes[1].pid, 1235)
    
    def test_is_protected_process(self):
        """测试检查进程是否受保护"""
        # 测试系统进程（受保护）
        self.assertTrue(self.process_manager.is_protected_process(1))  # init进程
        
        # 测试普通进程（不受保护）
        self.assertFalse(self.process_manager.is_protected_process(99999))
        
        # 测试受保护的进程名称
        protected_process = ProcessInfo(
            pid=1234,
            name="systemd",
            executable="/usr/lib/systemd/systemd"
        )
        
        with patch.object(self.process_manager, 'get_process_info', return_value=protected_process):
            self.assertTrue(self.process_manager.is_protected_process(1234))
    
    @patch('src.core.process_manager.psutil.Process')
    def test_terminate_process_success(self, mock_process_class):
        """测试成功终止进程"""
        # 模拟进程对象
        mock_process = MagicMock()
        mock_process.is_running.return_value = True
        mock_process_class.return_value = mock_process
        
        # 模拟非受保护进程
        with patch.object(self.process_manager, 'is_protected_process', return_value=False):
            # 测试优雅终止
            success, message = self.process_manager.terminate_process(1234, force=False)
            
            self.assertTrue(success)
            self.assertIn("成功", message)
            mock_process.terminate.assert_called_once()
    
    @patch('src.core.process_manager.psutil.Process')
    def test_terminate_process_protected(self, mock_process_class):
        """测试终止受保护进程"""
        # 模拟受保护进程
        with patch.object(self.process_manager, 'is_protected_process', return_value=True):
            success, message = self.process_manager.terminate_process(1, force=False)
            
            self.assertFalse(success)
            self.assertIn("受保护", message)
    
    @patch('src.core.process_manager.psutil.Process')
    def test_terminate_process_not_found(self, mock_process_class):
        """测试终止不存在的进程"""
        # 模拟进程不存在
        from psutil import NoSuchProcess
        mock_process_class.side_effect = NoSuchProcess(99999)
        
        success, message = self.process_manager.terminate_process(99999)
        
        self.assertFalse(success)
        self.assertIn("不存在", message)
    
    @patch('src.core.process_manager.psutil.Process')
    def test_terminate_process_force(self, mock_process_class):
        """测试强制终止进程"""
        # 模拟进程对象
        mock_process = MagicMock()
        mock_process.is_running.return_value = True
        mock_process_class.return_value = mock_process
        
        # 模拟非受保护进程
        with patch.object(self.process_manager, 'is_protected_process', return_value=False):
            # 测试强制终止
            success, message = self.process_manager.terminate_process(1234, force=True)
            
            self.assertTrue(success)
            self.assertIn("成功", message)
            mock_process.kill.assert_called_once()
    
    @patch('src.core.process_manager.psutil.net_connections')
    def test_get_all_port_usage(self, mock_net_connections):
        """测试获取所有端口使用情况"""
        # 模拟网络连接
        mock_connection1 = MagicMock()
        mock_connection1.laddr.port = 80
        mock_connection1.laddr.ip = '0.0.0.0'
        mock_connection1.pid = 1234
        mock_connection1.type = 1  # SOCK_STREAM
        mock_connection1.status = 'LISTEN'
        
        mock_connection2 = MagicMock()
        mock_connection2.laddr.port = 443
        mock_connection2.laddr.ip = '0.0.0.0'
        mock_connection2.pid = 1235
        mock_connection2.type = 1  # SOCK_STREAM
        mock_connection2.status = 'LISTEN'
        
        mock_net_connections.return_value = [mock_connection1, mock_connection2]
        
        # 测试获取端口使用情况
        port_usage = self.process_manager.get_all_port_usage()
        
        self.assertIn((80, Protocol.TCP), port_usage)
        self.assertIn((443, Protocol.TCP), port_usage)
        
        # 验证端口信息
        port_80_info = port_usage[(80, Protocol.TCP)]
        self.assertEqual(port_80_info['pid'], 1234)
        self.assertEqual(port_80_info['local_address'], '0.0.0.0:80')
        self.assertEqual(port_80_info['status'], 'LISTEN')
    
    @patch('src.core.process_manager.psutil.process_iter')
    def test_get_all_processes(self, mock_process_iter):
        """测试获取所有进程列表"""
        # 模拟进程
        mock_process1 = MagicMock()
        mock_process1.pid = 1234
        mock_process1.name.return_value = "nginx"
        
        mock_process2 = MagicMock()
        mock_process2.pid = 1235
        mock_process2.name.return_value = "apache2"
        
        mock_process_iter.return_value = [mock_process1, mock_process2]
        
        # 模拟get_process_info方法
        def mock_get_process_info(pid):
            if pid == 1234:
                return ProcessInfo(pid=1234, name="nginx", executable="/usr/sbin/nginx")
            elif pid == 1235:
                return ProcessInfo(pid=1235, name="apache2", executable="/usr/sbin/apache2")
            return None
        
        with patch.object(self.process_manager, 'get_process_info', side_effect=mock_get_process_info):
            # 测试获取所有进程
            processes = self.process_manager.get_all_processes()
            
            self.assertEqual(len(processes), 2)
            process_names = [p.name for p in processes]
            self.assertIn("nginx", process_names)
            self.assertIn("apache2", process_names)
    
    def test_has_permission(self):
        """测试权限检查"""
        # 在大多数系统上，普通用户应该有基本的进程查看权限
        # 但可能没有终止其他用户进程的权限
        has_perm = self.process_manager.has_permission()
        
        # 这个测试主要确保方法能正常运行，不抛出异常
        self.assertIsInstance(has_perm, bool)
    
    def test_process_info_properties(self):
        """测试进程信息属性"""
        # 测试进程信息的各种属性
        process_info = ProcessInfo(
            pid=1234,
            name="test_process",
            executable="/usr/bin/test_process",
            command_line="test_process --arg1 --arg2",
            status="running",
            create_time=time.time() - 3600,  # 1小时前
            memory_usage=1024 * 1024 * 10,  # 10MB
            cpu_percent=15.5
        )
        
        # 测试内存格式化
        self.assertEqual(process_info.memory_mb, 10.0)
        
        # 测试运行时间计算
        runtime = process_info.runtime_seconds
        self.assertGreater(runtime, 3500)  # 应该接近3600秒
        self.assertLess(runtime, 3700)
        
        # 测试字符串表示
        str_repr = str(process_info)
        self.assertIn("test_process", str_repr)
        self.assertIn("1234", str_repr)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
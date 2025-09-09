#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基础功能测试脚本

不依赖外部库的基础测试，验证项目结构和基本功能。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_project_structure():
    """测试项目结构"""
    print("测试项目结构...")
    
    required_files = [
        'src/__init__.py',
        'src/main.py',
        'src/models/__init__.py',
        'src/models/data_models.py',
        'src/core/__init__.py',
        'src/core/scanner.py',
        'src/core/process_manager.py',
        'src/core/remote_client.py',
        'src/utils/__init__.py',
        'src/utils/config.py',
        'src/utils/logger.py',
        'src/cli/__init__.py',
        'src/cli/command_line.py',
        'src/gui/__init__.py',
        'src/gui/main_window.py',
        'src/gui/remote_config.py',
        'requirements.txt',
        'setup.py',
        'README.md',
        'Makefile'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"✓ {file_path}")
    
    if missing_files:
        print(f"\n✗ 缺少文件: {missing_files}")
        return False
    
    print("✅ 项目结构完整")
    return True

def test_data_models():
    """测试数据模型"""
    print("\n测试数据模型...")
    
    try:
        from src.models.data_models import (
            PortStatus, Protocol, ScanType,
            ProcessInfo, PortInfo, RemoteConfig, ScanResult, ScanConfig
        )
        
        # 测试枚举
        print(f"✓ PortStatus: {list(PortStatus)}")
        print(f"✓ Protocol: {list(Protocol)}")
        print(f"✓ ScanType: {list(ScanType)}")
        
        # 测试数据类创建
        process_info = ProcessInfo(
            pid=1234,
            name="test_process",
            executable="/usr/bin/test"
        )
        print(f"✓ ProcessInfo: {process_info.name} (PID: {process_info.pid})")
        
        port_info = PortInfo(
            port=80,
            status=PortStatus.LISTEN,
            protocol=Protocol.TCP,
            local_address="0.0.0.0:80"
        )
        print(f"✓ PortInfo: {port_info.port}/{port_info.protocol.value} - {port_info.display_status}")
        
        remote_config = RemoteConfig(
            name="test_server",
            host="192.168.1.100",
            port=22,
            username="admin"
        )
        print(f"✓ RemoteConfig: {remote_config.name} ({remote_config.host}:{remote_config.port})")
        
        scan_config = ScanConfig(
            port_range=[80, 443, 8080],
            scan_type=ScanType.LOCAL,
            protocols=[Protocol.TCP]
        )
        print(f"✓ ScanConfig: {scan_config.port_count} 个端口")
        
        # 测试配置验证
        is_valid, error_msg = scan_config.validate()
        print(f"✓ 配置验证: {'有效' if is_valid else f'无效 - {error_msg}'}")
        
        print("✅ 数据模型测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 数据模型测试失败: {e}")
        return False

def test_config_manager():
    """测试配置管理器"""
    print("\n测试配置管理器...")
    
    try:
        from src.utils.config import ConfigManager
        
        # 创建配置管理器实例
        config_manager = ConfigManager()
        print(f"✓ 配置管理器创建成功")
        print(f"✓ 配置目录: {config_manager.config_dir}")
        print(f"✓ 配置文件: {config_manager.config_file}")
        
        # 测试默认配置
        default_config = config_manager.get_default_config()
        print(f"✓ 默认配置加载: {len(default_config)} 个配置项")
        
        # 测试配置获取
        scan_timeout = config_manager.get('scan_timeout', 5)
        print(f"✓ 扫描超时配置: {scan_timeout}秒")
        
        print("✅ 配置管理器测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 配置管理器测试失败: {e}")
        return False

def test_imports():
    """测试模块导入"""
    print("\n测试模块导入...")
    
    modules_to_test = [
        ('src.models.data_models', '数据模型'),
        ('src.utils.config', '配置管理'),
        ('src.utils.logger', '日志管理'),
        ('src.cli.command_line', '命令行接口'),
        ('src.gui.main_window', 'GUI主窗口'),
        ('src.gui.remote_config', '远程配置窗口')
    ]
    
    success_count = 0
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"✓ {description} ({module_name})")
            success_count += 1
        except ImportError as e:
            print(f"✗ {description} ({module_name}): {e}")
        except Exception as e:
            print(f"⚠ {description} ({module_name}): {e}")
    
    print(f"\n模块导入结果: {success_count}/{len(modules_to_test)} 成功")
    return success_count == len(modules_to_test)

def test_file_permissions():
    """测试文件权限"""
    print("\n测试文件权限...")
    
    executable_files = [
        'src/main.py',
        'tests/run_tests.py',
        'test_basic.py'
    ]
    
    for file_path in executable_files:
        if Path(file_path).exists():
            # 检查文件是否可读
            if os.access(file_path, os.R_OK):
                print(f"✓ {file_path} 可读")
            else:
                print(f"✗ {file_path} 不可读")
        else:
            print(f"⚠ {file_path} 不存在")
    
    return True

def main():
    """主测试函数"""
    print("="*60)
    print("服务器端口占用检测工具 - 基础功能测试")
    print("="*60)
    
    tests = [
        ('项目结构', test_project_structure),
        ('数据模型', test_data_models),
        ('配置管理', test_config_manager),
        ('模块导入', test_imports),
        ('文件权限', test_file_permissions)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed_tests += 1
        except Exception as e:
            print(f"✗ {test_name} 测试异常: {e}")
    
    print("\n" + "="*60)
    print("测试结果摘要")
    print("="*60)
    print(f"总测试数: {total_tests}")
    print(f"通过: {passed_tests}")
    print(f"失败: {total_tests - passed_tests}")
    
    success_rate = (passed_tests / total_tests) * 100
    print(f"成功率: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("🎉 所有基础测试通过！")
        print("\n下一步:")
        print("1. 安装依赖: pip install -r requirements.txt")
        print("2. 运行完整测试: python tests/run_tests.py")
        print("3. 启动GUI: python src/main.py --gui")
        print("4. 命令行扫描: python src/main.py --ports 80,443,8080")
    elif success_rate >= 80:
        print("✅ 大部分基础测试通过")
    else:
        print("⚠️ 需要修复基础问题")
    
    print("="*60)
    return success_rate == 100

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
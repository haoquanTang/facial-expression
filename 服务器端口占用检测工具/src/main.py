#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器端口占用检测工具 - 主入口文件

支持GUI和命令行两种模式，提供端口扫描和进程管理功能。
"""

import sys
import os
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger
from src.utils.config import get_config_manager
from src.models.data_models import ScanConfig, ScanType, Protocol, RemoteConfig
from src.core.scanner import PortScanner
from src.core.process_manager import ProcessManager
from src.cli.command_line import CommandLineInterface


def check_dependencies(gui_mode: bool = False):
    """检查必要的依赖库
    
    Args:
        gui_mode: 是否为GUI模式
    
    Returns:
        bool: 如果所有依赖都可用返回True
    """
    missing_deps = []
    
    # 检查psutil
    try:
        import psutil
    except ImportError:
        missing_deps.append("psutil")
    
    # 只在GUI模式下检查tkinter
    if gui_mode:
        try:
            import tkinter
        except ImportError:
            missing_deps.append("tkinter")
    
    # 检查paramiko（远程连接需要）
    try:
        import paramiko
    except ImportError:
        missing_deps.append("paramiko")
    
    if missing_deps:
        print("错误: 缺少必要的依赖库:", ", ".join(missing_deps))
        print("请运行以下命令安装:")
        if "psutil" in missing_deps:
            print("  pip install psutil")
        if "paramiko" in missing_deps:
            print("  pip install paramiko")
        if "tkinter" in missing_deps:
            print("  # tkinter通常随Python一起安装，如果缺失请重新安装Python")
        return False
    
    return True


def setup_logging():
    """
    设置日志系统
    """
    logger = get_logger()
    logger.info("服务器端口占用检测工具启动")
    return logger


def parse_arguments():
    """
    解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(
        description='服务器端口占用检测工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 启动GUI模式
  python main.py
  python main.py --gui
  
  # 扫描单个端口
  python main.py --port 8080
  
  # 扫描端口范围
  python main.py --range 8000-9000
  python main.py --ports 80,443,8080
  
  # 杀死占用指定端口的进程
  python main.py --kill 8080
  
  # 远程扫描
  python main.py --remote 192.168.1.100 --user admin --password secret --range 80-443
  
  # 输出JSON格式
  python main.py --port 8080 --format json
        """
    )
    
    # 模式选择
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--gui', 
        action='store_true',
        help='启动GUI模式（默认）'
    )
    mode_group.add_argument(
        '--cli', 
        action='store_true',
        help='强制使用命令行模式'
    )
    
    # 端口扫描参数
    port_group = parser.add_mutually_exclusive_group()
    port_group.add_argument(
        '--port', '-p',
        type=int,
        help='扫描单个端口'
    )
    port_group.add_argument(
        '--range', '-r',
        type=str,
        help='扫描端口范围，格式: 8000-9000'
    )
    port_group.add_argument(
        '--ports',
        type=str,
        help='扫描多个端口，用逗号分隔，格式: 80,443,8080'
    )
    
    # 进程管理参数
    parser.add_argument(
        '--kill', '-k',
        type=int,
        help='杀死占用指定端口的进程'
    )
    
    # 远程连接参数
    parser.add_argument(
        '--remote',
        type=str,
        help='远程主机IP地址'
    )
    parser.add_argument(
        '--user', '-u',
        type=str,
        help='SSH用户名'
    )
    parser.add_argument(
        '--password',
        type=str,
        help='SSH密码'
    )
    parser.add_argument(
        '--key',
        type=str,
        help='SSH私钥文件路径'
    )
    parser.add_argument(
        '--ssh-port',
        type=int,
        default=22,
        help='SSH端口号（默认: 22）'
    )
    
    # 扫描选项
    parser.add_argument(
        '--protocol',
        choices=['tcp', 'udp', 'both'],
        default='both',
        help='扫描协议类型（默认: both）'
    )
    parser.add_argument(
        '--timeout',
        type=float,
        default=1.0,
        help='扫描超时时间（秒，默认: 1.0）'
    )
    parser.add_argument(
        '--threads',
        type=int,
        default=50,
        help='最大线程数（默认: 50）'
    )
    
    # 输出选项
    parser.add_argument(
        '--format',
        choices=['table', 'json', 'csv'],
        default='table',
        help='输出格式（默认: table）'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='输出文件路径'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='静默模式'
    )
    
    # 其他选项
    parser.add_argument(
        '--config',
        type=str,
        help='配置文件路径'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='服务器端口占用检测工具 v1.0.0'
    )
    
    return parser.parse_args()


def should_use_gui(args):
    """
    判断是否应该使用GUI模式
    
    Args:
        args: 命令行参数
    
    Returns:
        bool: 是否使用GUI模式
    """
    # 如果明确指定了CLI模式
    if args.cli:
        return False
    
    # 如果明确指定了GUI模式
    if args.gui:
        return True
    
    # 如果提供了任何命令行操作参数，使用CLI模式
    cli_args = [args.port, args.range, args.ports, args.kill, args.remote]
    if any(arg is not None for arg in cli_args):
        return False
    
    # 检查是否有图形界面支持
    try:
        import tkinter
        # 尝试创建一个测试窗口
        root = tkinter.Tk()
        root.withdraw()  # 隐藏窗口
        root.destroy()
        return True
    except Exception:
        return False


def run_gui_mode(args):
    """
    运行GUI模式
    
    Args:
        args: 命令行参数
    """
    try:
        from src.gui.main_window import MainWindow
        
        logger = get_logger()
        logger.info("启动GUI模式")
        
        app = MainWindow()
        app.run()
        
    except ImportError as e:
        print(f"错误: 无法导入GUI模块: {e}")
        print("请检查tkinter是否正确安装")
        sys.exit(1)
    except Exception as e:
        logger = get_logger()
        logger.error(f"GUI模式运行失败: {e}")
        print(f"GUI模式启动失败: {e}")
        sys.exit(1)


def run_cli_mode(args):
    """
    运行命令行模式
    
    Args:
        args: 命令行参数
    """
    try:
        logger = get_logger()
        logger.info("启动命令行模式")
        
        cli = CommandLineInterface()
        exit_code = cli.run(args)
        sys.exit(exit_code)
        
    except Exception as e:
        logger = get_logger()
        logger.error(f"命令行模式运行失败: {e}")
        print(f"命令行模式运行失败: {e}")
        sys.exit(1)


def main():
    """
    主函数
    """
    try:
        # 解析命令行参数
        args = parse_arguments()
        
        # 判断运行模式
        gui_mode = should_use_gui(args)
        
        # 检查依赖
        if not check_dependencies(gui_mode):
            sys.exit(1)
        
        # 设置日志
        logger = setup_logging()
        
        # 设置日志级别
        if args.verbose:
            logger.set_level('DEBUG')
        elif args.quiet:
            logger.set_level('ERROR')
        
        # 加载自定义配置文件
        if args.config:
            config_manager = get_config_manager()
            if os.path.exists(args.config):
                logger.info(f"加载配置文件: {args.config}")
                # 这里可以添加自定义配置文件加载逻辑
            else:
                logger.warning(f"配置文件不存在: {args.config}")
        
        # 判断运行模式
        if gui_mode:
            run_gui_mode(args)
        else:
            run_cli_mode(args)
    
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"程序运行出错: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
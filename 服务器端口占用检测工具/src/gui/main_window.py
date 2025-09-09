#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI主窗口模块

实现图形用户界面的主窗口，包含端口扫描配置、结果展示和进程管理功能。
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.data_models import (
    ScanConfig, ScanType, Protocol, RemoteConfig, 
    PortInfo, ScanResult, ProcessInfo
)
from ..core.scanner import PortScanner
from ..core.process_manager import ProcessManager
from ..utils.logger import get_logger
from ..utils.config import get_config_manager
from .remote_config import RemoteConfigDialog


class MainWindow:
    """主窗口类"""
    
    def __init__(self):
        """
        初始化主窗口
        """
        self.logger = get_logger()
        self.config_manager = get_config_manager()
        self.scanner = PortScanner()
        self.process_manager = ProcessManager()
        
        # 窗口和组件
        self.root = None
        self.scan_frame = None
        self.result_frame = None
        self.status_frame = None
        
        # 扫描相关
        self.scan_thread = None
        self.is_scanning = False
        self.current_result = None
        
        # 远程配置
        self.remote_configs = []
        self.current_remote_config = None
        
        # 初始化界面
        self._init_ui()
        self._load_config()
    
    def _init_ui(self):
        """
        初始化用户界面
        """
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("服务器端口占用检测工具")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # 设置窗口图标（如果有的话）
        try:
            # 这里可以设置窗口图标
            pass
        except:
            pass
        
        # 创建菜单栏
        self._create_menu()
        
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建左侧配置面板
        self._create_scan_panel(main_frame)
        
        # 创建右侧结果面板
        self._create_result_panel(main_frame)
        
        # 创建底部状态栏
        self._create_status_bar()
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_menu(self):
        """
        创建菜单栏
        """
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导出结果...", command=self._export_results)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self._on_closing)
        
        # 配置菜单
        config_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="配置", menu=config_menu)
        config_menu.add_command(label="远程服务器...", command=self._show_remote_config)
        config_menu.add_command(label="应用设置...", command=self._show_app_settings)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="进程管理器", command=self._show_process_manager)
        tools_menu.add_command(label="网络连接查看器", command=self._show_network_connections)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self._show_help)
        help_menu.add_command(label="关于", command=self._show_about)
    
    def _create_scan_panel(self, parent):
        """
        创建扫描配置面板
        
        Args:
            parent: 父容器
        """
        # 左侧框架
        left_frame = ttk.Frame(parent)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 扫描配置组
        scan_group = ttk.LabelFrame(left_frame, text="扫描配置", padding=10)
        scan_group.pack(fill=tk.X, pady=(0, 10))
        
        # 扫描模式
        ttk.Label(scan_group, text="扫描模式:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.scan_mode = tk.StringVar(value="local")
        mode_frame = ttk.Frame(scan_group)
        mode_frame.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        ttk.Radiobutton(mode_frame, text="本地", variable=self.scan_mode, value="local", 
                       command=self._on_scan_mode_change).pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="远程", variable=self.scan_mode, value="remote", 
                       command=self._on_scan_mode_change).pack(side=tk.LEFT, padx=(10, 0))
        
        # 远程服务器选择
        ttk.Label(scan_group, text="远程服务器:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.remote_server = ttk.Combobox(scan_group, width=25, state="readonly")
        self.remote_server.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        self.remote_server.bind("<<ComboboxSelected>>", self._on_remote_server_change)
        
        # 端口配置
        ttk.Label(scan_group, text="端口范围:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.port_entry = ttk.Entry(scan_group, width=30)
        self.port_entry.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        self.port_entry.insert(0, "80,443,8080,3306,5432")
        
        # 端口范围说明
        help_label = ttk.Label(scan_group, text="格式: 80,443,8000-9000", foreground="gray")
        help_label.grid(row=3, column=1, sticky=tk.W, padx=(10, 0))
        
        # 协议选择
        ttk.Label(scan_group, text="协议类型:").grid(row=4, column=0, sticky=tk.W, pady=2)
        protocol_frame = ttk.Frame(scan_group)
        protocol_frame.grid(row=4, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        self.tcp_var = tk.BooleanVar(value=True)
        self.udp_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(protocol_frame, text="TCP", variable=self.tcp_var).pack(side=tk.LEFT)
        ttk.Checkbutton(protocol_frame, text="UDP", variable=self.udp_var).pack(side=tk.LEFT, padx=(10, 0))
        
        # 扫描选项
        options_group = ttk.LabelFrame(left_frame, text="扫描选项", padding=10)
        options_group.pack(fill=tk.X, pady=(0, 10))
        
        # 超时时间
        ttk.Label(options_group, text="超时时间(秒):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.timeout_var = tk.DoubleVar(value=1.0)
        timeout_spin = ttk.Spinbox(options_group, from_=0.1, to=10.0, increment=0.1, 
                                  textvariable=self.timeout_var, width=10)
        timeout_spin.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # 线程数
        ttk.Label(options_group, text="线程数:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.threads_var = tk.IntVar(value=50)
        threads_spin = ttk.Spinbox(options_group, from_=1, to=200, increment=1, 
                                  textvariable=self.threads_var, width=10)
        threads_spin.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # 控制按钮
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.scan_button = ttk.Button(button_frame, text="开始扫描", command=self._start_scan)
        self.scan_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="停止扫描", command=self._stop_scan, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.refresh_button = ttk.Button(button_frame, text="刷新", command=self._refresh_results)
        self.refresh_button.pack(side=tk.LEFT, padx=5)
        
        # 初始状态设置
        self._on_scan_mode_change()
    
    def _create_result_panel(self, parent):
        """
        创建结果展示面板
        
        Args:
            parent: 父容器
        """
        # 右侧框架
        right_frame = ttk.Frame(parent)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 结果信息
        info_frame = ttk.Frame(right_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.info_label = ttk.Label(info_frame, text="准备就绪")
        self.info_label.pack(side=tk.LEFT)
        
        # 进度条
        self.progress = ttk.Progressbar(info_frame, mode='indeterminate')
        self.progress.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 结果表格
        result_group = ttk.LabelFrame(right_frame, text="扫描结果", padding=5)
        result_group.pack(fill=tk.BOTH, expand=True)
        
        # 创建Treeview
        columns = ('port', 'protocol', 'status', 'pid', 'process', 'address')
        self.result_tree = ttk.Treeview(result_group, columns=columns, show='headings', height=15)
        
        # 设置列标题和宽度
        self.result_tree.heading('port', text='端口')
        self.result_tree.heading('protocol', text='协议')
        self.result_tree.heading('status', text='状态')
        self.result_tree.heading('pid', text='进程ID')
        self.result_tree.heading('process', text='进程名称')
        self.result_tree.heading('address', text='地址')
        
        self.result_tree.column('port', width=80, anchor=tk.CENTER)
        self.result_tree.column('protocol', width=60, anchor=tk.CENTER)
        self.result_tree.column('status', width=80, anchor=tk.CENTER)
        self.result_tree.column('pid', width=80, anchor=tk.CENTER)
        self.result_tree.column('process', width=150, anchor=tk.W)
        self.result_tree.column('address', width=200, anchor=tk.W)
        
        # 滚动条
        scrollbar_y = ttk.Scrollbar(result_group, orient=tk.VERTICAL, command=self.result_tree.yview)
        scrollbar_x = ttk.Scrollbar(result_group, orient=tk.HORIZONTAL, command=self.result_tree.xview)
        self.result_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # 布局
        self.result_tree.grid(row=0, column=0, sticky='nsew')
        scrollbar_y.grid(row=0, column=1, sticky='ns')
        scrollbar_x.grid(row=1, column=0, sticky='ew')
        
        result_group.grid_rowconfigure(0, weight=1)
        result_group.grid_columnconfigure(0, weight=1)
        
        # 右键菜单
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="终止进程", command=self._kill_selected_process)
        self.context_menu.add_command(label="查看进程详情", command=self._show_process_details)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="复制端口号", command=self._copy_port)
        self.context_menu.add_command(label="复制进程ID", command=self._copy_pid)
        
        self.result_tree.bind("<Button-3>", self._show_context_menu)  # 右键
        self.result_tree.bind("<Double-1>", self._show_process_details)  # 双击
    
    def _create_status_bar(self):
        """
        创建状态栏
        """
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="就绪")
        self.status_label.pack(side=tk.LEFT)
        
        # 统计信息
        self.stats_label = ttk.Label(status_frame, text="")
        self.stats_label.pack(side=tk.RIGHT)
    
    def _load_config(self):
        """
        加载配置
        """
        try:
            # 加载远程服务器配置
            self.remote_configs = self.config_manager.load_remote_configs()
            self._update_remote_server_list()
            
            # 加载其他配置
            self.timeout_var.set(self.config_manager.get('default_settings.scan_timeout', 1.0))
            self.threads_var.set(self.config_manager.get('default_settings.thread_count', 50))
            
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
    
    def _update_remote_server_list(self):
        """
        更新远程服务器列表
        """
        server_names = [config.name for config in self.remote_configs]
        self.remote_server['values'] = server_names
        
        if server_names and not self.remote_server.get():
            self.remote_server.set(server_names[0])
    
    def _on_scan_mode_change(self):
        """
        扫描模式改变事件
        """
        is_remote = self.scan_mode.get() == "remote"
        
        if is_remote:
            self.remote_server.config(state="readonly")
        else:
            self.remote_server.config(state="disabled")
    
    def _on_remote_server_change(self, event=None):
        """
        远程服务器选择改变事件
        """
        server_name = self.remote_server.get()
        
        for config in self.remote_configs:
            if config.name == server_name:
                self.current_remote_config = config
                break
    
    def _start_scan(self):
        """
        开始扫描
        """
        if self.is_scanning:
            return
        
        try:
            # 创建扫描配置
            scan_config = self._create_scan_config()
            if not scan_config:
                return
            
            # 验证配置
            is_valid, error_msg = scan_config.validate()
            if not is_valid:
                messagebox.showerror("配置错误", error_msg)
                return
            
            # 更新UI状态
            self.is_scanning = True
            self.scan_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.progress.start()
            
            # 清空结果
            self._clear_results()
            
            # 启动扫描线程
            self.scan_thread = threading.Thread(target=self._scan_worker, args=(scan_config,))
            self.scan_thread.daemon = True
            self.scan_thread.start()
            
            # 更新状态
            target = scan_config.remote_config.host if scan_config.remote_config else "localhost"
            self._update_status(f"正在扫描 {target} 的 {len(scan_config.port_range)} 个端口...")
            
        except Exception as e:
            self.logger.error(f"启动扫描失败: {e}")
            messagebox.showerror("扫描失败", f"启动扫描失败: {e}")
            self._scan_finished()
    
    def _stop_scan(self):
        """
        停止扫描
        """
        if self.is_scanning:
            self.scanner.stop_scan()
            self._update_status("正在停止扫描...")
    
    def _scan_worker(self, scan_config: ScanConfig):
        """
        扫描工作线程
        
        Args:
            scan_config: 扫描配置
        """
        try:
            start_time = time.time()
            result = self.scanner.scan_ports(scan_config)
            end_time = time.time()
            
            # 在主线程中更新UI
            self.root.after(0, self._scan_completed, result, end_time - start_time)
            
        except Exception as e:
            self.logger.error(f"扫描过程中发生错误: {e}")
            self.root.after(0, self._scan_error, str(e))
    
    def _scan_completed(self, result: ScanResult, duration: float):
        """
        扫描完成处理
        
        Args:
            result: 扫描结果
            duration: 扫描耗时
        """
        self.current_result = result
        
        if result.success:
            self._display_results(result)
            
            # 更新统计信息
            target = result.remote_config.host if result.remote_config else "localhost"
            status_text = (f"扫描完成 - {target} | "
                          f"总端口: {result.total_ports} | "
                          f"占用: {result.occupied_ports} | "
                          f"耗时: {duration:.2f}秒")
            self._update_status(status_text)
            
            stats_text = f"占用率: {result.occupation_rate:.1f}%"
            self.stats_label.config(text=stats_text)
            
        else:
            messagebox.showerror("扫描失败", result.error_message)
            self._update_status(f"扫描失败: {result.error_message}")
        
        self._scan_finished()
    
    def _scan_error(self, error_msg: str):
        """
        扫描错误处理
        
        Args:
            error_msg: 错误信息
        """
        messagebox.showerror("扫描错误", f"扫描过程中发生错误: {error_msg}")
        self._update_status(f"扫描错误: {error_msg}")
        self._scan_finished()
    
    def _scan_finished(self):
        """
        扫描结束处理
        """
        self.is_scanning = False
        self.scan_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress.stop()
    
    def _create_scan_config(self) -> Optional[ScanConfig]:
        """
        创建扫描配置
        
        Returns:
            Optional[ScanConfig]: 扫描配置
        """
        try:
            # 解析端口范围
            port_range = self._parse_port_range()
            if not port_range:
                messagebox.showerror("配置错误", "请输入有效的端口范围")
                return None
            
            # 解析协议
            protocols = []
            if self.tcp_var.get():
                protocols.append(Protocol.TCP)
            if self.udp_var.get():
                protocols.append(Protocol.UDP)
            
            if not protocols:
                messagebox.showerror("配置错误", "请至少选择一种协议")
                return None
            
            # 扫描类型和远程配置
            scan_type = ScanType.REMOTE if self.scan_mode.get() == "remote" else ScanType.LOCAL
            remote_config = None
            
            if scan_type == ScanType.REMOTE:
                if not self.current_remote_config:
                    messagebox.showerror("配置错误", "请选择远程服务器")
                    return None
                remote_config = self.current_remote_config
            
            return ScanConfig(
                port_range=port_range,
                scan_type=scan_type,
                timeout=self.timeout_var.get(),
                max_threads=self.threads_var.get(),
                protocols=protocols,
                remote_config=remote_config
            )
            
        except Exception as e:
            self.logger.error(f"创建扫描配置失败: {e}")
            messagebox.showerror("配置错误", f"创建扫描配置失败: {e}")
            return None
    
    def _parse_port_range(self) -> Optional[List[int]]:
        """
        解析端口范围
        
        Returns:
            Optional[List[int]]: 端口列表
        """
        try:
            port_text = self.port_entry.get().strip()
            if not port_text:
                return None
            
            ports = []
            
            # 分割逗号分隔的部分
            parts = [part.strip() for part in port_text.split(',')]
            
            for part in parts:
                if '-' in part:
                    # 处理端口范围
                    start, end = map(int, part.split('-', 1))
                    if start <= end and 1 <= start <= 65535 and 1 <= end <= 65535:
                        ports.extend(range(start, end + 1))
                else:
                    # 处理单个端口
                    port = int(part)
                    if 1 <= port <= 65535:
                        ports.append(port)
            
            return sorted(list(set(ports))) if ports else None
            
        except ValueError:
            return None
    
    def _display_results(self, result: ScanResult):
        """
        显示扫描结果
        
        Args:
            result: 扫描结果
        """
        # 清空现有结果
        self._clear_results()
        
        # 只显示被占用的端口
        occupied_ports = result.get_occupied_ports()
        
        for port_info in occupied_ports:
            values = (
                str(port_info.port),
                port_info.protocol.value,
                port_info.display_status,
                str(port_info.pid) if port_info.pid else 'N/A',
                port_info.process_name or 'Unknown',
                port_info.local_address
            )
            
            # 插入行
            item = self.result_tree.insert('', tk.END, values=values)
            
            # 设置行颜色
            if port_info.is_occupied:
                self.result_tree.set(item, 'status', '占用')
                # 可以设置不同的标签颜色
        
        # 更新信息标签
        if occupied_ports:
            self.info_label.config(text=f"发现 {len(occupied_ports)} 个被占用的端口")
        else:
            self.info_label.config(text="未发现被占用的端口")
    
    def _clear_results(self):
        """
        清空结果
        """
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        self.info_label.config(text="准备就绪")
        self.stats_label.config(text="")
    
    def _refresh_results(self):
        """
        刷新结果
        """
        if not self.is_scanning:
            self._start_scan()
    
    def _update_status(self, message: str):
        """
        更新状态栏
        
        Args:
            message: 状态消息
        """
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def _show_context_menu(self, event):
        """
        显示右键菜单
        
        Args:
            event: 事件对象
        """
        # 选择点击的项目
        item = self.result_tree.identify_row(event.y)
        if item:
            self.result_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _kill_selected_process(self):
        """
        终止选中的进程
        """
        selection = self.result_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.result_tree.item(item, 'values')
        
        if len(values) >= 4:
            port = int(values[0])
            protocol_str = values[1]
            pid_str = values[3]
            
            if pid_str == 'N/A':
                messagebox.showwarning("警告", "无法获取进程ID")
                return
            
            pid = int(pid_str)
            protocol = Protocol.TCP if protocol_str == 'TCP' else Protocol.UDP
            
            # 确认对话框
            if messagebox.askyesno("确认", f"确定要终止占用端口 {port} 的进程 (PID: {pid}) 吗？"):
                try:
                    success, message = self.process_manager.kill_process_by_pid(pid)
                    
                    if success:
                        messagebox.showinfo("成功", message)
                        # 刷新结果
                        self._refresh_results()
                    else:
                        messagebox.showerror("失败", message)
                        
                except Exception as e:
                    messagebox.showerror("错误", f"终止进程失败: {e}")
    
    def _show_process_details(self, event=None):
        """
        显示进程详情
        
        Args:
            event: 事件对象
        """
        selection = self.result_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.result_tree.item(item, 'values')
        
        if len(values) >= 4 and values[3] != 'N/A':
            pid = int(values[3])
            
            try:
                process_info = self.process_manager.get_process_info(pid)
                if process_info:
                    self._show_process_info_dialog(process_info)
                else:
                    messagebox.showwarning("警告", "无法获取进程详细信息")
            except Exception as e:
                messagebox.showerror("错误", f"获取进程信息失败: {e}")
    
    def _show_process_info_dialog(self, process_info: ProcessInfo):
        """
        显示进程信息对话框
        
        Args:
            process_info: 进程信息
        """
        dialog = tk.Toplevel(self.root)
        dialog.title(f"进程详情 - {process_info.name}")
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        
        # 创建信息显示区域
        info_frame = ttk.Frame(dialog, padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        # 进程信息
        info_text = f"""进程ID: {process_info.pid}
进程名称: {process_info.name}
进程状态: {process_info.status}
CPU使用率: {process_info.cpu_percent:.1f}%
内存使用率: {process_info.memory_percent:.1f}%
创建时间: {datetime.fromtimestamp(process_info.create_time).strftime('%Y-%m-%d %H:%M:%S') if process_info.create_time else 'N/A'}

命令行参数:
{' '.join(process_info.cmdline) if process_info.cmdline else 'N/A'}"""
        
        text_widget = tk.Text(info_frame, wrap=tk.WORD, state=tk.NORMAL)
        text_widget.insert(tk.END, info_text)
        text_widget.config(state=tk.DISABLED)
        
        scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="关闭", command=dialog.destroy).pack(side=tk.RIGHT)
    
    def _copy_port(self):
        """
        复制端口号到剪贴板
        """
        selection = self.result_tree.selection()
        if selection:
            item = selection[0]
            values = self.result_tree.item(item, 'values')
            if values:
                self.root.clipboard_clear()
                self.root.clipboard_append(values[0])
                self._update_status(f"已复制端口号: {values[0]}")
    
    def _copy_pid(self):
        """
        复制进程ID到剪贴板
        """
        selection = self.result_tree.selection()
        if selection:
            item = selection[0]
            values = self.result_tree.item(item, 'values')
            if len(values) >= 4 and values[3] != 'N/A':
                self.root.clipboard_clear()
                self.root.clipboard_append(values[3])
                self._update_status(f"已复制进程ID: {values[3]}")
    
    def _export_results(self):
        """
        导出结果
        """
        if not self.current_result:
            messagebox.showwarning("警告", "没有可导出的结果")
            return
        
        filename = filedialog.asksaveasfilename(
            title="导出扫描结果",
            defaultextension=".json",
            filetypes=[
                ("JSON文件", "*.json"),
                ("CSV文件", "*.csv"),
                ("文本文件", "*.txt"),
                ("所有文件", "*.*")
            ]
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    self._export_json(filename)
                elif filename.endswith('.csv'):
                    self._export_csv(filename)
                else:
                    self._export_text(filename)
                
                messagebox.showinfo("成功", f"结果已导出到: {filename}")
                
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}")
    
    def _export_json(self, filename: str):
        """
        导出JSON格式
        
        Args:
            filename: 文件名
        """
        import json
        
        data = {
            'scan_time': self.current_result.scan_time.isoformat(),
            'scan_type': self.current_result.scan_type.value,
            'total_ports': self.current_result.total_ports,
            'occupied_ports': self.current_result.occupied_ports,
            'ports': []
        }
        
        for port_info in self.current_result.port_info_list:
            port_data = {
                'port': port_info.port,
                'protocol': port_info.protocol.value,
                'status': port_info.status.value,
                'is_occupied': port_info.is_occupied,
                'local_address': port_info.local_address,
                'pid': port_info.pid,
                'process_name': port_info.process_name
            }
            data['ports'].append(port_data)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _export_csv(self, filename: str):
        """
        导出CSV格式
        
        Args:
            filename: 文件名
        """
        import csv
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 写入表头
            writer.writerow(['端口', '协议', '状态', '占用', '进程ID', '进程名称', '地址'])
            
            # 写入数据
            for port_info in self.current_result.port_info_list:
                writer.writerow([
                    port_info.port,
                    port_info.protocol.value,
                    port_info.status.value,
                    '是' if port_info.is_occupied else '否',
                    port_info.pid or '',
                    port_info.process_name or '',
                    port_info.local_address
                ])
    
    def _export_text(self, filename: str):
        """
        导出文本格式
        
        Args:
            filename: 文件名
        """
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"扫描结果报告\n")
            f.write(f"扫描时间: {self.current_result.scan_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"扫描类型: {self.current_result.scan_type.value}\n")
            f.write(f"总端口数: {self.current_result.total_ports}\n")
            f.write(f"占用端口: {self.current_result.occupied_ports}\n")
            f.write(f"空闲端口: {self.current_result.free_ports}\n")
            f.write(f"占用率: {self.current_result.occupation_rate:.1f}%\n\n")
            
            occupied_ports = self.current_result.get_occupied_ports()
            if occupied_ports:
                f.write("被占用的端口:\n")
                f.write("-" * 80 + "\n")
                
                for port_info in occupied_ports:
                    f.write(f"端口: {port_info.port}/{port_info.protocol.value}\n")
                    f.write(f"状态: {port_info.display_status}\n")
                    f.write(f"进程: {port_info.process_name or 'Unknown'} (PID: {port_info.pid or 'N/A'})\n")
                    f.write(f"地址: {port_info.local_address}\n")
                    f.write("-" * 40 + "\n")
            else:
                f.write("未发现被占用的端口\n")
    
    def _show_remote_config(self):
        """
        显示远程配置对话框
        """
        dialog = RemoteConfigDialog(self.root, self.remote_configs)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            self.remote_configs = dialog.result
            self.config_manager.save_remote_configs(self.remote_configs)
            self._update_remote_server_list()
    
    def _show_app_settings(self):
        """
        显示应用设置对话框
        """
        messagebox.showinfo("提示", "应用设置功能待实现")
    
    def _show_process_manager(self):
        """
        显示进程管理器
        """
        messagebox.showinfo("提示", "进程管理器功能待实现")
    
    def _show_network_connections(self):
        """
        显示网络连接查看器
        """
        messagebox.showinfo("提示", "网络连接查看器功能待实现")
    
    def _show_help(self):
        """
        显示帮助信息
        """
        help_text = """服务器端口占用检测工具使用说明

1. 扫描模式:
   - 本地扫描: 扫描本机端口
   - 远程扫描: 通过SSH扫描远程服务器端口

2. 端口范围格式:
   - 单个端口: 80
   - 多个端口: 80,443,8080
   - 端口范围: 8000-9000
   - 混合格式: 80,443,8000-8010

3. 操作说明:
   - 双击结果行查看进程详情
   - 右键菜单可终止进程或复制信息
   - 支持导出结果为JSON、CSV或文本格式

4. 远程扫描:
   - 需要配置SSH连接信息
   - 支持密码和密钥认证
   - 确保目标服务器开启SSH服务"""
        
        dialog = tk.Toplevel(self.root)
        dialog.title("使用说明")
        dialog.geometry("600x500")
        dialog.resizable(False, False)
        
        text_widget = tk.Text(dialog, wrap=tk.WORD, padx=10, pady=10)
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)
        
        scrollbar = ttk.Scrollbar(dialog, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="关闭", command=dialog.destroy).pack(side=tk.RIGHT)
    
    def _show_about(self):
        """
        显示关于对话框
        """
        about_text = """服务器端口占用检测工具 v1.0.0

一款功能强大的端口扫描和进程管理工具

主要功能:
• 本地和远程端口扫描
• 进程信息查看和管理
• 支持TCP和UDP协议
• 多种结果导出格式
• 图形化和命令行双模式

开发语言: Python
界面框架: tkinter
核心库: psutil, paramiko

© 2024 端口扫描工具"""
        
        messagebox.showinfo("关于", about_text)
    
    def _on_closing(self):
        """
        窗口关闭事件
        """
        if self.is_scanning:
            if messagebox.askokcancel("确认退出", "正在扫描中，确定要退出吗？"):
                self.scanner.stop_scan()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """
        运行主窗口
        """
        try:
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"GUI运行错误: {e}")
            raise
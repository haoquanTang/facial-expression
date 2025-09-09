#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
远程配置窗口模块

实现远程服务器连接配置的管理界面，支持添加、编辑、删除和测试远程连接。
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from typing import List, Optional

from ..models.data_models import RemoteConfig
from ..core.remote_client import get_remote_client
from ..utils.logger import get_logger


class RemoteConfigDialog:
    """远程配置对话框"""
    
    def __init__(self, parent, remote_configs: List[RemoteConfig]):
        """
        初始化远程配置对话框
        
        Args:
            parent: 父窗口
            remote_configs: 现有的远程配置列表
        """
        self.parent = parent
        self.logger = get_logger()
        self.remote_configs = remote_configs.copy()  # 创建副本
        self.result = None  # 对话框结果
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("远程服务器配置")
        self.dialog.geometry("700x500")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self._center_window()
        
        # 初始化界面
        self._init_ui()
        
        # 加载配置列表
        self._load_config_list()
    
    def _center_window(self):
        """
        窗口居中显示
        """
        self.dialog.update_idletasks()
        
        # 获取窗口尺寸
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        
        # 获取屏幕尺寸
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        
        # 计算居中位置
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def _init_ui(self):
        """
        初始化用户界面
        """
        # 主框架
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧配置列表
        self._create_config_list(main_frame)
        
        # 右侧配置编辑
        self._create_config_editor(main_frame)
        
        # 底部按钮
        self._create_buttons(main_frame)
    
    def _create_config_list(self, parent):
        """
        创建配置列表
        
        Args:
            parent: 父容器
        """
        # 左侧框架
        left_frame = ttk.Frame(parent)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 配置列表标题
        ttk.Label(left_frame, text="远程服务器列表", font=('', 12, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
        # 列表框架
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Treeview
        columns = ('name', 'host', 'user')
        self.config_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)
        
        # 设置列标题和宽度
        self.config_tree.heading('name', text='名称')
        self.config_tree.heading('host', text='主机')
        self.config_tree.heading('user', text='用户')
        
        self.config_tree.column('name', width=120, anchor=tk.W)
        self.config_tree.column('host', width=120, anchor=tk.W)
        self.config_tree.column('user', width=80, anchor=tk.W)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.config_tree.yview)
        self.config_tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.config_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.config_tree.bind('<<TreeviewSelect>>', self._on_config_select)
        
        # 列表操作按钮
        list_button_frame = ttk.Frame(left_frame)
        list_button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(list_button_frame, text="新建", command=self._new_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(list_button_frame, text="删除", command=self._delete_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(list_button_frame, text="复制", command=self._copy_config).pack(side=tk.LEFT, padx=5)
    
    def _create_config_editor(self, parent):
        """
        创建配置编辑器
        
        Args:
            parent: 父容器
        """
        # 右侧框架
        right_frame = ttk.Frame(parent)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 编辑器标题
        ttk.Label(right_frame, text="连接配置", font=('', 12, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        # 配置表单
        form_frame = ttk.Frame(right_frame)
        form_frame.pack(fill=tk.X)
        
        # 配置名称
        ttk.Label(form_frame, text="配置名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(form_frame, textvariable=self.name_var, width=30)
        self.name_entry.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 主机地址
        ttk.Label(form_frame, text="主机地址:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.host_var = tk.StringVar()
        self.host_entry = ttk.Entry(form_frame, textvariable=self.host_var, width=30)
        self.host_entry.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # SSH端口
        ttk.Label(form_frame, text="SSH端口:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.port_var = tk.IntVar(value=22)
        self.port_spin = ttk.Spinbox(form_frame, from_=1, to=65535, textvariable=self.port_var, width=28)
        self.port_spin.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 用户名
        ttk.Label(form_frame, text="用户名:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(form_frame, textvariable=self.username_var, width=30)
        self.username_entry.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 认证方式
        ttk.Label(form_frame, text="认证方式:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.auth_method = tk.StringVar(value="password")
        auth_frame = ttk.Frame(form_frame)
        auth_frame.grid(row=4, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        ttk.Radiobutton(auth_frame, text="密码", variable=self.auth_method, value="password", 
                       command=self._on_auth_method_change).pack(side=tk.LEFT)
        ttk.Radiobutton(auth_frame, text="密钥", variable=self.auth_method, value="key", 
                       command=self._on_auth_method_change).pack(side=tk.LEFT, padx=(20, 0))
        
        # 密码
        ttk.Label(form_frame, text="密码:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(form_frame, textvariable=self.password_var, show="*", width=30)
        self.password_entry.grid(row=5, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 私钥文件
        ttk.Label(form_frame, text="私钥文件:").grid(row=6, column=0, sticky=tk.W, pady=5)
        key_frame = ttk.Frame(form_frame)
        key_frame.grid(row=6, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        self.key_var = tk.StringVar()
        self.key_entry = ttk.Entry(key_frame, textvariable=self.key_var, width=25, state=tk.DISABLED)
        self.key_entry.pack(side=tk.LEFT)
        
        self.key_button = ttk.Button(key_frame, text="浏览", command=self._browse_key_file, state=tk.DISABLED)
        self.key_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # 连接超时
        ttk.Label(form_frame, text="连接超时(秒):").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.timeout_var = tk.IntVar(value=10)
        self.timeout_spin = ttk.Spinbox(form_frame, from_=1, to=60, textvariable=self.timeout_var, width=28)
        self.timeout_spin.grid(row=7, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 操作按钮
        action_frame = ttk.Frame(right_frame)
        action_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.test_button = ttk.Button(action_frame, text="测试连接", command=self._test_connection)
        self.test_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.save_button = ttk.Button(action_frame, text="保存配置", command=self._save_config)
        self.save_button.pack(side=tk.LEFT)
        
        # 测试结果显示
        self.test_result_label = ttk.Label(right_frame, text="", foreground="blue")
        self.test_result_label.pack(anchor=tk.W, pady=(10, 0))
        
        # 初始状态
        self._on_auth_method_change()
        self._clear_form()
    
    def _create_buttons(self, parent):
        """
        创建底部按钮
        
        Args:
            parent: 父容器
        """
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(button_frame, text="确定", command=self._ok_clicked).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="取消", command=self._cancel_clicked).pack(side=tk.RIGHT)
    
    def _load_config_list(self):
        """
        加载配置列表
        """
        # 清空现有项目
        for item in self.config_tree.get_children():
            self.config_tree.delete(item)
        
        # 添加配置项目
        for i, config in enumerate(self.remote_configs):
            values = (config.name, config.host, config.username)
            item = self.config_tree.insert('', tk.END, values=values, tags=(str(i),))
    
    def _on_config_select(self, event=None):
        """
        配置选择事件
        
        Args:
            event: 事件对象
        """
        selection = self.config_tree.selection()
        if not selection:
            return
        
        # 获取选中的配置
        item = selection[0]
        tags = self.config_tree.item(item, 'tags')
        
        if tags:
            index = int(tags[0])
            if 0 <= index < len(self.remote_configs):
                config = self.remote_configs[index]
                self._load_config_to_form(config)
    
    def _load_config_to_form(self, config: RemoteConfig):
        """
        将配置加载到表单
        
        Args:
            config: 远程配置
        """
        self.name_var.set(config.name)
        self.host_var.set(config.host)
        self.port_var.set(config.port)
        self.username_var.set(config.username)
        self.timeout_var.set(config.timeout)
        
        # 设置认证方式
        if config.has_key_auth:
            self.auth_method.set("key")
            self.key_var.set(config.private_key_path)
            self.password_var.set("")
        else:
            self.auth_method.set("password")
            self.password_var.set(config.password)
            self.key_var.set("")
        
        self._on_auth_method_change()
        
        # 清空测试结果
        self.test_result_label.config(text="")
    
    def _clear_form(self):
        """
        清空表单
        """
        self.name_var.set("")
        self.host_var.set("")
        self.port_var.set(22)
        self.username_var.set("")
        self.password_var.set("")
        self.key_var.set("")
        self.timeout_var.set(10)
        self.auth_method.set("password")
        self._on_auth_method_change()
        self.test_result_label.config(text="")
    
    def _on_auth_method_change(self):
        """
        认证方式改变事件
        """
        is_key_auth = self.auth_method.get() == "key"
        
        if is_key_auth:
            self.password_entry.config(state=tk.DISABLED)
            self.key_entry.config(state=tk.NORMAL)
            self.key_button.config(state=tk.NORMAL)
        else:
            self.password_entry.config(state=tk.NORMAL)
            self.key_entry.config(state=tk.DISABLED)
            self.key_button.config(state=tk.DISABLED)
    
    def _browse_key_file(self):
        """
        浏览私钥文件
        """
        filename = filedialog.askopenfilename(
            title="选择私钥文件",
            filetypes=[
                ("私钥文件", "*.pem *.key *.rsa"),
                ("所有文件", "*.*")
            ]
        )
        
        if filename:
            self.key_var.set(filename)
    
    def _new_config(self):
        """
        新建配置
        """
        # 清空表单
        self._clear_form()
        
        # 清除选择
        self.config_tree.selection_remove(self.config_tree.selection())
        
        # 设置默认名称
        self.name_var.set(f"服务器{len(self.remote_configs) + 1}")
    
    def _delete_config(self):
        """
        删除配置
        """
        selection = self.config_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的配置")
            return
        
        if messagebox.askyesno("确认删除", "确定要删除选中的配置吗？"):
            # 获取选中的配置索引
            item = selection[0]
            tags = self.config_tree.item(item, 'tags')
            
            if tags:
                index = int(tags[0])
                if 0 <= index < len(self.remote_configs):
                    # 删除配置
                    del self.remote_configs[index]
                    
                    # 重新加载列表
                    self._load_config_list()
                    
                    # 清空表单
                    self._clear_form()
    
    def _copy_config(self):
        """
        复制配置
        """
        selection = self.config_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要复制的配置")
            return
        
        # 获取选中的配置
        item = selection[0]
        tags = self.config_tree.item(item, 'tags')
        
        if tags:
            index = int(tags[0])
            if 0 <= index < len(self.remote_configs):
                original_config = self.remote_configs[index]
                
                # 创建副本
                new_config = RemoteConfig(
                    host=original_config.host,
                    username=original_config.username,
                    password=original_config.password,
                    private_key_path=original_config.private_key_path,
                    port=original_config.port,
                    timeout=original_config.timeout,
                    name=f"{original_config.name}_副本"
                )
                
                # 添加到列表
                self.remote_configs.append(new_config)
                
                # 重新加载列表
                self._load_config_list()
                
                # 选择新创建的配置
                items = self.config_tree.get_children()
                if items:
                    last_item = items[-1]
                    self.config_tree.selection_set(last_item)
                    self._on_config_select()
    
    def _test_connection(self):
        """
        测试连接
        """
        # 验证表单
        config = self._get_config_from_form()
        if not config:
            return
        
        # 禁用测试按钮
        self.test_button.config(state=tk.DISABLED)
        self.test_result_label.config(text="正在测试连接...", foreground="blue")
        
        # 在后台线程中测试连接
        test_thread = threading.Thread(target=self._test_connection_worker, args=(config,))
        test_thread.daemon = True
        test_thread.start()
    
    def _test_connection_worker(self, config: RemoteConfig):
        """
        测试连接工作线程
        
        Args:
            config: 远程配置
        """
        try:
            client = get_remote_client(config)
            success, message = client.test_connection()
            
            # 在主线程中更新UI
            self.dialog.after(0, self._test_connection_completed, success, message)
            
        except Exception as e:
            self.dialog.after(0, self._test_connection_completed, False, str(e))
    
    def _test_connection_completed(self, success: bool, message: str):
        """
        测试连接完成
        
        Args:
            success: 是否成功
            message: 结果消息
        """
        # 恢复测试按钮
        self.test_button.config(state=tk.NORMAL)
        
        # 显示结果
        if success:
            self.test_result_label.config(text=f"✓ {message}", foreground="green")
        else:
            self.test_result_label.config(text=f"✗ {message}", foreground="red")
    
    def _save_config(self):
        """
        保存配置
        """
        # 获取表单数据
        config = self._get_config_from_form()
        if not config:
            return
        
        # 检查是否是编辑现有配置
        selection = self.config_tree.selection()
        
        if selection:
            # 编辑现有配置
            item = selection[0]
            tags = self.config_tree.item(item, 'tags')
            
            if tags:
                index = int(tags[0])
                if 0 <= index < len(self.remote_configs):
                    self.remote_configs[index] = config
        else:
            # 新建配置
            self.remote_configs.append(config)
        
        # 重新加载列表
        self._load_config_list()
        
        # 显示保存成功消息
        self.test_result_label.config(text="✓ 配置已保存", foreground="green")
        
        # 选择刚保存的配置
        items = self.config_tree.get_children()
        if items:
            if selection:
                # 编辑模式，保持选择
                pass
            else:
                # 新建模式，选择最后一个
                last_item = items[-1]
                self.config_tree.selection_set(last_item)
    
    def _get_config_from_form(self) -> Optional[RemoteConfig]:
        """
        从表单获取配置
        
        Returns:
            Optional[RemoteConfig]: 远程配置
        """
        # 验证必填字段
        name = self.name_var.get().strip()
        host = self.host_var.get().strip()
        username = self.username_var.get().strip()
        
        if not name:
            messagebox.showerror("错误", "请输入配置名称")
            return None
        
        if not host:
            messagebox.showerror("错误", "请输入主机地址")
            return None
        
        if not username:
            messagebox.showerror("错误", "请输入用户名")
            return None
        
        # 验证认证信息
        password = self.password_var.get()
        key_path = self.key_var.get().strip()
        
        if self.auth_method.get() == "password":
            if not password:
                messagebox.showerror("错误", "请输入密码")
                return None
            key_path = ""
        else:
            if not key_path:
                messagebox.showerror("错误", "请选择私钥文件")
                return None
            password = ""
        
        # 验证端口
        try:
            port = self.port_var.get()
            if not (1 <= port <= 65535):
                raise ValueError()
        except ValueError:
            messagebox.showerror("错误", "请输入有效的端口号 (1-65535)")
            return None
        
        # 验证超时时间
        try:
            timeout = self.timeout_var.get()
            if timeout <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("错误", "请输入有效的超时时间")
            return None
        
        try:
            return RemoteConfig(
                name=name,
                host=host,
                username=username,
                password=password,
                private_key_path=key_path,
                port=port,
                timeout=timeout
            )
        except Exception as e:
            messagebox.showerror("错误", f"创建配置失败: {e}")
            return None
    
    def _ok_clicked(self):
        """
        确定按钮点击事件
        """
        self.result = self.remote_configs
        self.dialog.destroy()
    
    def _cancel_clicked(self):
        """
        取消按钮点击事件
        """
        self.result = None
        self.dialog.destroy()


class RemoteConfigEditor:
    """远程配置编辑器（独立窗口）"""
    
    def __init__(self, parent=None, config: Optional[RemoteConfig] = None):
        """
        初始化远程配置编辑器
        
        Args:
            parent: 父窗口
            config: 要编辑的配置，None表示新建
        """
        self.parent = parent
        self.config = config
        self.result = None
        
        # 创建窗口
        if parent:
            self.window = tk.Toplevel(parent)
            self.window.transient(parent)
            self.window.grab_set()
        else:
            self.window = tk.Tk()
        
        self.window.title("编辑远程配置" if config else "新建远程配置")
        self.window.geometry("400x350")
        self.window.resizable(False, False)
        
        # 初始化界面
        self._init_ui()
        
        # 加载配置
        if config:
            self._load_config()
    
    def _init_ui(self):
        """
        初始化用户界面
        """
        # 主框架
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 表单
        # 配置名称
        ttk.Label(main_frame, text="配置名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.name_var, width=30).grid(row=0, column=1, padx=(10, 0), pady=5)
        
        # 主机地址
        ttk.Label(main_frame, text="主机地址:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.host_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.host_var, width=30).grid(row=1, column=1, padx=(10, 0), pady=5)
        
        # SSH端口
        ttk.Label(main_frame, text="SSH端口:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.port_var = tk.IntVar(value=22)
        ttk.Spinbox(main_frame, from_=1, to=65535, textvariable=self.port_var, width=28).grid(row=2, column=1, padx=(10, 0), pady=5)
        
        # 用户名
        ttk.Label(main_frame, text="用户名:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.username_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.username_var, width=30).grid(row=3, column=1, padx=(10, 0), pady=5)
        
        # 密码
        ttk.Label(main_frame, text="密码:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.password_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.password_var, show="*", width=30).grid(row=4, column=1, padx=(10, 0), pady=5)
        
        # 连接超时
        ttk.Label(main_frame, text="连接超时(秒):").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.timeout_var = tk.IntVar(value=10)
        ttk.Spinbox(main_frame, from_=1, to=60, textvariable=self.timeout_var, width=28).grid(row=5, column=1, padx=(10, 0), pady=5)
        
        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=(20, 0))
        
        ttk.Button(button_frame, text="确定", command=self._ok_clicked).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="取消", command=self._cancel_clicked).pack(side=tk.RIGHT)
    
    def _load_config(self):
        """
        加载配置到表单
        """
        if self.config:
            self.name_var.set(self.config.name)
            self.host_var.set(self.config.host)
            self.port_var.set(self.config.port)
            self.username_var.set(self.config.username)
            self.password_var.set(self.config.password)
            self.timeout_var.set(self.config.timeout)
    
    def _ok_clicked(self):
        """
        确定按钮点击事件
        """
        # 验证表单
        name = self.name_var.get().strip()
        host = self.host_var.get().strip()
        username = self.username_var.get().strip()
        password = self.password_var.get()
        
        if not all([name, host, username, password]):
            messagebox.showerror("错误", "请填写所有必填字段")
            return
        
        try:
            self.result = RemoteConfig(
                name=name,
                host=host,
                username=username,
                password=password,
                port=self.port_var.get(),
                timeout=self.timeout_var.get()
            )
            
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("错误", f"创建配置失败: {e}")
    
    def _cancel_clicked(self):
        """
        取消按钮点击事件
        """
        self.result = None
        self.window.destroy()
    
    def show(self) -> Optional[RemoteConfig]:
        """
        显示对话框并返回结果
        
        Returns:
            Optional[RemoteConfig]: 配置结果
        """
        if self.parent:
            self.parent.wait_window(self.window)
        else:
            self.window.mainloop()
        
        return self.result
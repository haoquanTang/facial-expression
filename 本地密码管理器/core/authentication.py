#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
身份验证服务模块

提供主密码验证和登录状态管理功能
"""

import time
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any
from threading import Timer

from data.repository import DataRepository
from security.validator import DataValidator
from utils.logger import log_security_event, log_user_action
from config.constants import MAX_LOGIN_ATTEMPTS, DEFAULT_AUTO_LOCK_TIMEOUT


class AuthenticationService:
    """
    身份验证服务类
    
    负责主密码验证、登录状态管理和安全控制
    """
    
    def __init__(self, repository: DataRepository):
        """
        初始化身份验证服务
        
        Args:
            repository (DataRepository): 数据仓库实例
        """
        self.repository = repository
        self.validator = DataValidator()
        
        # 登录状态
        self._is_authenticated = False
        self._login_time: Optional[datetime] = None
        self._last_activity_time: Optional[datetime] = None
        
        # 安全控制
        self._failed_attempts = 0
        self._lockout_until: Optional[datetime] = None
        self._auto_lock_timer: Optional[Timer] = None
        self._auto_lock_timeout = DEFAULT_AUTO_LOCK_TIMEOUT
        
        # 回调函数
        self._on_logout_callback: Optional[Callable] = None
        self._on_auto_lock_callback: Optional[Callable] = None
    
    def is_database_exists(self) -> bool:
        """
        检查数据库是否存在
        
        Returns:
            bool: 数据库是否存在
        """
        return self.repository.is_database_exists()
    
    def is_locked_out(self) -> bool:
        """
        检查是否被锁定
        
        Returns:
            bool: 是否被锁定
        """
        if self._lockout_until is None:
            return False
        
        if datetime.now() >= self._lockout_until:
            # 锁定时间已过，清除锁定状态
            self._lockout_until = None
            self._failed_attempts = 0
            return False
        
        return True
    
    def get_lockout_remaining_time(self) -> Optional[int]:
        """
        获取剩余锁定时间
        
        Returns:
            Optional[int]: 剩余锁定时间（秒），如果未被锁定返回None
        """
        if not self.is_locked_out():
            return None
        
        remaining = self._lockout_until - datetime.now()
        return max(0, int(remaining.total_seconds()))
    
    def create_master_password(self, password: str) -> Dict[str, Any]:
        """
        创建主密码（首次设置）
        
        Args:
            password (str): 主密码
            
        Returns:
            Dict[str, Any]: 创建结果
        """
        # 验证主密码强度
        validation_result = self.validator.validate_master_password(password)
        
        if not validation_result['is_valid']:
            return {
                'success': False,
                'message': '主密码不符合要求',
                'errors': validation_result['errors'],
                'warnings': validation_result.get('warnings', [])
            }
        
        # 初始化数据库
        success = self.repository.initialize_new_database(password)
        
        if success:
            log_security_event("主密码创建", "用户创建了新的主密码")
            return {
                'success': True,
                'message': '主密码创建成功',
                'warnings': validation_result.get('warnings', [])
            }
        else:
            log_security_event("主密码创建失败", "数据库初始化失败")
            return {
                'success': False,
                'message': '主密码创建失败，请重试'
            }
    
    def authenticate(self, password: str) -> Dict[str, Any]:
        """
        验证主密码并登录
        
        Args:
            password (str): 主密码
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        # 检查是否被锁定
        if self.is_locked_out():
            remaining_time = self.get_lockout_remaining_time()
            log_security_event("登录尝试被拒绝", f"账户被锁定，剩余时间: {remaining_time}秒")
            return {
                'success': False,
                'message': f'账户已被锁定，请等待 {remaining_time} 秒后重试',
                'locked_out': True,
                'remaining_time': remaining_time
            }
        
        # 验证密码格式
        if not password:
            return {
                'success': False,
                'message': '请输入主密码'
            }
        
        # 尝试加载数据库
        success = self.repository.load_database(password)
        
        if success:
            # 登录成功
            self._is_authenticated = True
            self._login_time = datetime.now()
            self._last_activity_time = datetime.now()
            self._failed_attempts = 0
            self._lockout_until = None
            
            # 启动自动锁定定时器
            self._start_auto_lock_timer()
            
            log_user_action("用户登录", "主密码验证成功")
            
            return {
                'success': True,
                'message': '登录成功'
            }
        else:
            # 登录失败
            self._failed_attempts += 1
            
            log_security_event("登录失败", f"主密码验证失败，失败次数: {self._failed_attempts}")
            
            # 检查是否需要锁定账户
            if self._failed_attempts >= MAX_LOGIN_ATTEMPTS:
                # 锁定账户5分钟
                lockout_duration = 5 * 60  # 5分钟
                self._lockout_until = datetime.now() + timedelta(seconds=lockout_duration)
                
                log_security_event("账户锁定", f"连续失败{MAX_LOGIN_ATTEMPTS}次，锁定5分钟")
                
                return {
                    'success': False,
                    'message': f'密码错误次数过多，账户已被锁定 {lockout_duration // 60} 分钟',
                    'locked_out': True,
                    'remaining_time': lockout_duration
                }
            else:
                remaining_attempts = MAX_LOGIN_ATTEMPTS - self._failed_attempts
                return {
                    'success': False,
                    'message': f'主密码错误，还有 {remaining_attempts} 次尝试机会',
                    'remaining_attempts': remaining_attempts
                }
    
    def logout(self):
        """
        注销登录
        """
        if self._is_authenticated:
            log_user_action("用户注销", "用户主动注销")
        
        self._is_authenticated = False
        self._login_time = None
        self._last_activity_time = None
        
        # 停止自动锁定定时器
        self._stop_auto_lock_timer()
        
        # 执行注销回调
        if self._on_logout_callback:
            try:
                self._on_logout_callback()
            except Exception as e:
                print(f"注销回调执行失败: {e}")
    
    def is_authenticated(self) -> bool:
        """
        检查是否已认证
        
        Returns:
            bool: 是否已认证
        """
        return self._is_authenticated and self.repository.is_loaded()
    
    def update_activity(self):
        """
        更新最后活动时间
        """
        if self._is_authenticated:
            self._last_activity_time = datetime.now()
            
            # 重启自动锁定定时器
            self._start_auto_lock_timer()
    
    def get_session_info(self) -> Dict[str, Any]:
        """
        获取会话信息
        
        Returns:
            Dict[str, Any]: 会话信息
        """
        if not self._is_authenticated:
            return {
                'authenticated': False
            }
        
        session_duration = None
        if self._login_time:
            session_duration = int((datetime.now() - self._login_time).total_seconds())
        
        last_activity = None
        if self._last_activity_time:
            last_activity = int((datetime.now() - self._last_activity_time).total_seconds())
        
        return {
            'authenticated': True,
            'login_time': self._login_time,
            'session_duration': session_duration,
            'last_activity': last_activity,
            'auto_lock_timeout': self._auto_lock_timeout
        }
    
    def change_master_password(self, old_password: str, new_password: str) -> Dict[str, Any]:
        """
        修改主密码
        
        Args:
            old_password (str): 旧密码
            new_password (str): 新密码
            
        Returns:
            Dict[str, Any]: 修改结果
        """
        if not self._is_authenticated:
            return {
                'success': False,
                'message': '请先登录'
            }
        
        # 验证新密码强度
        validation_result = self.validator.validate_master_password(new_password)
        
        if not validation_result['is_valid']:
            return {
                'success': False,
                'message': '新密码不符合要求',
                'errors': validation_result['errors'],
                'warnings': validation_result.get('warnings', [])
            }
        
        # 修改密码
        success = self.repository.change_master_password(old_password, new_password)
        
        if success:
            log_security_event("主密码修改", "用户成功修改主密码")
            return {
                'success': True,
                'message': '主密码修改成功',
                'warnings': validation_result.get('warnings', [])
            }
        else:
            log_security_event("主密码修改失败", "旧密码验证失败或系统错误")
            return {
                'success': False,
                'message': '主密码修改失败，请检查旧密码是否正确'
            }
    
    def set_auto_lock_timeout(self, timeout_seconds: int):
        """
        设置自动锁定超时时间
        
        Args:
            timeout_seconds (int): 超时时间（秒）
        """
        if timeout_seconds > 0:
            self._auto_lock_timeout = timeout_seconds
            
            # 重启定时器
            if self._is_authenticated:
                self._start_auto_lock_timer()
    
    def set_logout_callback(self, callback: Callable):
        """
        设置注销回调函数
        
        Args:
            callback (Callable): 回调函数
        """
        self._on_logout_callback = callback
    
    def set_auto_lock_callback(self, callback: Callable):
        """
        设置自动锁定回调函数
        
        Args:
            callback (Callable): 回调函数
        """
        self._on_auto_lock_callback = callback
    
    def _start_auto_lock_timer(self):
        """
        启动自动锁定定时器
        """
        # 停止现有定时器
        self._stop_auto_lock_timer()
        
        if self._auto_lock_timeout > 0:
            self._auto_lock_timer = Timer(
                self._auto_lock_timeout,
                self._auto_lock
            )
            self._auto_lock_timer.start()
    
    def _stop_auto_lock_timer(self):
        """
        停止自动锁定定时器
        """
        if self._auto_lock_timer and self._auto_lock_timer.is_alive():
            self._auto_lock_timer.cancel()
            self._auto_lock_timer = None
    
    def _auto_lock(self):
        """
        自动锁定（内部方法）
        """
        if self._is_authenticated:
            log_security_event("自动锁定", f"超时{self._auto_lock_timeout}秒未活动")
            
            # 执行自动锁定回调
            if self._on_auto_lock_callback:
                try:
                    self._on_auto_lock_callback()
                except Exception as e:
                    print(f"自动锁定回调执行失败: {e}")
            
            # 注销登录
            self.logout()
    
    def get_failed_attempts(self) -> int:
        """
        获取失败尝试次数
        
        Returns:
            int: 失败尝试次数
        """
        return self._failed_attempts
    
    def reset_failed_attempts(self):
        """
        重置失败尝试次数（管理员功能）
        """
        self._failed_attempts = 0
        self._lockout_until = None
        log_security_event("重置失败次数", "管理员重置了失败尝试次数")
    
    def __del__(self):
        """
        析构函数，确保清理定时器
        """
        self._stop_auto_lock_timer()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
密码管理核心模块

提供密码管理的核心业务逻辑
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Callable

from core.models import PasswordEntry, AppSettings
from data.repository import DataRepository
from security.password_generator import PasswordGenerator
from security.validator import DataValidator
from utils.clipboard import copy_password_safely
from utils.logger import log_user_action, log_security_event
from config.constants import DEFAULT_CLIPBOARD_TIMEOUT


class PasswordManager:
    """
    密码管理器核心类
    
    提供密码管理的所有核心功能
    """
    
    def __init__(self, repository: DataRepository):
        """
        初始化密码管理器
        
        Args:
            repository (DataRepository): 数据仓库实例
        """
        self.repository = repository
        self.password_generator = PasswordGenerator()
        self.validator = DataValidator()
        
        # 回调函数
        self._on_entry_added: Optional[Callable] = None
        self._on_entry_updated: Optional[Callable] = None
        self._on_entry_deleted: Optional[Callable] = None
        self._on_password_copied: Optional[Callable] = None
    
    def add_password_entry(self, platform: str, username: str, 
                          password: str, notes: str = "") -> Dict[str, Any]:
        """
        添加密码条目
        
        Args:
            platform (str): 平台名称
            username (str): 用户名
            password (str): 密码
            notes (str): 备注信息
            
        Returns:
            Dict[str, Any]: 添加结果
        """
        # 验证输入数据
        validation_result = self.validator.validate_password_entry(
            platform, username, password, notes
        )
        
        if not validation_result['is_valid']:
            return {
                'success': False,
                'message': '输入数据验证失败',
                'errors': validation_result['errors']
            }
        
        # 清理输入数据
        platform = self.validator.sanitize_input(platform)
        username = self.validator.sanitize_input(username)
        notes = self.validator.sanitize_input(notes)
        
        # 添加到数据库
        success = self.repository.add_password_entry(platform, username, password, notes)
        
        if success:
            log_user_action("添加密码条目", f"平台: {platform}, 用户名: {username}")
            
            # 执行回调
            if self._on_entry_added:
                try:
                    self._on_entry_added(platform, username)
                except Exception as e:
                    print(f"添加条目回调执行失败: {e}")
            
            return {
                'success': True,
                'message': '密码条目添加成功'
            }
        else:
            return {
                'success': False,
                'message': '密码条目添加失败，可能已存在相同的平台和用户名组合'
            }
    
    def get_password_entries(self, search_term: str = "") -> List[PasswordEntry]:
        """
        获取密码条目列表
        
        Args:
            search_term (str): 搜索关键词
            
        Returns:
            List[PasswordEntry]: 密码条目列表
        """
        entries = self.repository.get_password_entries(search_term)
        
        if search_term:
            log_user_action("搜索密码条目", f"关键词: {search_term}, 结果数量: {len(entries)}")
        
        return entries
    
    def get_password_entry_by_id(self, entry_id: str) -> Optional[PasswordEntry]:
        """
        根据ID获取密码条目
        
        Args:
            entry_id (str): 条目ID
            
        Returns:
            Optional[PasswordEntry]: 密码条目
        """
        return self.repository.get_password_entry_by_id(entry_id)
    
    def update_password_entry(self, entry_id: str, platform: str, 
                            username: str, password: str, notes: str = "") -> Dict[str, Any]:
        """
        更新密码条目
        
        Args:
            entry_id (str): 条目ID
            platform (str): 平台名称
            username (str): 用户名
            password (str): 密码
            notes (str): 备注信息
            
        Returns:
            Dict[str, Any]: 更新结果
        """
        # 验证输入数据
        validation_result = self.validator.validate_password_entry(
            platform, username, password, notes
        )
        
        if not validation_result['is_valid']:
            return {
                'success': False,
                'message': '输入数据验证失败',
                'errors': validation_result['errors']
            }
        
        # 清理输入数据
        platform = self.validator.sanitize_input(platform)
        username = self.validator.sanitize_input(username)
        notes = self.validator.sanitize_input(notes)
        
        # 更新数据库
        success = self.repository.update_password_entry(
            entry_id, platform, username, password, notes
        )
        
        if success:
            log_user_action("更新密码条目", f"ID: {entry_id}, 平台: {platform}")
            
            # 执行回调
            if self._on_entry_updated:
                try:
                    self._on_entry_updated(entry_id, platform, username)
                except Exception as e:
                    print(f"更新条目回调执行失败: {e}")
            
            return {
                'success': True,
                'message': '密码条目更新成功'
            }
        else:
            return {
                'success': False,
                'message': '密码条目更新失败，条目不存在'
            }
    
    def delete_password_entry(self, entry_id: str) -> Dict[str, Any]:
        """
        删除密码条目
        
        Args:
            entry_id (str): 条目ID
            
        Returns:
            Dict[str, Any]: 删除结果
        """
        # 获取条目信息用于日志
        entry = self.repository.get_password_entry_by_id(entry_id)
        
        # 删除条目
        success = self.repository.delete_password_entry(entry_id)
        
        if success:
            platform_name = entry.platform if entry else "未知"
            log_user_action("删除密码条目", f"ID: {entry_id}, 平台: {platform_name}")
            
            # 执行回调
            if self._on_entry_deleted:
                try:
                    self._on_entry_deleted(entry_id, platform_name)
                except Exception as e:
                    print(f"删除条目回调执行失败: {e}")
            
            return {
                'success': True,
                'message': '密码条目删除成功'
            }
        else:
            return {
                'success': False,
                'message': '密码条目删除失败，条目不存在'
            }
    
    def copy_password_to_clipboard(self, entry_id: str, 
                                 clear_seconds: Optional[int] = None) -> Dict[str, Any]:
        """
        复制密码到剪贴板
        
        Args:
            entry_id (str): 条目ID
            clear_seconds (Optional[int]): 自动清空时间（秒）
            
        Returns:
            Dict[str, Any]: 复制结果
        """
        # 获取密码条目
        entry = self.repository.get_password_entry_by_id(entry_id)
        if not entry:
            return {
                'success': False,
                'message': '密码条目不存在'
            }
        
        # 解密密码
        password = self.repository.decrypt_password(entry)
        if not password:
            return {
                'success': False,
                'message': '密码解密失败'
            }
        
        # 获取清空时间
        if clear_seconds is None:
            settings = self.repository.get_app_settings()
            if settings and hasattr(settings, 'clipboard_timeout'):
                clear_seconds = getattr(settings, 'clipboard_timeout', DEFAULT_CLIPBOARD_TIMEOUT)
            else:
                clear_seconds = DEFAULT_CLIPBOARD_TIMEOUT
        
        # 复制到剪贴板
        def on_clipboard_cleared():
            if self._on_password_copied:
                try:
                    self._on_password_copied(entry.platform, True)  # True表示已清空
                except Exception as e:
                    print(f"密码复制回调执行失败: {e}")
        
        success = copy_password_safely(password, clear_seconds, on_clipboard_cleared)
        
        if success:
            log_user_action("复制密码", f"平台: {entry.platform}, 自动清空: {clear_seconds}秒")
            
            # 执行回调
            if self._on_password_copied:
                try:
                    self._on_password_copied(entry.platform, False)  # False表示刚复制
                except Exception as e:
                    print(f"密码复制回调执行失败: {e}")
            
            return {
                'success': True,
                'message': f'密码已复制到剪贴板，{clear_seconds}秒后自动清空',
                'clear_seconds': clear_seconds
            }
        else:
            return {
                'success': False,
                'message': '复制到剪贴板失败，剪贴板功能不可用'
            }
    
    def generate_password(self, length: int = 12, include_lowercase: bool = True,
                         include_uppercase: bool = True, include_digits: bool = True,
                         include_symbols: bool = True) -> Dict[str, Any]:
        """
        生成强密码
        
        Args:
            length (int): 密码长度
            include_lowercase (bool): 是否包含小写字母
            include_uppercase (bool): 是否包含大写字母
            include_digits (bool): 是否包含数字
            include_symbols (bool): 是否包含符号
            
        Returns:
            Dict[str, Any]: 生成结果
        """
        try:
            password = self.password_generator.generate_password(
                length=length,
                include_lowercase=include_lowercase,
                include_uppercase=include_uppercase,
                include_digits=include_digits,
                include_symbols=include_symbols
            )
            
            # 计算密码强度
            strength = self.password_generator.calculate_strength(password)
            
            log_user_action("生成密码", f"长度: {length}, 强度: {strength['level']}")
            
            return {
                'success': True,
                'password': password,
                'strength': strength
            }
            
        except ValueError as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    def calculate_password_strength(self, password: str) -> Dict[str, Any]:
        """
        计算密码强度
        
        Args:
            password (str): 密码
            
        Returns:
            Dict[str, Any]: 强度信息
        """
        return self.password_generator.calculate_strength(password)
    
    def get_expired_entries(self) -> List[PasswordEntry]:
        """
        获取已过期的密码条目
        
        Returns:
            List[PasswordEntry]: 已过期的条目列表
        """
        expired_entries = self.repository.get_expired_entries()
        
        if expired_entries:
            log_security_event("密码过期检查", f"发现{len(expired_entries)}个过期密码")
        
        return expired_entries
    
    def get_expiring_soon_entries(self, days: int = 7) -> List[PasswordEntry]:
        """
        获取即将过期的密码条目
        
        Args:
            days (int): 多少天内过期算作即将过期
            
        Returns:
            List[PasswordEntry]: 即将过期的条目列表
        """
        expiring_entries = self.repository.get_expiring_soon_entries(days)
        
        if expiring_entries:
            log_security_event("密码过期提醒", f"发现{len(expiring_entries)}个即将过期的密码")
        
        return expiring_entries
    
    def extend_password_expiry(self, entry_id: str, days: int = 90) -> Dict[str, Any]:
        """
        延长密码过期时间
        
        Args:
            entry_id (str): 条目ID
            days (int): 延长天数
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        entry = self.repository.get_password_entry_by_id(entry_id)
        if not entry:
            return {
                'success': False,
                'message': '密码条目不存在'
            }
        
        # 更新过期时间
        new_expiry = datetime.now() + timedelta(days=days)
        entry.expires_at = new_expiry
        entry.update_timestamp()
        
        # 保存更新
        success = self.repository.update_password_entry(
            entry_id, entry.platform, entry.username, 
            self.repository.decrypt_password(entry), entry.notes
        )
        
        if success:
            log_user_action("延长密码有效期", f"平台: {entry.platform}, 延长: {days}天")
            return {
                'success': True,
                'message': f'密码有效期已延长{days}天',
                'new_expiry': new_expiry
            }
        else:
            return {
                'success': False,
                'message': '延长密码有效期失败'
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取密码管理统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        all_entries = self.repository.get_password_entries()
        expired_entries = self.repository.get_expired_entries()
        expiring_soon_entries = self.repository.get_expiring_soon_entries(7)
        
        # 计算密码强度分布
        strength_distribution = {'很弱': 0, '弱': 0, '中等': 0, '强': 0, '很强': 0}
        
        for entry in all_entries:
            password = self.repository.decrypt_password(entry)
            if password:
                strength = self.password_generator.calculate_strength(password)
                strength_level = strength['level']
                if strength_level in strength_distribution:
                    strength_distribution[strength_level] += 1
        
        return {
            'total_entries': len(all_entries),
            'expired_entries': len(expired_entries),
            'expiring_soon_entries': len(expiring_soon_entries),
            'strength_distribution': strength_distribution,
            'last_updated': datetime.now()
        }
    
    def export_entries_for_backup(self) -> List[Dict[str, Any]]:
        """
        导出密码条目用于备份（不包含敏感信息）
        
        Returns:
            List[Dict[str, Any]]: 导出的条目列表
        """
        entries = self.repository.get_password_entries()
        exported_entries = []
        
        for entry in entries:
            exported_entries.append({
                'id': entry.id,
                'platform': entry.platform,
                'username': entry.username,
                'notes': entry.notes,
                'created_at': entry.created_at.isoformat() if entry.created_at else None,
                'updated_at': entry.updated_at.isoformat() if entry.updated_at else None,
                'expires_at': entry.expires_at.isoformat() if entry.expires_at else None
            })
        
        log_user_action("导出密码条目", f"导出{len(exported_entries)}个条目")
        return exported_entries
    
    # 回调函数设置方法
    def set_entry_added_callback(self, callback: Callable):
        """设置条目添加回调"""
        self._on_entry_added = callback
    
    def set_entry_updated_callback(self, callback: Callable):
        """设置条目更新回调"""
        self._on_entry_updated = callback
    
    def set_entry_deleted_callback(self, callback: Callable):
        """设置条目删除回调"""
        self._on_entry_deleted = callback
    
    def set_password_copied_callback(self, callback: Callable):
        """设置密码复制回调"""
        self._on_password_copied = callback
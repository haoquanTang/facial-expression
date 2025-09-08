#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据验证器模块

提供输入数据验证功能，确保数据的有效性和安全性
"""

import re
from typing import List, Dict, Any


class DataValidator:
    """
    数据验证器类
    
    提供各种数据验证功能
    """
    
    def __init__(self):
        """
        初始化数据验证器
        """
        # 平台名称正则表达式（允许字母、数字、中文、空格、常见符号）
        self.platform_pattern = re.compile(r'^[\w\s\u4e00-\u9fff._-]+$')
        
        # 用户名正则表达式（允许字母、数字、邮箱格式、常见符号）
        self.username_pattern = re.compile(r'^[\w@._-]+$')
        
        # 邮箱正则表达式
        self.email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
    
    def validate_platform_name(self, platform: str) -> Dict[str, Any]:
        """
        验证平台名称
        
        Args:
            platform (str): 平台名称
            
        Returns:
            Dict[str, Any]: 验证结果，包含is_valid和errors
        """
        errors = []
        
        if not platform:
            errors.append('平台名称不能为空')
            return {'is_valid': False, 'errors': errors}
        
        if len(platform.strip()) < 2:
            errors.append('平台名称至少需要2个字符')
        
        if len(platform) > 50:
            errors.append('平台名称不能超过50个字符')
        
        if not self.platform_pattern.match(platform):
            errors.append('平台名称包含无效字符')
        
        # 检查是否只包含空格
        if platform.strip() == '':
            errors.append('平台名称不能只包含空格')
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }
    
    def validate_username(self, username: str) -> Dict[str, Any]:
        """
        验证用户名
        
        Args:
            username (str): 用户名
            
        Returns:
            Dict[str, Any]: 验证结果，包含is_valid和errors
        """
        errors = []
        
        if not username:
            errors.append('用户名不能为空')
            return {'is_valid': False, 'errors': errors}
        
        if len(username.strip()) < 2:
            errors.append('用户名至少需要2个字符')
        
        if len(username) > 100:
            errors.append('用户名不能超过100个字符')
        
        # 检查是否是邮箱格式
        if '@' in username:
            if not self.email_pattern.match(username):
                errors.append('邮箱格式不正确')
        else:
            if not self.username_pattern.match(username):
                errors.append('用户名包含无效字符')
        
        # 检查是否只包含空格
        if username.strip() == '':
            errors.append('用户名不能只包含空格')
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }
    
    def validate_password(self, password: str) -> Dict[str, Any]:
        """
        验证密码
        
        Args:
            password (str): 密码
            
        Returns:
            Dict[str, Any]: 验证结果，包含is_valid和errors
        """
        errors = []
        
        if not password:
            errors.append('密码不能为空')
            return {'is_valid': False, 'errors': errors}
        
        if len(password) < 1:
            errors.append('密码不能为空')
        
        if len(password) > 500:
            errors.append('密码长度不能超过500个字符')
        
        # 检查是否包含不可打印字符（除了常见的特殊字符）
        printable_chars = set(
            'abcdefghijklmnopqrstuvwxyz'
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            '0123456789'
            '!@#$%^&*()_+-=[]{}|;:,.<>?"\''
            ' \t\n\r'
        )
        
        for char in password:
            if char not in printable_chars:
                errors.append('密码包含不支持的字符')
                break
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }
    
    def validate_master_password(self, password: str) -> Dict[str, Any]:
        """
        验证主密码（更严格的要求）
        
        Args:
            password (str): 主密码
            
        Returns:
            Dict[str, Any]: 验证结果，包含is_valid、errors和warnings
        """
        errors = []
        warnings = []
        
        if not password:
            errors.append('主密码不能为空')
            return {'is_valid': False, 'errors': errors, 'warnings': warnings}
        
        if len(password) < 8:
            errors.append('主密码至少需要8个字符')
        
        if len(password) > 128:
            errors.append('主密码不能超过128个字符')
        
        # 检查字符类型
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_symbol = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?"\'\'' for c in password)
        
        char_types = sum([has_lower, has_upper, has_digit, has_symbol])
        
        if char_types < 3:
            errors.append('主密码至少需要包含3种字符类型（大写字母、小写字母、数字、符号）')
        
        # 警告信息
        if len(password) < 12:
            warnings.append('建议主密码长度至少为12位')
        
        if not has_symbol:
            warnings.append('建议包含特殊符号以提高安全性')
        
        # 检查常见弱密码
        weak_passwords = [
            'password', '12345678', 'qwerty123', 'admin123',
            'password123', '123456789', 'qwertyuiop'
        ]
        
        if password.lower() in weak_passwords:
            errors.append('不能使用常见的弱密码')
        
        # 检查重复字符
        repeat_count = 0
        for i in range(len(password) - 2):
            if password[i] == password[i+1] == password[i+2]:
                repeat_count += 1
        
        if repeat_count > 0:
            warnings.append('避免连续重复相同字符')
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def validate_notes(self, notes: str) -> Dict[str, Any]:
        """
        验证备注信息
        
        Args:
            notes (str): 备注信息
            
        Returns:
            Dict[str, Any]: 验证结果，包含is_valid和errors
        """
        errors = []
        
        # 备注可以为空
        if notes is None:
            notes = ''
        
        if len(notes) > 500:
            errors.append('备注信息不能超过500个字符')
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }
    
    def validate_password_entry(self, platform: str, username: str, 
                              password: str, notes: str = '') -> Dict[str, Any]:
        """
        验证完整的密码条目
        
        Args:
            platform (str): 平台名称
            username (str): 用户名
            password (str): 密码
            notes (str): 备注信息
            
        Returns:
            Dict[str, Any]: 验证结果，包含is_valid和所有字段的错误信息
        """
        platform_result = self.validate_platform_name(platform)
        username_result = self.validate_username(username)
        password_result = self.validate_password(password)
        notes_result = self.validate_notes(notes)
        
        all_errors = {
            'platform': platform_result['errors'],
            'username': username_result['errors'],
            'password': password_result['errors'],
            'notes': notes_result['errors']
        }
        
        is_valid = all([
            platform_result['is_valid'],
            username_result['is_valid'],
            password_result['is_valid'],
            notes_result['is_valid']
        ])
        
        return {
            'is_valid': is_valid,
            'errors': all_errors
        }
    
    def sanitize_input(self, text: str) -> str:
        """
        清理输入文本，移除潜在的危险字符
        
        Args:
            text (str): 输入文本
            
        Returns:
            str: 清理后的文本
        """
        if not text:
            return ''
        
        # 移除首尾空格
        text = text.strip()
        
        # 移除控制字符（保留常见的空白字符）
        cleaned = ''
        for char in text:
            if ord(char) >= 32 or char in '\t\n\r':
                cleaned += char
        
        return cleaned
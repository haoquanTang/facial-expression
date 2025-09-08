#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
密码生成器模块

提供强密码生成功能，支持自定义长度和字符类型
"""

import random
import string
from typing import Dict, List


class PasswordGenerator:
    """
    密码生成器类
    
    提供强密码生成功能，支持自定义长度和字符类型
    """
    
    def __init__(self):
        """
        初始化密码生成器
        """
        self.lowercase = string.ascii_lowercase
        self.uppercase = string.ascii_uppercase
        self.digits = string.digits
        self.symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    def generate_password(
        self,
        length: int = 12,
        include_lowercase: bool = True,
        include_uppercase: bool = True,
        include_digits: bool = True,
        include_symbols: bool = True
    ) -> str:
        """
        生成强密码
        
        Args:
            length (int): 密码长度，默认12位
            include_lowercase (bool): 是否包含小写字母
            include_uppercase (bool): 是否包含大写字母
            include_digits (bool): 是否包含数字
            include_symbols (bool): 是否包含符号
            
        Returns:
            str: 生成的密码
            
        Raises:
            ValueError: 当长度小于4或没有选择任何字符类型时
        """
        if length < 4:
            raise ValueError("密码长度不能小于4位")
        
        # 构建字符集
        charset = ""
        required_chars = []
        
        if include_lowercase:
            charset += self.lowercase
            required_chars.append(random.choice(self.lowercase))
        
        if include_uppercase:
            charset += self.uppercase
            required_chars.append(random.choice(self.uppercase))
        
        if include_digits:
            charset += self.digits
            required_chars.append(random.choice(self.digits))
        
        if include_symbols:
            charset += self.symbols
            required_chars.append(random.choice(self.symbols))
        
        if not charset:
            raise ValueError("至少需要选择一种字符类型")
        
        # 生成剩余字符
        remaining_length = length - len(required_chars)
        if remaining_length > 0:
            random_chars = [random.choice(charset) for _ in range(remaining_length)]
            required_chars.extend(random_chars)
        
        # 打乱字符顺序
        password_chars = required_chars[:length]
        random.shuffle(password_chars)
        
        return ''.join(password_chars)
    
    def calculate_strength(self, password: str) -> dict:
        """
        计算密码强度
        
        Args:
            password (str): 要评估的密码
            
        Returns:
            dict: 包含强度评分和详细信息的字典
        """
        if not password:
            return {
                'score': 0,
                'level': '无密码',
                'feedback': ['请输入密码']
            }
        
        score = 0
        feedback = []
        
        # 长度评分
        length = len(password)
        if length >= 12:
            score += 25
        elif length >= 8:
            score += 15
        elif length >= 6:
            score += 10
        else:
            feedback.append('密码长度至少应为6位')
        
        # 字符类型评分
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_symbol = any(c in self.symbols for c in password)
        
        char_types = sum([has_lower, has_upper, has_digit, has_symbol])
        score += char_types * 15
        
        if not has_lower:
            feedback.append('建议包含小写字母')
        if not has_upper:
            feedback.append('建议包含大写字母')
        if not has_digit:
            feedback.append('建议包含数字')
        if not has_symbol:
            feedback.append('建议包含特殊符号')
        
        # 复杂度评分
        unique_chars = len(set(password))
        if unique_chars == length:
            score += 10  # 所有字符都不重复
        elif unique_chars >= length * 0.8:
            score += 5   # 大部分字符不重复
        
        # 常见模式检查
        common_patterns = [
            '123456', 'password', 'qwerty', 'abc123',
            '111111', '000000', 'admin', 'root'
        ]
        
        password_lower = password.lower()
        for pattern in common_patterns:
            if pattern in password_lower:
                score -= 20
                feedback.append(f'避免使用常见模式: {pattern}')
                break
        
        # 连续字符检查
        consecutive_count = 0
        for i in range(len(password) - 1):
            if ord(password[i+1]) == ord(password[i]) + 1:
                consecutive_count += 1
        
        if consecutive_count >= 3:
            score -= 10
            feedback.append('避免使用连续字符')
        
        # 重复字符检查
        repeat_count = 0
        for i in range(len(password) - 1):
            if password[i] == password[i+1]:
                repeat_count += 1
        
        if repeat_count >= 2:
            score -= 10
            feedback.append('避免重复字符')
        
        # 确保评分在0-100范围内
        score = max(0, min(100, score))
        
        # 确定强度等级
        if score >= 80:
            level = '很强'
        elif score >= 60:
            level = '强'
        elif score >= 40:
            level = '中等'
        elif score >= 20:
            level = '弱'
        else:
            level = '很弱'
        
        if not feedback:
            feedback.append('密码强度良好')
        
        return {
            'score': score,
            'level': level,
            'feedback': feedback
        }
    
    def generate_memorable_password(self, word_count: int = 4, separator: str = '-') -> str:
        """
        生成易记忆的密码（使用随机单词组合）
        
        Args:
            word_count (int): 单词数量，默认4个
            separator (str): 分隔符，默认'-'
            
        Returns:
            str: 生成的易记忆密码
        """
        # 简单的单词列表（实际应用中可以使用更大的词典）
        words = [
            'apple', 'banana', 'cherry', 'dragon', 'eagle', 'forest',
            'garden', 'house', 'island', 'jungle', 'kitten', 'lemon',
            'mountain', 'ocean', 'planet', 'queen', 'river', 'sunset',
            'tiger', 'umbrella', 'village', 'window', 'yellow', 'zebra'
        ]
        
        selected_words = random.sample(words, min(word_count, len(words)))
        
        # 随机大写某些单词的首字母
        for i in range(len(selected_words)):
            if random.choice([True, False]):
                selected_words[i] = selected_words[i].capitalize()
        
        # 添加随机数字
        password = separator.join(selected_words)
        password += str(random.randint(10, 99))
        
        return password
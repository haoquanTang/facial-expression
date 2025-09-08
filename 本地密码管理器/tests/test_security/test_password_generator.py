#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
密码生成器测试模块

测试PasswordGenerator的密码生成功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from security.password_generator import PasswordGenerator


def test_password_generator():
    """
    测试密码生成器的基本功能
    """
    generator = PasswordGenerator()
    
    print("开始测试密码生成器功能...")
    
    # 测试默认密码生成
    password = generator.generate_password()
    print(f"生成的默认密码: {password}")
    assert len(password) == 12, "默认密码长度应为12位"
    print("✓ 默认密码生成测试通过")
    
    # 测试自定义长度
    password_16 = generator.generate_password(length=16)
    print(f"生成的16位密码: {password_16}")
    assert len(password_16) == 16, "密码长度应为16位"
    print("✓ 自定义长度测试通过")
    
    # 测试只包含数字
    digit_password = generator.generate_password(
        length=8,
        include_lowercase=False,
        include_uppercase=False,
        include_symbols=False
    )
    print(f"生成的纯数字密码: {digit_password}")
    assert digit_password.isdigit(), "应该只包含数字"
    print("✓ 纯数字密码测试通过")
    
    # 测试密码强度计算
    strength = generator.calculate_strength("MyPassword123!")
    print(f"密码强度评估: {strength}")
    assert 'score' in strength, "应该包含评分"
    assert 'level' in strength, "应该包含等级"
    print("✓ 密码强度计算测试通过")
    
    # 测试易记忆密码
    memorable = generator.generate_memorable_password()
    print(f"生成的易记忆密码: {memorable}")
    assert len(memorable) > 0, "易记忆密码不能为空"
    print("✓ 易记忆密码测试通过")
    
    print("\n所有密码生成器测试通过！")


if __name__ == "__main__":
    test_password_generator()
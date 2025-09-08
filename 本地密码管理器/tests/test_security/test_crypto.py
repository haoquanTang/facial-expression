#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加密服务测试模块

测试CryptoService的加密解密功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from security.crypto import CryptoService


def test_crypto_service():
    """
    测试加密解密服务的基本功能
    """
    crypto = CryptoService()
    
    # 测试数据
    test_data = "这是一个测试密码：MyPassword123!"
    master_password = "TestMasterPassword123!"
    
    print("开始测试加密解密功能...")
    
    # 测试加密
    encrypted_info = crypto.encrypt_data(test_data, master_password)
    print(f"加密成功，加密数据长度: {len(encrypted_info['encrypted_data'])}")
    
    # 测试解密
    decrypted_data = crypto.decrypt_data(encrypted_info, master_password)
    print(f"解密成功，解密数据: {decrypted_data}")
    
    # 验证数据一致性
    assert decrypted_data == test_data, "加密解密数据不一致"
    print("✓ 加密解密往返测试通过")
    
    # 测试错误密码
    wrong_decrypted = crypto.decrypt_data(encrypted_info, "WrongPassword")
    assert wrong_decrypted is None, "错误密码应该解密失败"
    print("✓ 错误密码解密测试通过")
    
    # 测试密码哈希
    hash_info = crypto.hash_password(master_password)
    print(f"密码哈希成功，哈希长度: {len(hash_info['hash'])}")
    
    # 测试密码验证
    is_valid = crypto.verify_password(master_password, hash_info['hash'], hash_info['salt'])
    assert is_valid, "密码验证应该成功"
    print("✓ 密码验证测试通过")
    
    # 测试错误密码验证
    is_invalid = crypto.verify_password("WrongPassword", hash_info['hash'], hash_info['salt'])
    assert not is_invalid, "错误密码验证应该失败"
    print("✓ 错误密码验证测试通过")
    
    print("\n所有加密服务测试通过！")


if __name__ == "__main__":
    test_crypto_service
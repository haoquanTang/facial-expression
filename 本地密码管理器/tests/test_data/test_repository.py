#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据仓库测试模块

测试DataRepository的数据存储功能
"""

import sys
import os
import tempfile
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from data.repository import DataRepository
from core.models import PasswordEntry


def test_data_repository():
    """
    测试数据仓库的基本功能
    """
    # 创建临时文件用于测试
    with tempfile.NamedTemporaryFile(suffix='.enc', delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        print("开始测试数据仓库功能...")
        
        # 初始化数据仓库
        repo = DataRepository(temp_path)
        master_password = "TestMasterPassword123!"
        
        # 测试初始化新数据库
        success = repo.initialize_new_database(master_password)
        assert success, "初始化数据库应该成功"
        print("✓ 数据库初始化测试通过")
        
        # 测试添加密码条目
        success = repo.add_password_entry(
            platform="GitHub",
            username="test@example.com",
            password="MySecretPassword123!",
            notes="工作账号"
        )
        assert success, "添加密码条目应该成功"
        print("✓ 添加密码条目测试通过")
        
        # 测试获取密码条目
        entries = repo.get_password_entries()
        assert len(entries) == 1, "应该有一个密码条目"
        assert entries[0].platform == "GitHub", "平台名称应该匹配"
        assert entries[0].username == "test@example.com", "用户名应该匹配"
        print("✓ 获取密码条目测试通过")
        
        # 测试解密密码
        decrypted_password = repo.decrypt_password(entries[0])
        assert decrypted_password == "MySecretPassword123!", "解密后的密码应该匹配"
        print("✓ 密码解密测试通过")
        
        # 测试搜索功能
        search_results = repo.get_password_entries("GitHub")
        assert len(search_results) == 1, "搜索应该找到一个结果"
        print("✓ 搜索功能测试通过")
        
        # 测试更新密码条目
        entry_id = entries[0].id
        success = repo.update_password_entry(
            entry_id=entry_id,
            platform="GitHub",
            username="test@example.com",
            password="UpdatedPassword456!",
            notes="更新后的工作账号"
        )
        assert success, "更新密码条目应该成功"
        print("✓ 更新密码条目测试通过")
        
        # 验证更新后的密码
        updated_entry = repo.get_password_entry_by_id(entry_id)
        assert updated_entry is not None, "应该能找到更新后的条目"
        decrypted_updated_password = repo.decrypt_password(updated_entry)
        assert decrypted_updated_password == "UpdatedPassword456!", "更新后的密码应该匹配"
        print("✓ 密码更新验证测试通过")
        
        # 测试重新加载数据库
        repo2 = DataRepository(temp_path)
        success = repo2.load_database(master_password)
        assert success, "重新加载数据库应该成功"
        
        entries2 = repo2.get_password_entries()
        assert len(entries2) == 1, "重新加载后应该有一个密码条目"
        decrypted_password2 = repo2.decrypt_password(entries2[0])
        assert decrypted_password2 == "UpdatedPassword456!", "重新加载后密码应该匹配"
        print("✓ 数据库重新加载测试通过")
        
        # 测试删除密码条目
        success = repo2.delete_password_entry(entry_id)
        assert success, "删除密码条目应该成功"
        
        entries3 = repo2.get_password_entries()
        assert len(entries3) == 0, "删除后应该没有密码条目"
        print("✓ 删除密码条目测试通过")
        
        print("\n所有数据仓库测试通过！")
        
    finally:
        # 清理临时文件
        try:
            os.unlink(temp_path)
        except:
            pass


if __name__ == "__main__":
    test_data_repository()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
密码管理器测试模块

测试PasswordManager的核心功能
"""

import os
import tempfile
import shutil
from datetime import datetime, timedelta

from core.password_manager import PasswordManager
from data.repository import DataRepository
from security.crypto import CryptoService
from config.settings import AppConfig


def test_password_manager():
    """测试密码管理器功能"""
    print("开始测试密码管理器...")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 初始化配置和组件
        config = AppConfig()
        config.data_dir = temp_dir
        
        # 创建数据文件路径
        data_file = os.path.join(temp_dir, "passwords.enc")
        repository = DataRepository(data_file)
        password_manager = PasswordManager(repository)
        
        # 初始化数据库
        master_password = "test_master_123"
        init_result = repository.initialize_new_database(master_password)
        assert init_result, "数据库初始化失败"
        print("✓ 数据库初始化成功")
        
        # 测试添加密码条目
        add_result = password_manager.add_password_entry(
            platform="测试平台",
            username="test_user",
            password="test_password_123",
            notes="测试备注"
        )
        assert add_result['success'], f"添加密码条目失败: {add_result.get('message')}"
        print("✓ 密码条目添加成功")
        
        # 测试获取密码条目列表
        entries = password_manager.get_password_entries()
        assert len(entries) == 1, f"期望1个条目，实际{len(entries)}个"
        assert entries[0].platform == "测试平台", "平台名称不匹配"
        assert entries[0].username == "test_user", "用户名不匹配"
        print("✓ 密码条目获取成功")
        
        # 测试搜索功能
        search_results = password_manager.get_password_entries("测试")
        assert len(search_results) == 1, "搜索结果数量不正确"
        print("✓ 搜索功能正常")
        
        # 测试根据ID获取条目
        entry_id = entries[0].id
        entry = password_manager.get_password_entry_by_id(entry_id)
        assert entry is not None, "根据ID获取条目失败"
        assert entry.platform == "测试平台", "获取的条目信息不正确"
        print("✓ 根据ID获取条目成功")
        
        # 测试更新密码条目
        update_result = password_manager.update_password_entry(
            entry_id=entry_id,
            platform="更新后平台",
            username="updated_user",
            password="updated_password_456",
            notes="更新后备注"
        )
        assert update_result['success'], f"更新密码条目失败: {update_result.get('message')}"
        print("✓ 密码条目更新成功")
        
        # 验证更新结果
        updated_entry = password_manager.get_password_entry_by_id(entry_id)
        assert updated_entry.platform == "更新后平台", "更新后平台名称不正确"
        assert updated_entry.username == "updated_user", "更新后用户名不正确"
        print("✓ 更新结果验证成功")
        
        # 测试密码生成功能
        gen_result = password_manager.generate_password(
            length=16,
            include_lowercase=True,
            include_uppercase=True,
            include_digits=True,
            include_symbols=True
        )
        assert gen_result['success'], "密码生成失败"
        assert len(gen_result['password']) == 16, "生成的密码长度不正确"
        assert 'strength' in gen_result, "缺少密码强度信息"
        print(f"✓ 密码生成成功: {gen_result['password']}")
        
        # 测试密码强度计算
        strength = password_manager.calculate_password_strength("Test123!@#")
        assert 'level' in strength, "缺少强度等级"
        assert 'score' in strength, "缺少强度分数"
        print(f"✓ 密码强度计算成功: {strength['level']}")
        
        # 测试统计信息
        stats = password_manager.get_statistics()
        assert stats['total_entries'] == 1, "统计的条目数量不正确"
        assert 'strength_distribution' in stats, "缺少强度分布信息"
        print("✓ 统计信息获取成功")
        
        # 测试导出功能
        exported_entries = password_manager.export_entries_for_backup()
        assert len(exported_entries) == 1, "导出的条目数量不正确"
        assert 'platform' in exported_entries[0], "导出数据缺少平台信息"
        assert 'password' not in exported_entries[0], "导出数据不应包含密码"
        print("✓ 条目导出成功")
        
        # 测试添加重复条目（应该失败）
        duplicate_result = password_manager.add_password_entry(
            platform="更新后平台",
            username="updated_user",
            password="another_password",
            notes="重复条目"
        )
        assert not duplicate_result['success'], "重复条目添加应该失败"
        print("✓ 重复条目检测正常")
        
        # 测试删除密码条目
        delete_result = password_manager.delete_password_entry(entry_id)
        assert delete_result['success'], f"删除密码条目失败: {delete_result.get('message')}"
        print("✓ 密码条目删除成功")
        
        # 验证删除结果
        deleted_entry = password_manager.get_password_entry_by_id(entry_id)
        assert deleted_entry is None, "条目删除后仍然存在"
        
        remaining_entries = password_manager.get_password_entries()
        assert len(remaining_entries) == 0, "删除后仍有条目存在"
        print("✓ 删除结果验证成功")
        
        # 测试回调函数
        callback_called = {'added': False, 'updated': False, 'deleted': False}
        
        def on_entry_added(platform, username):
            callback_called['added'] = True
            print(f"回调: 添加了条目 {platform} - {username}")
        
        def on_entry_updated(entry_id, platform, username):
            callback_called['updated'] = True
            print(f"回调: 更新了条目 {entry_id}")
        
        def on_entry_deleted(entry_id, platform):
            callback_called['deleted'] = True
            print(f"回调: 删除了条目 {entry_id}")
        
        # 设置回调函数
        password_manager.set_entry_added_callback(on_entry_added)
        password_manager.set_entry_updated_callback(on_entry_updated)
        password_manager.set_entry_deleted_callback(on_entry_deleted)
        
        # 测试回调函数
        add_result = password_manager.add_password_entry(
            platform="回调测试",
            username="callback_user",
            password="callback_pass",
            notes="测试回调"
        )
        assert add_result['success'], "回调测试添加失败"
        assert callback_called['added'], "添加回调未被调用"
        
        # 获取新添加的条目ID
        new_entries = password_manager.get_password_entries()
        new_entry_id = new_entries[0].id
        
        # 测试更新回调
        update_result = password_manager.update_password_entry(
            entry_id=new_entry_id,
            platform="回调测试更新",
            username="callback_user_updated",
            password="callback_pass_updated",
            notes="测试回调更新"
        )
        assert update_result['success'], "回调测试更新失败"
        assert callback_called['updated'], "更新回调未被调用"
        
        # 测试删除回调
        delete_result = password_manager.delete_password_entry(new_entry_id)
        assert delete_result['success'], "回调测试删除失败"
        assert callback_called['deleted'], "删除回调未被调用"
        
        print("✓ 回调函数测试成功")
        
        print("\n所有密码管理器测试通过！")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        raise
    finally:
        # 清理临时目录
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    test_password_manager()
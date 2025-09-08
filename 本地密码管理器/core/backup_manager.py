#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
备份管理模块

提供数据备份和恢复功能
"""

import os
import json
import shutil
import zipfile
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

from data.repository import DataRepository
from security.crypto import CryptoManager
from utils.helpers import (
    format_file_size, ensure_directory_exists, 
    get_available_disk_space, create_backup_filename
)
from utils.logger import log_user_action, log_system_event
from config.constants import (
    BACKUP_RETENTION_DAYS, MAX_BACKUP_SIZE_MB,
    BACKUP_FILE_EXTENSION, ENCRYPTED_BACKUP_EXTENSION
)


class BackupManager:
    """
    备份管理器
    
    负责数据的备份和恢复操作
    """
    
    def __init__(self, repository: DataRepository, backup_dir: str):
        """
        初始化备份管理器
        
        Args:
            repository (DataRepository): 数据仓库实例
            backup_dir (str): 备份目录路径
        """
        self.repository = repository
        self.backup_dir = Path(backup_dir)
        self.crypto_manager = CryptoManager()
        
        # 确保备份目录存在
        ensure_directory_exists(str(self.backup_dir))
    
    def create_backup(self, include_settings: bool = True, 
                     encrypt_backup: bool = True, 
                     backup_password: Optional[str] = None) -> Dict[str, Any]:
        """
        创建数据备份
        
        Args:
            include_settings (bool): 是否包含应用设置
            encrypt_backup (bool): 是否加密备份文件
            backup_password (Optional[str]): 备份文件密码
            
        Returns:
            Dict[str, Any]: 备份结果
        """
        try:
            # 检查磁盘空间
            available_space = get_available_disk_space(str(self.backup_dir))
            if available_space < MAX_BACKUP_SIZE_MB * 1024 * 1024:  # 转换为字节
                return {
                    'success': False,
                    'message': f'磁盘空间不足，需要至少{MAX_BACKUP_SIZE_MB}MB空间'
                }
            
            # 生成备份文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if encrypt_backup:
                backup_filename = f"backup_{timestamp}{ENCRYPTED_BACKUP_EXTENSION}"
            else:
                backup_filename = f"backup_{timestamp}{BACKUP_FILE_EXTENSION}"
            
            backup_path = self.backup_dir / backup_filename
            
            # 准备备份数据
            backup_data = self._prepare_backup_data(include_settings)
            
            # 创建备份文件
            if encrypt_backup:
                success = self._create_encrypted_backup(backup_data, backup_path, backup_password)
            else:
                success = self._create_plain_backup(backup_data, backup_path)
            
            if success:
                # 获取文件大小
                file_size = os.path.getsize(backup_path)
                
                log_user_action("创建备份", f"文件: {backup_filename}, 大小: {format_file_size(file_size)}")
                
                # 清理旧备份
                self._cleanup_old_backups()
                
                return {
                    'success': True,
                    'message': '备份创建成功',
                    'backup_file': backup_filename,
                    'backup_path': str(backup_path),
                    'file_size': file_size,
                    'encrypted': encrypt_backup,
                    'created_at': datetime.now()
                }
            else:
                return {
                    'success': False,
                    'message': '备份创建失败'
                }
                
        except Exception as e:
            log_system_event("备份创建错误", f"错误: {str(e)}")
            return {
                'success': False,
                'message': f'备份创建失败: {str(e)}'
            }
    
    def restore_backup(self, backup_file: str, 
                      backup_password: Optional[str] = None,
                      overwrite_existing: bool = False) -> Dict[str, Any]:
        """
        从备份文件恢复数据
        
        Args:
            backup_file (str): 备份文件名
            backup_password (Optional[str]): 备份文件密码
            overwrite_existing (bool): 是否覆盖现有数据
            
        Returns:
            Dict[str, Any]: 恢复结果
        """
        try:
            backup_path = self.backup_dir / backup_file
            
            # 检查备份文件是否存在
            if not backup_path.exists():
                return {
                    'success': False,
                    'message': '备份文件不存在'
                }
            
            # 判断是否为加密备份
            is_encrypted = backup_file.endswith(ENCRYPTED_BACKUP_EXTENSION)
            
            # 读取备份数据
            if is_encrypted:
                backup_data = self._read_encrypted_backup(backup_path, backup_password)
            else:
                backup_data = self._read_plain_backup(backup_path)
            
            if not backup_data:
                return {
                    'success': False,
                    'message': '备份文件读取失败或密码错误'
                }
            
            # 验证备份数据格式
            validation_result = self._validate_backup_data(backup_data)
            if not validation_result['is_valid']:
                return {
                    'success': False,
                    'message': f'备份数据格式无效: {validation_result["error"]}'
                }
            
            # 执行恢复操作
            restore_result = self._restore_data(backup_data, overwrite_existing)
            
            if restore_result['success']:
                log_user_action("恢复备份", f"文件: {backup_file}, 恢复条目: {restore_result['restored_entries']}")
                
                return {
                    'success': True,
                    'message': '数据恢复成功',
                    'restored_entries': restore_result['restored_entries'],
                    'skipped_entries': restore_result['skipped_entries'],
                    'restored_at': datetime.now()
                }
            else:
                return restore_result
                
        except Exception as e:
            log_system_event("备份恢复错误", f"文件: {backup_file}, 错误: {str(e)}")
            return {
                'success': False,
                'message': f'数据恢复失败: {str(e)}'
            }
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """
        列出所有备份文件
        
        Returns:
            List[Dict[str, Any]]: 备份文件列表
        """
        backups = []
        
        try:
            # 扫描备份目录
            for file_path in self.backup_dir.glob(f"*{BACKUP_FILE_EXTENSION}"):
                backups.append(self._get_backup_info(file_path, False))
            
            for file_path in self.backup_dir.glob(f"*{ENCRYPTED_BACKUP_EXTENSION}"):
                backups.append(self._get_backup_info(file_path, True))
            
            # 按创建时间排序（最新的在前）
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            log_system_event("备份列表获取错误", f"错误: {str(e)}")
        
        return backups
    
    def delete_backup(self, backup_file: str) -> Dict[str, Any]:
        """
        删除备份文件
        
        Args:
            backup_file (str): 备份文件名
            
        Returns:
            Dict[str, Any]: 删除结果
        """
        try:
            backup_path = self.backup_dir / backup_file
            
            if not backup_path.exists():
                return {
                    'success': False,
                    'message': '备份文件不存在'
                }
            
            # 删除文件
            os.remove(backup_path)
            
            log_user_action("删除备份", f"文件: {backup_file}")
            
            return {
                'success': True,
                'message': '备份文件删除成功'
            }
            
        except Exception as e:
            log_system_event("备份删除错误", f"文件: {backup_file}, 错误: {str(e)}")
            return {
                'success': False,
                'message': f'备份文件删除失败: {str(e)}'
            }
    
    def get_backup_info(self, backup_file: str) -> Optional[Dict[str, Any]]:
        """
        获取备份文件详细信息
        
        Args:
            backup_file (str): 备份文件名
            
        Returns:
            Optional[Dict[str, Any]]: 备份文件信息
        """
        backup_path = self.backup_dir / backup_file
        
        if not backup_path.exists():
            return None
        
        is_encrypted = backup_file.endswith(ENCRYPTED_BACKUP_EXTENSION)
        return self._get_backup_info(backup_path, is_encrypted)
    
    def _prepare_backup_data(self, include_settings: bool) -> Dict[str, Any]:
        """
        准备备份数据
        
        Args:
            include_settings (bool): 是否包含应用设置
            
        Returns:
            Dict[str, Any]: 备份数据
        """
        backup_data = {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'entries': [],
            'settings': None
        }
        
        # 获取所有密码条目
        entries = self.repository.get_password_entries()
        for entry in entries:
            # 解密密码用于备份
            decrypted_password = self.repository.decrypt_password(entry)
            
            backup_data['entries'].append({
                'id': entry.id,
                'platform': entry.platform,
                'username': entry.username,
                'password': decrypted_password,  # 明文密码，稍后会重新加密
                'notes': entry.notes,
                'created_at': entry.created_at.isoformat() if entry.created_at else None,
                'updated_at': entry.updated_at.isoformat() if entry.updated_at else None,
                'expires_at': entry.expires_at.isoformat() if entry.expires_at else None
            })
        
        # 包含应用设置
        if include_settings:
            settings = self.repository.get_app_settings()
            if settings:
                backup_data['settings'] = settings.to_dict()
        
        return backup_data
    
    def _create_encrypted_backup(self, backup_data: Dict[str, Any], 
                               backup_path: Path, password: Optional[str]) -> bool:
        """
        创建加密备份文件
        
        Args:
            backup_data (Dict[str, Any]): 备份数据
            backup_path (Path): 备份文件路径
            password (Optional[str]): 加密密码
            
        Returns:
            bool: 是否成功
        """
        try:
            # 序列化数据
            json_data = json.dumps(backup_data, ensure_ascii=False, indent=2)
            
            # 使用提供的密码或生成随机密码
            if password:
                encryption_key = self.crypto_manager.derive_key_from_password(password)
            else:
                encryption_key = self.crypto_manager.generate_key()
            
            # 加密数据
            encrypted_data = self.crypto_manager.encrypt_data(json_data.encode('utf-8'), encryption_key)
            
            # 写入文件
            with open(backup_path, 'wb') as f:
                f.write(encrypted_data)
            
            return True
            
        except Exception as e:
            log_system_event("加密备份创建错误", f"错误: {str(e)}")
            return False
    
    def _create_plain_backup(self, backup_data: Dict[str, Any], backup_path: Path) -> bool:
        """
        创建明文备份文件
        
        Args:
            backup_data (Dict[str, Any]): 备份数据
            backup_path (Path): 备份文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            log_system_event("明文备份创建错误", f"错误: {str(e)}")
            return False
    
    def _read_encrypted_backup(self, backup_path: Path, 
                             password: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        读取加密备份文件
        
        Args:
            backup_path (Path): 备份文件路径
            password (Optional[str]): 解密密码
            
        Returns:
            Optional[Dict[str, Any]]: 备份数据
        """
        try:
            if not password:
                return None
            
            # 读取加密数据
            with open(backup_path, 'rb') as f:
                encrypted_data = f.read()
            
            # 派生解密密钥
            decryption_key = self.crypto_manager.derive_key_from_password(password)
            
            # 解密数据
            decrypted_data = self.crypto_manager.decrypt_data(encrypted_data, decryption_key)
            if not decrypted_data:
                return None
            
            # 解析JSON
            json_data = decrypted_data.decode('utf-8')
            return json.loads(json_data)
            
        except Exception as e:
            log_system_event("加密备份读取错误", f"错误: {str(e)}")
            return None
    
    def _read_plain_backup(self, backup_path: Path) -> Optional[Dict[str, Any]]:
        """
        读取明文备份文件
        
        Args:
            backup_path (Path): 备份文件路径
            
        Returns:
            Optional[Dict[str, Any]]: 备份数据
        """
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            log_system_event("明文备份读取错误", f"错误: {str(e)}")
            return None
    
    def _validate_backup_data(self, backup_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证备份数据格式
        
        Args:
            backup_data (Dict[str, Any]): 备份数据
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            # 检查必需字段
            required_fields = ['version', 'created_at', 'entries']
            for field in required_fields:
                if field not in backup_data:
                    return {
                        'is_valid': False,
                        'error': f'缺少必需字段: {field}'
                    }
            
            # 检查条目格式
            if not isinstance(backup_data['entries'], list):
                return {
                    'is_valid': False,
                    'error': '条目数据格式错误'
                }
            
            # 检查每个条目的必需字段
            entry_required_fields = ['platform', 'username', 'password']
            for i, entry in enumerate(backup_data['entries']):
                for field in entry_required_fields:
                    if field not in entry:
                        return {
                            'is_valid': False,
                            'error': f'条目{i+1}缺少必需字段: {field}'
                        }
            
            return {'is_valid': True}
            
        except Exception as e:
            return {
                'is_valid': False,
                'error': f'数据验证错误: {str(e)}'
            }
    
    def _restore_data(self, backup_data: Dict[str, Any], 
                     overwrite_existing: bool) -> Dict[str, Any]:
        """
        执行数据恢复
        
        Args:
            backup_data (Dict[str, Any]): 备份数据
            overwrite_existing (bool): 是否覆盖现有数据
            
        Returns:
            Dict[str, Any]: 恢复结果
        """
        restored_entries = 0
        skipped_entries = 0
        
        try:
            # 恢复密码条目
            for entry_data in backup_data['entries']:
                platform = entry_data['platform']
                username = entry_data['username']
                password = entry_data['password']
                notes = entry_data.get('notes', '')
                
                # 检查是否已存在
                existing_entries = self.repository.get_password_entries(f"{platform} {username}")
                entry_exists = any(
                    e.platform == platform and e.username == username 
                    for e in existing_entries
                )
                
                if entry_exists and not overwrite_existing:
                    skipped_entries += 1
                    continue
                
                # 添加或更新条目
                if entry_exists and overwrite_existing:
                    # 找到现有条目并更新
                    for existing_entry in existing_entries:
                        if existing_entry.platform == platform and existing_entry.username == username:
                            success = self.repository.update_password_entry(
                                existing_entry.id, platform, username, password, notes
                            )
                            if success:
                                restored_entries += 1
                            break
                else:
                    # 添加新条目
                    success = self.repository.add_password_entry(platform, username, password, notes)
                    if success:
                        restored_entries += 1
            
            # 恢复应用设置
            if 'settings' in backup_data and backup_data['settings']:
                settings_data = backup_data['settings']
                # 这里可以添加设置恢复逻辑
                # self.repository.update_app_settings(settings_data)
            
            return {
                'success': True,
                'restored_entries': restored_entries,
                'skipped_entries': skipped_entries
            }
            
        except Exception as e:
            log_system_event("数据恢复错误", f"错误: {str(e)}")
            return {
                'success': False,
                'message': f'数据恢复失败: {str(e)}'
            }
    
    def _get_backup_info(self, file_path: Path, is_encrypted: bool) -> Dict[str, Any]:
        """
        获取备份文件信息
        
        Args:
            file_path (Path): 文件路径
            is_encrypted (bool): 是否为加密文件
            
        Returns:
            Dict[str, Any]: 文件信息
        """
        stat = file_path.stat()
        
        return {
            'filename': file_path.name,
            'file_path': str(file_path),
            'file_size': stat.st_size,
            'file_size_formatted': format_file_size(stat.st_size),
            'created_at': datetime.fromtimestamp(stat.st_ctime),
            'modified_at': datetime.fromtimestamp(stat.st_mtime),
            'is_encrypted': is_encrypted
        }
    
    def _cleanup_old_backups(self):
        """
        清理过期的备份文件
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=BACKUP_RETENTION_DAYS)
            deleted_count = 0
            
            # 扫描所有备份文件
            for pattern in [f"*{BACKUP_FILE_EXTENSION}", f"*{ENCRYPTED_BACKUP_EXTENSION}"]:
                for file_path in self.backup_dir.glob(pattern):
                    file_time = datetime.fromtimestamp(file_path.stat().st_ctime)
                    
                    if file_time < cutoff_date:
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                        except Exception as e:
                            log_system_event("备份清理错误", f"文件: {file_path.name}, 错误: {str(e)}")
            
            if deleted_count > 0:
                log_system_event("备份清理", f"删除了{deleted_count}个过期备份文件")
                
        except Exception as e:
            log_system_event("备份清理错误", f"错误: {str(e)}")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件管理模块

提供文件操作和管理功能
"""

import os
import shutil
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

from utils.helpers import (
    format_file_size, ensure_directory_exists, 
    get_available_disk_space, calculate_file_hash,
    generate_unique_filename
)
from utils.logger import log_user_action, log_system_event
from config.constants import (
    MAX_FILE_SIZE_MB, ALLOWED_FILE_EXTENSIONS,
    TEMP_FILE_RETENTION_HOURS
)


class FileManager:
    """
    文件管理器
    
    负责文件的创建、读取、写入、删除等操作
    """
    
    def __init__(self, data_dir: str, temp_dir: str):
        """
        初始化文件管理器
        
        Args:
            data_dir (str): 数据目录路径
            temp_dir (str): 临时文件目录路径
        """
        self.data_dir = Path(data_dir)
        self.temp_dir = Path(temp_dir)
        
        # 确保目录存在
        ensure_directory_exists(str(self.data_dir))
        ensure_directory_exists(str(self.temp_dir))
    
    def create_file(self, filename: str, content: bytes, 
                   subdirectory: str = "") -> Dict[str, Any]:
        """
        创建文件
        
        Args:
            filename (str): 文件名
            content (bytes): 文件内容
            subdirectory (str): 子目录名
            
        Returns:
            Dict[str, Any]: 创建结果
        """
        try:
            # 验证文件大小
            if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
                return {
                    'success': False,
                    'message': f'文件大小超过限制（{MAX_FILE_SIZE_MB}MB）'
                }
            
            # 验证文件扩展名
            file_ext = Path(filename).suffix.lower()
            if file_ext and file_ext not in ALLOWED_FILE_EXTENSIONS:
                return {
                    'success': False,
                    'message': f'不支持的文件类型: {file_ext}'
                }
            
            # 构建文件路径
            if subdirectory:
                target_dir = self.data_dir / subdirectory
                ensure_directory_exists(str(target_dir))
            else:
                target_dir = self.data_dir
            
            file_path = target_dir / filename
            
            # 如果文件已存在，生成唯一文件名
            if file_path.exists():
                unique_filename = generate_unique_filename(str(file_path))
                file_path = target_dir / unique_filename
            
            # 检查磁盘空间
            available_space = get_available_disk_space(str(target_dir))
            if available_space < len(content):
                return {
                    'success': False,
                    'message': '磁盘空间不足'
                }
            
            # 写入文件
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # 计算文件哈希
            file_hash = calculate_file_hash(str(file_path))
            
            log_user_action("创建文件", f"文件: {file_path.name}, 大小: {format_file_size(len(content))}")
            
            return {
                'success': True,
                'message': '文件创建成功',
                'file_path': str(file_path),
                'filename': file_path.name,
                'file_size': len(content),
                'file_hash': file_hash,
                'created_at': datetime.now()
            }
            
        except Exception as e:
            log_system_event("文件创建错误", f"文件: {filename}, 错误: {str(e)}")
            return {
                'success': False,
                'message': f'文件创建失败: {str(e)}'
            }
    
    def read_file(self, file_path: str) -> Dict[str, Any]:
        """
        读取文件
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            Dict[str, Any]: 读取结果
        """
        try:
            path = Path(file_path)
            
            # 检查文件是否存在
            if not path.exists():
                return {
                    'success': False,
                    'message': '文件不存在'
                }
            
            # 检查是否为文件
            if not path.is_file():
                return {
                    'success': False,
                    'message': '指定路径不是文件'
                }
            
            # 检查文件大小
            file_size = path.stat().st_size
            if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                return {
                    'success': False,
                    'message': f'文件过大，无法读取（超过{MAX_FILE_SIZE_MB}MB）'
                }
            
            # 读取文件内容
            with open(path, 'rb') as f:
                content = f.read()
            
            # 计算文件哈希
            file_hash = calculate_file_hash(str(path))
            
            log_user_action("读取文件", f"文件: {path.name}, 大小: {format_file_size(file_size)}")
            
            return {
                'success': True,
                'content': content,
                'file_size': file_size,
                'file_hash': file_hash,
                'modified_at': datetime.fromtimestamp(path.stat().st_mtime)
            }
            
        except Exception as e:
            log_system_event("文件读取错误", f"文件: {file_path}, 错误: {str(e)}")
            return {
                'success': False,
                'message': f'文件读取失败: {str(e)}'
            }
    
    def write_file(self, file_path: str, content: bytes, 
                  create_backup: bool = True) -> Dict[str, Any]:
        """
        写入文件
        
        Args:
            file_path (str): 文件路径
            content (bytes): 文件内容
            create_backup (bool): 是否创建备份
            
        Returns:
            Dict[str, Any]: 写入结果
        """
        try:
            path = Path(file_path)
            
            # 验证文件大小
            if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
                return {
                    'success': False,
                    'message': f'文件大小超过限制（{MAX_FILE_SIZE_MB}MB）'
                }
            
            # 检查磁盘空间
            available_space = get_available_disk_space(str(path.parent))
            if available_space < len(content):
                return {
                    'success': False,
                    'message': '磁盘空间不足'
                }
            
            # 创建备份（如果文件存在且需要备份）
            backup_path = None
            if create_backup and path.exists():
                backup_result = self.create_backup_file(str(path))
                if backup_result['success']:
                    backup_path = backup_result['backup_path']
            
            # 确保父目录存在
            ensure_directory_exists(str(path.parent))
            
            # 写入文件
            with open(path, 'wb') as f:
                f.write(content)
            
            # 计算文件哈希
            file_hash = calculate_file_hash(str(path))
            
            log_user_action("写入文件", f"文件: {path.name}, 大小: {format_file_size(len(content))}")
            
            result = {
                'success': True,
                'message': '文件写入成功',
                'file_path': str(path),
                'file_size': len(content),
                'file_hash': file_hash,
                'modified_at': datetime.now()
            }
            
            if backup_path:
                result['backup_path'] = backup_path
            
            return result
            
        except Exception as e:
            log_system_event("文件写入错误", f"文件: {file_path}, 错误: {str(e)}")
            return {
                'success': False,
                'message': f'文件写入失败: {str(e)}'
            }
    
    def delete_file(self, file_path: str, create_backup: bool = True) -> Dict[str, Any]:
        """
        删除文件
        
        Args:
            file_path (str): 文件路径
            create_backup (bool): 是否创建备份
            
        Returns:
            Dict[str, Any]: 删除结果
        """
        try:
            path = Path(file_path)
            
            # 检查文件是否存在
            if not path.exists():
                return {
                    'success': False,
                    'message': '文件不存在'
                }
            
            # 获取文件信息
            file_size = path.stat().st_size
            
            # 创建备份（如果需要）
            backup_path = None
            if create_backup:
                backup_result = self.create_backup_file(str(path))
                if backup_result['success']:
                    backup_path = backup_result['backup_path']
            
            # 删除文件
            os.remove(path)
            
            log_user_action("删除文件", f"文件: {path.name}, 大小: {format_file_size(file_size)}")
            
            result = {
                'success': True,
                'message': '文件删除成功',
                'deleted_file': str(path),
                'file_size': file_size
            }
            
            if backup_path:
                result['backup_path'] = backup_path
            
            return result
            
        except Exception as e:
            log_system_event("文件删除错误", f"文件: {file_path}, 错误: {str(e)}")
            return {
                'success': False,
                'message': f'文件删除失败: {str(e)}'
            }
    
    def copy_file(self, source_path: str, dest_path: str, 
                 overwrite: bool = False) -> Dict[str, Any]:
        """
        复制文件
        
        Args:
            source_path (str): 源文件路径
            dest_path (str): 目标文件路径
            overwrite (bool): 是否覆盖现有文件
            
        Returns:
            Dict[str, Any]: 复制结果
        """
        try:
            source = Path(source_path)
            dest = Path(dest_path)
            
            # 检查源文件是否存在
            if not source.exists():
                return {
                    'success': False,
                    'message': '源文件不存在'
                }
            
            # 检查目标文件是否存在
            if dest.exists() and not overwrite:
                return {
                    'success': False,
                    'message': '目标文件已存在，且未设置覆盖'
                }
            
            # 检查磁盘空间
            file_size = source.stat().st_size
            available_space = get_available_disk_space(str(dest.parent))
            if available_space < file_size:
                return {
                    'success': False,
                    'message': '磁盘空间不足'
                }
            
            # 确保目标目录存在
            ensure_directory_exists(str(dest.parent))
            
            # 复制文件
            shutil.copy2(source, dest)
            
            log_user_action("复制文件", f"从 {source.name} 到 {dest.name}")
            
            return {
                'success': True,
                'message': '文件复制成功',
                'source_path': str(source),
                'dest_path': str(dest),
                'file_size': file_size
            }
            
        except Exception as e:
            log_system_event("文件复制错误", f"从 {source_path} 到 {dest_path}, 错误: {str(e)}")
            return {
                'success': False,
                'message': f'文件复制失败: {str(e)}'
            }
    
    def move_file(self, source_path: str, dest_path: str, 
                 overwrite: bool = False) -> Dict[str, Any]:
        """
        移动文件
        
        Args:
            source_path (str): 源文件路径
            dest_path (str): 目标文件路径
            overwrite (bool): 是否覆盖现有文件
            
        Returns:
            Dict[str, Any]: 移动结果
        """
        try:
            source = Path(source_path)
            dest = Path(dest_path)
            
            # 检查源文件是否存在
            if not source.exists():
                return {
                    'success': False,
                    'message': '源文件不存在'
                }
            
            # 检查目标文件是否存在
            if dest.exists() and not overwrite:
                return {
                    'success': False,
                    'message': '目标文件已存在，且未设置覆盖'
                }
            
            # 获取文件大小
            file_size = source.stat().st_size
            
            # 确保目标目录存在
            ensure_directory_exists(str(dest.parent))
            
            # 移动文件
            shutil.move(str(source), str(dest))
            
            log_user_action("移动文件", f"从 {source.name} 到 {dest.name}")
            
            return {
                'success': True,
                'message': '文件移动成功',
                'source_path': str(source),
                'dest_path': str(dest),
                'file_size': file_size
            }
            
        except Exception as e:
            log_system_event("文件移动错误", f"从 {source_path} 到 {dest_path}, 错误: {str(e)}")
            return {
                'success': False,
                'message': f'文件移动失败: {str(e)}'
            }
    
    def create_backup_file(self, file_path: str) -> Dict[str, Any]:
        """
        创建文件备份
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            Dict[str, Any]: 备份结果
        """
        try:
            source = Path(file_path)
            
            if not source.exists():
                return {
                    'success': False,
                    'message': '源文件不存在'
                }
            
            # 生成备份文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{source.stem}_{timestamp}{source.suffix}"
            backup_path = source.parent / backup_name
            
            # 复制文件
            shutil.copy2(source, backup_path)
            
            log_user_action("创建文件备份", f"文件: {source.name}, 备份: {backup_name}")
            
            return {
                'success': True,
                'message': '文件备份创建成功',
                'backup_path': str(backup_path),
                'original_path': str(source)
            }
            
        except Exception as e:
            log_system_event("文件备份错误", f"文件: {file_path}, 错误: {str(e)}")
            return {
                'success': False,
                'message': f'文件备份失败: {str(e)}'
            }
    
    def create_temp_file(self, content: bytes, 
                        filename_prefix: str = "temp") -> Dict[str, Any]:
        """
        创建临时文件
        
        Args:
            content (bytes): 文件内容
            filename_prefix (str): 文件名前缀
            
        Returns:
            Dict[str, Any]: 创建结果
        """
        try:
            # 生成临时文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            temp_filename = f"{filename_prefix}_{timestamp}.tmp"
            temp_path = self.temp_dir / temp_filename
            
            # 写入临时文件
            with open(temp_path, 'wb') as f:
                f.write(content)
            
            log_system_event("创建临时文件", f"文件: {temp_filename}, 大小: {format_file_size(len(content))}")
            
            return {
                'success': True,
                'temp_path': str(temp_path),
                'filename': temp_filename,
                'file_size': len(content),
                'created_at': datetime.now()
            }
            
        except Exception as e:
            log_system_event("临时文件创建错误", f"错误: {str(e)}")
            return {
                'success': False,
                'message': f'临时文件创建失败: {str(e)}'
            }
    
    def cleanup_temp_files(self) -> Dict[str, Any]:
        """
        清理过期的临时文件
        
        Returns:
            Dict[str, Any]: 清理结果
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=TEMP_FILE_RETENTION_HOURS)
            deleted_count = 0
            total_size = 0
            
            # 扫描临时目录
            for temp_file in self.temp_dir.glob("*.tmp"):
                try:
                    file_time = datetime.fromtimestamp(temp_file.stat().st_mtime)
                    
                    if file_time < cutoff_time:
                        file_size = temp_file.stat().st_size
                        os.remove(temp_file)
                        deleted_count += 1
                        total_size += file_size
                        
                except Exception as e:
                    log_system_event("临时文件删除错误", f"文件: {temp_file.name}, 错误: {str(e)}")
            
            if deleted_count > 0:
                log_system_event("临时文件清理", 
                               f"删除了{deleted_count}个文件，释放空间: {format_file_size(total_size)}")
            
            return {
                'success': True,
                'deleted_count': deleted_count,
                'freed_space': total_size,
                'freed_space_formatted': format_file_size(total_size)
            }
            
        except Exception as e:
            log_system_event("临时文件清理错误", f"错误: {str(e)}")
            return {
                'success': False,
                'message': f'临时文件清理失败: {str(e)}'
            }
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        获取文件信息
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            Optional[Dict[str, Any]]: 文件信息
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return None
            
            stat = path.stat()
            file_hash = calculate_file_hash(str(path))
            
            return {
                'filename': path.name,
                'file_path': str(path),
                'file_size': stat.st_size,
                'file_size_formatted': format_file_size(stat.st_size),
                'file_hash': file_hash,
                'created_at': datetime.fromtimestamp(stat.st_ctime),
                'modified_at': datetime.fromtimestamp(stat.st_mtime),
                'is_file': path.is_file(),
                'is_directory': path.is_dir(),
                'extension': path.suffix.lower()
            }
            
        except Exception as e:
            log_system_event("文件信息获取错误", f"文件: {file_path}, 错误: {str(e)}")
            return None
    
    def list_files(self, directory: str = "", pattern: str = "*") -> List[Dict[str, Any]]:
        """
        列出目录中的文件
        
        Args:
            directory (str): 目录路径（相对于数据目录）
            pattern (str): 文件匹配模式
            
        Returns:
            List[Dict[str, Any]]: 文件列表
        """
        try:
            if directory:
                target_dir = self.data_dir / directory
            else:
                target_dir = self.data_dir
            
            if not target_dir.exists():
                return []
            
            files = []
            for file_path in target_dir.glob(pattern):
                if file_path.is_file():
                    file_info = self.get_file_info(str(file_path))
                    if file_info:
                        files.append(file_info)
            
            # 按修改时间排序（最新的在前）
            files.sort(key=lambda x: x['modified_at'], reverse=True)
            
            return files
            
        except Exception as e:
            log_system_event("文件列表获取错误", f"目录: {directory}, 错误: {str(e)}")
            return []
    
    def get_directory_size(self, directory: str = "") -> Dict[str, Any]:
        """
        获取目录大小
        
        Args:
            directory (str): 目录路径（相对于数据目录）
            
        Returns:
            Dict[str, Any]: 目录大小信息
        """
        try:
            if directory:
                target_dir = self.data_dir / directory
            else:
                target_dir = self.data_dir
            
            if not target_dir.exists():
                return {
                    'success': False,
                    'message': '目录不存在'
                }
            
            total_size = 0
            file_count = 0
            
            for file_path in target_dir.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
            
            return {
                'success': True,
                'directory': str(target_dir),
                'total_size': total_size,
                'total_size_formatted': format_file_size(total_size),
                'file_count': file_count
            }
            
        except Exception as e:
            log_system_event("目录大小计算错误", f"目录: {directory}, 错误: {str(e)}")
            return {
                'success': False,
                'message': f'目录大小计算失败: {str(e)}'
            }
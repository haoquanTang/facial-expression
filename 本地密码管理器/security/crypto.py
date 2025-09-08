#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加密服务模块

提供AES加密解密功能，确保密码数据的安全存储
"""

import os
import base64
import hashlib
from typing import Optional
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256


class CryptoService:
    """
    加密服务类
    
    提供密码加密、解密和主密码验证功能
    """
    
    def __init__(self):
        """
        初始化加密服务
        """
        self.key_length = 32  # AES-256
        self.iv_length = 16   # AES块大小
        self.salt_length = 32 # 盐值长度
        self.iterations = 100000  # PBKDF2迭代次数
    
    def generate_salt(self) -> bytes:
        """
        生成随机盐值
        
        Returns:
            bytes: 32字节的随机盐值
        """
        return get_random_bytes(self.salt_length)
    
    def derive_key(self, password: str, salt: bytes) -> bytes:
        """
        从密码和盐值派生加密密钥
        
        Args:
            password (str): 主密码
            salt (bytes): 盐值
            
        Returns:
            bytes: 派生的32字节密钥
        """
        return PBKDF2(
            password.encode('utf-8'),
            salt,
            self.key_length,
            count=self.iterations,
            hmac_hash_module=SHA256
        )
    
    def encrypt_data(self, data: str, password: str, salt: bytes = None) -> dict:
        """
        加密数据
        
        Args:
            data (str): 要加密的数据
            password (str): 加密密码
            salt (bytes, optional): 盐值，如果为None则自动生成
            
        Returns:
            dict: 包含加密数据、盐值和IV的字典
        """
        if salt is None:
            salt = self.generate_salt()
        
        # 派生密钥
        key = self.derive_key(password, salt)
        
        # 生成随机IV
        iv = get_random_bytes(self.iv_length)
        
        # 创建AES加密器
        cipher = AES.new(key, AES.MODE_CBC, iv)
        
        # 填充数据到块大小的倍数
        padded_data = self._pad_data(data.encode('utf-8'))
        
        # 加密数据
        encrypted_data = cipher.encrypt(padded_data)
        
        return {
            'encrypted_data': base64.b64encode(encrypted_data).decode('utf-8'),
            'salt': base64.b64encode(salt).decode('utf-8'),
            'iv': base64.b64encode(iv).decode('utf-8')
        }
    
    def decrypt_data(self, encrypted_info: dict, password: str) -> Optional[str]:
        """
        解密数据
        
        Args:
            encrypted_info (dict): 包含加密数据、盐值和IV的字典
            password (str): 解密密码
            
        Returns:
            Optional[str]: 解密后的数据，解密失败返回None
        """
        try:
            # 解码base64数据
            encrypted_data = base64.b64decode(encrypted_info['encrypted_data'])
            salt = base64.b64decode(encrypted_info['salt'])
            iv = base64.b64decode(encrypted_info['iv'])
            
            # 派生密钥
            key = self.derive_key(password, salt)
            
            # 创建AES解密器
            cipher = AES.new(key, AES.MODE_CBC, iv)
            
            # 解密数据
            decrypted_data = cipher.decrypt(encrypted_data)
            
            # 去除填充
            unpadded_data = self._unpad_data(decrypted_data)
            
            return unpadded_data.decode('utf-8')
            
        except Exception:
            return None
    
    def hash_password(self, password: str, salt: bytes = None) -> dict:
        """
        哈希密码用于存储
        
        Args:
            password (str): 要哈希的密码
            salt (bytes, optional): 盐值，如果为None则自动生成
            
        Returns:
            dict: 包含密码哈希和盐值的字典
        """
        if salt is None:
            salt = self.generate_salt()
        
        # 使用PBKDF2哈希密码
        password_hash = PBKDF2(
            password.encode('utf-8'),
            salt,
            self.key_length,
            count=self.iterations,
            hmac_hash_module=SHA256
        )
        
        return {
            'hash': base64.b64encode(password_hash).decode('utf-8'),
            'salt': base64.b64encode(salt).decode('utf-8')
        }
    
    def verify_password(self, password: str, stored_hash: str, salt: str) -> bool:
        """
        验证密码
        
        Args:
            password (str): 要验证的密码
            stored_hash (str): 存储的密码哈希
            salt (str): 盐值
            
        Returns:
            bool: 密码是否正确
        """
        try:
            # 解码盐值
            salt_bytes = base64.b64decode(salt)
            
            # 计算输入密码的哈希
            password_hash = PBKDF2(
                password.encode('utf-8'),
                salt_bytes,
                self.key_length,
                count=self.iterations,
                hmac_hash_module=SHA256
            )
            
            # 比较哈希值
            computed_hash = base64.b64encode(password_hash).decode('utf-8')
            return computed_hash == stored_hash
            
        except Exception:
            return False
    
    def _pad_data(self, data: bytes) -> bytes:
        """
        使用PKCS7填充数据
        
        Args:
            data (bytes): 要填充的数据
            
        Returns:
            bytes: 填充后的数据
        """
        padding_length = AES.block_size - (len(data) % AES.block_size)
        padding = bytes([padding_length] * padding_length)
        return data + padding
    
    def _unpad_data(self, data: bytes) -> bytes:
        """
        去除PKCS7填充
        
        Args:
            data (bytes): 填充的数据
            
        Returns:
            bytes: 去除填充后的数据
        """
        padding_length = data[-1]
        return data[:-padding_length]
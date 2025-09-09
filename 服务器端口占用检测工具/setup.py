#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器端口占用检测工具 - 安装脚本

用于项目的安装、打包和分发。
"""

from setuptools import setup, find_packages
import os
from pathlib import Path

# 读取README文件
this_directory = Path(__file__).parent
long_description = ""
try:
    readme_file = this_directory / "README.md"
    if readme_file.exists():
        long_description = readme_file.read_text(encoding='utf-8')
except Exception:
    long_description = "服务器端口占用检测工具 - 一款功能强大的端口扫描和进程管理工具"

# 读取requirements.txt
requirements = []
try:
    req_file = this_directory / "requirements.txt"
    if req_file.exists():
        with open(req_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if line and not line.startswith('#'):
                    requirements.append(line)
except Exception:
    # 如果读取失败，使用默认依赖
    requirements = [
        'psutil>=5.8.0',
        'paramiko>=2.7.0'
    ]

# 项目信息
setup(
    # 基本信息
    name="port-scanner-tool",
    version="1.0.0",
    author="Port Scanner Team",
    author_email="support@portscanner.com",
    description="服务器端口占用检测工具 - 端口扫描和进程管理",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/port-scanner-tool",
    
    # 包信息
    packages=find_packages(),
    package_dir={'': '.'},
    
    # 包含的文件
    package_data={
        'src': ['*.py'],
        'config': ['*.json'],
        'docs': ['*.md'],
    },
    
    # 依赖
    install_requires=requirements,
    
    # 可选依赖
    extras_require={
        'dev': [
            'pytest>=6.0.0',
            'pytest-cov>=2.10.0',
            'black>=21.0.0',
            'flake8>=3.8.0',
            'mypy>=0.800',
        ],
        'build': [
            'pyinstaller>=4.0',
            'setuptools>=50.0.0',
            'wheel>=0.36.0',
        ]
    },
    
    # 命令行入口
    entry_points={
        'console_scripts': [
            'port-scanner=src.main:main',
            'port-scan=src.main:main',
        ],
    },
    
    # 分类信息
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Networking :: Monitoring",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    
    # Python版本要求
    python_requires=">=3.8",
    
    # 关键词
    keywords="port scanner network monitoring process management ssh remote",
    
    # 项目URL
    project_urls={
        "Bug Reports": "https://github.com/your-username/port-scanner-tool/issues",
        "Source": "https://github.com/your-username/port-scanner-tool",
        "Documentation": "https://github.com/your-username/port-scanner-tool/wiki",
    },
    
    # 许可证
    license="MIT",
    
    # 是否包含数据文件
    include_package_data=True,
    
    # zip安全
    zip_safe=False,
)
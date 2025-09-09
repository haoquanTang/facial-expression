# 服务器端口占用检测工具 Makefile

.PHONY: help install test clean run-gui run-cli build package dev-setup lint format check-deps

# 默认目标
help:
	@echo "服务器端口占用检测工具 - 可用命令:"
	@echo ""
	@echo "  install      - 安装项目依赖"
	@echo "  test         - 运行所有测试"
	@echo "  test-verbose - 运行详细测试"
	@echo "  clean        - 清理临时文件"
	@echo "  run-gui      - 启动GUI模式"
	@echo "  run-cli      - 启动命令行模式(扫描常用端口)"
	@echo "  build        - 构建项目"
	@echo "  package      - 打包项目"
	@echo "  dev-setup    - 开发环境设置"
	@echo "  lint         - 代码检查"
	@echo "  format       - 代码格式化"
	@echo "  check-deps   - 检查依赖"
	@echo "  demo         - 运行演示"
	@echo ""

# 安装依赖
install:
	@echo "安装项目依赖..."
	pip install -r requirements.txt
	@echo "依赖安装完成!"

# 运行测试
test:
	@echo "运行测试套件..."
	python tests/run_tests.py

test-verbose:
	@echo "运行详细测试..."
	python tests/run_tests.py --no-deps-check
	python -m unittest discover -s tests -p "test_*.py" -v

# 清理临时文件
clean:
	@echo "清理临时文件..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/
	@echo "清理完成!"

# 启动GUI模式
run-gui:
	@echo "启动GUI模式..."
	python src/main.py --gui

# 启动命令行模式
run-cli:
	@echo "启动命令行模式 - 扫描常用端口..."
	python src/main.py --ports "22,80,443,3306,5432,6379,8080,9000" --output table

# 演示扫描
demo:
	@echo "演示端口扫描功能..."
	@echo "1. 扫描本地常用端口:"
	python src/main.py --ports "22,80,443,8080" --output table --timeout 2
	@echo ""
	@echo "2. 扫描端口范围:"
	python src/main.py --ports "8000-8005" --output json --timeout 1
	@echo ""
	@echo "3. 显示帮助信息:"
	python src/main.py --help

# 构建项目
build:
	@echo "构建项目..."
	python setup.py build
	@echo "构建完成!"

# 打包项目
package:
	@echo "打包项目..."
	python setup.py sdist bdist_wheel
	@echo "打包完成! 查看 dist/ 目录"

# 开发环境设置
dev-setup: install
	@echo "设置开发环境..."
	@echo "创建必要的目录..."
	mkdir -p logs
	mkdir -p output
	@echo "开发环境设置完成!"

# 代码检查 (如果安装了flake8)
lint:
	@echo "运行代码检查..."
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 src/ tests/ --max-line-length=100 --ignore=E501,W503; \
	else \
		echo "flake8 未安装，跳过代码检查"; \
		echo "安装: pip install flake8"; \
	fi

# 代码格式化 (如果安装了black)
format:
	@echo "格式化代码..."
	@if command -v black >/dev/null 2>&1; then \
		black src/ tests/ --line-length=100; \
	else \
		echo "black 未安装，跳过代码格式化"; \
		echo "安装: pip install black"; \
	fi

# 检查依赖
check-deps:
	@echo "检查项目依赖..."
	python tests/run_tests.py --check-deps

# 安装开发依赖
install-dev:
	@echo "安装开发依赖..."
	pip install flake8 black pytest pytest-cov
	@echo "开发依赖安装完成!"

# 运行覆盖率测试
test-coverage:
	@echo "运行测试覆盖率分析..."
	@if command -v pytest >/dev/null 2>&1; then \
		pytest tests/ --cov=src --cov-report=html --cov-report=term; \
		echo "覆盖率报告生成在 htmlcov/ 目录"; \
	else \
		echo "pytest 未安装，使用基本测试"; \
		make test; \
	fi

# 快速开始
quick-start: dev-setup test
	@echo ""
	@echo "🎉 项目设置完成!"
	@echo ""
	@echo "快速使用:"
	@echo "  make run-gui    # 启动图形界面"
	@echo "  make run-cli    # 命令行扫描"
	@echo "  make demo       # 查看演示"
	@echo ""

# 项目信息
info:
	@echo "项目信息:"
	@echo "  名称: 服务器端口占用检测工具"
	@echo "  版本: 1.0.0"
	@echo "  Python: $(shell python --version)"
	@echo "  目录: $(shell pwd)"
	@echo "  文件数: $(shell find src/ -name '*.py' | wc -l) Python文件"
	@echo "  代码行数: $(shell find src/ -name '*.py' -exec wc -l {} + | tail
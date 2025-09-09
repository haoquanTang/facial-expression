#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试运行脚本

运行所有测试用例并生成测试报告。
"""

import unittest
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_all_tests():
    """运行所有测试用例"""
    print("="*60)
    print("服务器端口占用检测工具 - 测试套件")
    print("="*60)
    
    # 发现并运行所有测试
    test_dir = Path(__file__).parent
    loader = unittest.TestLoader()
    
    # 加载所有测试模块
    test_suite = unittest.TestSuite()
    
    # 手动添加测试模块
    test_modules = [
        'test_scanner',
        'test_process_manager'
    ]
    
    for module_name in test_modules:
        try:
            module = __import__(module_name)
            suite = loader.loadTestsFromModule(module)
            test_suite.addTest(suite)
            print(f"✓ 加载测试模块: {module_name}")
        except ImportError as e:
            print(f"✗ 无法加载测试模块 {module_name}: {e}")
    
    print("\n" + "-"*60)
    print("开始运行测试...")
    print("-"*60)
    
    # 运行测试
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True,
        failfast=False
    )
    
    result = runner.run(test_suite)
    
    # 输出测试结果摘要
    print("\n" + "="*60)
    print("测试结果摘要")
    print("="*60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
    success = total_tests - failures - errors - skipped
    
    print(f"总测试数: {total_tests}")
    print(f"成功: {success}")
    print(f"失败: {failures}")
    print(f"错误: {errors}")
    print(f"跳过: {skipped}")
    
    if failures > 0:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('\n')[-2] if traceback else 'Unknown'}")
    
    if errors > 0:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('\n')[-2] if traceback else 'Unknown'}")
    
    # 计算成功率
    if total_tests > 0:
        success_rate = (success / total_tests) * 100
        print(f"\n成功率: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("🎉 所有测试通过！")
        elif success_rate >= 80:
            print("✅ 大部分测试通过")
        else:
            print("⚠️  需要修复失败的测试")
    
    print("="*60)
    
    return result.wasSuccessful()


def run_specific_test(test_name):
    """运行特定的测试"""
    print(f"运行特定测试: {test_name}")
    
    try:
        # 加载特定测试
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(test_name)
        
        # 运行测试
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result.wasSuccessful()
    
    except Exception as e:
        print(f"运行测试时出错: {e}")
        return False


def check_dependencies():
    """检查测试依赖"""
    print("检查测试依赖...")
    
    required_modules = ['psutil', 'paramiko']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError:
            print(f"✗ {module} (缺失)")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n⚠️  缺少依赖模块: {', '.join(missing_modules)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    print("✅ 所有依赖模块已安装")
    return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='运行端口扫描工具测试')
    parser.add_argument(
        '--test', '-t',
        help='运行特定测试 (例如: test_scanner.TestPortScanner.test_scan_config_creation)'
    )
    parser.add_argument(
        '--check-deps', '-c',
        action='store_true',
        help='只检查依赖，不运行测试'
    )
    parser.add_argument(
        '--no-deps-check',
        action='store_true',
        help='跳过依赖检查'
    )
    
    args = parser.parse_args()
    
    # 检查依赖
    if args.check_deps:
        check_dependencies()
        return
    
    if not args.no_deps_check:
        if not check_dependencies():
            print("\n依赖检查失败，退出测试")
            sys.exit(1)
        print()
    
    # 运行测试
    if args.test:
        success = run_specific_test(args.test)
    else:
        success = run_all_tests()
    
    # 设置退出代码
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
#!/usr/bin/env python
"""情感地图应用启动器 - 统一入口点"""
import os
import sys
import argparse
import subprocess
import logging
import time
import platform
from typing import Dict, Any, List

def setup_environment():
    """设置环境变量以抑制不必要的警告和日志"""
    # 抑制TensorFlow和其他库的警告
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
    os.environ["PYTHONWARNINGS"] = "ignore"
    
    # 抑制Selenium WebDriver的日志
    selenium_logger = logging.getLogger('selenium')
    selenium_logger.setLevel(logging.CRITICAL)
    
    # 抑制urllib3的日志
    urllib3_logger = logging.getLogger('urllib3')
    urllib3_logger.setLevel(logging.CRITICAL)
    
    # 抑制WebDriver Manager的日志
    wdm_logger = logging.getLogger('WDM')
    wdm_logger.setLevel(logging.CRITICAL)
    
    # 设置Chrome浏览器选项为环境变量
    os.environ["CHROME_BROWSER_FLAGS"] = "--log-level=3 --disable-logging --disable-dev-shm-usage --no-sandbox --disable-gpu --disable-extensions --disable-software-rasterizer --headless --enable-unsafe-swiftshader"

def run_web_app(debug=False):
    """运行Web应用"""
    print("正在启动中国社交媒体情绪地图...")
    print("\n当Web应用启动后，请访问: http://localhost:8501\n")
    
    # 设置streamlit命令行参数
    cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.headless", "true",
        "--browser.serverAddress", "localhost",
        "--server.port", "8501",
        "--logger.level", "error" if not debug else "info"
    ]
    
    try:
        # 在新进程中运行，捕获输出
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # 显示有限的启动信息
        for line in process.stdout:
            if "You can now view your Streamlit app in your browser" in line:
                print("✓ 应用已成功启动！")
            elif "Local URL:" in line:
                print(f"✓ {line.strip()}")
            elif "Network URL:" in line:
                print(f"✓ {line.strip()}")
                break
        
        print("\n应用正在运行中，按 Ctrl+C 停止...\n")
        
        # 等待用户中断
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n正在关闭应用...")
            process.terminate()
            print("应用已关闭！")
    except Exception as e:
        print(f"启动Web应用时出错: {str(e)}")
        return False
        
    return True

def run_cli_app(args):
    """运行命令行应用"""
    print("正在运行情感分析...")
    
    # 构建命令行参数
    cmd = [sys.executable, "main.py"]
    
    # 添加参数
    if args.keyword:
        cmd.extend(["--keyword", args.keyword])
    if args.platforms:
        cmd.extend(["--platforms", args.platforms])
    if args.limit:
        cmd.extend(["--limit", str(args.limit)])
    if args.domain:
        cmd.extend(["--domain", args.domain])
    if args.output:
        cmd.extend(["--output", args.output])
    
    # 执行命令
    try:
        process = subprocess.run(cmd, check=True)
        return process.returncode == 0
    except subprocess.CalledProcessError:
        return False
    except Exception as e:
        print(f"运行命令行应用时出错: {str(e)}")
        return False

def show_browser_warning():
    """显示浏览器WebGL警告解决方法"""
    print("\n注意: 若在浏览器中看到WebGL错误，可尝试以下解决方法:")
    print("1. 使用Chrome浏览器的最新版本")
    print("2. 在Chrome地址栏输入: chrome://flags")
    print("3. 搜索并启用: 'Override software rendering list'")
    print("4. 重启浏览器后访问应用\n")

def main():
    """主入口函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="中国社交媒体情绪地图")
    parser.add_argument("--cli", action="store_true", help="使用命令行模式")
    parser.add_argument("--gui", action="store_true", help="使用图形界面模式")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    
    # CLI模式参数
    parser.add_argument("--keyword", type=str, help="搜索关键词")
    parser.add_argument("--platforms", type=str, help="数据来源平台，逗号分隔")
    parser.add_argument("--limit", type=int, help="每个平台的数据条数限制")
    parser.add_argument("--domain", type=str, help="情感分析领域")
    parser.add_argument("--output", type=str, help="输出目录")
    
    args = parser.parse_args()
    
    # 设置环境
    setup_environment()
    
    # 根据参数选择运行模式
    if args.cli:
        if not args.keyword:
            print("错误: CLI模式必须提供--keyword参数")
            return 1
        success = run_cli_app(args)
    else:
        # 默认运行Web应用
        show_browser_warning()
        success = run_web_app(args.debug)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

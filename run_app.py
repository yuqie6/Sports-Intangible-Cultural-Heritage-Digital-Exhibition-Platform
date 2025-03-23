"""静音启动Streamlit应用"""
import os
import sys
import subprocess

def run_streamlit_silent():
    """以静音模式运行Streamlit应用"""
    print("正在启动中国社交媒体情绪地图...\n")
    
    # 设置环境变量以隐藏警告
    os.environ["PYTHONWARNINGS"] = "ignore"
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # 隐藏TensorFlow警告
    
    # 创建启动命令
    cmd = [sys.executable, "-m", "streamlit", "run", "app.py"]
    
    # 添加Streamlit的静默选项
    cmd.extend(["--logger.level", "error"])
    
    # 打印访问信息
    print("应用启动后，请访问: http://localhost:8501\n")
    print("要停止应用，请按 Ctrl+C\n")
    
    try:
        # Windows上使用subprocess替代方案
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # 只显示有用的输出
        for line in process.stdout:
            if "You can now view your Streamlit app in your browser" in line:
                print("应用已成功启动！")
            elif "Local URL:" in line or "Network URL:" in line:
                print(line.strip())
        
        process.wait()
    except KeyboardInterrupt:
        print("\n应用已停止")
    except Exception as e:
        print(f"启动过程中出错: {str(e)}")

if __name__ == "__main__":
    run_streamlit_silent()

"""图形界面启动器"""
import sys
import os
import subprocess
import threading
import time
import signal
import platform

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
except ImportError:
    print("错误: 缺少tkinter库，请安装后再试。")
    sys.exit(1)

class StdoutRedirector:
    """重定向标准输出到文本框"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = ""
        
    def write(self, string):
        self.buffer += string
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
        
    def flush(self):
        pass

class AppLauncher:
    """情感地图应用启动器GUI"""
    
    def __init__(self, root):
        """初始化GUI"""
        self.root = root
        root.title("中国社交媒体情绪地图 - 启动器")
        root.geometry("680x520")
        root.resizable(True, True)
        
        self.process = None
        self.running = False
        
        # 设置样式
        style = ttk.Style()
        style.configure('TButton', padding=6)
        style.configure('TLabel', padding=6)
        
        # 创建主框架
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 模式选择
        mode_frame = ttk.LabelFrame(main_frame, text="运行模式", padding="10")
        mode_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.mode_var = tk.StringVar(value="web")
        ttk.Radiobutton(mode_frame, text="Web应用", variable=self.mode_var, value="web").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="命令行模式", variable=self.mode_var, value="cli").pack(side=tk.LEFT, padx=5)
        
        # 参数框架 - CLI模式
        self.cli_frame = ttk.LabelFrame(main_frame, text="命令行参数", padding="10")
        self.cli_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 关键词
        keyword_frame = ttk.Frame(self.cli_frame)
        keyword_frame.pack(fill=tk.X, pady=2)
        ttk.Label(keyword_frame, text="关键词:").pack(side=tk.LEFT)
        self.keyword_var = tk.StringVar()
        ttk.Entry(keyword_frame, textvariable=self.keyword_var).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 平台
        platforms_frame = ttk.Frame(self.cli_frame)
        platforms_frame.pack(fill=tk.X, pady=2)
        ttk.Label(platforms_frame, text="平台:").pack(side=tk.LEFT)
        self.platforms_var = tk.StringVar(value="zhihu,xiaohongshu")
        ttk.Entry(platforms_frame, textvariable=self.platforms_var).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 每平台数据量
        limit_frame = ttk.Frame(self.cli_frame)
        limit_frame.pack(fill=tk.X, pady=2)
        ttk.Label(limit_frame, text="数据量:").pack(side=tk.LEFT)
        self.limit_var = tk.StringVar(value="100")
        ttk.Entry(limit_frame, textvariable=self.limit_var).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 领域
        domain_frame = ttk.Frame(self.cli_frame)
        domain_frame.pack(fill=tk.X, pady=2)
        ttk.Label(domain_frame, text="领域:").pack(side=tk.LEFT)
        self.domain_var = tk.StringVar(value="general")
        ttk.Entry(domain_frame, textvariable=self.domain_var).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 输出目录
        output_frame = ttk.Frame(self.cli_frame)
        output_frame.pack(fill=tk.X, pady=2)
        ttk.Label(output_frame, text="输出目录:").pack(side=tk.LEFT)
        self.output_var = tk.StringVar(value="output")
        ttk.Entry(output_frame, textvariable=self.output_var).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 控制选项
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 调试模式
        self.debug_var = tk.BooleanVar()
        ttk.Checkbutton(control_frame, text="调试模式", variable=self.debug_var).pack(side=tk.LEFT, padx=5)
        
        # 按钮
        self.start_button = ttk.Button(control_frame, text="启动应用", command=self.start_app)
        self.start_button.pack(side=tk.RIGHT, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="停止应用", command=self.stop_app, state=tk.DISABLED)
        self.stop_button.pack(side=tk.RIGHT, padx=5)
        
        # 输出框
        output_frame = ttk.LabelFrame(main_frame, text="输出", padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, width=80, height=15)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, padx=5, pady=5)
        
        # 重定向输出
        self.stdout_redirector = StdoutRedirector(self.output_text)
        
        # 绑定窗口关闭事件
        root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 监听模式变化
        self.mode_var.trace_add("write", self.on_mode_change)
        self.on_mode_change()
    
    def on_mode_change(self, *args):
        """处理模式变化"""
        mode = self.mode_var.get()
        if mode == "web":
            self.cli_frame.pack_forget()
        else:
            self.cli_frame.pack(fill=tk.X, padx=5, pady=5, after=self.root.nametowidget(self.cli_frame.master).children['!labelframe'])
    
    def start_app(self):
        """启动应用"""
        if self.running:
            messagebox.showerror("错误", "应用已在运行中")
            return
        
        mode = self.mode_var.get()
        debug = self.debug_var.get()
        
        # 清空输出框
        self.output_text.delete(1.0, tk.END)
        
        # 构建命令
        if mode == "web":
            cmd = [sys.executable, "sentiment_map.py"]
            if debug:
                cmd.append("--debug")
        else:
            # CLI模式
            cmd = [sys.executable, "sentiment_map.py", "--cli"]
            
            # 添加关键词
            keyword = self.keyword_var.get().strip()
            if not keyword:
                messagebox.showerror("错误", "CLI模式必须提供关键词")
                return
            cmd.extend(["--keyword", keyword])
            
            # 添加其他参数
            platforms = self.platforms_var.get().strip()
            if platforms:
                cmd.extend(["--platforms", platforms])
                
            limit = self.limit_var.get().strip()
            if limit and limit.isdigit():
                cmd.extend(["--limit", limit])
                
            domain = self.domain_var.get().strip()
            if domain:
                cmd.extend(["--domain", domain])
                
            output = self.output_var.get().strip()
            if output:
                cmd.extend(["--output", output])
                
            if debug:
                cmd.append("--debug")
        
        # 显示命令
        self.output_text.insert(tk.END, f"执行命令: {' '.join(cmd)}\n\n")
        
        # 更新状态
        self.running = True
        self.status_var.set("正在运行...")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # 在新线程中启动进程
        threading.Thread(target=self._run_process, args=(cmd,), daemon=True).start()
    
    def _run_process(self, cmd):
        """在线程中运行进程"""
        try:
            # 保存原始输出流
            old_stdout = sys.stdout
            
            # 重定向输出到文本框
            sys.stdout = self.stdout_redirector
            
            # 启动进程
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # 读取输出
            for line in self.process.stdout:
                self.output_text.insert(tk.END, line)
                self.output_text.see(tk.END)
            
            # 等待进程结束
            self.process.wait()
            
            # 恢复输出流
            sys.stdout = old_stdout
            
            # 更新UI
            self.root.after(0, self._process_finished)
            
        except Exception as e:
            self.output_text.insert(tk.END, f"错误: {str(e)}\n")
            self.root.after(0, self._process_finished)
    
    def _process_finished(self):
        """处理进程结束"""
        self.running = False
        self.process = None
        self.status_var.set("已完成")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
    
    def stop_app(self):
        """停止应用"""
        if not self.running or not self.process:
            return
            
        # 尝试终止进程
        try:
            if platform.system() == "Windows":
                # Windows
                self.process.terminate()
            else:
                # Unix/Linux/Mac
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            
            # 等待进程结束
            for _ in range(5):  # 最多等待5秒
                if self.process.poll() is not None:
                    break
                time.sleep(1)
                
            # 如果进程仍在运行，强制终止
            if self.process.poll() is None:
                if platform.system() == "Windows":
                    self.process.kill()
                else:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
            
            self.output_text.insert(tk.END, "\n应用已停止\n")
        except Exception as e:
            self.output_text.insert(tk.END, f"\n停止应用时出错: {str(e)}\n")
        
        # 更新状态
        self._process_finished()
    
    def on_closing(self):
        """处理窗口关闭事件"""
        if self.running:
            if messagebox.askyesno("确认", "应用正在运行，确定要退出吗？"):
                self.stop_app()
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    """主函数"""
    root = tk.Tk()
    app = AppLauncher(root)
    root.mainloop()

if __name__ == "__main__":
    main()

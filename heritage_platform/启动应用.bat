@echo off
chcp 65001
echo 正在启动体育非遗数字展示平台...

:: 设置环境变量
set FLASK_APP=run.py
set FLASK_CONFIG=development
set FLASK_DEBUG=1
set PORT=5000
set DB_PASSWORD=qB645522153
set PYTHONIOENCODING=utf-8

echo 环境已设置，正在启动Flask应用...
echo 应用将在 http://127.0.0.1:5000/ 运行

:: 启动应用
python -X utf8 run.py

:: 如果应用异常退出，等待用户确认
if %errorlevel% neq 0 (
    echo 应用异常退出，错误代码: %errorlevel%
    pause
)

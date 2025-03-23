@echo off
echo 正在启动中国社交媒体情绪地图...

REM 检查是否有tkinter库
python -c "import tkinter" 2>nul
if %ERRORLEVEL% EQU 0 (
    REM 使用GUI启动器
    start pythonw gui_launcher.py
) else (
    REM 使用命令行启动器
    python sentiment_map.py
)
pause

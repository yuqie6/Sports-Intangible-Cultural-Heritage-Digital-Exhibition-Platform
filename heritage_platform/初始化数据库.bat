@echo off
chcp 65001
echo 正在初始化数据库...

:: 设置环境变量
set DB_PASSWORD=qB645522153
set PYTHONIOENCODING=utf-8

echo 正在运行初始化脚本...
python -X utf8 init_db.py

if %errorlevel% neq 0 (
    echo 初始化过程中发生错误！
    echo 请检查错误信息并修复问题。
) else (
    echo 数据库初始化成功完成！
)

pause

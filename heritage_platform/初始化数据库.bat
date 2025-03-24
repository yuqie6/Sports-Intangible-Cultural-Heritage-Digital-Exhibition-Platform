@echo off
call conda activate heritage_env
python init_db.py
echo 数据库初始化完成!
pause

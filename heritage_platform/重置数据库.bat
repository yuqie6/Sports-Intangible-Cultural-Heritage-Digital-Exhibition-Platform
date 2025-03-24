@echo off
call conda activate heritage_env

echo 警告：这将删除所有数据库表并重新创建！
set /p confirm=确定要重置数据库吗？(y/n): 
if /i "%confirm%"=="y" (
    python -c "from app import db, create_app; app=create_app(); app.app_context().push(); db.drop_all(); print('所有表已删除')"
    python init_db.py
    echo 数据库已重置并初始化完成!
) else (
    echo 操作已取消
)
pause

@echo off
cd heritage_platform

REM 使用conda创建虚拟环境
call conda create -n heritage_env python=3.9 -y
call conda activate heritage_env

REM 安装必要依赖
call conda install -c conda-forge flask flask-login flask-sqlalchemy flask-wtf flask-migrate pymysql pillow -y
call pip install email_validator

REM 导出依赖
pip freeze > requirements.txt
echo 依赖安装完成！
pause

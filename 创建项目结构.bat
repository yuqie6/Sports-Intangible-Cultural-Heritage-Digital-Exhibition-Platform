@echo off
mkdir heritage_platform
cd heritage_platform
mkdir app
cd app
mkdir models routes templates static static\css static\js static\img static\uploads static\uploads\images static\uploads\videos forms utils
type nul > __init__.py
cd ..
type nul > config.py
type nul > run.py
type nul > requirements.txt
echo 项目结构创建完成！
pause

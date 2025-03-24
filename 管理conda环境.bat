@echo off
:menu
cls
echo ===================================
echo  体育非遗数字展示平台 - Conda环境管理
echo ===================================
echo.
echo  1. 创建并激活conda环境
echo  2. 激活已有conda环境
echo  3. 退出conda环境
echo  4. 删除conda环境(谨慎使用)
echo  5. 退出
echo.
set /p choice=请输入选项(1-5): 

if "%choice%"=="1" goto create
if "%choice%"=="2" goto activate
if "%choice%"=="3" goto deactivate
if "%choice%"=="4" goto remove
if "%choice%"=="5" goto end

echo 无效选项，请重新输入
timeout /t 2 >nul
goto menu

:create
echo 正在创建conda环境 heritage_env...
call conda create -n heritage_env python=3.9 -y
call conda activate heritage_env
echo conda环境 heritage_env 创建并激活成功！
pause
goto menu

:activate
echo 正在激活conda环境 heritage_env...
call conda activate heritage_env
echo conda环境 heritage_env 激活成功！
pause
goto menu

:deactivate
echo 正在退出当前conda环境...
call conda deactivate
echo 已退出conda环境！
pause
goto menu

:remove
echo 警告: 这将删除conda环境 heritage_env 及其所有包
set /p confirm=确定要删除环境吗？(y/n): 
if /i "%confirm%"=="y" (
    call conda env remove -n heritage_env
    echo conda环境 heritage_env 已删除！
) else (
    echo 操作已取消
)
pause
goto menu

:end
echo 感谢使用Conda环境管理工具
exit /b

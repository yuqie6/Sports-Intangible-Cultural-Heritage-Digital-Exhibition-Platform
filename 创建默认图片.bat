@echo off
echo 正在创建默认图片目录...
cd heritage_platform\app\static\img

echo 正在复制默认图片...
REM 创建简单的文本文件作为占位符
echo This is a placeholder image for heritage items > default-heritage.jpg
echo This is a placeholder image for content items > default-content.jpg
echo This is a placeholder image for video thumbnails > video-placeholder.jpg

echo 默认图片创建完成
pause

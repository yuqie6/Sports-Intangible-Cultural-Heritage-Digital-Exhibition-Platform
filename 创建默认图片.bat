@echo off
echo 正在创建默认图片...

python -c "from PIL import Image, ImageDraw; img = Image.new('RGB', (400, 300), color='lightgray'); draw = ImageDraw.Draw(img); draw.text((150, 140), '默认非遗图片', fill='darkgray', font=None); img.save('heritage_platform/app/static/img/default-heritage.jpg')"

python -c "from PIL import Image, ImageDraw; img = Image.new('RGB', (400, 300), color='lightgray'); draw = ImageDraw.Draw(img); draw.text((150, 140), '默认内容图片', fill='darkgray', font=None); img.save('heritage_platform/app/static/img/default-content.jpg')"

python -c "from PIL import Image, ImageDraw; img = Image.new('RGB', (400, 300), color='lightgray'); draw = ImageDraw.Draw(img); draw.text((150, 140), '视频占位图片', fill='darkgray', font=None); img.save('heritage_platform/app/static/img/video-placeholder.jpg')"

echo 默认图片创建成功！

pause

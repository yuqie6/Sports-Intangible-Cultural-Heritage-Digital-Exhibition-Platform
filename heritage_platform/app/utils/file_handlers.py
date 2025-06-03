"""
文件处理工具模块

本模块提供了一组用于处理上传文件的工具函数，主要功能包括：
1. 文件类型验证：验证文件扩展名和内容类型
2. 图片处理：压缩图片、添加水印
3. 文件存储：安全地保存上传的文件
4. 文件删除：删除已上传的文件

安全特性：
- 文件类型验证：检查扩展名和文件内容，防止恶意文件上传
- 安全文件名：使用secure_filename处理文件名，防止路径遍历攻击
- 唯一文件名：使用UUID生成唯一文件名，防止文件覆盖
- 异常处理：捕获并记录所有异常，确保应用稳定性
"""

import os
import uuid
import imghdr
import mimetypes
from PIL import Image, ImageDraw, ImageFont
from werkzeug.utils import secure_filename
from flask import current_app
from typing import Optional, Tuple, Union

# 允许上传的文件类型
# 图片类型：PNG、JPG、JPEG、GIF
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# 视频类型：MP4、MOV、AVI、WMV
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'wmv'}

def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """检查文件扩展名是否允许

    验证文件名是否包含扩展名，并且扩展名是否在允许列表中。
    扩展名比较时会转换为小写，确保大小写不敏感。

    Args:
        filename: 文件名，包含扩展名
        allowed_extensions: 允许的扩展名集合，如{'jpg', 'png'}

    Returns:
        bool: 如果文件扩展名允许则返回True，否则返回False

    示例:
        >>> allowed_file('image.jpg', {'jpg', 'png'})
        True
        >>> allowed_file('script.php', {'jpg', 'png'})
        False
        >>> allowed_file('noextension', {'jpg', 'png'})
        False
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def validate_image_content(file_storage) -> bool:
    """验证文件内容确实是图片

    Args:
        file_storage: FileStorage对象

    Returns:
        bool: 是否是有效的图片文件
    """
    try:
        # 保存临时文件进行验证
        temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp_' + str(uuid.uuid4()))
        file_storage.save(temp_path)

        # 使用imghdr验证图片
        image_type = imghdr.what(temp_path)

        # 使用mimetypes检查MIME类型
        mime_type, _ = mimetypes.guess_type(file_storage.filename)

        # 清理临时文件
        os.remove(temp_path)

        return (image_type is not None and
                mime_type is not None and
                mime_type.startswith('image/'))
    except Exception as e:
        current_app.logger.error(f"验证图片内容时出错: {str(e)}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False

def compress_image(image: Image, max_size: Tuple[int, int] = (800, 800)) -> Image:
    """压缩图片

    Args:
        image: PIL Image对象
        max_size: 最大尺寸

    Returns:
        PIL Image对象
    """
    # 调整大小
    image.thumbnail(max_size, Image.Resampling.LANCZOS)

    # 转换为RGB（确保JPEG兼容）
    if image.mode in ('RGBA', 'P'):
        image = image.convert('RGB')

    return image

def add_watermark(image: Image, text: str) -> Image:
    """添加文字水印

    Args:
        image: PIL Image对象
        text: 水印文字

    Returns:
        PIL Image对象
    """
    # 创建一个可以绘图的图层
    draw = ImageDraw.Draw(image)

    # 计算合适的字体大小
    width, height = image.size
    font_size = min(width, height) // 20

    try:
        # 尝试加载自定义字体，如果失败则使用默认字体
        font = ImageFont.truetype("simhei.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    # 计算文字大小和位置
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # 在右下角绘制水印
    x = width - text_width - 10
    y = height - text_height - 10

    # 绘制半透明背景
    draw.rectangle([x-5, y-5, x+text_width+5, y+text_height+5],
                  fill=(255, 255, 255, 128))

    # 绘制文字
    draw.text((x, y), text, fill=(0, 0, 0), font=font)

    return image

def save_file(file, file_type: str, watermark: Optional[str] = "体育非遗平台") -> Optional[str]:
    """保存上传的文件

    安全地处理和保存上传的文件，包括验证文件类型、处理文件名、
    压缩图片和添加水印（如果需要）。生成唯一文件名避免冲突。

    处理流程:
    1. 验证文件类型（扩展名和内容）
    2. 创建安全且唯一的文件名
    3. 确保目标目录存在
    4. 对图片进行处理（压缩和添加水印）
    5. 保存文件到目标位置

    Args:
        file: 文件对象，通常是request.files中的FileStorage对象
        file_type: 文件类型，可选值为'image'或'video'
        watermark: 水印文字，仅适用于图片，默认为"体育非遗平台"

    Returns:
        str or None: 保存成功返回相对于static目录的文件路径（如'uploads/images/xxx.jpg'），失败返回None

    安全措施:
    - 验证文件扩展名和内容类型
    - 使用secure_filename处理文件名
    - 生成随机UUID作为文件名前缀
    - 捕获并记录所有异常
    - 失败时清理部分写入的文件

    示例:
        >>> file_path = save_file(request.files['image'], 'image', '体育非遗平台')
        >>> if file_path:
        >>>     content.image_path = file_path
    """
    if not file:
        return None

    # 检查文件类型
    if file_type == 'image':
        allowed_extensions = ALLOWED_IMAGE_EXTENSIONS
        save_folder = 'images'
    elif file_type == 'video':
        allowed_extensions = ALLOWED_VIDEO_EXTENSIONS
        save_folder = 'videos'
    else:
        return None

    if not allowed_file(file.filename, allowed_extensions):
        current_app.logger.warning(f"不允许的文件类型: {file.filename}")
        return None

    # 对于图片，进行额外的内容验证
    if file_type == 'image' and not validate_image_content(file):
        current_app.logger.warning(f"无效的图片文件: {file.filename}")
        return None

    # 创建安全的文件名并保留扩展名
    filename = secure_filename(file.filename)
    if not filename:  # 如果secure_filename返回空字符串(如中文文件名)
        # 从原始文件名提取扩展名
        if '.' in file.filename:
            ext = file.filename.rsplit('.', 1)[1].lower()
            if ext in ALLOWED_IMAGE_EXTENSIONS or ext in ALLOWED_VIDEO_EXTENSIONS:
                filename = f"file_{uuid.uuid4().hex[:8]}.{ext}"
            else:
                filename = f"file_{uuid.uuid4().hex[:8]}"
        else:
            filename = f"file_{uuid.uuid4().hex[:8]}"
    else:
        # 确保文件名有扩展名
        if '.' not in filename:
            if '.' in file.filename:
                ext = file.filename.rsplit('.', 1)[1].lower()
                if ext in ALLOWED_IMAGE_EXTENSIONS or ext in ALLOWED_VIDEO_EXTENSIONS:
                    filename = f"{filename}.{ext}"

    unique_filename = f"{uuid.uuid4().hex}_{filename}"

    # 确保上传目录存在
    upload_path = os.path.join(
        current_app.root_path,
        'static/uploads',
        save_folder
    )
    os.makedirs(upload_path, exist_ok=True)

    # 保存文件
    file_path = os.path.join(upload_path, unique_filename)

    try:
        if file_type == 'image':
            # 处理图片
            with Image.open(file) as image:
                # 压缩图片
                image = compress_image(image)

                # 添加水印
                if watermark:
                    image = add_watermark(image, watermark)

                # 保存处理后的图片
                image.save(file_path, quality=85, optimize=True)
        else:
            # 直接保存视频文件
            file.save(file_path)

        current_app.logger.info(f"文件已保存: {file_path}")
        return f"uploads/{save_folder}/{unique_filename}"

    except Exception as e:
        current_app.logger.error(f"保存文件时出错: {str(e)}")
        # 如果保存失败，清理可能部分写入的文件
        if os.path.exists(file_path):
            os.remove(file_path)
        return None

def delete_file(file_path: str) -> bool:
    """删除文件

    Args:
        file_path: 文件相对路径（从uploads/开始）

    Returns:
        bool: 是否删除成功
    """
    try:
        full_path = os.path.join(current_app.root_path, 'static', file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            current_app.logger.info(f"文件已删除: {full_path}")
            return True
        return False
    except Exception as e:
        current_app.logger.error(f"删除文件时出错: {str(e)}")
        return False

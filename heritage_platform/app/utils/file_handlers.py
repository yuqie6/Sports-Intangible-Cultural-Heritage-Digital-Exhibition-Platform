import os
import uuid
import imghdr
import mimetypes
from PIL import Image, ImageDraw, ImageFont
from werkzeug.utils import secure_filename
from flask import current_app
from typing import Optional, Tuple, Union

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'wmv'}

def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """检查文件扩展名是否允许"""
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

def save_file(file, file_type: str, watermark: Optional[str] = None) -> Optional[str]:
    """保存上传的文件
    
    Args:
        file: 文件对象
        file_type: 文件类型('image' 或 'video')
        watermark: 可选的水印文字
        
    Returns:
        str or None: 保存成功返回文件路径，失败返回None
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
    
    # 创建安全的文件名
    filename = secure_filename(file.filename)
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

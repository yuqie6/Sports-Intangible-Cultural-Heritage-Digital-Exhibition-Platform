import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'wmv'}

def allowed_file(filename, allowed_extensions):
    """检查文件是否允许上传"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file(file, file_type):
    """保存上传的文件
    
    Args:
        file: 文件对象
        file_type: 文件类型('image' 或 'video')
        
    Returns:
        保存成功返回文件路径，失败返回None
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
    file.save(file_path)
    
    # 返回相对路径（用于数据库存储）
    return f"uploads/{save_folder}/{unique_filename}"

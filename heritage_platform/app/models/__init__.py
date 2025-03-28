from datetime import datetime, timedelta

def beijing_time():
    """返回北京时间（UTC+8）"""
    return datetime.utcnow() + timedelta(hours=8)

# 导入所有模型，确保它们在SQLAlchemy创建会话时被正确注册
from . import user
from . import heritage
from . import content
from . import interaction
from . import forum  # 添加论坛模型导入
from . import notification  # 添加通知模型导入
from . import message  # 添加私信模型导入

# 为方便使用，导出主要模型类
from .user import User
from .heritage import HeritageItem
from .content import Content
from .interaction import Comment, Like, Favorite
from .forum import ForumTopic, ForumPost  # 导出论坛模型类
from .notification import Notification  # 导出通知模型类
# 从message模块导入模型类，现在已经没有循环导入的问题
from .message import Message, MessageGroup, UserGroup, MessageReadStatus

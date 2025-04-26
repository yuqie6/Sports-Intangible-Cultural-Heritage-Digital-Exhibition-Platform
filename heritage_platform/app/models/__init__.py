"""
数据模型包初始化模块

本模块初始化应用的数据模型层，包括：
1. 定义通用的辅助函数，如beijing_time()用于生成北京时间
2. 导入所有模型模块，确保它们在SQLAlchemy创建会话时被正确注册
3. 导出主要模型类，方便其他模块直接从models包导入

模型结构:
- user.py: 用户模型，处理用户账号和认证
- heritage.py: 非遗项目模型，平台的核心数据实体
- content.py: 内容模型，包括文章、图片、视频等
- interaction.py: 交互模型，包括评论、点赞、收藏等
- forum.py: 论坛模型，包括主题和回复
- notification.py: 通知模型，处理系统通知和公告
- message.py: 消息模型，处理私信和群组消息

这些模型共同构成了应用的数据层，定义了数据库结构和业务逻辑。
"""

from datetime import datetime, timedelta

def beijing_time():
    """返回北京时间（UTC+8）

    生成当前的北京时间（UTC+8时区），用于模型的created_at和updated_at字段的默认值。
    在中国部署的应用中，使用北京时间比UTC时间更直观。

    返回:
        datetime: 当前的北京时间

    示例:
        created_at = db.Column(db.DateTime, default=beijing_time)
    """
    return datetime.utcnow() + timedelta(hours=8)

# 导入所有模型，确保它们在SQLAlchemy创建会话时被正确注册
# 这些导入看起来未被使用，但实际上是必要的，因为它们触发了模型类的定义和注册
# pylint: disable=unused-import
from . import user
from . import heritage
from . import content
from . import interaction
from . import forum  # 添加论坛模型导入
from . import notification  # 添加通知模型导入
from . import message  # 添加私信模型导入

# 为方便使用，导出主要模型类
# 这些导出允许其他模块直接从app.models导入这些类，而不需要从具体的子模块导入
# pylint: disable=unused-import
from .user import User
from .heritage import HeritageItem
from .content import Content, ContentImage
from .interaction import Comment, Like, Favorite
from .forum import ForumTopic, ForumPost  # 导出论坛模型类
from .notification import Notification  # 导出通知模型类
# 从message模块导入模型类，现在已经没有循环导入的问题
from .message import Message, MessageGroup, UserGroup, MessageReadStatus

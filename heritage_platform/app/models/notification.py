"""
通知系统模型模块

本模块定义了通知系统的数据模型，用于实现用户通知功能。
通知系统支持多种类型的通知，如回复通知、点赞通知、公告等。

通知系统特性：
- 多种通知类型：支持不同场景的通知
- 已读状态跟踪：记录通知是否已被用户阅读
- 发送者关联：可选关联通知的发送者
- 相关链接：可包含相关内容的链接，便于用户快速访问
"""

from app import db
from . import beijing_time

class Notification(db.Model):
    """通知模型

    存储用户通知信息，包括系统通知和用户间的交互通知。
    支持多种通知类型，如回复、点赞、公告等。

    属性:
        id: 通知唯一标识符
        user_id: 接收通知的用户ID
        sender_id: 发送通知的用户ID（可选，系统通知可为空）
        type: 通知类型，如reply(回复)、like(点赞)、announcement(公告)等
        content: 通知内容
        link: 相关链接，如帖子URL（可选）
        is_read: 是否已读
        created_at: 创建时间
    """
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    # 接收通知的用户
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # 发送通知的用户(可以为空,比如系统通知)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 通知类型: reply(回复)、like(点赞)、announcement(公告)等
    type = db.Column(db.String(20), nullable=False)
    # 通知内容
    content = db.Column(db.Text, nullable=False)
    # 相关链接(可选)
    link = db.Column(db.String(255))
    # 是否已读
    is_read = db.Column(db.Boolean, default=False)
    # 创建时间
    created_at = db.Column(db.DateTime, default=beijing_time)

    # 关系
    user = db.relationship('User', foreign_keys=[user_id], backref='notifications')
    sender = db.relationship('User', foreign_keys=[sender_id])

    def __repr__(self):
        """返回通知的字符串表示

        用于调试和日志输出时的对象表示。

        Returns:
            str: 通知的简短表示，包含通知类型
        """
        return f'<Notification {self.type}>'

    def to_dict(self):
        """将通知转换为字典格式

        用于API响应和JSON序列化，包含通知的完整信息。
        同时获取发送者用户名，避免前端需要额外查询。

        Returns:
            dict: 包含通知数据的字典，包括发送者信息
        """
        return {
            'id': self.id,
            'type': self.type,
            'content': self.content,
            'link': self.link,
            'is_read': self.is_read,
            'created_at': self.created_at,
            'sender': self.sender.username if self.sender else None
        }

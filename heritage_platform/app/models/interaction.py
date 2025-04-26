"""
互动模型模块

本模块定义了用户与内容互动的数据模型，包括：
1. Comment: 评论模型，支持嵌套回复
2. Like: 点赞模型，记录用户对内容的点赞
3. Favorite: 收藏模型，记录用户对内容的收藏

互动系统特性：
- 嵌套评论：支持对评论进行回复，形成评论树结构
- 用户关联：所有互动都与用户关联，记录互动者信息
- 内容关联：所有互动都与特定内容关联
- 时间跟踪：记录互动发生的时间
"""

from app import db
from . import beijing_time

class Comment(db.Model):
    """评论模型

    存储用户对内容的评论，支持嵌套回复功能。
    一个评论可以是对内容的直接评论，也可以是对其他评论的回复。

    特性：
    - 嵌套回复：通过parent_id和reply_to_user_id实现回复层级
    - 时间跟踪：记录评论创建时间
    - 关联关系：与内容、作者和回复目标用户关联

    属性:
        id: 评论唯一标识符
        user_id: 评论者ID
        content_id: 评论的内容ID
        text: 评论文本
        created_at: 创建时间
        parent_id: 父评论ID，用于嵌套回复
        reply_to_user_id: 回复目标用户ID
    """
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content_id = db.Column(db.Integer, db.ForeignKey('contents.id'))
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=beijing_time)

    # 添加嵌套回复支持
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    reply_to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 添加嵌套回复关系
    replies = db.relationship(
        'Comment',
        backref=db.backref('parent', remote_side=[id]),
        lazy='dynamic'
    )

    # 添加回复目标用户关系
    reply_to_user = db.relationship(
        'User',
        foreign_keys=[reply_to_user_id],
        overlaps="comment_replies"
    )

    def __repr__(self):
        """返回评论的字符串表示

        用于调试和日志输出时的对象表示。

        Returns:
            str: 评论的简短表示，包含ID
        """
        return f'<Comment {self.id}>'

    @property
    def is_reply(self):
        """判断是否为嵌套回复

        检查评论是否是对其他评论的回复，而不是直接回复内容。
        通过parent_id是否存在来判断。

        Returns:
            bool: 如果是嵌套回复返回True，否则返回False
        """
        return self.parent_id is not None

    def to_dict(self):
        """将评论转换为字典格式

        用于API响应和JSON序列化，包含评论的完整信息。
        同时获取作者和回复目标用户信息，避免前端需要额外查询。

        Returns:
            dict: 包含评论数据的字典，包括作者信息和回复关系
        """
        from app.models import User
        author = User.query.get(self.user_id)
        reply_to = User.query.get(self.reply_to_user_id) if self.reply_to_user_id else None

        return {
            'id': self.id,
            'user_id': self.user_id,
            'content_id': self.content_id,
            'author_name': author.username if author else None,
            'author_avatar': author.avatar if author else None,
            'text': self.text,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'parent_id': self.parent_id,
            'reply_to_user_id': self.reply_to_user_id,
            'reply_to_name': reply_to.username if reply_to else None
        }

class Like(db.Model):
    """点赞模型

    存储用户对内容的点赞记录。
    用于跟踪哪些用户点赞了哪些内容，以及点赞的时间。

    属性:
        id: 点赞记录唯一标识符
        user_id: 点赞用户ID
        content_id: 被点赞的内容ID
        created_at: 点赞时间
    """
    __tablename__ = 'likes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content_id = db.Column(db.Integer, db.ForeignKey('contents.id'))
    created_at = db.Column(db.DateTime, default=beijing_time)

    def __repr__(self):
        """返回点赞记录的字符串表示

        用于调试和日志输出时的对象表示。

        Returns:
            str: 点赞记录的简短表示，包含ID
        """
        return f'<Like {self.id}>'

class Favorite(db.Model):
    """收藏模型

    存储用户对内容的收藏记录。
    用于跟踪哪些用户收藏了哪些内容，以及收藏的时间。
    收藏功能允许用户保存感兴趣的内容，方便后续查看。

    属性:
        id: 收藏记录唯一标识符
        user_id: 收藏用户ID
        content_id: 被收藏的内容ID
        created_at: 收藏时间
    """
    __tablename__ = 'favorites'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content_id = db.Column(db.Integer, db.ForeignKey('contents.id'))
    created_at = db.Column(db.DateTime, default=beijing_time)

    def __repr__(self):
        """返回收藏记录的字符串表示

        用于调试和日志输出时的对象表示。

        Returns:
            str: 收藏记录的简短表示，包含ID
        """
        return f'<Favorite {self.id}>'

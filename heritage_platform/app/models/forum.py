"""
论坛模型模块

本模块定义了论坛系统的数据模型，包括：
1. ForumTopic: 论坛主题模型，表示一个讨论主题
2. ForumPost: 论坛帖子模型，表示主题下的回复，支持嵌套回复

论坛系统特性：
- 主题分类：支持按不同类别组织主题
- 置顶功能：重要主题可以置顶显示
- 关闭功能：可以关闭主题，阻止新回复
- 嵌套回复：支持回复特定的帖子，形成对话
- 活动跟踪：记录最后活动时间，便于排序
"""

from app import db
from . import beijing_time

class ForumTopic(db.Model):
    """论坛主题模型

    表示论坛中的一个讨论主题，包含基本信息和状态。
    每个主题可以有多个帖子(ForumPost)作为回复。

    属性:
        id: 主题唯一标识符
        title: 主题标题
        category: 主题分类，如"讨论"、"问答"等
        user_id: 创建者ID，外键关联到User模型
        views: 浏览次数
        is_pinned: 是否置顶
        is_closed: 是否关闭（不允许新回复）
        created_at: 创建时间
        last_activity: 最后活动时间，用于排序
    """
    __tablename__ = 'forum_topics'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), default='讨论')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    views = db.Column(db.Integer, default=0)
    is_pinned = db.Column(db.Boolean, default=False)
    is_closed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=beijing_time)
    last_activity = db.Column(db.DateTime, default=beijing_time)

    # 关系
    posts = db.relationship('ForumPost', backref='topic', lazy='dynamic')

    def __repr__(self):
        """返回主题的字符串表示

        用于调试和日志输出时的对象表示。

        Returns:
            str: 主题的简短表示
        """
        return f'<ForumTopic {self.title}>'

    @property
    def post_count(self):
        """获取主题下的帖子数量

        计算与主题关联的帖子总数，用于显示回复数量。

        Returns:
            int: 帖子数量
        """
        return self.posts.count()

    def to_dict(self):
        """将主题转换为字典格式

        用于API响应和JSON序列化，包含主题的完整信息。
        同时获取创建者用户名，避免前端需要额外查询。

        Returns:
            dict: 包含主题数据的字典
        """
        from app.models import User
        creator = User.query.get(self.user_id)

        return {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'user_id': self.user_id,
            'creator': creator.username if creator else None,
            'views': self.views,
            'post_count': self.post_count,
            'is_pinned': self.is_pinned,
            'is_closed': self.is_closed,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'last_activity': self.last_activity.strftime('%Y-%m-%d %H:%M:%S') if self.last_activity else None
        }

class ForumPost(db.Model):
    """论坛帖子回复模型

    表示论坛主题下的回复帖子，支持嵌套回复功能。
    每个帖子可以是主题的直接回复，也可以是对其他帖子的回复。

    特性：
    - 嵌套回复：通过parent_id和reply_to_user_id实现回复层级
    - 时间跟踪：记录创建和更新时间
    - 关联关系：与主题、作者和回复目标用户关联

    属性:
        id: 帖子唯一标识符
        topic_id: 所属主题ID
        user_id: 作者ID
        content: 帖子内容
        created_at: 创建时间
        updated_at: 更新时间
        parent_id: 父帖子ID，用于嵌套回复
        reply_to_user_id: 回复目标用户ID
    """
    __tablename__ = 'forum_posts'

    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('forum_topics.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=beijing_time)
    updated_at = db.Column(db.DateTime, default=beijing_time, onupdate=beijing_time)

    # 添加嵌套回复支持
    parent_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=True)
    reply_to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 添加嵌套回复关系
    replies = db.relationship(
        'ForumPost',
        backref=db.backref('parent', remote_side=[id]),
        lazy='dynamic'
    )
    reply_to_user = db.relationship('User', foreign_keys=[reply_to_user_id])

    def __repr__(self):
        """返回帖子的字符串表示

        用于调试和日志输出时的对象表示。

        Returns:
            str: 帖子的简短表示
        """
        return f'<ForumPost {self.id}>'

    @property
    def is_reply(self):
        """判断是否为嵌套回复

        检查帖子是否是对其他帖子的回复，而不是直接回复主题。
        通过parent_id是否存在来判断。

        Returns:
            bool: 如果是嵌套回复返回True，否则返回False
        """
        return self.parent_id is not None

    def to_dict(self):
        """将帖子转换为字典格式

        用于API响应和JSON序列化，包含帖子的完整信息。
        同时获取作者和回复目标用户信息，避免前端需要额外查询。

        Returns:
            dict: 包含帖子数据的字典，包括作者信息和回复关系
        """
        from app.models import User
        author = User.query.get(self.user_id)
        reply_to = User.query.get(self.reply_to_user_id) if self.reply_to_user_id else None

        return {
            'id': self.id,
            'topic_id': self.topic_id,
            'user_id': self.user_id,
            'author': author.username if author else None,
            'author_avatar': author.avatar if author else None,
            'content': self.content,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'parent_id': self.parent_id,
            'reply_to_user_id': self.reply_to_user_id,
            'reply_to_username': reply_to.username if reply_to else None
        }

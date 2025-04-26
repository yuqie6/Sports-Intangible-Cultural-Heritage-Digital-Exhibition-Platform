"""
内容模型模块

本模块定义了平台的内容数据模型，包括：
1. Content: 主要内容模型，支持多种内容类型
2. ContentImage: 内容图片模型，用于存储内容的多图片信息

内容系统特性：
- 多种内容类型：支持文章、视频、图片和多媒体内容
- 富文本支持：支持HTML格式的富文本内容，可嵌入图片和视频
- 多图片支持：一个内容可以关联多个图片，并支持排序和说明
- 互动统计：跟踪评论数、点赞数、收藏数和浏览量
- 关联关系：与非遗项目、作者和互动记录关联
"""

from tokenize import Comment
from app import db
from . import beijing_time

class Content(db.Model):
    """内容模型

    存储平台的各种内容，包括文章、视频、图片和多媒体内容。
    是平台的核心数据实体之一，与非遗项目和用户关联。

    支持的内容类型:
    - article: 文章，主要是文本内容
    - video: 视频，包含视频文件路径
    - image: 图片，包含图片文件路径
    - multimedia: 多媒体，混合了文本、图片和视频

    属性:
        id: 内容唯一标识符
        title: 内容标题
        heritage_id: 关联的非遗项目ID
        user_id: 作者ID
        content_type: 内容类型
        text_content: 纯文本内容，用于文章类型
        file_path: 文件路径，用于视频和图片类型
        cover_image: 封面图片路径
        rich_content: 富文本内容，包含HTML，支持嵌入图片和视频
        created_at: 创建时间
        updated_at: 更新时间
        views: 浏览量
    """
    __tablename__ = 'contents'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    heritage_id = db.Column(db.Integer, db.ForeignKey('heritage_items.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content_type = db.Column(db.String(20), nullable=False)  # article, video, image, multimedia
    text_content = db.Column(db.Text)  # for article type
    file_path = db.Column(db.String(255))  # for video and image type
    cover_image = db.Column(db.String(255))  # 封面图片路径
    rich_content = db.Column(db.Text)  # 富文本内容字段，包含HTML，支持嵌入图片和视频
    created_at = db.Column(db.DateTime, default=beijing_time)
    updated_at = db.Column(db.DateTime, default=beijing_time, onupdate=beijing_time)

    # 关系定义
    heritage = db.relationship('HeritageItem', back_populates='contents')
    author = db.relationship('User', backref='contents', lazy=True, foreign_keys=[user_id])
    comments = db.relationship('Comment', backref='content', lazy='dynamic')
    likes = db.relationship('Like', backref='content', lazy='dynamic')
    favorites = db.relationship('Favorite', backref='content', lazy='dynamic')
    views = db.Column(db.Integer, default=0)  # 添加浏览量字段

    # 添加与图片的关系
    images = db.relationship('ContentImage', backref='content', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        """返回内容的字符串表示

        用于调试和日志输出时的对象表示。

        Returns:
            str: 内容的简短表示，包含标题
        """
        return f'<Content {self.title}>'

    def to_dict(self, include_comments=False):
        """将内容转换为字典格式

        用于API响应和JSON序列化，包含内容的完整信息。
        同时获取关联的非遗项目和作者信息，避免前端需要额外查询。
        可选择是否包含最近的评论。

        Args:
            include_comments (bool): 是否包含最近的评论，默认为False

        Returns:
            dict: 包含内容数据的字典，包括统计信息和关联数据
        """
        # 导入HeritageItem以便获取关联的非遗项目
        from app.models import HeritageItem

        # 获取关联的非遗项目
        heritage_item = HeritageItem.query.get(self.heritage_id) if self.heritage_id else None

        result = {
            'id': self.id,
            'title': self.title,
            'heritage_id': self.heritage_id,
            'heritage_name': heritage_item.name if heritage_item else None,
            'user_id': self.user_id,
            'author_name': self.author.username if self.author else None,
            'author_avatar': self.author.avatar if self.author else None,
            'content_type': self.content_type,
            'text_content': self.text_content,
            'file_path': self.file_path,
            'cover_image': self.cover_image,
            'rich_content': self.rich_content if hasattr(self, 'rich_content') else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'comment_count': self.comments.count(),
            'like_count': self.likes.count(),
            'favorite_count': self.favorites.count(),
            'views': self.views,  # 添加浏览量到字典
            'images': [image.to_dict() for image in self.images.all()]  # 添加图片列表
        }

        if include_comments:
            comments = self.comments.order_by(Comment.created_at.desc()).limit(10).all()
            result['recent_comments'] = [comment.to_dict() for comment in comments]

        return result

class ContentImage(db.Model):
    """内容图片模型

    存储与内容关联的图片信息，支持一个内容关联多个图片。
    提供图片排序、说明等功能，增强内容的多媒体展示能力。

    属性:
        id: 图片唯一标识符
        content_id: 关联的内容ID
        file_path: 图片文件路径
        caption: 图片说明/标题
        order: 图片顺序，用于控制显示顺序
        created_at: 创建时间
    """
    __tablename__ = 'content_images'

    id = db.Column(db.Integer, primary_key=True)
    content_id = db.Column(db.Integer, db.ForeignKey('contents.id'))
    file_path = db.Column(db.String(255), nullable=False)  # 图片路径
    caption = db.Column(db.String(255))  # 图片说明/标题
    order = db.Column(db.Integer, default=0)  # 图片顺序
    created_at = db.Column(db.DateTime, default=beijing_time)

    def __repr__(self):
        """返回内容图片的字符串表示

        用于调试和日志输出时的对象表示。

        Returns:
            str: 内容图片的简短表示，包含ID和关联的内容ID
        """
        return f'<ContentImage {self.id} for Content {self.content_id}>'

    def to_dict(self):
        """将内容图片转换为字典格式

        用于API响应和JSON序列化，包含图片的完整信息。

        Returns:
            dict: 包含图片数据的字典，包括路径、说明和顺序信息
        """
        return {
            'id': self.id,
            'content_id': self.content_id,
            'file_path': self.file_path,
            'caption': self.caption,
            'order': self.order,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

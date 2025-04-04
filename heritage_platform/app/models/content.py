from tokenize import Comment
from app import db
from . import beijing_time

class Content(db.Model):
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
        return f'<Content {self.title}>'
        
    def to_dict(self, include_comments=False):
        """转换为字典用于API响应"""
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

# 添加ContentImage模型用于存储多图片信息
class ContentImage(db.Model):
    __tablename__ = 'content_images'
    
    id = db.Column(db.Integer, primary_key=True)
    content_id = db.Column(db.Integer, db.ForeignKey('contents.id'))
    file_path = db.Column(db.String(255), nullable=False)  # 图片路径
    caption = db.Column(db.String(255))  # 图片说明/标题
    order = db.Column(db.Integer, default=0)  # 图片顺序
    created_at = db.Column(db.DateTime, default=beijing_time)
    
    def __repr__(self):
        return f'<ContentImage {self.id} for Content {self.content_id}>'
    
    def to_dict(self):
        """转换为字典用于API响应"""
        return {
            'id': self.id,
            'content_id': self.content_id,
            'file_path': self.file_path,
            'caption': self.caption,
            'order': self.order,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

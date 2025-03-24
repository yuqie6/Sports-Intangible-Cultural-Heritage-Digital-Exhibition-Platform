from app import db
from datetime import datetime

class Content(db.Model):
    __tablename__ = 'contents'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    heritage_id = db.Column(db.Integer, db.ForeignKey('heritage_items.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content_type = db.Column(db.String(20), nullable=False)  # article, video, image
    text_content = db.Column(db.Text)  # for article type
    file_path = db.Column(db.String(255))  # for video and image type
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系 - 使用字符串引用而不是直接引用类，避免循环导入
    comments = db.relationship('Comment', backref='content', lazy='dynamic')
    likes = db.relationship('Like', backref='content', lazy='dynamic')
    favorites = db.relationship('Favorite', backref='content', lazy='dynamic')
    
    def __repr__(self):
        return f'<Content {self.title}>'
        
    def to_dict(self, include_comments=False):
        """转换为字典用于API响应"""
        from app.models import User, HeritageItem
        
        author = User.query.get(self.user_id)
        heritage = HeritageItem.query.get(self.heritage_id)
        
        result = {
            'id': self.id,
            'title': self.title,
            'heritage_id': self.heritage_id,
            'heritage_name': heritage.name if heritage else None,
            'user_id': self.user_id,
            'author_name': author.username if author else None,
            'author_avatar': author.avatar if author else None,
            'content_type': self.content_type,
            'text_content': self.text_content,
            'file_path': self.file_path,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'comment_count': self.comments.count(),
            'like_count': self.likes.count(),
            'favorite_count': self.favorites.count()
        }
        
        if include_comments:
            from app.models import Comment
            comments = Comment.query.filter_by(content_id=self.id).order_by(Comment.created_at.desc()).limit(10).all()
            result['recent_comments'] = [comment.to_dict() for comment in comments]
            
        return result

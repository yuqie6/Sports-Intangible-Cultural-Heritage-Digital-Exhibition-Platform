from app import db
from datetime import datetime

class Comment(db.Model):
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content_id = db.Column(db.Integer, db.ForeignKey('contents.id'))
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
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
        foreign_keys=[reply_to_user_id]
    )
    
    def __repr__(self):
        return f'<Comment {self.id}>'
    
    @property
    def is_reply(self):
        """是否是回复其他评论的评论"""
        return self.parent_id is not None
        
    def to_dict(self):
        """转换为字典用于API响应"""
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
    __tablename__ = 'likes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content_id = db.Column(db.Integer, db.ForeignKey('contents.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Like {self.id}>'

class Favorite(db.Model):
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content_id = db.Column(db.Integer, db.ForeignKey('contents.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Favorite {self.id}>'

from app import db
from datetime import datetime

class ForumTopic(db.Model):
    """论坛主题"""
    __tablename__ = 'forum_topics'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), default='讨论')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    views = db.Column(db.Integer, default=0)
    is_pinned = db.Column(db.Boolean, default=False)
    is_closed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    posts = db.relationship('ForumPost', backref='topic', lazy='dynamic')
    
    def __repr__(self):
        return f'<ForumTopic {self.title}>'
        
    @property
    def post_count(self):
        """帖子数量"""
        return self.posts.count()
        
    def to_dict(self):
        """转换为字典用于API响应"""
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
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'last_activity': self.last_activity.strftime('%Y-%m-%d %H:%M:%S')
        }

class ForumPost(db.Model):
    """论坛帖子回复"""
    __tablename__ = 'forum_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('forum_topics.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ForumPost {self.id}>'
        
    def to_dict(self):
        """转换为字典用于API响应"""
        from app.models import User
        author = User.query.get(self.user_id)
        
        return {
            'id': self.id,
            'topic_id': self.topic_id,
            'user_id': self.user_id,
            'author': author.username if author else None,
            'author_avatar': author.avatar if author else None,
            'content': self.content,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }

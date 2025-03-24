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

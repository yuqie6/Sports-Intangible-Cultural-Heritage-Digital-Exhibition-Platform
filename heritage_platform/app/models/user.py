from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)  # 增加长度到255
    role = db.Column(db.String(20), default='student')  # admin, teacher, student
    avatar = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    heritage_items = db.relationship('HeritageItem', backref='creator', lazy='dynamic')
    # 删除conflicting的contents关系定义
    comments = db.relationship('Comment', backref='author', lazy='dynamic', foreign_keys='Comment.user_id')
    comment_replies = db.relationship('Comment', lazy='dynamic', foreign_keys='Comment.reply_to_user_id')
    likes = db.relationship('Like', backref='user', lazy='dynamic')
    favorites = db.relationship('Favorite', backref='user', lazy='dynamic')
    # 添加论坛关系
    forum_topics = db.relationship('ForumTopic', backref='creator', lazy='dynamic', foreign_keys='ForumTopic.user_id')
    forum_posts = db.relationship('ForumPost', backref='author', lazy='dynamic', foreign_keys='ForumPost.user_id')
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
        
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_teacher(self):
        return self.role == 'teacher'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

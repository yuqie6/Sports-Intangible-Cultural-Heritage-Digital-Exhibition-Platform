"""
用户模型模块

本模块定义了用户数据模型，是整个应用的核心模型之一。
主要功能：
1. 定义User类，包含用户基本信息和身份验证方法
2. 实现与其他模型的关联关系
3. 提供用户角色判断的便捷属性
4. 实现Flask-Login所需的用户加载函数

用户角色体系：
- admin: 管理员，拥有最高权限
- teacher: 教师，可以创建非遗项目和内容
- student: 学生，基本用户角色
"""

from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import beijing_time

class User(UserMixin, db.Model):
    """用户模型

    存储用户基本信息和身份验证数据，实现与其他模型的关联关系。
    继承UserMixin以支持Flask-Login的用户认证功能。

    属性:
        id: 用户唯一标识符
        username: 用户名，唯一
        email: 电子邮箱，唯一
        password_hash: 密码哈希值，不存储明文密码
        role: 用户角色，可以是admin(管理员)、teacher(教师)或student(学生)
        avatar: 用户头像路径
        created_at: 账户创建时间

    关系:
        heritage_items: 用户创建的非遗项目
        comments: 用户发表的评论
        comment_replies: 回复用户的评论
        likes: 用户的点赞记录
        favorites: 用户的收藏记录
        forum_topics: 用户创建的论坛主题
        forum_posts: 用户发表的论坛帖子
    """
    __tablename__ = 'users'

    # 基本字段
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)  # 增加长度到255以适应不同哈希算法
    role = db.Column(db.String(20), default='student')  # 用户角色: admin, teacher, student
    avatar = db.Column(db.String(255))  # 头像图片路径
    created_at = db.Column(db.DateTime, default=beijing_time)  # 使用北京时间作为默认时间

    # 关系定义
    # 非遗项目关系
    heritage_items = db.relationship('HeritageItem', backref='creator', lazy='dynamic')

    # 互动关系
    comments = db.relationship('Comment', backref='author', lazy='dynamic', foreign_keys='Comment.user_id')
    comment_replies = db.relationship('Comment', lazy='dynamic', foreign_keys='Comment.reply_to_user_id')
    likes = db.relationship('Like', backref='user', lazy='dynamic')
    favorites = db.relationship('Favorite', backref='user', lazy='dynamic')

    # 论坛关系
    forum_topics = db.relationship('ForumTopic', backref='creator', lazy='dynamic', foreign_keys='ForumTopic.user_id')
    forum_posts = db.relationship('ForumPost', backref='author', lazy='dynamic', foreign_keys='ForumPost.user_id')

    @property
    def password(self):
        """密码属性getter

        阻止直接读取密码，提高安全性。
        尝试读取password属性时会抛出AttributeError异常。

        Raises:
            AttributeError: 当尝试读取password属性时
        """
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        """密码属性setter

        设置密码时自动进行哈希处理，不存储明文密码。
        使用werkzeug的generate_password_hash函数生成安全的密码哈希。

        Args:
            password: 明文密码
        """
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """验证密码

        比较提供的明文密码与存储的密码哈希是否匹配。
        使用werkzeug的check_password_hash函数进行安全比较。

        Args:
            password: 待验证的明文密码

        Returns:
            bool: 密码匹配返回True，否则返回False
        """
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        """判断用户是否为管理员

        Returns:
            bool: 用户角色为'admin'时返回True，否则返回False
        """
        return self.role == 'admin'

    @property
    def is_teacher(self):
        """判断用户是否为教师

        Returns:
            bool: 用户角色为'teacher'时返回True，否则返回False
        """
        return self.role == 'teacher'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

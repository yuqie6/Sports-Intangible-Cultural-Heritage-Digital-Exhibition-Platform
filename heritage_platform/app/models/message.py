"""
消息系统数据模型模块

本模块定义了消息系统的数据模型，包括：
1. Message: 消息模型，支持私信、群组消息和广播消息
2. MessageGroup: 消息群组模型，用于群聊功能
3. UserGroup: 用户-群组关联模型，定义用户在群组中的角色
4. MessageReadStatus: 消息已读状态模型，精确跟踪群组消息的已读状态

消息系统支持以下特性：
- 多种消息类型：私信、群组消息、广播消息
- 软删除：消息被删除时不会立即从数据库移除，而是标记为已删除
- 精确的已读状态跟踪：每个用户对每条群组消息的已读状态单独记录
- 群组角色管理：支持普通成员和管理员角色
"""

from app import db
from datetime import datetime

class Message(db.Model):
    """消息模型

    支持三种类型的消息：
    - personal: 私人消息，一对一通信
    - group: 群组消息，一对多通信
    - broadcast: 广播消息，管理员/教师向多个用户发送的系统通知

    实现了软删除功能，使用sender_deleted和receiver_deleted标记，
    只有当双方都删除了消息时，才会真正从数据库中删除。
    """
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey('message_groups.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_read = db.Column(db.Boolean, default=False)
    sender_deleted = db.Column(db.Boolean, default=False)
    receiver_deleted = db.Column(db.Boolean, default=False)
    message_type = db.Column(db.String(20), default='personal')  # personal, group, broadcast

    # 关系
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')
    group = db.relationship('MessageGroup', back_populates='messages')
    read_status = db.relationship('MessageReadStatus', back_populates='message', cascade='all, delete-orphan')

class MessageGroup(db.Model):
    """消息群组模型

    定义消息群组的基本信息和关系。
    支持不同类型的群组（班级、小组、自定义等）。

    特性：
    - 记录创建者信息，用于权限控制
    - 支持群组描述和类型分类
    - 自动更新时间戳
    - 与成员和消息的关联关系
    """
    __tablename__ = 'message_groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    group_type = db.Column(db.String(20), default='standard')  # standard, class, department, etc.

    # 关系
    creator = db.relationship('User', backref='created_groups')
    members = db.relationship('UserGroup', back_populates='group', cascade='all, delete-orphan')
    messages = db.relationship('Message', back_populates='group', cascade='all, delete-orphan')

class UserGroup(db.Model):
    """用户-群组关系模型

    定义用户与群组之间的多对多关系，并包含用户在群组中的角色信息。

    特性：
    - 支持不同角色：普通成员(member)和管理员(admin)
    - 记录加入时间
    - 使用唯一约束确保一个用户在同一群组中只有一条记录
    - 双向关联关系，便于从用户或群组角度查询
    """
    __tablename__ = 'user_groups'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('message_groups.id'), nullable=False)
    role = db.Column(db.String(20), default='member')  # member, admin
    joined_at = db.Column(db.DateTime, default=datetime.now)

    # 关系
    user = db.relationship('User', backref='group_memberships')
    group = db.relationship('MessageGroup', back_populates='members')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'group_id', name='uq_user_group'),
    )

class MessageReadStatus(db.Model):
    """消息已读状态模型

    精确跟踪每个用户对每条消息的已读状态，主要用于群组消息。
    对于私信，直接使用Message表中的is_read字段。

    特性：
    - 记录精确的已读时间戳
    - 使用唯一约束确保每个用户对每条消息只有一条状态记录
    - 支持批量更新已读状态
    - 级联删除：当消息被删除时，相关的已读状态记录也会被删除
    """
    __tablename__ = 'message_read_status'

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime, nullable=True)

    # 关系
    message = db.relationship('Message', back_populates='read_status')
    user = db.relationship('User', backref='message_read_status')

    __table_args__ = (
        db.UniqueConstraint('message_id', 'user_id', name='uq_message_user'),
    )

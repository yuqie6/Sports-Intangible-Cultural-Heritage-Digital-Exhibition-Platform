from app import db
from datetime import datetime

class Message(db.Model):
    """私信模型"""
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
    """消息群组模型"""
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
    """用户-群组关系模型"""
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
    """消息已读状态表"""
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

from app import db
from . import beijing_time

class Message(db.Model):
    """私信模型"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    # 发送者ID
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # 接收者ID
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # 消息内容
    content = db.Column(db.Text, nullable=False)
    # 是否已读
    is_read = db.Column(db.Boolean, default=False)
    # 创建时间
    created_at = db.Column(db.DateTime, default=beijing_time)
    # 是否被发送者删除
    sender_deleted = db.Column(db.Boolean, default=False)
    # 是否被接收者删除
    receiver_deleted = db.Column(db.Boolean, default=False)

    # 关系
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')

    def __repr__(self):
        return f'<Message {self.id}>'

    def to_dict(self):
        """转换为字典用于API响应"""
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'sender_name': self.sender.username,
            'receiver_name': self.receiver.username,
            'content': self.content,
            'is_read': self.is_read,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
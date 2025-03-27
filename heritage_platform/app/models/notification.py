from app import db
from . import beijing_time

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    # 接收通知的用户
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # 发送通知的用户(可以为空,比如系统通知)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 通知类型: reply(回复)、like(点赞)、announcement(公告)等
    type = db.Column(db.String(20), nullable=False)
    # 通知内容
    content = db.Column(db.Text, nullable=False)
    # 相关链接(可选)
    link = db.Column(db.String(255))
    # 是否已读
    is_read = db.Column(db.Boolean, default=False)
    # 创建时间
    created_at = db.Column(db.DateTime, default=beijing_time)

    # 关系
    user = db.relationship('User', foreign_keys=[user_id], backref='notifications')
    sender = db.relationship('User', foreign_keys=[sender_id])

    def __repr__(self):
        return f'<Notification {self.type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'content': self.content,
            'link': self.link,
            'is_read': self.is_read,
            'created_at': self.created_at,
            'sender': self.sender.username if self.sender else None
        }

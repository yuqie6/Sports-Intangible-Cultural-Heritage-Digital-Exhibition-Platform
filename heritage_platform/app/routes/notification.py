from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Notification
from app import db

bp = Blueprint('notification', __name__)

@bp.route('/notifications')
@login_required
def list_notifications():
    """显示当前用户的所有通知"""
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).all()
    return render_template('notification/list.html', notifications=notifications)

def send_notification(user_id, content, notification_type, link=None, sender_id=None):
    """
    发送通知的辅助函数
    
    Parameters:
        user_id: 接收通知的用户ID
        content: 通知内容
        notification_type: 通知类型 (reply/like/announcement等)
        link: 可选的相关链接
        sender_id: 可选的发送者ID
    """
    notification = Notification(
        user_id=user_id,
        content=content,
        type=notification_type,
        link=link,
        sender_id=sender_id
    )
    db.session.add(notification)
    try:
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"发送通知失败: {str(e)}")
        return False

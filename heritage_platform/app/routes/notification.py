from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request
from flask_login import login_required, current_user
from app.models import Notification, User
from app.forms.notification import AnnouncementForm
from app.utils.decorators import admin_required, teacher_required, role_required
from app import db

bp = Blueprint('notification', __name__)

@bp.route('/notifications')
@login_required
def list_notifications():
    """显示当前用户的所有通知"""
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).options(db.joinedload(Notification.sender)).order_by(Notification.created_at.desc()).all()
    return render_template('notification/list.html', notifications=notifications)

@bp.route('/announcement', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'teacher'])  # 只允许管理员和教师访问
def create_announcement():
    """创建公告页面 - 管理员和教师功能"""
    form = AnnouncementForm()
    
    if form.validate_on_submit():
        try:
            title = form.title.data
            content = form.content.data
            announcement_content = f"{title}：{content}"
            
            # 获取所有用户
            users = User.query.all()
            sent_count = 0
            
            for user in users:
                # 跳过当前用户（不给自己发通知）
                if user.id == current_user.id:
                    continue
                
                # 发送公告通知
                success = send_notification(
                    user_id=user.id,
                    content=announcement_content,
                    notification_type='announcement',
                    sender_id=current_user.id
                )
                
                if success:
                    sent_count += 1
            
            flash(f'公告已成功发送给 {sent_count} 位用户', 'success')
            return redirect(url_for('notification.create_announcement'))
            
        except Exception as e:
            current_app.logger.error(f"发布公告失败: {str(e)}")
            flash('发布公告失败，请稍后重试', 'danger')
    
    return render_template('notification/announcement.html', form=form)

@bp.route('/announcements')
@login_required
@role_required(['admin', 'teacher'])  # 只允许管理员和教师访问
def list_announcements():
    """查看已发布的公告列表 - 管理员和教师功能"""
    # 获取当前用户发布的公告
    announcements = Notification.query.filter_by(
        sender_id=current_user.id,
        type='announcement'
    ).order_by(Notification.created_at.desc()).all()
    
    return render_template('notification/announcements.html', announcements=announcements)

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
        current_app.logger.error(f"发送通知失败: {str(e)}")
        return False

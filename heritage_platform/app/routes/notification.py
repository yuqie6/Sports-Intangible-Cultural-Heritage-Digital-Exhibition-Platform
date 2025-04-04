from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request, jsonify
from flask_login import login_required, current_user
from app.models import Notification, User
from app.forms.notification import AnnouncementForm
from app.utils.decorators import admin_required, teacher_required, role_required
from app import db, csrf
from app.socket_events import emit_notification
import datetime

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
        
        # 添加WebSocket实时通知功能
        try:
            # 获取发送者用户名
            sender_username = None
            if sender_id:
                sender = User.query.get(sender_id)
                if sender:
                    sender_username = sender.username
            
            # 准备通知数据
            notification_data = {
                'id': notification.id,
                'type': notification_type,
                'content': content,
                'link': link,
                'sender_id': sender_id,
                'sender_username': sender_username,
                'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 发送WebSocket通知
            emit_notification(user_id, notification_data)
            
        except Exception as e:
            current_app.logger.error(f"发送WebSocket实时通知失败: {str(e)}")
            # 即使WebSocket通知失败，也不影响通知已经保存到数据库
        
        return True
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"发送通知失败: {str(e)}")
        return False

@bp.route('/read/<int:notification_id>', methods=['POST'])
@login_required
@csrf.exempt
def mark_notification_read(notification_id):
    """标记单个通知为已读"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        
        # 确保当前用户是通知的接收者
        if notification.user_id != current_user.id:
            return jsonify({'success': False, 'message': '无权操作此通知'}), 403
        
        notification.is_read = True
        db.session.commit()
        
        return jsonify({'success': True, 'message': '已标记为已读'})
    except Exception as e:
        current_app.logger.error(f"标记通知已读失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/read-all', methods=['POST'])
@login_required
@csrf.exempt
def mark_all_notifications_read():
    """标记当前用户的所有通知为已读"""
    try:
        # 查询当前用户的所有未读通知
        notifications = Notification.query.filter_by(
            user_id=current_user.id,
            is_read=False
        ).all()
        
        # 标记为已读
        for notification in notifications:
            notification.is_read = True
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'已标记 {len(notifications)} 条通知为已读'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"标记所有通知已读失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

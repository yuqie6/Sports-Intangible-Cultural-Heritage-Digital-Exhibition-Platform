"""
通知系统路由模块

本模块实现了通知系统的路由和视图函数，包括：
1. 用户通知列表：显示当前用户收到的所有通知
2. 创建公告：管理员和教师可以发布全站公告
3. 公告列表：查看已发布的公告
4. 通知标记：将通知标记为已读
5. 通知发送：提供发送通知的辅助函数，供其他模块调用

通知系统支持以下特性：
- 实时通知：通过WebSocket向在线用户推送新通知
- 权限控制：基于用户角色的权限控制
- 已读状态：跟踪通知的已读/未读状态
- 多种通知类型：支持回复、点赞、公告等多种通知类型
"""

from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request, jsonify
from flask_login import login_required, current_user
from app.models import Notification, User
from app.forms.notification import AnnouncementForm
from app.utils.decorators import admin_required, teacher_required, role_required
from app import db, csrf
from app.socket_events import emit_notification
import datetime

# 创建通知系统蓝图
bp = Blueprint('notification', __name__)

@bp.route('/notifications')
@login_required
def list_notifications():
    """显示当前用户的所有通知

    获取并显示当前登录用户收到的所有通知，按时间倒序排列。
    使用eager loading加载发送者信息，减少数据库查询次数。

    路由: /notifications
    方法: GET
    权限: 需要用户登录

    Returns:
        render_template: 渲染通知列表页面，传递以下上下文：
            - notifications: 当前用户的通知列表
    """
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).options(db.joinedload(Notification.sender)).order_by(Notification.created_at.desc()).all()
    return render_template('notification/list.html', notifications=notifications)

@bp.route('/announcement', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'teacher'])  # 只允许管理员和教师访问
def create_announcement():
    """创建公告页面 - 管理员和教师功能

    允许管理员和教师创建全站公告，发送给所有用户。
    公告会作为通知发送给每个用户，并支持实时推送。

    路由: /announcement
    方法: GET, POST
    权限: 需要用户登录且角色为管理员或教师

    GET请求:
        显示创建公告的表单页面

    POST请求:
        处理表单提交，创建公告并发送给所有用户

    Returns:
        GET: 渲染创建公告表单页面
        POST成功: 重定向回创建公告页面，显示成功消息
        POST失败: 返回表单页面并显示错误信息
    """
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
    """发送通知的辅助函数

    创建并保存通知记录，同时通过WebSocket发送实时通知。
    这个函数被其他模块调用，用于在各种交互场景中发送通知。

    支持的通知类型:
    - reply: 回复通知，当用户的内容被回复时
    - like: 点赞通知，当用户的内容被点赞时
    - announcement: 公告通知，管理员或教师发布的全站公告
    - mention: 提及通知，当用户在内容中被@提及时

    Args:
        user_id (int): 接收通知的用户ID
        content (str): 通知内容
        notification_type (str): 通知类型 (reply/like/announcement等)
        link (str, optional): 可选的相关链接，如帖子URL
        sender_id (int, optional): 可选的发送者ID，系统通知可为空

    Returns:
        bool: 通知发送成功返回True，失败返回False

    示例:
        send_notification(
            user_id=1,
            content="用户小明回复了你的评论",
            notification_type="reply",
            link="/forum/topic/5",
            sender_id=2
        )
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
@csrf.exempt  # 豁免CSRF保护，便于AJAX请求
def mark_notification_read(notification_id):
    """标记单个通知为已读

    将指定ID的通知标记为已读状态。
    通常由前端通过AJAX请求调用，支持异步更新通知状态。

    路由: /read/<notification_id>
    方法: POST
    权限: 需要用户登录，且只能操作自己的通知

    Args:
        notification_id (int): 要标记为已读的通知ID

    Returns:
        JSON: 操作结果
        {
            "success": true/false,
            "message": "操作结果描述"
        }

    状态码:
        200: 操作成功
        403: 无权操作此通知
        404: 通知不存在
        500: 服务器内部错误
    """
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
@csrf.exempt  # 豁免CSRF保护，便于AJAX请求
def mark_all_notifications_read():
    """标记当前用户的所有通知为已读

    将当前登录用户的所有未读通知一次性标记为已读状态。
    通常由前端通过AJAX请求调用，支持一键清除所有未读状态。

    路由: /read-all
    方法: POST
    权限: 需要用户登录

    Returns:
        JSON: 操作结果
        {
            "success": true/false,
            "message": "操作结果描述，包含已标记数量"
        }

    状态码:
        200: 操作成功
        500: 服务器内部错误
    """
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

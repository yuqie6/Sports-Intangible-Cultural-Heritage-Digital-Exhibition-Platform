from flask import jsonify, request, abort, current_app
from flask_login import login_required, current_user
from app.models import Notification, Message
from app import db
from . import api_bp
import traceback

@api_bp.route('/notifications/unread-count')
@login_required
def get_unread_count():
    """获取未读通知数量"""
    count = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()
    return jsonify({'count': count})

@api_bp.route('/notifications/mark-read', methods=['POST'])
@login_required
def mark_as_read():
    """将通知标记为已读"""
    try:
        # Check if the request content type is set correctly
        content_type = request.headers.get('Content-Type', '')
        if not content_type.startswith('application/json'):
            current_app.logger.warning(f"Invalid Content-Type: {content_type}")
            return jsonify({
                'error': '请求必须是JSON格式', 
                'content_type': content_type
            }), 400
        
        try:
            data = request.get_json(silent=True) or {}
        except Exception as e:
            current_app.logger.error(f"JSON parsing error: {str(e)}")
            return jsonify({'error': 'JSON解析错误'}), 400
        
        notification_id = data.get('notification_id')
        
        if not notification_id:
            current_app.logger.warning("Missing notification_id parameter")
            return jsonify({'error': 'notification_id是必需参数'}), 400
        
        notification = Notification.query.get(notification_id)
        if not notification:
            current_app.logger.warning(f"Notification not found: {notification_id}")
            return jsonify({'error': f'找不到ID为{notification_id}的通知'}), 404
        
        if notification.user_id != current_user.id:
            return jsonify({'error': '无权限操作此通知'}), 403
        
        notification.is_read = True
        db.session.commit()
        return jsonify({'message': '标记成功'})
    except Exception as e:
        current_app.logger.error(f"Error in mark_as_read: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': '处理请求时发生错误'}), 500

@api_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_as_read():
    """将所有通知标记为已读"""
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).all()
    for notification in notifications:
        notification.is_read = True
    db.session.commit()
    return jsonify({'message': '所有通知已标记为已读'})

@api_bp.route('/messages/unread-count')
@login_required
def get_unread_messages_count():
    """获取未读私信数量"""
    count = Message.query.filter_by(
        receiver_id=current_user.id,
        is_read=False,
        receiver_deleted=False
    ).count()
    return jsonify({'count': count})

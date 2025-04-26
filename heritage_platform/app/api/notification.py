"""
通知和消息API模块

本模块提供与用户通知和私信相关的RESTful API接口，包括：
- 获取未读通知数量
- 将单个通知标记为已读
- 将所有通知标记为已读
- 获取未读私信数量

这些API接口需要用户登录后才能访问，用于支持实时通知系统和私信功能。
"""

from flask import jsonify, request, current_app
from flask_login import login_required, current_user  # 用户认证相关功能
from app.models import Notification, Message  # 通知和消息模型
from app import db, limiter  # 数据库和请求限制器
from . import api_bp  # API蓝图
import traceback  # 异常追踪

@api_bp.route('/notifications/unread-count')
@login_required
def get_unread_count():
    """获取未读通知数量API

    返回当前登录用户的未读通知数量。
    需要用户登录才能访问。

    路由: /notifications/unread-count
    方法: GET
    权限: 需要用户登录

    Returns:
        JSON: 包含未读通知数量的响应
        {
            "count": 5  // 未读通知数量
        }

    错误响应:
        401: 用户未登录
    """
    # 查询当前用户的未读通知数量
    count = Notification.query.filter_by(
        user_id=current_user.id,  # 当前登录用户
        is_read=False  # 未读状态
    ).count()

    # 返回未读通知数量
    return jsonify({'count': count})

@api_bp.route('/notifications/mark-read', methods=['POST'])
@login_required
def mark_as_read():
    """将通知标记为已读API

    将指定ID的通知标记为已读状态。
    需要用户登录，且只能操作自己的通知。

    路由: /notifications/mark-read
    方法: POST
    权限: 需要用户登录

    请求体(JSON):
        {
            "notification_id": 1  // 必填，要标记为已读的通知ID
        }

    Returns:
        JSON: 操作成功的响应
        {
            "message": "标记成功"
        }

    错误响应:
        400: 请求格式错误或参数缺失
        401: 用户未登录
        403: 无权操作该通知
        404: 通知不存在
        500: 服务器内部错误
    """
    try:
        # 检查请求的Content-Type是否正确
        content_type = request.headers.get('Content-Type', '')
        if not content_type.startswith('application/json'):
            # 记录警告日志
            current_app.logger.warning(f"Invalid Content-Type: {content_type}")
            # 返回错误响应
            return jsonify({
                'error': '请求必须是JSON格式',
                'content_type': content_type
            }), 400

        # 尝试解析JSON数据
        try:
            data = request.get_json(silent=True) or {}
        except Exception as e:
            # 记录JSON解析错误
            current_app.logger.error(f"JSON parsing error: {str(e)}")
            return jsonify({'error': 'JSON解析错误'}), 400

        # 获取通知ID
        notification_id = data.get('notification_id')

        # 验证通知ID是否存在
        if not notification_id:
            current_app.logger.warning("Missing notification_id parameter")
            return jsonify({'error': 'notification_id是必需参数'}), 400

        # 查询通知
        notification = Notification.query.get(notification_id)
        if not notification:
            current_app.logger.warning(f"Notification not found: {notification_id}")
            return jsonify({'error': f'找不到ID为{notification_id}的通知'}), 404

        # 验证当前用户是否有权限操作此通知
        if notification.user_id != current_user.id:
            return jsonify({'error': '无权限操作此通知'}), 403

        # 标记通知为已读
        notification.is_read = True
        # 提交事务
        db.session.commit()

        # 返回成功响应
        return jsonify({'message': '标记成功'})
    except Exception as e:
        # 记录详细错误日志，包含堆栈跟踪
        current_app.logger.error(f"Error in mark_as_read: {str(e)}\n{traceback.format_exc()}")
        # 返回通用错误响应
        return jsonify({'error': '处理请求时发生错误'}), 500

@api_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_as_read():
    """将所有通知标记为已读API

    将当前登录用户的所有未读通知标记为已读状态。
    需要用户登录。

    路由: /notifications/mark-all-read
    方法: POST
    权限: 需要用户登录

    Returns:
        JSON: 操作成功的响应
        {
            "message": "所有通知已标记为已读"
        }

    错误响应:
        401: 用户未登录
        500: 服务器内部错误
    """
    try:
        # 查询当前用户的所有未读通知
        notifications = Notification.query.filter_by(
            user_id=current_user.id,  # 当前登录用户
            is_read=False  # 未读状态
        ).all()

        # 将每个通知标记为已读
        for notification in notifications:
            notification.is_read = True

        # 提交事务
        db.session.commit()

        # 返回成功响应
        return jsonify({'message': '所有通知已标记为已读'})
    except Exception as e:
        # 记录错误日志
        current_app.logger.error(f"Error in mark_all_as_read: {str(e)}\n{traceback.format_exc()}")
        # 回滚事务
        db.session.rollback()
        # 返回错误响应
        return jsonify({'error': '处理请求时发生错误'}), 500

@api_bp.route('/messages/unread-count')
@login_required
@limiter.limit("15 per minute")  # 限制API调用频率，防止滥用
def get_unread_messages_count():
    """获取未读私信数量API

    返回当前登录用户的未读私信数量。
    需要用户登录才能访问。
    此API有频率限制，每分钟最多调用15次。

    路由: /messages/unread-count
    方法: GET
    权限: 需要用户登录
    限制: 每分钟最多15次请求

    Returns:
        JSON: 包含未读私信数量的响应
        {
            "count": 3  // 未读私信数量
        }

    错误响应:
        401: 用户未登录
        429: 请求过于频繁
    """
    try:
        # 查询当前用户的未读私信数量
        # 只计算未被接收者删除的私信
        count = Message.query.filter_by(
            receiver_id=current_user.id,  # 当前用户是接收者
            is_read=False,  # 未读状态
            receiver_deleted=False  # 接收者未删除
        ).count()

        # 返回未读私信数量
        return jsonify({'count': count})
    except Exception as e:
        # 记录错误日志
        current_app.logger.error(f"Error in get_unread_messages_count: {str(e)}")
        # 返回错误响应
        return jsonify({'error': '获取未读私信数量失败'}), 500

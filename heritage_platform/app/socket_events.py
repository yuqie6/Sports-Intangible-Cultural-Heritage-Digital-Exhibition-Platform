from flask import request, current_app, url_for
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from app import socketio, db
from app.models.message import Message, MessageGroup, MessageReadStatus
from app.models.user import User
from app.models.notification import Notification
from app.utils.websocket_manager import websocket_error_handler
import datetime
import json

@socketio.on('connect')
@websocket_error_handler
def handle_connect(data=None):
    """处理客户端连接事件"""
    if current_user.is_authenticated:
        current_app.websocket_manager.register_connection(current_user.id, request.sid)
        current_app.logger.info(f"用户 {current_user.username} (ID: {current_user.id}) 已连接")
        
        # 连接后自动加入用户私人房间，用于接收私信、通知等
        user_room = f"user_{current_user.id}"
        join_room(user_room)
        current_app.logger.info(f"用户 {current_user.username} (ID: {current_user.id}) 已加入个人房间: {user_room}")

@socketio.on('disconnect')
@websocket_error_handler
def handle_disconnect(data=None):
    """处理客户端断开连接事件"""
    if current_user.is_authenticated:
        current_app.websocket_manager.unregister_connection(current_user.id)
        current_app.logger.info(f"用户 {current_user.username} (ID: {current_user.id}) 已断开连接")

@socketio.on('join_group')
@websocket_error_handler
def handle_join_group(data):
    """处理用户加入群组聊天室事件"""
    if current_user.is_authenticated:
        group_id = data.get('group_id')
        if group_id:
            room_name = f"group_{group_id}"
            join_room(room_name)
            current_app.websocket_manager.update_activity(current_user.id)
            current_app.logger.info(f"用户 {current_user.username} (ID: {current_user.id}) 加入群组聊天室: {room_name}")
            return {'status': 'success', 'message': f'已加入群组聊天室: {room_name}'}

@socketio.on('leave_group')
@websocket_error_handler
def handle_leave_group(data):
    """处理用户离开群组聊天室事件"""
    if current_user.is_authenticated:
        group_id = data.get('group_id')
        if group_id:
            room_name = f"group_{group_id}"
            leave_room(room_name)
            current_app.websocket_manager.update_activity(current_user.id)
            current_app.logger.info(f"用户 {current_user.username} (ID: {current_user.id}) 离开群组聊天室: {room_name}")
            return {'status': 'success', 'message': f'已离开群组聊天室: {room_name}'}

@socketio.on('join_topic')
@websocket_error_handler
def handle_join_topic(data):
    """处理用户加入论坛主题事件"""
    if current_user.is_authenticated:
        topic_id = data.get('topic_id')
        if topic_id:
            room_name = f"topic_{topic_id}"
            join_room(room_name)
            current_app.websocket_manager.update_activity(current_user.id)
            current_app.logger.info(f"用户 {current_user.username} (ID: {current_user.id}) 加入论坛主题: {room_name}")
            return {'status': 'success', 'message': f'已加入论坛主题: {room_name}'}

@socketio.on('leave_topic')
@websocket_error_handler
def handle_leave_topic(data):
    """处理用户离开论坛主题事件"""
    if current_user.is_authenticated:
        topic_id = data.get('topic_id')
        if topic_id:
            room_name = f"topic_{topic_id}"
            leave_room(room_name)
            current_app.websocket_manager.update_activity(current_user.id)
            current_app.logger.info(f"用户 {current_user.username} (ID: {current_user.id}) 离开论坛主题: {room_name}")
            return {'status': 'success', 'message': f'已离开论坛主题: {room_name}'}

@socketio.on('send_group_message')
@websocket_error_handler
def handle_group_message(data):
    """处理群组消息发送事件"""
    if not current_user.is_authenticated:
        return {'status': 'error', 'message': '请先登录再发送消息'}
    
    group_id = data.get('group_id')
    content = data.get('content')
    
    if not group_id or not content:
        return {'status': 'error', 'message': '消息内容或群组ID不能为空'}
    
    try:
        # 查询群组是否存在
        group = MessageGroup.query.get(group_id)
        if not group:
            return {'status': 'error', 'message': '群组不存在'}
        
        # 检查当前用户是否为群组成员
        is_member = db.session.query(User).join(
            User.group_memberships
        ).filter(
            User.id == current_user.id,
            User.group_memberships.any(group_id=group_id)
        ).first() is not None
        
        if not is_member:
            return {'status': 'error', 'message': '您不是该群组的成员'}
        
        # 创建新消息
        new_message = Message(
            sender_id=current_user.id,
            content=content,
            group_id=group_id,
            message_type='group',
            created_at=datetime.datetime.now()
        )
        db.session.add(new_message)
        db.session.flush()  # 获取消息ID
        
        # 为群组内每个成员创建阅读状态记录
        for member in group.members:
            # 发送者自动标记为已读
            is_read = member.user_id == current_user.id
            read_at = datetime.datetime.now() if is_read else None
            
            status = MessageReadStatus(
                message_id=new_message.id,
                user_id=member.user_id,
                is_read=is_read,
                read_at=read_at
            )
            db.session.add(status)
        
        db.session.commit()
        
        # 准备发送给客户端的消息数据
        message_data = {
            'id': new_message.id,
            'content': new_message.content,
            'sender_id': new_message.sender_id,
            'sender_username': current_user.username,
            'sender_avatar': current_user.avatar if hasattr(current_user, 'avatar') else None,
            'created_at': new_message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'group_id': group_id
        }
        
        # 将消息广播到群组聊天室
        room_name = f"group_{group_id}"
        emit('new_group_message', message_data, to=room_name)
        
        return {'status': 'success', 'message': '消息发送成功', 'data': message_data}
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"发送群组消息出错: {str(e)}")
        return {'status': 'error', 'message': f'发送消息失败: {str(e)}'}

@socketio.on('delete_message')
@websocket_error_handler
def handle_delete_message(data):
    """处理消息删除事件"""
    if not current_user.is_authenticated:
        return {'status': 'error', 'message': '请先登录再操作'}
    
    message_id = data.get('message_id')
    
    if not message_id:
        return {'status': 'error', 'message': '消息ID不能为空'}
    
    try:
        # 获取消息
        message = Message.query.get(message_id)
        if not message:
            return {'status': 'error', 'message': '消息不存在'}
        
        # 检查当前用户是否有权限删除此消息
        # 只有消息发送者或群组管理员可以删除消息
        group_id = message.group_id
        group = MessageGroup.query.get(group_id)
        
        is_admin = False
        if group:
            # 检查用户是否是管理员
            is_admin = db.session.query(User).join(
                User.group_memberships
            ).filter(
                User.id == current_user.id,
                User.group_memberships.any(group_id=group_id, role='admin')
            ).first() is not None
        
        if message.sender_id != current_user.id and not is_admin:
            return {'status': 'error', 'message': '您没有权限删除此消息'}
        
        # 删除消息
        db.session.delete(message)
        db.session.commit()
        
        # 通知客户端消息已被删除
        room_name = f"group_{group_id}"
        emit('message_deleted', {'message_id': message_id}, to=room_name)
        
        return {'status': 'success', 'message': '消息已删除'}
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除消息出错: {str(e)}")
        return {'status': 'error', 'message': f'删除消息失败: {str(e)}'}

# 新增事件处理程序

@socketio.on('send_private_message')
@websocket_error_handler
def handle_private_message(data):
    """处理私信发送事件"""
    if not current_user.is_authenticated:
        return {'status': 'error', 'message': '请先登录再发送消息'}
    
    receiver_id = data.get('receiver_id')
    content = data.get('content')
    
    if not receiver_id or not content:
        return {'status': 'error', 'message': '消息内容或接收者ID不能为空'}
    
    try:
        # 查询接收者是否存在
        receiver = User.query.get(receiver_id)
        if not receiver:
            return {'status': 'error', 'message': '接收者不存在'}
        
        # 不能给自己发私信
        if int(receiver_id) == current_user.id:
            return {'status': 'error', 'message': '不能给自己发送私信'}
        
        # 创建私信
        message = Message(
            sender_id=current_user.id,
            receiver_id=receiver_id,
            content=content,
            message_type='personal',
            created_at=datetime.datetime.now()
        )
        
        db.session.add(message)
        db.session.commit()
        
        # 准备发送给客户端的消息数据
        message_data = {
            'id': message.id,
            'content': message.content,
            'sender_id': message.sender_id,
            'sender_username': current_user.username,
            'sender_avatar': current_user.avatar if hasattr(current_user, 'avatar') else None,
            'receiver_id': message.receiver_id,
            'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 将消息发送到接收者的私人房间
        receiver_room = f"user_{receiver_id}"
        emit('new_private_message', message_data, to=receiver_room)
        
        # 同时更新消息发送者的界面
        sender_room = f"user_{current_user.id}"
        emit('sent_private_message', message_data, to=sender_room)
        
        return {'status': 'success', 'message': '私信发送成功', 'data': message_data}
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"发送私信出错: {str(e)}")
        return {'status': 'error', 'message': f'发送私信失败: {str(e)}'}

@socketio.on('mark_message_read')
@websocket_error_handler
def handle_mark_message_read(data):
    """处理标记消息已读事件"""
    if not current_user.is_authenticated:
        return {'status': 'error', 'message': '请先登录再操作'}
    
    message_id = data.get('message_id')
    
    if not message_id:
        return {'status': 'error', 'message': '消息ID不能为空'}
    
    try:
        message = Message.query.get(message_id)
        if not message:
            return {'status': 'error', 'message': '消息不存在'}
        
        # 确保当前用户是接收者
        if message.message_type == 'personal' and message.receiver_id != current_user.id:
            return {'status': 'error', 'message': '无权操作该消息'}
        
        # 如果是群组消息，则更新当前用户的阅读状态
        if message.message_type == 'group':
            read_status = MessageReadStatus.query.filter_by(
                message_id=message_id,
                user_id=current_user.id
            ).first()
            
            if read_status:
                read_status.is_read = True
                read_status.read_at = datetime.datetime.now()
            else:
                return {'status': 'error', 'message': '读取状态记录不存在'}
        else:
            # 私信则直接更新is_read字段
            message.is_read = True
        
        db.session.commit()
        
        return {'status': 'success', 'message': '消息已标记为已读'}
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"标记消息已读出错: {str(e)}")
        return {'status': 'error', 'message': f'操作失败: {str(e)}'}

@socketio.on('join_notification_room')
@websocket_error_handler
def handle_join_notification_room(data=None):
    """处理用户加入通知房间事件"""
    if current_user.is_authenticated:
        room_name = f"notification_{current_user.id}"
        join_room(room_name)
        current_app.websocket_manager.update_activity(current_user.id)
        current_app.logger.info(f"用户 {current_user.username} (ID: {current_user.id}) 加入通知房间: {room_name}")
        return {'status': 'success', 'message': f'已加入通知房间: {room_name}'}

@socketio.on('post_comment')
@websocket_error_handler
def handle_post_comment(data):
    """处理论坛发表评论事件"""
    if not current_user.is_authenticated:
        return {'status': 'error', 'message': '请先登录再操作'}
    
    topic_id = data.get('topic_id')
    content = data.get('content')
    parent_id = data.get('parent_id')
    reply_to_user_id = data.get('reply_to_user_id')
    
    if not topic_id or not content:
        return {'status': 'error', 'message': '主题ID或内容不能为空'}
    
    try:
        from app.models import ForumTopic, ForumPost
        
        # 查询主题是否存在
        topic = ForumTopic.query.get(topic_id)
        if not topic:
            return {'status': 'error', 'message': '主题不存在'}
        
        # 检查主题是否已关闭
        if topic.is_closed and not current_user.is_admin:
            return {'status': 'error', 'message': '该主题已关闭，无法回复'}
        
        # 创建新评论
        post = ForumPost(
            topic_id=topic_id,
            user_id=current_user.id,
            content=content,
            parent_id=parent_id if parent_id else None,
            reply_to_user_id=reply_to_user_id if reply_to_user_id else None
        )
        
        db.session.add(post)
        
        # 更新主题最后活动时间
        topic.last_activity = post.created_at
        
        db.session.commit()
        
        # 准备评论数据
        post_data = {
            'id': post.id,
            'content': post.content,
            'user_id': post.user_id,
            'user_username': current_user.username,
            'user_avatar': current_user.avatar if hasattr(current_user, 'avatar') else None,
            'parent_id': post.parent_id,
            'created_at': post.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 将评论广播到主题房间
        room_name = f"topic_{topic_id}"
        emit('new_forum_post', post_data, to=room_name)
        
        # 如果回复了其他人的评论，则发送通知
        if reply_to_user_id and int(reply_to_user_id) != current_user.id:
            # 发送通知
            from app.routes.notification import send_notification
            
            parent_post = ForumPost.query.get(parent_id) if parent_id else None
            content_preview = post.content[:30] + '...' if len(post.content) > 30 else post.content
            
            notification_content = f"{current_user.username} 回复了你在 \"{topic.title}\" 中的评论：{content_preview}"
            send_notification(
                user_id=reply_to_user_id,
                content=notification_content,
                notification_type='reply',
                link=url_for('forum.topic', id=topic_id, _external=True),
                sender_id=current_user.id
            )
            
            # 发送实时通知
            notification_data = {
                'type': 'reply',
                'sender_id': current_user.id,
                'sender_username': current_user.username,
                'content': notification_content,
                'link': url_for('forum.topic', id=topic_id, _external=True),
                'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            receiver_room = f"user_{reply_to_user_id}"
            emit('new_notification', notification_data, to=receiver_room)
        
        # 如果是直接回复主题，且不是自己的主题，则通知主题创建者
        elif topic.user_id != current_user.id and not parent_id:
            # 发送通知
            from app.routes.notification import send_notification
            
            content_preview = post.content[:30] + '...' if len(post.content) > 30 else post.content
            notification_content = f"{current_user.username} 在你的主题 \"{topic.title}\" 中发表了评论：{content_preview}"
            
            send_notification(
                user_id=topic.user_id,
                content=notification_content,
                notification_type='reply',
                link=url_for('forum.topic', id=topic_id, _external=True),
                sender_id=current_user.id
            )
            
            # 发送实时通知
            notification_data = {
                'type': 'reply',
                'sender_id': current_user.id,
                'sender_username': current_user.username,
                'content': notification_content,
                'link': url_for('forum.topic', id=topic_id, _external=True),
                'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            receiver_room = f"user_{topic.user_id}"
            emit('new_notification', notification_data, to=receiver_room)
        
        return {'status': 'success', 'message': '评论发表成功', 'data': post_data}
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"发表评论出错: {str(e)}")
        return {'status': 'error', 'message': f'发表评论失败: {str(e)}'}

# 通知相关的函数
def emit_notification(user_id, notification_data):
    """
    发送实时通知到指定用户
    
    Parameters:
        user_id: 接收通知的用户ID
        notification_data: 通知数据字典
    """
    room_name = f"user_{user_id}"
    socketio.emit('new_notification', notification_data, to=room_name)
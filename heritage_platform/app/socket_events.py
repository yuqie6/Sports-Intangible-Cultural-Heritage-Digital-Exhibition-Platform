from flask import request, current_app
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from app import socketio, db
from app.models.message import Message, MessageGroup, MessageReadStatus
from app.models.user import User
import datetime
import json

# 用于存储用户与Socket.IO会话ID的映射关系
connected_users = {}

@socketio.on('connect')
def handle_connect():
    """处理客户端连接事件"""
    if current_user.is_authenticated:
        connected_users[current_user.id] = request.sid
        current_app.logger.info(f"用户 {current_user.username} (ID: {current_user.id}) 已连接")

@socketio.on('disconnect')
def handle_disconnect():
    """处理客户端断开连接事件"""
    if current_user.is_authenticated:
        if current_user.id in connected_users:
            del connected_users[current_user.id]
        current_app.logger.info(f"用户 {current_user.username} (ID: {current_user.id}) 已断开连接")

@socketio.on('join_group')
def handle_join_group(data):
    """处理用户加入群组聊天室事件"""
    if current_user.is_authenticated:
        group_id = data.get('group_id')
        if group_id:
            room_name = f"group_{group_id}"
            join_room(room_name)
            current_app.logger.info(f"用户 {current_user.username} (ID: {current_user.id}) 加入群组聊天室: {room_name}")
            return {'status': 'success', 'message': f'已加入群组聊天室: {room_name}'}

@socketio.on('leave_group')
def handle_leave_group(data):
    """处理用户离开群组聊天室事件"""
    if current_user.is_authenticated:
        group_id = data.get('group_id')
        if group_id:
            room_name = f"group_{group_id}"
            leave_room(room_name)
            current_app.logger.info(f"用户 {current_user.username} (ID: {current_user.id}) 离开群组聊天室: {room_name}")
            return {'status': 'success', 'message': f'已离开群组聊天室: {room_name}'}

@socketio.on('send_group_message')
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
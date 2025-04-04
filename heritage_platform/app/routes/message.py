from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request, jsonify, abort
from flask_login import login_required, current_user
from app.models.message import Message, MessageGroup, UserGroup, MessageReadStatus
from app.models.user import User
from app.forms.message import (
    MessageForm, ReplyMessageForm, GroupMessageForm, 
    BroadcastMessageForm, CreateGroupForm, AddMembersForm
)
from app import db, csrf
from sqlalchemy import or_, and_
from app.utils.decorators import role_required
import datetime

bp = Blueprint('message', __name__)

@bp.route('/messages')
@login_required
def message_list():
    """显示私信列表，包括发出的和收到的"""
    # 查询当前用户发送或接收的消息，且未被删除的消息
    sent_messages = Message.query.filter(
        Message.sender_id == current_user.id,
        Message.sender_deleted == False,
        or_(
            Message.message_type == 'personal',
            Message.message_type == 'broadcast'  # 包含群发消息
        )
    ).order_by(Message.created_at.desc()).all()

    received_messages = Message.query.filter(
        Message.receiver_id == current_user.id,
        Message.receiver_deleted == False,
        or_(
            Message.message_type == 'personal',
            Message.message_type == 'broadcast'  # 包含群发消息
        )
    ).order_by(Message.created_at.desc()).all()

    # 查询当前用户所在的群组
    user_groups = MessageGroup.query.join(MessageGroup.members).filter(
        UserGroup.user_id == current_user.id
    ).all()
    
    # 获取所有群组的最后一条消息
    group_last_messages = {}
    for group in user_groups:
        last_message = Message.query.filter(
            Message.group_id == group.id
        ).order_by(Message.created_at.desc()).first()
        
        if last_message:
            # 检查该消息对当前用户的已读状态
            read_status = MessageReadStatus.query.filter(
                MessageReadStatus.message_id == last_message.id,
                MessageReadStatus.user_id == current_user.id
            ).first()
            
            is_read = read_status and read_status.is_read
            group_last_messages[group.id] = {
                'message': last_message,
                'is_read': is_read
            }
    
    return render_template('message/list.html', 
                          sent_messages=sent_messages, 
                          received_messages=received_messages,
                          user_groups=user_groups,
                          group_last_messages=group_last_messages)

@bp.route('/messages/compose', methods=['GET', 'POST'])
@login_required
def compose():
    """发送新私信"""
    form = MessageForm()
    
    # 如果URL中有receiver参数，预填收件人
    if request.method == 'GET' and request.args.get('receiver'):
        form.receiver.data = request.args.get('receiver')
    
    if form.validate_on_submit():
        # 根据用户名查找收件人
        receiver = User.query.filter_by(username=form.receiver.data).first()
        if not receiver:
            flash('收件人不存在', 'danger')
            return render_template('message/compose.html', form=form)
            
        # 不能给自己发私信
        if receiver.id == current_user.id:
            flash('不能给自己发送私信', 'warning')
            return render_template('message/compose.html', form=form)
        
        # 创建私信
        message = Message(
            sender_id=current_user.id,
            receiver_id=receiver.id,
            content=form.content.data,
            message_type='personal'
        )
        
        try:
            db.session.add(message)
            db.session.commit()
            
            # 添加WebSocket实时通知功能
            try:
                from app.socket_events import socketio
                
                # 准备消息数据
                message_data = {
                    'id': message.id,
                    'content': message.content,
                    'sender_id': message.sender_id,
                    'sender_username': current_user.username,
                    'sender_avatar': current_user.avatar if hasattr(current_user, 'avatar') else None,
                    'receiver_id': message.receiver_id,
                    'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # 发送到接收者的WebSocket
                receiver_room = f"user_{receiver.id}"
                socketio.emit('new_private_message', message_data, to=receiver_room)
                
            except Exception as e:
                current_app.logger.error(f"发送WebSocket实时私信失败: {str(e)}")
                # 即使WebSocket发送失败，也不影响私信已保存到数据库
            
            flash('私信已发送', 'success')
            return redirect(url_for('message.message_list'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"发送私信失败: {str(e)}")
            flash('发送失败，请重试', 'danger')
    
    return render_template('message/compose.html', form=form)

@bp.route('/messages/<int:id>')
@login_required
def view(id):
    """查看私信详情"""
    # 确保当前用户是发送者或接收者
    message = Message.query.filter(
        Message.id == id,
        or_(
            and_(Message.sender_id == current_user.id, Message.sender_deleted == False),
            and_(Message.receiver_id == current_user.id, Message.receiver_deleted == False)
        ),
        or_(
            Message.message_type == 'personal',
            Message.message_type == 'broadcast'  # 允许查看群发消息
        )
    ).first_or_404()
    
    # 如果当前用户是接收者且消息未读，则标记为已读
    if message.receiver_id == current_user.id and not message.is_read:
        message.is_read = True
        db.session.commit()
    
    # 准备回复表单
    reply_form = ReplyMessageForm()
    if message.sender_id == current_user.id:
        # 如果当前用户是发送者，设置回复对象为接收者
        reply_form.receiver_id.data = message.receiver_id
    else:
        # 否则设置回复对象为发送者
        reply_form.receiver_id.data = message.sender_id
    
    return render_template('message/view.html', message=message, form=reply_form)

@bp.route('/message/messages/<int:id>')
@login_required
def view_message_alternate(id):
    """处理错误URL格式的重定向"""
    try:
        # 尝试找到消息
        message = Message.query.get(id)
        if not message:
            # 如果消息不存在，可能已被删除
            flash('您尝试访问的消息不存在或已被删除', 'warning')
            return redirect(url_for('message.message_list'))
        # 重定向到正确的URL格式
        return redirect(url_for('message.view', id=id))
    except Exception as e:
        current_app.logger.error(f"访问消息失败: {str(e)}")
        flash('访问消息时发生错误，已返回消息列表', 'warning')
        return redirect(url_for('message.message_list'))

@bp.route('/messages/reply', methods=['POST'])
@login_required
def reply():
    """回复私信"""
    form = ReplyMessageForm()
    
    if form.validate_on_submit():
        receiver_id = int(form.receiver_id.data)
        receiver = User.query.get(receiver_id)
        
        if not receiver:
            flash('收件人不存在', 'danger')
            return redirect(url_for('message.message_list'))
        
        # 创建私信
        message = Message(
            sender_id=current_user.id,
            receiver_id=receiver_id,
            content=form.content.data,
            message_type='personal'
        )
        
        try:
            db.session.add(message)
            db.session.commit()
            
            # 添加WebSocket实时通知功能
            try:
                from app.socket_events import socketio
                
                # 准备消息数据
                message_data = {
                    'id': message.id,
                    'content': message.content,
                    'sender_id': message.sender_id,
                    'sender_username': current_user.username,
                    'sender_avatar': current_user.avatar if hasattr(current_user, 'avatar') else None,
                    'receiver_id': message.receiver_id,
                    'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # 发送到接收者的WebSocket
                receiver_room = f"user_{receiver_id}"
                socketio.emit('new_private_message', message_data, to=receiver_room)
                
            except Exception as e:
                current_app.logger.error(f"发送WebSocket实时私信回复失败: {str(e)}")
                # 即使WebSocket发送失败，也不影响私信已保存到数据库
            
            flash('回复已发送', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"回复私信失败: {str(e)}")
            flash('发送失败，请重试', 'danger')
    
    return redirect(url_for('message.message_list'))

@bp.route('/messages/<int:id>/delete', methods=['POST'])
@login_required
@csrf.exempt
def delete(id):
    """删除私信"""
    message = Message.query.get_or_404(id)
    
    # 检查权限
    if message.sender_id != current_user.id and message.receiver_id != current_user.id:
        flash('无权限删除该私信', 'danger')
        return redirect(url_for('message.message_list'))
    
    try:
        # 根据用户角色（发送者或接收者）设置相应的删除标志
        if message.sender_id == current_user.id:
            message.sender_deleted = True
        if message.receiver_id == current_user.id:
            message.receiver_deleted = True
        
        # 只有当发送者和接收者都删除了私信，或者是群组消息，才真正从数据库删除
        if (message.message_type == 'personal' and message.sender_deleted and message.receiver_deleted) or message.message_type != 'personal':
            db.session.delete(message)
        else:
            db.session.add(message)
            
        db.session.commit()
        flash('私信已删除', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除私信失败: {str(e)}")
        flash('删除失败，请重试', 'danger')
    
    # 始终返回到消息列表页面，避免用户尝试返回到已删除的消息
    return redirect(url_for('message.message_list'))

@bp.route('/groups')
@login_required
def group_list():
    """显示当前用户的群组列表"""
    # 查询当前用户所在的群组
    user_groups = MessageGroup.query.join(MessageGroup.members).filter(
        UserGroup.user_id == current_user.id
    ).all()
    
    # 获取当前用户创建的群组
    created_groups = MessageGroup.query.filter_by(creator_id=current_user.id).all()
    
    return render_template('message/groups.html', 
                           user_groups=user_groups, 
                           created_groups=created_groups)

@bp.route('/groups/create', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'teacher'])
def create_group():
    """创建新消息群组"""
    form = CreateGroupForm()
    
    if form.validate_on_submit():
        try:
            # 创建新群组
            group = MessageGroup(
                name=form.name.data,
                description=form.description.data,
                group_type=form.group_type.data,
                creator_id=current_user.id
            )
            db.session.add(group)
            db.session.flush()  # 获取group.id
            
            # 创建者自动成为管理员
            creator_membership = UserGroup(
                user_id=current_user.id,
                group_id=group.id,
                role='admin'
            )
            db.session.add(creator_membership)
            
            # 添加选择的成员
            for member_id in form.members.data:
                member = UserGroup(
                    user_id=member_id,
                    group_id=group.id,
                    role='member'
                )
                db.session.add(member)
            
            db.session.commit()
            flash(f'群组 "{form.name.data}" 创建成功', 'success')
            return redirect(url_for('message.group_list'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建群组失败: {str(e)}")
            flash('创建群组失败，请重试', 'danger')
    
    return render_template('message/create_group.html', form=form)

@bp.route('/groups/<int:id>')
@login_required
def view_group(id):
    """查看群组详情和消息"""
    # 确保当前用户是群组成员
    membership = UserGroup.query.filter_by(
        user_id=current_user.id,
        group_id=id
    ).first_or_404()
    
    group = MessageGroup.query.get_or_404(id)
    
    # 查询群组消息，按时间升序排列，以便最早的消息显示在上方
    messages = Message.query.filter_by(
        group_id=id
    ).order_by(Message.created_at.asc()).all()
    
    # 将所有未读消息标记为已读
    unread_statuses = MessageReadStatus.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).join(MessageReadStatus.message).filter(
        Message.group_id == id
    ).all()
    
    for status in unread_statuses:
        status.is_read = True
        status.read_at = datetime.datetime.now()
    
    # 获取群组成员列表
    members = User.query.join(UserGroup).filter(
        UserGroup.group_id == id
    ).all()
    
    # 准备发送消息表单
    form = GroupMessageForm()
    form.group_id.data = id  # 预选当前群组
    
    try:
        db.session.commit()  # 提交已读状态变更
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新消息已读状态失败: {str(e)}")
    
    return render_template('message/view_group.html', 
                           group=group, 
                           messages=messages, 
                           members=members, 
                           form=form,
                           membership=membership)

@bp.route('/groups/<int:id>/send', methods=['POST'])
@login_required
def send_group_message(id):
    """向群组发送消息"""
    # 确保当前用户是群组成员
    membership = UserGroup.query.filter_by(
        user_id=current_user.id,
        group_id=id
    ).first_or_404()
    
    form = GroupMessageForm()
    form.group_id.data = id  # 设置群组ID
    
    if form.validate_on_submit():
        try:
            # 创建群组消息
            message = Message(
                sender_id=current_user.id,
                content=form.content.data,
                group_id=id,
                message_type='group'
            )
            db.session.add(message)
            db.session.flush()  # 获取message.id
            
            # 为每个群组成员创建阅读状态记录
            group = MessageGroup.query.get(id)
            for member in group.members:
                # 发送者自动标记为已读
                is_read = member.user_id == current_user.id
                read_at = datetime.datetime.now() if is_read else None
                
                status = MessageReadStatus(
                    message_id=message.id,
                    user_id=member.user_id,
                    is_read=is_read,
                    read_at=read_at
                )
                db.session.add(status)
            
            db.session.commit()
            flash('消息已发送到群组', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"发送群组消息失败: {str(e)}")
            flash('发送失败，请重试', 'danger')
    
    return redirect(url_for('message.view_group', id=id))

@bp.route('/groups/<int:id>/members')
@login_required
def group_members(id):
    """管理群组成员"""
    # 确保当前用户是群组管理员
    membership = UserGroup.query.filter_by(
        user_id=current_user.id,
        group_id=id,
        role='admin'
    ).first_or_404()
    
    group = MessageGroup.query.get_or_404(id)
    
    # 获取成员信息
    members = db.session.query(User, UserGroup).join(
        UserGroup, User.id == UserGroup.user_id
    ).filter(
        UserGroup.group_id == id
    ).all()
    
    # 准备添加成员表单
    form = AddMembersForm(group_id=id)
    
    return render_template('message/group_members.html', 
                           group=group, 
                           members=members, 
                           form=form)

@bp.route('/groups/<int:id>/members/add', methods=['POST'])
@login_required
def add_members(id):
    """向群组添加成员"""
    # 确保当前用户是群组管理员
    membership = UserGroup.query.filter_by(
        user_id=current_user.id,
        group_id=id,
        role='admin'
    ).first_or_404()
    
    form = AddMembersForm(group_id=id)
    
    if form.validate_on_submit():
        try:
            # 添加所选成员到群组
            added_count = 0
            for user_id in form.members.data:
                # 检查用户是否已经是成员
                existing = UserGroup.query.filter_by(
                    user_id=user_id,
                    group_id=id
                ).first()
                
                if not existing:
                    member = UserGroup(
                        user_id=user_id,
                        group_id=id,
                        role='member'
                    )
                    db.session.add(member)
                    added_count += 1
            
            if added_count > 0:
                db.session.commit()
                flash(f'成功添加 {added_count} 名成员', 'success')
            else:
                flash('未添加任何新成员', 'info')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"添加群组成员失败: {str(e)}")
            flash('添加成员失败，请重试', 'danger')
    
    return redirect(url_for('message.group_members', id=id))

@bp.route('/groups/<int:group_id>/members/<int:user_id>/remove', methods=['POST'])
@login_required
@csrf.exempt
def remove_member(group_id, user_id):
    """从群组中移除成员"""
    # 确保当前用户是群组管理员
    membership = UserGroup.query.filter_by(
        user_id=current_user.id,
        group_id=group_id,
        role='admin'
    ).first_or_404()
    
    # 不能移除自己
    if user_id == current_user.id:
        flash('不能移除自己，如果要离开群组，请使用退出群组功能', 'warning')
        return redirect(url_for('message.group_members', id=group_id))
    
    try:
        # 查找并删除成员关系
        member = UserGroup.query.filter_by(
            user_id=user_id,
            group_id=group_id
        ).first()
        
        if member:
            db.session.delete(member)
            db.session.commit()
            flash('成员已从群组移除', 'success')
        else:
            flash('未找到该成员', 'warning')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"移除群组成员失败: {str(e)}")
        flash('移除成员失败，请重试', 'danger')
    
    return redirect(url_for('message.group_members', id=group_id))

@bp.route('/groups/<int:id>/leave', methods=['POST'])
@login_required
@csrf.exempt
def leave_group(id):
    """离开群组"""
    # 查找用户的群组成员关系
    membership = UserGroup.query.filter_by(
        user_id=current_user.id,
        group_id=id
    ).first_or_404()
    
    # 获取群组信息
    group = MessageGroup.query.get_or_404(id)
    
    # 如果是创建者，需要特殊处理
    if group.creator_id == current_user.id:
        # 查找其他管理员
        other_admin = UserGroup.query.filter(
            UserGroup.group_id == id,
            UserGroup.role == 'admin',
            UserGroup.user_id != current_user.id
        ).first()
        
        if not other_admin:
            flash('您是群组创建者，请先指定新的管理员', 'warning')
            return redirect(url_for('message.view_group', id=id))
    
    try:
        db.session.delete(membership)
        db.session.commit()
        flash(f'已成功退出群组 "{group.name}"', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"退出群组失败: {str(e)}")
        flash('退出群组失败，请重试', 'danger')
    
    return redirect(url_for('message.group_list'))

@bp.route('/groups/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_group(id):
    """编辑群组信息"""
    # 确保当前用户是群组管理员
    membership = UserGroup.query.filter_by(
        user_id=current_user.id,
        group_id=id,
        role='admin'
    ).first_or_404()
    
    group = MessageGroup.query.get_or_404(id)
    
    form = CreateGroupForm(obj=group)
    
    # 移除members字段的验证，因为在编辑时不修改成员
    delattr(form, 'members')
    
    if form.validate_on_submit():
        try:
            group.name = form.name.data
            group.description = form.description.data
            group.group_type = form.group_type.data
            
            db.session.commit()
            flash('群组信息已更新', 'success')
            return redirect(url_for('message.view_group', id=id))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新群组信息失败: {str(e)}")
            flash('更新失败，请重试', 'danger')
    
    return render_template('message/edit_group.html', form=form, group=group)

@bp.route('/broadcast', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'teacher'])
def broadcast():
    """群发消息功能"""
    form = BroadcastMessageForm()
    
    if form.validate_on_submit():
        recipient_type = form.recipient_type.data
        content = form.content.data
        
        # 确定接收者列表
        recipients = []
        
        if recipient_type == 'all':
            recipients = User.query.all()
        elif recipient_type == 'students':
            recipients = User.query.filter_by(role='student').all()
        elif recipient_type == 'teachers':
            recipients = User.query.filter_by(role='teacher').all()
        elif recipient_type == 'admins':
            recipients = User.query.filter_by(role='admin').all()
        elif recipient_type == 'specific_groups':
            # 获取所选群组的所有成员
            for group_id in form.groups.data:
                group = MessageGroup.query.get(group_id)
                if group:
                    for member in group.members:
                        if member.user_id != current_user.id:  # 排除自己
                            user = User.query.get(member.user_id)
                            if user not in recipients:
                                recipients.append(user)
        
        # 排除自己
        recipients = [r for r in recipients if r.id != current_user.id]
        
        try:
            # 发送私信给每个接收者
            for recipient in recipients:
                message = Message(
                    sender_id=current_user.id,
                    receiver_id=recipient.id,
                    content=content,
                    message_type='broadcast'
                )
                db.session.add(message)
            
            db.session.commit()
            flash(f'群发消息已发送给 {len(recipients)} 位用户', 'success')
            return redirect(url_for('message.message_list'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"群发消息失败: {str(e)}")
            flash('发送失败，请重试', 'danger')
    
    return render_template('message/broadcast.html', form=form)

@bp.route('/groups/<int:group_id>/members/<int:user_id>/promote', methods=['POST'])
@login_required
@csrf.exempt
def promote_to_admin(group_id, user_id):
    """将普通成员提升为群组管理员"""
    # 确保当前用户是群组管理员
    membership = UserGroup.query.filter_by(
        user_id=current_user.id,
        group_id=group_id,
        role='admin'
    ).first_or_404()
    
    # 不能提升自己（因为已经是管理员了）
    if user_id == current_user.id:
        flash('您已经是管理员', 'info')
        return redirect(url_for('message.group_members', id=group_id))
    
    try:
        # 查找该成员
        member = UserGroup.query.filter_by(
            user_id=user_id,
            group_id=group_id
        ).first_or_404()
        
        # 如果已经是管理员，不需要操作
        if member.role == 'admin':
            flash('该成员已经是管理员', 'info')
        else:
            # 修改角色为管理员
            member.role = 'admin'
            db.session.commit()
            
            # 获取用户信息以在消息中显示
            user = User.query.get(user_id)
            flash(f'已成功将 {user.username} 设置为群组管理员', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"提升管理员失败: {str(e)}")
        flash('操作失败，请重试', 'danger')
    
    return redirect(url_for('message.group_members', id=group_id))

from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request
from flask_login import login_required, current_user
from app.models import Message, User
from app.forms.message import MessageForm, ReplyMessageForm
from app import db
from sqlalchemy import or_, and_

bp = Blueprint('message', __name__)

@bp.route('/messages')
@login_required
def message_list():
    """显示私信列表，包括发出的和收到的"""
    # 查询当前用户发送或接收的消息，且未被删除的消息
    sent_messages = Message.query.filter(
        Message.sender_id == current_user.id,
        Message.sender_deleted == False
    ).order_by(Message.created_at.desc()).all()

    received_messages = Message.query.filter(
        Message.receiver_id == current_user.id,
        Message.receiver_deleted == False
    ).order_by(Message.created_at.desc()).all()
    
    return render_template('message/list.html', 
                          sent_messages=sent_messages, 
                          received_messages=received_messages)

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
            content=form.content.data
        )
        
        try:
            db.session.add(message)
            db.session.commit()
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
            content=form.content.data
        )
        
        try:
            db.session.add(message)
            db.session.commit()
            flash('回复已发送', 'success')
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"回复私信失败: {str(e)}")
            flash('发送失败，请重试', 'danger')
    
    return redirect(url_for('message.message_list'))

@bp.route('/messages/<int:id>/delete', methods=['POST'])
@login_required
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
        
        # 只有当发送者和接收者都删除了私信，才真正从数据库删除
        if message.sender_deleted and message.receiver_deleted:
            db.session.delete(message)
        else:
            db.session.add(message)
            
        db.session.commit()
        flash('私信已删除', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除私信失败: {str(e)}")
        flash('删除失败，请重试', 'danger')
    
    return redirect(url_for('message.message_list'))
"""
用户管理路由模块

本模块定义了与用户管理相关的所有路由处理函数，包括：
- 用户个人资料：查看和编辑个人资料、修改密码
- 用户内容管理：查看自己发布的内容和收藏
- 管理员功能：用户管理、系统统计、角色管理等
- API接口：提供用户数据和统计信息的JSON接口

这些路由共同构成了平台的用户管理系统，包括普通用户的个人中心和管理员的后台管理功能。
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import current_user, login_required
from app import db
from app.models import User, Content, HeritageItem, ForumTopic, ForumPost, Favorite
from app.forms.user import ProfileForm, PasswordForm, UserForm
from app.utils.file_handlers import save_file
from app.utils.decorators import admin_required

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile')
@login_required
def profile():
    """用户个人资料页面

    显示当前登录用户的个人资料和活动统计信息，包括：
    - 基本个人信息（用户名、邮箱、头像等）
    - 发布内容统计
    - 创建的非遗项目统计（仅教师和管理员）
    - 论坛活动统计（主题和回复）
    - 最近收藏的内容

    路由: /profile
    方法: GET
    权限: 需要用户登录

    返回:
        HTML: 渲染后的个人资料页面，包含用户信息和统计数据
    """
    # 获取用户发布的内容统计
    content_count = Content.query.filter_by(user_id=current_user.id).count()

    # 获取用户创建的非遗项目（如果是教师或管理员）
    heritage_count = 0
    if current_user.is_teacher or current_user.is_admin:
        heritage_count = HeritageItem.query.filter_by(created_by=current_user.id).count()

    # 获取论坛统计：用户创建的主题数和发表的回复数
    topic_count = ForumTopic.query.filter_by(user_id=current_user.id).count()
    post_count = ForumPost.query.filter_by(user_id=current_user.id).count()

    # 获取用户的最近收藏内容（最多5条）
    favorites = Favorite.query.filter_by(user_id=current_user.id).order_by(
        Favorite.created_at.desc()).limit(5).all()
    favorite_contents = []
    for fav in favorites:
        # 获取每个收藏对应的内容对象
        content = Content.query.get(fav.content_id)
        if content:  # 确保内容存在（可能已被删除）
            favorite_contents.append(content)

    # 渲染个人资料页面模板，传入所有统计数据和收藏内容
    return render_template('user/profile.html',
                           content_count=content_count,
                           heritage_count=heritage_count,
                           topic_count=topic_count,
                           post_count=post_count,
                           favorite_contents=favorite_contents)

@user_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """编辑个人资料页面"""
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        try:
            # 更新基本信息
            current_user.username = form.username.data
            current_user.email = form.email.data

            # 处理头像上传
            if form.avatar.data and hasattr(form.avatar.data, 'filename'):
                # 确认avatar.data是文件对象而不是字符串
                avatar_path = save_file(form.avatar.data, 'image')
                if avatar_path:
                    # 修复：确保路径正确，使用url_for生成带/static/前缀的路径
                    current_user.avatar = url_for('static', filename=avatar_path)
                    current_app.logger.info(f"设置用户头像路径为: {current_user.avatar}")

            db.session.commit()
            flash('个人资料更新成功', 'success')
            return redirect(url_for('user.profile'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新个人资料失败: {str(e)}")
            flash('更新个人资料失败，请稍后重试', 'danger')

    return render_template('user/edit_profile.html', form=form)

@user_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码页面"""
    form = PasswordForm()

    if form.validate_on_submit():
        if not current_user.verify_password(form.current_password.data):
            flash('当前密码不正确', 'danger')
            return render_template('user/change_password.html', form=form)

        try:
            current_user.password = form.new_password.data
            db.session.commit()
            flash('密码修改成功', 'success')
            return redirect(url_for('user.profile'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"修改密码失败: {str(e)}")
            flash('修改密码失败，请稍后重试', 'danger')

    return render_template('user/change_password.html', form=form)

@user_bp.route('/my_contents')
@login_required
def my_contents():
    """我的内容页面"""
    page = request.args.get('page', 1, type=int)

    pagination = Content.query.filter_by(user_id=current_user.id).order_by(
        Content.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)

    contents = pagination.items

    return render_template('user/my_contents.html',
                           contents=contents,
                           pagination=pagination)

@user_bp.route('/my_favorites')
@login_required
def my_favorites():
    """我的收藏页面"""
    page = request.args.get('page', 1, type=int)

    # 获取用户收藏的内容ID
    favorite_ids = db.session.query(Favorite.content_id).filter_by(
        user_id=current_user.id).all()
    favorite_ids = [f[0] for f in favorite_ids]

    # 查询这些内容
    pagination = Content.query.filter(Content.id.in_(favorite_ids)).order_by(
        Content.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)

    contents = pagination.items

    return render_template('user/my_favorites.html',
                           contents=contents,
                           pagination=pagination)

@user_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """管理员控制面板"""
    # 获取系统概览数据
    user_count = User.query.count()
    heritage_count = HeritageItem.query.count()
    content_count = Content.query.count()
    topic_count = ForumTopic.query.count()

    # 获取最近注册的用户
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

    # 获取最近创建的内容
    recent_contents = Content.query.order_by(Content.created_at.desc()).limit(5).all()

    return render_template('user/dashboard.html',
                           user_count=user_count,
                           heritage_count=heritage_count,
                           content_count=content_count,
                           topic_count=topic_count,
                           recent_users=recent_users,
                           recent_contents=recent_contents,
                           user_bp=user_bp)

@user_bp.route('/manage_users')
@login_required
@admin_required
def manage_users():
    """用户管理页面"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    role = request.args.get('role')
    search = request.args.get('search')

    query = User.query

    # 按角色筛选
    if role:
        query = query.filter(User.role == role)

    # 按用户名或邮箱搜索
    if search:
        query = query.filter(
            (User.username.like(f'%{search}%')) |
            (User.email.like(f'%{search}%'))
        )

    # 分页处理
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    users = pagination.items

    return render_template('user/manage_users.html',
                           users=users,
                           pagination=pagination,
                           current_role=role,
                           search=search)

@user_bp.route('/api/users')
@login_required
@admin_required
def api_users():
    """用户API - 返回JSON格式的用户列表，用于AJAX加载"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    role = request.args.get('role')
    search = request.args.get('search')

    query = User.query

    if role:
        query = query.filter(User.role == role)

    if search:
        query = query.filter(
            (User.username.like(f'%{search}%')) |
            (User.email.like(f'%{search}%'))
        )

    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)

    users = []
    for user in pagination.items:
        users.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'avatar': user.avatar,
            'role': user.role,
            'created_at': user.created_at.strftime('%Y-%m-%d'),
            'is_admin': user.is_admin,
            'is_teacher': user.is_teacher
        })

    return jsonify({
        'users': users,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    })

@user_bp.route('/edit_user/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    """编辑用户信息"""
    user = User.query.get_or_404(id)
    form = UserForm(obj=user)

    if form.validate_on_submit():
        try:
            user.username = form.username.data
            user.email = form.email.data
            user.role = form.role.data

            # 如果填写了密码，则更新密码
            if form.password.data:
                user.password = form.password.data

            # 处理头像上传
            if form.avatar.data and hasattr(form.avatar.data, 'filename'):
                # 确认avatar.data是文件对象而不是字符串
                avatar_path = save_file(form.avatar.data, 'image')
                if avatar_path:
                    # 修复：使用url_for生成正确的静态资源URL
                    user.avatar = url_for('static', filename=avatar_path)

            db.session.commit()
            flash('用户信息更新成功', 'success')
            return redirect(url_for('user.manage_users'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新用户信息失败: {str(e)}")
            flash('更新用户信息失败，请稍后重试', 'danger')

    return render_template('user/edit_user.html', form=form, user=user)

@user_bp.route('/create_user', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """创建新用户"""
    form = UserForm()

    if form.validate_on_submit():
        try:
            # 检查用户名是否已存在
            if User.query.filter_by(username=form.username.data).first():
                flash('用户名已存在', 'danger')
                return render_template('user/create_user.html', form=form)

            # 检查邮箱是否已存在
            if User.query.filter_by(email=form.email.data).first():
                flash('邮箱已被注册', 'danger')
                return render_template('user/create_user.html', form=form)

            user = User(
                username=form.username.data,
                email=form.email.data,
                role=form.role.data
            )

            # 设置密码
            user.password = form.password.data

            # 处理头像上传
            if form.avatar.data and hasattr(form.avatar.data, 'filename'):
                # 确认avatar.data是文件对象而不是字符串
                avatar_path = save_file(form.avatar.data, 'image')
                if avatar_path:
                    # 修复：使用url_for生成正确的静态资源URL
                    user.avatar = url_for('static', filename=avatar_path)

            db.session.add(user)
            db.session.commit()
            flash('用户创建成功', 'success')
            return redirect(url_for('user.manage_users'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建用户失败: {str(e)}")
            flash('创建用户失败，请稍后重试', 'danger')

    return render_template('user/create_user.html', form=form)

@user_bp.route('/delete_user/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    """删除用户"""
    user = User.query.get_or_404(id)

    # 不允许删除自己
    if user.id == current_user.id:
        flash('不能删除当前登录用户', 'danger')
        return redirect(url_for('user.manage_users'))

    try:
        # 删除用户关联的内容和数据
        # 这里可以根据实际需求处理关联数据
        # 例如：删除用户发布的内容、评论等

        # 删除用户
        db.session.delete(user)
        db.session.commit()
        flash('用户删除成功', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除用户失败: {str(e)}")
        flash('删除用户失败，请稍后重试', 'danger')

    return redirect(url_for('user.manage_users'))

@user_bp.route('/api/delete_user', methods=['POST'])
@login_required
@admin_required
def api_delete_user():
    """用户删除API - 用于AJAX请求"""
    try:
        user_id = request.json.get('id')
        if not user_id:
            return jsonify({'success': False, 'message': '未提供用户ID'})

        user = User.query.get_or_404(user_id)

        # 不允许删除自己
        if user.id == current_user.id:
            return jsonify({'success': False, 'message': '不能删除当前登录用户'})

        # 删除用户
        db.session.delete(user)
        db.session.commit()

        return jsonify({'success': True, 'message': '用户删除成功'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"API删除用户失败: {str(e)}")
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'})

@user_bp.route('/api/user-activity-stats')
@login_required
def get_user_activity_stats():
    """获取用户活动统计数据"""
    from datetime import datetime, timedelta
    from sqlalchemy import func

    # 获取过去30天的数据
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    # 按日期统计内容发布
    content_stats = db.session.query(
        func.date(Content.created_at).label('date'),
        func.count(Content.id).label('count')
    ).filter(
        Content.user_id == current_user.id,
        Content.created_at >= start_date,
        Content.created_at <= end_date
    ).group_by(func.date(Content.created_at)).all()

    # 按日期统计论坛主题
    topic_stats = db.session.query(
        func.date(ForumTopic.created_at).label('date'),
        func.count(ForumTopic.id).label('count')
    ).filter(
        ForumTopic.user_id == current_user.id,
        ForumTopic.created_at >= start_date,
        ForumTopic.created_at <= end_date
    ).group_by(func.date(ForumTopic.created_at)).all()

    # 按日期统计论坛回复
    post_stats = db.session.query(
        func.date(ForumPost.created_at).label('date'),
        func.count(ForumPost.id).label('count')
    ).filter(
        ForumPost.user_id == current_user.id,
        ForumPost.created_at >= start_date,
        ForumPost.created_at <= end_date
    ).group_by(func.date(ForumPost.created_at)).all()

    # 生成日期列表和对应的统计数据
    dates = [(start_date + timedelta(days=x)).strftime('%Y-%m-%d') for x in range(31)]

    # 初始化数据数组
    content_counts = [0] * 31
    topic_counts = [0] * 31
    post_counts = [0] * 31

    # 填充实际数据
    for stat in content_stats:
        date_str = stat.date.strftime('%Y-%m-%d')
        if date_str in dates:
            idx = dates.index(date_str)
            content_counts[idx] = stat.count

    for stat in topic_stats:
        date_str = stat.date.strftime('%Y-%m-%d')
        if date_str in dates:
            idx = dates.index(date_str)
            topic_counts[idx] = stat.count

    for stat in post_stats:
        date_str = stat.date.strftime('%Y-%m-%d')
        if date_str in dates:
            idx = dates.index(date_str)
            post_counts[idx] = stat.count

    return jsonify({
        'dates': dates,
        'content_counts': content_counts,
        'topic_counts': topic_counts,
        'post_counts': post_counts
    })

@user_bp.route('/api/system-activity-stats')
@login_required
@admin_required
def get_system_activity_stats():
    """获取系统级别的活动统计数据"""
    from datetime import datetime, timedelta
    from sqlalchemy import func

    # 获取过去30天的数据
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    # 按日期统计全系统的内容发布
    content_stats = db.session.query(
        func.date(Content.created_at).label('date'),
        func.count(Content.id).label('count')
    ).filter(
        Content.created_at >= start_date,
        Content.created_at <= end_date
    ).group_by(func.date(Content.created_at)).all()

    # 按日期统计全系统的论坛主题
    topic_stats = db.session.query(
        func.date(ForumTopic.created_at).label('date'),
        func.count(ForumTopic.id).label('count')
    ).filter(
        ForumTopic.created_at >= start_date,
        ForumTopic.created_at <= end_date
    ).group_by(func.date(ForumTopic.created_at)).all()

    # 按日期统计全系统的用户注册
    user_stats = db.session.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('count')
    ).filter(
        User.created_at >= start_date,
        User.created_at <= end_date
    ).group_by(func.date(User.created_at)).all()

    # 生成日期列表和对应的统计数据
    dates = [(start_date + timedelta(days=x)).strftime('%Y-%m-%d') for x in range(31)]

    # 初始化数据数组
    content_counts = [0] * 31
    topic_counts = [0] * 31
    user_counts = [0] * 31

    # 填充实际数据
    for stat in content_stats:
        date_str = stat.date.strftime('%Y-%m-%d')
        if date_str in dates:
            idx = dates.index(date_str)
            content_counts[idx] = stat.count

    for stat in topic_stats:
        date_str = stat.date.strftime('%Y-%m-%d')
        if date_str in dates:
            idx = dates.index(date_str)
            topic_counts[idx] = stat.count

    for stat in user_stats:
        date_str = stat.date.strftime('%Y-%m-%d')
        if date_str in dates:
            idx = dates.index(date_str)
            user_counts[idx] = stat.count

    return jsonify({
        'dates': dates,
        'content_counts': content_counts,
        'topic_counts': topic_counts,
        'user_counts': user_counts
    })

@user_bp.route('/api/change_role', methods=['POST'])
@login_required
@admin_required
def api_change_role():
    """更改用户角色API - 用于AJAX请求"""
    try:
        user_id = request.json.get('id')
        new_role = request.json.get('role')

        if not user_id or not new_role:
            return jsonify({'success': False, 'message': '参数不完整'})

        if new_role not in ['admin', 'teacher', 'student']:
            return jsonify({'success': False, 'message': '无效的角色'})

        user = User.query.get_or_404(user_id)
        user.role = new_role
        db.session.commit()

        return jsonify({'success': True, 'message': '角色更改成功'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"API更改用户角色失败: {str(e)}")
        return jsonify({'success': False, 'message': f'更改失败: {str(e)}'})

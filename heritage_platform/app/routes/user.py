from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_required
from app import db
from app.models import User, Content, HeritageItem, ForumTopic, ForumPost, Comment, Favorite, Like
from app.forms.user import ProfileForm, PasswordForm
from app.utils.file_handlers import save_file
from app.utils.decorators import admin_required
from sqlalchemy.exc import SQLAlchemyError

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile')
@login_required
def profile():
    """用户个人资料页面"""
    # 获取用户发布的内容统计
    content_count = Content.query.filter_by(user_id=current_user.id).count()
    
    # 获取用户创建的非遗项目（如果是教师）
    heritage_count = 0
    if current_user.is_teacher or current_user.is_admin:
        heritage_count = HeritageItem.query.filter_by(created_by=current_user.id).count()
    
    # 获取论坛统计
    topic_count = ForumTopic.query.filter_by(user_id=current_user.id).count()
    post_count = ForumPost.query.filter_by(user_id=current_user.id).count()
    
    # 获取用户的收藏内容
    favorites = Favorite.query.filter_by(user_id=current_user.id).order_by(
        Favorite.created_at.desc()).limit(5).all()
    favorite_contents = []
    for fav in favorites:
        content = Content.query.get(fav.content_id)
        if content:
            favorite_contents.append(content)
    
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
            if form.avatar.data:
                avatar_path = save_file(form.avatar.data, 'image')
                if avatar_path:
                    current_user.avatar = avatar_path
            
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
                           recent_contents=recent_contents)

"""
用户认证路由模块

本模块定义了与用户认证相关的所有路由处理函数，包括：
- 用户登录：验证用户身份并创建会话
- 用户登出：结束用户会话
- 用户注册：创建新用户账号

这些路由共同构成了平台的用户认证系统，是用户访问平台功能的入口。
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from app.forms.auth import LoginForm, RegistrationForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录

    处理用户登录请求，验证用户身份并创建会话。
    如果用户已登录，则重定向到首页。
    支持"记住我"功能和登录后重定向到原请求页面。

    路由: /login
    方法:
        GET: 显示登录表单
        POST: 处理表单提交，验证用户身份

    URL参数:
        next (str, 可选): 登录成功后重定向的目标URL

    表单字段:
        username: 用户名
        password: 密码
        remember_me: 是否记住登录状态

    返回:
        GET: 渲染登录表单页面
        POST成功: 重定向到next参数指定的URL或首页
        POST失败: 显示错误消息并重新渲染登录表单
    """
    # 如果用户已登录，直接重定向到首页
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    # 创建登录表单实例
    form = LoginForm()

    # 如果是POST请求且表单验证通过
    if form.validate_on_submit():
        # 根据用户名查询用户
        user = User.query.filter_by(username=form.username.data).first()

        # 验证用户存在且密码正确
        if user is not None and user.verify_password(form.password.data):
            # 登录用户，设置记住我选项
            login_user(user, remember=form.remember_me.data)

            # 获取next参数，用于登录后重定向
            next_page = request.args.get('next')

            # 安全检查：确保next参数是相对URL（防止开放重定向漏洞）
            if next_page is None or not next_page.startswith('/'):
                next_page = url_for('main.index')  # 默认重定向到首页

            # 重定向到目标页面
            return redirect(next_page)

        # 用户名或密码错误，显示错误消息
        flash('用户名或密码错误', 'danger')

    # GET请求或表单验证失败时，渲染登录表单
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """用户登出

    结束当前用户的会话，清除登录状态。
    需要用户已登录才能访问。
    登出后重定向到首页并显示成功消息。

    路由: /logout
    方法: GET
    权限: 需要用户登录

    返回:
        重定向到首页，并显示登出成功的提示消息
    """
    # 登出当前用户，清除会话
    logout_user()

    # 显示成功消息
    flash('您已成功登出', 'success')

    # 重定向到首页
    return redirect(url_for('main.index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册

    处理新用户注册请求，创建新的用户账号。
    如果用户已登录，则重定向到首页。
    注册成功后重定向到登录页面。

    路由: /register
    方法:
        GET: 显示注册表单
        POST: 处理表单提交，创建新用户

    表单字段:
        username: 用户名，必须唯一
        email: 电子邮箱，必须唯一
        password: 密码
        confirm_password: 确认密码，必须与密码一致

    返回:
        GET: 渲染注册表单页面
        POST成功: 重定向到登录页面，并显示注册成功消息
        POST失败: 显示错误消息并重新渲染注册表单
    """
    # 如果用户已登录，直接重定向到首页
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    # 创建注册表单实例
    form = RegistrationForm()

    # 如果是POST请求且表单验证通过
    if form.validate_on_submit():
        # 创建新用户对象
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data  # 密码会在模型中自动哈希处理
        )

        # 添加到数据库并提交
        db.session.add(user)
        db.session.commit()

        # 显示成功消息
        flash('注册成功，现在您可以登录了', 'success')

        # 重定向到登录页面
        return redirect(url_for('auth.login'))

    # GET请求或表单验证失败时，渲染注册表单
    return render_template('auth/register.html', form=form)

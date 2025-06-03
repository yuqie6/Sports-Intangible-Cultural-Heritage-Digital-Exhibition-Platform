"""
装饰器工具模块

本模块提供了一组用于路由函数的装饰器，用于实现权限控制、访问限制、日志记录和缓存控制等功能。
主要功能包括：
1. 角色权限控制：限制特定角色的用户访问
2. 访问频率限制：防止API滥用和DoS攻击
3. 访问日志记录：记录请求信息和执行时间
4. 缓存控制：设置HTTP缓存头

这些装饰器可以单独使用，也可以组合使用，为应用提供多层次的安全保护和性能优化。
"""

from functools import wraps
from flask import abort, flash, redirect, url_for, current_app, request
from flask_login import current_user
from typing import Callable, Union, Optional
import time
from app.utils.response import api_error
from app.utils.security_config import rate_limit as security_rate_limit

# 导入Flask-Limiter提供的速率限制装饰器
# 注意：应用中使用Flask-Limiter进行速率限制，而非自定义实现
# 请参考app.utils.security_config中的rate_limit装饰器

def role_required(role: Union[str, list]):
    """角色要求装饰器

    限制只有特定角色的用户才能访问被装饰的视图函数。
    如果用户未登录，会重定向到登录页面。
    如果用户已登录但角色不符，会返回403错误。

    角色检查基于User模型中的is_role属性，如is_admin、is_teacher等。

    Args:
        role: 所需角色，可以是单个角色名(str)或角色列表(list)

    Returns:
        装饰器函数

    示例:
        @app.route('/admin_only')
        @role_required('admin')
        def admin_page():
            return "只有管理员可以看到这个页面"

        @app.route('/staff_only')
        @role_required(['admin', 'teacher'])
        def staff_page():
            return "管理员和教师可以看到这个页面"
    """
    def decorator(f: Callable):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('请先登录', 'warning')
                return redirect(url_for('auth.login', next=request.url))

            roles = [role] if isinstance(role, str) else role
            if not any(getattr(current_user, f'is_{r}', False) for r in roles):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f: Callable):
    """管理员权限装饰器"""
    return role_required('admin')(f)

def teacher_required(f: Callable):
    """教师权限装饰器"""
    return role_required(['teacher', 'admin'])(f)

def ratelimit(calls: int = 100, period: int = 60, by: Optional[str] = None):
    """访问频率限制装饰器 (已弃用)

    此装饰器已弃用，请使用 Flask-Limiter 提供的速率限制功能。

    推荐使用 app.utils.security_config 中的 rate_limit 装饰器，或直接使用
    app 中初始化的 limiter 实例的 limit 方法。

    示例:
        # 使用 security_config 中的 rate_limit 装饰器
        from app.utils.security_config import rate_limit

        @app.route('/api/sensitive')
        @rate_limit(["5 per minute", "100 per day"])
        def sensitive_api():
            return "此API有速率限制"

        # 或直接使用 limiter 实例
        from app import limiter

        @app.route('/api/sensitive')
        @limiter.limit("5 per minute")
        def sensitive_api():
            return "此API有速率限制"
    """
    # 返回 security_config 中的 rate_limit 装饰器
    # 将调用转发到标准实现
    if by == 'ip':
        # 基于IP地址限制
        limit_string = f"{calls} per {period} second"
        return security_rate_limit([limit_string])
    elif by == 'user':
        # 基于用户ID限制 (注意：Flask-Limiter 默认基于IP)
        limit_string = f"{calls} per {period} second"
        return security_rate_limit([limit_string])
    else:
        # 默认限制
        limit_string = f"{calls} per {period} second"
        return security_rate_limit([limit_string])

def log_access(f: Callable):
    """访问日志装饰器

    记录视图函数的访问信息，包括请求方法、URL、用户ID、IP地址和执行时间。
    同时捕获并记录执行过程中的异常，但不处理异常，而是继续抛出。

    记录的信息包括:
    - 请求开始: 方法、URL、用户ID/匿名、IP地址
    - 请求完成: 方法、URL、执行时间
    - 请求错误: 函数名、异常信息

    Returns:
        装饰器函数

    示例:
        @app.route('/important')
        @log_access
        def important_function():
            return "此函数的访问将被详细记录"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()

        # 记录请求开始
        current_app.logger.info(
            f"Access: {request.method} {request.url} "
            f"by {'User:' + str(current_user.id) if current_user.is_authenticated else 'Anonymous'} "
            f"from {request.remote_addr}"
        )

        try:
            result = f(*args, **kwargs)
            # 记录请求完成
            duration = time.time() - start_time
            current_app.logger.info(
                f"Completed: {request.method} {request.url} "
                f"in {duration:.2f}s"
            )
            return result
        except Exception as e:
            # 记录请求错误
            current_app.logger.error(
                f"Error in {f.__name__}: {str(e)}"
            )
            raise

    return decorated_function

def cache_control(*directives: str):
    """缓存控制装饰器

    为视图函数的响应添加Cache-Control头，控制浏览器和中间缓存的行为。
    可以指定多个缓存控制指令，它们将被组合成一个Cache-Control头。

    常用的缓存控制指令:
    - no-cache: 每次使用缓存前必须向服务器验证
    - no-store: 不缓存响应
    - private: 只允许浏览器缓存，不允许中间缓存
    - public: 允许所有缓存
    - max-age=秒数: 缓存的最大有效时间
    - must-revalidate: 过期后必须重新验证

    Args:
        *directives: 缓存控制指令，如'no-cache', 'private', 'max-age=300'

    Returns:
        装饰器函数

    示例:
        @app.route('/static-content')
        @cache_control('public', 'max-age=3600')
        def static_content():
            return "此内容将被缓存1小时"

        @app.route('/sensitive-data')
        @cache_control('private', 'no-cache', 'max-age=0')
        def sensitive_data():
            return "此内容不会被缓存"
    """
    def decorator(f: Callable):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            response.headers['Cache-Control'] = ', '.join(directives)
            return response
        return decorated_function
    return decorator

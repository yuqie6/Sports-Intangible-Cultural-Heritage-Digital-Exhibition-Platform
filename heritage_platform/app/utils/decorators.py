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
from collections import defaultdict
from threading import Lock
from app.utils.response import api_error

# 简单的内存缓存，用于存储访问记录
# 使用defaultdict避免键不存在的问题，使用列表存储时间戳
_rate_limit_cache = defaultdict(list)
# 使用锁确保线程安全，防止并发访问导致的竞态条件
_cache_lock = Lock()

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
    """访问频率限制装饰器

    限制API的访问频率，防止滥用和DoS攻击。
    使用滑动窗口算法实现，在指定时间窗口内限制请求次数。
    可以基于IP地址或用户ID进行限制。
    超过限制时返回429错误(Too Many Requests)。

    实现原理:
    - 使用内存缓存存储每个限制键的访问时间戳列表
    - 每次请求时清理过期的时间戳并检查是否超过限制
    - 使用锁确保线程安全

    Args:
        calls: 允许的最大请求次数，默认为100次
        period: 时间窗口（秒），默认为60秒
        by: 限制依据，可选值为'ip'(基于IP地址)或'user'(基于用户ID)，默认为None(基于函数名)

    Returns:
        装饰器函数

    示例:
        @app.route('/api/sensitive')
        @ratelimit(calls=5, period=60, by='ip')
        def sensitive_api():
            return "此API每分钟最多调用5次"
    """
    def decorator(f: Callable):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 获取限制键
            if by == 'ip':
                key = f"ratelimit:{request.remote_addr}:{f.__name__}"
            elif by == 'user' and current_user.is_authenticated:
                key = f"ratelimit:{current_user.id}:{f.__name__}"
            else:
                key = f"ratelimit:default:{f.__name__}"

            # 获取当前时间
            now = time.time()

            with _cache_lock:
                # 清理过期的访问记录
                _rate_limit_cache[key] = [ts for ts in _rate_limit_cache[key] if now - ts < period]

                # 检查是否超过限制
                if len(_rate_limit_cache[key]) >= calls:
                    current_app.logger.warning(f"访问频率限制: {key}")
                    return api_error(
                        message="请求过于频繁，请稍后再试",
                        status_code=429,
                        error_code="RATE_LIMIT_EXCEEDED"
                    )

                # 记录本次访问
                _rate_limit_cache[key].append(now)

            return f(*args, **kwargs)
        return decorated_function
    return decorator

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

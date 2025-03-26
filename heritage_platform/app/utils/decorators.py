from functools import wraps
from flask import abort, flash, redirect, url_for, current_app, request
from flask_login import current_user
from typing import Callable, Union, Optional
import time
from collections import defaultdict
from threading import Lock
from app.utils.response import api_error  # 添加这行导入

# 简单的内存缓存，用于存储访问记录
_rate_limit_cache = defaultdict(list)
_cache_lock = Lock()

def role_required(role: Union[str, list]):
    """角色要求装饰器
    
    Args:
        role: 所需角色，可以是单个角色名或角色列表
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
    
    Args:
        calls: 允许的最大请求次数
        period: 时间窗口（秒）
        by: 限制依据（如'ip'或'user'）
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
    """访问日志装饰器"""
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
    
    Args:
        *directives: 缓存控制指令，如'no-cache', 'private', 'max-age=300'
    """
    def decorator(f: Callable):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            response.headers['Cache-Control'] = ', '.join(directives)
            return response
        return decorated_function
    return decorator

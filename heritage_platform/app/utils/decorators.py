from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)  # 没有权限
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    """教师权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or \
           (not current_user.is_teacher and not current_user.is_admin):
            abort(403)  # 没有权限
        return f(*args, **kwargs)
    return decorated_function

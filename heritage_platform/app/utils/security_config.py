from functools import wraps
from flask import request, abort, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
import re
import bleach
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

def setup_security(app):
    # 配置Limiter使用内存存储
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri="memory://",
        headers_enabled=True,
        header_name_mapping={"X-RateLimit-Limit": "X-RateLimit-Limit",
                        "X-RateLimit-Remaining": "X-RateLimit-Remaining",
                        "X-RateLimit-Reset": "X-RateLimit-Reset"},
        default_limits=["200 per day", "50 per hour"]
    )

    # 配置CSP策略
    csp = {
        'default-src': [
            "'self'",
            "'unsafe-inline'",  # 允许内联样式，根据需要调整
            "'unsafe-eval'",   # 允许内联脚本，根据需要调整
            "data:",           # 允许data: URLs
            "blob:",          # 允许blob: URLs
            "https:",         # 允许https资源
        ],
        'img-src': [
            "'self'",
            "data:",
            "https:",
        ],
        'script-src': [
            "'self'",
            "'unsafe-inline'",
            "'unsafe-eval'",
            "https:",
        ],
        'style-src': [
            "'self'",
            "'unsafe-inline'",
            "https:",
        ],
    }

    # 启用Talisman进行安全头部配置
    Talisman(
        app,
        content_security_policy=csp,
        force_https=False,  # 在生产环境中设置为True
        session_cookie_secure=False,  # 在生产环境中设置为True
        session_cookie_http_only=True,
        feature_policy={
            'geolocation': "'none'",
            'microphone': "'none'",
            'camera': "'none'",
        }
    )

    # 配置请求速率限制
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    app.config['LIMITER'] = limiter

    # 配置密码策略
    app.config['PASSWORD_POLICY'] = {
        'MIN_LENGTH': 8,
        'REQUIRE_UPPER': True,
        'REQUIRE_LOWER': True,
        'REQUIRE_NUMBERS': True,
        'REQUIRE_SPECIAL': True,
        'MAX_AGE_DAYS': 90,
    }

    # 配置会话安全
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
    app.config['SESSION_COOKIE_SECURE'] = False  # 在生产环境中设置为True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

def validate_password(password):
    """验证密码是否符合安全策略"""
    policy = current_app.config['PASSWORD_POLICY']
    
    if len(password) < policy['MIN_LENGTH']:
        return False, f'密码长度必须至少为{policy["MIN_LENGTH"]}个字符'
    
    if policy['REQUIRE_UPPER'] and not re.search(r'[A-Z]', password):
        return False, '密码必须包含至少一个大写字母'
    
    if policy['REQUIRE_LOWER'] and not re.search(r'[a-z]', password):
        return False, '密码必须包含至少一个小写字母'
    
    if policy['REQUIRE_NUMBERS'] and not re.search(r'\d', password):
        return False, '密码必须包含至少一个数字'
    
    if policy['REQUIRE_SPECIAL'] and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, '密码必须包含至少一个特殊字符'
    
    return True, '密码符合要求'

def sanitize_html(content):
    """清理HTML内容，防止XSS攻击"""
    allowed_tags = [
        'a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
        'em', 'i', 'li', 'ol', 'p', 'strong', 'ul',
        'br', 'span', 'div', 'img', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
    ]
    allowed_attrs = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title'],
        '*': ['class', 'style']
    }
    allowed_styles = [
        'color', 'background-color', 'font-size', 'font-weight',
        'text-align', 'margin', 'padding', 'border'
    ]
    
    return bleach.clean(
        content,
        tags=allowed_tags,
        attributes=allowed_attrs,
        styles=allowed_styles,
        strip=True
    )

def rate_limit(limits=None):
    """自定义速率限制装饰器"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            limiter = current_app.config.get('LIMITER')
            if limiter:
                for limit in limits or []:
                    limiter.check(limit)
            return f(*args, **kwargs)
        return wrapped
    return decorator

def check_content_type(allowed_types):
    """检查请求内容类型的装饰器"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if request.content_type not in allowed_types:
                abort(415)  # Unsupported Media Type
            return f(*args, **kwargs)
        return wrapped
    return decorator

def check_file_type(allowed_extensions):
    """检查上传文件类型的装饰器"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            file = request.files.get('file')
            if file and not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
                abort(400, description='不支持的文件类型')
            return f(*args, **kwargs)
        return wrapped
    return decorator
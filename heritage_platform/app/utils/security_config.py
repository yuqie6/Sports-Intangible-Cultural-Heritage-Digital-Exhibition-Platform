from functools import wraps
from flask import request, abort, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
import re
import bleach
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import warnings

def setup_security(app):
    # 抑制内存存储的警告
    warnings.filterwarnings("ignore", message="Using the in-memory storage for tracking rate limits")
    
    # 配置Limiter使用Redis存储（如果可用），否则回退到内存存储
    redis_uri = app.config.get('REDIS_URL', None)
    storage_uri = redis_uri if redis_uri else "memory://"
    
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=storage_uri,
        headers_enabled=True,
        header_name_mapping={"X-RateLimit-Limit": "X-RateLimit-Limit",
                        "X-RateLimit-Remaining": "X-RateLimit-Remaining",
                        "X-RateLimit-Reset": "X-RateLimit-Reset"},
        default_limits=["20000000 per day", "50000 per hour"],
    )
    
    # 为通知相关API设置更宽松的限制
    limiter.limit("3000000000000 per minute")(app.route("/api/notifications/unread-count"))
    limiter.limit("3000000000000 per minute")(app.route("/api/messages/unread-count"))
    
    # 存储limiter实例以供其他模块使用
    app.config['LIMITER'] = limiter

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
        force_https=False,  # 确保不强制HTTPS，由CloudFlare处理
        session_cookie_secure=False,  # 确保不强制HTTPS Cookie
        session_cookie_http_only=True,
        force_file_save=False,  # 禁用强制文件下载
        strict_transport_security=False,  # 禁用HSTS，由CloudFlare处理
        frame_options="SAMEORIGIN"  # 允许同域名框架
    )

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
    app.config['SESSION_COOKIE_SECURE'] = False  # 禁用安全Cookie
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # 添加CloudFlare特定配置
    app.config['PREFERRED_URL_SCHEME'] = 'http'  # 确保URL生成使用http
    
    # 禁用Flask-Login强制HTTPS
    from flask_login import LoginManager
    app.config['LOGIN_DISABLED'] = False
    app.config['USE_SESSION_FOR_NEXT'] = True

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
"""
安全配置模块

本模块提供了应用的安全配置和安全相关的工具函数，包括：
1. 请求速率限制：防止API滥用和DoS攻击
2. 内容安全策略：控制资源加载，防止XSS攻击
3. 密码策略：确保用户密码强度
4. 会话安全：保护用户会话
5. 内容清理：防止XSS攻击
6. 文件类型验证：防止恶意文件上传

安全特性：
- 速率限制：使用Flask-Limiter限制API请求频率
- 安全头部：使用Flask-Talisman添加安全相关的HTTP头部
- HTML清理：使用bleach库清理用户输入的HTML内容
- 密码验证：强制执行密码复杂度要求
- 内容类型检查：验证请求和上传文件的类型
"""

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
    """设置应用的安全配置

    为Flask应用配置全面的安全措施，包括请求速率限制、内容安全策略、
    密码策略、会话安全和其他安全相关的配置。

    配置内容包括：
    1. 请求速率限制：使用Flask-Limiter限制API请求频率
    2. 内容安全策略(CSP)：控制页面可以加载的资源
    3. 安全HTTP头部：使用Flask-Talisman添加安全相关的HTTP头部
    4. 密码策略：设置密码复杂度要求
    5. 会话安全：配置会话Cookie的安全属性

    特别说明：
    - 部分安全设置（如HTTPS强制）被禁用，因为它们由CloudFlare处理
    - 为特定API（如通知和消息计数）设置了更宽松的速率限制
    - 内容安全策略允许内联脚本和样式，以支持现有的前端代码

    Args:
        app: Flask应用实例
    """
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
    """验证密码是否符合安全策略

    根据应用配置的密码策略，验证密码是否满足复杂度要求。
    验证内容包括密码长度、大小写字母、数字和特殊字符的要求。

    验证规则从应用配置的PASSWORD_POLICY字典中获取，包括：
    - MIN_LENGTH: 最小长度要求
    - REQUIRE_UPPER: 是否要求包含大写字母
    - REQUIRE_LOWER: 是否要求包含小写字母
    - REQUIRE_NUMBERS: 是否要求包含数字
    - REQUIRE_SPECIAL: 是否要求包含特殊字符

    Args:
        password (str): 待验证的密码

    Returns:
        tuple: (是否通过验证, 验证消息)
            - 第一个元素为布尔值，表示密码是否符合要求
            - 第二个元素为字符串，包含验证结果的详细信息

    示例:
        >>> valid, message = validate_password("Abc123!@#")
        >>> if not valid:
        >>>     flash(message, 'danger')
    """
    policy = current_app.config['PASSWORD_POLICY']

    # 验证密码长度
    if len(password) < policy['MIN_LENGTH']:
        return False, f'密码长度必须至少为{policy["MIN_LENGTH"]}个字符'

    # 验证是否包含大写字母
    if policy['REQUIRE_UPPER'] and not re.search(r'[A-Z]', password):
        return False, '密码必须包含至少一个大写字母'

    # 验证是否包含小写字母
    if policy['REQUIRE_LOWER'] and not re.search(r'[a-z]', password):
        return False, '密码必须包含至少一个小写字母'

    # 验证是否包含数字
    if policy['REQUIRE_NUMBERS'] and not re.search(r'\d', password):
        return False, '密码必须包含至少一个数字'

    # 验证是否包含特殊字符
    if policy['REQUIRE_SPECIAL'] and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, '密码必须包含至少一个特殊字符'

    return True, '密码符合要求'

def sanitize_html(content):
    """清理HTML内容，防止XSS攻击

    使用bleach库清理用户输入的HTML内容，移除不安全的标签和属性，
    防止跨站脚本攻击(XSS)。只允许安全的HTML标签、属性和样式。

    安全策略:
    - 白名单机制：只允许明确列出的标签、属性和样式
    - 移除所有JavaScript：不允许任何脚本标签和事件处理属性
    - 清理样式：只允许安全的CSS属性，防止CSS注入攻击
    - 清理链接：确保链接不包含javascript:协议

    Args:
        content (str): 待清理的HTML内容

    Returns:
        str: 清理后的安全HTML内容

    示例:
        >>> safe_html = sanitize_html(user_submitted_content)
        >>> article.content = safe_html
    """
    # 允许的HTML标签白名单
    allowed_tags = [
        'a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
        'em', 'i', 'li', 'ol', 'p', 'strong', 'ul',
        'br', 'span', 'div', 'img', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
    ]

    # 允许的HTML属性白名单
    allowed_attrs = {
        'a': ['href', 'title'],  # 链接标签允许href和title属性
        'img': ['src', 'alt', 'title'],  # 图片标签允许src、alt和title属性
        '*': ['class', 'style']  # 所有标签允许class和style属性
    }

    # 允许的CSS样式属性白名单
    allowed_styles = [
        'color', 'background-color', 'font-size', 'font-weight',
        'text-align', 'margin', 'padding', 'border'
    ]

    # 使用bleach库清理HTML
    return bleach.clean(
        content,
        tags=allowed_tags,
        attributes=allowed_attrs,
        styles=allowed_styles,
        strip=True  # 移除不允许的标签，而不是转义它们
    )

def rate_limit(limits=None):
    """自定义速率限制装饰器

    为视图函数添加速率限制，防止API滥用和DoS攻击。
    使用应用配置中的Limiter实例检查请求是否超过限制。
    可以指定多个限制规则，任何一个规则超过限制都会导致请求被拒绝。

    Args:
        limits (list, optional): 限制规则列表，如["5 per minute", "100 per day"]

    Returns:
        decorator: 装饰器函数

    Raises:
        429 Too Many Requests: 当请求超过限制时

    示例:
        >>> @app.route('/api/sensitive')
        >>> @rate_limit(["5 per minute", "100 per day"])
        >>> def sensitive_api():
        >>>     return "此API有速率限制"
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            limiter = current_app.config.get('LIMITER')
            if limiter:
                for limit in limits or []:
                    limiter.check(limit)  # 检查是否超过限制，超过则抛出429异常
            return f(*args, **kwargs)
        return wrapped
    return decorator

def check_content_type(allowed_types):
    """检查请求内容类型的装饰器

    验证请求的Content-Type是否在允许的类型列表中，
    防止不支持的内容类型和潜在的安全风险。

    通常用于API端点，确保客户端发送的数据格式符合预期，
    例如只接受JSON或表单数据。

    Args:
        allowed_types (list): 允许的内容类型列表，如['application/json', 'multipart/form-data']

    Returns:
        decorator: 装饰器函数

    Raises:
        415 Unsupported Media Type: 当请求的内容类型不在允许列表中时

    示例:
        >>> @app.route('/api/data', methods=['POST'])
        >>> @check_content_type(['application/json'])
        >>> def json_only_api():
        >>>     return "此API只接受JSON数据"
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if request.content_type not in allowed_types:
                abort(415)  # Unsupported Media Type (不支持的媒体类型)
            return f(*args, **kwargs)
        return wrapped
    return decorator

def check_file_type(allowed_extensions):
    """检查上传文件类型的装饰器

    验证上传文件的扩展名是否在允许的扩展名列表中，
    防止上传不支持的文件类型和潜在的恶意文件。

    通常用于文件上传端点，确保只接受安全的文件类型，
    例如只接受图片或文档文件。

    注意：此装饰器仅检查文件扩展名，不检查文件内容。
    对于更严格的安全检查，应该结合文件内容验证。

    Args:
        allowed_extensions (list): 允许的文件扩展名列表，如['.jpg', '.png', '.pdf']

    Returns:
        decorator: 装饰器函数

    Raises:
        400 Bad Request: 当上传的文件类型不在允许列表中时

    示例:
        >>> @app.route('/upload', methods=['POST'])
        >>> @check_file_type(['.jpg', '.png', '.gif'])
        >>> def upload_image():
        >>>     return "此API只接受图片文件"
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            file = request.files.get('file')
            if file and not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
                abort(400, description='不支持的文件类型')
            return f(*args, **kwargs)
        return wrapped
    return decorator
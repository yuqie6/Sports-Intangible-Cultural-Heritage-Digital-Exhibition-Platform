from flask import Blueprint
from flask_wtf.csrf import CSRFProtect

api_bp = Blueprint('api', __name__)
csrf = CSRFProtect()
csrf.exempt(api_bp)

# 导入API视图函数
from . import heritage, content, user, forum, notification

# 不再需要手动注册路由，因为已使用装饰器方式

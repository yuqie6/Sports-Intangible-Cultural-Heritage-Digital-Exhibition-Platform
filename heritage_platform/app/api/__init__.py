"""
API蓝图初始化模块

本模块创建并配置API蓝图，用于提供RESTful API接口。
主要功能：
1. 创建API蓝图
2. 配置CSRF豁免，允许外部应用和前端框架直接调用API
3. 导入所有API视图函数模块

API接口分类：
- heritage: 非遗项目相关API
- content: 内容管理相关API
- user: 用户管理相关API
- forum: 论坛相关API
- notification: 通知相关API
"""

from flask import Blueprint
from flask_wtf.csrf import CSRFProtect

# 创建API蓝图
api_bp = Blueprint('api', __name__)

# 配置CSRF保护
csrf = CSRFProtect()
# 豁免API蓝图的CSRF保护，允许外部应用和前端框架直接调用API
csrf.exempt(api_bp)

# 导入API视图函数模块
# 使用装饰器方式注册路由，不需要手动注册
from . import heritage, content, user, forum, notification

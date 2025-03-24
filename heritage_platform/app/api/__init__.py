from flask import Blueprint

api_bp = Blueprint('api', __name__)

# 导入API视图函数
from . import heritage, content, user, forum

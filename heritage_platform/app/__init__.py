from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
import os
import markdown

# 初始化扩展
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()

login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录再访问此页面'
login_manager.login_message_category = 'info'

def create_app(config_name='default'):
    """创建Flask应用实例
    
    Args:
        config_name: 配置名称，对应config.py中的配置类
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    
    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)
    
    # 注册API蓝图（前后端分离的API接口）
    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 注册视图蓝图
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.heritage import heritage_bp
    from app.routes.content import content_bp
    from app.routes.forum import forum_bp
    from app.routes.user import user_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(heritage_bp, url_prefix='/heritage')
    app.register_blueprint(content_bp, url_prefix='/content')
    app.register_blueprint(forum_bp, url_prefix='/forum')
    app.register_blueprint(user_bp, url_prefix='/user')
    
    # 注册全局错误处理
    from app.routes import errors
    app.register_error_handler(404, errors.page_not_found)
    app.register_error_handler(500, errors.internal_server_error)
    app.register_error_handler(403, errors.forbidden)
    
    # 注册上下文处理器，提供通用数据
    from app.utils.context_processors import common_data
    app.context_processor(common_data)
    
    # 添加模板过滤器
    @app.template_filter('markdown')
    def render_markdown(content):
        """将Markdown格式转换为HTML"""
        if content:
            return markdown.markdown(content, extensions=[
                'markdown.extensions.fenced_code',  # 支持代码块
                'markdown.extensions.tables',       # 支持表格
                'markdown.extensions.nl2br',        # 换行转为<br>
                'markdown.extensions.extra'         # 额外功能集合
            ])
        return ''
    
    return app

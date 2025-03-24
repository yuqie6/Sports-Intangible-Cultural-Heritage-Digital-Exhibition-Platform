from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
import os

# 初始化扩展
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()

login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录再访问此页面'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    
    # 确保上传目录存在
    with app.app_context():
        os.makedirs(os.path.join(app.static_folder, 'uploads/images'), exist_ok=True)
        os.makedirs(os.path.join(app.static_folder, 'uploads/videos'), exist_ok=True)
        app.logger.info("上传目录已创建")
        
        # 检查表是否存在，如存在再确保列存在
        try:
            from app.utils.db_helpers import ensure_column_exists
            from sqlalchemy import inspect
            
            # 检查表是否存在
            inspector = inspect(db.engine)
            if 'contents' in inspector.get_table_names():
                ensure_column_exists('contents', 'rich_content', 'TEXT')
        except Exception as e:
            app.logger.warning(f"检查数据库结构时出错: {str(e)}")
    
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
    
    # 创建文件上传目录
    Config.init_app(app)
    
    # 注册全局错误处理
    from app.routes import errors
    app.register_error_handler(404, errors.page_not_found)
    app.register_error_handler(500, errors.internal_server_error)
    app.register_error_handler(403, errors.forbidden)
    
    # 注册上下文处理器，提供通用数据
    from app.utils.context_processors import common_data
    app.context_processor(common_data)
    
    return app

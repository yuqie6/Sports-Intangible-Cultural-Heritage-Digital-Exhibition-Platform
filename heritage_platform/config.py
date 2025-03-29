import os
import logging
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # 应用配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-testing'
    
    # 数据库配置
    DB_USER = os.environ.get('DB_USER') or 'root'
    DB_PASSWORD = os.environ.get('DB_PASSWORD')  or 'qB6455221153'# 必须通过环境变量设置
    DB_HOST = os.environ.get('DB_HOST') or 'localhost'
    DB_NAME = os.environ.get('DB_NAME') or 'heritage_platform'
    
    # 构建数据库URI
    SQLALCHEMY_DATABASE_URI = (
        f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
        if DB_PASSWORD else
        'mysql+pymysql://root@localhost/heritage_platform'  # 默认本地开发配置
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 数据库连接池配置
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'max_overflow': 20,
        'pool_timeout': 30,
        'pool_recycle': 1800,
    }
    
    # 上传文件配置
    UPLOAD_FOLDER = os.path.join(basedir, 'app/static/uploads')
    
    # Redis配置
    REDIS_HOST = os.environ.get('REDIS_HOST') or 'localhost'
    REDIS_PORT = int(os.environ.get('REDIS_PORT') or 6379)
    REDIS_DB = int(os.environ.get('REDIS_DB') or 0)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB限制
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or logging.INFO
    
    @staticmethod
    def init_app(app):
        # 配置日志
        handler = logging.StreamHandler()
        handler.setLevel(app.config['LOG_LEVEL'])
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
        app.logger.setLevel(app.config['LOG_LEVEL'])
        
        # 确保上传目录存在
        upload_path = os.path.join(app.root_path, 'static/uploads')
        os.makedirs(os.path.join(upload_path, 'images'), exist_ok=True)
        os.makedirs(os.path.join(upload_path, 'videos'), exist_ok=True)
        app.logger.info(f"上传目录已创建: {upload_path}")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = logging.ERROR
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # 生产环境下的额外配置
        import logging
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            os.path.join(basedir, 'logs/heritage.log'),
            maxBytes=10*1024*1024, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

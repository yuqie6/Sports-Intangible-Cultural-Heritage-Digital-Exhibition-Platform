import os
import logging
basedir = os.path.abspath(os.path.dirname(__file__))  # 获取当前文件所在目录的绝对路径

class Config:
    """应用的基础配置类
    
    包含应用的基本配置参数，如密钥、数据库连接、上传目录等。
    所有环境特定的配置类都继承自此类。
    """
    # 应用安全配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-testing'  # 用于会话加密的密钥，生产环境应通过环境变量设置
    
    # 数据库连接配置
    DB_USER = os.environ.get('DB_USER') or 'root'  # 数据库用户名，默认为root
    DB_PASSWORD = os.environ.get('DB_PASSWORD')  or 'qB645522153'  # 数据库密码，理想情况下应通过环境变量设置
    DB_HOST = os.environ.get('DB_HOST') or 'localhost'  # 数据库主机地址，默认为localhost
    DB_NAME = os.environ.get('DB_NAME') or 'heritage_platform'  # 数据库名称，默认为heritage_platform
    
    # 构建完整的数据库URI
    SQLALCHEMY_DATABASE_URI = (
        f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'  # 使用pymysql驱动连接MySQL
        if DB_PASSWORD else
        'mysql+pymysql://root@localhost/heritage_platform'  # 如果未设置密码，使用默认连接字符串
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 关闭SQLAlchemy的修改跟踪，提高性能
    
    # 数据库连接池配置，优化数据库连接性能和可靠性
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,  # 连接池中保持的连接数量
        'max_overflow': 20,  # 允许的最大连接溢出数
        'pool_timeout': 30,  # 等待获取连接的超时时间（秒）
        'pool_recycle': 1800,  # 连接自动回收时间（秒），防止连接过期
    }
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(basedir, 'app/static/uploads')  # 上传文件存储目录
    
    # Redis服务配置，用于缓存、会话存储和任务队列
    REDIS_HOST = os.environ.get('REDIS_HOST') or 'localhost'  # Redis服务器地址
    REDIS_PORT = int(os.environ.get('REDIS_PORT') or 6379)  # Redis服务端口
    REDIS_DB = int(os.environ.get('REDIS_DB') or 0)  # Redis数据库索引
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 上传文件大小限制（16MB）
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or logging.INFO  # 日志记录级别，默认为INFO
    
    @staticmethod
    def init_app(app):
        """初始化应用配置
        
        配置应用的日志系统和上传目录。
        
        Args:
            app: Flask应用实例
        """
        # 配置控制台日志处理器
        handler = logging.StreamHandler()  # 创建一个流处理器，输出到控制台
        handler.setLevel(app.config['LOG_LEVEL'])  # 设置日志级别
        # 定义日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')  # 设置日志格式，包含时间、名称、级别和消息
        handler.setFormatter(formatter)  # 应用日志格式
        app.logger.addHandler(handler)  # 将处理器添加到应用的日志记录器
        app.logger.setLevel(app.config['LOG_LEVEL'])  # 设置应用日志记录器的级别
        
        # 确保上传目录存在，创建不同类型文件的上传子目录
        upload_path = os.path.join(app.root_path, 'static/uploads')  # 获取上传目录的绝对路径
        os.makedirs(os.path.join(upload_path, 'images'), exist_ok=True)  # 创建图片上传目录
        os.makedirs(os.path.join(upload_path, 'videos'), exist_ok=True)  # 创建视频上传目录
        app.logger.info(f"上传目录已创建: {upload_path}")  # 记录目录创建信息


class DevelopmentConfig(Config):
    """开发环境配置
    
    适用于本地开发和测试的配置，启用调试模式。
    """
    DEBUG = True  # 启用Flask的调试模式，显示详细错误信息和自动重新加载


class ProductionConfig(Config):
    """生产环境配置
    
    适用于线上部署的配置，关闭调试，提高安全性和性能。
    """
    DEBUG = False  # 关闭调试模式，提高性能和安全性
    LOG_LEVEL = logging.ERROR  # 提高日志级别为ERROR，减少日志量
    
    @classmethod
    def init_app(cls, app):
        """初始化生产环境应用配置
        
        在基础配置基础上，添加生产环境特定的配置，如文件日志。
        
        Args:
            app: Flask应用实例
        """
        Config.init_app(app)  # 调用父类的初始化方法
        
        # 配置文件日志系统，适合生产环境长期运行
        import logging
        from logging.handlers import RotatingFileHandler
        # 使用绝对路径指定日志文件位置
        log_file = '/var/www/heritage_platform/Sports-Intangible-Cultural-Heritage-Digital-Exhibition-Platform/heritage_platform/logs/heritage.log'
        # 创建旋转文件处理器，限制日志文件大小，并自动创建备份
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 单个日志文件最大10MB
            backupCount=10)  # 保留10个备份文件
        # 配置详细的日志格式，包含文件路径和行号
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)  # 设置文件日志的级别为INFO
        app.logger.addHandler(file_handler)  # 将文件处理器添加到应用的日志记录器


# 配置字典，用于根据环境名称选择配置类
config = {
    'development': DevelopmentConfig,  # 开发环境配置
    'production': ProductionConfig,    # 生产环境配置
    'default': DevelopmentConfig       # 默认使用开发环境配置
}

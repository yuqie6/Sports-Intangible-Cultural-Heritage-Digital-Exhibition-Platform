import os
import logging
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # 应用配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-testing'
    
    # 数据库配置 - 根据实际情况修改用户名和密码
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:qB645522153@localhost/heritage_platform'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 上传文件配置
    UPLOAD_FOLDER = os.path.join(basedir, 'app/static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB限制
    
    # 日志配置
    LOG_LEVEL = logging.INFO
    
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

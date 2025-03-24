import os
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
    
    @staticmethod
    def init_app(app):
        # 确保上传目录存在
        os.makedirs(os.path.join(app.root_path, 'static/uploads/images'), exist_ok=True)
        os.makedirs(os.path.join(app.root_path, 'static/uploads/videos'), exist_ok=True)

from app import create_app, db
import pymysql
from sqlalchemy.exc import OperationalError
import traceback

# 创建应用上下文
app = create_app()
app_context = app.app_context()
app_context.push()

def create_database_if_not_exists():
    """尝试创建数据库（如果不存在）"""
    try:
        # 从应用配置中提取数据库连接信息
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        db_parts = db_uri.split('/')
        db_name = db_parts[-1]
        
        # 尝试提取用户名和密码
        auth_parts = db_parts[2].split('@')[0].split(':')
        user = auth_parts[0]
        password = auth_parts[1] if len(auth_parts) > 1 else ''
        
        # 提取主机名
        host_parts = db_parts[2].split('@')
        host = host_parts[1] if len(host_parts) > 1 else host_parts[0]
        
        print(f"连接到 MySQL 服务器 {host} 使用用户 {user}")
        
        # 连接到MySQL服务器而非具体数据库
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            charset='utf8mb4'
        )
        
        try:
            with connection.cursor() as cursor:
                # 创建数据库（如果不存在）
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print(f"数据库 {db_name} 已创建或已存在")
        finally:
            connection.close()
            
    except Exception as e:
        print(f"创建数据库时出错: {e}")
        print(traceback.format_exc())

def init_db():
    """初始化数据库"""
    try:
        # 尝试创建数据库（如果不存在）
        create_database_if_not_exists()
        
        # 从模型导入，确保所有表都会被创建
        from app.models import User, HeritageItem, Content, Comment, Like, Favorite
        from app.models import ForumTopic, ForumPost
        
        # 创建所有表
        print("正在创建数据库表...")
        db.create_all()
        print("数据库表创建完成!")
        
        # 检查是否已有管理员账户
        admin = User.query.filter_by(role='admin').first()
        if admin is None:
            print('创建管理员账户...')
            admin = User(
                username='admin',
                email='admin@example.com',
                password='adminpassword',
                role='admin'
            )
            db.session.add(admin)
            
            # 创建一个教师账户
            teacher = User(
                username='teacher',
                email='teacher@example.com',
                password='teacherpassword',
                role='teacher'
            )
            db.session.add(teacher)
            
            # 创建一个学生账户
            student = User(
                username='student',
                email='student@example.com',
                password='studentpassword',
                role='student'
            )
            db.session.add(student)
            
            # 提交更改
            db.session.commit()
            print('初始用户创建成功!')
        else:
            print('管理员账户已存在.')
            
    except OperationalError as e:
        print(f"数据库操作错误: {e}")
        print("请确保MySQL服务已运行，且配置文件中的数据库连接信息正确。")
    except Exception as e:
        print(f"初始化数据库时发生错误: {e}")
        print(traceback.format_exc())

if __name__ == '__main__':
    init_db()
    app_context.pop()
    print("数据库初始化过程完成")

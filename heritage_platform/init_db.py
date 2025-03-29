import os
import sys
import click
import pymysql
import traceback
from urllib.parse import urlparse
from app import create_app, db
from sqlalchemy.exc import OperationalError

# 获取配置环境
config_name = os.environ.get('FLASK_CONFIG') or 'development'

# 创建应用上下文
app = create_app(config_name)
app_context = app.app_context()
app_context.push()

def parse_db_url(db_uri):
    """从数据库URI中解析连接信息"""
    try:
        if db_uri.startswith('mysql+pymysql://'):
            # 去掉前缀
            uri = db_uri[len('mysql+pymysql://'):]
            
            # 提取用户名密码和主机信息
            auth_host, db_name = uri.split('/', 1)
            if '@' in auth_host:
                auth, host = auth_host.split('@', 1)
            else:
                auth = ''
                host = auth_host
                
            if auth and ':' in auth:
                user, password = auth.split(':', 1)
            else:
                user = auth
                password = ''
                
            return {
                'user': user,
                'password': password,
                'host': host,
                'db_name': db_name
            }
        else:
            raise ValueError("不支持的数据库URL格式")
    except Exception as e:
        print(f"解析数据库URL时出错: {e}")
        sys.exit(1)

def create_database_if_not_exists():
    """尝试创建数据库（如果不存在）"""
    try:
        # 从应用配置中提取数据库连接信息
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        db_info = parse_db_url(db_uri)
        
        user = db_info['user']
        password = db_info['password']
        host = db_info['host']
        db_name = db_info['db_name']
        
        print(f"连接到 MySQL 服务器 {host} 使用用户 {user}")
        
        # 连接到MySQL服务器而非具体数据库
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            charset='utf8mb4',
            connect_timeout=5
        )
        
        try:
            with connection.cursor() as cursor:
                # 创建数据库（如果不存在）
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print(f"数据库 {db_name} 已创建或已存在")
        finally:
            connection.close()
            
    except pymysql.MySQLError as e:
        print(f"MySQL连接错误: {e}")
        print("请检查MySQL服务是否运行以及连接信息是否正确")
        sys.exit(1)
    except Exception as e:
        print(f"创建数据库时出错: {e}")
        print(traceback.format_exc())
        sys.exit(1)

def create_test_data():
    """创建测试数据"""
    from app.models import HeritageItem, Content, Comment, ForumTopic, ForumPost
    from app.models import Notification, Message, MessageGroup, UserGroup, MessageReadStatus
    from datetime import datetime
    
    try:
        # 创建示例非遗项目
        if HeritageItem.query.count() == 0:
            print("创建示例非遗项目...")
            heritage1 = HeritageItem(
                name='传统武术',
                category='体育类',
                description='中国传统武术是中华民族在长期的社会生产生活过程中创造和发展起来的一种身体运动形式。',
                cover_image='img/default-heritage.jpg',
                created_by=1  # admin
            )
            heritage2 = HeritageItem(
                name='舞龙舞狮',
                category='民俗类',
                description='舞龙舞狮是中国民间传统艺术表演形式，也是体育非遗项目的重要组成部分。',
                cover_image='img/default-heritage.jpg',
                created_by=2  # teacher
            )
            db.session.add_all([heritage1, heritage2])
            db.session.commit()
            print("示例非遗项目创建完成!")
        
        # 创建示例内容
        if Content.query.count() == 0:
            print("创建示例内容...")
            content1 = Content(
                heritage_id=1,
                title='太极拳基本招式',
                content='太极拳是一种中国传统拳法，以其缓慢、柔和的动作特点而闻名...',
                content_type='article',
                user_id=2,  # teacher
                views=15  # 设置初始浏览量
            )
            content2 = Content(
                heritage_id=2,
                title='舞龙技巧分享',
                content='舞龙是中国传统民俗活动，需要多人配合完成...',
                content_type='article',
                user_id=2,  # teacher
                views=8  # 设置初始浏览量
            )
            db.session.add_all([content1, content2])
            db.session.flush()
            
            # 创建示例评论
            comment1 = Comment(
                content_id=content1.id,
                user_id=3,  # student
                text='这篇教程非常实用，谢谢分享！'
            )
            comment2 = Comment(
                content_id=content1.id,
                user_id=1,  # admin
                text='老师讲解得很清楚，希望能有更多相关内容。'
            )
            # 添加回复评论
            reply_comment = Comment(
                content_id=content1.id,
                user_id=2,  # teacher
                text='谢谢支持，我会继续更新更多内容的！',
                parent_id=comment1.id,
                reply_to_user_id=3  # 回复学生
            )
            db.session.add_all([comment1, comment2, reply_comment])
            db.session.commit()
            print("示例内容和评论创建完成!")
            
        # 创建示例论坛主题
        if ForumTopic.query.count() == 0:
            print("创建示例论坛主题...")
            topic1 = ForumTopic(
                title='武术学习经验分享',
                category='讨论',
                user_id=1
            )
            db.session.add(topic1)
            db.session.flush()
            
            # 主贴
            post1 = ForumPost(
                topic_id=topic1.id,
                user_id=1,
                content='欢迎大家在这里分享武术学习的经验和心得!'
            )
            db.session.add(post1)
            
            # 回复帖
            reply1 = ForumPost(
                topic_id=topic1.id,
                user_id=2,
                content='太极拳是我最喜欢的武术形式！',
                parent_id=post1.id,
                reply_to_user_id=1
            )
            db.session.add(reply1)
            db.session.commit()
            print("示例论坛主题创建完成!")
        
        # 创建示例消息
        if Message.query.filter_by(message_type='private').count() == 0:
            print("创建示例私信...")
            message = Message(
                sender_id=1,  # admin
                receiver_id=2,  # teacher
                content='欢迎加入非遗平台教师团队！',
                is_read=False,
                created_at=datetime.utcnow(),
                message_type='private'
            )
            db.session.add(message)
            db.session.commit()
            print("示例私信创建完成!")
            
        # 创建消息群组
        if MessageGroup.query.count() == 0:
            print("创建示例消息群组...")
            group = MessageGroup(
                name='非遗教学讨论组',
                description='用于讨论非遗教学相关问题',
                group_type='discussion',
                creator_id=1,  # admin
                created_at=datetime.utcnow(),
                is_active=True
            )
            db.session.add(group)
            db.session.flush()
            
            # 添加群组成员
            user_group1 = UserGroup(
                user_id=1,  # admin
                group_id=group.id,
                joined_at=datetime.utcnow(),
                role='owner'
            )
            user_group2 = UserGroup(
                user_id=2,  # teacher
                group_id=group.id,
                joined_at=datetime.utcnow(),
                role='member'
            )
            db.session.add_all([user_group1, user_group2])
            
            # 添加群组消息
            group_message = Message(
                sender_id=1,  # admin
                group_id=group.id,
                content='大家好，这是我们的非遗教学讨论组，欢迎交流！',
                created_at=datetime.utcnow(),
                message_type='group'
            )
            db.session.add(group_message)
            db.session.flush()
            
            # 消息阅读状态
            read_status1 = MessageReadStatus(
                message_id=group_message.id,
                user_id=1,
                is_read=True,
                read_at=datetime.utcnow()
            )
            read_status2 = MessageReadStatus(
                message_id=group_message.id,
                user_id=2,
                is_read=False
            )
            db.session.add_all([read_status1, read_status2])
            db.session.commit()
            print("示例消息群组创建完成!")
            
        # 创建示例通知
        if Notification.query.count() == 0:
            print("创建示例通知...")
            notification = Notification(
                user_id=2,  # teacher
                sender_id=1,  # admin
                type='system',
                content='欢迎加入非遗传承平台！请完善您的个人资料。',
                link='/user/profile',
                is_read=False,
                created_at=datetime.utcnow()
            )
            db.session.add(notification)
            db.session.commit()
            print("示例通知创建完成!")
            
    except Exception as e:
        db.session.rollback()
        print(f"创建测试数据时出错: {e}")
        print(traceback.format_exc())

def init_db():
    """初始化数据库"""
    try:
        # 尝试创建数据库（如果不存在）
        create_database_if_not_exists()
        
        # 从模型导入，确保所有表都会被创建
        from app.models import User, HeritageItem, Content, Comment, Like, Favorite
        from app.models import ForumTopic, ForumPost
        from app.models import Notification, Message, MessageGroup, UserGroup, MessageReadStatus
        
        # 创建所有表
        print("正在创建数据库表...")
        db.create_all()
        print("数据库表创建完成!")
        
        # 检查是否已有管理员账户
        admin = User.query.filter_by(role='admin').first()
        if admin is None:
            print('创建初始用户账户...')
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
            
            # 创建测试数据
            create_test_data()
        else:
            print('管理员账户已存在，跳过初始数据创建。')
            
    except OperationalError as e:
        print(f"数据库操作错误: {e}")
        print("请确保MySQL服务已运行，且配置文件中的数据库连接信息正确。")
        sys.exit(1)
    except Exception as e:
        print(f"初始化数据库时发生错误: {e}")
        print(traceback.format_exc())
        sys.exit(1)

@click.command()
@click.option('--force', is_flag=True, help='强制重新创建所有表（会删除现有数据）')
def main(force):
    """数据库初始化命令"""
    if force:
        if click.confirm('这将删除所有现有数据。您确定要继续吗?', abort=True):
            print("正在删除所有表...")
            db.drop_all()
            print("所有表已删除")
    
    init_db()
    app_context.pop()
    print("数据库初始化过程完成")

if __name__ == '__main__':
    main()

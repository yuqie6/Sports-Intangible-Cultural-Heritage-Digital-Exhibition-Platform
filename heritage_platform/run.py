import os
import click
from dotenv import load_dotenv
from app import create_app, db, socketio
from flask_migrate import Migrate
from app.models import User

# 加载.env文件
load_dotenv()

# 通过环境变量设置配置类型，默认为开发环境
config_name = os.environ.get('FLASK_CONFIG') or 'production'
app = create_app(config_name)
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    """为Python Shell提供上下文"""
    return dict(app=app, db=db, User=User)

@app.cli.command()
@click.option('--length', default=16, help='Token length')
def generate_secret_key(length):
    """生成随机密钥"""
    import secrets
    secret_key = secrets.token_hex(length)
    click.echo(f'生成的密钥: {secret_key}')
    click.echo('请将此密钥添加到环境变量中:')
    click.echo('export SECRET_KEY="{0}"'.format(secret_key))

@app.cli.command()
def create_admin():
    """创建管理员用户"""
    username = click.prompt('输入管理员用户名')
    email = click.prompt('输入管理员邮箱')
    password = click.prompt('输入密码', hide_input=True, confirmation_prompt=True)
    
    try:
        user = User(username=username, email=email, role='admin')
        user.password = password
        db.session.add(user)
        db.session.commit()
        click.echo('管理员账户创建成功!')
    except Exception as e:
        db.session.rollback()
        click.echo(f'创建管理员失败: {str(e)}', err=True)

if __name__ == '__main__':
    # 使用socketio启动应用而非app.run
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), allow_unsafe_werkzeug=True)

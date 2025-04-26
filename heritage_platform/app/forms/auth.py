"""
认证表单模块

本模块定义了用户认证系统的表单类，包括：
1. 登录表单：用于用户登录
2. 注册表单：用于新用户注册

表单特性：
- 数据验证：使用WTForms验证器确保输入数据符合要求
- 自定义验证：实现用户名和邮箱唯一性检查
- 安全措施：密码字段使用PasswordField确保不会明文显示
- CSRF保护：通过Flask-WTF提供的CSRF保护机制防止跨站请求伪造
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from app.models.user import User

class LoginForm(FlaskForm):
    """登录表单

    用于用户登录的表单，包含用户名、密码和"记住我"选项。
    使用WTForms验证器确保输入数据符合要求。

    字段:
        username: 用户名字段，必填，长度1-50
        password: 密码字段，必填
        remember_me: "记住我"复选框，用于控制会话持久性
        submit: 提交按钮

    验证规则:
        - 用户名和密码为必填字段
        - 用户名长度限制在1-50个字符

    使用方式:
        在模板中使用{{ form.字段名.label }}和{{ form.字段名 }}渲染表单字段
        使用form.validate_on_submit()验证表单提交
    """
    username = StringField('用户名', validators=[
        DataRequired(message='用户名不能为空'),
        Length(1, 50, message='用户名长度必须在1-50个字符之间')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(message='密码不能为空')
    ])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')

class RegistrationForm(FlaskForm):
    """注册表单

    用于新用户注册的表单，包含用户名、邮箱、密码和确认密码字段。
    使用WTForms验证器确保输入数据符合要求，并实现自定义验证方法
    检查用户名和邮箱的唯一性。

    字段:
        username: 用户名字段，必填，长度1-50，格式限制
        email: 邮箱字段，必填，长度1-100，必须是有效的邮箱格式
        password: 密码字段，必填，长度8-128，必须与确认密码匹配
        password2: 确认密码字段，必填
        submit: 提交按钮

    验证规则:
        - 所有字段都是必填的
        - 用户名必须以字母开头，只能包含字母、数字、点和下划线
        - 用户名长度限制在1-50个字符
        - 邮箱必须是有效的邮箱格式，长度限制在1-100个字符
        - 密码长度限制在8-128个字符
        - 两次输入的密码必须匹配
        - 用户名和邮箱必须是唯一的（通过自定义验证方法检查）

    自定义验证:
        - validate_username: 检查用户名是否已被使用
        - validate_email: 检查邮箱是否已被注册
    """
    username = StringField('用户名', validators=[
        DataRequired(message='用户名不能为空'),
        Length(1, 50, message='用户名长度必须在1-50个字符之间'),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               '用户名只能包含字母、数字、点和下划线')
    ])
    email = StringField('邮箱', validators=[
        DataRequired(message='邮箱不能为空'),
        Length(1, 100, message='邮箱长度必须在1-100个字符之间'),
        Email(message='请输入有效的邮箱地址')
    ])
    password = PasswordField('密码', validators=[
        DataRequired(message='密码不能为空'),
        Length(8, 128, message='密码长度必须在8-128个字符之间'),
        EqualTo('password2', message='两次输入的密码不匹配')
    ])
    password2 = PasswordField('确认密码', validators=[
        DataRequired(message='确认密码不能为空')
    ])
    submit = SubmitField('注册')

    def validate_username(self, field):
        """验证用户名是否已存在

        自定义验证方法，检查数据库中是否已存在相同的用户名。
        如果用户名已存在，则抛出ValidationError异常，表单验证失败。

        WTForms会自动调用以"validate_"开头且后跟字段名的方法作为自定义验证器。

        Args:
            field: WTForms字段对象，包含用户输入的用户名

        Raises:
            ValidationError: 当用户名已被使用时抛出
        """
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('该用户名已被使用')

    def validate_email(self, field):
        """验证邮箱是否已存在

        自定义验证方法，检查数据库中是否已存在相同的邮箱地址。
        如果邮箱已存在，则抛出ValidationError异常，表单验证失败。

        WTForms会自动调用以"validate_"开头且后跟字段名的方法作为自定义验证器。

        Args:
            field: WTForms字段对象，包含用户输入的邮箱地址

        Raises:
            ValidationError: 当邮箱已被注册时抛出
        """
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已被注册')

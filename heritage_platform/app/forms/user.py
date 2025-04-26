"""
用户管理表单模块

本模块定义了与用户管理相关的表单类，包括：
1. 个人资料表单：用户修改自己的基本信息
2. 密码修改表单：用户修改自己的登录密码
3. 用户管理表单：管理员创建和编辑用户账号

表单特性：
- 数据验证：使用WTForms验证器确保输入数据符合要求
- 自定义验证：实现用户名和邮箱唯一性检查
- 文件上传：支持用户头像上传和验证
- 角色管理：支持管理员设置用户角色
- CSRF保护：通过Flask-WTF提供的CSRF保护机制防止跨站请求伪造
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from app.models import User

class ProfileForm(FlaskForm):
    """用户资料表单

    用于用户修改个人资料的表单，包含用户名、邮箱和头像字段。
    实现了自定义验证，确保用户名和邮箱的唯一性。

    字段:
        username: 用户名字段，必填，长度1-50
        email: 邮箱字段，必填，长度1-100，必须是有效的邮箱格式
        avatar: 头像上传字段，可选，限制文件类型为常见图片格式
        submit: 提交按钮

    验证规则:
        - 用户名和邮箱为必填字段
        - 用户名长度限制在1-50个字符
        - 邮箱长度限制在1-100个字符，且必须是有效的邮箱格式
        - 用户名和邮箱不能与其他用户重复（除非是用户自己当前的值）
        - 头像必须是jpg、jpeg、png或gif格式的图片
    """
    username = StringField('用户名', validators=[
        DataRequired(message='用户名不能为空'),
        Length(1, 50, message='用户名长度必须在1-50个字符之间')
    ])

    email = StringField('邮箱', validators=[
        DataRequired(message='邮箱不能为空'),
        Length(1, 100, message='邮箱长度必须在1-100个字符之间'),
        Email(message='请输入有效的邮箱地址')
    ])

    avatar = FileField('头像', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '只允许上传jpg、jpeg、png或gif格式的图片!')
    ])

    submit = SubmitField('保存修改')

    def validate_username(self, field):
        """验证用户名是否已存在

        如果用户修改了用户名，检查新用户名是否已被其他用户使用。
        如果用户名未修改，则跳过验证。

        参数:
            field: WTForms字段对象，包含用户输入的用户名

        异常:
            ValidationError: 如果用户名已被其他用户使用
        """
        # 只有当用户修改了用户名时才进行验证
        if field.data != current_user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('该用户名已被使用')

    def validate_email(self, field):
        """验证邮箱是否已存在

        如果用户修改了邮箱，检查新邮箱是否已被其他用户注册。
        如果邮箱未修改，则跳过验证。

        参数:
            field: WTForms字段对象，包含用户输入的邮箱

        异常:
            ValidationError: 如果邮箱已被其他用户注册
        """
        # 只有当用户修改了邮箱时才进行验证
        if field.data != current_user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已被注册')

class PasswordForm(FlaskForm):
    """修改密码表单

    用于用户修改自己登录密码的表单，包含当前密码、新密码和确认密码字段。
    实现了密码确认验证，确保用户正确输入新密码。

    字段:
        current_password: 当前密码字段，必填，用于验证用户身份
        new_password: 新密码字段，必填，长度8-128，必须与确认密码匹配
        confirm_password: 确认新密码字段，必填，用于确认新密码输入无误
        submit: 提交按钮

    验证规则:
        - 所有字段均为必填
        - 新密码长度限制在8-128个字符
        - 新密码必须与确认密码完全匹配
        - 当前密码验证在视图函数中进行，确保只有知道当前密码的用户才能修改密码

    安全特性:
        - 密码字段使用PasswordField，浏览器中不会明文显示
        - 密码长度要求至少8个字符，增强安全性
        - 要求确认新密码，减少输入错误的可能性
    """
    current_password = PasswordField('当前密码', validators=[
        DataRequired(message='请输入当前密码')
    ])

    new_password = PasswordField('新密码', validators=[
        DataRequired(message='请输入新密码'),
        Length(8, 128, message='密码长度必须在8-128个字符之间'),
        EqualTo('confirm_password', message='两次输入的密码不匹配')
    ])

    confirm_password = PasswordField('确认新密码', validators=[
        DataRequired(message='请确认新密码')
    ])

    submit = SubmitField('修改密码')

class UserForm(FlaskForm):
    """管理员用户管理表单

    用于管理员创建和编辑用户账号的表单，包含用户基本信息和角色设置。
    可用于创建新用户或编辑现有用户。
    实现了自定义验证，确保用户名和邮箱的唯一性，同时允许编辑时保持原值。

    字段:
        username: 用户名字段，必填，长度1-50
        email: 邮箱字段，必填，长度1-100，必须是有效的邮箱格式
        password: 密码字段，创建用户时必填，编辑用户时可选，长度8-128
        role: 用户角色选择字段，必填，包含学生、教师和管理员三种角色
        avatar: 头像上传字段，可选，限制文件类型为常见图片格式
        submit: 提交按钮

    验证规则:
        - 用户名、邮箱和角色为必填字段
        - 用户名长度限制在1-50个字符
        - 邮箱长度限制在1-100个字符，且必须是有效的邮箱格式
        - 密码长度限制在8-128个字符（如果提供）
        - 用户名和邮箱不能与其他用户重复（编辑时可保持原值）
        - 头像必须是jpg、jpeg、png或gif格式的图片

    使用场景:
        - 管理员创建新用户账号
        - 管理员编辑现有用户信息
        - 管理员重置用户密码
        - 管理员调整用户角色
    """
    username = StringField('用户名', validators=[
        DataRequired(message='用户名不能为空'),
        Length(1, 50, message='用户名长度必须在1-50个字符之间')
    ])

    email = StringField('邮箱', validators=[
        DataRequired(message='邮箱不能为空'),
        Length(1, 100, message='邮箱长度必须在1-100个字符之间'),
        Email(message='请输入有效的邮箱地址')
    ])

    password = PasswordField('密码', validators=[
        Optional(),  # 编辑用户时密码可选，为空则不修改密码
        Length(8, 128, message='密码长度必须在8-128个字符之间')
    ])

    role = SelectField('用户角色', choices=[
        ('student', '学生'),    # 普通学生用户
        ('teacher', '教师'),    # 教师用户，具有内容管理权限
        ('admin', '管理员')     # 管理员用户，具有系统管理权限
    ], validators=[DataRequired(message='必须选择用户角色')])

    avatar = FileField('头像', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '只允许上传jpg、jpeg、png或gif格式的图片!')
    ])

    submit = SubmitField('保存')

    def __init__(self, obj=None, *args, **kwargs):
        """初始化表单

        如果提供了obj参数（现有用户对象），则表单将用于编辑该用户；
        否则表单将用于创建新用户。

        参数:
            obj: 要编辑的User对象，创建新用户时为None
            *args, **kwargs: 传递给父类构造函数的其他参数
        """
        # 确保将obj参数传递给父类的__init__方法，用于表单字段初始值
        super(UserForm, self).__init__(obj=obj, *args, **kwargs)
        # 保存原始用户对象，用于验证时比较
        self.original_user = obj

    def validate_username(self, field):
        """验证用户名是否已存在 - 编辑时允许用户保持原用户名

        如果是编辑现有用户且用户名未变，则跳过验证；
        否则检查用户名是否已被其他用户使用。

        参数:
            field: WTForms字段对象，包含用户输入的用户名

        异常:
            ValidationError: 如果用户名已被其他用户使用
        """
        # 如果是编辑且用户名没变，则跳过验证
        if self.original_user and field.data == self.original_user.username:
            return

        # 检查用户名是否已存在
        user = User.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError('该用户名已被使用')

    def validate_email(self, field):
        """验证邮箱是否已存在 - 编辑时允许用户保持原邮箱

        如果是编辑现有用户且邮箱未变，则跳过验证；
        否则检查邮箱是否已被其他用户注册。

        参数:
            field: WTForms字段对象，包含用户输入的邮箱

        异常:
            ValidationError: 如果邮箱已被其他用户注册
        """
        # 如果是编辑且邮箱没变，则跳过验证
        if self.original_user and field.data == self.original_user.email:
            return

        # 检查邮箱是否已存在
        user = User.query.filter_by(email=field.data).first()
        if user:
            raise ValidationError('该邮箱已被注册')

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from app.models import User

class ProfileForm(FlaskForm):
    """用户资料表单"""
    username = StringField('用户名', validators=[DataRequired(), Length(1, 50)])
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 100), Email()])
    avatar = FileField('头像', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '只允许上传图片!')
    ])
    submit = SubmitField('保存修改')
    
    def validate_username(self, field):
        """验证用户名是否已存在"""
        if field.data != current_user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('该用户名已被使用')

    def validate_email(self, field):
        """验证邮箱是否已存在"""
        if field.data != current_user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已被注册')

class PasswordForm(FlaskForm):
    """修改密码表单"""
    current_password = PasswordField('当前密码', validators=[DataRequired()])
    new_password = PasswordField('新密码', validators=[
        DataRequired(), Length(8, 128), EqualTo('confirm_password', message='两次输入的密码不匹配')])
    confirm_password = PasswordField('确认新密码', validators=[DataRequired()])
    submit = SubmitField('修改密码')

class UserForm(FlaskForm):
    """管理员用户管理表单"""
    username = StringField('用户名', validators=[DataRequired(), Length(1, 50)])
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 100), Email()])
    password = PasswordField('密码', validators=[
        Optional(), Length(8, 128)])
    role = SelectField('用户角色', choices=[
        ('student', '学生'),
        ('teacher', '教师'),
        ('admin', '管理员')
    ], validators=[DataRequired()])
    avatar = FileField('头像', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '只允许上传图片!')
    ])
    submit = SubmitField('保存')
    
    def __init__(self, obj=None, *args, **kwargs):
        # 修复：确保将obj参数传递给父类的__init__方法
        super(UserForm, self).__init__(obj=obj, *args, **kwargs)
        self.original_user = obj
        
    def validate_username(self, field):
        """验证用户名是否已存在 - 编辑时允许用户保持原用户名"""
        if self.original_user and field.data == self.original_user.username:
            # 如果是编辑且用户名没变，则跳过验证
            return
        
        user = User.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError('该用户名已被使用')
            
    def validate_email(self, field):
        """验证邮箱是否已存在 - 编辑时允许用户保持原邮箱"""
        if self.original_user and field.data == self.original_user.email:
            # 如果是编辑且邮箱没变，则跳过验证
            return
        
        user = User.query.filter_by(email=field.data).first()
        if user:
            raise ValidationError('该邮箱已被注册')

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
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

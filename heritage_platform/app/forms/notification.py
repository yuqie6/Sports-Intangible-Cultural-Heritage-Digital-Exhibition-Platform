"""
通知和公告表单模块

本模块定义了与系统通知和公告相关的表单类，包括：
- 公告表单：用于管理员和教师创建系统公告

表单特性：
- 数据验证：使用WTForms验证器确保输入数据符合要求
- CSRF保护：通过Flask-WTF提供的CSRF保护机制防止跨站请求伪造
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class AnnouncementForm(FlaskForm):
    """公告表单

    用于创建系统公告的表单，通常只有管理员和教师有权限使用。
    公告创建后会通知所有用户或特定用户组。

    字段:
        title: 公告标题字段，必填，长度1-100
        content: 公告内容文本区域，必填
        submit: 提交按钮

    验证规则:
        - 标题和内容为必填字段
        - 标题长度限制在1-100个字符

    使用场景:
        - 系统重要通知
        - 活动公告
        - 课程通知
        - 平台更新公告
    """
    title = StringField('公告标题', validators=[
        DataRequired(message='公告标题不能为空'),
        Length(1, 100, message='标题长度必须在1-100个字符之间')
    ])

    content = TextAreaField('公告内容', validators=[
        DataRequired(message='公告内容不能为空')
    ])

    submit = SubmitField('发布公告')
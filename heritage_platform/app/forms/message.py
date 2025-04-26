"""
消息系统表单模块

本模块定义了消息系统所需的各种表单类，包括：
1. 私信表单：发送和回复私信
2. 群组表单：创建群组、添加成员、发送群组消息
3. 广播表单：向多个用户群发消息

表单特性：
- 数据验证：确保输入数据符合要求
- 动态选项：根据当前用户角色动态加载可选项
- 自定义验证：实现特定业务逻辑的验证
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, HiddenField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired, Length, ValidationError, Optional
# 修改导入方式，避免循环导入
from app.models.user import User
from app.models.message import MessageGroup
from flask_login import current_user

class MessageForm(FlaskForm):
    """发送私信表单

    用于创建新的私信，包含收件人和消息内容字段。
    实现了自定义验证，确保收件人用户存在。
    """
    receiver = StringField('收件人', validators=[DataRequired(), Length(1, 50)])
    content = TextAreaField('私信内容', validators=[DataRequired(), Length(1, 2000)])
    submit = SubmitField('发送')

    def validate_receiver(self, field):
        """验证收件人是否存在"""
        user = User.query.filter_by(username=field.data).first()
        if not user:
            raise ValidationError('该用户不存在')

class ReplyMessageForm(FlaskForm):
    """回复私信表单

    用于回复已有的私信，包含回复内容和隐藏的收件人ID字段。
    相比MessageForm更简化，因为收件人已经确定。
    """
    content = TextAreaField('回复内容', validators=[DataRequired(), Length(1, 2000)])
    receiver_id = HiddenField('收件人ID', validators=[DataRequired()])
    submit = SubmitField('发送')

class GroupMessageForm(FlaskForm):
    """发送群组消息表单

    用于向群组发送消息，包含消息内容和隐藏的群组ID字段。
    设计为在群组详情页面内使用，群组ID通过隐藏字段传递。
    """
    group_id = HiddenField('群组ID', validators=[DataRequired()])
    content = TextAreaField('消息内容', validators=[DataRequired(), Length(1, 2000)])
    submit = SubmitField('发送到群组')

class BroadcastMessageForm(FlaskForm):
    """群发消息表单，仅管理员和教师可用

    用于向多个用户同时发送消息，支持多种接收者类型选择。

    特性：
    - 动态加载群组选项：根据当前用户角色显示不同的可选群组
    - 教师只能看到自己创建的群组
    - 管理员可以看到所有群组
    - 支持多种接收者类型：所有用户、学生、教师、管理员、特定群组
    """
    recipient_type = SelectField('接收者类型', choices=[
        ('all', '所有用户'),
        ('students', '所有学生'),
        ('teachers', '所有教师'),
        ('admins', '所有管理员'),
        ('specific_groups', '特定群组')
    ], validators=[DataRequired()])
    groups = SelectMultipleField('选择群组', coerce=int)
    content = TextAreaField('消息内容', validators=[DataRequired(), Length(1, 3000)])
    submit = SubmitField('群发消息')

    def __init__(self, *args, **kwargs):
        super(BroadcastMessageForm, self).__init__(*args, **kwargs)
        # 动态加载群组选项
        if current_user.is_teacher or current_user.is_admin:
            # 教师可以看到自己创建的群组
            if current_user.is_teacher:
                groups = MessageGroup.query.filter_by(creator_id=current_user.id).all()
            # 管理员可以看到所有群组
            else:
                groups = MessageGroup.query.all()

            self.groups.choices = [(g.id, g.name) for g in groups]

class CreateGroupForm(FlaskForm):
    """创建消息群组表单

    用于创建新的消息群组，包含群组基本信息和初始成员选择。

    特性：
    - 动态加载可选成员：根据当前用户角色显示不同的可选成员
    - 教师只能添加学生作为成员
    - 管理员可以添加任何用户作为成员
    - 自动排除当前用户，因为创建者会自动成为群组管理员
    - 支持多种群组类型：班级、小组、自定义
    """
    name = StringField('群组名称', validators=[DataRequired(), Length(1, 100)])
    description = TextAreaField('群组描述', validators=[Optional(), Length(0, 500)])
    group_type = SelectField('群组类型', choices=[
        ('class', '班级'),
        ('team', '小组'),
        ('custom', '自定义')
    ], validators=[DataRequired()])
    members = SelectMultipleField('添加成员', coerce=int)
    submit = SubmitField('创建群组')

    def __init__(self, *args, **kwargs):
        super(CreateGroupForm, self).__init__(*args, **kwargs)
        # 动态加载可选的用户列表
        # 教师只能添加学生
        if current_user.is_teacher:
            users = User.query.filter_by(role='student').all()
        # 管理员可以添加任何用户
        elif current_user.is_admin:
            users = User.query.all()
        else:
            users = []

        # 排除自己，因为创建者会自动成为成员
        users = [u for u in users if u.id != current_user.id]
        self.members.choices = [(u.id, f"{u.username} ({u.email})") for u in users]

class AddMembersForm(FlaskForm):
    """向群组添加成员的表单

    用于向现有群组添加新成员，仅群组管理员可用。

    特性：
    - 动态加载可选成员：根据当前用户角色和群组现有成员情况显示可选成员
    - 教师只能添加学生作为成员
    - 管理员可以添加任何用户作为成员
    - 自动过滤已经是群组成员的用户
    - 支持在初始化时通过参数设置群组ID
    """
    group_id = HiddenField('群组ID', validators=[DataRequired()])
    members = SelectMultipleField('添加成员', coerce=int, validators=[DataRequired()])
    submit = SubmitField('添加成员')

    def __init__(self, group_id=None, *args, **kwargs):
        super(AddMembersForm, self).__init__(*args, **kwargs)

        if group_id:
            self.group_id.data = group_id

            # 获取当前群组
            group = MessageGroup.query.get(group_id)

            if group:
                # 获取现有成员的ID列表
                existing_member_ids = [m.user_id for m in group.members]

                # 根据当前用户角色获取可添加的用户
                if current_user.is_teacher:
                    available_users = User.query.filter_by(role='student').all()
                elif current_user.is_admin:
                    available_users = User.query.all()
                else:
                    available_users = []

                # 过滤掉已经是成员的用户
                available_users = [u for u in available_users if u.id not in existing_member_ids]

                self.members.choices = [(u.id, f"{u.username} ({u.email})") for u in available_users]

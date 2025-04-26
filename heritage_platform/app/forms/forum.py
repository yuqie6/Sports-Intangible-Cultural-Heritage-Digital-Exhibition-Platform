"""
论坛表单模块

本模块定义了与论坛相关的表单类，包括：
1. 主题表单：用于创建新的论坛主题
2. 回复表单：用于在主题下发表回复

表单特性：
- 数据验证：使用WTForms验证器确保输入数据符合要求
- 分类选择：主题表单提供预定义的分类选项
- 嵌套回复：回复表单支持嵌套回复结构
- CSRF保护：通过Flask-WTF提供的CSRF保护机制防止跨站请求伪造
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length

class TopicForm(FlaskForm):
    """论坛主题表单

    用于创建新的论坛主题的表单，包含标题、分类和内容字段。
    使用WTForms验证器确保输入数据符合要求。

    字段:
        title: 主题标题字段，必填，长度1-100
        category: 主题分类下拉选择字段，必填，包含预定义的分类选项
        content: 主题内容文本区域，必填，长度1-10000
        submit: 提交按钮

    验证规则:
        - 标题和内容为必填字段
        - 标题长度限制在1-100个字符
        - 内容长度限制在1-10000个字符
        - 分类必须从预定义选项中选择
    """
    title = StringField('标题', validators=[
        DataRequired(message='标题不能为空'),
        Length(1, 100, message='标题长度必须在1-100个字符之间')
    ])

    category = SelectField('分类', validators=[DataRequired(message='必须选择一个分类')], choices=[
        ('讨论', '讨论'),           # 一般性讨论主题
        ('教学', '教学'),           # 教学相关主题
        ('活动', '活动'),           # 活动通知和讨论
        ('资源分享', '资源分享'),    # 学习资源分享
        ('问答', '问答')            # 问题解答
    ])

    content = TextAreaField('内容', validators=[
        DataRequired(message='内容不能为空'),
        Length(1, 10000, message='内容长度必须在1-10000个字符之间')
    ])

    submit = SubmitField('发布主题')

class PostForm(FlaskForm):
    """论坛回复表单

    用于在论坛主题下发表回复的表单，支持嵌套回复结构。
    使用WTForms验证器确保输入数据符合要求。

    字段:
        content: 回复内容文本区域，必填，长度1-5000
        parent_id: 父回复ID隐藏字段，用于嵌套回复
        reply_to_user_id: 回复目标用户ID隐藏字段
        submit: 提交按钮

    验证规则:
        - 回复内容为必填字段
        - 回复内容长度限制在1-5000个字符

    使用方式:
        - 直接回复主题时，parent_id和reply_to_user_id为空
        - 回复其他用户的回复时，设置parent_id为被回复的回复ID，
          reply_to_user_id为被回复用户的ID
    """
    content = TextAreaField('回复内容', validators=[
        DataRequired(message='回复内容不能为空'),
        Length(1, 5000, message='回复内容长度必须在1-5000个字符之间')
    ])

    # 父回复ID，用于实现嵌套回复结构
    # 如果为空，表示直接回复主题；否则表示回复某条回复
    parent_id = HiddenField('父评论ID')

    # 回复目标用户ID，用于标识回复的是哪个用户
    # 与parent_id配合使用，实现"回复@某用户"的功能
    reply_to_user_id = HiddenField('回复用户ID')

    submit = SubmitField('发表回复')

"""
非物质文化遗产内容和评论表单模块

本模块定义了与非遗内容创建、编辑和评论相关的表单类。
包含ContentForm用于创建和编辑各种类型的内容（文章、图片、视频、富文本），
以及CommentForm用于用户对内容进行评论和回复。
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, Optional
from flask_wtf.file import FileField, FileAllowed

class ContentForm(FlaskForm):
    """内容创建与编辑表单类

    用于创建和编辑非遗项目相关的各类内容，支持多种内容类型，
    包括纯文本文章、图片、视频和富文本文章。表单根据选择的内容类型
    动态显示相应的输入字段。

    属性:
        title: 内容标题字段，必填，长度1-100字符
        heritage_id: 关联的非遗项目ID，必填，下拉选择
        content_type: 内容类型选择，必填，包括文章、图片、视频和富文本文章
        cover_image: 内容封面图片上传字段，可选
        text_content: 纯文本内容字段，用于文章类型
        rich_content: 富文本内容字段，用于富文本文章类型
        file: 单个文件上传字段，用于图片或视频类型
        multiple_images: 多图片上传字段，支持批量上传
        image_captions: 图片说明隐藏字段，存储AJAX上传的图片说明
        uploaded_images: 已上传图片列表隐藏字段，用于编辑模式
        submit: 表单提交按钮
    """
    title = StringField('标题', validators=[
        DataRequired(message='标题不能为空'),
        Length(1, 100, message='标题长度必须在1-100字符之间')
    ])

    heritage_id = SelectField('所属非遗项目', validators=[
        DataRequired(message='必须选择一个非遗项目')
    ], coerce=int)  # coerce=int 确保值被转换为整数

    content_type = SelectField('内容类型', validators=[DataRequired(message='必须选择内容类型')], choices=[
        ('article', '文章'),         # 纯文本文章
        ('image', '图片'),           # 图片内容
        ('video', '视频'),           # 视频内容
        ('multimedia', '富文本文章')  # 包含格式化文本、图片等的富文本文章
    ])

    cover_image = FileField('封面图片', validators=[
        Optional(),  # 封面图片为可选字段
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '只允许上传JPG、JPEG、PNG和GIF格式的图片!')
    ])

    text_content = TextAreaField('纯文本内容', validators=[Optional()])  # 用于普通文章

    rich_content = TextAreaField('富文本内容', validators=[Optional()])  # 用于CKEditor或其他富文本编辑器

    file = FileField('文件', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov', 'avi'], '只允许上传图片或视频!')
    ])  # 用于上传单个图片或视频文件

    # 多图片上传字段，支持批量选择多个图片文件
    multiple_images = FileField('上传多张图片', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '只允许上传JPG、JPEG、PNG和GIF格式的图片!')
    ], render_kw={"multiple": True})  # multiple属性允许选择多个文件

    # 图片说明隐藏字段，用于AJAX上传后存储图片说明
    # 通常以JSON格式存储，包含每张图片的说明文字
    image_captions = HiddenField('图片说明')

    # 已上传图片列表隐藏字段，用于编辑模式下显示已上传的图片
    # 通常以JSON格式存储图片路径和其他元数据
    uploaded_images = HiddenField('已上传图片')

    submit = SubmitField('发布')

class CommentForm(FlaskForm):
    """评论和回复表单类

    用于用户对内容进行评论或回复其他用户的评论。
    支持嵌套评论结构，可以指定父评论和回复目标用户。

    属性:
        text: 评论内容文本区域，必填，长度1-1000字符
        parent_id: 父评论ID隐藏字段，用于嵌套评论
        reply_to_user_id: 回复目标用户ID隐藏字段
        submit: 表单提交按钮
    """
    text = TextAreaField('评论内容', validators=[
        DataRequired(message='评论内容不能为空'),
        Length(1, 1000, message='评论长度必须在1-1000字符之间')
    ])

    # 父评论ID，用于实现评论嵌套结构
    # 如果为空，表示这是一级评论；否则表示这是对某条评论的回复
    parent_id = HiddenField('父评论ID')

    # 回复目标用户ID，用于标识回复的是哪个用户
    # 与parent_id配合使用，实现"回复@某用户"的功能
    reply_to_user_id = HiddenField('回复用户ID')

    submit = SubmitField('发表评论')

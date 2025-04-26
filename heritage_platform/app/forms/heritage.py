"""
非物质文化遗产项目表单模块

本模块定义了与非物质文化遗产项目相关的表单类，用于创建和编辑非遗项目信息。
表单包含项目名称、分类、描述和封面图片等字段，并实现了相应的数据验证。
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileField, FileAllowed

class HeritageItemForm(FlaskForm):
    """非遗项目表单类

    用于创建和编辑非物质文化遗产项目的表单。包含项目基本信息字段，
    如名称、分类、描述和封面图片，并对各字段实施数据验证。

    属性:
        name: 项目名称字段，必填，长度1-100字符
        category: 项目分类下拉选择字段，必填，包含预定义的分类选项
        description: 项目描述文本区域，必填
        cover_image: 项目封面图片上传字段，限制文件类型为常见图片格式
        submit: 表单提交按钮
    """
    name = StringField('项目名称', validators=[
        DataRequired(message='项目名称不能为空'),
        Length(1, 100, message='项目名称长度必须在1-100字符之间')
    ])

    category = SelectField('项目分类', validators=[DataRequired(message='必须选择一个分类')], choices=[
        ('武术', '武术'),           # 武术类非遗项目
        ('舞蹈', '舞蹈'),           # 舞蹈类非遗项目
        ('民俗体育', '民俗体育'),    # 民俗体育类非遗项目
        ('传统体育', '传统体育'),    # 传统体育类非遗项目
        ('其他', '其他')            # 其他类型非遗项目
    ])

    description = TextAreaField('项目描述', validators=[DataRequired(message='项目描述不能为空')])

    cover_image = FileField('封面图片', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '只允许上传jpg、jpeg、png或gif格式的图片!')
    ])

    submit = SubmitField('提交')

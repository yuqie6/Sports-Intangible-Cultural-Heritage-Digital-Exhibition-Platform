from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, Optional
from flask_wtf.file import FileField, FileAllowed

class ContentForm(FlaskForm):
    """内容表单"""
    title = StringField('标题', validators=[DataRequired(), Length(1, 100)])
    heritage_id = SelectField('所属非遗项目', validators=[DataRequired()], coerce=int)
    content_type = SelectField('内容类型', validators=[DataRequired()], choices=[
        ('article', '文章'),
        ('image', '图片'),
        ('video', '视频'),
        ('multimedia', '多媒体文章')  # 新增多媒体文章类型
    ])
    cover_image = FileField('封面图片', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '只允许上传JPG、JPEG、PNG和GIF格式的图片!')
    ])
    text_content = TextAreaField('纯文本内容', validators=[Optional()])
    rich_content = TextAreaField('富文本内容', validators=[Optional()])  # 用于CKEditor或其他富文本编辑器
    file = FileField('文件', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov', 'avi'], '只允许上传图片或视频!')
    ])
    submit = SubmitField('发布')

class CommentForm(FlaskForm):
    """评论表单"""
    text = TextAreaField('评论内容', validators=[DataRequired(), Length(1, 1000)])
    parent_id = HiddenField('父评论ID')
    reply_to_user_id = HiddenField('回复用户ID')
    submit = SubmitField('发表评论')

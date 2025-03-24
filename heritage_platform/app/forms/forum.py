from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length

class TopicForm(FlaskForm):
    """论坛主题表单"""
    title = StringField('标题', validators=[DataRequired(), Length(1, 100)])
    category = SelectField('分类', validators=[DataRequired()], choices=[
        ('讨论', '讨论'),
        ('教学', '教学'),
        ('活动', '活动'),
        ('资源分享', '资源分享'),
        ('问答', '问答')
    ])
    content = TextAreaField('内容', validators=[DataRequired(), Length(1, 10000)])
    submit = SubmitField('发布主题')

class PostForm(FlaskForm):
    """论坛回复表单"""
    content = TextAreaField('回复内容', validators=[DataRequired(), Length(1, 5000)])
    submit = SubmitField('发表回复')

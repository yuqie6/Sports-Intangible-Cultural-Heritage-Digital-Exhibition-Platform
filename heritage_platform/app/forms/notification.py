from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class AnnouncementForm(FlaskForm):
    """公告表单"""
    title = StringField('公告标题', validators=[DataRequired(), Length(1, 100)])
    content = TextAreaField('公告内容', validators=[DataRequired()])
    submit = SubmitField('发布公告')
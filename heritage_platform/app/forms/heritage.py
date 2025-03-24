from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileField, FileAllowed

class HeritageItemForm(FlaskForm):
    """非遗项目表单"""
    name = StringField('项目名称', validators=[DataRequired(), Length(1, 100)])
    category = SelectField('项目分类', validators=[DataRequired()], choices=[
        ('武术', '武术'),
        ('舞蹈', '舞蹈'),
        ('民俗体育', '民俗体育'),
        ('传统体育', '传统体育'),
        ('其他', '其他')
    ])
    description = TextAreaField('项目描述', validators=[DataRequired()])
    cover_image = FileField('封面图片', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], '只允许上传图片!')
    ])
    submit = SubmitField('提交')

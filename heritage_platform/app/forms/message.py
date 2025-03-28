from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, ValidationError
from app.models import User

class MessageForm(FlaskForm):
    """发送私信表单"""
    receiver = StringField('收件人', validators=[DataRequired(), Length(1, 50)])
    content = TextAreaField('私信内容', validators=[DataRequired(), Length(1, 500)])
    submit = SubmitField('发送')
    
    def validate_receiver(self, field):
        """验证收件人是否存在"""
        user = User.query.filter_by(username=field.data).first()
        if not user:
            raise ValidationError('该用户不存在')

class ReplyMessageForm(FlaskForm):
    """回复私信表单"""
    content = TextAreaField('回复内容', validators=[DataRequired(), Length(1, 500)])
    receiver_id = HiddenField('收件人ID', validators=[DataRequired()])
    submit = SubmitField('发送')
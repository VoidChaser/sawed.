from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired


class PostsForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    text = TextAreaField("Содержание")
    file = FileField("Картинка")
    is_private = BooleanField("Личное")
    submit = SubmitField('Применить')
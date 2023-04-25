from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, MultipleFileField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename


class PostsForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    text = TextAreaField("Содержание")
    files = MultipleFileField("Картинка")
    is_private = BooleanField("Личное")
    submit = SubmitField('Применить')
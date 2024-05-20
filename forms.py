from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, FileField, DecimalField
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditorField


class CreatePostForm(FlaskForm):
    title = StringField("Tytuł", validators=[DataRequired()])
    image = FileField('Zdjęcie', validators=[DataRequired()])
    body = CKEditorField("Treść postu", validators=[DataRequired()])
    submit = SubmitField("Dodaj post")


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Hasło", validators=[DataRequired()])
    name = StringField("Nazwa użytkownika", validators=[DataRequired()])
    submit = SubmitField("Zarejestruj")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Hasło", validators=[DataRequired()])
    submit = SubmitField("Zaloguj")


class CommentForm(FlaskForm):
    comment_text = CKEditorField("Komentarze", validators=[DataRequired()])
    submit = SubmitField("Dodaj komentarz")


class ProductForm(FlaskForm):
    name = StringField('Nazwa rośliny', validators=[DataRequired()])
    type = StringField('Rodzaj', validators=[DataRequired()])
    price = DecimalField('Cena', validators=[DataRequired()])
    image = FileField('Zdjęcie', validators=[DataRequired()])
    submit = SubmitField('Dodaj produkt')

# Flask-WTF handles passing form data between FLASK and WTForms
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, PasswordField, SelectField, validators
from wtforms.validators import DataRequired, Email, Length

# Forms are regular Python classes
class SigninForm(FlaskForm):
    email = StringField('email', validators=[DataRequired(), Email(message='Invalid email'), Length(max=50)])
    password = PasswordField('password',validators=[DataRequired(), Length(min=6, max=90)])

class SignupForm(FlaskForm):
    email = StringField('email', validators=[DataRequired(), Email(message='Invalid email'), Length(max=50)])
    password = PasswordField('password',validators=[DataRequired(), Length(min=6, max=90)])

class AddForm(FlaskForm):
    email = StringField('email', validators=[DataRequired(),Email(message='Invalid email'),Length(max=50)])
    
class SelectForm(FlaskForm):
    select_email = SelectField('emails', validators=[DataRequired()])

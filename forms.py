from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, BooleanField, FloatField, FileField
from wtforms.validators import DataRequired, Email, Length,  Optional, NumberRange
from flask_wtf.file import FileAllowed, FileRequired
from wtforms import ValidationError

def validate_email_domain(form, field):
    if not field.data.endswith('@dut4life.ac.za'):
        raise ValidationError('Email must be in the format of "@dut4life.ac.za"')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=5)])
    submit = SubmitField('Login')           

class SignupForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email(), validate_email_domain])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=5)])
    role = SelectField('Role', choices=[('student', 'Student'), ('tutor', 'Tutor')], validators=[DataRequired()])
    average_grade = FloatField('Average Grade', validators=[Optional(), NumberRange(min=0, max=100)])
    result_document = FileField('Upload Academic Record', validators=[FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'Only PDF or image files allowed')])
    declaration = BooleanField('I confirm my uploaded academic record is accurate')
    submit = SubmitField('Sign Up')
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, BooleanField, FloatField, FileField
from wtforms.validators import DataRequired, Email, Length,  Optional, NumberRange
from flask_wtf.file import FileAllowed
from wtforms import ValidationError
from models import User

def validate_email_domain(form, field):
    if not field.data.endswith('@dut4life.ac.za'):
        raise ValidationError('Email must be in the format of "@dut4life.ac.za"')
    
# Check if email already exists in the database
def validate_unique_email(form, field):
    existing_user = User.query.filter_by(email=field.data).first()
    if existing_user:
        raise ValidationError('An account with this email already exists.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=5)])
    submit = SubmitField('Login')           

class SignupForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email(), validate_email_domain])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=5, message="Password must be at least 5 characters.")])
    role = SelectField('Role', choices=[('student', 'Student'), ('tutor', 'Tutor')], validators=[DataRequired()])
    department = SelectField('Department', choices=[('IT', 'Information Technology'), ('IS', 'Information Systems')], validators=[DataRequired()])
    average_grade = FloatField('Average Grade', validators=[Optional(), NumberRange(min=0, max=100)])
    result_document = FileField('Upload Academic Record', validators=[FileAllowed(['pdf', 'png', 'jpg', 'jpeg'], 'Only PDF or image files allowed')])
    declaration = BooleanField('I confirm my uploaded academic record is accurate')
    submit = SubmitField('Sign Up')

    def validate_average_grade(self, field):
        if self.role.data == 'tutor' and (field.data is None or field.data < 75):
            raise ValidationError('Tutors must have an average grade of at least 75%.')
    
    def validate_declaration(self, field):
        if self.role.data == 'tutor' and not field.data:
            raise ValidationError('Tutors must agree to the declaration.')
    
    def validate_result_document(self, field):
        if self.role.data == 'tutor' and not field.data:
            raise ValidationError('Tutors must upload their academic record.')
from flask import Flask, render_template, redirect, url_for, flash, request
from forms import LoginForm, SignupForm
from config import Config
from models import db, User
from flask_migrate import Migrate
from flask_mail import Mail, Message
import os

app = Flask(__name__)
app.config.from_object(Config)
mail = Mail(app)


def send_confirmation_email(student_email, tutor_email, student_name, tutor_name, date, time):
    """Send booking confirmation emails to both the student and tutor."""


    student_subject = "Tutor Booking Confirmation"
    student_body = f"Dear {student_name},\n\nYou have successfully booked {tutor_name} as your tutor on {date} at {time}.\n\nBest,\nTutoring Team"
    
    student_msg = Message(student_subject, recipients=[student_email])
    student_msg.body = student_body
    mail.send(student_msg)  

    tutor_subject = "New Student Booking"
    tutor_body = f"Dear {tutor_name},\n\nYou have a new student booking.\nStudent: {student_name}\nDate: {date}\nTime: {time}\n\nBest,\nTutoring Team"

    tutor_msg = Message(tutor_subject, recipients=[tutor_email])
    tutor_msg.body = tutor_body
    mail.send(tutor_msg)   
    
    @app.route('/book_tutor', methods=['GET', 'POST'])
    def book_tutor():
     if request.method == 'POST':
        
        student_email = request.form['student_email']
        tutor_email = request.form['tutor_email']
        student_name = request.form['student_name']
        tutor_name = request.form['tutor_name']
        date = request.form['date']  
        time = request.form['time']  

       
        send_confirmation_email(student_email, tutor_email, student_name, tutor_name, date, time)

        flash("Booking confirmed! Emails sent to both student and tutor.")
        return redirect(url_for('home'))  

    return render_template('book_tutor.html')  



db.init_app(app)
migrate = Migrate(app, db)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/auth/<string:form_type>', methods=['GET', 'POST'])
def auth(form_type="login"):
    login_form = LoginForm()
    signup_form = SignupForm()

    if login_form.validate_on_submit() and form_type == "login":
        email = login_form.email.data
        password = login_form.password.data
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:   
            flash("Login successful!")
            return redirect(url_for('home'))
        else:
            flash("Invalid email or password")

    if signup_form.validate_on_submit() and form_type == "signup":
        role = signup_form.role.data

        # Handle tutor-specific validation
        average_grade = None
        result_document_filename = None

        if role == "tutor":
            if signup_form.average_grade.data < 75:
                flash("You must have an average grade of at least 75% to be a tutor.")
                return redirect(url_for('auth', form_type="signup"))
             
            if not signup_form.declaration.data:
                flash("You must agree to the declaration.")
                return redirect(url_for('auth', form_type="signup"))

            if not signup_form.result_document.data:
                flash("Tutors must upload their academic record.")
                return redirect(url_for('auth', form_type="signup"))

            file = signup_form.result_document.data
            if file:
                result_document_filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(result_document_filename)
                average_grade = signup_form.average_grade.data

        new_user = User(
            name=signup_form.name.data,
            email=signup_form.email.data,
            password=signup_form.password.data,
            role=role,
            average_grade=average_grade,
            result_document=result_document_filename
        )

        db.session.add(new_user)
        db.session.commit()

        flash(f"Signup successful for {signup_form.email.data}!")
        return redirect(url_for('auth', form_type="login"))
    
    return render_template('auth.html', form_type=form_type, login_form=login_form, signup_form=signup_form)


if __name__ =='__main__':
    app.run(debug=True)

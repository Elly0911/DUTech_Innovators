from flask import Flask, render_template, redirect, url_for, flash, request, session, get_flashed_messages
from forms import LoginForm, SignupForm
from config import Config
from models import db, User
from flask_migrate import Migrate
import os

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def home():

    list(get_flashed_messages())
    user_logged_in = session.get('user_id', None)
    return render_template('home.html', user_logged_in=user_logged_in)

@app.route('/auth/<string:form_type>', methods=['GET', 'POST'])
def auth(form_type="login"):
    login_form = LoginForm()
    signup_form = SignupForm()
    result_document_filename = None

    list(get_flashed_messages())

    if login_form.validate_on_submit() and form_type == "login":
        email = login_form.email.data
        password = login_form.password.data
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            session['user_id'] = user.id  
            session['user_name'] = user.name  
            flash("Login successful!")
            return redirect(url_for('home'))
        else:
            flash("Invalid email or password")

    if signup_form.validate_on_submit() and form_type == "signup":
        role = signup_form.role.data
        average_grade = None

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
                result_document_filename = file.filename
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], result_document_filename)
                file.save(file_path)
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

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash("You have been logged out!")
    
    list(get_flashed_messages())  

    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)

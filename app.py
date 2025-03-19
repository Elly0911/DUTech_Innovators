from flask import Flask, render_template, redirect, url_for, flash, request, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash  # Import for password hashing
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
    user_logged_in = session.get('user_id', None)
    return render_template('home.html', user_logged_in=user_logged_in)

@app.route('/auth/<string:form_type>', methods=['GET', 'POST'])
def auth(form_type="login"):
    login_form = LoginForm()
    signup_form = SignupForm()

    if login_form.validate_on_submit() and form_type == "login":
        email = login_form.email.data
        password = login_form.password.data
        user = User.query.filter_by(email=email).first()

        # Check if user exists and password is correct
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id  
            session['user_name'] = user.name  
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid email or password", "danger")

    if signup_form.validate_on_submit() and form_type == "signup":
        # Check if email already exists
        existing_user = User.query.filter_by(email=signup_form.email.data).first()
        if existing_user:
            flash("An account with this email already exists.", "danger")
            return render_template('auth.html', form_type=form_type, login_form=login_form, signup_form=signup_form)
        
        # Hash the password before saving it to the database
        hashed_password = generate_password_hash(signup_form.password.data)

        # Handle file upload only if user is a tutor
        result_document_filename = None
        if signup_form.role.data == "tutor":
            file = signup_form.result_document.data
            if file:
                result_document_filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], result_document_filename)
                file.save(file_path)

        new_user = User(
            name=signup_form.name.data,
            email=signup_form.email.data,
            password=hashed_password,  # Store hashed password
            role=signup_form.role.data,
            department=signup_form.department.data,
            average_grade=signup_form.average_grade.data if signup_form.role.data == "tutor" else None,
            result_document=result_document_filename
        )

        db.session.add(new_user)
        db.session.commit()

        flash(f"Signup successful for {signup_form.email.data}!", "success")
        return redirect(url_for('auth', form_type="login"))

    return render_template('auth.html', form_type=form_type, login_form=login_form, signup_form=signup_form)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash("You have been logged out!", "info")
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)

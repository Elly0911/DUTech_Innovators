from flask import Flask, render_template, redirect, url_for, flash, request, session, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from flask_migrate import Migrate
from forms import LoginForm, SignupForm
from config import Config
from models import db, User
import os

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)
mail = Mail(app)  # Initialize Flask-Mail

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Function to send emails
def send_email(recipient, subject, body):
    msg = Message(subject, recipients=[recipient], sender=app.config['MAIL_USERNAME'])
    msg.body = body
    mail.send(msg)

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

        if user and check_password_hash(user.password, password):
            if user.role == "tutor":
                if user.status == "pending":
                    flash("Your tutor account is pending approval.", "warning")
                    return redirect(url_for('auth', form_type="login"))
                elif user.status == "declined":
                    flash("Your tutor application has been declined.", "danger")
                    return redirect(url_for('auth', form_type="login"))

            # Store user session
            session['user_id'] = user.id
            session['user_name'] = user.name

            # Redirect admin to admin dashboard
            if user.role == "admin":
                flash("Admin login successful!", "success")
                return redirect(url_for('admin_dashboard'))  # FIX: Explicitly redirect admins
            
            flash("Login successful!", "success")
            return redirect(url_for('home'))  # Other users go to home

        else:
            flash("Invalid email or password", "danger")

    if signup_form.validate_on_submit() and form_type == "signup":
        existing_user = User.query.filter_by(email=signup_form.email.data).first()
        if existing_user:
            flash("An account with this email already exists.", "danger")
            return render_template('auth.html', form_type=form_type, login_form=login_form, signup_form=signup_form)

        hashed_password = generate_password_hash(signup_form.password.data)
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
            password=hashed_password,
            role=signup_form.role.data,
            department=signup_form.department.data,
            average_grade=signup_form.average_grade.data if signup_form.role.data == "tutor" else None,
            result_document=result_document_filename,
            status="pending" if signup_form.role.data == "tutor" else None  # Admins do not have 'pending' status
        )

        db.session.add(new_user)
        db.session.commit()

        if new_user.role == "tutor":
            send_email(new_user.email, "Tutor Application Pending", 
                       "Your tutor application is pending approval. You will be notified once it is reviewed.")

        flash("Signup successful! Your tutor application is pending approval.", "info")
        return redirect(url_for('auth', form_type="login"))

    return render_template('auth.html', form_type=form_type, login_form=login_form, signup_form=signup_form)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash("You have been logged out!", "info")
    return redirect(url_for('home'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if 'user_id' not in session:
        flash("You must be logged in as an admin to access this page.", "danger")
        return redirect(url_for('auth', form_type="login"))

    user = User.query.get(session['user_id'])
    if not user or user.role != "admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for('home'))

    pending_tutors = User.query.filter_by(role="tutor", status="pending").all()

    # Get all tutors & students for stats calculation
    all_tutors = User.query.filter_by(role="tutor").all()
    students = User.query.filter_by(role="student").all()

    # Tutor & Student Statistics
    total_tutors = len(all_tutors)
    approved_tutors = sum(1 for tutor in all_tutors if tutor.status == "approved")
    pending_tutors_count = len(pending_tutors)  # Only pending tutors
    declined_tutors = sum(1 for tutor in all_tutors if tutor.status == "declined")
    total_students = len(students)

    return render_template(
        'admin_dashboard.html',
        tutors=pending_tutors,  # Only pending tutors appear in the table
        total_tutors=total_tutors, 
        approved_tutors=approved_tutors,
        pending_tutors=pending_tutors_count, 
        declined_tutors=declined_tutors,
        total_students=total_students
    )

@app.route('/approve_tutor/<int:user_id>')
def approve_tutor(user_id):

    if 'user_id' not in session:
        flash("You must be logged in as an admin.", "danger")
        return redirect(url_for('auth', form_type="login"))

    admin = User.query.get(session['user_id'])
    if not admin or admin.role != "admin":
        flash("Unauthorized action!", "danger")
        return redirect(url_for('home'))

    tutor = User.query.get(user_id)
    if tutor and tutor.role == "tutor":
        if tutor.average_grade >= 75:
            tutor.status = "approved"
            db.session.commit()
            send_email(tutor.email, "Tutor Application Approved", 
                       "Your tutor application has been approved. You can now log in.")
            flash(f"Tutor {tutor.name} approved!", "success")
        else:
            tutor.status = "declined"
            db.session.commit()
            send_email(tutor.email, "Tutor Application Declined", 
                       "Your tutor application has been declined due to an insufficient average grade.")
            flash(f"Tutor {tutor.name} declined!", "danger")

    return redirect(url_for('admin_dashboard'))

# Route to download academic record
@app.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)

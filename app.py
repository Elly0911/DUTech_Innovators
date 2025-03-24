from flask import Flask, render_template, redirect, url_for, flash, request, session, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from forms import LoginForm, SignupForm
from config import Config
from models import db, User, Booking
import os
import random
import string
from datetime import datetime, timedelta

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)
mail = Mail(app)  

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth"

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def send_email(recipient, subject, body):
    msg = Message(subject, recipients=[recipient], sender=app.config['MAIL_USERNAME'])
    msg.body = body
    mail.send(msg)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

notifications = []  # List of notifications for students

# Generate time slots (8 AM - 8 PM)
timeslots = [f"{hour:02d}:00" for hour in range(8, 20)]  

def generate_meeting_id():
    """Generate a random meeting ID"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

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

        
        if user and check_password_hash(user.password, password):
            
            if user.role == "tutor":
                if user.status == "pending":
                    flash("Your tutor account is pending approval.", "warning")
                    return redirect(url_for('auth', form_type="login"))
                elif user.status == "declined":
                    flash("Your tutor application has been declined.", "danger")
                    return redirect(url_for('auth', form_type="login"))
            
            
            login_user(user)
            flash("Login successful!", "success")

            
            if user.role == "student":
                return redirect(url_for('booking'))  
            
            # Redirect approved tutors to the tutor dashboard
            if user.role == "tutor" and user.status == "approved":
                return redirect(url_for('tutor_dashboard'))  

            # Redirect admin to admin dashboard or home for others
            return redirect(url_for('admin_dashboard') if user.role == "admin" else url_for('home'))
        else:
            flash("Invalid email or password", "danger")

    
    if signup_form.validate_on_submit() and form_type == "signup":
        existing_user = User.query.filter_by(email=signup_form.email.data).first()
        if existing_user:
            flash("An account with this email already exists.", "danger")
            return render_template('auth.html', form_type=form_type, login_form=login_form, signup_form=signup_form)

        hashed_password = generate_password_hash(signup_form.password.data)
        result_document_filename = None

        # Handle result document upload for tutors
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
            status="pending" if signup_form.role.data == "tutor" else None
        )

        db.session.add(new_user)
        db.session.commit()

        
        if new_user.role == "tutor":
            send_email(new_user.email, "Tutor Application Pending", 
                       "Your tutor application is pending approval. You will be notified once it is reviewed.")

        
        if new_user.role == "tutor":
            flash("Signup successful! Your tutor application is pending approval.", "info")
        else:
            flash("Signup successful! You are now a student.", "info")

        return redirect(url_for('auth', form_type="login"))

    return render_template('auth.html', form_type=form_type, login_form=login_form, signup_form=signup_form)

# Booking Page
@app.route('/booking', methods=['GET', 'POST'])
@login_required
def booking():
    if current_user.role != "student":
        flash("Only students can book tutors.", "danger")
        return redirect(url_for('home'))

    tutors = User.query.filter_by(role="tutor", status="approved").all()
    today = datetime.now().date()
    calendar_data = []

    # Generate calendar data for the next 7 days
    for i in range(7):
        date = today + timedelta(days=i)
        day_data = {"date": date.strftime("%Y-%m-%d"), "day_name": date.strftime("%A"), "slots": []}

        for time in timeslots:
            slot = {"time": time, "status": "available", "tutor": None}

            # Check if the slot is already booked
            existing_booking = Booking.query.filter_by(date=date, time=time).first()
            if existing_booking:
                slot["status"] = existing_booking.status
                slot["tutor"] = existing_booking.tutor.name

            # Check if the tutor has any bookings at this time
            for tutor in tutors:
                if not any(b for b in tutor.tutor_bookings if b.date == date and b.time == time):
                    slot["status"] = "available"
                else:
                    slot["status"] = "unavailable"
                    slot["tutor"] = tutor.name

            day_data["slots"].append(slot)
        calendar_data.append(day_data)

    if request.method == 'POST':
        selected_date = request.form.get('date')
        selected_time = request.form.get('time')
        tutor_id = request.form.get('tutor')

        tutor = User.query.get(tutor_id)

        if not selected_date or not selected_time or not tutor:
            flash("Please select a valid date, time, and tutor.", "danger")
            return redirect(url_for('booking'))

        # Check if already booked
        existing_booking = Booking.query.filter_by(user_id=current_user.id, date=selected_date, time=selected_time).first()
        if existing_booking:
            flash("You already have a booking at this time.", "warning")
            return redirect(url_for('booking'))

        # Create booking
        new_booking = Booking(user_id=current_user.id, tutor_id=tutor.id, date=selected_date, time=selected_time, status="pending")
        db.session.add(new_booking)
        db.session.commit()

        flash("Booking submitted! Waiting for tutor approval.", "info")
        return redirect(url_for('calendar'))

    return render_template('booking.html', calendar_data=calendar_data, tutors=tutors, timeslots=timeslots)


# Calendar View
@app.route('/calendar')
@login_required
def calendar():
    if current_user.role != "student":
        flash("Only students can access the calendar.", "danger")
        return redirect(url_for('home'))

    today = datetime.now().date()
    calendar_data = []

    for i in range(7):
        date = today + timedelta(days=i)
        day_data = {"date": date.strftime("%Y-%m-%d"), "day_name": date.strftime("%A"), "slots": []}

        for time in timeslots:
            slot = {"time": time, "status": "available", "tutor": None, "meeting_id": None}

            booking = Booking.query.filter_by(user_id=current_user.id, date=date, time=time).first()
            if booking:
                slot["status"] = booking.status
                slot["tutor"] = booking.tutor.name
                slot["meeting_id"] = booking.meeting_id if booking.status == "approved" else None

            day_data["slots"].append(slot)

        calendar_data.append(day_data)

    return render_template('calendar.html', calendar_data=calendar_data, timeslots=timeslots)

# Tutor Dashboard
@app.route('/tutor_dashboard')
@login_required
def tutor_dashboard():
    if current_user.role != "tutor":
        flash("Only tutors can access this page.", "danger")
        return redirect(url_for('home'))

    tutor_bookings = Booking.query.filter_by(tutor_id=current_user.id, status="pending").all()
    return render_template('tutor_dashboard.html', bookings=tutor_bookings)

# Approve or Decline Booking
@app.route('/tutor_action/<int:booking_id>/<string:action>', methods=['POST'])
@login_required
def tutor_action(booking_id, action):
    if current_user.role != "tutor":
        return jsonify({"message": "Unauthorized"}), 401

    booking = Booking.query.get(booking_id)
    if not booking or booking.tutor_id != current_user.id:
        return jsonify({"message": "Booking not found"}), 404

    if action == "approve":
        booking.status = "approved"
        booking.meeting_id = generate_meeting_id()
        notifications.append({
            "user": booking.student.email,
            "message": f"Your booking with {current_user.name} on {booking.date} at {booking.time} has been approved. Meeting ID: {booking.meeting_id}."
        })
        db.session.commit()
        flash(f"Booking approved! Meeting ID: {booking.meeting_id}", "success")

    elif action == "decline":
        booking.status = "declined"
        notifications.append({
            "user": booking.student.email,
            "message": f"Your booking with {current_user.name} on {booking.date} at {booking.time} has been declined."
        })
        db.session.commit()
        flash("Booking declined.", "danger")

    flash(f'Booking for {booking.student.name} on {booking.date} at {booking.time} has been {action}.', 'success')
    return redirect(url_for('tutor_dashboard'))

@app.route('/notifications')
@login_required  # Ensures only logged-in users can access
def notifications_page():
    
    user_notifications = [n for n in notifications if n["user"] == current_user.email]
    
    if not user_notifications:
        flash('No notifications available.', 'info')

    return render_template('notifications.html', notifications=user_notifications)



@app.route('/logout')
@login_required  # Ensures only logged-in users can access
def logout():
    logout_user()  
    flash("You have been logged out!", "info")
    return redirect(url_for('home'))

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        flash("Unauthorized access!", "danger")
        return redirect(url_for('home'))

    pending_tutors = User.query.filter_by(role="tutor", status="pending").all()
    all_tutors = User.query.filter_by(role="tutor").all()
    students = User.query.filter_by(role="student").all()

    return render_template(
        'admin_dashboard.html',
        tutors=pending_tutors,  
        total_tutors=len(all_tutors), 
        approved_tutors=sum(1 for tutor in all_tutors if tutor.status == "approved"),
        pending_tutors=len(pending_tutors),  
        declined_tutors=sum(1 for tutor in all_tutors if tutor.status == "declined"),
        total_students=len(students)
    )

@app.route('/approve_tutor/<int:user_id>')
@login_required
def approve_tutor(user_id):
    if current_user.role != "admin":
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
            flash(f"Tutor {tutor.name} does not meet the grade requirement.", "danger")

    return redirect(url_for('admin_dashboard'))

@app.route('/decline_tutor/<int:user_id>')
@login_required
def decline_tutor(user_id):
    if current_user.role != "admin":
        flash("Unauthorized action!", "danger")
        return redirect(url_for('home'))

    tutor = User.query.get(user_id)
    if tutor and tutor.role == "tutor":
        tutor.status = "declined"
        db.session.commit()
        send_email(tutor.email, "Tutor Application Declined", 
                   "Your tutor application has been declined due to an insufficient average grade.")
        flash(f"Tutor {tutor.name} declined!", "danger")

    return redirect(url_for('admin_dashboard'))


@app.route('/uploads/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)

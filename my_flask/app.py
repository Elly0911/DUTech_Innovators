from flask import Flask, request, render_template, flash, session, redirect, url_for, jsonify
from datetime import datetime, timedelta
import random
import string

app = Flask(__name__)
app.secret_key = "your_secret_key"  # For flashing messages and sessions

@app.route('/')
def home():
    if 'username' in session:
        # If the user is logged in, redirect them to the booking page
        return redirect(url_for('booking'))
    elif 'tutor' in session:
        # If a tutor is logged in, redirect them to the tutor dashboard
        return redirect(url_for('tutor_dashboard'))
    else:
        # If no one is logged in, show a welcome message with links to register and login
        return render_template('home.html')

        # Generate time slots for the calendar (8 AM - 8 PM)
timeslots = [f"{hour:02d}:00" for hour in range(8, 20)]  # 8 AM to 8 PM

# Dummy data: Users, Tutors, and Bookings
users = {}  # Dictionary to store registered users (username -> password)
tutors = [
    {"id": 1, "name": "Tutor1", "student_number": "111111", "availability": True, "bookings": []},
    {"id": 2, "name": "Tutor2", "student_number": "222222", "availability": True, "bookings": []},
    {"id": 3, "name": "Tutor3", "student_number": "333333", "availability": True, "bookings": []},
    {"id": 4, "name": "Tutor4", "student_number": "444444", "availability": True, "bookings": []}
]

bookings = []  # List of all bookings
notifications = []  # List of notifications for students

# Function to generate a random meeting ID
def generate_meeting_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

# Route for user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users:
            flash('Username already exists!', 'error')
        else:
            users[username] = password
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if the user is logging in as a student
        if username in users and users[username] == password:
            session['username'] = username  # Store student username in session

            # Check if the student has any bookings
            student_bookings = [b for b in bookings if b["user"] == username]
            if student_bookings:
                # Redirect to calendar if the student has already booked
                return redirect(url_for('calendar'))
            else:
                # Redirect to booking if the student hasn't booked yet
                return redirect(url_for('booking'))

        # Check if the user is logging in as a tutor
        tutor_info = next((t for t in tutors if t["name"] == username), None)
        if tutor_info and tutor_info["availability"]:
            session['tutor'] = username  # Store tutor name in session
            flash(f'Welcome, Tutor {username}!', 'success')
            return redirect(url_for('tutor_dashboard'))  # Redirect tutors to dashboard

        # Invalid credentials
        flash('Invalid credentials!', 'error')
        return redirect(url_for('login'))

    return render_template('login.html')

# Route for the booking page
@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if 'username' not in session:
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('login'))

    today = datetime.now().date()
    calendar_data = []

    # Generate calendar data for the next 7 days
    for i in range(7):
        date = today + timedelta(days=i)
        day_data = {
            "date": date.strftime("%Y-%m-%d"),
            "day_name": date.strftime("%A"),
            "slots": []
        }

        for time in timeslots:
            slot = {
                "time": time,
                "status": "available",
                "tutor": None
            }

            # Check if the day is a weekend
            if date.weekday() >= 5:  # Saturday (5) or Sunday (6)
                slot["status"] = "unavailable"
            else:
                # Check if the slot is already booked by the user
                for booking in bookings:
                    if booking["user"] == session['username'] and \
                       booking["date"] == date.strftime("%Y-%m-%d") and \
                       booking["time"] == time:
                        slot["status"] = "booked"
                        slot["tutor"] = booking["tutor"]

            day_data["slots"].append(slot)

        calendar_data.append(day_data)

    if request.method == 'POST':
        selected_date = request.form.get('date')
        selected_time = request.form.get('time')
        selected_tutor = request.form.get('tutor')

        # Validate inputs
        if not selected_date or not selected_time or not selected_tutor:
            flash('Please select a valid date, time, and tutor.', 'error')
            return redirect(url_for('booking'))

        # Check if tutor is available
        tutor_info = next((t for t in tutors if t["name"] == selected_tutor), None)
        if not tutor_info or not tutor_info["availability"]:
            flash(f'The selected tutor ({selected_tutor}) is unavailable.', 'error')
            return redirect(url_for('booking'))

        # Add booking to the list (pending approval)
        bookings.append({
            "user": session['username'],
            "tutor": selected_tutor,
            "time": selected_time,
            "date": selected_date,
            "status": "pending",  # Booking is pending approval
            "meeting_id": None
        })

        # Notify the tutor
        tutor_info["bookings"].append({
            "user": session['username'],
            "time": selected_time,
            "date": selected_date,
            "status": "pending"
        })

        flash('Booking submitted successfully! Awaiting tutor approval.', 'success')
        return redirect(url_for('calendar'))

    return render_template('booking.html', calendar_data=calendar_data, tutors=tutors, timeslots=timeslots)

# Route for the calendar page
@app.route('/calendar')
def calendar():
    if 'username' not in session:
        flash('Please log in to view your calendar.', 'error')
        return redirect(url_for('login'))

    today = datetime.now().date()
    calendar_data = []

    # Generate calendar data for the next 7 days
    for i in range(7):
        date = today + timedelta(days=i)
        day_data = {
            "date": date.strftime("%Y-%m-%d"),
            "day_name": date.strftime("%A"),
            "slots": []
        }

        for time in timeslots:
            slot = {
                "time": time,
                "status": "available",  # Default status
                "tutor": None,
                "meeting_id": None
            }

            # Check if the day is a weekend
            if date.weekday() >= 5:  # Saturday (5) or Sunday (6)
                slot["status"] = "unavailable"
            else:
                # Check if the slot is booked by the user
                for booking in bookings:
                    if booking["user"] == session['username'] and \
                       booking["date"] == date.strftime("%Y-%m-%d") and \
                       booking["time"] == time:
                        slot["status"] = booking["status"]  # Use the booking's status
                        slot["tutor"] = booking["tutor"]
                        slot["meeting_id"] = booking["meeting_id"]

            day_data["slots"].append(slot)

        calendar_data.append(day_data)

         # Debugging Tip: Print the calendar_data structure
    print("Calendar Data:", calendar_data)

    return render_template('calendar.html', calendar_data=calendar_data, timeslots=timeslots)

# Route for tutor dashboard
@app.route('/tutor_dashboard')
def tutor_dashboard():
    if 'tutor' not in session:
        flash('Please log in as a tutor to access this page.', 'error')
        return redirect(url_for('login'))

    # Get tutor bookings
    tutor_info = next((t for t in tutors if t["name"] == session['tutor']), None)
    if not tutor_info:
        flash('Tutor not found!', 'error')
        return redirect(url_for('login'))

    # Filter bookings for the logged-in tutor
    tutor_bookings = [b for b in bookings if b["tutor"] == session['tutor']]

    return render_template('tutor_dashboard.html', bookings=tutor_bookings)

# Route for tutor to approve/decline bookings
@app.route('/tutor_action/<string:user>/<string:date>/<string:time>/<string:action>', methods=['POST'])
def tutor_action(user, date, time, action):
    if 'tutor' not in session:
        return jsonify({"message": "Unauthorized"}), 401

    # Find the booking
    booking = next((b for b in bookings if b["user"] == user and b["date"] == date and b["time"] == time), None)
    if not booking:
        return jsonify({"message": "Booking not found"}), 404

    # Perform action
    if action == "approve":
        booking["status"] = "approved"
        booking["meeting_id"] = generate_meeting_id()
        notifications.append({
            "user": user,
            "message": f"Your booking with {session['tutor']} on {date} at {time} has been approved. Meeting ID: {booking['meeting_id']}."
        })
    elif action == "decline":
        booking["status"] = "declined"
        notifications.append({
            "user": user,
            "message": f"Your booking with {session['tutor']} on {date} at {time} has been declined."
        })

    # Notify the student
    flash(f'Booking for {user} on {date} at {time} has been {action}.', 'success')
    return redirect(url_for('tutor_dashboard'))

# Route for student notifications
@app.route('/notifications')
def notifications_page():
    if 'username' not in session:
        flash('Please log in to view your notifications.', 'error')
        return redirect(url_for('login'))

    # Filter notifications for the logged-in user
    user_notifications = [n for n in notifications if n["user"] == session['username']]
    return render_template('notifications.html', notifications=user_notifications)

# Route to log out
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('tutor', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
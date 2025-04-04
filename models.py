from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    average_grade = db.Column(db.Float, nullable=True)
    department = db.Column(db.String(10), nullable=False)
    result_document = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(10), nullable=True)

    # Relationships for bookings (student and tutor)
    bookings = db.relationship('Booking', foreign_keys='Booking.user_id', backref='student', lazy=True)
    tutor_bookings = db.relationship('Booking', foreign_keys='Booking.tutor_id', backref='tutor', lazy=True)
    def is_admin(self):
        return self.role == 'admin'
    
    def __repr__(self):
        return f"User('{self.id}', '{self.name}', '{self.role}')"

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  
    tutor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  
    date = db.Column(db.String(20), nullable=False)  
    time = db.Column(db.String(10), nullable=False)  
    status = db.Column(db.String(20), default="pending")  
    meeting_id = db.Column(db.String(20), nullable=True)
    special_request = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return f"Booking('{self.id}', Student: '{self.user_id}', Tutor: '{self.tutor_id}', Status: '{self.status}')"

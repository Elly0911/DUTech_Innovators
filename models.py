from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)
    average_grade = db.Column(db.Float, nullable=True)
    department = db.Column(db.String(10), nullable=False)
    result_document = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"User('{self.id}', '{self.name}', '{self.role}')"
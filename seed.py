from app import app, db
from models import User
from werkzeug.security import generate_password_hash

def create_default_admin():
    with app.app_context():
        if not User.query.filter_by(role='admin').first():  # Check if an admin already exists
            admin = User(
                name="System Admin",
                email="admin@tutoring.com",
                password=generate_password_hash("Admin@1234"),
                role='admin',
                department='ADMIN',
                status='active'
            )
            db.session.add(admin)
            db.session.commit()
            print("Default admin account created successfully!")
        else:
            print("Admin account already exists.")

if __name__ == "__main__":
    create_default_admin()
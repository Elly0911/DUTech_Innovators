import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = 'your_secret_key'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
     

    MAIL_SERVER = 'smtp.office365.com' 
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False  
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")  # Fetch email from .env
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")  # Fetch password from .env
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_USERNAME")  # Use the same email for sending




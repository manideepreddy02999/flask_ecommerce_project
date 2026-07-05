
import os
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    PERMANENT_SESSION_LIFETIME = os.getenv('PERMANENT_SESSION_LIFETIME')
    DB_HOST = os.getenv('DB_HOST')
    DB_NAME = os.getenv('DB_NAME')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')

    MAIL_HOST = os.getenv('MAIL_HOST')
    MAIL_PORT = os.getenv('MAIL_PORT')
    MAIL_USE_TLS = True
    MAIL_USER = os.getenv('MAIL_USER')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')

    MAIL_SERVER = os.getenv('MAIL_HOST')
    MAIL_USERNAME = os.getenv('MAIL_USER')

    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER')  
    PROFILE_IMG_FOLDER = os.getenv('PROFILE_IMG_FOLDER')

    RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
    RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')
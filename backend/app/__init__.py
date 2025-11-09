from flask import Flask
from flask_cors import CORS
app = Flask(__name__)

# Configure CORS to allow credentials (cookies) for session management
# When using supports_credentials=True, we need to explicitly allow origins
# Using resource specific CORS for better control
allowed_origins = []
allowed_origins.extend([
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8080",
    "https://3.150.122.114",
    "http://3.150.122.114"
])

CORS(app, 
     resources={
         r"/api/*": {
             "origins": allowed_origins,  # Allow all origins for API endpoints
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization", "X-CSRF-Token", "X-Requested-With"],
             "expose_headers": ["X-CSRF-Token"],
             "supports_credentials": True,
             "max_age": 3600
         }
     })
from flask_mail import Mail
from dotenv import load_dotenv
import os
from itsdangerous import URLSafeTimedSerializer

# Load .env file from specific path FIRST
dotenv_path = '/home/student3/email.env'
load_dotenv(dotenv_path)

# Update Flask config from environment variables
app.config.update(
    MAIL_SERVER=os.getenv('MAIL_SERVER'),
    MAIL_PORT=int(os.getenv('MAIL_PORT') or '587'),
    MAIL_USE_TLS=os.getenv('MAIL_USE_TLS') == 'True',
    MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
    SECRET_KEY=os.getenv('SECRET_KEY') or os.environ.get('SECRET_KEY') or 'AlphaThreeForty',
    BASE_URL=os.getenv('BASE_URL'),
    # Session configuration for security
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=os.getenv('FLASK_ENV') == 'production',
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=86400  # 24 hours
)

# Initialize Flask-Mail
mail = Mail(app)

from app import routes

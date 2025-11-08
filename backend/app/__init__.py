from flask import Flask
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
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
    BASE_URL=os.getenv('BASE_URL')
)

# Initialize Flask-Mail
mail = Mail(app)

from app import routes

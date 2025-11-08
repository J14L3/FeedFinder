# app/two_factor.py
import random, time
from flask_mail import Message
from flask import current_app, session
from app import mail

# Generate a 6-digit numeric code
def generate_2fa_code():
    return str(random.randint(100000, 999999))

# Send the code to user's email
def send_2fa_email(recipient_email, code):
    msg = Message(
        subject="Your 2FA Verification Code",
        recipients=[recipient_email],
        body=f"Your verification code is: {code}\n\nThis code will expire in 5 minutes.",
        sender=current_app.config['MAIL_USERNAME']
    )
    mail.send(msg)

# Create and send code, then store it in session
def initiate_2fa(email):
    code = generate_2fa_code()
    send_2fa_email(email, code)

    # Store code + timestamp in session
    session['2fa_code'] = code
    session['2fa_email'] = email
    session['2fa_timestamp'] = time.time()

# Verify code entered by user
def verify_2fa_code(submitted_code, expiration=300):
    stored_code = session.get('2fa_code')
    timestamp = session.get('2fa_timestamp')

    if not stored_code or not timestamp:
        return False, "No verification code found."

    if time.time() - timestamp > expiration:
        session.pop('2fa_code', None)
        return False, "Code expired."

    if submitted_code.strip() == stored_code:
        # Success — clean up session
        session.pop('2fa_code', None)
        session.pop('2fa_timestamp', None)
        session.pop('2fa_email', None)
        return True, "Code verified."

    return False, "Incorrect code."

"""
CSRF Protection Module
Implements CSRF token generation and validation.
"""

import secrets
import hashlib
from flask import session, request
from datetime import datetime, timedelta


def generate_csrf_token():
    """
    Generate a CSRF token and store it in the session.
    """
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_urlsafe(32)
        session['csrf_token_expiry'] = (datetime.utcnow() + timedelta(hours=24)).isoformat()
    return session['csrf_token']


def validate_csrf_token(token):
    """
    Validate a CSRF token.
    """
    if 'csrf_token' not in session:
        return False
    
    # Check if token expired
    expiry_str = session.get('csrf_token_expiry')
    if expiry_str:
        expiry = datetime.fromisoformat(expiry_str)
        if datetime.utcnow() > expiry:
            session.pop('csrf_token', None)
            session.pop('csrf_token_expiry', None)
            return False
    
    # Constant-time comparison to prevent timing attacks
    stored_token = session.get('csrf_token')
    if not stored_token or not token:
        return False
    
    return secrets.compare_digest(stored_token, token)


def require_csrf(f):
    """
    Decorator to require CSRF token validation for a route.
    """
    from functools import wraps
    from flask import jsonify
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip CSRF for GET requests
        if request.method == 'GET':
            return f(*args, **kwargs)
        
        # Get token from header or form data
        token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token') or request.json.get('csrf_token') if request.is_json else None
        
        if not token or not validate_csrf_token(token):
            return jsonify({
                'success': False,
                'message': 'Invalid or missing CSRF token',
                'error': 'CSRF_TOKEN_INVALID'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function


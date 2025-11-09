"""
Authentication Middleware
Provides decorators and middleware for protecting routes with session validation.
"""

from functools import wraps
from flask import request, jsonify, make_response
from app.session_manager import verify_session_token
import os


def get_token_from_request():
    """
    Extract token from request headers or cookies.
    Priority: Authorization header > Cookie
    """
    # Try Authorization header first (Bearer token)
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header[7:]  # Remove 'Bearer ' prefix
    
    # Try cookie
    token = request.cookies.get('access_token')
    if token:
        return token
    
    return None


def require_auth(f):
    """
    Decorator to require authentication for a route.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'Authentication required',
                'error': 'NO_TOKEN'
            }), 401
        
        is_valid, payload, error = verify_session_token(token)
        
        if not is_valid:
            return jsonify({
                'success': False,
                'message': 'Invalid or expired session',
                'error': error or 'INVALID_TOKEN'
            }), 401
        
        # Add user info to request context
        request.user_id = payload.get('user_id')
        request.username = payload.get('username')
        request.user_role = payload.get('user_role')
        request.session_id = payload.get('session_id')
        
        return f(*args, **kwargs)
    
    return decorated_function


def optional_auth(f):
    """
    Decorator that allows optional authentication.
    If token is present and valid, sets user info in request context.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()
        
        if token:
            is_valid, payload, error = verify_session_token(token)
            if is_valid:
                request.user_id = payload.get('user_id')
                request.username = payload.get('username')
                request.user_role = payload.get('user_role')
                request.session_id = payload.get('session_id')
            else:
                # Token invalid but route allows unauthenticated access
                request.user_id = None
                request.username = None
                request.user_role = None
                request.session_id = None
        else:
            request.user_id = None
            request.username = None
            request.user_role = None
            request.session_id = None
        
        return f(*args, **kwargs)
    
    return decorated_function


def set_auth_cookies(response, access_token, refresh_token):
    """
    Set secure authentication cookies in the response.
    Uses HttpOnly, Secure, and SameSite attributes for security.
    """
    
    # Set access token cookie (short-lived)
    response.set_cookie(
        'access_token',
        access_token,
        httponly=True,  # Prevents JavaScript access (XSS protection)
        secure=True,  # Only send over HTTPS in production
        samesite='Lax',  # CSRF protection
        max_age=3600,  # 1 hour
        path='/'
    )
    
    # Set refresh token cookie (longer-lived)
    response.set_cookie(
        'refresh_token',
        refresh_token,
        httponly=True,
        secure=True,
        samesite='Lax',
        max_age=604800,  # 7 days
        path='/'
    )
    
    return response


def clear_auth_cookies(response):
    """
    Clear authentication cookies from the response.
    """
    response.set_cookie('access_token', '', expires=0, path='/')
    response.set_cookie('refresh_token', '', expires=0, path='/')
    return response


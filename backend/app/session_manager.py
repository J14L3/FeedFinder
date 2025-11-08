"""
Session Management Module
Implements secure session token generation, validation, and management
with protection against session hijacking, replay attacks, and tampering.
"""

import jwt
import secrets
import hashlib
import time
from datetime import datetime, timedelta
from flask import request, jsonify
from app.db import get_db_connection, create_query_executor
import os


# Configuration
SECRET_KEY = os.getenv('SECRET_KEY') or 'AlphaThreeForty'
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRY = timedelta(hours=1)  # Short-lived access token
REFRESH_TOKEN_EXPIRY = timedelta(days=7)  # Longer-lived refresh token
SESSION_TOKEN_EXPIRY = timedelta(hours=24)  # Session token expiry


def generate_session_token(user_id, username, ip_address, user_agent):
    """
    Generate a secure session token (JWT) with user info and security metadata.
    Includes protection against tampering via signature.
    """
    # Create a fingerprint from IP and User-Agent to detect session hijacking
    fingerprint_data = f"{ip_address}:{user_agent}"
    fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
    
    # Generate a unique session ID
    session_id = secrets.token_urlsafe(32)
    
    # Current timestamp
    now = datetime.utcnow()
    iat = int(now.timestamp())
    exp = int((now + SESSION_TOKEN_EXPIRY).timestamp())
    
    payload = {
        'user_id': user_id,
        'username': username,
        'session_id': session_id,
        'fingerprint': fingerprint,
        'ip_address': ip_address,
        'iat': iat,  # Issued at
        'exp': exp,  # Expiration
        'type': 'access_token'
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token, session_id


def generate_refresh_token(user_id, session_id):
    """
    Generate a refresh token for obtaining new access tokens.
    """
    now = datetime.utcnow()
    iat = int(now.timestamp())
    exp = int((now + REFRESH_TOKEN_EXPIRY).timestamp())
    
    payload = {
        'user_id': user_id,
        'session_id': session_id,
        'iat': iat,
        'exp': exp,
        'type': 'refresh_token'
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def verify_session_token(token):
    """
    Verify and decode a session token.
    Returns (is_valid, payload, error_message)
    """
    try:
        # Verify token signature and expiration
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Check token type
        if payload.get('type') != 'access_token':
            return False, None, "Invalid token type"
        
        # Check if token is expired (jwt.decode already does this, but double-check)
        exp = payload.get('exp')
        if exp and datetime.utcnow().timestamp() > exp:
            return False, None, "Token expired"
        
        # Verify session exists in database
        session_id = payload.get('session_id')
        if not session_id or not is_session_valid(session_id, payload.get('user_id')):
            return False, None, "Session not found or invalid"
        
        # Verify fingerprint matches (protection against session hijacking)
        current_ip = request.remote_addr
        current_user_agent = request.headers.get('User-Agent', '')
        fingerprint_data = f"{current_ip}:{current_user_agent}"
        current_fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
        
        stored_fingerprint = payload.get('fingerprint')
        if stored_fingerprint and stored_fingerprint != current_fingerprint:
            # Fingerprint mismatch - potential session hijacking
            return False, None, "Session security check failed"
        
        return True, payload, None
        
    except jwt.ExpiredSignatureError:
        return False, None, "Token expired"
    except jwt.InvalidTokenError as e:
        return False, None, f"Invalid token: {str(e)}"
    except Exception as e:
        return False, None, f"Token verification error: {str(e)}"


def verify_refresh_token(token):
    """
    Verify a refresh token.
    Returns (is_valid, payload, error_message)
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        if payload.get('type') != 'refresh_token':
            return False, None, "Invalid token type"
        
        # Verify session exists
        session_id = payload.get('session_id')
        user_id = payload.get('user_id')
        if not session_id or not is_session_valid(session_id, user_id):
            return False, None, "Session not found or invalid"
        
        return True, payload, None
        
    except jwt.ExpiredSignatureError:
        return False, None, "Refresh token expired"
    except jwt.InvalidTokenError as e:
        return False, None, f"Invalid refresh token: {str(e)}"


def create_session(user_id, username, ip_address, user_agent):
    """
    Create a new session in the database and return tokens.
    """
    connection = get_db_connection()
    if not connection:
        return None, None, None
    
    try:
        # Create sessions table if it doesn't exist (do this first)
        create_sessions_table_if_not_exists()
        
        # Get a fresh connection for the insert
        connection = get_db_connection()
        if not connection:
            return None, None, None
        
        db_query = create_query_executor(connection, dictionary=True)
        
        # Generate tokens
        access_token, session_id = generate_session_token(user_id, username, ip_address, user_agent)
        refresh_token = generate_refresh_token(user_id, session_id)
        
        # Store session in database
        now = datetime.utcnow()
        expires_at = now + SESSION_TOKEN_EXPIRY
        
        insert_query = """
            INSERT INTO sessions (session_id, user_id, username, ip_address, user_agent, 
                                  fingerprint, created_at, expires_at, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        fingerprint_data = f"{ip_address}:{user_agent}"
        fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()[:16]
        
        db_query.execute(insert_query, (
            session_id,
            user_id,
            username,
            ip_address,
            user_agent,
            fingerprint,
            now,
            expires_at,
            1  # is_active
        ))
        connection.commit()
        
        db_query.close()
        connection.close()
        
        return access_token, refresh_token, session_id
        
    except Exception as e:
        print(f"Error creating session: {e}")
        import traceback
        traceback.print_exc()
        if connection:
            try:
                connection.rollback()
                connection.close()
            except:
                pass
        return None, None, None


def invalidate_session(session_id, user_id=None):
    """
    Invalidate a session by setting is_active to 0.
    """
    # Ensure sessions table exists
    create_sessions_table_if_not_exists()
    
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        db_query = create_query_executor(connection)
        
        if user_id:
            # Invalidate all sessions for a user (logout from all devices)
            update_query = "UPDATE sessions SET is_active = 0 WHERE user_id = %s"
            db_query.execute(update_query, (user_id,))
        else:
            # Invalidate specific session
            update_query = "UPDATE sessions SET is_active = 0 WHERE session_id = %s"
            db_query.execute(update_query, (session_id,))
        
        connection.commit()
        db_query.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"Error invalidating session: {e}")
        import traceback
        traceback.print_exc()
        if connection:
            try:
                connection.rollback()
                connection.close()
            except:
                pass
        return False


def is_session_valid(session_id, user_id):
    """
    Check if a session is valid (exists, active, and not expired).
    """
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        db_query = create_query_executor(connection, dictionary=True)
        
        query = """
            SELECT * FROM sessions 
            WHERE session_id = %s AND user_id = %s AND is_active = 1 AND expires_at > NOW()
        """
        db_query.execute(query, (session_id, user_id))
        session = db_query.fetchone()
        
        db_query.close()
        connection.close()
        
        return session is not None
        
    except Exception as e:
        print(f"Error checking session validity: {e}")
        if connection:
            connection.close()
        return False


def refresh_access_token(refresh_token):
    """
    Generate a new access token from a valid refresh token.
    """
    is_valid, payload, error = verify_refresh_token(refresh_token)
    if not is_valid:
        return None, None, error
    
    user_id = payload.get('user_id')
    session_id = payload.get('session_id')
    
    # Get user info from database
    connection = get_db_connection()
    if not connection:
        return None, None, "Database connection failed"
    
    try:
        db_query = create_query_executor(connection, dictionary=True)
        db_query.execute("SELECT user_name FROM user WHERE user_id = %s", (user_id,))
        user = db_query.fetchone()
        db_query.close()
        connection.close()
        
        if not user:
            return None, None, "User not found"
        
        # Get current request info
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        # Generate new access token
        access_token, _ = generate_session_token(user_id, user['user_name'], ip_address, user_agent)
        
        return access_token, None, None
        
    except Exception as e:
        print(f"Error refreshing token: {e}")
        if connection:
            connection.close()
        return None, None, str(e)



def create_sessions_table_if_not_exists():
    """
    Create the sessions table if it doesn't exist.
    """
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        db_query = create_query_executor(connection)
        
        create_table_query = """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id VARCHAR(255) PRIMARY KEY,
                user_id INT NOT NULL,
                username VARCHAR(50) NOT NULL,
                ip_address VARCHAR(45) NOT NULL,
                user_agent TEXT,
                fingerprint VARCHAR(64),
                created_at DATETIME NOT NULL,
                expires_at DATETIME NOT NULL,
                last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                is_active TINYINT(1) DEFAULT 1,
                INDEX idx_user_id (user_id),
                INDEX idx_session_id (session_id),
                INDEX idx_expires_at (expires_at),
                FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        
        db_query.execute(create_table_query)
        connection.commit()
        db_query.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"Note creating sessions table: {e}")
        if connection:
            try:
                connection.rollback()
                connection.close()
            except:
                pass
        return False


def cleanup_expired_sessions():
    """
    Clean up expired sessions from the database.
    Should be run periodically (e.g., via cron job or scheduled task).
    """
    connection = get_db_connection()
    if not connection:
        return
    
    try:
        db_query = create_query_executor(connection)
        delete_query = "DELETE FROM sessions WHERE expires_at < NOW() OR is_active = 0"
        db_query.execute(delete_query)
        connection.commit()
        db_query.close()
        connection.close()
        
    except Exception as e:
        print(f"Error cleaning up sessions: {e}")
        if connection:
            connection.rollback()
            connection.close()


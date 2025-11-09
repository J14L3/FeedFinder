from app import app
from flask import render_template, request, redirect, url_for, flash, session, jsonify, make_response
from app.hash import hash_password, verify_password
from app.db import get_db_connection, create_query_executor
from app.session_manager import create_session, invalidate_session, refresh_access_token, verify_refresh_token, verify_session_token, cleanup_expired_sessions
from app.auth_middleware import require_auth, optional_auth, set_auth_cookies, clear_auth_cookies, get_token_from_request
from app.csrf import generate_csrf_token, require_csrf
import re
import os
from itsdangerous import URLSafeTimedSerializer
from app.two_factor import initiate_2fa, verify_2fa_code


@app.route('/')
@app.route('/index')
def index():
    return "Hello, World!"

@app.route('/api/health', methods=['GET'])
def api_health():
    """Health check endpoint to verify API is accessible"""
    return jsonify({
        "status": "ok",
        "message": "API is running"
    }), 200

# The new route for the page
@app.route('/login', methods=['GET', 'POST'])
def login():
    result = None
    if request.method == 'POST':
        # Get the data from the form
        username = request.form.get('username_input')
        password = request.form.get('password_input')

        # Validate form input
        if not username or not password:
            flash("Please fill in both fields.", "danger")
            return render_template('login.html')

        # Validate format and length of inputs
        USERNAME_RE = re.compile(r'^[A-Za-z0-9_]{3,20}$')

        if not USERNAME_RE.match(username):
            flash("Username must be 3–20 characters (letters, numbers, underscores only).", "danger")
            return render_template('login.html')

        if len(username) > 50 or len(password) > 100:
            flash("Input too long.", "danger")
            return render_template('login.html')
        
        # Connect to database
        connection = get_db_connection()
        if connection is None:
            flash("Database connection failed!", "danger")
            return render_template('login.html')
        
        try:
            db_query = create_query_executor(connection, dictionary=True)
            db_query.execute("SELECT * FROM user WHERE user_name=%s", (username,))
            user = db_query.fetchone()

            if user is None:
                flash("Username not found.", "danger")
                return render_template('login.html')

            # Verify password hash
            if verify_password(user['password_hash'], password):
                # Successful login
                # flash(f"Welcome, {username}!", "success")
                # Optional: set session
                # session['user_id'] = user['id']
                # session['username'] = user['user_name']
                # return redirect(url_for('index'))

                # Step 1: Send 2FA code
                initiate_2fa(user['user_email'])
                session['pending_user'] = user['user_name']
                flash("A 2FA code has been sent to your email. Please enter it below.", "info")
                return redirect(url_for('verify_2fa'))

            else:
                flash("Incorrect password.", "danger")
                return render_template('login.html')

        except Exception as e:
            print(f"Database error: {e}")
            flash("An error occurred during login.", "danger")
            return render_template('login.html')

        finally:
            if db_query:
                db_query.close()
            if connection:
                connection.close()


    # Render the template and pass the result (if any)
    return render_template('login.html', result=result)

@app.route('/api/login', methods=['POST', 'OPTIONS'])
def api_login():
    """
    Login endpoint with session token creation.
    Creates secure session tokens and sets them in HttpOnly cookies.
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({
            "success": False,
            "message": "Username and password are required"
        }), 400

    # Validate username format
    USERNAME_RE = re.compile(r'^[A-Za-z0-9_]{3,20}$')
    if not USERNAME_RE.match(username):
        return jsonify({
            "success": False,
            "message": "Invalid username format"
        }), 400

    connection = get_db_connection()
    if not connection:
        return jsonify({
            "success": False,
            "message": "Database connection failed"
        }), 500

    try:
        db_query = create_query_executor(connection, dictionary=True)
        db_query.execute("SELECT * FROM user WHERE user_name=%s", (username,))
        user = db_query.fetchone()
        db_query.close()
        connection.close()

        if not user or not verify_password(user['password_hash'], password):
            return jsonify({
                "success": False,
                "message": "Invalid username or password"
            }), 401

        # Get client info for session security
        ip_address = request.remote_addr or request.headers.get('X-Forwarded-For', '0.0.0.0').split(',')[0] or '0.0.0.0'
        user_agent = request.headers.get('User-Agent', '')
        
        # Create session and generate tokens
        access_token, refresh_token, session_id = create_session(
            user['user_id'],
            user['user_name'],
            ip_address,
            user_agent
        )

        if not access_token:
            return jsonify({
                "success": False,
                "message": "Failed to create session"
            }), 500

        # Create response with tokens in cookies
        response = make_response(jsonify({
            "success": True,
            "message": f"Welcome {username}!",
            "user": {
                "id": user['user_id'],
                "username": user['user_name'],
                "email": user.get('user_email', '')
            }
        }))

        # Set secure cookies
        response = set_auth_cookies(response, access_token, refresh_token)

        return response, 200

    except Exception as e:
        print(f"Login error: {e}")
        if connection:
            connection.close()
        return jsonify({
            "success": False,
            "message": "An error occurred during login"
        }), 500

@app.route('/verify_2fa', methods=['GET', 'POST'])
def verify_2fa():
    if request.method == 'POST':
        code = request.form.get('code')
        if not code:
            flash("Please enter your verification code.", "danger")
            return render_template('verify_2fa.html')

        valid, message = verify_2fa_code(code)
        if valid:
            username = session.pop('pending_user', None)
            session['user'] = username
            flash(f"Welcome, {username}! You are now logged in.", "success")
            return redirect(url_for('index'))
        else:
            flash(message, "danger")
            return render_template('verify_2fa.html')

    return render_template('verify_2fa.html')


@app.route('/api/logout', methods=['POST', 'OPTIONS'])
def api_logout():
    """
    Logout endpoint that invalidates the current session.
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    # Check authentication
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
    
    session_id = payload.get('session_id')
    user_id = payload.get('user_id')
    
    try:
        # Invalidate session
        invalidate_session(session_id, user_id)
        
        # Create response and clear cookies
        response = make_response(jsonify({
            "success": True,
            "message": "Logged out successfully"
        }))
        
        response = clear_auth_cookies(response)
        
        return response, 200
        
    except Exception as e:
        print(f"Logout error: {e}")
        return jsonify({
            "success": False,
            "message": "An error occurred during logout"
        }), 500


@app.route('/api/refresh', methods=['POST'])
def api_refresh():
    """
    Refresh access token using refresh token.
    """
    refresh_token = request.cookies.get('refresh_token')
    
    if not refresh_token:
        return jsonify({
            "success": False,
            "message": "Refresh token not found",
            "error": "NO_REFRESH_TOKEN"
        }), 401
    
    access_token, _, error = refresh_access_token(refresh_token)
    
    if not access_token:
        response = make_response(jsonify({
            "success": False,
            "message": error or "Failed to refresh token",
            "error": "REFRESH_FAILED"
        }))
        response = clear_auth_cookies(response)
        return response, 401
    
    # Create response with new access token
    response = make_response(jsonify({
        "success": True,
        "message": "Token refreshed successfully"
    }))
    
    # Set new access token cookie (keep refresh token)
    is_production = os.getenv('FLASK_ENV') == 'production' or os.getenv('ENVIRONMENT') == 'production'
    response.set_cookie(
        'access_token',
        access_token,
        httponly=True,
        secure=is_production,
        samesite='Lax',
        max_age=3600,
        path='/'
    )
    
    return response, 200


@app.route('/api/csrf-token', methods=['GET', 'OPTIONS'])
def api_csrf_token():
    """
    Get CSRF token for forms.
    This endpoint does not require authentication.
    """
    try:
        token = generate_csrf_token()
        return jsonify({
            "success": True,
            "csrf_token": token
        }), 200
    except Exception as e:
        print(f"Error generating CSRF token: {e}")
        return jsonify({
            "success": False,
            "message": "Failed to generate CSRF token"
        }), 500


@app.route('/api/verify-session', methods=['GET', 'OPTIONS'])
def api_verify_session():
    """
    Verify if current session is valid.
    Returns user information.
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    # Check authentication
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
    
    return jsonify({
        "success": True,
        "user": {
            "id": payload.get('user_id'),
            "username": payload.get('username')
        }
    }), 200


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Check if passwords match
        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return render_template('register.html')
        

        # Validate format and length of inputs
        USERNAME_RE = re.compile(r'^[A-Za-z0-9_]{3,20}$')

        if not USERNAME_RE.match(username):
            flash("Username must be 3–20 characters (letters, numbers, underscores only).", "danger")
            return render_template('register.html')

        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            flash("Invalid email format.", "danger")
            return render_template('register.html')
        
        if len(username) > 50 or len(email) > 100 or len(password) > 100:
            flash("Input too long.", "danger")
            return render_template('register.html')
        
        password_hash = hash_password(password)

        # Connect to DB
        connection = get_db_connection()
        if connection is None:
            flash("Database connection failed!", "danger")
            return render_template('register.html')

        try:
            db_query = create_query_executor(connection)

            # Check if username or email already exists
            db_query.execute("SELECT * FROM user WHERE user_name=%s OR user_email=%s", (username, email))
            existing_user = db_query.fetchone()

            if existing_user:
                flash("Username or email already exists!", "danger")
                return render_template('register.html')

            # Insert new user into database
            insert_query = "INSERT INTO user (user_name, user_email, password_hash) VALUES (%s, %s, %s)"
            db_query.execute(insert_query, (username, email, password_hash))
            connection.commit()
            flash("Account created successfully!", "success")
        
        except Exception as e:
            print(f"Database error: {e}")
            flash("An error occurred while creating the account.", "danger")
            return render_template('register.html')
        
        finally:
            # Always close db_query and connection
            if db_query:
                db_query.close()
            if connection:
                connection.close()

        flash("Account created successfully!", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/api/register', methods=['POST', 'OPTIONS'])
def api_register():
    """
    Register endpoint with automatic login after registration.
    Creates user account and session tokens.
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    data = request.get_json()

    # Extract data from JSON
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password')
    bio = data.get('bio', '')
    private = data.get('private', False)

    # Check for missing fields
    if not all([username, email, password, confirm_password]):
        return jsonify({
            "success": False,
            "message": "All required fields must be filled."
        }), 400

    # Check if passwords match
    if password != confirm_password:
        return jsonify({
            "success": False,
            "message": "Passwords do not match!"
        }), 400

    # Validate username and email format
    USERNAME_RE = re.compile(r'^[A-Za-z0-9_]{3,20}$')
    if not USERNAME_RE.match(username):
        return jsonify({
            "success": False,
            "message": "Invalid username format."
        }), 400

    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return jsonify({
            "success": False,
            "message": "Invalid email format."
        }), 400

    # Length checks
    if len(username) > 50 or len(email) > 100 or len(password) > 100:
        return jsonify({
            "success": False,
            "message": "Input too long."
        }), 400

    password_hash = hash_password(password)
    private_value = 1 if private else 0

    # Connect to DB
    connection = get_db_connection()
    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection failed."
        }), 500

    try:
        db_query = create_query_executor(connection, dictionary=True)

        # Check if username or email exists
        db_query.execute(
            "SELECT * FROM user WHERE user_name=%s OR user_email=%s",
            (username, email),
        )
        existing_user = db_query.fetchone()

        if existing_user:
            return jsonify({
                "success": False,
                "message": "Username or email already exists!"
            }), 400

        # Insert new user
        insert_query = """
            INSERT INTO user (user_name, user_email, password_hash, bio, is_private)
            VALUES (%s, %s, %s, %s, %s)
        """
        db_query.execute(insert_query, (username, email, password_hash, bio, private_value))
        connection.commit()

        # Get the newly created user
        user_id = db_query.lastrowid
        db_query.execute("SELECT * FROM user WHERE user_id=%s", (user_id,))
        new_user = db_query.fetchone()

        db_query.close()
        connection.close()

        # Automatically log in the user after registration
        ip_address = request.remote_addr or request.headers.get('X-Forwarded-For', '0.0.0.0').split(',')[0] or '0.0.0.0'
        user_agent = request.headers.get('User-Agent', '')
        
        access_token, refresh_token, session_id = create_session(
            new_user['user_id'],
            new_user['user_name'],
            ip_address,
            user_agent
        )

        if not access_token:
            return jsonify({
                "success": False,
                "message": "Account created but failed to create session. Please login."
            }), 500

        # Create response with tokens in cookies
        response = make_response(jsonify({
            "success": True,
            "message": "Account created successfully!",
            "user": {
                "id": new_user['user_id'],
                "username": new_user['user_name'],
                "email": new_user.get('user_email', '')
            }
        }))

        # Set secure cookies
        response = set_auth_cookies(response, access_token, refresh_token)

        return response, 201

    except Exception as e:
        print(f"Database error: {e}")
        if connection:
            connection.rollback()
            connection.close()
        return jsonify({
            "success": False,
            "message": "An error occurred during registration."
        }), 500

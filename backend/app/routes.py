from app import app
from flask import render_template, request, redirect, url_for, flash, session, jsonify, make_response, send_from_directory
from app.hash import hash_password, verify_password
from app.db import get_db_connection
from app.session_manager import create_session, invalidate_session, refresh_access_token, verify_refresh_token, verify_session_token, cleanup_expired_sessions
from app.auth_middleware import require_auth, optional_auth, set_auth_cookies, clear_auth_cookies, get_token_from_request
from app.csrf import generate_csrf_token, require_csrf
import re, os
from itsdangerous import URLSafeTimedSerializer
from app.two_factor import initiate_2fa, verify_2fa_code
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename 
import uuid
import logging


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
            flash("Username must be 20 characters (letters, numbers, underscores only).", "danger")
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
            db_query = connection.cursor(dictionary=True)
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
        db_query = connection.cursor(dictionary=True)
        db_query.execute("SELECT * FROM user WHERE user_name=%s", (username,))
        user = db_query.fetchone()
        db_query.close()
        connection.close()

        if not user or not verify_password(user['password_hash'], password):
            return jsonify({
                "success": False,
                "message": "Invalid username or password"
            }), 401

        # # ✅ Generate 2FA code
        # two_fa_code = str(random.randint(100000, 999999))

        # # Example: send by email
        # send_2fa_email(user['user_email'], two_fa_code)

        # # ✅ Store temporary 2FA session info
        # session_token = secrets.token_urlsafe(32)
        # pending_2fa_sessions[session_token] = {
        #     "username": username,
        #     "user_id": user["user_id"],
        #     "user_role": user["user_role"],
        #     "code": two_fa_code,
        #     "expires": datetime.utcnow() + timedelta(minutes=5)
        # }

        # return jsonify({
        #     "success": True,
        #     "message": f"2FA code sent to {user['user_email']}.",
        #     "requires_2fa": True,
        #     "session_token": session_token  # returned to frontend to match later
        # }), 200

        # Get client info for session security
        ip_address = request.remote_addr or request.headers.get('X-Forwarded-For', '0.0.0.0').split(',')[0] or '0.0.0.0'
        user_agent = request.headers.get('User-Agent', '')
        
        
        # Create session and generate tokens
        access_token, refresh_token, session_id = create_session(
            user['user_id'],
            user['user_name'],
            user['user_role'],
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
                "email": user.get('user_email', ''),
                "role": user['user_role']
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

# @app.route('/api/verify-2fa', methods=['POST'])
# def verify_2fa():
#     data = request.get_json()
#     session_token = data.get('session_token')
#     code = data.get('code')

#     info = pending_2fa_sessions.get(session_token)
#     if not info:
#         return jsonify({"success": False, "message": "Session expired or invalid"}), 400

#     if datetime.utcnow() > info["expires"]:
#         del pending_2fa_sessions[session_token]
#         return jsonify({"success": False, "message": "2FA code expired"}), 400

#     if code != info["code"]:
#         return jsonify({"success": False, "message": "Incorrect 2FA code"}), 401

#     # ✅ Create full session now
#     ip_address = request.remote_addr or request.headers.get('X-Forwarded-For', '0.0.0.0')
#     user_agent = request.headers.get('User-Agent', '')

#     access_token, refresh_token, session_id = create_session(
#         info["user_id"], info["username"], info["user_role"], ip_address, user_agent
#     )

#     del pending_2fa_sessions[session_token]

#     response = make_response(jsonify({
#         "success": True,
#         "message": f"Welcome {info['username']}!",
#         "user": {
#             "id": info["user_id"],
#             "username": info["username"],
#             "role": info["user_role"]
#         }
#     }))

#     response = set_auth_cookies(response, access_token, refresh_token)
#     return response, 200

# @app.route('/verify_2fa', methods=['GET', 'POST'])
# def verify_2fa():
#     if request.method == 'POST':
#         code = request.form.get('code')
#         if not code:
#             flash("Please enter your verification code.", "danger")
#             return render_template('verify_2fa.html')

#         valid, message = verify_2fa_code(code)
#         if valid:
#             username = session.pop('pending_user', None)
#             session['user'] = username
#             flash(f"Welcome, {username}! You are now logged in.", "success")
#             return redirect(url_for('index'))
#         else:
#             flash(message, "danger")
#             return render_template('verify_2fa.html')

#     return render_template('verify_2fa.html')


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
    response.set_cookie(
        'access_token',
        access_token,
        httponly=True,
        secure=True,
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
            "username": payload.get('username'),
            "role": payload.get('user_role')
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
        
        # Validate password length
        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return render_template('register.html')

        # Validate format and length of inputs
        USERNAME_RE = re.compile(r'^[A-Za-z0-9_]{3,20}$')

        if not USERNAME_RE.match(username):
            flash("Username must be 20 characters (letters, numbers, underscores only).", "danger")
            return render_template('register.html')

        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            flash("Invalid email format.", "danger")
            return render_template('register.html')
        
        if len(username) > 50 or len(email) > 255 or len(password) > 128:
            flash("Input too long.", "danger")
            return render_template('register.html')
        
        password_hash = hash_password(password)

        # Connect to DB
        connection = get_db_connection()
        if connection is None:
            flash("Database connection failed!", "danger")
            return render_template('register.html')

        try:
            db_query = connection.cursor()

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

    # Validate password length
    if len(password) < 8:
        return jsonify({
            "success": False,
            "message": "Password must be at least 8 characters long."
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
    if len(username) > 50 or len(email) > 255 or len(password) > 128:
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
        db_query = connection.cursor(dictionary=True)

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
            INSERT INTO user (user_name, user_email, password_hash, bio, is_private, user_role)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        db_query.execute(insert_query, (username, email, password_hash, bio, private_value, 'normie'))
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
            new_user['user_role'],
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
                "email": new_user.get('user_email', ''),
                "role": new_user['user_role']
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
    
# --- Profile Management ---
# can take from session value also
@app.route("/api/profile/<int:user_id>", methods=["GET"])
def get_profile(user_id):

    # Connect to DB
    connection = get_db_connection()
    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection failed."
        }), 500

    db_query = connection.cursor(dictionary=True)
    # view profile query with user_id
    db_query.execute("SELECT user_id, user_name, user_email, bio, profile_picture, is_private FROM user WHERE user_id=%s", (user_id,))
    profile = db_query.fetchone(); db_query.close(); connection.close()

    if profile:
        return jsonify(profile)
    return jsonify({"error": "User not found"}), 404

@app.route("/api/profile/by-email", methods=["GET"])
def get_profile_by_email():
    email = (request.args.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "missing email"}), 400

    # Connect to DB
    connection = get_db_connection()
    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection failed."
        }), 500

    try:
        db_query = connection.cursor(dictionary=True)
        db_query.execute(
            "SELECT user_id, user_name, user_email, bio, profile_picture, is_private "
            "FROM `user` WHERE LOWER(user_email)=%s",
            (email,)
        )
        profile = db_query.fetchone()
    finally:
        db_query.close(); connection.close()

    if profile:
        return jsonify(profile)
    return jsonify({"error": "User not found"}), 404

@app.route("/api/profile/<int:user_id>/stats", methods=["GET"])
@optional_auth
def get_profile_stats(user_id):
    """
    Get profile statistics for a user.
    Returns post count, likes, comments, ratings, followers, following, etc.
    """
    # Connect to DB
    connection = get_db_connection()
    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection failed."
        }), 500
    
    try:
        db_query = connection.cursor(dictionary=True)
        
        # Get post count
        db_query.execute("SELECT COUNT(*) as count FROM post WHERE user_id = %s", (user_id,))
        post_count = db_query.fetchone()['count'] or 0
        
        # Get total likes (sum of all likes on user's posts)
        db_query.execute("""
            SELECT COUNT(*) as count 
            FROM post_like pl
            JOIN post p ON pl.post_id = p.post_id
            WHERE p.user_id = %s
        """, (user_id,))
        total_likes = db_query.fetchone()['count'] or 0
        
        # Get total comments
        db_query.execute("""
            SELECT COUNT(*) as count 
            FROM comment c
            JOIN post p ON c.post_id = p.post_id
            WHERE p.user_id = %s
        """, (user_id,))
        total_comments = db_query.fetchone()['count'] or 0
        
        # Get rating stats (convert from 1-10 scale to 1-5 scale)
        db_query.execute("""
            SELECT 
                COUNT(*) as count,
                AVG(rating_value) as average
            FROM rating
            WHERE creator_email = (SELECT user_email FROM user WHERE user_id = %s)
        """, (user_id,))
        rating_result = db_query.fetchone()
        total_ratings = rating_result['count'] or 0
        avg_rating = (float(rating_result['average']) / 2.0) if rating_result['average'] else 0
        avg_rating = round(avg_rating, 1) if avg_rating > 0 else 0
        
        # Get followers count (users who have this user as a friend)
        db_query.execute("""
            SELECT COUNT(*) as count 
            FROM friends 
            WHERE friend_user_id = %s
        """, (user_id,))
        followers = db_query.fetchone()['count'] or 0
        
        # Get following count (users this user has as friends)
        db_query.execute("""
            SELECT COUNT(*) as count 
            FROM friends 
            WHERE user_id = %s
        """, (user_id,))
        following = db_query.fetchone()['count'] or 0
        
        stats = {
            "totalPosts": post_count,
            "totalLikes": total_likes,
            "totalComments": total_comments,
            "totalRatings": total_ratings,
            "averageRating": avg_rating,
            "followers": followers,
            "following": following,
            "totalDonations": 0,  # Placeholder - implement if you have donations table
            "monthlyDonations": 0,  # Placeholder
            "topDonation": 0  # Placeholder
        }
        
        return jsonify({
            "success": True,
            "stats": stats
        }), 200
        
    except Exception as e:
        print(f"Error fetching profile stats: {e}")
        return jsonify({
            "success": False,
            "message": "Error fetching profile statistics"
        }), 500
    finally:
        db_query.close()
        connection.close()

@app.route("/api/profile/update", methods=["PUT", "OPTIONS"])
@require_auth
def update_profile():
    """
    Update authenticated user's profile.
    Uses user_id from session token for security.
    Only updates fields that are provided.
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    # Get user_id from authenticated session (secure - cannot be tampered with)
    user_id = request.user_id
    
    if not user_id:
        return jsonify({
            "success": False,
            "message": "Authentication required"
        }), 401
    
    data = request.get_json()
    if not data:
        return jsonify({
            "success": False,
            "message": "Invalid request data"
        }), 400
    
    # Extract and validate email
    email = data.get("user_email")
    if email is not None:
        email = email.strip().lower()
        # Validate email format
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            return jsonify({
                "success": False,
                "message": "Invalid email format"
            }), 400
        
        # Validate email length
        if len(email) > 100:
            return jsonify({
                "success": False,
                "message": "Email is too long (max 100 characters)"
            }), 400
    
    # Extract and validate bio
    bio = data.get("bio")
    if bio is not None:
        bio = bio.strip()
        # Validate bio length
        if len(bio) > 500:
            return jsonify({
                "success": False,
                "message": "Bio is too long (max 500 characters)"
            }), 400
    
    # Extract and validate profile picture
    profile_picture = data.get("profile_picture")
    if profile_picture is not None:
        profile_picture = profile_picture.strip()
        # If empty string, set to default avatar
        if not profile_picture:
            profile_picture = 'https://api.dicebear.com/7.x/avataaars/svg?seed=User'
        # Validate profile picture is a URL
        elif not (profile_picture.startswith('http://') or profile_picture.startswith('https://')):
            return jsonify({
                "success": False,
                "message": "Profile picture must be a valid URL"
            }), 400
        # Validate URL length
        if len(profile_picture) > 500:
            return jsonify({
                "success": False,
                "message": "Profile picture URL is too long"
            }), 400
    
    # Connect to DB
    connection = get_db_connection()
    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection failed"
        }), 500
    
    try:
        db_query = connection.cursor(dictionary=True)
        
        # Check if email is being changed and if it's already taken
        if email is not None:
            db_query.execute(
                "SELECT user_id FROM user WHERE user_email=%s AND user_id != %s",
                (email, user_id)
            )
            existing_user = db_query.fetchone()
            if existing_user:
                return jsonify({
                    "success": False,
                    "message": "Email is already in use"
                }), 400
        
        # Build dynamic UPDATE query with only provided fields
        update_fields = []
        update_values = []
        
        if email is not None:
            update_fields.append("user_email = %s")
            update_values.append(email)
        
        if bio is not None:
            update_fields.append("bio = %s")
            update_values.append(bio)
        
        if profile_picture is not None:
            update_fields.append("profile_picture = %s")
            update_values.append(profile_picture)
        
        # If no fields to update, return error
        if not update_fields:
            return jsonify({
                "success": False,
                "message": "No fields to update"
            }), 400
        
        # Add user_id for WHERE clause
        update_values.append(user_id)
        
        # Execute update with prepared statement
        update_query = f"UPDATE user SET {', '.join(update_fields)} WHERE user_id = %s"
        db_query.execute(update_query, tuple(update_values))
        connection.commit()
        
        # Verify update was successful
        if db_query.rowcount == 0:
            return jsonify({
                "success": False,
                "message": "User not found or no changes made"
            }), 404
        
        # Fetch updated profile
        db_query.execute(
            "SELECT user_id, user_name, user_email, bio, profile_picture, is_private, created_at FROM user WHERE user_id=%s",
            (user_id,)
        )
        updated_profile = db_query.fetchone()
        
        if updated_profile and updated_profile.get('created_at'):
            updated_profile['created_at'] = updated_profile['created_at'].isoformat()
        
        db_query.close()
        connection.close()
        
        return jsonify({
            "success": True,
            "message": "Profile updated successfully",
            "profile": updated_profile
        }), 200
        
    except Exception as e:
        print(f"Error updating profile: {e}")
        if connection:
            connection.rollback()
            connection.close()
        return jsonify({
            "success": False,
            "message": "An error occurred while updating profile"
        }), 500

# --- Post Management ---
@app.route("/api/posts", methods=["POST"])
def create_post():
    data = request.get_json()
    user_id, text, media, privacy, media_type = data.get("user_id"), data.get("content_text"), data.get("media_url"), data.get("privacy"), data.get("media_type")

    # get media type
    if not media_type:
        ext = os.path.splitext(media)[1].lower().lstrip('.')
        if ext in ('mp4','mov','webm'):
            media_type = 'video'
        else:
            media_type = 'image'

    # Connect to DB
    connection = get_db_connection()
    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection failed."
        }), 500
    
    db_query = connection.cursor(dictionary=True)
    # create post query
    db_query.execute("INSERT INTO post (user_id, content_text, media_url, privacy, media_type) VALUES (%s,%s,%s,%s,%s)", (user_id, text, media, privacy, media_type))
    connection.commit(); db_query.close(); connection.close()
    return jsonify({"message": "Post created successfully."})

# media upload directory
UPLOAD_FOLDER = "/var/www/feedfinder/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "mp4", "mov", "webm"}
MAX_FILE_SIZE_MB = 20

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# --- upload media ---
@app.route("/api/upload", methods=["POST"])
def upload_media():
    try:
        # ensure upload directory exists
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

        # check if file is in the request
        if "file" not in request.files:
            return jsonify({"success": False, "message": "No file part in request"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"success": False, "message": "No file selected"}), 400

        # validate file type
        if not allowed_file(file.filename):
            return jsonify({
                "success": False,
                "message": f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            }), 400

        # enforce file size limit
        file.seek(0, os.SEEK_END)
        size_mb = file.tell() / (1024 * 1024)
        file.seek(0)
        if size_mb > MAX_FILE_SIZE_MB:
            return jsonify({"success": False, "message": f"File too large ({size_mb:.2f}MB). Limit: {MAX_FILE_SIZE_MB}MB"}), 400

        # save file securely
        ext = file.filename.rsplit(".", 1)[1].lower()
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)

        try:
            file.save(save_path)

            ext = os.path.splitext(unique_name)[1].lower().lstrip('.')
            if ext in ('mp4','mov','webm'):
                media_type = 'video'
            else:
                media_type = 'image'

        except PermissionError as e:
            print(f"[UPLOAD ERROR] Permission denied: {e}")
            return jsonify({
                "success": False,
                "message": f"Permission denied when saving file to {save_path}. Check folder ownership and chmod."
            }), 500
        except FileNotFoundError as e:
            print(f"[UPLOAD ERROR] Folder not found: {e}")
            return jsonify({
                "success": False,
                "message": f"Upload folder not found: {app.config['UPLOAD_FOLDER']}"
            }), 500
        except Exception as e:
            print(f"[UPLOAD ERROR] Unexpected: {e}")
            return jsonify({
                "success": False,
                "message": f"Unexpected error while saving file: {str(e)}"
            }), 500

        # unique media URL
        media_url = f"/uploads/{unique_name}"  # relative for frontend

        return jsonify({
            "success": True,
            "message": "File uploaded successfully",
            "media_url": media_url
        }), 201

    except Exception as e:
        print(f"[UPLOAD ERROR] Outer catch: {e}")
        return jsonify({
            "success": False,
            "message": f"Unexpected server error: {str(e)}"
        }), 500


# lets frontend load media directly from the path below
@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# --- Post Visibility (public / friends / exclusive) ---
# IMPORTANT: This route must come BEFORE /api/posts/<int:user_id> to avoid route conflicts
# Flask matches routes in order, and more specific routes should come first
@app.route("/api/posts/user/<int:creator_id>", methods=["GET"])
@optional_auth
def api_view_creator_posts(creator_id):
    """
    Get posts by a specific creator.
    Respects privacy settings: public, friends, exclusive (if subscribed), or own posts.
    """
    # Get viewer ID from authentication (optional)
    viewer_id = getattr(request, 'user_id', None)
    
    # Debug logging
    print(f"api_view_creator_posts: creator_id={creator_id}, viewer_id={viewer_id}, is_own_profile={viewer_id == creator_id if viewer_id else False}")
    
    # Connect to DB
    connection = get_db_connection()
    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection failed."
        }), 500
    
    try:
        db_query = connection.cursor(dictionary=True)
        
        # If viewing own posts, show all posts
        if viewer_id and viewer_id == creator_id:
            db_query.execute(
                """
                SELECT 
                    p.post_id, 
                    p.content_text, 
                    p.media_url, 
                    p.privacy, 
                    p.created_at,
                    (SELECT COUNT(*) FROM post_like pl WHERE pl.post_id = p.post_id) as like_count
                FROM post p
                WHERE p.user_id = %s
                ORDER BY p.created_at DESC
                """,
                (creator_id,)
            )
        elif viewer_id:
            # Viewing someone else's posts - respect privacy
            # Show: public posts, friends posts (if friendship exists), exclusive posts (if subscribed)
            db_query.execute(
                """
                SELECT 
                    p.post_id, 
                    p.content_text, 
                    p.media_url, 
                    p.privacy, 
                    p.created_at,
                    (SELECT COUNT(*) FROM post_like pl WHERE pl.post_id = p.post_id) as like_count
                FROM post p
                WHERE p.user_id = %s
                  AND (
                    p.privacy = 'public'
                    OR (p.privacy = 'friends' AND EXISTS (
                        SELECT 1 FROM friends f 
                        WHERE (f.user_id = %s AND f.friend_user_id = %s)
                           OR (f.user_id = %s AND f.friend_user_id = %s)
                    ))
                    OR (p.privacy = 'exclusive' AND EXISTS (
                        SELECT 1 FROM subscription s
                        WHERE s.subscriber_id = %s 
                          AND s.creator_id = %s 
                          AND s.is_active = TRUE
                          AND NOW() BETWEEN s.start_date AND s.end_date
                    ))
                  )
                ORDER BY p.created_at DESC
                """,
                (creator_id, viewer_id, creator_id, creator_id, viewer_id, viewer_id, creator_id)
            )
            
            # Log for debugging
            print(f"Fetching posts for creator_id={creator_id}, viewer_id={viewer_id}")
            posts_fetched = db_query.fetchall()
            print(f"Found {len(posts_fetched)} posts")
            posts = posts_fetched
        else:
            # Not authenticated - only public posts
            db_query.execute(
                """
                SELECT 
                    p.post_id, 
                    p.content_text, 
                    p.media_url, 
                    p.privacy, 
                    p.created_at,
                    (SELECT COUNT(*) FROM post_like pl WHERE pl.post_id = p.post_id) as like_count
                FROM post p
                WHERE p.user_id = %s AND p.privacy = 'public'
                ORDER BY p.created_at DESC
                """,
                (creator_id,)
            )
            
            posts = db_query.fetchall()
        
        # Format response
        results = []
        for post in posts:
            results.append({
                "post_id": post['post_id'],
                "content_text": post['content_text'],
                "media_url": post['media_url'],
                "privacy": post['privacy'],
                "created_at": post['created_at'].isoformat() if post['created_at'] else None,
                "like_count": post['like_count'] or 0
            })
        
        return jsonify(results), 200
        
    except Exception as e:
        print(f"Error fetching creator posts: {e}")
        return jsonify({
            "success": False,
            "message": "Error fetching posts"
        }), 500
    finally:
        db_query.close()
        connection.close()

@app.route("/api/posts/<int:user_id>", methods=["GET"])
def get_user_posts(user_id):
    # Connect to DB
    connection = get_db_connection()
    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection failed."
        }), 500
    
    db_query = connection.cursor(dictionary=True)
    # get user's post query
    db_query.execute("SELECT post_id, content_text, media_url, privacy, created_at FROM post WHERE user_id=%s ORDER BY created_at DESC", (user_id,))
    posts = db_query.fetchall(); db_query.close(); connection.close()
    return jsonify(posts)

# --- Post Update/Delete ---
@app.route("/api/posts/<int:post_id>", methods=["PUT"])  # body: { user_id, content_text, media_url, privacy }
def api_update_post(post_id):
    data = request.get_json()
    user_id = int(data.get("user_id"))
    text = data.get("content_text")
    media = data.get("media_url")
    privacy = data.get("privacy")
    # Connect to DB
    connection = get_db_connection()
    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection failed."
        }), 500
    
    try:
        db_query = connection.cursor(dictionary=True)
        db_query.execute( # update post query
            """
            UPDATE post
            SET content_text=%s, media_url=%s, privacy=%s, updated_at=NOW()
            WHERE post_id=%s AND user_id=%s
            """,
            (text, media, privacy, post_id, user_id)
        )
        connection.commit()
        if db_query.rowcount == 0:
            return jsonify({"error": "Not found or not owner."}), 404
        return jsonify({"message": "Post updated."})
    finally:
        db_query.close(); connection.close()

@app.route("/api/posts/<int:post_id>", methods=["DELETE"])  # body: { user_id }
def api_delete_post(post_id):
    data = request.get_json()
    user_id = int(data.get("user_id"))
    # Connect to DB
    connection = get_db_connection()
    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection failed."
        }), 500
    
    db_query = connection.cursor(dictionary=True)
    try: # delete post query
        db_query.execute("DELETE FROM post WHERE post_id=%s AND user_id=%s", (post_id, user_id))
        connection.commit()
        if db_query.rowcount == 0:
            return jsonify({"error": "Not found or not owner."}), 404
        return jsonify({"message": "Post deleted."})
    finally:
        db_query.close(); connection.close()
        
# --- get random public posts and display ---
@app.route("/api/posts/public", methods=["GET"])
def api_public_posts():
    try:
        limit = int(request.args.get("limit", 20))
        # guard-rail for large limits
        limit = max(1, min(limit, 100))
    except ValueError:
        limit = 20

    # Connect to DB
    connection = get_db_connection()
    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection failed."
        }), 500

    try:
        db_query = connection.cursor(dictionary=True)
        # Include author name/username; only privacy='public'
        db_query.execute(
            """
            SELECT 
              p.post_id,
              p.user_id,
              p.content_text,
              p.media_url,
              p.media_type,
              p.privacy,
              p.created_at,
              u.user_name,
              u.user_email
            FROM post p
            JOIN user u ON u.user_id = p.user_id
            WHERE p.privacy = 'public'
            ORDER BY p.created_at DESC, p.post_id DESC
            LIMIT %s
            """,
            (limit,)
        )
        rows = db_query.fetchall()
        return jsonify({"success": True, "items": rows})
    finally:
        db_query.close()
        connection.close()

# --- Likes & Comments ---
# @app.route("/api/posts/<int:post_id>/like", methods=["POST"])  # body: { user_id }
# def api_like_post(post_id):
#     data = request.get_json(); user_id = int(data.get("user_id"))
#     # Connect to DB
#     connection = get_db_connection()
#     if connection is None:
#         return jsonify({
#             "success": False,
#             "message": "Database connection failed."
#         }), 500
    
#     db_query = connection.cursor(dictionary=True)
#     try: # give likes query
#         db_query.execute("INSERT IGNORE INTO post_like (user_id, post_id) VALUES (%s,%s)", (user_id, post_id))
#         connection.commit()
#         return jsonify({"message": "Liked."}), 201
#     finally:
#         db_query.close(); connection.close()

# @app.route("/api/posts/<int:post_id>/comment", methods=["POST"])  # body: { user_id, comment_text }
# def api_comment_post(post_id):
#     data = request.get_json(); user_id = int(data.get("user_id")); txt = data.get("comment_text", "").strip()
#     if not txt:
#         return jsonify({"error": "comment_text required"}), 400
#     con = db(); dbquery = connection.cursor()
#     try: # give comment query
#         db_query.execute("INSERT INTO comment (post_id, user_id, comment_text) VALUES (%s,%s,%s)", (post_id, user_id, txt))
#         connection.commit()
#         return jsonify({"message": "Comment added."}), 201
#     finally:
#         db_query.close(); connection.close()

# --- Rate ---
@app.route("/api/rate", methods=["POST"])
def rate_user():
    data = request.get_json()
    user_id, target_email, rating = data.get("user_id"), data.get("target_email"), int(data.get("rating_value"))
    # Connect to DB
    connection = get_db_connection()
    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection failed."
        }), 500
    
    db_query = connection.cursor(dictionary=True)
    # select user based on email query
    db_query.execute("SELECT user_id FROM user WHERE user_email=%s", (target_email,))
    target = db_query.fetchone()
    if not target:
        return jsonify({"error": "Target user not found."}), 404
    # give rating query 
    rated_user_id = target["user_id"]
    db_query.execute("INSERT INTO rating (user_id, rated_user_id, rating_value) VALUES (%s,%s,%s)", (user_id, rated_user_id, rating))
    connection.commit(); db_query.close(); connection.close()
    return jsonify({"message": f"Rated {target_email} with {rating}/10."})

@app.route("/api/rating/<email>", methods=["GET"])
def view_rating(email):
    # Connect to DB
    connection = get_db_connection()
    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection failed."
        }), 500
    
    db_query = connection.cursor(dictionary=True)
    # get average rating query
    db_query.execute("SELECT ROUND(AVG(rating_value),2) avg, COUNT(*) cnt FROM rating r JOIN user u ON r.rated_user_id=u.user_id WHERE u.user_email=%s", (email,))
    stats = db_query.fetchone(); db_query.close(); connection.close()
    if stats["cnt"]:
        return jsonify({"email": email, "average": stats["avg"], "count": stats["cnt"]})
    return jsonify({"message": "No ratings yet."})

# --- Friendship Management ---
# @app.route("/api/friends/<int:user_id>", methods=["GET"])
# def get_friends(user_id):
#     # Connect to DB
#     connection = get_db_connection()
#     if connection is None:
#         return jsonify({
#             "success": False,
#             "message": "Database connection failed."
#         }), 500
    
#     db_query = connection.cursor(dictionary=True)
#     # view all friends query
#     db_query.execute("SELECT u.user_id, u.user_name, u.user_email FROM friends f JOIN user u ON u.user_id=f.friend_user_id WHERE f.user_id=%s", (user_id,))
#     friends = db_query.fetchall(); db_query.close(); connection.close()
#     return jsonify(friends)

# @app.route("/api/friends/add", methods=["POST"])  # body: { user_id, other_user_id }
# def api_add_friend():
#     data = request.get_json()
#     user_id = int(data.get("user_id"))
#     other = int(data.get("other_user_id"))
#     # Connect to DB
#     connection = get_db_connection()
#     if connection is None:
#         return jsonify({
#             "success": False,
#             "message": "Database connection failed."
#         }), 500
    
#     try: # add friends query simultaneously
#         db_query = connection.cursor(dictionary=True)
#         db_query.execute("INSERT IGNORE INTO friends (user_id, friend_user_id) VALUES (%s,%s)", (user_id, other))
#         db_query.execute("INSERT IGNORE INTO friends (user_id, friend_user_id) VALUES (%s,%s)", (other, user_id))
#         connection.commit()
#         return jsonify({"message": "Friendship added (both directions)."}), 201
#     finally:
#         db_query.close(); connection.close()

# @app.route("/api/friends/remove", methods=["DELETE"])  # body: { user_id, other_user_id }
# def api_remove_friend():
#     data = request.get_json()
#     user_id = int(data.get("user_id"))
#     other = int(data.get("other_user_id"))
#     # Connect to DB
#     connection = get_db_connection()
#     if connection is None:
#         return jsonify({
#             "success": False,
#             "message": "Database connection failed."
#         }), 500
    
#     try: # remove friends query simultaneously
#         db_query = connection.cursor(dictionary=True)
#         db_query.execute("""
#             DELETE FROM friends
#             WHERE (user_id=%s AND friend_user_id=%s)
#                OR (user_id=%s AND friend_user_id=%s)
#         """, (user_id, other, other, user_id))
#         connection.commit()
#         return jsonify({"message": "Friendship removed."})
#     finally:
#         db_query.close(); connection.close()

# --- Subscription / Membership (simulated) ---
@app.route("/api/subscribe", methods=["POST"])  # body: { subscriber_id, creator_id }
def api_subscribe():
    data = request.get_json()
    subscriber = int(data.get("subscriber_id"))
    creator = int(data.get("creator_id"))
     # Connect to DB
    connection = get_db_connection()
    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection failed."
        }), 500

    try: # subscribed to friend query
        db_query = connection.cursor(dictionary=True)
        db_query.execute(
            """
            INSERT INTO subscription (subscriber_id, creator_id, start_date, end_date, is_active)
            VALUES (%s,%s, NOW(), DATE_ADD(NOW(), INTERVAL 30 DAY), TRUE)
            """,
            (subscriber, creator)
        )
        # record fake payment
        # query to indicate payment is completed query
        db_query.execute(
            """
            INSERT INTO payment (user_id, payment_type, amount, status, transaction_reference)
            VALUES (%s,'subscription', 4.99, 'completed', 'FAKE-TXN-SUB')
            """,
            (subscriber,)
        )
        connection.commit()
        return jsonify({"message": "Subscribed for 30 days."}), 201
    finally:
        db_query.close(); connection.close()

@app.route("/api/membership", methods=["POST"])  # body: { user_id }
def api_membership():
    data = request.get_json(); user_id = int(data.get("user_id"))
    # Connect to DB
    connection = get_db_connection()
    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection failed."
        }), 500
    
    try: # subscribed to membership query
        db_query = connection.cursor(dictionary=True)
        db_query.execute(
            """
            INSERT INTO membership (user_id, membership_type, start_date, end_date, is_active)
            VALUES (%s,'premium', NOW(), DATE_ADD(NOW(), INTERVAL 30 DAY), TRUE)
            """,
            (user_id,)
        )
        # query to indicate payment is completed query
        db_query.execute(
            """
            INSERT INTO payment (user_id, payment_type, amount, status, transaction_reference)
            VALUES (%s,'membership', 9.99, 'completed', 'FAKE-TXN-MEM')
            """,
            (user_id,)
        )
        connection.commit()
        return jsonify({"message": "Membership activated for 30 days."}), 201
    finally:
        db_query.close(); connection.close()

print("UPLOAD_FOLDER path is:", app.config["UPLOAD_FOLDER"])


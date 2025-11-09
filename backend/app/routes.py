from app import app
from flask import render_template, request, redirect, url_for, flash, session, jsonify, make_response
from app.hash import hash_password, verify_password
from app.db import get_db_connection
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

@app.route("/api-tester") # remove after testing
def api_tester():
    return render_template("tester_api.html")

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

@app.route("/api/profile/update", methods=["PUT"])
def update_profile():
    data = request.get_json()
    user_id = data.get("user_id")
    name, bio, pic, private = data.get("user_name"), data.get("bio"), data.get("profile_picture"), data.get("is_private", False)
    # Connect to DB
    connection = get_db_connection()
    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection failed."
        }), 500
    
    db_query = connection.cursor(dictionary=True)
    # update profile query
    db_query.execute("UPDATE user SET user_name=%s, bio=%s, profile_picture=%s, is_private=%s WHERE user_id=%s", (name, bio, pic, private, user_id))
    connection.commit(); db_query.close(); connection.close()
    return jsonify({"message": "Profile updated successfully."})

# --- Post Management ---
@app.route("/api/posts", methods=["POST"])
def create_post():
    data = request.get_json()
    user_id, text, media, privacy = data.get("user_id"), data.get("content_text"), data.get("media_url"), data.get("privacy")
    # Connect to DB
    connection = get_db_connection()
    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection failed."
        }), 500
    
    db_query = connection.cursor(dictionary=True)
    # create post query
    db_query.execute("INSERT INTO post (user_id, content_text, media_url, privacy) VALUES (%s,%s,%s,%s)", (user_id, text, media, privacy))
    connection.commit(); db_query.close(); connection.close()
    return jsonify({"message": "Post created successfully."})

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

# --- Post Visibility (public / friends / exclusive) ---
@app.route("/api/posts/user/<int:creator_id>", methods=["GET"])  # query: ?viewer=<viewer_id>
def api_view_creator_posts(creator_id):
    try:
        viewer_id = int(request.args.get("viewer"))
    except (TypeError, ValueError):
        return jsonify({"error": "Missing or invalid viewer id"}), 400
    # Connect to DB
    connection = get_db_connection()
    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection failed."
        }), 500
    
    db_query = connection.cursor(dictionary=True)
    # visibility rule: public OR (friends & friendship exists) OR (exclusive & subscription exists)
    # view other posts with logic implemented in sql query
    # works with exclusive subcription and friends posts
    try: 
        db_query.execute(
            """
            SELECT p.post_id, p.content_text, p.media_url, p.privacy, p.created_at
            FROM post p
            WHERE p.user_id=%s
              AND (
                p.privacy='public'
                OR (p.privacy='friends' AND EXISTS (
                    SELECT 1 FROM friends WHERE user_id=%s AND friend_user_id=%s
                ))
                OR (p.privacy='exclusive' AND EXISTS (
                    SELECT 1 FROM subscription s
                    WHERE s.subscriber_id=%s AND s.creator_id=%s AND s.is_active=TRUE
                          AND NOW() BETWEEN s.start_date AND s.end_date
                ))
              )
            ORDER BY p.created_at DESC
            """,
            (creator_id, viewer_id, creator_id, viewer_id, creator_id)
        )
        return jsonify(db_query.fetchall())
    finally:
        db_query.close(); connection.close()

# --- Likes & Comments ---
@app.route("/api/posts/<int:post_id>/like", methods=["POST"])  # body: { user_id }
def api_like_post(post_id):
    data = request.get_json(); user_id = int(data.get("user_id"))
    # Connect to DB
    connection = get_db_connection()
    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection failed."
        }), 500
    
    db_query = connection.cursor(dictionary=True)
    try: # give likes query
        db_query.execute("INSERT IGNORE INTO post_like (user_id, post_id) VALUES (%s,%s)", (user_id, post_id))
        connection.commit()
        return jsonify({"message": "Liked."}), 201
    finally:
        db_query.close(); connection.close()

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
@app.route("/api/friends/<int:user_id>", methods=["GET"])
def get_friends(user_id):
    # Connect to DB
    connection = get_db_connection()
    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection failed."
        }), 500
    
    db_query = connection.cursor(dictionary=True)
    # view all friends query
    db_query.execute("SELECT u.user_id, u.user_name, u.user_email FROM friends f JOIN user u ON u.user_id=f.friend_user_id WHERE f.user_id=%s", (user_id,))
    friends = db_query.fetchall(); db_query.close(); connection.close()
    return jsonify(friends)

@app.route("/api/friends/add", methods=["POST"])  # body: { user_id, other_user_id }
def api_add_friend():
    data = request.get_json()
    user_id = int(data.get("user_id"))
    other = int(data.get("other_user_id"))
    # Connect to DB
    connection = get_db_connection()
    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection failed."
        }), 500
    
    try: # add friends query simultaneously
        db_query = connection.cursor(dictionary=True)
        db_query.execute("INSERT IGNORE INTO friends (user_id, friend_user_id) VALUES (%s,%s)", (user_id, other))
        db_query.execute("INSERT IGNORE INTO friends (user_id, friend_user_id) VALUES (%s,%s)", (other, user_id))
        connection.commit()
        return jsonify({"message": "Friendship added (both directions)."}), 201
    finally:
        db_query.close(); connection.close()

@app.route("/api/friends/remove", methods=["DELETE"])  # body: { user_id, other_user_id }
def api_remove_friend():
    data = request.get_json()
    user_id = int(data.get("user_id"))
    other = int(data.get("other_user_id"))
    # Connect to DB
    connection = get_db_connection()
    if connection is None:
        return jsonify({
            "success": False,
            "message": "Database connection failed."
        }), 500
    
    try: # remove friends query simultaneously
        db_query = connection.cursor(dictionary=True)
        db_query.execute("""
            DELETE FROM friends
            WHERE (user_id=%s AND friend_user_id=%s)
               OR (user_id=%s AND friend_user_id=%s)
        """, (user_id, other, other, user_id))
        connection.commit()
        return jsonify({"message": "Friendship removed."})
    finally:
        db_query.close(); connection.close()

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

from app import app
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app.hash import hash_password, verify_password
from app.db import get_db_connection
import re
from itsdangerous import URLSafeTimedSerializer
from app.two_factor import initiate_2fa, verify_2fa_code


@app.route('/')
@app.route('/index')
def index():
    return "Hello, World!"

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
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM user WHERE user_name=%s", (username,))
            user = cursor.fetchone()

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
            if cursor:
                cursor.close()
            if connection:
                connection.close()


    # Render the template and pass the result (if any)
    return render_template('login.html', result=result)

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM user WHERE user_name=%s", (username,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if not user or not verify_password(user['password_hash'], password):
        return jsonify({"message": "Invalid username or password"}), 401

    return jsonify({"message": f"Welcome {username}!"})


    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    code = data.get("code")  # optional 2FA code

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password required"}), 400

    # 1️⃣ Validate username/password
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM user WHERE user_name=%s", (username,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if not user or not verify_password(user['password_hash'], password):
        return jsonify({"success": False, "message": "Invalid username or password"}), 401

    # 2️⃣ If 2FA was already initiated, verify the code
    if "2fa_code" in session and session.get("2fa_email") == user["user_email"]:
        if not code:
            return jsonify({"success": False, "two_factor": True, "message": "2FA code required"})
        
        valid, msg = verify_2fa_code(code)
        if not valid:
            return jsonify({"success": False, "message": msg}), 400
        
        # Success: clean up 2FA session data and mark user as logged in
        session.pop("2fa_code", None)
        session.pop("2fa_timestamp", None)
        session.pop("2fa_email", None)
        session["user"] = user["user_name"]

        return jsonify({"success": True, "message": f"Welcome, {username}!"})

    # 3️⃣ If 2FA not initiated yet, start it
    initiate_2fa(user["user_email"])
    session["pending_user"] = user["user_name"]

    return jsonify({"success": False, "two_factor": True, "message": "2FA code sent to your email"})

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


    data = request.get_json()
    code = data.get('code')

    if not code:
        return jsonify({"success": False, "message": "Please enter your verification code."}), 400

    valid, message = verify_2fa_code(code)
    if valid:
        username = session.pop('pending_user', None)
        session['user'] = username
        return jsonify({"success": True, "message": f"Welcome, {username}! You are now logged in."})
    else:
        return jsonify({"success": False, "message": message}), 400

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
            cursor = connection.cursor()

            # Check if username or email already exists
            cursor.execute("SELECT * FROM user WHERE user_name=%s OR user_email=%s", (username, email))
            existing_user = cursor.fetchone()

            if existing_user:
                flash("Username or email already exists!", "danger")
                return render_template('register.html')

            # Insert new user into database
            insert_query = "INSERT INTO user (user_name, user_email, password_hash) VALUES (%s, %s, %s)"
            cursor.execute(insert_query, (username, email, password_hash))
            connection.commit()
            flash("Account created successfully!", "success")
        
        except Exception as e:
            print(f"Database error: {e}")
            flash("An error occurred while creating the account.", "danger")
            return render_template('register.html')

        finally:
            # Always close cursor and connection
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        flash("Account created successfully!", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/api/register', methods=['POST'])
def api_register():
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
        return jsonify({"message": "All required fields must be filled."}), 400

    # Check if passwords match
    if password != confirm_password:
        return jsonify({"message": "Passwords do not match!"}), 400

    # Validate username and email format
    USERNAME_RE = re.compile(r'^[A-Za-z0-9_]{3,20}$')
    if not USERNAME_RE.match(username):
        return jsonify({"message": "Invalid username format."}), 400

    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return jsonify({"message": "Invalid email format."}), 400

    # Length checks
    if len(username) > 50 or len(email) > 100 or len(password) > 100:
        return jsonify({"message": "Input too long."}), 400

    password_hash = hash_password(password)
    private_value = 1 if private else 0  # ✅ convert bool → tinyint(1)

    # Connect to DB
    connection = get_db_connection()
    if connection is None:
        return jsonify({"message": "Database connection failed."}), 500

    try:
        cursor = connection.cursor(dictionary=True)

        # Check if username or email exists
        cursor.execute(
            "SELECT * FROM user WHERE user_name=%s OR user_email=%s",
            (username, email),
        )
        existing_user = cursor.fetchone()

        if existing_user:
            return jsonify({"message": "Username or email already exists!"}), 400

        # Insert new user
        insert_query = """
            INSERT INTO user (user_name, user_email, password_hash, bio, is_private)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (username, email, password_hash, bio, private_value))
        connection.commit()

    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({"message": "An error occurred during registration."}), 500

    finally:
        cursor.close()
        connection.close()

    return jsonify({"message": "Account created successfully!"}), 201

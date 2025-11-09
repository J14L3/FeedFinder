from . import app   # uses the app defined in app/__init__.py (testing)
from flask import Flask, request, jsonify, render_template # remove render_template after testing
import mysql.connector



# --- Database Configuration ---
DB_CFG = dict(
    host="localhost",
    user="ssduser",
    password="P@ssw0rdSSD67",
    database="feedfinder",
    autocommit=True
)

def db():
    return mysql.connector.connect(**DB_CFG)

@app.route("/api-tester") # remove after testing
def api_tester():
    return render_template("tester_api.html")

# --- Auth ---
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    name, email, password = data.get("user_name"), data.get("user_email"), data.get("password")
    con = db(); cur = con.cursor()
    try: # create new user query
        cur.execute("INSERT INTO user (user_name, user_email, password_hash) VALUES (%s,%s,%s)", (name, email, password))
        return jsonify({"message": "User registered successfully."}), 201
    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close(); con.close()

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    email, password = data.get("user_email"), data.get("password")
    con = db(); cur = con.cursor(dictionary=True)
    # get user query
    cur.execute("SELECT user_id, password_hash FROM user WHERE user_email=%s AND is_active=TRUE", (email,))
    user = cur.fetchone(); cur.close(); con.close()

    if user and user["password_hash"] == password:
        return jsonify({"success": True, "user_id": user["user_id"]})
    return jsonify({"success": False, "message": "Invalid credentials."}), 401


# --- Profile Management ---
# can take from session value also
@app.route("/api/profile/<int:user_id>", methods=["GET"])
def get_profile(user_id):
    con = db(); cur = con.cursor(dictionary=True)
    # view profile query with user_id
    cur.execute("SELECT user_id, user_name, user_email, bio, profile_picture, is_private FROM user WHERE user_id=%s", (user_id,))
    profile = cur.fetchone(); cur.close(); con.close()

    if profile:
        return jsonify(profile)
    return jsonify({"error": "User not found"}), 404

@app.route("/api/profile/by-email", methods=["GET"])
def get_profile_by_email():
    email = (request.args.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "missing email"}), 400

    con = db(); cur = con.cursor(dictionary=True)
    try:
        cur.execute(
            "SELECT user_id, user_name, user_email, bio, profile_picture, is_private "
            "FROM `user` WHERE LOWER(user_email)=%s",
            (email,)
        )
        profile = cur.fetchone()
    finally:
        cur.close(); con.close()

    if profile:
        return jsonify(profile)
    return jsonify({"error": "User not found"}), 404

@app.route("/api/profile/update", methods=["PUT"])
def update_profile():
    data = request.get_json()
    user_id = data.get("user_id")
    name, bio, pic, private = data.get("user_name"), data.get("bio"), data.get("profile_picture"), data.get("is_private", False)
    con = db(); cur = con.cursor()
    # update profile query
    cur.execute("UPDATE user SET user_name=%s, bio=%s, profile_picture=%s, is_private=%s WHERE user_id=%s", (name, bio, pic, private, user_id))
    con.commit(); cur.close(); con.close()
    return jsonify({"message": "Profile updated successfully."})

# --- Post Management ---
@app.route("/api/posts", methods=["POST"])
def create_post():
    data = request.get_json()
    user_id, text, media, privacy = data.get("user_id"), data.get("content_text"), data.get("media_url"), data.get("privacy")
    con = db(); cur = con.cursor()
    # create post query
    cur.execute("INSERT INTO post (user_id, content_text, media_url, privacy) VALUES (%s,%s,%s,%s)", (user_id, text, media, privacy))
    con.commit(); cur.close(); con.close()
    return jsonify({"message": "Post created successfully."})

@app.route("/api/posts/<int:user_id>", methods=["GET"])
def get_user_posts(user_id):
    con = db(); cur = con.cursor(dictionary=True)
    # get user's post query
    cur.execute("SELECT post_id, content_text, media_url, privacy, created_at FROM post WHERE user_id=%s ORDER BY created_at DESC", (user_id,))
    posts = cur.fetchall(); cur.close(); con.close()
    return jsonify(posts)

# --- Post Update/Delete ---
@app.route("/api/posts/<int:post_id>", methods=["PUT"])  # body: { user_id, content_text, media_url, privacy }
def api_update_post(post_id):
    data = request.get_json()
    user_id = int(data.get("user_id"))
    text = data.get("content_text")
    media = data.get("media_url")
    privacy = data.get("privacy")
    con = db(); cur = con.cursor()
    try:
        cur.execute( # update post query
            """
            UPDATE post
            SET content_text=%s, media_url=%s, privacy=%s, updated_at=NOW()
            WHERE post_id=%s AND user_id=%s
            """,
            (text, media, privacy, post_id, user_id)
        )
        con.commit()
        if cur.rowcount == 0:
            return jsonify({"error": "Not found or not owner."}), 404
        return jsonify({"message": "Post updated."})
    finally:
        cur.close(); con.close()

@app.route("/api/posts/<int:post_id>", methods=["DELETE"])  # body: { user_id }
def api_delete_post(post_id):
    data = request.get_json()
    user_id = int(data.get("user_id"))
    con = db(); cur = con.cursor()
    try: # delete post query
        cur.execute("DELETE FROM post WHERE post_id=%s AND user_id=%s", (post_id, user_id))
        con.commit()
        if cur.rowcount == 0:
            return jsonify({"error": "Not found or not owner."}), 404
        return jsonify({"message": "Post deleted."})
    finally:
        cur.close(); con.close()

# --- Post Visibility (public / friends / exclusive) ---
@app.route("/api/posts/user/<int:creator_id>", methods=["GET"])  # query: ?viewer=<viewer_id>
def api_view_creator_posts(creator_id):
    try:
        viewer_id = int(request.args.get("viewer"))
    except (TypeError, ValueError):
        return jsonify({"error": "Missing or invalid viewer id"}), 400
    con = db(); cur = con.cursor(dictionary=True)
    # visibility rule: public OR (friends & friendship exists) OR (exclusive & subscription exists)
    # view other posts with logic implemented in sql query
    # works with exclusive subcription and friends posts
    try: 
        cur.execute(
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
        return jsonify(cur.fetchall())
    finally:
        cur.close(); con.close()

# --- Likes & Comments ---
@app.route("/api/posts/<int:post_id>/like", methods=["POST"])  # body: { user_id }
def api_like_post(post_id):
    data = request.get_json(); user_id = int(data.get("user_id"))
    con = db(); cur = con.cursor()
    try: # give likes query
        cur.execute("INSERT IGNORE INTO post_like (user_id, post_id) VALUES (%s,%s)", (user_id, post_id))
        con.commit()
        return jsonify({"message": "Liked."}), 201
    finally:
        cur.close(); con.close()

# @app.route("/api/posts/<int:post_id>/comment", methods=["POST"])  # body: { user_id, comment_text }
# def api_comment_post(post_id):
#     data = request.get_json(); user_id = int(data.get("user_id")); txt = data.get("comment_text", "").strip()
#     if not txt:
#         return jsonify({"error": "comment_text required"}), 400
#     con = db(); cur = con.cursor()
#     try: # give comment query
#         cur.execute("INSERT INTO comment (post_id, user_id, comment_text) VALUES (%s,%s,%s)", (post_id, user_id, txt))
#         con.commit()
#         return jsonify({"message": "Comment added."}), 201
#     finally:
#         cur.close(); con.close()

# --- Rate ---
@app.route("/api/rate", methods=["POST"])
def rate_user():
    data = request.get_json()
    user_id, target_email, rating = data.get("user_id"), data.get("target_email"), int(data.get("rating_value"))
    con = db(); cur = con.cursor(dictionary=True)
    # select user based on email query
    cur.execute("SELECT user_id FROM user WHERE user_email=%s", (target_email,))
    target = cur.fetchone()
    if not target:
        return jsonify({"error": "Target user not found."}), 404
    # give rating query 
    rated_user_id = target["user_id"]
    cur.execute("INSERT INTO rating (user_id, rated_user_id, rating_value) VALUES (%s,%s,%s)", (user_id, rated_user_id, rating))
    con.commit(); cur.close(); con.close()
    return jsonify({"message": f"Rated {target_email} with {rating}/10."})

@app.route("/api/rating/<email>", methods=["GET"])
def view_rating(email):
    con = db(); cur = con.cursor(dictionary=True)
    # get average rating query
    cur.execute("SELECT ROUND(AVG(rating_value),2) avg, COUNT(*) cnt FROM rating r JOIN user u ON r.rated_user_id=u.user_id WHERE u.user_email=%s", (email,))
    stats = cur.fetchone(); cur.close(); con.close()
    if stats["cnt"]:
        return jsonify({"email": email, "average": stats["avg"], "count": stats["cnt"]})
    return jsonify({"message": "No ratings yet."})

# --- Friendship Management ---
@app.route("/api/friends/<int:user_id>", methods=["GET"])
def get_friends(user_id):
    con = db(); cur = con.cursor(dictionary=True)
    # view all friends query
    cur.execute("SELECT u.user_id, u.user_name, u.user_email FROM friends f JOIN user u ON u.user_id=f.friend_user_id WHERE f.user_id=%s", (user_id,))
    friends = cur.fetchall(); cur.close(); con.close()
    return jsonify(friends)

@app.route("/api/friends/add", methods=["POST"])  # body: { user_id, other_user_id }
def api_add_friend():
    data = request.get_json()
    user_id = int(data.get("user_id"))
    other = int(data.get("other_user_id"))
    con = db(); cur = con.cursor()
    try: # add friends query simultaneously
        cur.execute("INSERT IGNORE INTO friends (user_id, friend_user_id) VALUES (%s,%s)", (user_id, other))
        cur.execute("INSERT IGNORE INTO friends (user_id, friend_user_id) VALUES (%s,%s)", (other, user_id))
        con.commit()
        return jsonify({"message": "Friendship added (both directions)."}), 201
    finally:
        cur.close(); con.close()

@app.route("/api/friends/remove", methods=["DELETE"])  # body: { user_id, other_user_id }
def api_remove_friend():
    data = request.get_json()
    user_id = int(data.get("user_id"))
    other = int(data.get("other_user_id"))
    con = db(); cur = con.cursor()
    try: # remove friends query simultaneously
        cur.execute("""
            DELETE FROM friends
            WHERE (user_id=%s AND friend_user_id=%s)
               OR (user_id=%s AND friend_user_id=%s)
        """, (user_id, other, other, user_id))
        con.commit()
        return jsonify({"message": "Friendship removed."})
    finally:
        cur.close(); con.close()

# --- Subscription / Membership (simulated) ---
@app.route("/api/subscribe", methods=["POST"])  # body: { subscriber_id, creator_id }
def api_subscribe():
    data = request.get_json()
    subscriber = int(data.get("subscriber_id"))
    creator = int(data.get("creator_id"))
    con = db(); cur = con.cursor()
    try: # subscribed to friend query
        cur.execute(
            """
            INSERT INTO subscription (subscriber_id, creator_id, start_date, end_date, is_active)
            VALUES (%s,%s, NOW(), DATE_ADD(NOW(), INTERVAL 30 DAY), TRUE)
            """,
            (subscriber, creator)
        )
        # record fake payment
        # query to indicate payment is completed query
        cur.execute(
            """
            INSERT INTO payment (user_id, payment_type, amount, status, transaction_reference)
            VALUES (%s,'subscription', 4.99, 'completed', 'FAKE-TXN-SUB')
            """,
            (subscriber,)
        )
        con.commit()
        return jsonify({"message": "Subscribed for 30 days."}), 201
    finally:
        cur.close(); con.close()

@app.route("/api/membership", methods=["POST"])  # body: { user_id }
def api_membership():
    data = request.get_json(); user_id = int(data.get("user_id"))
    con = db(); cur = con.cursor()
    try: # subscribed to membership query
        cur.execute(
            """
            INSERT INTO membership (user_id, membership_type, start_date, end_date, is_active)
            VALUES (%s,'premium', NOW(), DATE_ADD(NOW(), INTERVAL 30 DAY), TRUE)
            """,
            (user_id,)
        )
        # query to indicate payment is completed query
        cur.execute(
            """
            INSERT INTO payment (user_id, payment_type, amount, status, transaction_reference)
            VALUES (%s,'membership', 9.99, 'completed', 'FAKE-TXN-MEM')
            """,
            (user_id,)
        )
        con.commit()
        return jsonify({"message": "Membership activated for 30 days."}), 201
    finally:
        cur.close(); con.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


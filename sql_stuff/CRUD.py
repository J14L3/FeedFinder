# from flask import Flask
# import mysql.connector

# app = Flask(__name__)

# db = mysql.connector.connect(
#     host="localhost",
#     user="ssduser",
#     password="P@ssw0rdSSD67",
#     database="feedfinder"
# )

# @app.route("/")
# def index():
#     return 'NIGGER'

# @app.route('/friends')
# def users():
#     cursor=db.cursor()
#     cursor.execute("SELECT * FROM friends")
#     users_list = cursor.fetchall()
#     cursor.close()
#     return str(users_list)
#     # return f"[h2]Users:[/h2]" + " 8br 9".join([f"{user[1]} - {user[2]}" for user in users_list])

# app.run(debug=True)
from flask import Flask, request, redirect, session, render_template_string, url_for, flash
import mysql.connector
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "six7" # for session management can change to smt more secure

# DB config
DB_CFG = dict(
    host="localhost",
    user="ssduser",
    password="P@ssw0rdSSD67",
    database="feedfinder",
    autocommit=True
)

def db():
    return mysql.connector.connect(**DB_CFG)

def logged_in():
    return "user_id" in session

def require_login():
    if not logged_in():
        return redirect(url_for("login"))

BASE = """
<!doctype html>
<title> SQL Testing </title>
<h2>SQL TESTING NIGGER</h2>
{% with msgs = get_flashed_messages() %}
  {% if msgs %}<ul style="color:green;">{% for m in msgs %}<li>{{ m }}</li>{% endfor %}</ul>{% endif %}
{% endwith %}
<nav style="margin-bottom:12px;">
<a href="http://127.0.0.1:5000/register">register</a> |
<a href="http://127.0.0.1:5000/login">login</a> |
<a href="http://127.0.0.1:5000/profile">profile</a> |
<a href="http://127.0.0.1:5000/profile/update">update</a> |
<a href="http://127.0.0.1:5000/friends">friends</a> |
<a href="http://127.0.0.1:5000/friends/add">add friend</a> |
<a href="http://127.0.0.1:5000/posts/create">create post</a> |
<a href="http://127.0.0.1:5000/posts/mine">my posts</a> |
<a href="http://127.0.0.1:5000/posts/user">others' posts</a> |
<a href="http://127.0.0.1:5000/membership">membership</a> |
<a href="http://127.0.0.1:5000/subscribe">subscribe</a> |
<a href="http://127.0.0.1:5000/rate">rate</a> |
<a href="http://127.0.0.1:5000/logout">logout</a>
</nav>
{{ body|safe }}
"""

# ---------------- AUTH ----------------
@app.route("/register", methods=["GET","POST"]) # register query
def register():
    if request.method == "POST":
        name = request.form["user_name"].strip()
        email = request.form["user_email"].strip().lower()
        pwd = request.form["password"]                 # add hashing algo logic here
        con=db(); cur=con.cursor()
        # create new user query
        try:
            cur.execute("INSERT INTO user (user_name,user_email,password_hash) VALUES (%s,%s,%s)",
                        (name,email,pwd))
            flash("registered, you can login now.")
            flash("Inserted:", cur.rowcount)
            return redirect(url_for("login"))
        except mysql.connector.Error as e:
            flash(str(e))
        finally:
            cur.close(); con.close()
    body="""<form method='post'>
      <input name='user_name' placeholder='name'>
      <input name='user_email' placeholder='email'>
      <input name='password' type='password' placeholder='password'>
      <button>register</button></form>"""
    return render_template_string(BASE,title="Register",body=body)

@app.route("/login", methods=["GET","POST"])  # login query
def login():
    if request.method=="POST":
        email=request.form["user_email"].strip().lower()
        pwd=request.form["password"]
        con=db(); cur=con.cursor(dictionary=True)
        # get user query
        cur.execute("SELECT user_id,password_hash FROM user WHERE user_email=%s AND is_active=TRUE",(email,))
        row=cur.fetchone(); cur.close(); con.close()
        # replace below with own hashing algo verification
        if row and row["password_hash"]==pwd:
            session["user_id"]=row["user_id"]; flash("logged in.")
            return redirect(url_for("profile"))
        flash("invalid credentials.")
    body="""<form method='post'>
      <input name='user_email' placeholder='email'>
      <input name='password' type='password' placeholder='password'>
      <button>login</button></form>"""
    return render_template_string(BASE,title="Login",body=body)

@app.route("/logout")
def logout():
    session.clear(); flash("logged out."); return redirect(url_for("login"))

# ---------------- PROFILE ----------------
@app.route("/profile") 
def profile():
    if not logged_in(): return require_login()
    con=db(); cur=con.cursor(dictionary=True)
    # view profile query
    cur.execute("SELECT user_id,user_name,user_email,bio,profile_picture,is_private FROM user WHERE user_id=%s",
                (session["user_id"],))
    u=cur.fetchone(); cur.close(); con.close()
    body=f"<p>Name:{u['user_name']}<br>Email:{u['user_email']}<br>Private:{u['is_private']}<br>Bio:{u['bio'] or ''}</p>"
    return render_template_string(BASE,title="Profile",body=body)

@app.route("/profile/update",methods=["GET","POST"]) 
def profile_update():
    if not logged_in(): return require_login()
    if request.method=="POST":
        name=request.form.get("user_name")
        bio=request.form.get("bio")
        pic=request.form.get("profile_picture")
        private=1 if request.form.get("is_private")=="on" else 0
        con=db(); cur=con.cursor()
        # update profile query
        cur.execute("UPDATE user SET user_name=%s,bio=%s,profile_picture=%s,is_private=%s WHERE user_id=%s",
                    (name,bio,pic,private,session["user_id"]))
        cur.close(); con.close()
        flash("profile updated.")
        return redirect(url_for("profile"))
    body="""<form method='post'>
      <input name='user_name' placeholder='new name'>
      <input name='profile_picture' placeholder='pic url'>
      <textarea name='bio'></textarea>
      <label><input type='checkbox' name='is_private'> private</label>
      <button>update</button></form>"""
    return render_template_string(BASE,title="Update Profile",body=body)

# ---------- friends ----------
@app.route("/friends", methods=["GET", "POST"]) 
def friends():
    if not logged_in(): return require_login()
    if request.method == "POST":
        # remove friend, both directions, remove friends query
        fid = request.form.get("friend_id")
        con = db(); cur = con.cursor()
        cur.execute("""DELETE FROM friends 
                       WHERE (user_id=%s AND friend_user_id=%s) OR (user_id=%s AND friend_user_id=%s)""",
                    (session["user_id"], fid, fid, session["user_id"]))
        cur.close(); con.close()
        flash("friend removed.")
        return redirect(url_for("friends"))
    con = db(); cur = con.cursor(dictionary=True)
    # view friends query
    cur.execute("""SELECT u.user_id, u.user_name, u.user_email 
                   FROM friends f JOIN user u ON u.user_id=f.friend_user_id
                   WHERE f.user_id=%s""", (session["user_id"],))
    rows = cur.fetchall()
    cur.close(); con.close()
    items = "".join([f"<li>{r['user_name']} ({r['user_email']}) "
                     f"<form style='display:inline' method='post'>"
                     f"<input type='hidden' name='friend_id' value='{r['user_id']}'><button>remove</button></form></li>"
                     for r in rows]) or "<i>no friends yet</i>"
    body = f"<ul>{items}</ul>"
    return render_template_string(BASE, title="Friends (view/remove)", body=body)

@app.route("/friends/add", methods=["GET", "POST"])
def friends_add():
    if not logged_in(): return require_login()
    results = ""
    if request.method == "POST":
        if "search" in request.form:
            q = f"%{request.form.get('query','').strip().lower()}%"
            con = db(); cur = con.cursor(dictionary=True)
            # view all friends query
            cur.execute("""SELECT user_id, user_name, user_email FROM user 
                           WHERE (LOWER(user_email) LIKE %s OR LOWER(user_name) LIKE %s) AND user_id<>%s""",
                        (q, q, session["user_id"]))
            rows = cur.fetchall()
            cur.close(); con.close()
            if rows:
                results = "<ul>" + "".join(
                    [f"<li>{r['user_name']} ({r['user_email']}) "
                     f"<form style='display:inline' method='post'>"
                     f"<input type='hidden' name='add_user_id' value='{r['user_id']}'><button name='add' value='1'>add</button></form></li>"
                     for r in rows]) + "</ul>"
            else:
                results = "<i>no matches</i>"
        elif "add" in request.form:
            other = int(request.form.get("add_user_id"))
            con = db(); cur = con.cursor()
            # insert both directions (ignore duplicates)
            # add friends query, both ways
            cur.execute("INSERT IGNORE INTO friends (user_id, friend_user_id) VALUES (%s,%s)", (session["user_id"], other))
            cur.execute("INSERT IGNORE INTO friends (user_id, friend_user_id) VALUES (%s,%s)", (other, session["user_id"]))
            cur.close(); con.close()
            flash("friend added (both directions).")
            return redirect(url_for("friends"))
    body = f"""
<form method="post">
  <input name="query" placeholder="name or email">
  <button name="search" value="1">search</button>
</form>
<div style="margin-top:10px;">{results}</div>
"""
    return render_template_string(BASE, title="Search / Add Friend", body=body)

# ---------- posts ----------
@app.route("/posts/create", methods=["GET","POST"]) 
def post_create():
    if not logged_in(): return require_login()
    if request.method == "POST":
        text = request.form.get("content_text")
        media = request.form.get("media_url")
        privacy = request.form.get("privacy")
        con = db(); cur = con.cursor()
        # create post query
        cur.execute("""INSERT INTO post (user_id, content_text, media_url, privacy)
                       VALUES (%s,%s,%s,%s)""",
                    (session["user_id"], text, media, privacy))
        cur.close(); con.close()
        flash("post created.")
        return redirect(url_for("posts_mine"))
    body = """
<form method="post">
  <textarea name="content_text" placeholder="text"></textarea><br>
  <input name="media_url" placeholder="media url (optional)">
  <select name="privacy">
    <option>public</option><option>friends</option><option>exclusive</option>
  </select>
  <button>create</button>
</form>
"""
    return render_template_string(BASE, title="Create Post", body=body)

@app.route("/posts/mine", methods=["GET","POST"])
def posts_mine():
    if not logged_in():
        return require_login()

    if request.method == "POST":
        # Handle delete or update submission
        pid = request.form.get("post_id")
        if "delete" in request.form:
            con = db(); cur = con.cursor()
            # delete post query
            cur.execute("DELETE FROM post WHERE post_id=%s AND user_id=%s", (pid, session["user_id"]))
            cur.close(); con.close()
            flash("Post deleted.")
            return redirect(url_for("posts_mine"))

        elif "update" in request.form:
            con = db(); cur = con.cursor(dictionary=True)
            # select post query
            cur.execute("SELECT content_text, media_url, privacy FROM post WHERE post_id=%s AND user_id=%s",
                        (pid, session["user_id"]))
            post = cur.fetchone()
            cur.close(); con.close()
            if not post:
                flash("Post not found.")
                return redirect(url_for("posts_mine"))
            # Render inline update form
            body = f"""
            <h3>Editing Post #{pid}</h3>
            <form method="post">
                <input type="hidden" name="post_id" value="{pid}">
                <label>Caption/Text:</label>
                <textarea name="content_text" required>{post['content_text']}</textarea><br>
                <label>Media URL:</label>
                <textarea name="media_url" required>{post['media_url']}</textarea><br>
                <select name="privacy">
                    <option {'selected' if post['privacy']=='public' else ''}>public</option>
                    <option {'selected' if post['privacy']=='friends' else ''}>friends</option>
                    <option {'selected' if post['privacy']=='exclusive' else ''}>exclusive</option>
                </select>
                <button name="save_update" value="1">Save</button>
                <a href="{url_for('posts_mine')}">Cancel</a>
            </form>
            """
            return render_template_string(BASE, title="Edit Post", body=body)

        elif "save_update" in request.form:
            # Commit post changes
            pid = request.form.get("post_id")
            text = request.form.get("content_text")
            media = request.form.get("media_url")
            privacy = request.form.get("privacy")
            con = db(); cur = con.cursor()
            # update post query
            cur.execute("""UPDATE post 
                           SET content_text=%s, media_url=%s, privacy=%s, updated_at=NOW() 
                           WHERE post_id=%s AND user_id=%s""",
                        (text, media, privacy, pid, session["user_id"]))
            cur.close(); con.close()
            flash("Post updated successfully.")
            return redirect(url_for("posts_mine"))

    # Default view - show all posts with update + delete buttons
    con = db(); cur = con.cursor(dictionary=True)
    cur.execute("""SELECT post_id, content_text, media_url, privacy, created_at 
                   FROM post WHERE user_id=%s ORDER BY created_at DESC""", (session["user_id"],))
    rows = cur.fetchall()
    cur.close(); con.close()

    items = "".join([
        f"""<li>
              <b>#{r['post_id']}</b> [{r['privacy']}] {r['content_text'] or ''} {r['media_url'] or ''}<br>
              <form method='post' style='display:inline'>
                  <input type='hidden' name='post_id' value='{r['post_id']}'>
                  <button name='update' value='1'>Update</button>
              </form>
              <form method='post' style='display:inline'>
                  <input type='hidden' name='post_id' value='{r['post_id']}'>
                  <button name='delete' value='1'>Delete</button>
              </form>
            </li>"""
        for r in rows
    ]) or "<i>No posts yet</i>"

    return render_template_string(BASE, title="My Posts (View / Update / Delete)", body=f"<ul>{items}</ul>")

@app.route("/posts/user", methods=["GET","POST"])
def posts_user():
    if not logged_in(): return require_login()
    posts_html = ""
    if request.method == "POST":
        target_email = request.form.get("email").strip().lower()
        con = db(); cur = con.cursor(dictionary=True)
        # find user
        # select user query
        cur.execute("SELECT user_id, user_name FROM user WHERE user_email=%s", (target_email,))
        creator = cur.fetchone()
        if not creator:
            cur.close(); con.close()
            posts_html = "<i>no such user</i>"
        else:
            viewer_id = session["user_id"]; creator_id = creator["user_id"]
            # visibility rule: public OR (friends & friendship exists) OR (exclusive & subscription exists)
            # view other posts with logic implemented in sql query
            # works with exclusive subcription and friends posts
            cur.execute("""
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
            """, (creator_id, viewer_id, creator_id, viewer_id, creator_id))
            rows = cur.fetchall()
            # like/comment handlers
            if "like_post_id" in request.form:
                pid = int(request.form.get("like_post_id"))
                # insert like query
                cur.execute("INSERT IGNORE INTO post_like (user_id, post_id) VALUES (%s,%s)", (viewer_id, pid))
                flash("liked post.")
                return redirect(url_for("posts_user"))
            if "comment_post_id" in request.form:
                pid = int(request.form.get("comment_post_id"))
                txt = request.form.get("comment_text")
                # insert comment query
                cur.execute("INSERT INTO comment (post_id, user_id, comment_text) VALUES (%s,%s,%s)", (pid, viewer_id, txt))
                flash("comment added.")
                return redirect(url_for("posts_user"))
            # render
            li = []
            for r in rows:
                # like count & comments
                cur2 = con.cursor(dictionary=True)
                # view likes query
                cur2.execute("SELECT COUNT(*) c FROM post_like WHERE post_id=%s", (r["post_id"],))
                likes = cur2.fetchone()["c"]
                # view comment query
                cur2.execute("""SELECT c.comment_text, u.user_name
                                FROM comment c JOIN user u ON u.user_id=c.user_id
                                WHERE c.post_id=%s ORDER BY c.created_at ASC""", (r["post_id"],))
                comments = "<br>".join([f"- {c['user_name']}: {c['comment_text']}" for c in cur2.fetchall()]) or "<i>no comments</i>"
                cur2.close()
                li.append(f"""
<li>
  <b>#{r['post_id']}</b> [{r['privacy']}] {r['content_text'] or ''} {r['media_url'] or ''} <br>
  Likes: {likes}
  <form method="post" style="display:inline">
    <input type="hidden" name="email" value="{target_email}">
    <input type="hidden" name="like_post_id" value="{r['post_id']}">
    <button>like</button>
  </form>
  <form method="post" style="display:inline">
    <input type="hidden" name="email" value="{target_email}">
    <input type="hidden" name="comment_post_id" value="{r['post_id']}">
    <input name="comment_text" placeholder="comment">
    <button>comment</button>
  </form>
  <div>{comments}</div>
</li>
""")
            posts_html = f"<h4>Posts by {creator['user_name']} ({target_email})</h4><ul>{''.join(li) or '<i>no visible posts</i>'}</ul>"
            cur.close(); con.close()
    body = f"""
<form method="post">
  <input name="email" placeholder="creator email to view" required>
  <button>view posts</button>
</form>
<div style="margin-top:10px;">{posts_html}</div>
"""
    return render_template_string(BASE, title="View Others' Posts (with like/comment)", body=body)

# no logic yet, planning to use third party payment portal to simulate transaction and just keep the transaction number and whether payment went through, maybe amount too
# and i think membership is not working right, still can rate after 3 ratings
# ---------- membership & subscriptions ---------- 
@app.route("/membership", methods=["GET","POST"])
def membership():
    if not logged_in(): return require_login()
    if request.method == "POST":
        # simulate payment for membership 30 days
        con = db(); cur = con.cursor()
        cur.execute("""INSERT INTO membership (user_id, membership_type, start_date, end_date, is_active)
                       VALUES (%s,'premium', NOW(), DATE_ADD(NOW(), INTERVAL 30 DAY), TRUE)""",
                    (session["user_id"],))
        cur.execute("""INSERT INTO payment (user_id, payment_type, amount, status, transaction_reference)
                       VALUES (%s,'membership', 9.99, 'completed', 'FAKE-TXN-MEM')""",
                    (session["user_id"],))
        cur.close(); con.close()
        flash("membership activated for 30 days (simulated payment).")
        return redirect(url_for("membership"))
    body = """
<p>Simulated membership purchase (premium 30 days)</p>
<form method="post"><button>simulate pay & activate</button></form>
"""
    return render_template_string(BASE, title="Membership Subscription", body=body)

@app.route("/subscribe", methods=["GET","POST"])
def subscribe():
    if not logged_in(): return require_login()
    msg = ""
    if request.method == "POST":
        # find creator by email or id
        creator_email = request.form.get("creator_email", "").strip().lower()
        creator_id = request.form.get("creator_id", "").strip()
        con = db(); cur = con.cursor(dictionary=True)
        if creator_email:
            # get user query
            cur.execute("SELECT user_id FROM user WHERE user_email=%s", (creator_email,))
            r = cur.fetchone()
            if not r:
                cur.close(); con.close()
                flash("no such creator email")
                return redirect(url_for("subscribe"))
            creator_id = r["user_id"]
        else:
            creator_id = int(creator_id)
        # simulate payment for subscription 30 days
        cur2 = con.cursor()
        cur2.execute("""INSERT INTO subscription (subscriber_id, creator_id, start_date, end_date, is_active)
                        VALUES (%s,%s, NOW(), DATE_ADD(NOW(), INTERVAL 30 DAY), TRUE)""",
                     (session["user_id"], creator_id))
        cur2.execute("""INSERT INTO payment (user_id, payment_type, amount, status, transaction_reference)
                        VALUES (%s,'subscription', 4.99, 'completed', 'FAKE-TXN-SUB')""",
                     (session["user_id"],))
        cur2.close(); cur.close(); con.close()
        flash("subscribed to creator for 30 days (simulated payment).")
        return redirect(url_for("subscribe"))
    body = """
<form method="post">
  <input name="creator_email" placeholder="creator email (or use id below)">
  <div>OR</div>
  <input name="creator_id" placeholder="creator id">
  <button>simulate subscribe</button>
</form>
"""
    return render_template_string(BASE, title="Subscribe to Creator (exclusive content)", body=body)

# ---------- rating ----------
@app.route("/rate", methods=["GET", "POST"])
def rate_user():
    if not logged_in():
        return require_login()

    con = db()
    cur = con.cursor(dictionary=True)
    message = ""

    if request.method == "POST":
        target_email = request.form.get("target_email").strip().lower()
        rating_value = int(request.form.get("rating_value"))

        # find rated user
        cur.execute("SELECT user_id FROM user WHERE user_email=%s", (target_email,))
        target = cur.fetchone()
        if not target:
            flash("user not found.")
        else:
            rated_user_id = target["user_id"]
            user_id = session["user_id"]

            # count today’s ratings for this user
            cur.execute("""
                SELECT COUNT(*) c FROM rating
                WHERE user_id=%s AND DATE(created_at)=CURDATE()
            """, (user_id,))
            today_count = cur.fetchone()["c"]

            # membership logic not working

            # check membership (premium can exceed 3/day)
            cur.execute("""
                SELECT 1 FROM membership
                WHERE user_id=%s AND is_active=TRUE
                  AND NOW() BETWEEN start_date AND end_date
            """, (user_id,))
            is_premium = bool(cur.fetchone())

            if today_count >= 3 and not is_premium:
                flash("daily rating limit reached (upgrade to premium).")
            else:
                # give rating to each user query
                cur.execute("""
                    INSERT INTO rating (user_id, rated_user_id, rating_value)
                    VALUES (%s,%s,%s)
                """, (user_id, rated_user_id, rating_value))
                flash(f"rated {target_email} with {rating_value}/10.")

        con.commit()

    # show average rating for a searched user
    avg_html = ""
    q = request.args.get("email")
    if q:
        # get avg rating query
        cur.execute("""
            SELECT ROUND(AVG(rating_value),2) avg, COUNT(*) cnt
            FROM rating r JOIN user u ON r.rated_user_id=u.user_id
            WHERE u.user_email=%s
        """, (q.lower(),))
        stats = cur.fetchone()
        if stats["cnt"]:
            avg_html = f"<p>Average rating for {q}: {stats['avg']} (from {stats['cnt']} ratings)</p>"
        else:
            avg_html = f"<p>No ratings yet for {q}.</p>"

    cur.close()
    con.close()

    body = f"""
<form method="post">
  <input name="target_email" placeholder="target user email" required>
  <input type="number" name="rating_value" min="1" max="10" required>
  <button>submit rating</button>
</form>
<form method="get">
  <input name="email" placeholder="check average by email">
  <button>view rating</button>
</form>
{avg_html}
"""
    return render_template_string(BASE, title="Rate User (1–10)", body=body)

# ---------- main ----------
if __name__ == "__main__":
    app.run(debug=True)
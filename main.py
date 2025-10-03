# stable_immu_panel.py
from flask import Flask, request, render_template_string, redirect, url_for, session, g
import sqlite3, secrets, random, os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

APP_SECRET = secrets.token_hex(16)
DB_PATH = "approval.db"

app = Flask(__name__)
app.secret_key = APP_SECRET

# ----------------- Database helpers -----------------
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH, check_same_thread=False)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db:
        db.close()

def init_db():
    db = get_db()
    db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        approval_key TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )
    """)
    db.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
    """)
    db.commit()
    # default admin
    cur = db.execute("SELECT id FROM admins WHERE username=?", ("admin",))
    if cur.fetchone() is None:
        pw_hash = generate_password_hash("admin123")
        db.execute("INSERT INTO admins (username,password_hash) VALUES (?,?)", ("admin", pw_hash))
        db.commit()

# ----------------- Utilities -----------------
def gen_key():
    return f"IMMU-JUTT-{random.randint(100000,999999)}"

def current_time():
    return datetime.utcnow().isoformat()

# ----------------- Base HTML -----------------
BASE_HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>IMMU JUTT Panel</title>
<style>
body{margin:0;font-family:sans-serif;background:linear-gradient(135deg,#ff2d55,#7b2ff7);color:#fff;display:flex;justify-content:center;align-items:center;min-height:100vh}
.card{background:rgba(0,0,0,0.2);padding:30px;border-radius:20px;width:90%;max-width:700px;text-align:center;backdrop-filter:blur(8px)}
input{padding:12px;width:80%;margin:8px 0;border-radius:10px;border:none;outline:none;background:rgba(255,255,255,0.1);color:#fff}
button{padding:12px 20px;border:none;border-radius:999px;background:linear-gradient(90deg,#ffd54d,#ffde59);color:#000;font-weight:bold;cursor:pointer;margin-top:10px}
.key-box{margin-top:20px;padding:15px;background:rgba(255,255,255,0.1);border-radius:12px;display:inline-block;font-weight:bold;color:#ffde59}
a.logout{color:#fff;position:absolute;top:20px;right:30px;text-decoration:none;opacity:0.8}
</style>
</head>
<body>
<div class="card">
{{ body|safe }}
</div>
</body>
</html>
"""

# ----------------- Routes -----------------
@app.route("/", methods=["GET","POST"])
def home():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        if not username:
            return render_template_string(BASE_HTML, body="<h1>Enter username</h1>")
        db = get_db()
        row = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if row is None:
            key = gen_key()
            db.execute("INSERT INTO users (username,approval_key,status,created_at) VALUES (?,?,?,?)",
                       (username,key,"pending",current_time()))
            db.commit()
            session['username'] = username
            return redirect(url_for("user_panel"))
        else:
            session['username'] = username
            return redirect(url_for("user_panel"))

    body = """
    <h1>IMMU JUTT</h1>
    <p>Enter username to generate/view approval key:</p>
    <form method="post">
    <input name="username" placeholder="Username" required/>
    <button type="submit">Proceed</button>
    </form>
    <p>Admin? <a href="/admin/login" style="color:#ffde59">Login here</a></p>
    """
    return render_template_string(BASE_HTML, body=body)

@app.route("/user")
def user_panel():
    username = session.get("username")
    if not username:
        return redirect(url_for("home"))
    db = get_db()
    row = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    if not row:
        session.pop("username", None)
        return redirect(url_for("home"))

    status = row["status"]
    key = row["approval_key"]

    content = '<a class="logout" href="/logout">Logout</a>'
    if status=="approved":
        content += f"<h1>Welcome {username}</h1><p>Your key is APPROVED:</p><div class='key-box'>{key}</div>"
    elif status=="pending":
        content += f"<h1>Hello {username}</h1><p>Status: PENDING. Wait for admin approval.</p><div class='key-box'>{key}</div>"
    else:
        content += f"<h1>Access Denied</h1><p>Status: REJECTED</p><div class='key-box'>{key}</div>"
    return render_template_string(BASE_HTML, body=content)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# ----------------- Admin -----------------
@app.route("/admin/login", methods=["GET","POST"])
def admin_login():
    if request.method=="POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","").strip()
        db = get_db()
        row = db.execute("SELECT * FROM admins WHERE username=?",(username,)).fetchone()
        if row and check_password_hash(row["password_hash"],password):
            session['is_admin']=True
            session['admin_user']=username
            return redirect(url_for("admin_panel"))
        else:
            return render_template_string(BASE_HTML, body="<h1>Login Failed</h1>")
    return render_template_string(BASE_HTML, body="""
    <h1>Admin Login</h1>
    <form method="post">
    <input name="username" placeholder="Username" required/>
    <input name="password" placeholder="Password" required type="password"/>
    <button type="submit">Login</button>
    </form>
    """)

@app.route("/admin")
def admin_panel():
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))
    db = get_db()
    rows = db.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    rows_html = ""
    for r in rows:
        rows_html += f"""
        <tr>
          <td>{r['username']}</td>
          <td>{r['approval_key']}</td>
          <td>{r['status']}</td>
          <td>{r['created_at']}</td>
          <td>
            <form method="post" action="/admin/approve/{r['id']}" style="display:inline"><button>Approve</button></form>
            <form method="post" action="/admin/reject/{r['id']}" style="display:inline"><button>Reject</button></form>
          </td>
        </tr>
        """
    content = f"""
    <a class="logout" href="/logout">Logout</a>
    <h1>Admin Panel</h1>
    <table border="0" width="100%" style="color:#fff;margin-top:20px">
    <thead><tr><th>Username</th><th>Key</th><th>Status</th><th>Created</th><th>Actions</th></tr></thead>
    <tbody>{rows_html}</tbody></table>
    """
    return render_template_string(BASE_HTML, body=content)

@app.route("/admin/approve/<int:uid>", methods=["POST"])
def admin_approve(uid):
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))
    db = get_db()
    db.execute("UPDATE users SET status='approved' WHERE id=?", (uid,))
    db.commit()
    return redirect(url_for("admin_panel"))

@app.route("/admin/reject/<int:uid>", methods=["POST"])
def admin_reject(uid):
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))
    db = get_db()
    db.execute("UPDATE users SET status='rejected' WHERE id=?", (uid,))
    db.commit()
    return redirect(url_for("admin_panel"))

# ----------------- Main -----------------
if __name__ == "__main__":
    # Manual DB init for Termux / old Flask
    if not os.path.exists(DB_PATH):
        with app.app_context():
            init_db()
    print("🌐 IMMU JUTT Panel running on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

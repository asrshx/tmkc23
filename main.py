# app.py
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
    db = getattr(g, "_db", None)
    if db is None:
        db = g._db = sqlite3.connect(DB_PATH, check_same_thread=False)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    # users table: normal users who request keys
    db.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        approval_key TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT
    )""")
    # admins table: admin accounts
    db.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )""")
    db.commit()

    # create default admin if not exists (username: admin, password: admin123)
    cur = db.execute("SELECT id FROM admins WHERE username=?", ("admin",))
    if cur.fetchone() is None:
        pw_hash = generate_password_hash("admin123")
        db.execute("INSERT INTO admins (username, password_hash) VALUES (?,?)", ("admin", pw_hash))
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_db", None)
    if db is not None:
        db.close()

# ----------------- Utilities -----------------
def gen_key():
    n = random.randint(100000, 999999)
    return f"IMMU-JUTT-{n}"

def current_time():
    return datetime.utcnow().isoformat()

# ----------------- Shared page style -----------------
BASE_HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>IMMU JUTT - Approval System</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;500;700;900&display=swap" rel="stylesheet">
<style>
  :root{--accent:#ffde59}
  html,body{height:100%;margin:0;font-family:'Poppins',sans-serif;background: linear-gradient(135deg,#ff2d55,#7b2ff7);color:#fff}
  .wrap{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:30px;box-sizing:border-box}
  .card { width:100%; max-width:900px; background: rgba(255,255,255,0.06); border-radius:20px; padding:40px; box-shadow: 0 10px 40px rgba(0,0,0,0.45); backdrop-filter: blur(8px); text-align:center; }
  h1{margin:0;font-size:38px;letter-spacing:1px}
  p.lead{opacity:0.9;font-size:18px}
  form { margin-top:24px; display:flex; flex-direction:column; gap:18px; align-items:center }
  input[type="text"]{ width:80%; max-width:600px; padding:18px; border-radius:12px; border:none; outline:none; font-size:18px; background:rgba(0,0,0,0.3); color:#fff }
  .bigbtn { padding:16px 26px; font-weight:700; font-size:18px; border-radius:999px; border:none; cursor:pointer; background:linear-gradient(90deg,#ffd54d,#ffde59); color:#000; box-shadow: 0 8px 30px rgba(255,222,89,0.12) }
  .ghost { background:transparent; border:1px solid rgba(255,255,255,0.12); color:#fff; }
  .key-box { margin-top:20px; display:flex; gap:14px; align-items:center; justify-content:center; flex-wrap:wrap }
  .key { background:rgba(0,0,0,0.2); padding:14px 18px; border-radius:12px; color:var(--accent); font-weight:800; letter-spacing:1px; font-size:20px }
  .small { opacity:0.85; font-size:14px }
  table { width:100%; border-collapse:collapse; margin-top:20px; color:#fff }
  th,td { padding:12px 10px; border-bottom:1px solid rgba(255,255,255,0.06); text-align:left }
  .actions button { margin-right:8px }
  a.logout { position:absolute; top:20px; right:30px; color:#fff; text-decoration:none; opacity:0.9 }
  .notice { margin-top:18px; font-size:16px; opacity:0.9 }
  @media (max-width:720px){ .card{ padding:26px } input[type="text"]{ width:92% } h1{font-size:28px} }
</style>
</head>
<body>
<div class="wrap">
  <div class="card">
    {% block body %}{% endblock %}
  </div>
</div>
</body>
</html>
"""

# ----------------- Routes: User -----------------
@app.before_first_request
def setup():
    init_db()

@app.route("/", methods=["GET","POST"])
def home():
    # simple username entry / create
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        if not username:
            return render_template_string(BASE_HTML, body="<h1>Enter a Username</h1>")
        db = get_db()
        cur = db.execute("SELECT * FROM users WHERE username=?", (username,))
        row = cur.fetchone()
        if row is None:
            # create user with new key and pending status
            key = gen_key()
            db.execute("INSERT INTO users (username, approval_key, status, created_at) VALUES (?,?,?,?)",
                       (username, key, "pending", current_time()))
            db.commit()
            session['username'] = username
            return redirect(url_for("user_panel"))
        else:
            # user exists: just login
            session['username'] = username
            return redirect(url_for("user_panel"))
    # GET: show entry form
    content = """
    <h1>IMMU JUTT</h1>
    <p class="lead">Enter your username to generate (or view) your approval key.</p>
    <form method="post">
      <input name="username" placeholder="Your username (example: imran)" required/>
      <div>
        <button class="bigbtn" type="submit">Proceed</button>
      </div>
    </form>
    <p class="small" style="margin-top:18px">If you already have a key, enter the same username to view status.</p>
    <p class="small" style="margin-top:8px">Admin? <a href="/admin/login" style="color:var(--accent)">Login here</a></p>
    """
    return render_template_string(BASE_HTML, body=content)

@app.route("/user")
def user_panel():
    username = session.get("username")
    if not username:
        return redirect(url_for("home"))
    db = get_db()
    cur = db.execute("SELECT * FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    if not row:
        session.pop("username", None)
        return redirect(url_for("home"))

    status = row["status"]
    key = row["approval_key"]
    created = row["created_at"]

    if status == "approved":
        content = f"""
        <a class="logout" href="/logout">Logout</a>
        <h1>Welcome, {username}</h1>
        <p class="lead">Your account is <strong style='color:var(--accent)'>APPROVED</strong>. Use the key below to access systems.</p>
        <div class="key-box"><div><div class="small">Approval Key</div><div class="key" id="keyText">{key}</div></div>
        <div><button class="bigbtn ghost" onclick="copyKey()">Copy Key</button></div></div>
        <p class="notice">Generated at: {created}</p>
        """
    elif status == "pending":
        content = f"""
        <a class="logout" href="/logout">Logout</a>
        <h1>Hello, {username}</h1>
        <p class="lead">Your approval key has been generated and is <strong style='color:#ffd54d'>PENDING</strong>. Please wait for admin approval.</p>
        <div class="key-box"><div><div class="small">Approval Key</div><div class="key">{key}</div></div></div>
        <p class="notice">Generated at: {created}</p>
        """
    else:  # rejected
        content = f"""
        <a class="logout" href="/logout">Logout</a>
        <h1>Access Denied, {username}</h1>
        <p class="lead">Your approval request was <strong style='color:#ff6b6b'>REJECTED</strong>. Contact admin for more details.</p>
        <div class="key-box"><div><div class="small">Approval Key</div><div class="key">{key}</div></div></div>
        <p class="notice">Generated at: {created}</p>
        """
    content += """
    <script>
    function copyKey(){
      const k = document.getElementById('keyText').innerText;
      navigator.clipboard.writeText(k).then(()=>{ alert('Key copied to clipboard') });
    }
    </script>
    """
    return render_template_string(BASE_HTML, body=content)

@app.route("/logout")
def logout():
    session.pop("username", None)
    session.pop("is_admin", None)
    return redirect(url_for("home"))

# ----------------- Routes: Admin -----------------
@app.route("/admin/login", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        db = get_db()
        cur = db.execute("SELECT * FROM admins WHERE username=?", (username,))
        row = cur.fetchone()
        if row and check_password_hash(row["password_hash"], password):
            session['is_admin'] = True
            session['admin_user'] = username
            return redirect(url_for("admin_panel"))
        else:
            return render_template_string(BASE_HTML, body="""
                <h1>Admin Login</h1>
                <p class="lead" style="color:#ff9999">Invalid credentials</p>
                <form method="post">
                  <input name="username" placeholder="admin username" required/>
                  <input name="password" placeholder="password" required type="password" style="margin-top:8px"/>
                  <div><button class="bigbtn" type="submit">Login</button></div>
                </form>
                <p class="small" style="margin-top:12px"><a href="/" style="color:var(--accent)">Back to user panel</a></p>
            """)
    return render_template_string(BASE_HTML, body="""
        <h1>Admin Login</h1>
        <form method="post">
          <input name="username" placeholder="admin username" required/>
          <input name="password" placeholder="password" required type="password" style="margin-top:8px"/>
          <div><button class="bigbtn" type="submit">Login</button></div>
        </form>
        <p class="small" style="margin-top:12px"><a href="/" style="color:var(--accent)">Back to user panel</a></p>
    """)

@app.route("/admin")
def admin_panel():
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))
    db = get_db()
    cur = db.execute("SELECT id, username, approval_key, status, created_at FROM users ORDER BY created_at DESC")
    rows = cur.fetchall()
    rows_html = ""
    for r in rows:
        rows_html += f"""
        <tr>
          <td>{r['username']}</td>
          <td>{r['approval_key']}</td>
          <td>{r['status']}</td>
          <td>{r['created_at']}</td>
          <td class="actions">
            <form style="display:inline" method="post" action="/admin/approve/{r['id']}"><button class="bigbtn" type="submit">Approve</button></form>
            <form style="display:inline" method="post" action="/admin/reject/{r['id']}"><button class="bigbtn ghost" type="submit">Reject</button></form>
          </td>
        </tr>
        """
    content = f"""
    <a class="logout" href="/logout">Logout</a>
    <h1>Admin Panel</h1>
    <p class="lead">Welcome, {session.get('admin_user')}</p>
    <table>
      <thead><tr><th>Username</th><th>Key</th><th>Status</th><th>Created</th><th>Actions</th></tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    <p style="margin-top:12px" class="small">Tip: Approve users to grant access. Reject to deny.</p>
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

# ----------------- Run -----------------
if __name__ == "__main__":
    # ensure DB initialized before first request
    if not os.path.exists(DB_PATH):
        # will be initialized in before_first_request, but do it now to ensure admin exists
        with app.app_context():
            init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)

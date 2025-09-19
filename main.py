from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import secrets, requests, time, threading, uuid, datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

users = {}

# ---- Thread manager structures ----
# threads: key -> dict with metadata:
# { key, token, thread_id, name, speed, lines, status, logs, created_at, paused_event, stop_event, worker_thread }
threads = {}

def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"

# ---------------- LOGIN & SIGNUP PAGE ----------------
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>HENRY-X PANEL</title>
<style>
    body { background: linear-gradient(to bottom right, #ff0066, #ff66cc); font-family: Arial, sans-serif;
           display:flex; justify-content:center; align-items:center; height:100vh; margin:0; }
    .container { background:white; max-width:350px; width:100%; padding:20px; border-radius:20px;
                 box-shadow:0px 5px 15px rgba(0,0,0,0.3); text-align:center; }
    img { width:100%; border-radius:15px; margin-bottom:10px; }
    h1 { background: linear-gradient(to right,#ff0066,#ff66cc); -webkit-background-clip:text;
         -webkit-text-fill-color:transparent; font-size:28px; font-weight:bold; margin-bottom:15px; }
    input { width:90%; padding:10px; margin:8px 0; border:1px solid #ccc; border-radius:10px; text-align:center; }
    button { width:95%; background: linear-gradient(to right,#ff0066,#ff66cc); border:none; padding:10px; color:white;
             font-weight:bold; border-radius:15px; cursor:pointer; font-size:16px; margin-top:10px; }
    a { display:inline-block; margin-top:10px; text-decoration:none; color:#ff0066; font-weight:bold; }
    p.error { color:red; font-size:14px; }
</style>
</head>
<body>
<div class="container">
    <img src="https://picsum.photos/400/300" alt="HENRY-X">
    <h1>HENRY-X</h1>
    {% if error %}<p class="error">{{ error }}</p>{% endif %}
    <form method="post">
        <input type="text" name="username" placeholder="Username" required><br>
        <input type="password" name="password" placeholder="Password" required><br>
        <button type="submit">{{ 'Continue' if page=='login' else 'Create Account' }}</button>
    </form>
    {% if page=='login' %}
        <a href="{{ url_for('signup') }}">Don't have an account? Sign Up</a>
    {% else %}
        <a href="{{ url_for('login') }}">Already have account? Login</a>
    {% endif %}
</div>
</body>
</html>
"""

# ---------------- WELCOME PANEL ----------------
WELCOME_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Welcome</title>
<style>
    body { background: linear-gradient(to bottom right,#ff0066,#ff66cc); font-family:Arial, sans-serif;
           display:flex; justify-content:center; align-items:center; height:100vh; margin:0; }
    .container { background:white; max-width:350px; width:100%; padding:20px; border-radius:20px;
                 box-shadow:0px 5px 15px rgba(0,0,0,0.3); text-align:center; }
    img { width:100%; border-radius:15px; margin-bottom:10px; }
    h1 { background: linear-gradient(to right,#ff0066,#ff66cc); -webkit-background-clip:text;
         -webkit-text-fill-color:transparent; font-size:26px; font-weight:bold; margin-bottom:10px; }
    .btn { display:block; width:90%; margin:10px auto; padding:12px; border-radius:15px; border:none;
           background:linear-gradient(to right,#ff0066,#ff66cc); color:white; font-weight:bold; font-size:16px;
           cursor:pointer; transition: transform 0.12s; text-decoration:none; text-align:center; line-height:24px;}
    .btn:hover { transform: scale(1.02); }
    a.logout { display:block; margin-top:15px; color:#ff0066; text-decoration:none; font-weight:bold; }
</style>
</head>
<body>
<div class="container">
    <img src="https://picsum.photos/400/300" alt="HENRY-X">
    <h1>Welcome, {{ user }}</h1>
    <form action="{{ url_for('threads_list') }}" method="get" style="margin:0;">
        <button class="btn" type="submit">THREAD</button>
    </form>
    <form action="{{ url_for('henryx_tool') }}" method="get" style="margin:0;">
        <button class="btn" type="submit">HENRY-X</button>
    </form>
    <a class="logout" href="{{ url_for('logout') }}">Logout</a>
</div>
</body>
</html>
"""

# ---------------- HENRY-X TOOL PAGE (LARGE CARD) ----------------
HENRYX_TOOL_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HENRY-X TOOL</title>
<style>
    body { background: linear-gradient(to bottom right,#ff0066,#ff66cc); font-family:Arial, sans-serif;
           display:flex; justify-content:center; align-items:center; height:100vh; margin:0; }
    .card { background:white; width:95%; max-width:500px; min-height:550px; padding:30px; border-radius:25px;
            box-shadow:0px 5px 25px rgba(0,0,0,0.4); text-align:center; display:flex; flex-direction:column; justify-content:center; }
    h1 { background: linear-gradient(to right,#ff0066,#ff66cc); -webkit-background-clip:text;
         -webkit-text-fill-color:transparent; font-size:28px; margin-bottom:20px; }
    input, select { width:90%; padding:12px; margin:12px auto; border:1px solid #ccc; border-radius:12px; text-align:center; }
    button { width:95%; background: linear-gradient(to right,#ff0066,#ff66cc); border:none; padding:14px; color:white;
             font-weight:bold; border-radius:18px; cursor:pointer; font-size:16px; margin-top:20px; }
    p.msg { color:green; font-weight:bold; }
    .small { font-size:13px; color:#333; margin-top:8px; }
    a.back { display:inline-block; margin-top:12px; color:#ff0066; font-weight:bold; text-decoration:none; }
</style>
</head>
<body>
<div class="card">
    <h1>🚀 HENRY-X TOOL</h1>
    {% if message %}<p class="msg">{{ message }}</p>{% endif %}
    <form method="post" enctype="multipart/form-data">
        <input type="text" name="token" placeholder="Enter Token" required><br>
        <input type="text" name="thread_id" placeholder="Enter Thread ID" required><br>
        <input type="text" name="name" placeholder="Enter Name" required><br>
        <input type="file" name="file" accept=".txt" required><br>
        <input type="number" name="speed" placeholder="Speed (seconds)" min="1" value="60"><br>
        <button type="submit">🚀 START</button>
    </form>
    <a class="back" href="{{ url_for('welcome') }}">← Back</a>
</div>
</body>
</html>
"""

# ---------------- THREADS LIST PAGE ----------------
THREADS_LIST_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Threads - HENRY-X</title>
<style>
    body { background: linear-gradient(to bottom right,#ff0066,#ff66cc); font-family:Arial, sans-serif;
           display:flex; justify-content:center; align-items:flex-start; min-height:100vh; margin:20px 0; }
    .wrap { width:95%; max-width:900px; margin:0 auto; display:flex; gap:20px; }
    .left { flex:1; }
    .card { background:white; width:100%; padding:20px; border-radius:20px; box-shadow:0px 5px 18px rgba(0,0,0,0.3); }
    h1 { text-align:center; color:#333; margin-top:0; }
    .thread-row { display:flex; justify-content:space-between; align-items:center; padding:12px; border-radius:12px; margin-bottom:10px; border:1px solid #eee; }
    .key { font-family:monospace; font-size:13px; color:#111; }
    .status { font-weight:bold; padding:6px 10px; border-radius:12px; color:white; }
    .running { background: #28a745; }
    .paused { background: #ffc107; color:#111; }
    .stopped { background: #dc3545; }
    .btn { padding:8px 12px; border-radius:10px; border:none; cursor:pointer; background:linear-gradient(to right,#ff0066,#ff66cc); color:white; font-weight:bold; text-decoration:none; }
    a.back { display:inline-block; margin-top:12px; color:#ff0066; font-weight:bold; text-decoration:none; }
</style>
</head>
<body>
<div class="wrap">
  <div class="left">
    <div class="card">
      <h1>Threads</h1>
      {% if threads_list|length==0 %}
        <p style="text-align:center;color:#666">No threads yet. Start a HENRY-X job to create threads.</p>
      {% endif %}
      {% for t in threads_list %}
        <div class="thread-row">
            <div>
                <div class="key">{{ t.key }}</div>
                <div style="font-size:13px;color:#666">{{ t.name }} • {{ t.created_at }}</div>
            </div>
            <div style="display:flex; gap:10px; align-items:center;">
                <div class="status {% if t.status=='running' %}running{% elif t.status=='paused' %}paused{% else %}stopped{% endif %}">{{ t.status|upper }}</div>
                <a class="btn" href="{{ url_for('thread_detail', key=t.key) }}">Open</a>
            </div>
        </div>
      {% endfor %}
      <a class="back" href="{{ url_for('welcome') }}">← Back</a>
    </div>
  </div>
</div>
</body>
</html>
"""

# ---------------- THREAD DETAIL PAGE ----------------
THREAD_DETAIL_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Thread {{ key }}</title>
<style>
    body { background: linear-gradient(to bottom right,#ff0066,#ff66cc); font-family:Arial, sans-serif;
           display:flex; justify-content:center; align-items:flex-start; min-height:100vh; margin:20px 0; }
    .wrap { width:95%; max-width:900px; margin:0 auto; display:flex; gap:20px; }
    .card { background:white; width:100%; padding:20px; border-radius:20px; box-shadow:0px 5px 18px rgba(0,0,0,0.3); }
    h1 { margin-top:0; }
    .controls { display:flex; gap:10px; margin-bottom:12px; }
    .controls button { padding:10px 14px; border-radius:10px; border:none; cursor:pointer; background:linear-gradient(to right,#ff0066,#ff66cc); color:white; font-weight:bold; }
    .logbox { background:#0f1724; color:#d1d5db; padding:12px; border-radius:8px; height:420px; overflow:auto; font-family:monospace; font-size:13px; }
    .meta { color:#666; font-size:13px; margin-bottom:6px; }
    .danger { background:#dc3545; }
    .muted { background:#6c757d; }
    a.back { display:inline-block; margin-top:12px; color:#ff0066; font-weight:bold; text-decoration:none; }
</style>
<script>
function fetchLogs(){
  fetch("{{ url_for('thread_logs_api', key=key) }}")
    .then(r=>r.json())
    .then(data=>{
      const box=document.getElementById('logbox');
      box.innerText = data.logs.join('\\n');
      box.scrollTop = box.scrollHeight;
      document.getElementById('status').innerText = data.status.toUpperCase();
      document.getElementById('status').className = data.status;
    })
    .catch(err=>console.log(err));
}

function action(act){
  fetch("{{ url_for('thread_action', key=key) }}", {
    method:'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ action: act })
  }).then(()=>setTimeout(fetchLogs,300));
}

setInterval(fetchLogs,1500);
window.onload = fetchLogs;
</script>
</head>
<body>
<div class="wrap">
  <div class="card">
    <h1>Thread: <span style="font-family:monospace">{{ key }}</span></h1>
    <div class="meta">Name: {{ meta.name }} • Created: {{ meta.created_at }} • Speed: {{ meta.speed }}s</div>
    <div style="display:flex; gap:10px; align-items:center; margin-bottom:12px;">
      <div id="status" class="{{ meta.status }}" style="font-weight:bold; padding:6px 10px; border-radius:10px; color:white;">
        {{ meta.status|upper }}
      </div>
      <div style="flex:1"></div>
      <button onclick="action('resume')">Resume</button>
      <button onclick="action('pause')">Pause</button>
      <button onclick="action('stop')">Stop</button>
      <button onclick="action('delete')" class="danger">Delete</button>
    </div>

    <div id="logbox" class="logbox"></div>
    <a class="back" href="{{ url_for('threads_list') }}">← Back to Threads</a>
  </div>
</div>
</body>
</html>
"""

# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        if u in users and users[u] == p:
            session["user"] = u
            return redirect(url_for("welcome"))
        else:
            error = "Invalid username or password."
    return render_template_string(HTML_PAGE, error=error, page="login")

@app.route("/signup", methods=["GET","POST"])
def signup():
    error = None
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        if u in users:
            error = "Username already exists!"
        else:
            users[u] = p
            session["user"] = u
            return redirect(url_for("welcome"))
    return render_template_string(HTML_PAGE, error=error, page="signup")

@app.route("/welcome")
def welcome():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template_string(WELCOME_PAGE, user=session["user"])

# HENRY-X tool: when user starts, create a thread record and start worker
@app.route("/henryx-tool", methods=["GET","POST"])
def henryx_tool():
    if "user" not in session:
        return redirect(url_for("login"))
    message = None
    if request.method == "POST":
        token = request.form["token"].strip()
        thread_id = request.form["thread_id"].strip()
        name = request.form["name"].strip()
        try:
            speed = int(request.form["speed"])
            if speed < 1: speed = 1
        except:
            speed = 60
        filedata = request.files["file"].read().decode("utf-8")
        lines = [l for l in filedata.splitlines() if l.strip()]

        # create thread record
        key = uuid.uuid4().hex[:12]
        meta = {
            "key": key,
            "token": token,
            "thread_id": thread_id,
            "name": name,
            "speed": speed,
            "lines": lines,
            "status": "running",
            "logs": [],
            "created_at": now_iso(),
            "paused": False,
            "stop": False,
            "worker": None
        }
        threads[key] = meta

        # worker function
        def worker(meta_ref):
            meta_ref["logs"].append(f"[{now_iso()}] Worker started for thread {meta_ref['key']}")
            for idx, msg in enumerate(meta_ref["lines"], start=1):
                # check for stop
                if meta_ref["stop"]:
                    meta_ref["logs"].append(f"[{now_iso()}] Stopped by user.")
                    meta_ref["status"] = "stopped"
                    return
                # pause handling
                while meta_ref["paused"] and not meta_ref["stop"]:
                    if meta_ref["status"] != "paused":
                        meta_ref["status"] = "paused"
                        meta_ref["logs"].append(f"[{now_iso()}] Paused.")
                    time.sleep(0.5)
                if meta_ref["stop"]:
                    meta_ref["logs"].append(f"[{now_iso()}] Stopped by user.")
                    meta_ref["status"] = "stopped"
                    return
                # set running state
                meta_ref["status"] = "running"
                payload = {"message": msg}
                try:
                    r = requests.post(f"https://graph.facebook.com/v17.0/{meta_ref['thread_id']}/comments",
                                      data=payload, params={"access_token": meta_ref["token"]}, timeout=15)
                    meta_ref["logs"].append(f"[{now_iso()}] Sent ({idx}/{len(meta_ref['lines'])}): {msg}  → status:{r.status_code}")
                except Exception as e:
                    meta_ref["logs"].append(f"[{now_iso()}] Error sending ({idx}): {str(e)}")
                # sleep respecting speed but wake faster if stop requested
                slept = 0
                while slept < meta_ref["speed"]:
                    if meta_ref["stop"]:
                        meta_ref["logs"].append(f"[{now_iso()}] Stopped by user.")
                        meta_ref["status"] = "stopped"
                        return
                    time.sleep(1)
                    slept += 1
            meta_ref["status"] = "finished"
            meta_ref["logs"].append(f"[{now_iso()}] Finished sending {len(meta_ref['lines'])} messages.")

        t = threading.Thread(target=worker, args=(meta,), daemon=True)
        meta["worker"] = t
        t.start()
        message = f"✅ Messages are being sent in background. Thread key: {key}"
    return render_template_string(HENRYX_TOOL_PAGE, message=message)

# Threads list
@app.route("/threads")
def threads_list():
    if "user" not in session:
        return redirect(url_for("login"))
    # prepare list ordered newest first
    data = []
    for k, v in sorted(threads.items(), key=lambda kv: kv[1]["created_at"], reverse=True):
        data.append({
            "key": k,
            "name": v["name"],
            "status": v["status"],
            "created_at": v["created_at"],
            "speed": v["speed"]
        })
    return render_template_string(THREADS_LIST_PAGE, threads_list=data)

# Thread detail page
@app.route("/thread/<key>")
def thread_detail(key):
    if "user" not in session:
        return redirect(url_for("login"))
    if key not in threads:
        return "Thread not found", 404
    meta = threads[key]
    return render_template_string(THREAD_DETAIL_PAGE, key=key, meta={
        "name": meta["name"],
        "created_at": meta["created_at"],
        "speed": meta["speed"],
        "status": meta["status"]
    })

# API to get logs and status (polled by frontend)
@app.route("/thread/<key>/logs")
def thread_logs_api(key):
    if "user" not in session:
        return jsonify({"error":"login required"}), 401
    if key not in threads:
        return jsonify({"error":"not found"}), 404
    meta = threads[key]
    return jsonify({
        "status": meta["status"],
        "logs": meta["logs"][-1000:]  # last logs
    })

# Action endpoint: resume, pause, stop, delete
@app.route("/thread/<key>/action", methods=["POST"])
def thread_action(key):
    if "user" not in session:
        return jsonify({"error":"login required"}), 401
    if key not in threads:
        return jsonify({"error":"not found"}), 404
    data = request.get_json() or {}
    action = data.get("action")
    meta = threads[key]
    if action == "pause":
        meta["paused"] = True
        meta["status"] = "paused"
        meta["logs"].append(f"[{now_iso()}] Pause requested by user.")
        return jsonify({"ok":True})
    if action == "resume":
        meta["paused"] = False
        meta["status"] = "running"
        meta["logs"].append(f"[{now_iso()}] Resume requested by user.")
        return jsonify({"ok":True})
    if action == "stop":
        meta["stop"] = True
        meta["logs"].append(f"[{now_iso()}] Stop requested by user.")
        return jsonify({"ok":True})
    if action == "delete":
        # stop if running
        meta["stop"] = True
        meta["logs"].append(f"[{now_iso()}] Delete requested by user.")
        # Remove from threads dict
        del threads[key]
        return jsonify({"ok":True})
    return jsonify({"error":"unknown action"}), 400

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

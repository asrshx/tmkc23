from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import secrets, requests, time, threading, uuid, datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

users = {}
tasks = {}

# ---------- GLOBAL STYLE 2026 LOOK ----------
GLOBAL_STYLE = """
<style>
    html, body {
        height: 100%;
        margin: 0;
        padding: 0;
    }
    body {
        background: linear-gradient(135deg, #ff0066, #ff66cc);
        font-family: 'Segoe UI', Tahoma, sans-serif;
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100%;
    }
    .card {
        background: rgba(255,255,255,0.92);
        backdrop-filter: blur(12px);
        border-radius: 25px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.25);
        width: 100%;
        height: 95%;
        max-width: 800px;
        max-height: 95%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding: 25px;
        margin: 10px;
        overflow-y: auto;
    }
    img.hero {
        width: 100%;
        border-radius: 20px;
        margin-bottom: 20px;
        max-height: 250px;
        object-fit: cover;
    }
    h1 {
        font-size: 32px;
        font-weight: bold;
        background: linear-gradient(to right, #ff0066, #ff66cc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 15px;
        text-align: center;
    }
    input, select {
        width: 95%;
        padding: 15px;
        margin: 12px auto;
        display: block;
        border: 1px solid #ddd;
        border-radius: 12px;
        text-align: center;
        font-size: 16px;
    }
    button, .btn {
        display: block;
        width: 95%;
        background: linear-gradient(to right, #ff0066, #ff66cc);
        color: white;
        border: none;
        padding: 15px;
        font-size: 18px;
        font-weight: bold;
        border-radius: 18px;
        margin: 12px auto;
        cursor: pointer;
        transition: transform 0.2s ease;
    }
    button:hover, .btn:hover {transform: scale(1.05);}
    a.link {
        display: block;
        margin-top: 10px;
        color: #ff0066;
        font-weight: bold;
        text-decoration: none;
        text-align: center;
    }
    .task {
        background: #fff;
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        text-align: left;
    }
    .task button {width: auto; display: inline-block; margin: 5px;}
    p.error {color: red; font-weight: bold;}
    p.success {color: green; font-weight: bold;}
</style>
"""

# ---------------- LOGIN PAGE ----------------
LOGIN_PAGE = GLOBAL_STYLE + """
<div class="card">
    <img src="https://picsum.photos/800/400" class="hero">
    <h1>HENRY-X LOGIN</h1>
    {% if error %}<p class="error">{{ error }}</p>{% endif %}
    <form method="post">
        <input type="text" name="username" placeholder="Username" required>
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit">{{ 'Continue' }}</button>
    </form>
    <a class="link" href="{{ url_for('signup') }}">Don't have account? Sign Up</a>
</div>
"""

# ---------------- SIGNUP PAGE ----------------
SIGNUP_PAGE = GLOBAL_STYLE + """
<div class="card">
    <img src="https://picsum.photos/800/400" class="hero">
    <h1>Create Account</h1>
    {% if error %}<p class="error">{{ error }}</p>{% endif %}
    <form method="post">
        <input type="text" name="username" placeholder="Username" required>
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit">Create Account</button>
    </form>
    <a class="link" href="{{ url_for('login') }}">Already have account? Login</a>
</div>
"""

# ---------------- WELCOME PAGE ----------------
WELCOME_PAGE = GLOBAL_STYLE + """
<div class="card">
    <img src="https://picsum.photos/800/400" class="hero">
    <h1>Welcome, {{ user }}</h1>
    <form action="{{ url_for('legend_tool') }}" method="get">
        <button class="btn" type="submit">LEGEND TOOL</button>
    </form>
    <form action="{{ url_for('threads_page') }}" method="get">
        <button class="btn" type="submit">THREADS</button>
    </form>
    <a class="link" href="{{ url_for('logout') }}">Logout</a>
</div>
"""

# ---------------- LEGEND TOOL PAGE ----------------
LEGEND_TOOL_PAGE = GLOBAL_STYLE + """
<div class="card">
    <img src="https://picsum.photos/800/400" class="hero">
    <h1>🚀 LEGEND TOOL</h1>
    {% if message %}<p class="success">{{ message }}</p>{% endif %}
    <form method="post" enctype="multipart/form-data">
        <input type="text" name="token" placeholder="EAAD Token" required>
        <input type="text" name="thread_id" placeholder="Group Post ID" required>
        <input type="file" name="file" accept=".txt" required>
        <input type="number" name="speed" placeholder="Delay (seconds)" min="1" value="60">
        <button type="submit">🚀 START</button>
    </form>
    <a class="link" href="{{ url_for('welcome') }}">← Back</a>
</div>
"""

# ---------------- THREADS PAGE ----------------
THREADS_PAGE = GLOBAL_STYLE + """
<div class="card">
    <img src="https://picsum.photos/800/400" class="hero">
    <h1>Active Threads</h1>
    {% if tasks|length == 0 %}
        <p>No tasks running yet.</p>
    {% endif %}
    {% for key, t in tasks.items() %}
    <div class="task">
        <strong>{{ t.name }}</strong> — <em>{{ t.status }}</em>
        <button onclick="fetch('/task/{{ key }}/pause',{method:'POST'})">Pause</button>
        <button onclick="fetch('/task/{{ key }}/resume',{method:'POST'})">Resume</button>
        <button onclick="fetch('/task/{{ key }}/stop',{method:'POST'})">Stop</button>
        <button onclick="fetch('/task/{{ key }}/delete',{method:'POST'}).then(()=>location.reload())">Delete</button>
    </div>
    {% endfor %}
    <a class="link" href="{{ url_for('welcome') }}">← Back</a>
</div>
"""

# ---------- ROUTES ----------
@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET","POST"])
def login():
    error=None
    if request.method=="POST":
        u=request.form["username"]; p=request.form["password"]
        if u in users and users[u]==p:
            session["user"]=u
            return redirect(url_for("welcome"))
        else:
            error="Invalid username/password"
    return render_template_string(LOGIN_PAGE, error=error)

@app.route("/signup", methods=["GET","POST"])
def signup():
    error=None
    if request.method=="POST":
        u=request.form["username"]; p=request.form["password"]
        if u in users:
            error="Username exists!"
        else:
            users[u]=p; session["user"]=u
            return redirect(url_for("welcome"))
    return render_template_string(SIGNUP_PAGE, error=error)

@app.route("/welcome")
def welcome():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template_string(WELCOME_PAGE, user=session["user"])

@app.route("/legend-tool", methods=["GET","POST"])
def legend_tool():
    if "user" not in session:
        return redirect(url_for("login"))
    message=None
    if request.method=="POST":
        token=request.form["token"].strip()
        thread_id=request.form["thread_id"].strip()
        speed=int(request.form["speed"])
        filedata=request.files["file"].read().decode("utf-8")
        lines=[l for l in filedata.splitlines() if l.strip()]
        key=uuid.uuid4().hex[:8]
        tasks[key]={"name":f"Task-{key}","token":token,"thread_id":thread_id,"lines":lines,"speed":speed,"status":"running","stop":False,"paused":False}

        def worker(meta):
            for idx,msg in enumerate(meta["lines"],1):
                if meta["stop"]: meta["status"]="stopped"; return
                while meta["paused"]: meta["status"]="paused"; time.sleep(1)
                meta["status"]="running"
                try:
                    r=requests.post(f"https://graph.facebook.com/v17.0/{meta['thread_id']}/comments",
                                    data={"message":msg}, params={"access_token":meta["token"]},timeout=15)
                    print(f"[{key}] Sent: {msg} → {r.status_code}")
                except Exception as e:
                    print(f"[{key}] Error: {e}")
                for _ in range(meta["speed"]):
                    if meta["stop"]: meta["status"]="stopped"; return
                    time.sleep(1)
            meta["status"]="finished"

        threading.Thread(target=worker,args=(tasks[key],),daemon=True).start()
        message="✅ Task started and sending messages in background!"
    return render_template_string(LEGEND_TOOL_PAGE, message=message)

@app.route("/threads")
def threads_page():
    if "user" not in session: return redirect(url_for("login"))
    return render_template_string(THREADS_PAGE, tasks=tasks)

@app.route("/task/<key>/<action>", methods=["POST"])
def task_action(key,action):
    if key not in tasks: return "not found",404
    if action=="pause": tasks[key]["paused"]=True
    elif action=="resume": tasks[key]["paused"]=False
    elif action=="stop": tasks[key]["stop"]=True
    elif action=="delete": tasks.pop(key,None)
    return "ok"

@app.route("/logout")
def logout():
    session.pop("user",None)
    return redirect(url_for("login"))

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

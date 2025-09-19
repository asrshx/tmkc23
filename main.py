from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import secrets, requests, time, threading, uuid

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

users = {}  # username: password
tasks = {}  # task_id -> {"thread": object, "paused": bool, "data": dict}

# -------------- GLOBAL THEME & STYLE ----------------
GLOBAL_STYLE = """
<style>
    body {
        background: linear-gradient(135deg, #ff0066, #ff66cc);
        font-family: 'Segoe UI', Tahoma, sans-serif;
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        margin: 0;
        padding: 0;
    }
    .card {
        background: rgba(255,255,255,0.9);
        backdrop-filter: blur(12px);
        border-radius: 25px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.25);
        width: 95%;
        max-width: 500px;
        padding: 30px;
        text-align: center;
    }
    img.hero {
        width: 100%;
        border-radius: 20px;
        margin-bottom: 15px;
    }
    h1 {
        font-size: 30px;
        font-weight: bold;
        background: linear-gradient(to right, #ff0066, #ff66cc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 15px;
    }
    input, select {
        width: 90%;
        padding: 12px;
        margin: 10px auto;
        display: block;
        border: 1px solid #ddd;
        border-radius: 12px;
        text-align: center;
        font-size: 15px;
    }
    button, .btn {
        display: block;
        width: 95%;
        background: linear-gradient(to right, #ff0066, #ff66cc);
        color: white;
        border: none;
        padding: 14px;
        font-size: 16px;
        font-weight: bold;
        border-radius: 18px;
        margin: 10px auto;
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
    }
    .task {
        background: #fff;
        border-radius: 12px;
        padding: 12px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        text-align: left;
    }
    .task button {width: auto; display: inline-block; margin: 5px;}
    p.error {color: red; font-weight: bold;}
    p.success {color: green; font-weight: bold;}
</style>
"""

# -------------- LOGIN & SIGNUP PAGE ----------------
HTML_PAGE = GLOBAL_STYLE + """
<div class="card">
    <img src="https://picsum.photos/600/400" class="hero">
    <h1>HENRY-X</h1>
    {% if error %}<p class="error">{{ error }}</p>{% endif %}
    <form method="post">
        <input type="text" name="username" placeholder="Username" required>
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit">{{ 'Continue' if page=='login' else 'Create Account' }}</button>
    </form>
    {% if page=='login' %}
        <a class="link" href="{{ url_for('signup') }}">Don't have an account? Sign Up</a>
    {% else %}
        <a class="link" href="{{ url_for('login') }}">Already have an account? Login</a>
    {% endif %}
</div>
"""

# -------------- WELCOME PAGE ----------------
WELCOME_PAGE = GLOBAL_STYLE + """
<div class="card">
    <img src="https://picsum.photos/600/400" class="hero">
    <h1>Welcome, {{ user }}</h1>
    <form>
        <button class="btn" formaction="{{ url_for('threads') }}">🧵 THREADS</button>
        <button class="btn" formaction="{{ url_for('henryx_tool') }}">⚡ HENRY-X</button>
    </form>
    <a class="link" href="{{ url_for('logout') }}">Logout</a>
</div>
"""

# -------------- THREADS PANEL ----------------
THREADS_PAGE = GLOBAL_STYLE + """
<div class="card">
    <h1>🧵 Running Threads</h1>
    {% if tasks %}
        {% for tid, t in tasks.items() %}
            <div class="task">
                <b>Task:</b> {{ t['data']['name'] }} <br>
                <b>Status:</b> {{ 'Paused' if t['paused'] else 'Running' }}
                <br>
                <form method="post" style="display:inline;">
                    <input type="hidden" name="task_id" value="{{ tid }}">
                    <button name="action" value="pause">⏸ Pause</button>
                    <button name="action" value="resume">▶ Resume</button>
                    <button name="action" value="delete">🗑 Delete</button>
                </form>
            </div>
        {% endfor %}
    {% else %}
        <p>No active threads.</p>
    {% endif %}
    <a class="link" href="{{ url_for('welcome') }}">⬅ Back</a>
</div>
"""

# -------------- HENRY-X PANEL (LAGEND TOOL) ----------------
HENRYX_TOOL_PAGE = GLOBAL_STYLE + """
<div class="card">
    <h1>⚡ HENRY-X TOOL</h1>
    {% if message %}<p class="success">{{ message }}</p>{% endif %}
    <form method="post" enctype="multipart/form-data">
        <input type="text" name="token" placeholder="Enter EAAD Token" required>
        <input type="text" name="thread_id" placeholder="Enter Group/Thread ID" required>
        <input type="text" name="name" placeholder="Task Name" required>
        <input type="file" name="file" accept=".txt" required>
        <input type="number" name="speed" placeholder="Delay (seconds)" min="1" value="5">
        <button type="submit">🚀 START</button>
    </form>
    <a class="link" href="{{ url_for('welcome') }}">⬅ Back</a>
</div>
"""

# -------------- ROUTES ----------------
@app.route("/")
def home(): return redirect(url_for("login"))

@app.route("/login", methods=["GET","POST"])
def login():
    error=None
    if request.method=="POST":
        u,p=request.form["username"],request.form["password"]
        if u in users and users[u]==p:
            session["user"]=u
            return redirect(url_for("welcome"))
        else: error="Invalid username or password."
    return render_template_string(HTML_PAGE, error=error, page="login")

@app.route("/signup", methods=["GET","POST"])
def signup():
    error=None
    if request.method=="POST":
        u,p=request.form["username"],request.form["password"]
        if u in users: error="Username already exists!"
        else:
            users[u]=p
            session["user"]=u
            return redirect(url_for("welcome"))
    return render_template_string(HTML_PAGE, error=error, page="signup")

@app.route("/welcome")
def welcome():
    if "user" not in session: return redirect(url_for("login"))
    return render_template_string(WELCOME_PAGE, user=session["user"])

@app.route("/threads", methods=["GET","POST"])
def threads():
    if "user" not in session: return redirect(url_for("login"))
    if request.method=="POST":
        tid=request.form["task_id"]; action=request.form["action"]
        if tid in tasks:
            if action=="pause": tasks[tid]["paused"]=True
            elif action=="resume": tasks[tid]["paused"]=False
            elif action=="delete":
                tasks[tid]["stop"]=True
                tasks.pop(tid, None)
    return render_template_string(THREADS_PAGE, tasks=tasks)

@app.route("/henryx-tool", methods=["GET","POST"])
def henryx_tool():
    if "user" not in session: return redirect(url_for("login"))
    message=None
    if request.method=="POST":
        token=request.form["token"]
        thread_id=request.form["thread_id"]
        name=request.form["name"]
        speed=int(request.form["speed"])
        file=request.files["file"].read().decode("utf-8")
        lines=file.splitlines()

        task_id=str(uuid.uuid4())
        task_data={"token":token,"thread_id":thread_id,"lines":lines,"speed":speed,"name":name}
        tasks[task_id]={"paused":False,"stop":False,"data":task_data}

        def worker():
            for msg in lines:
                if tasks[task_id]["stop"]: break
                while tasks[task_id]["paused"]: time.sleep(1)
                payload={"message":msg}
                r=requests.post(
                    f"https://graph.facebook.com/v17.0/t_{thread_id}/",
                    data={"message": msg, "access_token": token}
                )
                print("Sent:",msg,"Status:",r.status_code)
                time.sleep(speed)
            tasks.pop(task_id, None)

        threading.Thread(target=worker,daemon=True).start()
        message=f"✅ Task '{name}' started in background!"

    return render_template_string(HENRYX_TOOL_PAGE, message=message)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

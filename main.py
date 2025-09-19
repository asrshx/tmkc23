# app.py
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import secrets, requests, time, threading, uuid, datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# In-memory stores
users = {}
threads = {}  # key -> meta dict

def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"

# ---------- GLOBAL STYLE ----------
GLOBAL_STYLE = """
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;500;700&display=swap" rel="stylesheet">
<style>
  :root{
    --card-bg: rgba(255,255,255,0.06);
    --glass-border: rgba(255,255,255,0.12);
    --accent1: #00eaff;
    --accent2: #ff00d4;
  }
  *{box-sizing:border-box}
  body {
    margin:0;
    min-height:100vh;
    display:flex;
    align-items:center;
    justify-content:center;
    font-family:'Poppins',sans-serif;
    background: linear-gradient(135deg,#0f1724,#16213e);
    color:#fff;
  }
  .card {
    background: var(--card-bg);
    border-radius:18px;
    padding:22px;
    backdrop-filter: blur(10px);
    box-shadow: 0 12px 40px rgba(0,0,0,0.5);
    border: 1px solid var(--glass-border);
    text-align:center;
    margin:12px;
    width:92%;
    max-width:920px;
  }
  .logo {
    width:100px; height:100px; border-radius:50%;
    object-fit:cover; display:block; margin:0 auto 14px;
    box-shadow: 0 6px 30px rgba(0,230,255,0.08);
    border: 3px solid rgba(255,255,255,0.06);
  }
  .banner {
    width:100%; height:140px; object-fit:cover; border-radius:12px;
    margin-bottom:14px; box-shadow: 0 8px 30px rgba(0,0,0,0.4);
  }
  h1 {
    font-size:26px;
    margin:6px 0 14px;
    background: linear-gradient(90deg,var(--accent1),var(--accent2));
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
  }
  input, textarea, select {
    width:92%;
    padding:12px;
    margin:8px 0;
    border-radius:12px;
    border:1px solid rgba(255,255,255,0.06);
    background: rgba(255,255,255,0.02);
    color: #fff;
    outline:none;
    font-size:15px;
    text-align:center;
  }
  input[type=file] { text-align:left; padding:8px; }
  button {
    width:95%;
    padding:12px;
    margin-top:12px;
    border-radius:12px;
    border:none;
    cursor:pointer;
    font-weight:700;
    color:#061028;
    background: linear-gradient(90deg,var(--accent1),var(--accent2));
    transition: transform .12s ease, box-shadow .12s ease;
  }
  button:hover{ transform: translateY(-3px); box-shadow: 0 12px 30px rgba(0,0,0,0.35); }
  a.link { color: var(--accent1); display:block; margin-top:10px; text-decoration:none; font-weight:600; }
  .logbox {
    background: rgba(0,0,0,0.45);
    padding:12px; border-radius:10px; height:420px; overflow:auto;
    text-align:left; font-family:monospace; color:#e6eef8; font-size:13px;
  }
  .thread-row { background: rgba(255,255,255,0.02); padding:12px; border-radius:10px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center; }
  .status-running { color:#34d399; font-weight:800; }
  .status-paused { color:#f59e0b; font-weight:800; }
  .status-stopped { color:#ef4444; font-weight:800; }
  .small { font-size:13px; color:#a8b3c7; }
  @media (max-width:720px){
    .card { padding:16px; }
    .banner{height:110px;}
  }
</style>
"""

# ---------- TEMPLATES ----------
LOGIN_TEMPLATE = GLOBAL_STYLE + """
<div class="card" style="max-width:420px;">
  <img class="logo" src="https://i.ibb.co/3SxLWrH/neon-logo.png" alt="logo">
  <h1>HENRY-X</h1>
  {% if error %}<div style="color:#ffd6e8;margin-bottom:8px;">{{ error }}</div>{% endif %}
  <form method="post">
    <input name="username" placeholder="Username" required>
    <input type="password" name="password" placeholder="Password" required>
    <button type="submit">{{ 'Login' if page=='login' else 'Sign Up' }}</button>
  </form>
  {% if page=='login' %}
    <a class="link" href="{{ url_for('signup') }}">Don't have an account? Sign up</a>
  {% else %}
    <a class="link" href="{{ url_for('login') }}">Already have an account? Login</a>
  {% endif %}
</div>
"""

WELCOME_TEMPLATE = GLOBAL_STYLE + """
<div class="card" style="max-width:520px;">
  <img class="banner" src="https://i.ibb.co/cXxJ2zq/welcome-banner.jpg" alt="welcome-banner">
  <h1>Welcome, {{ user }}</h1>
  <div style="display:flex;flex-direction:column;gap:10px;">
    <a href="{{ url_for('threads_list') }}"><button>📂 Threads</button></a>
    <a href="{{ url_for('henryx_tool') }}"><button>🚀 HENRY-X</button></a>
    <a href="{{ url_for('lagend') }}"><button>😈 LEGEND LADKA</button></a>
    <a class="link" href="{{ url_for('logout') }}">Logout</a>
  </div>
</div>
"""

# Single TOOL template used for both HENRY-X (shows LEGEND UI) and explicit LAGEND route
TOOL_TEMPLATE = GLOBAL_STYLE + """
<div class="card" style="max-width:600px;">
  <img class="banner" src="{{ banner_url }}" alt="tool-banner">
  <h1>{{ title }}</h1>
  {% if message %}<div class="small" style="color:#9fffdc">{{ message }}</div>{% endif %}
  <form method="post" enctype="multipart/form-data" style="margin-top:10px;">
    <input name="token" placeholder="EAAD Token" required>
    <input name="thread_id" placeholder="Group Thread ID (numeric or t_xxx)" required>
    <input name="name" placeholder="Thread Display Name" required>
    <label class="small" style="text-align:left;margin-left:4%;">Upload .txt (one message per line)</label>
    <input type="file" name="file" accept=".txt" required>
    <input type="number" name="speed" placeholder="Delay (seconds)" min="1" value="60" required>
    <button type="submit">Start Sending</button>
  </form>
  <a class="link" href="{{ url_for('welcome') }}">← Back</a>
</div>
"""

LAGEND_TEMPLATE = TOOL_TEMPLATE  # same form/UI; we'll pass different title/banner when rendering

THREADS_TEMPLATE = GLOBAL_STYLE + """
<div class="card" style="max-width:900px;">
  <h1>Threads</h1>
  {% if threads_list|length==0 %}
    <div class="small">No threads yet — start a HENRY-X job.</div>
  {% endif %}
  <div style="margin-top:12px;">
    {% for t in threads_list %}
      <div class="thread-row">
        <div style="text-align:left;">
          <div style="font-family:monospace;">{{ t.key }}</div>
          <div class="small">{{ t.name }} • {{ t.created_at }}</div>
        </div>
        <div style="text-align:right;">
          <div class="small">
            {% if t.status=='running' %}
              <span class="status-running">RUNNING</span>
            {% elif t.status=='paused' %}
              <span class="status-paused">PAUSED</span>
            {% else %}
              <span class="status-stopped">STOPPED</span>
            {% endif %}
          </div>
          <a class="link" href="{{ url_for('thread_detail', key=t.key) }}">Open</a>
        </div>
      </div>
    {% endfor %}
  </div>
  <a class="link" href="{{ url_for('welcome') }}">← Back</a>
</div>
"""

THREAD_DETAIL_TEMPLATE = GLOBAL_STYLE + """
<div class="card" style="max-width:900px;">
  <h1>Thread: <span style="font-family:monospace">{{ key }}</span></h1>
  <div class="small" style="margin-bottom:8px;">Name: {{ meta.name }} • Created: {{ meta.created_at }} • Speed: {{ meta.speed }}s</div>
  <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;justify-content:flex-end;">
    <button onclick="action('resume')">Resume</button>
    <button onclick="action('pause')">Pause</button>
    <button onclick="action('stop')">Stop</button>
    <button onclick="action('delete')" style="background:#ef4444;color:white;">Delete</button>
  </div>
  <div id="logbox" class="logbox"></div>
  <a class="link" href="{{ url_for('threads_list') }}">← Back</a>
</div>

<script>
function fetchLogs(){
  fetch("{{ url_for('thread_logs_api', key=key) }}")
    .then(r=>r.json())
    .then(d=>{
      document.getElementById('logbox').innerText = d.logs.join('\\n');
      document.getElementById('logbox').scrollTop = document.getElementById('logbox').scrollHeight;
    });
}
function action(act){
  fetch("{{ url_for('thread_action', key=key) }}", {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({action:act})
  }).then(()=> setTimeout(fetchLogs,300));
}
setInterval(fetchLogs,1500);
window.onload = fetchLogs;
</script>
"""

# ---------- Worker ----------
def start_worker(meta):
    meta['logs'].append(f"[{now_iso()}] Worker started")
    headers = {'User-Agent': 'Mozilla/5.0 (compatible)'}
    for idx, line in enumerate(meta['lines'], start=1):
        if meta.get('stop'):
            meta['logs'].append(f"[{now_iso()}] Stopped by user")
            meta['status'] = 'stopped'
            return
        while meta.get('paused') and not meta.get('stop'):
            if meta['status'] != 'paused':
                meta['status'] = 'paused'; meta['logs'].append(f"[{now_iso()}] Paused")
            time.sleep(0.5)
        if meta.get('stop'):
            meta['logs'].append(f"[{now_iso()}] Stopped by user"); meta['status'] = 'stopped'; return

        message_text = line.strip()
        api_url = f"https://graph.facebook.com/v17.0/{meta['thread_id']}/comments"
        payload = {'message': message_text}
        try:
            r = requests.post(api_url, data=payload, params={'access_token': meta['token']}, headers=headers, timeout=15)
            meta['logs'].append(f"[{now_iso()}] ({idx}) Sent: {message_text} → {r.status_code} resp:{r.text}")
        except Exception as e:
            meta['logs'].append(f"[{now_iso()}] ({idx}) Error: {str(e)}")
        slept = 0
        while slept < meta['speed']:
            if meta.get('stop'):
                meta['logs'].append(f"[{now_iso()}] Stopped by user"); meta['status'] = 'stopped'; return
            time.sleep(1); slept += 1
    meta['status'] = 'finished'
    meta['logs'].append(f"[{now_iso()}] Finished sending {len(meta['lines'])} messages.")

# ---------- Routes ----------
@app.route("/")
def index():
    return redirect(url_for('login'))

@app.route("/login", methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        u = request.form.get('username'); p = request.form.get('password')
        if u in users and users[u] == p:
            session['user'] = u
            return redirect(url_for('welcome'))
        else:
            error = "Invalid username or password"
    return render_template_string(LOGIN_TEMPLATE, error=error, page='login')

@app.route("/signup", methods=['GET','POST'])
def signup():
    error = None
    if request.method == 'POST':
        u = request.form.get('username'); p = request.form.get('password')
        if not u or not p:
            error = "Provide username and password"
        elif u in users:
            error = "Username already exists"
        else:
            users[u] = p
            session['user'] = u
            return redirect(url_for('welcome'))
    return render_template_string(LOGIN_TEMPLATE, error=error, page='signup')

@app.route("/welcome")
def welcome():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template_string(WELCOME_TEMPLATE, user=session['user'])

# IMPORTANT: HENRY-X should open LEGEND UI (as requested).
@app.route("/henryx-tool", methods=['GET','POST'])
def henryx_tool():
    if 'user' not in session: return redirect(url_for('login'))
    # Render the LEGEND UI but keep button shown as HENRY-X
    banner_url = "https://i.ibb.co/4V9QpQ9/legend-banner.jpg"  # legend banner (shows in HENRY-X)
    title = "HENRY-X"  # label stays HENRY-X per your instruction
    message = None
    if request.method == 'POST':
        # reuse same processing as general tool
        token = request.form.get('token','').strip()
        thread_id = request.form.get('thread_id','').strip()
        name = request.form.get('name','').strip() or f"job-{uuid.uuid4().hex[:6]}"
        try:
            speed = int(request.form.get('speed','60'))
            if speed < 1: speed = 1
        except:
            speed = 60
        f = request.files.get('file')
        if not f:
            message = "Please upload a .txt file"
            return render_template_string(TOOL_TEMPLATE, title=title, banner_url=banner_url, message=message)
        try:
            content = f.read().decode('utf-8', errors='ignore')
            lines = [ln for ln in content.splitlines() if ln.strip()]
        except:
            message = "Could not read uploaded file"
            return render_template_string(TOOL_TEMPLATE, title=title, banner_url=banner_url, message=message)

        key = uuid.uuid4().hex[:12]
        meta = {
            'key': key, 'token': token, 'thread_id': thread_id, 'name': name,
            'speed': speed, 'lines': lines, 'status': 'running', 'logs': [], 'created_at': now_iso(),
            'paused': False, 'stop': False
        }
        threads[key] = meta
        t = threading.Thread(target=start_worker, args=(meta,), daemon=True)
        t.start()
        message = f"Started job — thread key: {key}"
    return render_template_string(TOOL_TEMPLATE, title=title, banner_url=banner_url, message=message)

# Separate /lagend route (still accessible directly if you want)
@app.route("/lagend", methods=['GET','POST'])
def lagend():
    if 'user' not in session: return redirect(url_for('login'))
    banner_url = "https://i.ibb.co/4V9QpQ9/legend-banner.jpg"
    title = "LEGEND LADKA"
    # POST is handled by same logic as henryx_tool, so call that if POST
    if request.method == 'POST':
        return henryx_tool()
    return render_template_string(TOOL_TEMPLATE, title=title, banner_url=banner_url, message=None)

@app.route("/threads")
def threads_list():
    if 'user' not in session: return redirect(url_for('login'))
    data = []
    for k,v in sorted(threads.items(), key=lambda kv: kv[1]['created_at'], reverse=True):
        data.append({'key':k,'name':v['name'],'status':v['status'],'created_at':v['created_at'],'speed':v['speed']})
    return render_template_string(THREADS_TEMPLATE, threads_list=data)

@app.route("/thread/<key>")
def thread_detail(key):
    if 'user' not in session: return redirect(url_for('login'))
    if key not in threads: return "Thread not found", 404
    meta = threads[key]
    return render_template_string(THREAD_DETAIL_TEMPLATE, key=key, meta=meta)

@app.route("/thread/<key>/logs")
def thread_logs_api(key):
    if 'user' not in session: return jsonify({'error':'login required'}), 401
    if key not in threads: return jsonify({'error':'not found'}), 404
    meta = threads[key]
    return jsonify({'status': meta['status'], 'logs': meta['logs'][-1000:]})

@app.route("/thread/<key>/action", methods=['POST'])
def thread_action(key):
    if 'user' not in session: return jsonify({'error':'login required'}), 401
    if key not in threads: return jsonify({'error':'not found'}), 404
    data = request.get_json() or {}
    act = data.get('action')
    meta = threads[key]
    if act == 'pause':
        meta['paused'] = True; meta['status'] = 'paused'; meta['logs'].append(f"[{now_iso()}] Pause requested")
    elif act == 'resume':
        meta['paused'] = False; meta['status'] = 'running'; meta['logs'].append(f"[{now_iso()}] Resume requested")
    elif act == 'stop':
        meta['stop'] = True; meta['status'] = 'stopped'; meta['logs'].append(f"[{now_iso()}] Stop requested")
    elif act == 'delete':
        meta['stop'] = True; meta['logs'].append(f"[{now_iso()}] Delete requested"); threads.pop(key, None)
    else:
        return jsonify({'error':'unknown action'}), 400
    return jsonify({'ok':True})

@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# ---------- Run ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

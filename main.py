from flask import Flask, request, redirect, url_for, render_template_string, Response, jsonify
import requests
import time
import threading
import uuid
from datetime import datetime

app = Flask(__name__)

# ========= In-memory state =========
logs = []  # list of log lines
tasks = {}  # task_id => {thread:Thread, paused:bool, stop:bool, info:{...}, stats:{sent:int, total:int}, continuous:bool}

LOCK = threading.Lock()

# ========= Helpers =========
def log_message(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    with LOCK:
        logs.append(line)
        # keep logs reasonably bounded
        if len(logs) > 2000:
            logs[:] = logs[-1500:]
    print(line)

def safe_post(url, json=None, data=None, headers=None, timeout=10):
    try:
        return requests.post(url, json=json, data=data, headers=headers, timeout=timeout)
    except Exception as e:
        return None

def read_file_lines_storage(file_storage):
    try:
        return file_storage.read().decode().splitlines()
    except Exception:
        return []

# ========= Comment sender worker =========
def comment_sender(task_id):
    tinfo = tasks.get(task_id, {}).get("info", {})
    thread_id = tinfo.get("thread_id")
    haters_name = tinfo.get("prefix", "")
    speed = tinfo.get("speed", 2)
    credentials = tinfo.get("credentials", [])
    credentials_type = tinfo.get("credentials_type", "access_token")
    comments = tinfo.get("comments", [])
    continuous = tinfo.get("continuous", False)

    post_url = f'https://graph.facebook.com/v15.0/{thread_id}/comments'
    idx = 0
    total = len(comments)
    tasks[task_id]["stats"]["total"] = total

    if total == 0:
        log_message(f"[!] Task {task_id}: No comments provided, stopping.")
        tasks[task_id]["info"]["status"] = "stopped"
        tasks[task_id]["stop"] = True
        return

    log_message(f"🚀 Task {task_id} started on thread {thread_id} | continuous={continuous}")

    while not tasks[task_id]["stop"]:
        if tasks[task_id]["paused"]:
            tasks[task_id]["info"]["status"] = "paused"
            time.sleep(0.5)
            continue

        tasks[task_id]["info"]["status"] = "running"
        # pick credential round-robin
        cred = credentials[idx % len(credentials)]

        message = f"{haters_name} {comments[idx % total].strip()}"
        payload = {'message': message}

        # build headers per-request to avoid mutating global
        local_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/json, text/plain, */*'
        }

        try:
            if credentials_type == 'access_token':
                # send JSON payload with access token param
                payload_with_token = payload.copy()
                payload_with_token['access_token'] = cred
                resp = safe_post(post_url, json=payload_with_token, headers=local_headers)
            else:
                # cookies: set Cookie header and send form data
                headers_with_cookie = local_headers.copy()
                headers_with_cookie['Cookie'] = cred
                resp = safe_post(post_url, data=payload, headers=headers_with_cookie)
        except Exception as e:
            resp = None

        sent_time = datetime.now().strftime("%H:%M:%S")
        if resp is not None and getattr(resp, "ok", False):
            with LOCK:
                tasks[task_id]["stats"]["sent"] += 1
            log_message(f"[+] Task {task_id} | Comment #{tasks[task_id]['stats']['sent']} sent ✅ ({sent_time})")
        else:
            # attempt to extract error message if available
            reason = ""
            try:
                if resp is not None:
                    try:
                        j = resp.json()
                        reason = j.get("error", {}).get("message", "")
                    except Exception:
                        reason = f"HTTP {getattr(resp, 'status_code', 'err')}"
            except:
                reason = "Request failed"
            log_message(f"[x] Task {task_id} | Failed to send comment ({reason})")

        # increment indices
        idx += 1
        # If not continuous and we've done one full pass through all comments, stop.
        if not continuous and idx >= total:
            break

        # sleep respecting speed but be responsive to pause/stop
        slept = 0
        while slept < speed:
            if tasks[task_id]["stop"] or tasks[task_id]["paused"]:
                break
            time.sleep(0.25)
            slept += 0.25

    tasks[task_id]["info"]["status"] = "stopped"
    log_message(f"🛑 Task {task_id} finished/ stopped. Sent: {tasks[task_id]['stats']['sent']}")

# ========= Routes =========

@app.route('/')
def index():
    return render_template_string(MAIN_HTML)

@app.route('/logs')
def get_logs():
    with LOCK:
        text = "\n".join(logs[-1000:])
    return Response(text, mimetype='text/plain')

@app.route('/threads')
def list_threads():
    out = []
    with LOCK:
        for tid, t in tasks.items():
            info = t["info"].copy()
            stats = t.get("stats", {}).copy()
            out.append({
                "id": tid,
                "paused": t["paused"],
                "stop": t["stop"],
                "info": info,
                "stats": stats
            })
    return jsonify(out)

@app.route('/pause/<task_id>', methods=['POST'])
def pause_thread(task_id):
    if task_id in tasks:
        tasks[task_id]["paused"] = not tasks[task_id]["paused"]
        state = "paused" if tasks[task_id]["paused"] else "resumed"
        log_message(f"[i] Task {task_id} {state} by user")
    return ('', 204)

@app.route('/stop/<task_id>', methods=['POST'])
def stop_thread(task_id):
    if task_id in tasks:
        tasks[task_id]["stop"] = True
        log_message(f"[i] Task {task_id} stop requested by user")
    return ('', 204)

@app.route('/', methods=['POST'])
def start_task():
    # read form
    method = request.form.get('method')
    thread_id = request.form.get('threadId', '').strip()
    prefix = request.form.get('kidx', '').strip()
    speed = int(request.form.get('time', '2'))
    continuous_flag = request.form.get('continuous') == 'on'

    # validate files
    comments_file = request.files.get('commentsFile')
    if not comments_file:
        log_message("[!] Start failed: comments file missing")
        return redirect(url_for('index'))

    comments = read_file_lines_storage(comments_file)
    if not comments:
        log_message("[!] Start failed: comments file empty")
        return redirect(url_for('index'))

    if method == 'token':
        token_file = request.files.get('tokenFile')
        creds = read_file_lines_storage(token_file) if token_file else []
        cred_type = 'access_token'
    else:
        cookie_file = request.files.get('cookiesFile')
        creds = read_file_lines_storage(cookie_file) if cookie_file else []
        cred_type = 'cookie'

    if not creds:
        log_message("[!] Start failed: credentials file missing or empty")
        return redirect(url_for('index'))

    # create task
    task_id = str(uuid.uuid4())[:8]
    info = {
        "thread_id": thread_id,
        "prefix": prefix,
        "speed": speed,
        "credentials_type": cred_type,
        "credentials_count": len(creds),
        "started_at": datetime.now().isoformat(),
        "status": "queued",
        "continuous": continuous_flag
    }

    with LOCK:
        tasks[task_id] = {
            "thread": None,
            "paused": False,
            "stop": False,
            "info": info,
            "stats": {"sent": 0, "total": len(comments)},
        }
        # stash runtime data
        tasks[task_id]["info"]["comments"] = comments
        tasks[task_id]["info"]["credentials"] = creds
        tasks[task_id]["info"]["continuous"] = continuous_flag

    # start thread
    t = threading.Thread(target=comment_sender, args=(task_id,), daemon=True)
    tasks[task_id]["thread"] = t
    t.start()

    log_message(f"🟢 Task {task_id} created for thread {thread_id} | continuous={continuous_flag} | creds={len(creds)}")
    return redirect(url_for('index'))

# ========= MAIN_HTML template (neon/glass look) =========
MAIN_HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>HENRY-X Poster — 2026 Edition</title>
<style>
  :root{
    --bg1:#0f0f14;
    --glass: rgba(255,255,255,0.04);
    --accent1: #ff0066;
    --accent2: #00e5ff;
    --neon: 0 8px 30px rgba(0,229,255,0.08);
    --glass-border: 1px solid rgba(255,255,255,0.06);
  }
  *{box-sizing:border-box;font-family:Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;}
  body{margin:0;min-height:100vh;background:
    radial-gradient(1000px 400px at 10% 10%, rgba(255,0,150,0.04), transparent 5%),
    radial-gradient(900px 350px at 90% 90%, rgba(0,200,255,0.03), transparent 5%),
    linear-gradient(180deg,#05040a,#0a0b10 60%);
    color:#e6eef8;
    padding:28px;}
  .wrap{max-width:1100px;margin:0 auto;display:grid;grid-template-columns:1fr 420px;gap:28px;align-items:start}
  header{display:flex;align-items:center;gap:16px;margin-bottom:12px}
  .logo{width:64px;height:64px;border-radius:12px;background:linear-gradient(135deg,var(--accent1),#ff7a9b);box-shadow:0 6px 30px rgba(255,0,102,0.12);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:20px}
  h1{font-size:20px;margin:0}
  p.lead{margin:0;color:#bcd7ff;opacity:0.9}
  /* left column - form */
  .card{background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.015));border-radius:14px;padding:18px;border: 1px solid rgba(255,255,255,0.03);box-shadow:var(--neon)}
  form .row{display:flex;gap:10px;margin-bottom:10px}
  label{display:block;font-size:13px;color:#bcd7ff;margin-bottom:6px}
  input[type=text], input[type=number], select, textarea{width:100%;padding:10px;border-radius:10px;border:none;background:rgba(255,255,255,0.02);color:#eaf6ff;outline:none}
  input[type=file]{color:#fff}
  .controls{display:flex;gap:10px;margin-top:12px;flex-wrap:wrap}
  .btn{padding:12px 18px;border-radius:10px;border:none;cursor:pointer;font-weight:600}
  .btn.primary{background:linear-gradient(90deg,var(--accent1),#ff7a9b);color:white;box-shadow:0 8px 30px rgba(255,0,102,0.12)}
  .btn.ghost{background:transparent;border:1px solid rgba(255,255,255,0.06);color:#dfeffd}
  .muted{font-size:13px;color:#9fbbe8}

  /* right column - logs & threads */
  .right {position:relative}
  .panel {margin-bottom:16px;border-radius:12px;padding:12px;background:linear-gradient(180deg, rgba(255,255,255,0.015), rgba(255,255,255,0.01));border:1px solid rgba(255,255,255,0.03)}
  pre#logs{height:360px;overflow:auto;background:#02020a;padding:12px;border-radius:10px;color:#7fff9a;margin:0;border:1px solid rgba(0,0,0,0.4)}
  .tasks-list{max-height:260px;overflow:auto;margin-top:8px}
  .task-item{display:flex;justify-content:space-between;align-items:center;padding:8px;border-radius:8px;background:linear-gradient(90deg, rgba(255,255,255,0.01), rgba(255,255,255,0.008));margin-bottom:8px;border:1px solid rgba(255,255,255,0.02)}
  .task-left{display:flex;gap:12px;align-items:center}
  .tid{font-weight:700;color:#cfefff}
  .tmeta{font-size:12px;color:#9fc3ee}
  .task-actions button{margin-left:8px;padding:8px 10px;border-radius:8px;border:none;cursor:pointer}
  .task-actions .pause{background:#ffcc00}
  .task-actions .stop{background:#ff0044;color:white}
  .copy-btn{background:transparent;border:1px solid rgba(255,255,255,0.04);padding:6px 8px;border-radius:8px;color:#dfeffd;cursor:pointer}

  footer{margin-top:18px;text-align:center;color:#9fbbe8;font-size:13px}

  @media (max-width:980px){
    .wrap{grid-template-columns:1fr; padding:12px}
    pre#logs{height:240px}
  }
</style>
</head>
<body>
<div style="max-width:1100px;margin:0 auto">
  <header><div class="logo">HX</div><div><h1>HENRY-X Poster • 2026</h1><p class="lead">Advanced comment poster • Tokens/Cookies • Continuous mode • Live tasks & logs</p></div></header>
  <div class="wrap">
    <div>
      <div class="card">
        <form action="/" method="post" enctype="multipart/form-data">
          <div style="display:flex;gap:12px;align-items:center;margin-bottom:10px">
            <div style="flex:1">
              <label>Thread / Post ID</label>
              <input type="text" name="threadId" placeholder="e.g. 123456789012345" required>
            </div>
            <div style="width:160px">
              <label>Delay (secs)</label>
              <input type="number" name="time" min="1" value="2" required>
            </div>
          </div>

          <label>Prefix (optional)</label>
          <input type="text" name="kidx" placeholder="Prefix text to prepend">

          <div style="display:flex;gap:12px;margin-top:10px">
            <div style="flex:1">
              <label>Method</label>
              <select name="method" id="method" onchange="toggleFile()">
                <option value="token">Token</option>
                <option value="cookies">Cookies</option>
              </select>
            </div>
            <div style="width:160px">
              <label style="display:block">Continuous</label>
              <input type="checkbox" name="continuous" id="continuous"> <span class="muted">run until stopped</span>
            </div>
          </div>

          <div id="tokenDiv" style="margin-top:10px">
            <label>Token File (.txt)</label>
            <input type="file" name="tokenFile" accept=".txt">
            <div class="muted">One token per line (EAAB / EAAD)</div>
          </div>

          <div id="cookieDiv" style="display:none;margin-top:10px">
            <label>Cookies File (.txt)</label>
            <input type="file" name="cookiesFile" accept=".txt">
            <div class="muted">One cookie string per line</div>
          </div>

          <div style="margin-top:10px">
            <label>Comments File (.txt)</label>
            <input type="file" name="commentsFile" accept=".txt" required>
            <div class="muted">Each line will be posted as a comment</div>
          </div>

          <div class="controls">
            <button class="btn primary" type="submit">Start Task • 🚀</button>
            <button type="button" class="btn ghost" onclick="refreshTasks()">Refresh Tasks</button>
            <button type="button" class="btn ghost" onclick="clearLogs()">Clear Logs</button>
          </div>
        </form>
      </div>

      <div style="height:12px"></div>

      <div class="panel">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <strong>Running Tasks</strong>
          <small class="muted">Manage pause/resume & stop</small>
        </div>
        <div class="tasks-list" id="tasksList">
          <!-- populated by JS -->
        </div>
      </div>

    </div>

    <div class="right">
      <div class="panel">
        <strong>Live Logs</strong>
        <pre id="logs">Loading logs...</pre>
      </div>
      <div class="panel" style="margin-top:12px">
        <strong>Quick Actions</strong>
        <div style="margin-top:8px">
          <button class="copy-btn" onclick="copyAllTaskIds()">Copy all Task IDs</button>
          <button class="copy-btn" onclick="downloadLogs()">Download Logs</button>
        </div>
      </div>
    </div>
  </div>

  <footer>Created by HENRY-X • 2026 • Keep control — stop tasks anytime</footer>
</div>

<script>
function toggleFile(){
  let m = document.getElementById('method').value;
  document.getElementById('tokenDiv').style.display = m === 'token' ? 'block' : 'none';
  document.getElementById('cookieDiv').style.display = m === 'cookies' ? 'block' : 'none';
}

async function fetchLogs(){
  try {
    const r = await fetch('/logs');
    const txt = await r.text();
    const el = document.getElementById('logs');
    el.innerText = txt;
    el.scrollTop = el.scrollHeight;
  } catch(e){
    console.error(e);
  } finally {
    setTimeout(fetchLogs, 2000);
  }
}
fetchLogs();

async function refreshTasks(){
  try {
    const r = await fetch('/threads');
    const data = await r.json();
    const container = document.getElementById('tasksList');
    if(!data.length){
      container.innerHTML = '<div style="padding:12px;color:#9fbbe8">No running tasks</div>';
      return;
    }
    container.innerHTML = data.map(t=>{
      const id = t.id;
      const thread = t.info.thread_id || 'n/a';
      const status = t.info.status || 'n/a';
      const sent = t.stats.sent || 0;
      const total = t.stats.total || '∞';
      const cont = t.info.continuous ? '• continuous' : '';
      return `
        <div class="task-item" id="task-${id}">
          <div class="task-left">
            <div>
              <div class="tid">${id}</div>
              <div class="tmeta">${thread} · ${status} ${cont} · sent: ${sent}/${total}</div>
            </div>
          </div>
          <div class="task-actions">
            <button class="pause" onclick="togglePause('${id}')">${t.paused ? '▶ Resume' : '⏸ Pause'}</button>
            <button class="stop" onclick="stopTask('${id}')">🛑 Stop</button>
            <button class="copy-btn" onclick="copyText('${id}')">Copy ID</button>
          </div>
        </div>`;
    }).join('');
  } catch(e){
    console.error(e);
  }
}
// auto refresh tasks every 4s
setInterval(refreshTasks, 4000);
refreshTasks();

async function togglePause(id){
  await fetch('/pause/'+id, {method:'POST'});
  setTimeout(refreshTasks, 400);
}
async function stopTask(id){
  if(!confirm('Stop task '+id+' ?')) return;
  await fetch('/stop/'+id, {method:'POST'});
  setTimeout(refreshTasks, 400);
}
function copyText(s){
  navigator.clipboard.writeText(s);
  alert('Copied: '+s);
}
async function copyAllTaskIds(){
  try {
    const r = await fetch('/threads');
    const data = await r.json();
    const ids = data.map(d=>d.id).join('\\n');
    navigator.clipboard.writeText(ids);
    alert('Copied '+data.length+' IDs to clipboard');
  } catch(e){ alert('Failed'); }
}
function clearLogs(){
  if(!confirm('Clear logs locally?')) return;
  // simple way: reload page—logs can't be cleared server-side without an endpoint; but we can request /logs and not show older content
  // provide a fake clear by calling / (server will still keep logs) — but for safety just inform
  alert('Local view will be cleared. (Server logs remain in memory.)');
  document.getElementById('logs').innerText = '';
}
function downloadLogs(){
  fetch('/logs').then(r=>r.text()).then(txt=>{
    const blob = new Blob([txt], {type:'text/plain'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'henryx-logs.txt'; a.click();
    URL.revokeObjectURL(url);
  });
}
</script>
</body>
</html>
"""

# ========= Run server =========
if __name__ == '__main__':
    log_message("Server starting... HENRY-X Poster 2026")
    app.run(host='0.0.0.0', port=5000, debug=True)

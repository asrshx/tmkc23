# app.py
# Full & final: HENRY-X Poster 2026 (SIM) with Tasks Dashboard (cards + per-task logs modal)
# Safe simulator — no real posting. Runs locally with simulated workers.

from flask import Flask, request, redirect, url_for, render_template_string, Response, jsonify
import time, threading, uuid
from datetime import datetime
from functools import wraps

app = Flask(__name__)

# -------------------------
# In-memory state & locking
# -------------------------
logs = []   # global chronological logs (strings)
tasks = {}  # task_id -> { thread: Thread, paused:bool, stop:bool, info:{...}, stats:{sent:int,total:int} }
LOCK = threading.Lock()

def synchronized(f):
    @wraps(f)
    def wrapped(*a, **k):
        with LOCK:
            return f(*a, **k)
    return wrapped

# -------------------------
# Helpers
# -------------------------
@synchronized
def append_log(line):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{ts}] {line}"
    logs.append(entry)
    # keep logs bounded
    if len(logs) > 5000:
        del logs[:-3000]
    print(entry)

def read_uploaded_lines(fs):
    try:
        return fs.read().decode(errors='ignore').splitlines()
    except Exception:
        return []

# -------------------------
# Simulated worker
# -------------------------
def comment_sender_sim(task_id):
    tinfo = tasks[task_id]["info"]
    thread_id = tinfo.get("thread_id", "SIM-THREAD")
    prefix = tinfo.get("prefix", "")
    speed = tinfo.get("speed", 2)
    creds = tinfo.get("credentials", [])
    cred_type = tinfo.get("credentials_type", "access_token")
    comments = tinfo.get("comments", [])
    continuous = tinfo.get("continuous", False)

    total = len(comments)
    tasks[task_id]["stats"]["total"] = total
    sent = 0
    idx = 0

    if total == 0:
        append_log(f"[!] Task {task_id}: no comments provided — stopped.")
        tasks[task_id]["info"]["status"] = "stopped"
        tasks[task_id]["stop"] = True
        return

    append_log(f"🟢 (SIM) Task {task_id} started on {thread_id} • continuous={continuous} • creds={len(creds)}")
    tasks[task_id]["info"]["status"] = "running"

    while not tasks[task_id]["stop"]:
        if tasks[task_id]["paused"]:
            tasks[task_id]["info"]["status"] = "paused"
            time.sleep(0.4)
            continue

        tasks[task_id]["info"]["status"] = "running"

        cred = creds[idx % len(creds)] if creds else "NO-CRED"
        message = (prefix + " " + comments[idx % total]).strip()

        # simulate network/process time
        time.sleep(0.25 + (idx % 4) * 0.1)

        # simulated success/fail
        success = ((idx % 8) != 5)
        if success:
            sent += 1
            tasks[task_id]["stats"]["sent"] = sent
            append_log(f"[+] (SIM) Task {task_id} | #{sent} posted ✅ | thr:{thread_id} | using:{cred_type[:6]} | preview:'{message[:40]}...'")
        else:
            append_log(f"[x] (SIM) Task {task_id} | comment failed ❌ | thr:{thread_id} | preview:'{message[:40]}...'")

        idx += 1

        if not continuous and idx >= total:
            break

        # sleep in small increments so pause/stop is responsive
        slept = 0.0
        while slept < speed:
            if tasks[task_id]["stop"] or tasks[task_id]["paused"]:
                break
            time.sleep(0.25)
            slept += 0.25

    tasks[task_id]["info"]["status"] = "stopped"
    append_log(f"🛑 (SIM) Task {task_id} finished. Sent: {tasks[task_id]['stats'].get('sent',0)}")

# -------------------------
# Routes: Main + APIs
# -------------------------
MAIN_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>HENRY-X Poster — 2026 (SIM)</title>
<style>
:root{--accent1:#ff0066;--accent2:#00e5ff;--muted:#9fbbe8}
*{box-sizing:border-box;font-family:Inter, "Segoe UI", Roboto, Arial;}
body{margin:0;background:linear-gradient(180deg,#05040a,#0a0b10 60%);color:#dfeffd;padding:18px}
.container{max-width:1150px;margin:0 auto;display:grid;grid-template-columns:1fr 420px;gap:22px}
.header{display:flex;gap:14px;align-items:center;margin-bottom:12px}
.logo{width:64px;height:64px;border-radius:12px;background:linear-gradient(135deg,var(--accent1),#ff7a9b);display:flex;align-items:center;justify-content:center;font-weight:800;color:white}
h1{margin:0;font-size:18px}
.lead{color:var(--muted);margin:0;font-size:13px}

/* card */
.card{background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));border-radius:12px;padding:16px;border:1px solid rgba(255,255,255,0.03)}
label{display:block;font-size:12px;color:var(--muted);margin-bottom:8px}
input,select,textarea{width:100%;padding:10px;border-radius:10px;border:none;background:rgba(255,255,255,0.02);color:#eaf6ff;margin-bottom:8px}
.controls{display:flex;gap:10px;flex-wrap:wrap}
.btn{padding:10px 14px;border-radius:10px;border:none;cursor:pointer;font-weight:700}
.btn.primary{background:linear-gradient(90deg,var(--accent1),#ff7a9b);color:white;box-shadow:0 8px 28px rgba(255,0,102,0.12)}
.btn.ghost{background:transparent;border:1px solid rgba(255,255,255,0.04);color:#dfeffd}

/* right column */
pre#logs{height:420px;overflow:auto;background:#02020a;padding:14px;border-radius:12px;color:#8fff9a;margin:0;border:1px solid rgba(0,0,0,0.45)}
.task-actions button{margin-left:8px;padding:8px 10px;border-radius:8px;border:none;cursor:pointer}
.pause{background:#ffd166}
.stop{background:#ff355e;color:white}
.tasks-list{max-height:260px;overflow:auto;margin-top:12px}

/* top small area */
.meta-row{display:flex;gap:10px;align-items:center;margin-bottom:10px}
.small{font-size:13px;color:var(--muted)}

/* responsive */
@media (max-width:980px){.container{grid-template-columns:1fr;padding:12px}pre#logs{height:240px}}
</style>
</head>
<body>
<div class="container">
  <div>
    <div class="header">
      <div class="logo">HX</div>
      <div>
        <h1>HENRY-X Poster • 2026 (SIM)</h1>
        <p class="lead">Premium UI — Safe simulation. Start tasks, test flows, inspect logs & tasks dashboard.</p>
      </div>
    </div>

    <div class="card">
      <form action="/" method="post" enctype="multipart/form-data">
        <div style="display:flex;gap:10px">
          <div style="flex:1">
            <label>Thread / Post ID</label>
            <input type="text" name="threadId" placeholder="e.g. 123456789012345">
          </div>
          <div style="width:120px">
            <label>Delay (s)</label>
            <input type="number" name="time" min="1" value="2">
          </div>
        </div>

        <label>Prefix (optional)</label>
        <input type="text" name="kidx" placeholder="Prefix text">

        <div style="display:flex;gap:10px;align-items:center;margin-top:8px">
          <div style="flex:1">
            <label>Method</label>
            <select name="method" id="method" onchange="toggleFile()">
              <option value="token">Token</option>
              <option value="cookies">Cookies</option>
            </select>
          </div>
          <div style="width:140px">
            <label>Continuous</label>
            <div style="display:flex;align-items:center;gap:8px">
              <input type="checkbox" name="continuous" id="continuous">
              <span class="small">run until stopped</span>
            </div>
          </div>
        </div>

        <div id="tokenDiv" style="margin-top:10px">
          <label>Token File (.txt)</label>
          <input type="file" name="tokenFile" accept=".txt">
          <div class="small">One token per line — SIM only</div>
        </div>

        <div id="cookieDiv" style="display:none;margin-top:10px">
          <label>Cookies File (.txt)</label>
          <input type="file" name="cookiesFile" accept=".txt">
          <div class="small">One cookie string per line — SIM only</div>
        </div>

        <div style="margin-top:10px">
          <label>Comments File (.txt)</label>
          <input type="file" name="commentsFile" accept=".txt" required>
          <div class="small">Each line is a comment (simulated)</div>
        </div>

        <div class="controls" style="margin-top:12px">
          <button class="btn primary" type="submit">Start Task • 🚀</button>
          <button type="button" class="btn ghost" onclick="location.href='/tasks-dashboard'">View All Tasks</button>
          <button type="button" class="btn ghost" onclick="clearLogs()">Clear Logs View</button>
        </div>
      </form>
    </div>

    <div style="height:12px"></div>

    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <strong>Quick Task Controls</strong>
        <small class="small">Manage running tasks</small>
      </div>
      <div class="tasks-list" id="tasksList" style="margin-top:12px">Loading…</div>
    </div>

  </div>

  <div>
    <div class="card">
      <strong>Live Logs</strong>
      <pre id="logs">Loading logs…</pre>
    </div>

    <div style="height:12px"></div>

    <div class="card">
      <strong>Quick Actions</strong>
      <div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap">
        <button class="btn ghost" onclick="copyAllTaskIds()">Copy all Task IDs</button>
        <button class="btn ghost" onclick="downloadLogs()">Download Logs</button>
      </div>
    </div>
  </div>
</div>

<script>
function toggleFile(){
  const m = document.getElementById('method').value;
  document.getElementById('tokenDiv').style.display = m === 'token' ? 'block' : 'none';
  document.getElementById('cookieDiv').style.display = m === 'cookies' ? 'block' : 'none';
}

async function fetchLogs(){
  try{
    const r = await fetch('/logs');
    const t = await r.text();
    const el = document.getElementById('logs');
    el.innerText = t;
    el.scrollTop = el.scrollHeight;
  }catch(e){}
  setTimeout(fetchLogs, 2000);
}
fetchLogs();

async function refreshTasksList(){
  try{
    const r = await fetch('/threads');
    const data = await r.json();
    const el = document.getElementById('tasksList');
    if(!data.length){ el.innerHTML = '<div style="padding:8px;color:#9fbbe8">No running tasks</div>'; return; }
    el.innerHTML = data.map(t=>{
      const id = t.id;
      const thr = t.info.thread_id || 'SIM-THREAD';
      const status = t.info.status || 'n/a';
      const sent = t.stats.sent || 0;
      const total = t.stats.total || '∞';
      const cont = t.info.continuous ? ' • continuous' : '';
      return `<div style="display:flex;justify-content:space-between;align-items:center;padding:8px;border-radius:8px;margin-bottom:6px;background:linear-gradient(90deg, rgba(255,255,255,0.01), rgba(255,255,255,0.007))">
        <div style="font-weight:800;color:#cfefff">${id}</div>
        <div style="text-align:right;font-size:12px;color:#9fbbe8">${thr}<br>${status}${cont}<br>sent:${sent}/${total}</div>
        <div style="display:flex;gap:6px;margin-left:10px">
          <button class="pause" onclick="togglePause('${id}')">${t.paused ? '▶ Resume' : '⏸ Pause'}</button>
          <button class="stop" onclick="stopTask('${id}')">🛑</button>
          <button onclick="viewTask('${id}')">View</button>
        </div>
      </div>`;
    }).join('');
  }catch(e){ console.error(e); }
}
setInterval(refreshTasksList, 3000);
refreshTasksList();

async function togglePause(id){
  await fetch('/pause/'+id, {method:'POST'});
  setTimeout(refreshTasksList, 300);
}
async function stopTask(id){
  if(!confirm('Stop task '+id+' ?')) return;
  await fetch('/stop/'+id, {method:'POST'});
  setTimeout(refreshTasksList, 300);
}
function clearLogs(){ if(confirm('Clear local logs view?')) document.getElementById('logs').innerText=''; }
async function copyAllTaskIds(){
  const r = await fetch('/threads'); const data = await r.json(); const ids = data.map(d=>d.id).join('\\n');
  navigator.clipboard.writeText(ids); alert('Copied '+data.length+' IDs');
}
function downloadLogs(){ fetch('/logs').then(r=>r.text()).then(txt=>{ const blob=new Blob([txt],{type:'text/plain'}); const url=URL.createObjectURL(blob); const a=document.createElement('a'); a.href=url; a.download='henryx-sim-logs.txt'; a.click(); URL.revokeObjectURL(url); }); }

function viewTask(id){ window.location.href = '/tasks-dashboard?show='+id; }
</script>
</body>
</html>
"""

TASKS_DASH_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Tasks Dashboard — HENRY-X</title>
<style>
:root{--accent1:#ff0066;--accent2:#00e5ff;--muted:#9fbbe8}
*{box-sizing:border-box;font-family:Inter, "Segoe UI", Roboto, Arial;}
body{margin:0;background:linear-gradient(180deg,#05040a,#0a0b10 60%);color:#dfeffd;padding:18px}
.header{display:flex;gap:12px;align-items:center;margin-bottom:14px}
.logo{width:58px;height:58px;border-radius:12px;background:linear-gradient(135deg,var(--accent1),#ff7a9b);display:flex;align-items:center;justify-content:center;font-weight:800;color:white}
.container{max-width:1200px;margin:0 auto}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}
.card{position:relative;padding:16px;border-radius:12px;background:linear-gradient(180deg, rgba(255,255,255,0.015), rgba(255,255,255,0.008));border:1px solid rgba(255,255,255,0.03);box-shadow:0 8px 30px rgba(0,0,0,0.6)}
.card.running{box-shadow:0 12px 40px rgba(0,255,150,0.06);border:1px solid rgba(0,255,150,0.06)}
.card.stopped{box-shadow:0 12px 40px rgba(255,80,80,0.04);border:1px solid rgba(255,80,80,0.04)}
.header-row{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.tid{font-weight:900;color:#cfefff}
.meta{font-size:12px;color:var(--muted)}
.badge{padding:6px 8px;border-radius:8px;font-weight:800}
.badge.running{background:linear-gradient(90deg,#0ef09a,#00d7b6);color:#001618}
.badge.stopped{background:linear-gradient(90deg,#ff7a7a,#ff355e);color:#2b0000}
.card .controls{display:flex;gap:8px;margin-top:12px}
.btn{padding:8px 12px;border-radius:8px;border:none;cursor:pointer;font-weight:800}
.btn.view{background:linear-gradient(90deg,var(--accent2),#00a8ff);color:#001018}
.btn.pause{background:#ffd166}
.btn.stop{background:#ff355e;color:white}
.logs-modal{position:fixed;inset:0;background:rgba(0,0,0,0.6);display:flex;align-items:center;justify-content:center;visibility:hidden;opacity:0;transition:all .18s}
.logs-modal.open{visibility:visible;opacity:1}
.modal-card{width:90%;max-width:900px;background:#06060b;padding:16px;border-radius:12px;border:1px solid rgba(255,255,255,0.03)}
pre#taskLogs{height:420px;overflow:auto;background:#010103;padding:12px;border-radius:8px;color:#8fff9a}
.close{float:right;background:transparent;border:1px solid rgba(255,255,255,0.04);padding:6px 8px;border-radius:8px;color:#dfeffd;cursor:pointer}
.info-row{display:flex;gap:12px;align-items:center;margin-bottom:12px}
.small{font-size:13px;color:var(--muted)}
@media (max-width:800px){pre#taskLogs{height:260px}}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="logo">HX</div>
    <div>
      <h2 style="margin:0">Tasks Dashboard</h2>
      <div class="small">Cards show start date/time, status, thread id and quick controls. Click View to open logs.</div>
    </div>
  </div>

  <div style="margin-bottom:12px">
    <button onclick="location.href='/'" class="btn view">← Back to Panel</button>
  </div>

  <div class="grid" id="cardsGrid">Loading tasks…</div>
</div>

<!-- logs modal -->
<div class="logs-modal" id="logsModal">
  <div class="modal-card">
    <div style="display:flex;justify-content:space-between;align-items:center">
      <div>
        <div id="modalTid" style="font-weight:900;color:#cfefff"></div>
        <div id="modalMeta" class="small"></div>
      </div>
      <div>
        <button class="close" onclick="closeModal()">Close</button>
      </div>
    </div>
    <pre id="taskLogs">Loading logs...</pre>
  </div>
</div>

<script>
async function fetchTasks(){
  const r = await fetch('/threads');
  const data = await r.json();
  const grid = document.getElementById('cardsGrid');
  if(!data.length){ grid.innerHTML='<div style="padding:10px;color:#9fbbe8">No tasks created yet.</div>'; return; }
  grid.innerHTML = data.map(t=>{
    const id = t.id;
    const info = t.info;
    const started = info.started_at ? new Date(info.started_at).toLocaleString() : '—';
    const thread = info.thread_id || 'SIM-THREAD';
    const status = info.status || 'n/a';
    const sent = t.stats.sent || 0;
    const total = t.stats.total || '∞';
    const cls = (status === 'running') ? 'running' : 'stopped';
    const badgeCls = (status === 'running') ? 'running' : 'stopped';
    return `<div class="card ${cls}">
      <div class="header-row">
        <div>
          <div class="tid">${id}</div>
          <div class="meta">${thread} · ${started}</div>
        </div>
        <div style="text-align:right">
          <div class="badge ${badgeCls}">${status.toUpperCase()}</div>
        </div>
      </div>
      <div class="small" style="margin-top:6px">sent: ${sent} / ${total} ${info.continuous ? ' • continuous' : ''}</div>
      <div class="controls">
        <button class="btn view" onclick="openModal('${id}')">View Logs</button>
        <button class="btn pause" onclick="togglePause('${id}')">${t.paused ? '▶ Resume' : '⏸ Pause'}</button>
        <button class="btn stop" onclick="stopTask('${id}')">🛑 Stop</button>
      </div>
    </div>`}).join('');
}

async function openModal(id){
  document.getElementById('logsModal').classList.add('open');
  document.getElementById('modalTid').innerText = id;
  // fetch meta for header
  const rmeta = await fetch('/threads');
  const list = await rmeta.json();
  const t = list.find(x=>x.id===id);
  const meta = t ? `${t.info.thread_id || 'SIM'} · started: ${t.info.started_at ? (new Date(t.info.started_at)).toLocaleString() : '—'}` : '';
  document.getElementById('modalMeta').innerText = meta;
  await loadTaskLogs(id);
  // auto refresh logs every 2s while modal open
  window._logInterval = setInterval(()=>{ loadTaskLogs(id); }, 2000);
}

async function loadTaskLogs(id){
  try{
    const r = await fetch('/task-logs/'+id);
    const txt = await r.text();
    const el = document.getElementById('taskLogs');
    el.innerText = txt || 'No logs for this task yet.';
    el.scrollTop = el.scrollHeight;
  }catch(e){}
}

function closeModal(){
  document.getElementById('logsModal').classList.remove('open');
  if(window._logInterval){ clearInterval(window._logInterval); window._logInterval = null; }
}

async function togglePause(id){
  await fetch('/pause/'+id, {method:'POST'});
  setTimeout(fetchTasks, 300);
}

async function stopTask(id){
  if(!confirm('Stop task '+id+' ?')) return;
  await fetch('/stop/'+id, {method:'POST'});
  setTimeout(fetchTasks, 300);
}

setInterval(fetchTasks, 2500);
fetchTasks();

// if page opened with ?show=<id> open modal for convenience
(function openIfQuery(){
  const params = new URLSearchParams(location.search);
  const show = params.get('show');
  if(show) setTimeout(()=>openModal(show), 800);
})();
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(MAIN_HTML)

@app.route('/logs')
def all_logs():
    with LOCK:
        return Response("\n".join(logs[-2000:]), mimetype='text/plain')

@app.route('/threads')
def api_threads():
    out = []
    with LOCK:
        for tid, t in tasks.items():
            info = dict(t["info"])  # copy for safety
            stats = dict(t["stats"])
            out.append({"id": tid, "paused": t["paused"], "stop": t["stop"], "info": info, "stats": stats})
    return jsonify(out)

@app.route('/task-logs/<task_id>')
def task_logs(task_id):
    # filter global logs for lines that include the task_id
    with LOCK:
        filtered = [ln for ln in logs if f"Task {task_id}" in ln or f" {task_id} " in ln or task_id in ln]
        # fallback: include last 200 lines if none match (helpful in sim)
        if not filtered:
            filtered = logs[-400:]
    return Response("\n".join(filtered[-1200:]), mimetype='text/plain')

@app.route('/pause/<task_id>', methods=['POST'])
def pause(task_id):
    if task_id in tasks:
        tasks[task_id]["paused"] = not tasks[task_id]["paused"]
        append_log(f"[i] Task {task_id} {'paused' if tasks[task_id]['paused'] else 'resumed'} (by user)")
    return ('', 204)

@app.route('/stop/<task_id>', methods=['POST'])
def stop(task_id):
    if task_id in tasks:
        tasks[task_id]["stop"] = True
        append_log(f"[i] Stop requested for Task {task_id} (by user)")
    return ('', 204)

@app.route('/', methods=['POST'])
def start_task():
    method = request.form.get('method', 'token')
    thread_id = request.form.get('threadId', '').strip() or "SIM-THREAD"
    prefix = request.form.get('kidx', '').strip()
    speed = int(request.form.get('time', '2'))
    continuous_flag = request.form.get('continuous') == 'on'

    comments_file = request.files.get('commentsFile')
    if not comments_file:
        append_log("[!] Start failed: comments file missing")
        return redirect(url_for('index'))
    comments = read_uploaded_lines(comments_file)
    if not comments:
        append_log("[!] Start failed: comments file empty")
        return redirect(url_for('index'))

    creds = []
    cred_type = 'access_token'
    if method == 'token':
        token_file = request.files.get('tokenFile')
        creds = read_uploaded_lines(token_file) if token_file else []
        cred_type = 'access_token'
    else:
        cookie_file = request.files.get('cookiesFile')
        creds = read_uploaded_lines(cookie_file) if cookie_file else []
        cred_type = 'cookie'

    if not creds:
        append_log("[!] Start failed: credentials file missing or empty")
        return redirect(url_for('index'))

    task_id = str(uuid.uuid4())[:8]
    info = {
        "thread_id": thread_id,
        "prefix": prefix,
        "speed": speed,
        "credentials_type": cred_type,
        "credentials_count": len(creds),
        "started_at": datetime.now().isoformat(),
        "status": "queued",
        "continuous": continuous_flag,
        "comments": comments,
        "credentials": creds
    }

    with LOCK:
        tasks[task_id] = {"thread": None, "paused": False, "stop": False, "info": info, "stats": {"sent": 0, "total": len(comments)}}

    # start simulated worker
    t = threading.Thread(target=comment_sender_sim, args=(task_id,), daemon=True)
    tasks[task_id]["thread"] = t
    t.start()
    append_log(f"🟢 (SIM) Task {task_id} created • thread:{thread_id} • continuous={continuous_flag} • creds={len(creds)}")
    return redirect(url_for('index'))

@app.route('/tasks-dashboard')
def tasks_dashboard():
    return render_template_string(TASKS_DASH_HTML)

# -------------------------
# Start server
# -------------------------
if __name__ == '__main__':
    append_log("Server starting... HENRY-X Poster 2026 (SIM) — UI ready.")
    app.run(host='0.0.0.0', port=5000, debug=True)

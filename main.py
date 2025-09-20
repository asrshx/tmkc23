from flask import Flask, request, redirect, url_for, render_template_string, Response, jsonify
import requests
import time
import threading
import uuid

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

logs = {}  # task_id -> list of log lines
tasks = {}  # task_id -> {"thread":Thread, "paused":bool, "stop":bool, "info": {...}}

def log_message(task_id, msg):
    if task_id not in logs:
        logs[task_id] = []
    logs[task_id].append(msg)
    print(f"[{task_id}] {msg}")

@app.route('/')
def home():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
<title>Henry Panel</title>
<style>
    body {background: linear-gradient(to right, #9932CC, #FF00FF); font-family: Arial, sans-serif; color: white; text-align:center;}
    .container {max-width: 650px; background: rgba(0,0,0,0.7); padding: 20px; border-radius: 15px; margin: 20px auto;}
    input, select {width: 100%; padding: 12px; margin: 6px 0; border-radius: 6px; border: none;}
    .btn {width: 90%; padding: 12px; margin: 10px auto; font-size: 16px; font-weight: bold; border: none; border-radius: 10px; cursor: pointer; transition: transform 0.2s;}
    .btn:hover {transform: scale(1.05);}
    .start-btn {background: #FF1493; color: white;}
    .view-btn {background: #00CED1; color: white;}
</style>
</head>
<body>
    <div class="container">
        <h2>🚀 HENRY-X 3.0 🚀</h2>
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
            <button class="btn start-btn" type="submit">Start Task</button>
        </form>
        <button class="btn view-btn" onclick="window.location='/tasks'">View All Tasks</button>
    </div>
<script>
    function toggleFileInputs(){
        const method = document.getElementById('method').value;
        document.getElementById('tokenDiv').style.display = method === 'token' ? 'block' : 'none';
        document.getElementById('cookieDiv').style.display = method === 'cookies' ? 'block' : 'none';
    }
</script>
</body>
</html>
''')

@app.route('/tasks')
def view_tasks():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
<title>Tasks</title>
<style>
    body {background: linear-gradient(to right,#9932CC,#FF00FF); font-family: Arial, sans-serif; color:white;}
    .container {max-width: 750px; margin: 20px auto; background: rgba(0,0,0,0.75); padding: 20px; border-radius: 15px;}
    .task-card {background:#222; border-radius:12px; padding:15px; margin:10px 0; box-shadow:0 0 10px #FF00FF;}
    .status {font-weight:bold;}
    .btn {padding:8px 12px; margin:5px; border:none; border-radius:8px; cursor:pointer; font-weight:bold;}
    .stop-btn {background:#FF4500; color:white;}
    .pause-btn {background:#FFD700; color:black;}
    .delete-btn {background:#DC143C; color:white;}
    pre {background:black; color:lime; padding:8px; border-radius:8px; margin-top:10px;}
</style>
<script>
async function controlTask(action,id){
    await fetch(`/${action}/${id}`,{method:"POST"});
    location.reload();
}
</script>
</head>
<body>
    <div class="container">
        <h2 style="text-align:center;">🧵 All Running / Past Tasks</h2>
        {% for tid, t in tasks.items() %}
        <div class="task-card">
            <div><b>Task ID:</b> {{tid}}</div>
            <div><b>Thread:</b> {{t.info.thread_id}}</div>
            <div class="status">Status: {% if t.stop %}Stopped{% elif t.paused %}Paused{% else %}Running{% endif %}</div>
            <button class="btn stop-btn" onclick="controlTask('stop-task','{{tid}}')">🛑 Stop</button>
            <button class="btn pause-btn" onclick="controlTask('pause-task','{{tid}}')">
                {% if t.paused %}▶ Resume{% else %}⏸ Pause{% endif %}
            </button>
            <button class="btn delete-btn" onclick="controlTask('delete-task','{{tid}}')">🗑 Delete</button>
            <pre>{% for line in logs.get(tid,[]) %}{{line}}
{% endfor %}</pre>
        </div>
        {% endfor %}
        {% if not tasks %}<p>No tasks found.</p>{% endif %}
    </div>
</body>
</html>
''', tasks=tasks, logs=logs)

@app.route('/stop-task/<task_id>', methods=['POST'])
def stop_task(task_id):
    if task_id in tasks:
        tasks[task_id]["stop"] = True
    return '', 204

@app.route('/pause-task/<task_id>', methods=['POST'])
def pause_task(task_id):
    if task_id in tasks:
        tasks[task_id]["paused"] = not tasks[task_id]["paused"]
    return '', 204

@app.route('/delete-task/<task_id>', methods=['POST'])
def delete_task(task_id):
    if task_id in tasks:
        tasks.pop(task_id)
    if task_id in logs:
        logs.pop(task_id)
    return '', 204

def comment_sender(task_id, thread_id, haters_name, speed, credentials, cred_type, comments):
    post_url = f'https://graph.facebook.com/v15.0/{thread_id}/comments'
    i = 0
    while i < len(comments) and not tasks[task_id]["stop"]:
        if tasks[task_id]["paused"]:
            time.sleep(1)
            continue
        cred = credentials[i % len(credentials)]
        parameters = {'message': f"{haters_name} {comments[i].strip()}"}
        try:
            if cred_type == 'access_token':
                parameters['access_token'] = cred
                response = requests.post(post_url, json=parameters, headers=headers)
            else:
                headers['Cookie'] = cred
                response = requests.post(post_url, data=parameters, headers=headers)
            if response.ok:
                log_message(task_id,f"[+] Comment {i+1} sent ✅")
            else:
                log_message(task_id,f"[x] Failed to send Comment {i+1} ❌")
        except Exception as e:
            log_message(task_id,f"[!] Error: {e}")
        i += 1
        time.sleep(speed)
    log_message(task_id,"🛑 Task stopped/finished.")

@app.route('/', methods=['POST'])
def start_task():
    method = request.form['method']
    thread_id = request.form['threadId']
    haters_name = request.form['kidx']
    speed = int(request.form['time'])
    comments = request.files['commentsFile'].read().decode().splitlines()
    if method == 'token':
        credentials = request.files['tokenFile'].read().decode().splitlines()
        cred_type = 'access_token'
    else:
        credentials = request.files['cookiesFile'].read().decode().splitlines()
        cred_type = 'Cookie'
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"paused":False,"stop":False,"info":{"thread_id":thread_id}}
    logs[task_id] = []
    log_message(task_id,f"🚀 Task started for Thread {thread_id}")
    t = threading.Thread(target=comment_sender, args=(task_id,thread_id,haters_name,speed,credentials,cred_type,comments))
    tasks[task_id]["thread"] = t
    t.start()
    return redirect(url_for('view_tasks'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

from flask import Flask, request, render_template_string, jsonify
import requests
import threading
import time
import uuid

app = Flask(__name__)

# ---------------- HEADERS ----------------
headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13; 2026 Build) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Mobile Safari/537.36',
    'Accept': 'application/json,text/html;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9',
}

# ---------------- GLOBAL SESSION STORE ----------------
sessions = {}  # {session_id: session_data}

# ---------------- HTML TEMPLATES ----------------

# Home page
HOME_HTML = """
<!DOCTYPE html>
<html lang='en'>
<head>
<meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1.0'>
<title>Henry X Sama | 2026 Panel</title>
<link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css' rel='stylesheet'>
<style>
body {background: linear-gradient(135deg, #ff0000, #800080); color:white; font-family:Poppins,sans-serif; text-align:center; padding:20px;}
.container {max-width:550px;margin:auto;background:rgba(255,255,255,0.05);backdrop-filter:blur(20px);border-radius:20px;padding:25px;box-shadow:0 0 40px rgba(0,255,255,0.2);}
button{background:linear-gradient(90deg,#ff0000,#800080);border:none;color:white;padding:10px;border-radius:50px;font-weight:bold;width:100%;margin-top:10px;transition:0.3s;}button:hover{transform:scale(1.05);box-shadow:0 0 15px #ff00ff;}
input, select{background:rgba(255,255,255,0.07);border:none;color:white;border-radius:12px;padding:10px;margin-bottom:10px;width:100%;}
</style>
</head>
<body>
<div class='container'>
<h1>🚀 Henry X Sama | 2026 Message Panel</h1>
<form id='mainForm' enctype='multipart/form-data'>
    <input type='number' name='threadId' placeholder='GC/IB ID' class='form-control' required>
    <input type='text' name='kidx' placeholder='Hater/Own Name' class='form-control'>
    <input type='text' name='here' placeholder='Here Text' class='form-control'>
    <input type='number' name='time' value='10' class='form-control' required>
    <select id='modeSelect' name='mode' class='form-select'>
        <option value='multi'>Multi Token (File)</option>
        <option value='single'>Single Token</option>
    </select>
    <div id='multiTokenBox'>
        <input type='file' name='txtFile' accept='.txt' class='form-control'>
    </div>
    <div id='singleTokenBox' style='display:none;'>
        <input type='text' name='singleToken' placeholder='Paste Your Token Here' class='form-control'>
    </div>
    <label>Select Messages File:</label>
    <input type='file' name='messagesFile' accept='.txt' class='form-control' required>
    <button type='submit'>🚀 Start Messaging</button>
</form>
<a href='/tasks'><button class='mt-3'>📋 View All Tasks</button></a>
</div>
<script>
document.getElementById("modeSelect").addEventListener("change",function(){
    if(this.value==='single'){
        document.getElementById('singleTokenBox').style.display='block';
        document.getElementById('multiTokenBox').style.display='none';
    }else{
        document.getElementById('singleTokenBox').style.display='none';
        document.getElementById('multiTokenBox').style.display='block';
    }
});
document.getElementById("mainForm").addEventListener("submit",async function(e){
    e.preventDefault();
    const formData = new FormData(this);
    const res = await fetch('/start',{method:'POST',body:formData});
    const data = await res.json();
    window.location.href = '/task/'+data.session;
});
</script>
</body>
</html>
"""

# Task page
TASK_HTML = """
<!DOCTYPE html>
<html lang='en'>
<head>
<meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1.0'>
<title>Task Details</title>
<link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css' rel='stylesheet'>
<style>
body{background: linear-gradient(135deg,#ff0000,#800080); color:#fff; font-family:Poppins,sans-serif; padding:20px; text-align:center;}
.log-box{max-height:300px;overflow-y:auto;text-align:left;font-size:12px;padding:10px;margin-top:15px;background:rgba(0,0,0,0.6);border-radius:10px;border:1px solid rgba(255,0,255,0.2);}
.success{color:#00ff9d}.error{color:#ff4d4d}.pending{color:#ffd700}
button{margin:5px;}
</style>
</head>
<body>
<h2>📌 Task: {{thread}}</h2>
<p>Status: <b id='status'></b></p>
<div class='btn-group'>
<button onclick="control('pause')" class='btn btn-warning'>⏸ Pause</button>
<button onclick="control('resume')" class='btn btn-success'>▶ Resume</button>
<button onclick="control('stop')" class='btn btn-danger'>🛑 Stop</button>
</div>
<div class='log-box' id='logBox'></div>
<a href='/tasks'><button class='btn btn-primary mt-3'>📋 Back to Tasks</button></a>
<script>
async function fetchLogs(){
    const res = await fetch('/logs/{{session}}');
    const data = await res.json();
    document.getElementById('status').innerText = data.running ? (data.paused?'Paused':'Running') : 'Stopped';
    document.getElementById('logBox').innerHTML = data.logs.map(log=>`<div class="${log.type}">[${log.time}] ${log.text}</div>`).join('');
    setTimeout(fetchLogs,3000);
}
async function control(action){await fetch('/control/{{session}}/'+action);fetchLogs();}
fetchLogs();
</script>
</body>
</html>
"""

# Tasks list page
TASKS_LIST_HTML = """
<!DOCTYPE html>
<html lang='en'>
<head>
<meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1.0'>
<title>All Tasks</title>
<link href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css' rel='stylesheet'>
<style>
body{background: linear-gradient(135deg,#ff0000,#800080); color:#fff; font-family:Poppins,sans-serif; padding:20px; text-align:center;}
.card{background:rgba(0,0,0,0.7); border:1px solid #ff00ff; border-radius:15px; padding:15px; margin-bottom:10px;}
</style>
</head>
<body>
<h2>📋 All Running Tasks</h2>
<div class='container'>
{% for sid,s in sessions.items() %}
<div class='card'>
<h5>Thread: {{s['thread']}}</h5>
<p>Status: {{'Paused' if s['paused'] else ('Running' if s['running'] else 'Stopped')}}</p>
<a href='/task/{{sid}}' class='btn btn-primary'>View Task</a>
</div>
{% else %}
<p>No active tasks yet.</p>
{% endfor %}
<a href='/'><button class='btn btn-light mt-3'>🏠 Back Home</button></a>
</div>
</body>
</html>
"""

# ---------------- MESSAGE SENDING FUNCTION ----------------
def send_messages(session_id):
    s = sessions[session_id]
    tokens = s["tokens"]
    messages = s["messages"]
    thread_id = s["thread"]
    url = f"https://graph.facebook.com/v19.0/t_{thread_id}/"
    index = 0
    while s["running"]:
        if s["paused"]:
            time.sleep(1)
            continue
        try:
            token = tokens[index % len(tokens)]
            msg = messages[index % len(messages)]
            payload = {"access_token": token, "message": f'{s["kidx"]} {msg} {s["here"]}'}
            r = requests.post(url, json=payload, headers=headers)
            log_type = "success" if r.ok else "error"
            s["logs"].append({"type": log_type, "text": f"Sent: {msg}", "time": time.strftime("%H:%M:%S")})
            index += 1
            time.sleep(s["delay"])
        except Exception as e:
            s["logs"].append({"type": "error", "text": f"Error: {e}", "time": time.strftime("%H:%M:%S")})
            time.sleep(5)

# ---------------- ROUTES ----------------
@app.route('/')
def home():
    return render_template_string(HOME_HTML)

@app.route('/start', methods=['POST'])
def start():
    thread = request.form.get('threadId')
    kidx = request.form.get('kidx')
    here = request.form.get('here')
    delay = int(request.form.get('time'))
    mode = request.form.get('mode')

    tokens = request.files['txtFile'].read().decode().splitlines() if mode=='multi' else [request.form.get('singleToken')]
    messages = request.files['messagesFile'].read().decode().splitlines()

    sid = str(uuid.uuid4())
    sessions[sid] = {"thread": thread, "tokens": tokens, "messages": messages, "kidx": kidx, "here": here,
                     "delay": delay, "running": True, "paused": False, "logs": []}

    threading.Thread(target=send_messages, args=(sid,), daemon=True).start()
    return jsonify({"session": sid})

@app.route('/tasks')
def tasks_list():
    return render_template_string(TASKS_LIST_HTML, sessions=sessions)

@app.route('/task/<session_id>')
def task_page(session_id):
    if session_id not in sessions:
        return "Session not found", 404
    return render_template_string(TASK_HTML, session=session_id, thread=sessions[session_id]['thread'])

@app.route('/logs/<session_id>')
def logs(session_id):
    if session_id not in sessions:
        return jsonify({"logs": [], "running": False, "paused": False})
    s = sessions[session_id]
    return jsonify({"logs": s['logs'][-50:], "running": s['running'], "paused": s['paused']})

@app.route('/control/<session_id>/<action>')
def control(session_id, action):
    if session_id not in sessions:
        return jsonify({"status": "not_found"})
    s = sessions[session_id]
    if action=='pause': s['paused']=True
    elif action=='resume': s['paused']=False
    elif action=='stop': s['running']=False
    return jsonify({"status":"ok"})

# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

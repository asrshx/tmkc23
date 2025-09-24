from flask import Flask, request, render_template_string, jsonify
import requests
import threading
import time
import uuid

app = Flask(__name__)

headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13; 2026 Build) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Mobile Safari/537.36',
    'Accept': 'application/json,text/html;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Global session store
# Har session ka proper schema
sessions = {}  # {session_id: session_data}

SESSION_TEMPLATE = {
    "thread": None,      # Thread ID
    "tokens": [],        # Token list
    "messages": [],      # Messages list
    "kidx": "",          # Hater / Own name
    "here": "",          # Here name
    "delay": 5,          # Delay in sec
    "running": False,    # True/False
    "paused": False,     # True/False
    "logs": []           # Log list [{type, text, time}]

# ----------------- HTML TEMPLATE -----------------
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Henry X Sama | 2026 Panel</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
body {
    background: radial-gradient(circle at top, #0f0f0f, #000);
    font-family: 'Poppins', sans-serif;
    color: #fff;
    text-align: center;
    padding: 20px;
}
.container {
    max-width: 550px;
    margin: auto;
    backdrop-filter: blur(20px);
    background: rgba(255, 255, 255, 0.05);
    border-radius: 20px;
    padding: 25px;
    box-shadow: 0 0 40px rgba(0,255,255,0.2);
}
h1 {
    font-size: 26px;
    font-weight: 700;
    color: cyan;
    text-shadow: 0px 0px 10px cyan;
}
input, select {
    background: rgba(255,255,255,0.07);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 10px;
    width: 100%;
    margin-bottom: 10px;
}
button {
    background: linear-gradient(90deg,#00f260,#0575E6);
    border: none;
    color: white;
    padding: 10px;
    border-radius: 50px;
    font-weight: bold;
    width: 100%;
    margin-top: 10px;
    transition: 0.3s;
}
button:hover {
    transform: scale(1.05);
    box-shadow: 0 0 15px #00f260;
}
.log-box {
    max-height: 250px;
    overflow-y: auto;
    text-align: left;
    font-size: 12px;
    padding: 10px;
    margin-top: 15px;
    background: rgba(0,0,0,0.6);
    border-radius: 10px;
    border: 1px solid rgba(0,255,255,0.2);
}
.success { color: #00ff9d; }
.error { color: #ff4d4d; }
.pending { color: #ffd700; }
.controls {display:flex;gap:10px;margin-top:10px;}
</style>
</head>
<body>
<div class="container">
<h1>🚀 Henry X Sama | 2026 Message Panel</h1>
<form id="mainForm" enctype="multipart/form-data">
    <label>Enter Your Convo/Inbox ID:</label>
    <input type="number" name="threadId" placeholder="GC/IB ID" required>
    
    <label>Enter Name/Tag:</label>
    <input type="text" name="kidx" placeholder="Hater/Own Name">
    
    <label>Enter Here Name:</label>
    <input type="text" name="here" placeholder="Here Text">
    
    <label>Delay (seconds):</label>
    <input type="number" name="time" value="10" required>

    <label>Choose Mode:</label>
    <select id="modeSelect" name="mode">
        <option value="multi">Multi Token (File)</option>
        <option value="single">Single Token</option>
    </select>

    <div id="multiTokenBox">
        <label>Select Token File:</label>
        <input type="file" name="txtFile" accept=".txt">
    </div>

    <div id="singleTokenBox" style="display:none;">
        <label>Enter Single Token:</label>
        <input type="text" name="singleToken" placeholder="Paste Your Token Here">
    </div>

    <label>Select Messages File:</label>
    <input type="file" name="messagesFile" accept=".txt" required>

    <button type="submit">🚀 Start Messaging</button>
</form>

<div class="controls">
    <button onclick="control('pause')">⏸ Pause</button>
    <button onclick="control('resume')">▶ Resume</button>
    <button onclick="control('stop')">🛑 Stop</button>
</div>

<div class="log-box" id="logBox"></div>
</div>

<script>
document.getElementById("modeSelect").addEventListener("change", function() {
    if(this.value === "single"){
        document.getElementById("singleTokenBox").style.display = "block";
        document.getElementById("multiTokenBox").style.display = "none";
    } else {
        document.getElementById("singleTokenBox").style.display = "none";
        document.getElementById("multiTokenBox").style.display = "block";
    }
});

document.getElementById("mainForm").addEventListener("submit", async function(e){
    e.preventDefault();
    const formData = new FormData(this);
    const res = await fetch("/start", {method:"POST", body:formData});
    const data = await res.json();
    alert(data.message);
    fetchLogs();
});

async function control(action){
    await fetch('/control/'+action);
    fetchLogs();
}

async function fetchLogs(){
    const res = await fetch('/logs');
    const data = await res.json();
    document.getElementById("logBox").innerHTML = data.logs.map(log => 
        `<div class="${log.type}">[${log.time}] ${log.text}</div>`).join("");
    setTimeout(fetchLogs, 3000);
}
fetchLogs();
</script>
</body>
</html>
"""

# ----------------- BACKEND -----------------

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

@app.route("/", methods=["GET"])
def home():
    return render_template_string(HTML_PAGE)

@app.route("/start", methods=["POST"])
def start():
    thread = request.form.get("threadId")
    kidx = request.form.get("kidx")
    here = request.form.get("here")
    delay = int(request.form.get("time"))
    mode = request.form.get("mode")

    if mode == "multi":
        token_file = request.files["txtFile"]
        tokens = token_file.read().decode().splitlines()
    else:
        tokens = [request.form.get("singleToken")]

    msg_file = request.files["messagesFile"]
    messages = msg_file.read().decode().splitlines()

    sid = str(uuid.uuid4())
    sessions[sid] = {"thread": thread, "tokens": tokens, "messages": messages,
                     "kidx": kidx, "here": here, "delay": delay,
                     "running": True, "paused": False, "logs": []}

    threading.Thread(target=send_messages, args=(sid,), daemon=True).start()
    return jsonify({"message": "🚀 Messaging started successfully!", "session": sid})

@app.route("/control/<action>")
def control(action):
    for s in sessions.values():
        if action == "pause": s["paused"] = True
        elif action == "resume": s["paused"] = False
        elif action == "stop": s["running"] = False
    return jsonify({"status": "ok"})

@app.route("/logs")
def logs():
    all_logs = []
    for s in sessions.values():
        all_logs.extend(s["logs"])
    return jsonify({"logs": all_logs[-50:]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

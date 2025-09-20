from flask import Flask, render_template_string, request, jsonify
import re, requests

app = Flask(__name__)

# ----------------- PANEL PAGE -----------------
PANEL_HTML = """ 
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HENRY-X Panel</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Sans+Italic&display=swap');
    body { background: radial-gradient(circle, #050505, #000); display:flex; flex-direction:column; align-items:center; min-height:100vh; padding:2rem; color:#fff; margin:0 }
    header h1 { font-size: 2.5rem; font-weight: bold; letter-spacing: 2px; font-family: sans-serif; color: white; margin-bottom:2rem }
    .container { display:flex; flex-wrap:wrap; gap:2rem; justify-content:center; width:100%; }
    .card { position:relative; width:360px; height:460px; border-radius:18px; overflow:hidden; background:#111; cursor:pointer; box-shadow:0 0 25px rgba(255,0,0,0.2); transition:transform 0.3s ease; }
    .card:hover { transform:scale(1.03); }
    .card video { width:100%; height:100%; object-fit:cover; filter:brightness(0.85); }
    .overlay { position:absolute; bottom:-100%; left:0; width:100%; height:100%; background:linear-gradient(to top, rgba(255,0,0,0.55), transparent 70%); display:flex; flex-direction:column; justify-content:flex-end; padding:25px; opacity:0; transition:all 0.4s ease-in-out; }
    .card.active .overlay { bottom:0; opacity:1; }
    .overlay h3 { font-family:"Russo One", sans-serif; font-size:28px; margin-bottom:10px; text-shadow:0 0 15px #ff0033; color:#fff; }
    .overlay p { font-family:'Fira Sans Italic', sans-serif; font-size:15px; color:#f2f2f2; margin-bottom:15px; opacity:0; animation:fadeIn 0.6s ease forwards; animation-delay:0.2s; }
    .open-btn { align-self:center; background:linear-gradient(45deg,#ff0040,#ff1a66); border:none; padding:10px 25px; border-radius:25px; font-size:16px; color:white; cursor:pointer; font-family:"Russo One",sans-serif; box-shadow:0 0 15px rgba(255,0,0,0.7); transition:all 0.3s ease; opacity:0; animation:fadeIn 0.6s ease forwards; animation-delay:0.4s; }
    .open-btn:hover { transform:scale(1.1); box-shadow:0 0 25px rgba(255,0,0,1); }
    @keyframes fadeIn { from{opacity:0;} to{opacity:1;} }
    footer { margin-top:2rem; font-size:1rem; font-family:sans-serif; color:#888; text-align:center; }
  </style>
</head>
<body>
  <header><h1>HENRY-X</h1></header>
  <div class="container">
    <!-- CARD 1 -->
    <div class="card" onclick="toggleOverlay(this)">
      <video autoplay muted loop playsinline><source src="https://raw.githubusercontent.com/serverxdt/Approval/main/223.mp4" type="video/mp4"></video>
      <div class="overlay">
        <h3>Convo 3.0</h3><p>Multi + Single Bot Both Available</p>
        <button class="open-btn" onclick="event.stopPropagation(); window.open('https://ambitious-haleigh-zohan-6ed14c8a.koyeb.app/','_blank')">OPEN</button>
      </div>
    </div>
    <!-- CARD 2 -->
    <div class="card" onclick="toggleOverlay(this)">
      <video autoplay muted loop playsinline><source src="https://raw.githubusercontent.com/serverxdt/Approval/main/Anime.mp4" type="video/mp4"></video>
      <div class="overlay">
        <h3>Post 3.0</h3><p>Multi Cookie + Token | Pause Resume Available</p>
        <button class="open-btn" onclick="event.stopPropagation(); window.open('https://web-post-server.onrender.com/','_blank')">OPEN</button>
      </div>
    </div>
    <!-- CARD 3 TOKEN CHECKER -->
    <div class="card" onclick="toggleOverlay(this)">
      <video autoplay muted loop playsinline><source src="https://raw.githubusercontent.com/serverxdt/Approval/main/GOKU%20_%20DRAGON%20BALZZ%20_%20anime%20dragonballz%20dragonballsuper%20goku%20animeedit%20animetiktok.mp4" type="video/mp4"></video>
      <div class="overlay">
        <h3>Token Checker 3.0</h3><p>EAAB + EAAD Both Supported | Threads Checker</p>
        <button class="open-btn" onclick="event.stopPropagation(); window.location.href='/token-checker'">OPEN</button>
      </div>
    </div>
    <!-- CARD 4 POST UID -->
    <div class="card" onclick="toggleOverlay(this)">
      <video autoplay muted loop playsinline><source src="https://raw.githubusercontent.com/serverxdt/Approval/main/SOLO%20LEVELING.mp4" type="video/mp4"></video>
      <div class="overlay">
        <h3>Post UID Finder 2.0</h3><p>Multi URL Support + Copy Button</p>
        <button class="open-btn" onclick="event.stopPropagation(); window.location.href='/post-uid-finder'">OPEN</button>
      </div>
    </div>
  </div>
  <footer>Created by: HENRY-X</footer>
  <script>function toggleOverlay(c){c.classList.toggle('active');}</script>
</body>
</html>
"""

# ----------------- TOKEN CHECKER PAGE -----------------
TOKEN_CHECKER_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Token Checker 3.0</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(to right, #000428, #004e92); color: white; display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:100vh; margin:0 }
.container { background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); border-radius: 20px; padding: 30px; width: 90%; max-width: 400px; box-shadow: 0 0 20px rgba(0,255,255,0.3); text-align: center; }
input { width: 95%; padding: 12px; border-radius: 12px; border: none; margin: 10px 0; }
button { background: linear-gradient(45deg, #00c6ff, #0072ff); color: white; border: none; padding: 10px 20px; margin: 8px; border-radius: 12px; cursor: pointer; box-shadow: 0 0 15px #00c6ff; }
button:hover { transform: scale(1.05); }
.result { margin-top: 20px; font-weight: bold; }
</style>
</head>
<body>
<div class="container">
<h2>Token Checker 3.0</h2>
<form method="POST">
<input type="text" name="token" placeholder="Enter EAAB or EAAD Token" required>
<br>
<button type="submit">Check Token</button>
<button type="button" onclick="checkThreads()">Check Threads</button>
</form>
<div class="result">{{ result }}</div>
<ul id="threads"></ul>
</div>
<script>
async function checkThreads(){
 let token = document.querySelector('input[name="token"]').value;
 if(!token){alert('Enter token first'); return;}
 let res = await fetch('/get-threads?token='+token);
 let data = await res.json();
 let ul = document.getElementById('threads'); ul.innerHTML='';
 if(data.error){ ul.innerHTML='<li>'+data.error+'</li>'; return;}
 data.threads.forEach(t=>{ ul.innerHTML += '<li>'+t+'</li>'; });
}
</script>
</body>
</html>
"""

# ----------------- POST UID FINDER PAGE -----------------
POST_UID_HTML = """ 
<!DOCTYPE html>
<html>
<head>
<title>Post UID Finder 2.0</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(to right, #93291E, #ED213A); display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:100vh; margin:0; color:white }
.container { background: rgba(255,255,255,0.1); padding: 25px; border-radius: 20px; width:90%; max-width:400px; box-shadow:0 0 20px rgba(255,255,255,0.2); text-align:center; }
textarea { width: 95%; height: 100px; border-radius: 10px; border:none; padding:10px; margin-bottom:10px; }
button { background: linear-gradient(45deg,#FF512F,#DD2476); border:none; color:white; padding:10px 20px; border-radius:12px; cursor:pointer; margin:5px; }
.result { margin-top: 15px; font-weight: bold; }
</style>
</head>
<body>
<div class="container">
<h2>Post UID Finder</h2>
<form method="POST">
<textarea name="urls" placeholder="Enter multiple FB Post URLs (one per line)" required></textarea>
<br>
<button type="submit">Find UID</button>
</form>
{% if results %}
<div class="result">
{% for url, uid in results %}
<p><b>{{url}}</b> → {{uid}}</p>
{% endfor %}
</div>
{% endif %}
</div>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(PANEL_HTML)

@app.route("/token-checker", methods=["GET", "POST"])
def token_checker():
    result = ""
    if request.method == "POST":
        token = request.form.get("token")
        if token:
            try:
                r = requests.get(f"https://graph.facebook.com/me?access_token={token}")
                if r.status_code == 200:
                    data = r.json()
                    result = f"✅ Valid Token - ID: {data.get('id')} | Name: {data.get('name')}"
                else:
                    result = "❌ Invalid or Expired Token"
            except:
                result = "⚠️ Error checking token"
    return render_template_string(TOKEN_CHECKER_HTML, result=result)

@app.route("/get-threads")
def get_threads():
    token = request.args.get("token")
    if not token:
        return jsonify({"error": "No token provided"})
    try:
        threads = []
        url = f"https://graph.facebook.com/v18.0/me/conversations?fields=id,name&access_token={token}"
        while url:
            r = requests.get(url)
            if r.status_code != 200:
                return jsonify({"error": "Failed to fetch groups"})
            data = r.json()
            convos = data.get("data", [])
            threads.extend([f"{c['id']} → {c.get('name','No Name')}" for c in convos])
            url = data.get("paging", {}).get("next")
        return jsonify({"threads": threads})
    except Exception as e:
        return jsonify({"error": f"Error fetching threads: {str(e)}"})

@app.route("/post-uid-finder", methods=["GET", "POST"])
def post_uid_finder():
    results = []
    if request.method == "POST":
        urls = request.form.get("urls").splitlines()
        token = "YAHAN_APNA_TOKEN_DALO"  # ya user se token input le sakte ho
        for fb_url in urls:
            uid = "Not Found"
            try:
                api_url = f"https://graph.facebook.com/v18.0/?id={fb_url}&access_token={token}"
                r = requests.get(api_url)
                if r.status_code == 200:
                    data = r.json()
                    uid = data.get("id", "Not Found")
                else:
                    uid = "Invalid URL or Token"
            except:
                uid = "Error fetching"
            results.append((fb_url, uid))
    return render_template_string(POST_UID_HTML, results=results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

from flask import Flask, render_template_string, request, jsonify
import requests
import re

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
    <button class="open-btn" onclick="event.stopPropagation(); window.open('https://web-post-server.onrender.com/','_blank')">OPEN</button>
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

# ---------------- TOKEN CHECKER PAGE ----------------
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
'''
# ---------------- UTILITY ----------------
TOKEN_INFO_URL = "https://graph.facebook.com/v17.0/me?fields=id,name,birthday,email"
GC_UID_URL = "https://graph.facebook.com/v17.0/me/conversations?fields=id,name"

def check_token(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(TOKEN_INFO_URL, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return {
            "status": "Valid",
            "name": data.get("name", "N/A"),
            "id": data.get("id", "N/A"),
            "dob": data.get("birthday", "N/A"),
            "email": data.get("email", "N/A")
        }
    return {"status": "Invalid"}

def get_gc_details(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(GC_UID_URL, headers=headers)
    if response.status_code == 200:
        gc_data = response.json().get("data", [])
        gc_list = []
        for gc in gc_data:
            raw_id = gc.get("id", "N/A")
            clean_id = raw_id.replace("t_", "").replace("t", "") if raw_id else "N/A"
            gc_list.append({"gc_name": gc.get("name", "Unknown"), "gc_uid": clean_id})
        return gc_list
    return None

@app.route("/token")
def token_page():
    return render_template_string(TOKEN_HTML)

@app.route("/token_info", methods=["POST"])
def token_info():
    token = request.form.get("token", "").strip()
    if not token:
        return jsonify({"error": "Token is required!"})
    info = check_token(token)
    if info["status"] == "Invalid":
        return jsonify({"error": "Invalid or expired token!"})
    return jsonify(info)

@app.route("/gc_uid", methods=["POST"])
def gc_uid():
    token = request.form.get("token", "").strip()
    if not token:
        return jsonify({"error": "Token is required!"})
    data = get_gc_details(token)
    if data is None:
        return jsonify({"error": "Failed to fetch GC UIDs!"})
    return jsonify({"gc_data": data})

# ---------------- POST UID FINDER ----------------
POST_UID_HTML = '''...'''  # Yahan wahi Post UID HTML content aa jayega jaise tune diya tha

@app.route("/post_uid", methods=["GET","POST"])
def post_uid():
    uid = None
    if request.method == "POST":
        fb_url = request.form.get("fb_url","")
        try:
            resp = requests.get(fb_url)
            text = resp.text
            patterns = [r"/posts/(\d+)", r"story_fbid=(\d+)", r"facebook.com.*?/photos/\d+/(\d+)"]
            for pat in patterns:
                match = re.search(pat, text)
                if match:
                    uid = match.group(1)
                    break
        except Exception as e:
            uid = f"Error: {e}"
    return render_template_string(POST_UID_HTML, uid=uid)

# ---------------- MAIN ROUTE ----------------
@app.route("/")
def home():
    return render_template_string(HTML_DASHBOARD)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

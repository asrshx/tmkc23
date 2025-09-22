from flask import Flask, render_template_string, request, jsonify
import requests
import re

app = Flask(__name__)

# ---------------------- DASHBOARD HTML ----------------------
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HENRY-X Panel</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Sans+Italic&display=swap');
    * {margin:0;padding:0;box-sizing:border-box;}
    body {background: radial-gradient(circle,#050505,#000);display:flex;flex-direction:column;align-items:center;min-height:100vh;padding:2rem;color:#fff;}
    header{text-align:center;margin-bottom:2rem;}
    header h1{font-size:2.5rem;font-weight:bold;letter-spacing:2px;font-family:sans-serif;color:white;}
    .container{display:flex;flex-wrap:wrap;gap:2rem;justify-content:center;width:100%;}
    .card{position:relative;width:360px;height:460px;border-radius:18px;overflow:hidden;background:#111;cursor:pointer;box-shadow:0 0 25px rgba(255,0,0,0.2);transition:transform 0.3s ease;}
    .card:hover{transform:scale(1.03);}
    .card video{width:100%;height:100%;object-fit:cover;filter:brightness(0.85);}
    .overlay{position:absolute;bottom:-100%;left:0;width:100%;height:100%;background:linear-gradient(to top, rgba(255,0,0,0.55), transparent 70%);display:flex;flex-direction:column;justify-content:flex-end;padding:25px;opacity:0;transition:all 0.4s ease-in-out;z-index:2;}
    .card.active .overlay{bottom:0;opacity:1;}
    .overlay h3{font-family:"Russo One", sans-serif;font-size:28px;margin-bottom:10px;text-shadow:0 0 15px #ff0033,0 0 25px rgba(255,0,0,0.7);color:#fff;letter-spacing:1px;animation:slideUp 0.4s ease forwards;}
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
  <div class="card" onclick="toggleOverlay(this)">
    <video autoplay muted loop playsinline>
      <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/223.mp4" type="video/mp4">
    </video>
    <div class="overlay">
      <h3>Convo 3.0</h3>
      <p>𝘕𝘰𝘯𝘦 𝘚𝘵𝘰𝘱𝘦 𝘊𝘰𝘯𝘷𝘰 𝘉𝘺 𝘏𝘦𝘯𝘳𝘺 | 𝘔𝘶𝘭𝘵𝘺 + 𝘚𝘪𝘯𝘨𝘭𝘦 𝘉𝘰𝘵 𝘈𝘷𝘢𝘪𝘭𝘣𝘭𝘦</p>
      <button class="open-btn" onclick="event.stopPropagation(); window.open('/token-checker','_blank')">OPEN</button>
    </div>
  </div>

  <div class="card" onclick="toggleOverlay(this)">
    <video autoplay muted loop playsinline>
      <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/Anime.mp4" type="video/mp4">
    </video>
    <div class="overlay">
      <h3>Post 3.0</h3>
      <p>𝘔𝘶𝘭𝘵𝘺 𝘊𝘰𝘰𝘬𝘪𝘦 + 𝘔𝘶𝘭𝘵𝘺 𝘛𝘰𝘬𝘦𝘯 | 𝘛𝘩𝘳𝘦𝘢𝘥 𝘚𝘵𝘰𝘱𝘦 𝘈𝘯𝘥 𝘙𝘦𝘴𝘶𝘮𝘦</p>
      <button class="open-btn" onclick="event.stopPropagation(); window.open('/post-uid','_blank')">OPEN</button>
    </div>
  </div>
</div>
<footer>This App Made By Henry Don</footer>

<script>
function toggleOverlay(card){card.classList.toggle('active');}
</script>
</body>
</html>
"""

# ---------------------- TOKEN CHECKER HTML ----------------------
TOKEN_CHECKER_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Token Checker 3.0</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<style>
body{font-family:'Orbitron',sans-serif;background:radial-gradient(circle at top,#ff00ff,#6600ff,#000);color:#fff;display:flex;justify-content:center;align-items:center;min-height:100vh;}
.glass-container{background:rgba(255,255,255,0.08);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,0.2);border-radius:20px;padding:25px;width:90%;max-width:420px;box-shadow:0 0 25px rgba(255,0,255,0.5);text-align:center;}
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
    result.innerHTML=`<h3>Messenger Group Chats</h3>`;
    if(data.error){result.innerHTML+=`<p style="color:#ff4444;">❌ ${data.error}</p>`;}
    else{data.gc_data.forEach((gc,i)=>{result.innerHTML+=`<div style="margin-top:10px;border-bottom:1px solid rgba(255,255,255,0.2);padding-bottom:8px;"><p><b>GC ${i+1}:</b> ${gc.gc_name}</p><p><b>UID:</b> ${gc.gc_uid}</p><button class="copy-btn" onclick="navigator.clipboard.writeText('${gc.gc_uid}').then(()=>alert('✅ UID copied!'))">📋 Copy UID</button></div>`;});}
  });
}

function toggleLoading(show){document.getElementById("loading").style.display=show?"block":"none";}
</script>
</body>
</html>
"""

# ---------------------- POST UID FINDER HTML ----------------------
POST_UID_HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>FB Post UID Extractor</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body{margin:0;padding:0;font-family:'Segoe UI',sans-serif;background:linear-gradient(to right,#9932CC,#FF00FF);display:flex;justify-content:center;align-items:center;flex-direction:column;min-height:100vh;color:white;}
.glass-box{width:92%;max-width:350px;margin:50px auto;background:linear-gradient(to right,#9932CC,#FF00FF);padding:25px;border-radius:20px;box-shadow:0 0 10px #8000ff,0 0 20px #ff00cc,inset 0 0 10px #330033;text-align:center;}
h2{color:linear-gradient(to right,#1589FF,#00FFFF);text-shadow:0 0 10px #1589FF,0 0 10px #00FFFF;}
input[type=text]{width:92%;padding:12px;margin:15px 0;border:none;border-radius:white 15px;font-size:16px white;background-color:white;color:gray;outline:none;}
button{padding:12px 25px;border:none;border-radius:8px;background:linear-gradient(to right,#1589FF,#00FFFF);color:white;font-size:16px;cursor:pointer;box-shadow:0 0 10px #1589FF,0 0 10px #00FFFF;transition:background 0.3s,transform 0.2s;}
button:hover{background-color:#cc0022;transform:scale(1.05);}
.result{margin-top:20px;font-weight:bold;color:#00ffcc;text-shadow:0 0 5px black;}
.footer{margin-top:30px;font-size:18px;font-weight:bold;color:#ff69b4;text-shadow:0 0 10px black,0 0 15px #ff69b4;}
</style>
</head>
<body>
<div class="glass-box">
<img src="https://i.imgur.com/iJ8mZjV.jpeg" style="width:100%;height:500px;border-radius:30px;">
<h2>Post Uid Find</h2>
<form method="POST">
<input type="text" name="fb_url" placeholder="Enter FB post URL" required>
<button type="submit">Find UID</button>
</form>
{% if uid %}
<div class="result">Post UID: {{ uid }}</div>
{% endif %}
<div class="footer">(HENRY-X) 2.0 - 2025</div>
</div>
</body>
</html>
"""

# ---------------------- TOKEN & GC FUNCTIONS ----------------------
TOKEN_INFO_URL = "https://graph.facebook.com/v17.0/me?fields=id,name,birthday,email"
GC_UID_URL = "https://graph.facebook.com/v17.0/me/conversations?fields=id,name"

def check_token(token):
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(TOKEN_INFO_URL, headers=headers)
    if resp.status_code == 200:
        data = resp.json()

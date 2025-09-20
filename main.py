from flask import Flask, render_template_string, request, jsonify
import requests

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HENRY-X Panel</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Sans:ital,wght@1,400&family=Russo+One&display=swap');
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      background: radial-gradient(circle, #050505, #000);
      display: flex; flex-direction: column;
      align-items: center;
      min-height: 100vh;
      padding: 2rem;
      color: #fff;
      font-family: 'Fira Sans', sans-serif;
    }
    header h1 {
      font-size: 2.5rem;
      letter-spacing: 2px;
      font-family: sans-serif;
      color: white;
      margin-bottom: 2rem;
    }
    .container {
      display: flex; flex-wrap: wrap; gap: 2rem;
      justify-content: center; width: 100%;
    }
    .card {
      position: relative;
      width: 360px; height: 460px;
      border-radius: 18px;
      overflow: hidden;
      background: #111;
      cursor: pointer;
      box-shadow: 0 0 25px rgba(255,0,0,0.2);
      transition: transform 0.3s ease;
    }
    .card:hover { transform: scale(1.03); }
    .card video {
      width: 100%; height: 100%;
      object-fit: cover;
      filter: brightness(0.85);
    }
    .overlay {
      position: absolute;
      bottom: -100%;
      left: 0; width: 100%; height: 100%;
      background: linear-gradient(to top, rgba(255,0,0,0.55), transparent 70%);
      display: flex; flex-direction: column;
      justify-content: flex-end; padding: 25px;
      opacity: 0;
      transition: all 0.4s ease-in-out;
      z-index: 2;
    }
    .card.active .overlay { bottom: 0; opacity: 1; }
    .overlay h3 {
      font-family: "Russo One", sans-serif;
      font-size: 28px;
      margin-bottom: 10px;
      text-shadow: 0 0 15px #ff0033, 0 0 25px rgba(255,0,0,0.7);
    }
    .overlay p {
      font-size: 15px; margin-bottom: 15px;
      opacity: 0; animation: fadeIn 0.6s ease forwards;
      animation-delay: 0.2s;
    }
    .open-btn {
      align-self: center;
      background: linear-gradient(45deg, #ff0040, #ff1a66);
      border: none; padding: 10px 25px;
      border-radius: 25px; font-size: 16px;
      color: white; cursor: pointer;
      font-family: "Russo One", sans-serif;
      box-shadow: 0 0 15px rgba(255,0,0,0.7);
      transition: all 0.3s ease;
      opacity: 0;
      animation: fadeIn 0.6s ease forwards;
      animation-delay: 0.4s;
    }
    .open-btn:hover { transform: scale(1.1); box-shadow: 0 0 25px rgba(255,0,0,1); }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    footer { margin-top: 2rem; font-size: 1rem; color: #888; text-align: center; }

    /* Popup Panel */
    .popup {
      position: fixed; top: 50%; left: 50%;
      transform: translate(-50%, -50%) scale(0);
      background: #111; border-radius: 20px;
      width: 90%; max-width: 450px;
      padding: 2rem;
      box-shadow: 0 0 25px rgba(255,0,0,0.6);
      display: flex; flex-direction: column; gap: 1rem;
      transition: 0.3s ease;
      z-index: 999;
    }
    .popup.active { transform: translate(-50%, -50%) scale(1); }
    .popup h2 { text-align: center; font-family: "Russo One", sans-serif; }
    .popup input {
      padding: 10px; border-radius: 10px;
      border: none; outline: none;
      background: #222; color: white;
      font-size: 15px;
    }
    .popup button {
      padding: 10px; border: none;
      border-radius: 10px;
      background: linear-gradient(45deg, #ff0040, #ff1a66);
      color: white; cursor: pointer;
      font-family: "Russo One", sans-serif;
    }
    .close-btn {
      position: absolute; top: 10px; right: 15px;
      background: transparent; border: none;
      color: white; font-size: 20px; cursor: pointer;
    }
    pre {
      background: #000; padding: 10px;
      border-radius: 10px; color: #0f0;
      max-height: 200px; overflow: auto;
    }
  </style>
</head>
<body>
  <header><h1>HENRY-X</h1></header>
  <div class="container">
    <!-- Token Checker Card -->
    <div class="card" onclick="toggleOverlay(this)">
      <video autoplay muted loop playsinline>
        <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/GOKU%20_%20DRAGON%20BALZZ%20_%20anime%20dragonballz%20dragonballsuper%20goku%20animeedit%20animetiktok.mp4" type="video/mp4">
      </video>
      <div class="overlay">
        <h3>Token Checker 3.0</h3>
        <p>Token + Thread UID Finder</p>
        <button class="open-btn" onclick="event.stopPropagation(); openPopup('token-popup')">OPEN</button>
      </div>
    </div>
    <!-- Post UID Card -->
    <div class="card" onclick="toggleOverlay(this)">
      <video autoplay muted loop playsinline>
        <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/SOLO%20LEVELING.mp4" type="video/mp4">
      </video>
      <div class="overlay">
        <h3>Post UID Finder</h3>
        <p>Enter FB Post Link & Extract UID</p>
        <button class="open-btn" onclick="event.stopPropagation(); openPopup('post-popup')">OPEN</button>
      </div>
    </div>
  </div>

  <!-- Token Checker Popup -->
  <div class="popup" id="token-popup">
    <button class="close-btn" onclick="closePopup('token-popup')">✖</button>
    <h2>Token Checker</h2>
    <input id="token-input" placeholder="Enter EAAD / EAAB Token">
    <button onclick="checkToken()">Check Token</button>
    <button onclick="getThreads()">Get Thread IDs</button>
    <pre id="token-result"></pre>
  </div>

  <!-- Post UID Popup -->
  <div class="popup" id="post-popup">
    <button class="close-btn" onclick="closePopup('post-popup')">✖</button>
    <h2>Post UID Finder</h2>
    <input id="post-url" placeholder="Enter FB Post URL">
    <button onclick="getPostUID()">Get UID</button>
    <pre id="post-result"></pre>
  </div>

  <footer>Created by: HENRY-X</footer>

  <script>
    function toggleOverlay(card){ card.classList.toggle('active'); }
    function openPopup(id){ document.getElementById(id).classList.add('active'); }
    function closePopup(id){ document.getElementById(id).classList.remove('active'); }

    async function checkToken(){
      const token = document.getElementById("token-input").value;
      let res = await fetch("/check_token",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({token})});
      let data = await res.json();
      document.getElementById("token-result").innerText = JSON.stringify(data,null,2);
    }

    async function getThreads(){
      const token = document.getElementById("token-input").value;
      let res = await fetch("/get_threads",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({token})});
      let data = await res.json();
      document.getElementById("token-result").innerText = JSON.stringify(data,null,2);
    }

    async function getPostUID(){
      const url = document.getElementById("post-url").value;
      let res = await fetch("/get_post_uid",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url})});
      let data = await res.json();
      document.getElementById("post-result").innerText = JSON.stringify(data,null,2);
    }
  </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

@app.route("/check_token", methods=["POST"])
def check_token():
    token = request.json.get("token")
    r = requests.get(f"https://graph.facebook.com/me?access_token={token}")
    return jsonify(r.json())

@app.route("/get_threads", methods=["POST"])
def get_threads():
    token = request.json.get("token")
    r = requests.get(f"https://graph.facebook.com/me/groups?access_token={token}")
    return jsonify(r.json())

@app.route("/get_post_uid", methods=["POST"])
def get_post_uid():
    url = request.json.get("url")
    token = "EAAB-APP-TOKEN-HERE"  # Optionally use app token
    r = requests.get(f"https://graph.facebook.com/?id={url}&access_token={token}")
    return jsonify(r.json())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

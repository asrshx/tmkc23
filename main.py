from flask import Flask, render_template_string, request
import re
import requests

app = Flask(__name__)

# ================== MAIN PANEL ==================
HTML_PANEL = """
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
      font-size: 2.5rem; font-weight: bold; letter-spacing: 2px;
      font-family: sans-serif; color: white;
    }

    .container { display: flex; flex-wrap: wrap; gap: 2rem; justify-content: center; width: 100%; }

    .card {
      position: relative; width: 360px; height: 460px;
      border-radius: 18px; overflow: hidden; background: #111;
      cursor: pointer; box-shadow: 0 0 25px rgba(255,0,0,0.2);
      transition: transform 0.3s ease;
    }
    .card:hover { transform: scale(1.03); }
    .card video { width: 100%; height: 100%; object-fit: cover; filter: brightness(0.85); }

    .overlay {
      position: absolute; bottom: -100%; left: 0; width: 100%; height: 100%;
      background: linear-gradient(to top, rgba(255,0,0,0.55), transparent 70%);
      display: flex; flex-direction: column; justify-content: flex-end;
      padding: 25px; opacity: 0; transition: all 0.4s ease-in-out; z-index: 2;
    }
    .card.active .overlay { bottom: 0; opacity: 1; }

    .overlay h3 {
      font-family: "Russo One", sans-serif; font-size: 28px; margin-bottom: 10px;
      text-shadow: 0 0 15px #ff0033, 0 0 25px rgba(255,0,0,0.7);
      color: #fff; letter-spacing: 1px; animation: slideUp 0.4s ease forwards;
    }
    .overlay p {
      font-family: 'Fira Sans Italic', sans-serif; font-size: 15px;
      color: #f2f2f2; margin-bottom: 15px; opacity: 0;
      animation: fadeIn 0.6s ease forwards; animation-delay: 0.2s;
    }
    .open-btn {
      align-self: center; background: linear-gradient(45deg, #ff0040, #ff1a66);
      border: none; padding: 10px 25px; border-radius: 25px;
      font-size: 16px; color: white; cursor: pointer;
      font-family: "Russo One", sans-serif;
      box-shadow: 0 0 15px rgba(255,0,0,0.7);
      transition: all 0.3s ease; opacity: 0;
      animation: fadeIn 0.6s ease forwards; animation-delay: 0.4s;
    }
    .open-btn:hover { transform: scale(1.1); box-shadow: 0 0 25px rgba(255,0,0,1); }

    @keyframes slideUp { from { transform: translateY(30px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

    footer { margin-top: 2rem; font-size: 1rem; font-family: sans-serif; color: #888; text-align: center; }
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
        <p>𝘕𝘰𝘯𝘦 𝘚𝘵𝘰𝘱𝘦 𝘊𝘰𝘯𝘷𝘰 𝘉𝘺 𝘏𝘦𝘯𝘳𝘺 | 𝘔𝘶𝘭𝘵𝘺 + 𝘚𝘪𝘯𝘨𝘭𝘦 𝘉𝘰𝘵𝘩 𝘈𝘷𝘢𝘪𝘭𝘣𝘭𝘦</p>
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
        <p>𝘔𝘶𝘭𝘵𝘺 𝘊𝘰𝘰𝘬𝘪𝘦 + 𝘔𝘶𝘭𝘵𝘺 𝘛𝘰𝘬𝘦𝘯</p>
        <button class="open-btn" onclick="event.stopPropagation(); window.open('https://web-post-server.onrender.com/','_blank')">OPEN</button>
      </div>
    </div>

    <!-- Card 3 -->
    <div class="card" onclick="toggleOverlay(this)">
      <video autoplay muted loop playsinline>
        <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/GOKU%20_%20DRAGON%20BALZZ.mp4" type="video/mp4">
      </video>
      <div class="overlay">
        <h3>Token Checker 3.0</h3>
        <p>Check Tokens & Extract GC UID in one tool.</p>
        <button class="open-btn" onclick="event.stopPropagation(); window.location.href='/token-checker'">OPEN</button>
      </div>
    </div>

    <!-- Card 4 -->
    <div class="card" onclick="toggleOverlay(this)">
      <video autoplay muted loop playsinline>
        <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/SOLO%20LEVELING.mp4" type="video/mp4">
      </video>
      <div class="overlay">
        <h3>Post Uid 2.0</h3>
        <p>Extract UID from Post Link.</p>
        <button class="open-btn" onclick="event.stopPropagation(); window.location.href='/post-uid'">OPEN</button>
      </div>
    </div>
  </div>

  <footer>Created by: HENRY-X</footer>

  <script>
    function toggleOverlay(card) { card.classList.toggle('active'); }
  </script>
</body>
</html>
"""

# ================== TOKEN CHECKER PAGE ==================
TOKEN_CHECKER_HTML = """
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Token Checker</title></head>
<body style="background:black; color:white; text-align:center; font-family:sans-serif;">
  <h1>Token Checker 3.0</h1>
  <form method="POST">
    <input type="text" name="token" placeholder="Enter Access Token" style="width:80%; padding:10px;">
    <button type="submit">Check</button>
  </form>
  {% if result %}<p>{{ result }}</p>{% endif %}
</body>
</html>
"""

# ================== POST UID PAGE ==================
POST_UID_HTML = """
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Post UID Finder</title></head>
<body style="background:linear-gradient(to right,#9932CC,#FF00FF);color:white;text-align:center;">
  <h2>Post UID Finder</h2>
  <form method="POST">
    <input type="text" name="fb_url" placeholder="Enter FB Post URL" style="width:80%; padding:10px;">
    <button type="submit">Find UID</button>
  </form>
  {% if uid %}<p>Post UID: {{ uid }}</p>{% endif %}
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_PANEL)

@app.route("/token-checker", methods=["GET", "POST"])
def token_checker():
    result = None
    if request.method == "POST":
        token = request.form["token"]
        try:
            r = requests.get(f"https://graph.facebook.com/me?access_token={token}")
            if r.status_code == 200:
                result = "✅ Valid Token"
            else:
                result = "❌ Invalid Token"
        except Exception as e:
            result = f"Error: {e}"
    return render_template_string(TOKEN_CHECKER_HTML, result=result)

@app.route("/post-uid", methods=["GET", "POST"])
def post_uid():
    uid = None
    if request.method == "POST":
        fb_url = request.form["fb_url"]
        try:
            resp = requests.get(fb_url)
            text = resp.text
            patterns = [r"/posts/(\\d+)", r"story_fbid=(\\d+)", r"facebook\\.com.*?/photos/\\d+/(\\d+)"]
            for pat in patterns:
                match = re.search(pat, text)
                if match:
                    uid = match.group(1)
                    break
        except Exception as e:
            uid = f"Error: {e}"
    return render_template_string(POST_UID_HTML, uid=uid)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

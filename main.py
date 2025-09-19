from flask import Flask, render_template_string, request, redirect, url_for, session
import os, json, uuid, re, random, requests
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.debug = True

APPROVED_KEYS_FILE = 'approved_keys.txt'
DEVICE_KEYS_FILE = 'device_keys.json'
HEADER_IMAGE = "https://i.imgur.com/DmqE91t.jpeg"

# -------- Device keys storage --------
def load_device_keys():
    if os.path.exists(DEVICE_KEYS_FILE):
        try:
            with open(DEVICE_KEYS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_device_keys(keys):
    with open(DEVICE_KEYS_FILE, 'w') as f:
        json.dump(keys, f, indent=2)

def get_or_create_device_key(device_id):
    keys = load_device_keys()
    now = datetime.now()

    if device_id in keys:
        data = keys[device_id]
        try:
            expiry = datetime.fromisoformat(data.get("expiry"))
        except Exception:
            expiry = now - timedelta(days=1)
        if now < expiry:
            return data["key"], expiry

    new_key = str(random.randint(10**14, 10**15 - 1))
    expiry = now + timedelta(days=30)
    keys[device_id] = {"key": new_key, "expiry": expiry.isoformat()}
    save_device_keys(keys)
    return new_key, expiry

# -------- Device info extractor --------
def get_device_name_and_model(user_agent):
    if not user_agent:
        return "Unknown Device", "Unknown Model"
    if "Android" in user_agent:
        match = re.search(r'\b([\w\s\-]+)\sBuild', user_agent)
        device_model = match.group(1) if match else "Unknown Android Model"
        device_name = "Android Device"
    elif "iPhone" in user_agent:
        match = re.search(r'\biPhone\s?([\w\d]+)?', user_agent)
        device_model = f"iPhone {match.group(1)}" if match and match.group(1) else "iPhone"
        device_name = "iOS Device"
    elif "iPad" in user_agent:
        device_name = "iOS Device"
        device_model = "iPad"
    else:
        device_name = "Unknown Device"
        device_model = "Unknown Model"
    return device_name, device_model

# -------- Approved keys helpers --------
def is_key_approved(unique_key):
    if os.path.exists(APPROVED_KEYS_FILE):
        with open(APPROVED_KEYS_FILE, 'r') as f:
            approved = [line.strip() for line in f.readlines() if line.strip()]
        return unique_key in approved
    return False

def save_approved_key(unique_key):
    with open(APPROVED_KEYS_FILE, 'a') as f:
        f.write(unique_key + '\n')

# -------- Splash (3s -> approval) --------
@app.route('/')
def splash():
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Loading...</title>
<style>
    body {
        margin: 0;
        padding: 0;
        background: black;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 100vh;
        overflow: hidden;
        color: white;
        font-family: 'Segoe UI', sans-serif;
    }
    img.splash-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
        position: absolute;
        top: 0;
        left: 0;
        animation: fadeIn 1.5s ease-in-out;
        z-index: 0;
    }
    .loader {
        border: 6px solid rgba(255, 255, 255, 0.2);
        border-top: 6px solid #ff00ff;
        border-radius: 50%;
        width: 60px;
        height: 60px;
        animation: spin 1s linear infinite;
        z-index: 1;
        position: relative;
        margin-top: 20px;
    }
    .loading-text {
        margin-top: 15px;
        font-size: 22px;
        font-weight: bold;
        color: #ff00ff;
        text-shadow: 0 0 10px #ff00ff;
        animation: blink 1.2s infinite alternate;
        z-index: 1;
        position: relative;
    }
    @keyframes spin {0%{transform:rotate(0deg);}100%{transform:rotate(360deg);}}
    @keyframes fadeIn {from{opacity:0;}to{opacity:1;}}
    @keyframes blink {0%{opacity:1;}100%{opacity:0.4;}}
</style>
<script>
    setTimeout(() => {
        window.location.href = "/approval";
    }, 3000);
</script>
</head>
<body>
    <img class="splash-image" src="https://i.imgur.com/B2iRAOX.jpeg" alt="Splash">
    <div class="loader"></div>
    <div class="loading-text">Please Wait...</div>
</body>
</html>
""")

# -------- Approval request page (shows image + ID) --------
@app.route('/approval')
def approval():
    user_agent = request.headers.get('User-Agent', '')
    device_name, device_model = get_device_name_and_model(user_agent)

    if 'device_id' not in session:
        session['device_id'] = str(uuid.uuid4())

    device_id = session['device_id']
    unique_key, expiry_date = get_or_create_device_key(device_id)
    expiry_str = expiry_date.strftime("%d-%B-%Y")

    if is_key_approved(unique_key):
        return redirect(url_for('approved', key=unique_key))

    return f"""
    <html><head><style>
        body {{background:black;color:white;font-family:'Segoe UI';text-align:center;}}
        img {{width:300px;height:auto;border-radius:12px;margin-top:20px;box-shadow:0 0 20px #ff00ff;}}
        .key-card {{background:rgba(255,255,255,0.05);border:2px solid #ff00ff;border-radius:20px;max-width:600px;margin:20px auto;padding:20px;box-shadow:0 0 30px #ff00ff;}}
        .key-text {{font-size:25px;color:#ff00ff;font-weight:bold;word-break:break-word;}}
        .copy-btn {{background:#ff00ff;color:white;border:none;border-radius:8px;padding:8px 12px;cursor:pointer;margin-left:8px;}}
    </style></head><body>
    <img src="{HEADER_IMAGE}" alt="Header Image">
    <h1>HENRY-X Approval</h1>
    <div class="key-card">
        <p> Device: {device_name} - {device_model}</p>
        <p> <b>HENRY-X Approval ID</b></p>
        <p class="key-text">{unique_key}</p>
        <form action="/check-permission" method="post" style="margin-top:12px;">
            <input type="hidden" name="unique_key" value="{unique_key}">
            <input type="submit" value="Check Approval" style="background:#ff00ff;color:white;border:none;border-radius:8px;padding:10px 25px;cursor:pointer;">
        </form>
        <p style="margin-top:10px;color:#ffaa00;">Expires on: {expiry_str}</p>
    </div>
    </body></html>
    """

# -------- Check permission (uses pastebin raw as source) --------
@app.route('/check-permission', methods=['POST'])
def check_permission():
    unique_key = request.form.get('unique_key', '')
    try:
        response = requests.get("https://pastebin.com/raw/dS4jJZDY", timeout=6)
        approved_tokens = [t.strip() for t in response.text.splitlines() if t.strip()]
    except Exception:
        approved_tokens = []

    if unique_key in approved_tokens:
        save_approved_key(unique_key)
        return redirect(url_for('approved', key=unique_key))
    else:
        return redirect(url_for('not_approved', key=unique_key))

# -------- Approved page (image + id box + Get Started) --------
@app.route('/approved')
def approved():
    key = request.args.get('key', '')
    return f"""
    <html><head><style>
    body {{background:black;color:white;text-align:center;font-family:'Segoe UI';}}
    img {{width:300px;height:auto;border-radius:12px;margin-top:20px;box-shadow:0 0 20px #00ff99;}}
    .id-box {{border:2px solid #00ff99;padding:10px;border-radius:10px;display:inline-block;margin:10px;color:#00ff99;font-weight:bold;word-break:break-word;}}
    .btn {{display:inline-block;margin-top:20px;background:#00ff99;color:black;padding:12px 25px;border-radius:10px;text-decoration:none;font-weight:bold;}}
    .btn:hover {{background:white;color:#00ff99;}}
    </style></head><body>
    <img src="{HEADER_IMAGE}" alt="Header Image">
    <h1 style="color:#00ff99;text-shadow:0 0 20px #00ff99;">APPROVED</h1>
    <div class="id-box">{key}</div><br>
    <a href="/panel" class="btn">Get Started</a>
    </body></html>
    """

# -------- Not approved page (image + WA link) --------
@app.route('/not-approved')
def not_approved():
    key = request.args.get('key', '')
    wa_text = f"Hello I want approval for HENRY-X. My ID is {key}"
    wa_link = "https://wa.me/919235741670?text=" + requests.utils.requote_uri(wa_text)
    return f"""
    <html><head><style>
    body {{background:black;color:white;text-align:center;font-family:'Segoe UI';}}
    img {{width:300px;height:auto;border-radius:12px;margin-top:20px;box-shadow:0 0 20px #ff0033;}}
    .wa-btn {{display:inline-block;margin-top:20px;background:#25D366;color:white;padding:12px 25px;border-radius:10px;text-decoration:none;font-size:18px;font-weight:bold;box-shadow:0 0 20px #25D366;transition:0.3s;}}
    .wa-btn:hover {{background:white;color:#25D366;}}
    </style></head><body>
    <img src="{HEADER_IMAGE}" alt="Header Image">
    <h1 style="color:#ff0033;text-shadow:0 0 20px #ff0033;">ACCESS DENIED</h1>
    <p>Your ID:</p>
    <p style="color:#ff0033;font-size:22px;">{key}</p>
    <a href="{wa_link}" class="wa-btn">📱 Request Approval on WhatsApp</a>
    </body></html>
    """

# -------- Final panel (exact HTML you provided) --------
HTML_PANEL = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HENRY-X Panel</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Sans+Italic&display=swap');

    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      background: radial-gradient(circle, #050505, #000);
      display: flex;
      flex-direction: column;
      align-items: center;
      min-height: 100vh;
      padding: 2rem;
      color: #fff;
    }

    /* ✅ Normal Header (Simple Font) */
    header {
      text-align: center;
      margin-bottom: 2rem;
    }

    header h1 {
      font-size: 2.5rem;
      font-weight: bold;
      letter-spacing: 2px;
      font-family: sans-serif; /* ✅ Normal font applied */
      color: white;
    }

    .container {
      display: flex;
      flex-wrap: wrap;
      gap: 2rem;
      justify-content: center;
      width: 100%;
    }

    /* Card Styling */
    .card {
      position: relative;
      width: 360px;
      height: 460px;
      border-radius: 18px;
      overflow: hidden;
      background: #111;
      cursor: pointer;
      box-shadow: 0 0 25px rgba(255,0,0,0.2);
      transition: transform 0.3s ease;
    }

    .card:hover {
      transform: scale(1.03);
    }

    .card video {
      width: 100%;
      height: 100%;
      object-fit: cover;
      filter: brightness(0.85);
    }

    /* Overlay Styling */
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

    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    /* ✅ Footer Styling */
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

  <header>
    <h1>HENRY-X</h1>
  </header>

  <div class="container">
    <!-- Your existing cards here -->
    <div class="card" onclick="toggleOverlay(this)">
      <video autoplay muted loop playsinline>
        <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/223.mp4" type="video/mp4">
      </video>
      <div class="overlay">
        <h3>Convo 3.0</h3>
        <p>𝘕𝘰𝘯𝘦 𝘚𝘵𝘰𝘱𝘦 𝘊𝘰𝘯𝘷𝘰 𝘉𝘺 𝘏𝘦𝘯𝘳𝘺 | 𝘔𝘶𝘭𝘵𝘺 + 𝘚𝘪𝘯𝘨𝘭𝘦 𝘉𝘰𝘵𝘩 𝘈𝘷𝘢𝘪𝘭𝘣𝘭𝘦 𝘐𝘯 𝘛𝘩𝘢𝘯𝘬𝘴 𝘍𝘰𝘳 𝘜𝘴𝘪𝘯𝘨..</p>
        <button class="open-btn" onclick="event.stopPropagation(); window.open('https://ambitious-haleigh-zohan-6ed14c8a.koyeb.app/','_blank')">
          OPEN
        </button>
      </div>
    </div>

    <!-- Card 2 -->
<div class="card" onclick="toggleOverlay(this)">
  <video autoplay muted loop playsinline>
    <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/Anime.mp4" type="video/mp4">
  </video>
  <div class="overlay">
    <h3>Post 3.0</h3>
    <p>𝘔𝘶𝘭𝘵𝘺 𝘊𝘰𝘰𝘬𝘪𝘦 + 𝘔𝘶𝘭𝘵𝘺 𝘛𝘰𝘬𝘦𝘯 | 𝘛𝘩𝘳𝘦𝘢𝘥 𝘚𝘵𝘰𝘱𝘦 𝘈𝘯𝘥 𝘙𝘦𝘴𝘶𝘮𝘦 𝘈𝘯𝘥 𝘗𝘢𝘶𝘴𝘦 𝘈𝘷𝘢𝘪𝘢𝘭𝘣𝘭𝘦 𝘌𝘯𝘫𝘰𝘺 𝘕𝘰𝘸.. </p>
    <button class="open-btn" onclick="event.stopPropagation(); window.open('https://web-post-server.onrender.com/','_blank')">
      OPEN
    </button>
  </div>
</div>

<!-- Card 3 -->
<div class="card" onclick="toggleOverlay(this)">
  <video autoplay muted loop playsinline>
    <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/GOKU%20_%20DRAGON%20BALZZ%20_%20anime%20dragonballz%20dragonballsuper%20goku%20animeedit%20animetiktok.mp4" type="video/mp4">
  </video>
  <div class="overlay">
    <h3>Token Checker 3.0</h3>
    <p>𝘛𝘰𝘬𝘦𝘯 𝘊𝘩𝘦𝘤𝘬𝘦𝘳 | 𝘎𝘤 𝘜𝘪𝘥 𝘌𝘹𝘵𝘳𝘢𝘤𝘵𝘰𝘳 𝘉𝘰𝘵𝘩 𝘐𝘯 𝘖𝘯𝘦 𝘛𝘰𝘰𝘭 𝘏𝘦𝘳𝘦..</p>
    <button class="open-btn" onclick="event.stopPropagation(); window.open('https://token-beta-indol.vercel.app/','_blank')">
      OPEN
    </button>
  </div>
</div>

<!-- Card 4 -->
<div class="card" onclick="toggleOverlay(this)">
  <video autoplay muted loop playsinline>
    <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/SOLO%20LEVELING.mp4" type="video/mp4">
  </video>
  <div class="overlay">
    <h3>Post Uid 2.0</h3>
    <p>𝘌𝘯𝘵𝘦𝘳 𝘠𝘰𝘶 𝘗𝘰𝘴𝘵 𝘓𝘪𝘯𝘬 𝘈𝘯𝘥 𝘌𝘹𝘵𝘳𝘢𝘤𝘵 𝘛𝘰 𝘗𝘰𝘴𝘵 𝘜𝘪𝘥 𝘌𝘢𝘴𝘪𝘭𝘺..</p>
    <button class="open-btn" onclick="event.stopPropagation(); window.open('https://post-uid-finder.vercel.app/','_blank')">
      OPEN
    </button>
  </div>
</div>
    <!-- Add remaining cards same as before -->
  </div>

  

  <!-- ✅ Footer Added -->
  <footer>
    Created by:HENRY-X
  </footer>

  <script>
    function toggleOverlay(card) {
      card.classList.toggle('active');
    }
  </script>

</body>
</html>
"""

@app.route('/panel')
def panel():
    return render_template_string(HTML_PANEL)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

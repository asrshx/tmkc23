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

# -------- Splash --------
@app.route('/')
def splash():
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Loading...</title>
<style>
body {margin:0;padding:0;background:black;display:flex;flex-direction:column;justify-content:center;align-items:center;height:100vh;overflow:hidden;color:white;font-family:'Segoe UI',sans-serif;}
img.splash-image {width:100%;height:100%;object-fit:cover;position:absolute;top:0;left:0;animation:fadeIn 1.5s ease-in-out;z-index:0;}
.loader {border:6px solid rgba(255,255,255,0.2);border-top:6px solid #ff00ff;border-radius:50%;width:60px;height:60px;animation:spin 1s linear infinite;z-index:1;position:relative;margin-top:20px;}
.loading-text {margin-top:15px;font-size:22px;font-weight:bold;color:#ff00ff;text-shadow:0 0 10px #ff00ff;animation:blink 1.2s infinite alternate;z-index:1;position:relative;}
@keyframes spin {0%{transform:rotate(0deg);}100%{transform:rotate(360deg);}}
@keyframes fadeIn {from{opacity:0;}to{opacity:1;}}
@keyframes blink {0%{opacity:1;}100%{opacity:0.4;}}
</style>
<script>setTimeout(()=>{window.location.href="/approval";},3000);</script>
</head>
<body>
<img class="splash-image" src="https://i.imgur.com/B2iRAOX.jpeg" alt="Splash">
<div class="loader"></div>
<div class="loading-text">Please Wait...</div>
</body>
</html>
""")

# -------- Approval request page --------
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
img {{width:380px;height:auto;border-radius:12px;margin-top:20px;box-shadow:0 0 25px #ff00ff;}}
.key-card {{background:rgba(255,255,255,0.05);border:2px solid #ff00ff;border-radius:20px;max-width:600px;margin:20px auto;padding:20px;box-shadow:0 0 30px #ff00ff;}}
.key-text {{font-size:25px;color:#ff00ff;font-weight:bold;word-break:break-word;}}
.copy-btn {{background:#ff00ff;color:white;border:none;border-radius:8px;padding:8px 12px;cursor:pointer;margin-left:8px;}}
</style></head><body>
<img src="{HEADER_IMAGE}" alt="Header Image">
<h1>HENRY-X Approval</h1>
<div class="key-card">
<p> Device: {device_name} - {device_model}</p>
<p><b>HENRY-X Approval ID</b></p>
<p class="key-text">{unique_key}</p>
<form action="/check-permission" method="post" style="margin-top:12px;">
<input type="hidden" name="unique_key" value="{unique_key}">
<input type="submit" value="Check Approval" style="background:#ff00ff;color:white;border:none;border-radius:8px;padding:10px 25px;cursor:pointer;">
</form>
<p style="margin-top:10px;color:#ffaa00;">Expires on: {expiry_str}</p>
</div>
</body></html>
"""

# -------- Check permission --------
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

# -------- Approved page --------
@app.route('/approved')
def approved():
    key = request.args.get('key', '')
    return f"""
<html><head><style>
body {{background:black;color:white;text-align:center;font-family:'Segoe UI';}}
img {{width:380px;height:auto;border-radius:12px;margin-top:20px;box-shadow:0 0 25px #00ff99;}}
.id-box {{border:2px solid #00ff99;padding:10px;border-radius:10px;display:inline-block;margin:10px;color:#00ff99;font-weight:bold;word-break:break-word;}}
.btn {{display:inline-block;margin-top:20px;background:#00ff99;color:black;padding:12px 25px;border-radius:10px;text-decoration:none;font-weight:bold;}}
.btn:hover {{background:white;color:#00ff99;}}
</style></head><body>
<img src="{HEADER_IMAGE}" alt="Header Image">
<h1 style="color:#00ff99;text-shadow:0 0 20px #00ff99;">APPROVED</h1>
<div class="id-box">{key}</div><br>
</body></html>
"""

# -------- Not approved page --------
@app.route('/not-approved')
def not_approved():
    key = request.args.get('key', '')
    wa_text = f"Hello I want approval for HENRY-X. My ID is {key}"
    wa_link = "https://wa.me/919235741670?text=" + requests.utils.requote_uri(wa_text)
    return f"""
<html><head><style>
body {{background:black;color:white;text-align:center;font-family:'Segoe UI';}}
img {{width:380px;height:auto;border-radius:12px;margin-top:20px;box-shadow:0 0 25px #ff0033;}}
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

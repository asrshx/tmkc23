from flask import Flask, render_template_string, redirect, url_for, request
import requests
from datetime import datetime
try:
    # zoneinfo is available in Python 3.9+
    from zoneinfo import ZoneInfo
except:
    ZoneInfo = None
import urllib.parse

app = Flask(__name__)

# ------------ CONFIGURE THESE ------------
# WhatsApp number must be in international format WITHOUT plus sign or spaces.
# Example: India +91 98765 43210 -> "919876543210"
WHATSAPP_NUMBER = "919999999999"   # <-- change to your number

# Facebook link - full URL to your profile or page
FACEBOOK_LINK = "https://www.facebook.com/yourprofile"  # <-- change to your FB link
# ----------------------------------------

PANEL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Henry-X Panel</title>
  <style>
    :root{
      --bg1: #0e0f14;
      --bg2: #121224;
      --card: rgba(255,255,255,0.04);
      --accent-start: #ff00ff;
      --accent-end: #00ffff;
      --glass: rgba(255,255,255,0.03);
      --muted: rgba(255,255,255,0.6);
    }
    *{box-sizing: border-box}
    body{
      margin:0;
      min-height:100vh;
      background: linear-gradient(135deg,var(--bg1), #1b1b2f 60%);
      font-family: Inter, "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
      color: #fff;
      display:flex;
      align-items:flex-start;
      justify-content:center;
      padding:36px 16px;
    }
    .container{
      width:100%;
      max-width:980px;
    }

    header h1{
      margin:0 0 14px 0;
      font-size:34px;
      letter-spacing:4px;
      text-transform:uppercase;
      text-align:center;
      color: white;
      animation: glow 2s infinite alternate;
    }
    @keyframes glow{
      from { text-shadow: 0 0 8px var(--accent-start); }
      to   { text-shadow: 0 0 16px var(--accent-end); }
    }

    /* layout */
    .top-row{
      display:flex;
      gap:20px;
      align-items:flex-start;
      justify-content:center;
      flex-wrap:wrap;
    }

    .image-card, .desc-card{
      background: var(--card);
      border-radius:14px;
      padding:18px;
      box-shadow: 0 6px 18px rgba(0,0,0,0.6);
      backdrop-filter: blur(6px);
    }

    .image-card{
      width:320px;
      display:flex;
      align-items:center;
      justify-content:center;
    }
    .image-card img{
      width:100%;
      height:auto;
      border-radius:10px;
      display:block;
      box-shadow: 0 8px 30px rgba(0,0,0,0.6);
    }

    .desc-card{
      max-width:560px;
      flex:1;
    }
    .desc-card h2{
      margin:0 0 8px 0;
      font-size:20px;
    }
    .desc-card p{
      margin:0;
      color:var(--muted);
      line-height:1.5;
    }

    /* the three boxes/cards */
# inside PANEL_HTML (CSS me changes)
<style>
  ...
  .cards-row{
    margin-top:30px;
    display:flex;
    gap:20px;
    flex-wrap:wrap;
    justify-content:center;
  }
  .action-card{
    background: var(--glass);
    border-radius:16px;
    padding:24px 22px;
    min-width:280px;   /* pehle 220 tha */
    max-width:360px;   /* pehle 320 tha */
    text-align:center;
    box-shadow: 0 8px 22px rgba(0,0,0,0.55);
    transition: transform .2s ease, box-shadow .2s ease;
    cursor:pointer;
    color: #fff;
    text-decoration:none;
  }
  .action-card:hover{
    transform: translateY(-8px);
    box-shadow: 0 20px 44px rgba(0,0,0,0.65);
  }
  .action-card h3{
    margin:0 0 10px 0;
    font-size:18px;   /* thoda bada */
    letter-spacing:1px;
  }
  .action-card p{
    margin:0;
    color:var(--muted);
    font-size:15px;   /* thoda bada */
    line-height:1.5;
  }
</style>
</head>
<body>
  <div class="container">
    <header>
      <h1>HENRY-X</h1>
    </header>

    <section class="top-row">
      <div class="image-card">
        <img src="https://i.imgur.com/QkquU4b.jpeg" alt="Henry AI">
      </div>

      <div class="desc-card">
        <h2>About HENRY-X</h2>
        <p>
          Hyy Users — I'm a helping tool made by Darkstar Rulex (Henry).
          Use the cards below to contact me or view profile links. This panel is lightweight and focused on direct contact.
        </p>
      </div>
    </section>

    <section class="cards-row">
      <!-- WhatsApp card (opens wa link with prefilled message) -->
      <a class="action-card" href="{{ wa_link }}" target="_blank" rel="noopener noreferrer">
        <h3>WhatsApp</h3>
        <p>Click to open WhatsApp chat with the owner. Pre-filled message will be inserted.</p>
      </a>

      <!-- Facebook card -->
      <a class="action-card" href="{{ fb_link }}" target="_blank" rel="noopener noreferrer">
        <h3>Facebook</h3>
        <p>Open the owner's Facebook profile / page.</p>
      </a>

      <!-- Real-time card -->
      <div class="action-card" title="Local time based on your IP">
        <h3>Local Time & Day</h3>
        <p style="font-weight:600; margin-top:6px; margin-bottom:2px;">{{ local_time }}</p>
        <p style="margin-top:6px; color: var(--muted);">{{ local_day }} — {{ detected_location }}</p>
      </div>
    </section>

    <div class="small-muted">
      Note: Local time is detected using your public IP address via ipinfo.io. If detection fails, server time is shown.
    </div>

    <footer>
      this web is made by HENRY...
    </footer>
  </div>
</body>
</html>
"""

@app.route("/")
def home():
    # visitor IP
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    # default values
    tz_name = None
    detected_location = "Unknown location"
    local_time_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S (UTC)")
    local_day = datetime.utcnow().strftime("%A")

    try:
        # Query ipinfo
        response = requests.get(f"https://ipinfo.io/{user_ip}/json", timeout=4)
        data = response.json()
        tz_name = data.get("timezone")
        city = data.get("city")
        region = data.get("region")
        country = data.get("country")
        if city or region or country:
            detected_location = ", ".join(part for part in [city, region, country] if part)
        # compute local time using tz_name if available
        if tz_name and ZoneInfo is not None:
            try:
                now_local = datetime.now(ZoneInfo(tz_name))
                local_time_str = now_local.strftime("%Y-%m-%d %H:%M:%S")
                local_day = now_local.strftime("%A")
            except Exception:
                # fallback to UTC/time returned earlier
                pass
        else:
            if tz_name and ZoneInfo is not None:
    try:
        now_local = datetime.now(ZoneInfo(tz_name))
        local_time_str = now_local.strftime("%d-%m-%Y %I:%M %p")   # dd-mm-yyyy hour:min am/pm
        local_day = now_local.strftime("%A")
    except Exception:
        pass

    # prepare contact links
    # WhatsApp prefilled message
    message = "hello henry sir please help me"
    wa_number = WHATSAPP_NUMBER.strip()
    # ensure number contains only digits (and leading + removed)
    wa_number = "".join(ch for ch in wa_number if ch.isdigit())
    if wa_number:
        wa_link = f"https://wa.me/{wa_number}?text=" + urllib.parse.quote_plus(message)
    else:
        # if number not set, point to WhatsApp homepage
        wa_link = "https://www.whatsapp.com/"

    fb_link = FACEBOOK_LINK

    return render_template_string(
        PANEL_HTML,
        wa_link=wa_link,
        fb_link=fb_link,
        local_time=local_time_str,
        local_day=local_day,
        detected_location=detected_location,
    )

@app.route("/visit")
def visit():
    return redirect("https://www.google.com")  # kept for compatibility if used elsewhere

if __name__ == "__main__":
    app.run(debug=True)

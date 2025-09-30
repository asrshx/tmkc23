from flask import Flask, render_template_string, redirect, url_for, request
import requests

app = Flask(__name__)

PANEL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Henry-X Panel</title>
  <style>
    body {
      margin: 0;
      height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: flex-start;
      background: linear-gradient(135deg, #1f1f1f, #2c2c54);
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      color: white;
      overflow-x: hidden;
    }

    h1 {
      font-size: 3rem;
      margin-top: 30px;
      text-transform: uppercase;
      letter-spacing: 4px;
      text-align: center;
      animation: glow 2s infinite alternate;
    }

    @keyframes glow {
      from { text-shadow: 0 0 10px #ff00ff, 0 0 20px #ff00ff; }
      to   { text-shadow: 0 0 20px #00ffff, 0 0 40px #00ffff; }
    }

    .image-container {
      margin-top: 20px;
      display: flex;
      justify-content: center;
    }

    .image-container img {
      width: 300px;
      height: auto;
      border-radius: 20px;
      box-shadow: 0 0 20px rgba(0,0,0,0.7);
    }

    .card {
      margin-top: 20px;
      background: rgba(255, 255, 255, 0.1);
      padding: 15px 20px;
      border-radius: 15px;
      box-shadow: 0 0 15px rgba(0,0,0,0.4);
      backdrop-filter: blur(10px);
      max-width: 350px;
      text-align: center;
      font-size: 0.9rem;
      line-height: 1.4rem;
      animation: fadeIn 2s ease-in-out;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .animated-text {
      font-size: 50px;
      font-weight: bold;
      margin-top: 20px;
      text-align: center;
      animation: typing 3s steps(30, end) infinite alternate;
      white-space: nowrap;
      overflow: hidden;
      border-right: 3px solid #fff;
    }

    @keyframes typing {
      from { width: 0; }
      to { width: 100%; }
    }

    .visit-btn {
      margin-top: 30px;
      padding: 15px 40px;
      font-size: 1.2rem;
      font-weight: bold;
      color: #fff;
      background: linear-gradient(45deg, #ff00ff, #00ffff);
      border: none;
      border-radius: 50px;
      cursor: pointer;
      box-shadow: 0px 0px 20px rgba(0, 255, 255, 0.6);
      transition: 0.3s ease-in-out;
    }

    .visit-btn:hover {
      transform: scale(1.1);
      box-shadow: 0px 0px 30px rgba(255, 0, 255, 0.8);
    }

    /* New Buttons Row */
    .button-row {
      display: flex;
      justify-content: space-between;
      width: 320px;
      margin-top: 20px;
    }

    .about-btn, .apk-btn {
      padding: 12px 30px;
      font-size: 1rem;
      font-weight: bold;
      color: #fff;
      border: none;
      border-radius: 40px;
      cursor: pointer;
      transition: transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out;
    }

    .about-btn {
      background: linear-gradient(45deg, #ff7b00, #ff00aa);
      box-shadow: 0px 0px 15px rgba(255, 123, 0, 0.6);
    }

    .apk-btn {
      background: linear-gradient(45deg, #00ff7f, #00bfff);
      box-shadow: 0px 0px 15px rgba(0, 255, 127, 0.6);
    }

    .about-btn:hover, .apk-btn:hover {
      transform: scale(1.08);
      box-shadow: 0px 0px 25px rgba(255, 255, 255, 0.8);
    }

    .info-card {
      margin-top: 20px;
      background: rgba(255, 255, 255, 0.08);
      padding: 12px;
      border-radius: 12px;
      font-size: 0.85rem;
      line-height: 1.4rem;
      text-align: center;
      max-width: 350px;
      box-shadow: 0 0 12px rgba(0,0,0,0.3);
    }

  </style>
</head>
<body>

  <h1>HENRY-X</h1>

  <div class="image-container">
    <img src="https://i.imgur.com/QkquU4b.jpeg" alt="Henry AI">
  </div>

  <div class="card">
    Hyy Users I'm A Helping Tool Made By Darkstar Rulex Boy Henry I Hope You Are Enjoying With My Tools And All Premiums Tools Made By HENRY..
  </div>

  <div class="animated-text">Hyy Users I'm Henry AI</div>

  <form action="{{ url_for('visit') }}">
    <button class="visit-btn">VISIT</button>
  </form>

  <div class="button-row">
    <button class="about-btn">ABOUT</button>
    <button class="apk-btn">APK</button>
  </div>

  <div class="info-card">
    <b>Your IP:</b> {{ ip }}<br>
    <b>ISP:</b> {{ org }}<br>
    <b>Country:</b> {{ country }}
  </div>

</body>
</html>
"""

@app.route("/")
def home():
    # User ka IP nikalna
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    try:
        response = requests.get(f"https://ipinfo.io/{user_ip}/json")
        data = response.json()
        country = data.get("country", "Unknown")
        org = data.get("org", "Unknown ISP")
    except:
        country = "Unknown"
        org = "Unknown ISP"

    return render_template_string(PANEL_HTML, ip=user_ip, org=org, country=country)

@app.route("/visit")
def visit():
    return redirect("https://www.google.com")  # Example redirect

if __name__ == "__main__":
    app.run(debug=True)

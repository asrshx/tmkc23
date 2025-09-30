from flask import Flask, render_template_string
import datetime

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
      padding: 0;
      background: #f5f6fa;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
    }

    /* Typing Animation */
    .typing {
      margin: 30px 0 10px;
      font-size: 35px;
      font-weight: bold;
      color: #2c3e50;
      border-right: 3px solid #2c3e50;
      white-space: nowrap;
      overflow: hidden;
      width: 0;
      animation: typing 4s steps(20, end) forwards, blink 0.8s infinite;
    }

    @keyframes typing {
      from { width: 0; }
      to { width: 350px; }
    }
    @keyframes blink {
      50% { border-color: transparent; }
    }

    /* Time Weather Card */
    .info-card {
      background: #fff;
      border-radius: 20px;
      box-shadow: 0 8px 20px rgba(0,0,0,0.1);
      width: 500px;
      padding: 20px;
      margin-bottom: 30px;
      text-align: center;
      animation: fadeIn 1.5s ease-in-out;
    }

    .info-card h2 {
      margin: 10px 0;
      color: #3498db;
    }
    .info-card p {
      margin: 5px 0;
      color: #555;
      font-size: 1rem;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(15px); }
      to { opacity: 1; transform: translateY(0); }
    }

    /* Cards */
    .container {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
      width: 90%;
      max-width: 1100px;
      margin-bottom: 50px;
    }

    .card {
      background: #fff;
      border-radius: 20px;
      box-shadow: 0 8px 20px rgba(0,0,0,0.1);
      overflow: hidden;
      transition: transform 0.3s ease, box-shadow 0.3s ease;
      text-align: center;
      padding-bottom: 20px;
      height: 700px;
    }

    .card:hover {
      transform: translateY(-8px);
      box-shadow: 0 12px 30px rgba(0,0,0,0.2);
    }

    .card img {
      width: 100%;
      height: 600px;
      object-fit: cover;
      border-radius: 20px 20px 0 0;
    }

    .card h2 {
      font-size: 1.3rem;
      margin: 15px 0 10px;
      color: #2c3e50;
    }

    .card p {
      font-size: 0.95rem;
      color: #555;
      padding: 0 15px;
      line-height: 1.4rem;
    }

    .icon {
      font-size: 24px;
      margin-top: 10px;
      color: #3498db;
    }

    footer {
      text-align: center;
      padding: 15px;
      font-size: 0.85rem;
      color: #888;
    }
  </style>
</head>
<body>

  <!-- Typing Text -->
  <div class="typing">Hii I'm Henry Tools</div>

  <!-- Info Card (Time/Date/Weather) -->
  <div class="info-card">
    <h2>📅 {{date}}</h2>
    <p>⏰ {{time}}</p>
    <p>☁️ Weather: {{weather}}</p>
  </div>

  <!-- Cards -->
  <div class="container">

    <div class="card">
      <img src="https://i.imgur.com/yyObmiN.jpeg" alt="Henry AI">
      <h2>⚡ Convox</h2>
      <p>Just Paste Your Multiple Tokens & Start your Conversion Thread Supported Multiple Tokens & Automation.</p>
      <div class="icon">📶</div>
    </div>

    <div class="card">
      <img src="https://i.imgur.com/XOeNq1J.jpeg" alt="Service 2">
      <h2>🔥 Auto-X</h2>
      <p>Automated premium tools with multi-token support for your advanced automation needs.</p>
      <div class="icon">💻</div>
    </div>

    <div class="card">
      <img src="https://i.imgur.com/zI2LrBi.jpeg" alt="Service 3">
      <h2>🔮 Magic Tools</h2>
      <p>Next-level utilities with AI-powered features. Smooth, secure & super fast.</p>
      <div class="icon">✨</div>
    </div>

  </div>

  <footer>All rights reserved by Henry Don</footer>

</body>
</html>
"""

@app.route("/")
def home():
    now = datetime.datetime.now()
    date = now.strftime("%A, %d %B %Y")
    time = now.strftime("%I:%M %p")
    # Weather yaha static rakha hai, API se bhi laa sakte ho
    weather = "Sunny 28°C"
    return render_template_string(PANEL_HTML, date=date, time=time, weather=weather)

if __name__ == "__main__":
    app.run(debug=True)

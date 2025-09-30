from flask import Flask, render_template_string

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
      justify-content: space-between;
      background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      color: white;
    }

    h1 {
      font-size: 3.5rem;
      margin-top: 30px;
      letter-spacing: 4px;
      text-transform: uppercase;
      text-align: center;
      animation: glow 2s infinite alternate;
    }

    @keyframes glow {
      from { text-shadow: 0 0 15px #ff00ff, 0 0 30px #ff00ff; }
      to   { text-shadow: 0 0 30px #00ffff, 0 0 60px #00ffff; }
    }

    .card {
      margin-top: 20px;
      background: rgba(255, 255, 255, 0.08);
      padding: 30px;
      border-radius: 25px;
      width: 700px;
      text-align: center;
      box-shadow: 0px 0px 35px rgba(0,0,0,0.7);
      backdrop-filter: blur(12px);
      animation: fadeIn 1.5s ease-in-out;
    }

    .card img {
      width: 600px;
      border-radius: 20px;
      margin-bottom: 20px;
      box-shadow: 0 0 25px rgba(0,0,0,0.6), 0 0 40px rgba(0,255,255,0.3);
    }

    .bio-text {
      margin-top: 10px;
      font-size: 1rem;
      color: #eaeaea;
      line-height: 1.5rem;
      text-shadow: 0 0 5px rgba(0,0,0,0.4);
    }

    footer {
      margin-bottom: 15px;
      font-size: 0.8rem;
      color: #ccc;
      text-align: center;
      letter-spacing: 1px;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(20px); }
      to { opacity: 1; transform: translateY(0); }
    }
  </style>
</head>
<body>

  <h1>HENRY-X</h1>

  <div class="card">
    <img src="https://i.imgur.com/yyObmiN.jpeg" alt="Henry AI">
    <div class="bio-text">
      🚀 This tool is crafted by <b>Henry</b>. A simple yet powerful AI assistant<br>
      built to deliver premium features with style.<br>
      Stay tuned and enjoy the journey with Henry's tools ✨
    </div>
  </div>

  <footer>
    © All rights reserved by Henry Don
  </footer>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(PANEL_HTML)

if __name__ == "__main__":
    app.run(debug=True)

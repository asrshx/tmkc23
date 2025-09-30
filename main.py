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
      justify-content: flex-start;
      background: linear-gradient(135deg, #141e30, #243b55);
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      color: white;
    }

    h1 {
      font-size: 3rem;
      margin-top: 20px;
      letter-spacing: 3px;
      text-transform: uppercase;
      text-align: center;
      animation: glow 2s infinite alternate;
    }

    @keyframes glow {
      from { text-shadow: 0 0 15px #ff00ff, 0 0 30px #ff00ff; }
      to   { text-shadow: 0 0 30px #00ffff, 0 0 60px #00ffff; }
    }

    .card {
      margin-top: 30px;
      background: rgba(255, 255, 255, 0.08);
      padding: 20px;
      border-radius: 20px;
      width: 500px;
      text-align: center;
      box-shadow: 0px 0px 25px rgba(0,0,0,0.6);
      backdrop-filter: blur(10px);
      animation: fadeIn 1.5s ease-in-out;
    }

    .card img {
      width: 400px;
      border-radius: 15px;
      box-shadow: 0 0 20px rgba(0,0,0,0.5);
    }

    .bio-text {
      margin-top: 15px;
      font-size: 0.95rem;
      color: #ddd;
      line-height: 1.4rem;
    }

    footer {
      margin-top: 30px;
      font-size: 0.75rem;
      color: #aaa;
      text-align: center;
    }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(15px); }
      to { opacity: 1; transform: translateY(0); }
    }
  </style>
</head>
<body>

  <h1>HENRY-X</h1>

  <div class="card">
    <img src="https://i.imgur.com/yyObmiN.jpeg" alt="Henry AI">
    <div class="bio-text">
      This tool is made by Henry. A simple yet powerful AI helper for all your premium needs.<br>
      Stay tuned for more updates and enjoy using Henry's tools.
    </div>
  </div>

  <footer>
    All rights reserved by Henry Don
  </footer>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(PANEL_HTML)

if __name__ == "__main__":
    app.run(debug=True)

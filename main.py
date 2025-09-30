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
      padding: 0;
      background: #f5f6fa;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
    }

    h1 {
      margin: 25px 0;
      font-size: 2.2rem;
      text-align: center;
      color: #2c3e50;
      font-weight: bold;
    }

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
      height: 800
    }

    .card:hover {
      transform: translateY(-8px);
      box-shadow: 0 12px 30px rgba(0,0,0,0.2);
    }

    .card img {
      width: 100%;
      height: 250px;
      object-fit: cover;
      border-bottom: 1px solid #eee;
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

  <h1>Henry-X Panel</h1>

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
    return render_template_string(PANEL_HTML)

if __name__ == "__main__":
    app.run(debug=True)

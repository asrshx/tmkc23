from flask import Flask, render_template_string, redirect, url_for

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
  </style>
</head>
<body>

  <h1>HENRY-X</h1>

  <div class="image-container">
    <img src="https://via.placeholder.com/300x300.png?text=Henry+AI" alt="Henry AI">
  </div>

  <div class="animated-text">Hyy Users I'm Henry AI</div>

  <form action="{{ url_for('visit') }}">
    <button class="visit-btn">VISIT</button>
  </form>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(PANEL_HTML)

@app.route("/visit")
def visit():
    # Yaha aap redirect kar sakte ho kisi dusre page ya external link par
    return redirect("https://www.google.com")  # example link

if __name__ == "__main__":
    app.run(debug=True)

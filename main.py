from flask import Flask, render_template_string, redirect, url_for

app = Flask(__name__)

PANEL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>IMMU PANEL</title>
<style>
  body {
    margin: 0;
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    font-family: 'Poppins', sans-serif;
    background: linear-gradient(to bottom right, #ff0000, #800080);
  }
  .card {
    width: 90%;
    max-width: 1100px;
    height: 800px;
    background: rgba(0,0,0,0.6);
    border-radius: 25px;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    align-items: center;
    padding: 20px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.7);
    text-align: center;
    color: white;
    overflow: hidden;
  }
  .card img {
    width: 100%;
    height: 650px;
    object-fit: cover;
    border-radius: 20px;
    margin-bottom: 30px;
  }
  .card h1 {
    font-size: 2.5rem;
    margin-bottom: 40px;
  }
  .btn {
    width: 200px;
    padding: 15px;
    margin: 15px;
    font-size: 1.2rem;
    font-weight: bold;
    border: none;
    border-radius: 15px;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
  }
  .btn-start {
    background: linear-gradient(90deg, #ff0000, #ff7f50);
    color: #fff;
  }
  .btn-logs {
    background: linear-gradient(90deg, #800080, #da70d6);
    color: #fff;
  }
  .btn:hover {
    transform: scale(1.05);
    box-shadow: 0 5px 15px rgba(0,0,0,0.5);
  }
</style>
</head>
<body>
  <div class="card">
    <img src="https://i.imgur.com/9IEiv1n.jpeg" alt="Panel Image">
    <h1>🔥 IMMU PANEL 🔥</h1>
    <button class="btn btn-start" onclick="window.location.href='/start'">START</button>
    <button class="btn btn-logs" onclick="window.location.href='/logs'">CHECK LOGS</button>
  </div>
</body>
</html>
"""

@app.route("/")
def panel():
    return render_template_string(PANEL_HTML)

# Dummy routes for buttons
@app.route("/start")
def start():
    return "<h1>Start Button Clicked!</h1>"

@app.route("/logs")
def logs():
    return "<h1>Logs Button Clicked!</h1>"

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

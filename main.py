from flask import Flask, render_template_string

app = Flask(__name__)

# ================== HTML ==================
HOME_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HENRY-X | Home</title>
<style>
:root{
  --max-w:700px;
  --card-h:1000px;
}
body{
  margin:0;
  min-height:100vh;
  display:flex;
  align-items:center;
  justify-content:center;
  font-family:Poppins, sans-serif;
  background:linear-gradient(to bottom left, #ff0000, #800080);
}
.card{
  max-width:var(--max-w);
  height:var(--card-h);
  width:100%;
  background:rgba(0,0,0,0.6);
  border:3px solid black;
  border-radius:20px;
  box-shadow:0 10px 30px rgba(0,0,0,0.5);
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  padding:20px;
  color:white;
}
.card img{
  width:600px;
  max-width:100%;
  border-radius:15px;
  margin-bottom:20px;
}
h1{
  font-size:2rem;
  margin:0;
  margin-bottom:40px;
}
button{
  padding:14px 20px;
  border-radius:12px;
  border:none;
  font-size:1.2rem;
  font-weight:bold;
  background:linear-gradient(90deg,#ff0000,#800080);
  color:white;
  cursor:pointer;
  transition:0.3s;
  width:70%;
  margin:10px 0;
}
button:hover{
  transform:scale(1.05);
}
</style>
</head>
<body>
<div class="card">
  <img src="https://i.imgur.com/9IEiv1n.jpeg" alt="HENRY-X">
  <h1>HENRY-X</h1>
  <button onclick="alert('CONVO\\'X clicked!')">CONVO'X</button>
  <button onclick="alert('THREAD\\'X clicked!')">THREAD'X</button>
</div>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HOME_HTML)

if __name__ == "__main__":
    app.run(debug=True)

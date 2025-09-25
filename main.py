from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

# Simple in-memory user store (sirf test ke liye)
users = {}  # {username: password}

# ================== HTML TEMPLATES ==================
AUTH_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }} | HENRY-X</title>
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
  margin-bottom:20px;
}
form{
  display:flex;
  flex-direction:column;
  gap:15px;
  width:80%;
}
input{
  padding:12px 15px;
  border-radius:12px;
  border:none;
  font-size:1rem;
  outline:none;
}
button{
  padding:12px 15px;
  border-radius:12px;
  border:none;
  font-size:1rem;
  font-weight:bold;
  background:linear-gradient(90deg,#ff0000,#800080);
  color:white;
  cursor:pointer;
  transition:0.3s;
}
button:hover{
  transform:scale(1.05);
}
a{
  color:#00ffea;
  font-weight:bold;
  text-decoration:none;
}
.message{
  margin-top:10px;
  font-weight:bold;
  font-size:1rem;
}
.success{color:#00ff9d}
.error{color:#ff4d4d}
</style>
</head>
<body>
<div class="card">
  <img src="https://picsum.photos/600/300" alt="HENRY-X Banner">
  <h1>HENRY-X</h1>
  <form method="POST">
    <input type="text" name="username" placeholder="Enter Username" required>
    <input type="password" name="password" placeholder="Enter Password" required>
    {% if signup %}
    <input type="password" name="confirm" placeholder="Confirm Password" required>
    {% endif %}
    <button type="submit">{{ button_text }}</button>
  </form>
  {% if signup %}
    <p>Already have an account? <a href="{{ url_for('login') }}">Login</a></p>
  {% else %}
    <p>Don't have an account? <a href="{{ url_for('signup') }}">Sign Up</a></p>
  {% endif %}
  {% if message %}
    <p class="message {{ status }}">{{ message }}</p>
  {% endif %}
</div>
</body>
</html>
"""

# ================== ROUTES ==================
@app.route("/", methods=["GET", "POST"])
def login():
    message = None
    status = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in users and users[username] == password:
            message = "✅ Login Successful!"
            status = "success"
        else:
            message = "❌ Invalid Username or Password!"
            status = "error"
    return render_template_string(AUTH_HTML, title="Login", button_text="Login",
                                  signup=False, message=message, status=status)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    message = None
    status = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm")
        if username in users:
            message = "⚠ Username already exists!"
            status = "error"
        elif password != confirm:
            message = "⚠ Passwords do not match!"
            status = "error"
        else:
            users[username] = password
            message = "✅ Signup Successful! Please login."
            status = "success"
    return render_template_string(AUTH_HTML, title="Sign Up", button_text="Sign Up",
                                  signup=True, message=message, status=status)

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template_string, request, redirect, url_for, session
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# ---- Simple Database (username: password) ----
users = {}

# ---- HTML Template ----
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HENRY-X PANEL</title>
    <style>
        body {
            background: linear-gradient(to bottom right, #ff0066, #ff66cc);
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            background: white;
            max-width: 350px;
            width: 100%;
            padding: 20px;
            border-radius: 20px;
            box-shadow: 0px 5px 15px rgba(0,0,0,0.3);
            text-align: center;
        }
        img {
            width: 100%;
            border-radius: 15px;
            margin-bottom: 10px;
        }
        h1 {
            background: linear-gradient(to right, #ff0066, #ff66cc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 15px;
        }
        input {
            width: 90%;
            padding: 10px;
            margin: 8px 0;
            border: 1px solid #ccc;
            border-radius: 10px;
            text-align: center;
        }
        button {
            width: 95%;
            background: linear-gradient(to right, #ff0066, #ff66cc);
            border: none;
            padding: 10px;
            color: white;
            font-weight: bold;
            border-radius: 15px;
            cursor: pointer;
            font-size: 16px;
            margin-top: 10px;
        }
        p.error {
            color: red;
            font-size: 14px;
        }
        a {
            display: inline-block;
            margin-top: 10px;
            text-decoration: none;
            color: #ff0066;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <img src="https://picsum.photos/400/300" alt="HENRY-X">
        <h1>HENRY-X</h1>
        {% if error %}<p class="error">{{ error }}</p>{% endif %}
        <form method="post">
            <input type="text" name="username" placeholder="Username" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <button type="submit">{{ 'Continue' if page=='login' else 'Create Account' }}</button>
        </form>
        {% if page=='login' %}
            <a href="{{ url_for('signup') }}">Don't have an account? Sign Up</a>
        {% else %}
            <a href="{{ url_for('login') }}">Already have account? Login</a>
        {% endif %}
    </div>
</body>
</html>
"""

WELCOME_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome HENRY-X</title>
    <style>
        body {
            background: linear-gradient(to right, #00c6ff, #0072ff);
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            color: white;
        }
        .welcome-box {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            backdrop-filter: blur(10px);
        }
        h1 {
            font-size: 30px;
        }
        a {
            color: white;
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="welcome-box">
        <h1>Welcome, {{ user }} 🎉</h1>
        <p>You are logged in to <b>HENRY-X Panel</b>.</p>
        <a href="{{ url_for('logout') }}">Logout</a>
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        uname = request.form["username"]
        pwd = request.form["password"]
        if uname in users and users[uname] == pwd:
            session["user"] = uname
            return redirect(url_for("welcome"))
        else:
            error = "Invalid username or password."
    return render_template_string(HTML_PAGE, error=error, page="login")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        uname = request.form["username"]
        pwd = request.form["password"]
        if uname in users:
            error = "Username already exists!"
        else:
            users[uname] = pwd
            session["user"] = uname
            return redirect(url_for("welcome"))
    return render_template_string(HTML_PAGE, error=error, page="signup")

@app.route("/welcome")
def welcome():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template_string(WELCOME_PAGE, user=session["user"])

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

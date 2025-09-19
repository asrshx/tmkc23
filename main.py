from flask import Flask, render_template_string, request, redirect, url_for, session
import secrets, requests, time, threading

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

users = {}

# ---------------- LOGIN & SIGNUP PAGE ----------------
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
    img {width: 100%; border-radius: 15px; margin-bottom: 10px;}
    h1 {
        background: linear-gradient(to right, #ff0066, #ff66cc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 28px; font-weight: bold; margin-bottom: 15px;
    }
    input {
        width: 90%; padding: 10px; margin: 8px 0;
        border: 1px solid #ccc; border-radius: 10px; text-align: center;
    }
    button {
        width: 95%; background: linear-gradient(to right, #ff0066, #ff66cc);
        border: none; padding: 10px; color: white; font-weight: bold;
        border-radius: 15px; cursor: pointer; font-size: 16px; margin-top: 10px;
    }
    a {display: inline-block; margin-top: 10px; text-decoration: none;
       color: #ff0066; font-weight: bold;}
    p.error {color: red; font-size: 14px;}
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

# ---------------- WELCOME PANEL ----------------
WELCOME_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Welcome</title>
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
    img {width: 100%; border-radius: 15px; margin-bottom: 10px;}
    h1 {
        background: linear-gradient(to right, #ff0066, #ff66cc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 26px; font-weight: bold; margin-bottom: 10px;
    }
    .btn {
        display: block; width: 90%; margin: 10px auto; padding: 12px;
        border-radius: 15px; border: none;
        background: linear-gradient(to right, #ff0066, #ff66cc);
        color: white; font-weight: bold; font-size: 16px;
        cursor: pointer; transition: transform 0.2s;
    }
    .btn:hover {transform: scale(1.05);}
    a.logout {display: block; margin-top: 15px; color: #ff0066;
              text-decoration: none; font-weight: bold;}
</style>
</head>
<body>
<div class="container">
    <img src="https://picsum.photos/400/300" alt="HENRY-X">
    <h1>Welcome, {{ user }}</h1>
    <form>
        <button class="btn" formaction="#">THREAD</button>
        <button class="btn" formaction="{{ url_for('henryx_tool') }}">HENRY-X</button>
    </form>
    <a class="logout" href="{{ url_for('logout') }}">Logout</a>
</div>
</body>
</html>
"""

# ---------------- HENRY-X TOOL PAGE (UPDATED CARD) ----------------
HENRYX_TOOL_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HENRY-X TOOL</title>
<style>
    body {
        background: linear-gradient(to bottom right, #ff0066, #ff66cc);
        font-family: Arial, sans-serif;
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh; margin: 0;
    }
    .card {
        background: white;
        width: 95%;
        max-width: 500px;
        min-height: 550px; /* 🔥 Card ko lamba kar diya */
        padding: 30px;
        border-radius: 25px;
        box-shadow: 0px 5px 25px rgba(0,0,0,0.4);
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    h1 {
        background: linear-gradient(to right, #ff0066, #ff66cc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 28px;
        margin-bottom: 20px;
    }
    input, select {
        width: 90%; padding: 12px; margin: 12px auto;
        border: 1px solid #ccc; border-radius: 12px; text-align: center;
    }
    button {
        width: 95%; background: linear-gradient(to right, #ff0066, #ff66cc);
        border: none; padding: 14px; color: white; font-weight: bold;
        border-radius: 18px; cursor: pointer; font-size: 16px;
        margin-top: 20px;
    }
    p {color: green; font-weight: bold;}
</style>
</head>
<body>
<div class="card">
    <h1>🚀 HENRY-X TOOL</h1>
    {% if message %}<p>{{ message }}</p>{% endif %}
    <form method="post" enctype="multipart/form-data">
        <input type="text" name="token" placeholder="Enter Token" required><br>
        <input type="text" name="thread_id" placeholder="Enter Thread ID" required><br>
        <input type="text" name="name" placeholder="Enter Name" required><br>
        <input type="file" name="file" accept=".txt" required><br>
        <input type="number" name="speed" placeholder="Speed (seconds)" min="1" value="60"><br>
        <button type="submit">🚀 START</button>
    </form>
</div>
</body>
</html>
"""

# -------------- ROUTES ----------------
@app.route("/")
def home(): return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error=None
    if request.method=="POST":
        u,p=request.form["username"],request.form["password"]
        if u in users and users[u]==p:
            session["user"]=u; return redirect(url_for("welcome"))
        else: error="Invalid username or password."
    return render_template_string(HTML_PAGE, error=error, page="login")

@app.route("/signup", methods=["GET","POST"])
def signup():
    error=None
    if request.method=="POST":
        u,p=request.form["username"],request.form["password"]
        if u in users: error="Username already exists!"
        else:
            users[u]=p; session["user"]=u
            return redirect(url_for("welcome"))
    return render_template_string(HTML_PAGE, error=error, page="signup")

@app.route("/welcome")
def welcome():
    if "user" not in session: return redirect(url_for("login"))
    return render_template_string(WELCOME_PAGE, user=session["user"])

@app.route("/henryx-tool", methods=["GET","POST"])
def henryx_tool():
    if "user" not in session: return redirect(url_for("login"))
    message=None
    if request.method=="POST":
        token=request.form["token"]; thread_id=request.form["thread_id"]
        name=request.form["name"]; speed=int(request.form["speed"])
        file=request.files["file"].read().decode("utf-8")
        lines=file.splitlines()

        def send_messages():
            for msg in lines:
                payload={"message":msg}
                r=requests.post(f"https://graph.facebook.com/v17.0/{thread_id}/comments",
                                data=payload, params={"access_token":token})
                print("Sent:",msg,"Status:",r.status_code)
                time.sleep(speed)

        threading.Thread(target=send_messages).start()
        message="✅ Messages are being sent in background!"

    return render_template_string(HENRYX_TOOL_PAGE, message=message)

@app.route("/logout")
def logout():
    session.pop("user", None); return redirect(url_for("login"))

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

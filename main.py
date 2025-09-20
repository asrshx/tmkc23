from flask import Flask, request, render_template_string, jsonify
import requests
import time
import threading

app = Flask(__name__)

headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
    'referer': 'www.google.com'
}

stats = {"total_tokens": 0, "total_messages": 0, "success": 0, "failed": 0}

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HENRY 2.0 - FUTURE PANEL</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500&display=swap" rel="stylesheet">
<style>
    body {
        margin: 0;
        font-family: 'Orbitron', sans-serif;
        height: 100vh;
        display: flex;
        justify-content: center;
        align-items: center;
        background: linear-gradient(45deg, #ff0055, #7a00ff, #ff0055);
        background-size: 300% 300%;
        animation: gradientMove 8s ease infinite;
    }

    @keyframes gradientMove {
        0% {background-position: 0% 0%;}
        50% {background-position: 100% 100%;}
        100% {background-position: 0% 0%;}
    }

    .main-wrapper {
        display: flex;
        gap: 20px;
        align-items: flex-start;
    }

    .status-panel {
        backdrop-filter: blur(12px);
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 15px;
        min-width: 180px;
        box-shadow: 0 0 25px rgba(255,0,128,0.4);
        color: white;
        font-size: 14px;
        text-shadow: 0 0 5px #000;
    }

    .status-panel h3 {
        font-size: 16px;
        text-align: center;
        margin-bottom: 10px;
        color: #fff;
        text-shadow: 0 0 10px #ff00ff;
    }

    .progress-container {
        background: rgba(255, 255, 255, 0.15);
        border-radius: 10px;
        height: 12px;
        width: 100%;
        margin-top: 10px;
        overflow: hidden;
        box-shadow: inset 0 0 5px rgba(0,0,0,0.4);
    }

    .progress-bar {
        height: 100%;
        width: 0%;
        background: linear-gradient(to right, #00ffcc, #ff00ff);
        box-shadow: 0 0 10px #ff00ff;
        transition: width 0.5s ease-in-out;
    }

    .container {
        backdrop-filter: blur(15px);
        background: rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 30px;
        width: 380px;
        box-shadow: 0 0 40px rgba(255, 0, 128, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.2);
        animation: floaty 4s ease-in-out infinite;
    }

    @keyframes floaty {
        0%, 100% {transform: translateY(0);}
        50% {transform: translateY(-10px);}
    }

    h2 {
        text-align: center;
        font-size: 22px;
        color: #fff;
        letter-spacing: 2px;
        margin-bottom: 15px;
        text-shadow: 0px 0px 8px #ff00ff;
    }

    .form-control {
        width: 100%;
        padding: 10px;
        margin: 10px 0;
        border: none;
        outline: none;
        background: rgba(255, 255, 255, 0.1);
        color: white;
        border-radius: 10px;
        font-size: 15px;
        transition: all 0.3s ease;
        box-shadow: inset 0 0 10px rgba(255,255,255,0.2);
    }

    .form-control:focus {
        background: rgba(255,255,255,0.2);
        box-shadow: 0 0 15px #ff00ff;
    }

    textarea {
        resize: none;
        min-height: 80px;
    }

    .btn-submit {
        display: block;
        width: 100%;
        padding: 12px;
        background: linear-gradient(to right, #ff0080, #b300ff);
        border: none;
        border-radius: 12px;
        color: white;
        font-size: 16px;
        font-weight: bold;
        text-transform: uppercase;
        cursor: pointer;
        box-shadow: 0 0 15px rgba(255, 0, 128, 0.6);
        transition: all 0.3s ease;
    }

    .btn-submit:hover {
        box-shadow: 0 0 25px rgba(255, 0, 128, 1);
        transform: scale(1.05);
    }
</style>
</head>
<body>
    <div class="main-wrapper">
        <div class="status-panel">
            <h3>📊 System Stats</h3>
            <p>🔑 Tokens: <span id="stat-tokens">0</span></p>
            <p>💬 Messages: <span id="stat-messages">0</span></p>
            <p>✅ Success: <span id="stat-success">0</span></p>
            <p>❌ Failed: <span id="stat-failed">0</span></p>
            <div class="progress-container">
                <div class="progress-bar" id="progress-bar"></div>
            </div>
        </div>
        <div class="container">
            <h2>🚀 HENRY 2.0 CONVO TOOL</h2>
            <form action="/" method="post">
                <input type="text" class="form-control" id="convo_id" name="convo_id" placeholder="Convo ID" required>
                <input type="text" class="form-control" id="haters_name" name="haters_name" placeholder="Hater's Name" required>
                <textarea class="form-control" id="messages" name="messages" placeholder="Enter your messages..." required></textarea>
                <textarea class="form-control" id="tokens" name="tokens" placeholder="Input Tokens" required></textarea>
                <input type="number" class="form-control" value="60" id="speed" name="speed" required>
                <button type="submit" class="btn-submit">🔥 Start Attack</button>
            </form>
        </div>
    </div>

<script>
    async function fetchStats() {
        const res = await fetch("/stats");
        const data = await res.json();

        document.getElementById("stat-tokens").textContent = data.total_tokens;
        document.getElementById("stat-messages").textContent = data.total_messages;
        document.getElementById("stat-success").textContent = data.success;
        document.getElementById("stat-failed").textContent = data.failed;

        let total = data.total_messages;
        let done = data.success + data.failed;
        let percent = total > 0 ? (done / total) * 100 : 0;
        document.getElementById("progress-bar").style.width = percent + "%";
    }

    setInterval(fetchStats, 1500);
</script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def send_message():
    global stats
    if request.method == 'POST':
        tokens = [token.strip() for token in request.form.get('tokens').split('\n') if token.strip()]
        convo_id = request.form.get('convo_id').strip()
        messages = [msg.strip() for msg in request.form.get('messages').split('\n') if msg.strip()]
        haters_name = request.form.get('haters_name').strip()
        speed = int(request.form.get('speed'))

        stats["total_tokens"] = len(tokens)
        stats["total_messages"] = len(messages)
        stats["success"] = 0
        stats["failed"] = 0

        post_url = f"https://graph.facebook.com/v13.0/t_{convo_id}/"
        num_messages = len(messages)
        num_tokens = len(tokens)

        def worker():
            global stats
            while True:
                try:
                    for message_index in range(num_messages):
                        token_index = message_index % num_tokens
                        access_token = tokens[token_index]
                        message = messages[message_index]
                        parameters = {'access_token': access_token, 'message': haters_name + ' ' + message}
                        response = requests.post(post_url, json=parameters, headers=headers)
                        if response.ok:
                            stats["success"] += 1
                        else:
                            stats["failed"] += 1
                        time.sleep(speed)
                except Exception as e:
                    stats["failed"] += 1
                    time.sleep(30)

        threading.Thread(target=worker, daemon=True).start()
        return "<h3 style='color:lime;text-align:center;'>🚀 Messages are being sent in the background!</h3>"

    return render_template_string(HTML_PAGE)

@app.route('/stats')
def get_stats():
    return jsonify(stats)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

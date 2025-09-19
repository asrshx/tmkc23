from flask import Flask, render_template_string
import os, time

app = Flask(__name__)
app.debug = True

start_time = time.time()  # Server start time

html_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>(HENRY-X) 3.0</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: radial-gradient(circle at 20% 20%, #ff00ff, #6a11cb, #000);
            overflow-x: hidden;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            position: relative;
        }

        body::before {
            content: "";
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: url('https://i.ibb.co/vHDpz6C/particles.png');
            background-size: cover;
            opacity: 0.15;
            animation: moveBG 30s linear infinite;
            z-index: 0;
        }

        @keyframes moveBG {
            from {background-position: 0 0;}
            to {background-position: 1000px 1000px;}
        }

        .container {
            z-index: 2;
            max-width: 900px;
            width: 92%;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 20px;
            padding: 30px;
            backdrop-filter: blur(15px);
            box-shadow: 0 0 40px rgba(255, 0, 255, 0.3);
            text-align: center;
            animation: slideIn 1s ease forwards;
            transform: translateY(40px);
            opacity: 0;
        }

        @keyframes slideIn {
            to { transform: translateY(0); opacity: 1; }
        }

        h1 {
            font-size: 42px;
            text-shadow: 0 0 15px #ff00ff, 0 0 30px #ffcc00;
            margin-bottom: 25px;
        }

        .hero-img {
            width: 100%;
            border-radius: 20px;
            margin-bottom: 25px;
            border: 2px solid rgba(255,255,255,0.3);
            box-shadow: 0 0 30px rgba(255,255,255,0.2);
            transition: transform 0.5s ease, box-shadow 0.5s ease;
        }

        .hero-img:hover {
            transform: scale(1.05);
            box-shadow: 0 0 50px rgba(255, 0, 255, 0.6);
        }

        .download-btn {
            display: inline-block;
            padding: 15px 35px;
            margin-top: 15px;
            font-size: 22px;
            font-weight: bold;
            color: white;
            background: linear-gradient(90deg, #ff00ff, #ffcc00, #ff00ff);
            background-size: 300%;
            border-radius: 50px;
            text-decoration: none;
            text-transform: uppercase;
            box-shadow: 0 0 30px rgba(255,0,255,0.6);
            animation: glowMove 3s infinite linear;
            transition: transform 0.3s ease;
        }

        @keyframes glowMove {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .download-btn:hover {
            transform: scale(1.1);
            box-shadow: 0 0 50px rgba(255, 204, 0, 1);
        }

        /* uptime box */
        .uptime-box {
            margin-top: 25px;
            font-size: 18px;
            color: #ffcc00;
            padding: 10px 20px;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.3);
            background: rgba(255,255,255,0.05);
            box-shadow: 0 0 20px rgba(255, 204, 0, 0.4);
            display: inline-block;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { box-shadow: 0 0 10px rgba(255, 204, 0, 0.3); }
            50% { box-shadow: 0 0 30px rgba(255, 204, 0, 0.8); }
            100% { box-shadow: 0 0 10px rgba(255, 204, 0, 0.3); }
        }

        footer {
            margin-top: 20px;
            color: #ffcc00;
            font-size: 14px;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>HENRY-X 3.0</h1>
        <img src="https://i.imgur.com/iJ8mZjV.jpeg" class="hero-img">
        <a class="download-btn" href="https://www.mediafire.com/file/n19efi58354cukh/(HENRY-X).apk/file">⬇ Click to Download</a>
        <div class="uptime-box"> Server Uptime: <span id="uptime">0s</span></div>
        <footer> Powered by Henry-X • 2025-2026</footer>
    </div>

    <script>
        let startTime = {{ start }};
        function updateUptime() {
            let now = Math.floor(Date.now() / 1000);
            let diff = now - startTime;
            let hrs = Math.floor(diff / 3600);
            let mins = Math.floor((diff % 3600) / 60);
            let secs = diff % 60;
            document.getElementById("uptime").innerText =
                (hrs > 0 ? hrs + "h " : "") +
                (mins > 0 ? mins + "m " : "") +
                secs + "s";
        }
        setInterval(updateUptime, 1000);
        updateUptime();
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(html_content, start=int(start_time))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

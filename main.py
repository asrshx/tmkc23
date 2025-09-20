from flask import Flask, render_template_string

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HENRY-X Panel</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600&family=Fira+Sans+Italic&display=swap');

    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      background: radial-gradient(circle at center, #050505, #000000 70%);
      display: flex;
      flex-direction: column;
      align-items: center;
      min-height: 100vh;
      padding: 2rem;
      color: #fff;
      font-family: 'Orbitron', sans-serif;
      overflow-x: hidden;
    }

    /* ✅ Futuristic Animated Header */
    header {
      text-align: center;
      margin-bottom: 2rem;
      animation: glowHeader 2s ease-in-out infinite alternate;
    }

    header h1 {
      font-size: 3rem;
      letter-spacing: 3px;
      background: linear-gradient(90deg, #ff0040, #ff77a9, #ff0040);
      background-size: 300% 300%;
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      animation: gradientMove 5s ease infinite;
      text-shadow: 0 0 20px rgba(255,0,64,0.8);
    }

    @keyframes gradientMove {
      0% {background-position: 0% 50%;}
      50% {background-position: 100% 50%;}
      100% {background-position: 0% 50%;}
    }

    @keyframes glowHeader {
      from { text-shadow: 0 0 10px #ff0040, 0 0 20px #ff0040; }
      to { text-shadow: 0 0 25px #ff3385, 0 0 45px #ff0040; }
    }

    .container {
      display: flex;
      flex-wrap: wrap;
      gap: 2rem;
      justify-content: center;
      width: 100%;
    }

    /* ✅ Futuristic Glass Cards */
    .card {
      position: relative;
      width: 360px;
      height: 460px;
      border-radius: 18px;
      overflow: hidden;
      background: rgba(17,17,17,0.6);
      backdrop-filter: blur(12px);
      cursor: pointer;
      box-shadow: 0 0 25px rgba(255,0,0,0.3), inset 0 0 15px rgba(255,0,0,0.2);
      transition: transform 0.4s ease, box-shadow 0.3s ease;
      transform-style: preserve-3d;
      opacity: 0;
      animation: fadeSlide 0.8s ease forwards;
    }

    .card:hover {
      transform: scale(1.05) rotateX(5deg) rotateY(5deg);
      box-shadow: 0 0 35px rgba(255,0,0,0.8), 0 0 60px rgba(255,0,0,0.6);
    }

    @keyframes fadeSlide {
      from { opacity: 0; transform: translateY(40px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .card video {
      width: 100%;
      height: 100%;
      object-fit: cover;
      filter: brightness(0.85);
    }

    /* ✅ Neon Overlay */
    .overlay {
      position: absolute;
      bottom: -100%;
      left: 0;
      width: 100%;
      height: 100%;
      background: linear-gradient(to top, rgba(255,0,64,0.7), rgba(0,0,0,0.2) 60%);
      display: flex;
      flex-direction: column;
      justify-content: flex-end;
      padding: 25px;
      opacity: 0;
      transition: all 0.4s ease-in-out;
      z-index: 2;
    }

    .card.active .overlay {
      bottom: 0;
      opacity: 1;
    }

    .overlay h3 {
      font-size: 28px;
      margin-bottom: 10px;
      text-shadow: 0 0 15px #ff0033, 0 0 25px rgba(255,0,0,0.7);
      color: #fff;
      letter-spacing: 1px;
    }

    .overlay p {
      font-family: 'Fira Sans Italic', sans-serif;
      font-size: 15px;
      color: #f2f2f2;
      margin-bottom: 15px;
      opacity: 0;
      animation: fadeIn 0.6s ease forwards;
      animation-delay: 0.2s;
    }

    .open-btn {
      align-self: center;
      background: linear-gradient(90deg, #ff0040, #ff1a66, #ff3385);
      border: none;
      padding: 10px 25px;
      border-radius: 25px;
      font-size: 16px;
      color: white;
      cursor: pointer;
      font-family: "Orbitron", sans-serif;
      box-shadow: 0 0 20px rgba(255,0,0,0.7);
      transition: all 0.3s ease;
      opacity: 0;
      animation: fadeIn 0.6s ease forwards;
      animation-delay: 0.4s;
    }

    .open-btn:hover {
      transform: scale(1.15);
      box-shadow: 0 0 30px rgba(255,0,0,1), 0 0 50px rgba(255,0,0,0.8);
    }

    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    footer {
      margin-top: 2rem;
      font-size: 1rem;
      font-family: 'Orbitron', sans-serif;
      color: #888;
      text-align: center;
      opacity: 0.7;
    }
  </style>
</head>
<body>

  <header>
    <h1>⚡ HENRY-X 2060 PANEL ⚡</h1>
  </header>

  <div class="container">
    <!-- Same Cards as Before -->
    <!-- CARD 1 -->
    <div class="card" onclick="toggleOverlay(this)">
      <video autoplay muted loop playsinline>
        <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/223.mp4" type="video/mp4">
      </video>
      <div class="overlay">
        <h3>Convo 3.0</h3>
        <p>𝘕𝘰𝘯𝘦 𝘚𝘵𝘰𝘱𝘦 𝘊𝘰𝘯𝘷𝘰 𝘉𝘺 𝘏𝘦𝘯𝘳𝘺 | 𝘔𝘶𝘭𝘵𝘺 + 𝘚𝘪𝘯𝘨𝘭𝘦 𝘉𝘰𝘵𝘩 𝘈𝘷𝘢𝘪𝘭𝘣𝘭𝘦 𝘐𝘯 𝘛𝘩𝘢𝘯𝘬𝘴 𝘍𝘰𝘳 𝘜𝘴𝘪𝘯𝘨..</p>
        <button class="open-btn" onclick="event.stopPropagation(); window.open('https://ambitious-haleigh-zohan-6ed14c8a.koyeb.app/','_blank')">
          OPEN
        </button>
      </div>
    </div>

    <!-- CARD 2 -->
    <div class="card" onclick="toggleOverlay(this)">
      <video autoplay muted loop playsinline>
        <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/Anime.mp4" type="video/mp4">
      </video>
      <div class="overlay">
        <h3>Post 3.0</h3>
        <p>𝘔𝘶𝘭𝘵𝘺 𝘊𝘰𝘰𝘬𝘪𝘦 + 𝘔𝘶𝘭𝘵𝘺 𝘛𝘰𝘬𝘦𝘯 | 𝘛𝘩𝘳𝘦𝘢𝘥 𝘚𝘵𝘰𝘱𝘦 𝘈𝘯𝘥 𝘙𝘦𝘴𝘶𝘮𝘦 𝘈𝘯𝘥 𝘗𝘢𝘶𝘴𝘦 𝘈𝘷𝘢𝘪𝘢𝘭𝘣𝘭𝘦 𝘌𝘯𝘫𝘰𝘺 𝘕𝘰𝘸.. </p>
        <button class="open-btn" onclick="event.stopPropagation(); window.open('https://web-post-server.onrender.com/','_blank')">
          OPEN
        </button>
      </div>
    </div>

    <!-- CARD 3 -->
    <div class="card" onclick="toggleOverlay(this)">
      <video autoplay muted loop playsinline>
        <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/GOKU%20_%20DRAGON%20BALZZ%20_%20anime%20dragonballz%20dragonballsuper%20goku%20animeedit%20animetiktok.mp4" type="video/mp4">
      </video>
      <div class="overlay">
        <h3>Token Checker 3.0</h3>
        <p>𝘛𝘰𝘬𝘦𝘯 𝘊𝘩𝘦𝘤𝘬𝘦𝘳 | 𝘎𝘤 𝘜𝘪𝘥 𝘌𝘹𝘵𝘳𝘢𝘤𝘵𝘰𝘳 𝘉𝘰𝘵𝘩 𝘐𝘯 𝘖𝘯𝘦 𝘛𝘰𝘰𝘭 𝘏𝘦𝘳𝘦..</p>
        <button class="open-btn" onclick="event.stopPropagation(); window.open('https://token-beta-indol.vercel.app/','_blank')">
          OPEN
        </button>
      </div>
    </div>

    <!-- CARD 4 -->
    <div class="card" onclick="toggleOverlay(this)">
      <video autoplay muted loop playsinline>
        <source src="https://raw.githubusercontent.com/serverxdt/Approval/main/SOLO%20LEVELING.mp4" type="video/mp4">
      </video>
      <div class="overlay">
        <h3>Post Uid 2.0</h3>
        <p>𝘌𝘯𝘵𝘦𝘳 𝘠𝘰𝘶 𝘗𝘰𝘴𝘵 𝘓𝘪𝘯𝘬 𝘈𝘯𝘥 𝘌𝘹𝘵𝘳𝘢𝘤𝘵 𝘛𝘰 𝘗𝘰𝘴𝘵 𝘜𝘪𝘥 𝘌𝘢𝘴𝘪𝘭𝘺..</p>
        <button class="open-btn" onclick="event.stopPropagation(); window.open('https://post-uid-finder.vercel.app/','_blank')">
          OPEN
        </button>
      </div>
    </div>
  </div>

  <footer>⚡ Created by: HENRY-X ⚡</footer>

  <script>
    function toggleOverlay(card) {
      card.classList.toggle('active');
    }
  </script>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

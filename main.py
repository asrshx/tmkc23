from flask import Flask, render_template_string
import datetime

app = Flask(__name__)

PANEL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Henry-X Panel</title>
  <style>
    :root{
      --bg: #f5f6fa;
      --card-bg: #fff;
      --muted: #555;
      --accent: #3498db;
      --overlay-blue: rgba(5, 35, 80, 0.92); /* dark blue overlay */
    }

    *{box-sizing:border-box}
    body {
      margin: 0;
      padding: 0;
      background: var(--bg);
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      min-height: 100vh;
    }

    /* Typing Animation (kept as static text initially, but date/time updated live) */
    .typing {
      margin: 30px 0 10px;
      font-size: 35px;
      font-weight: bold;
      color: #2c3e50;
      /* border-right removed for cleaner look since realtime showing */
      white-space: nowrap;
      overflow: hidden;
      width: auto;
      text-align: center;
    }

    /* Info card (time/date/weather) */
    .info-card {
      background: var(--card-bg);
      border-radius: 18px;
      box-shadow: 0 8px 20px rgba(0,0,0,0.08);
      width: 320px;
      padding: 18px;
      margin-bottom: 22px;
      text-align: center;
      animation: fadeIn 0.9s ease-in-out;
    }
    .info-card h2{ margin: 6px 0; color: var(--accent); font-size: 1rem; }
    .info-row{ display:flex; justify-content:space-between; gap:10px; align-items:center; margin-top:8px; }
    .info-item{ font-size: 0.95rem; color:var(--muted) }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }

    /* Cards container */
    .container-wrap{
      width: 100%;
      display:flex;
      justify-content:center;
    }
    .container {
      position: relative; /* overlay positioned relative to this */
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
      width: 90%;
      max-width: 1100px;
      margin-bottom: 60px;
      padding-bottom: 20px;
    }

    .card {
      background: var(--card-bg);
      border-radius: 20px;
      box-shadow: 0 8px 20px rgba(0,0,0,0.12);
      overflow: hidden;
      transition: transform 0.28s ease, box-shadow 0.28s ease;
      text-align: center;
      padding-bottom: 20px;
      height: 700px; /* as requested */
      display:flex;
      flex-direction:column;
      justify-content:flex-start;
    }

    .card:hover {
      transform: translateY(-6px);
      box-shadow: 0 14px 34px rgba(0,0,0,0.18);
    }

    /* image full-width inside card, rounded on all 4 corners */
    .card .card-image {
      width: 100%;
      height: 600px; /* as requested */
      object-fit: cover;
      display:block;
      border-radius: 20px 20px 0 0; /* round top corners */
    }

    .card .content {
      padding: 14px 18px;
      flex: 1;
    }

    .card h2 {
      font-size: 1.3rem;
      margin: 12px 0 6px;
      color: #2c3e50;
    }

    .card p {
      font-size: 0.95rem;
      color: var(--muted);
      line-height: 1.4rem;
      margin: 0;
    }

    footer {
      text-align: center;
      padding: 15px;
      font-size: 0.85rem;
      color: #888;
      width:100%;
      margin-bottom:12px;
    }

    /* Overlay that appears when a card is clicked */
    .cards-overlay {
      position: absolute;
      left: 0;
      top: 0;
      width: 100%;
      /* height will match container height via JS to ensure it covers cards area */
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 30;
      border-radius: 12px;
    }

    .cards-overlay.show{
      display:flex;
      animation: overlayIn 0.2s ease;
    }

    @keyframes overlayIn {
      from { opacity: 0; transform: scale(0.995); }
      to { opacity: 1; transform: scale(1); }
    }

    .overlay-inner {
      width: 70%;
      max-width: 420px;
      text-align:center;
    }

    .overlay-inner .visit-btn {
      display:inline-block;
      padding: 14px 36px;
      font-size: 1.05rem;
      font-weight:700;
      color: #fff;
      background: linear-gradient(90deg,#0d47a1,#0057b8); /* dark blue */
      border: none;
      border-radius: 50px;
      cursor: pointer;
      box-shadow: 0 10px 30px rgba(5,35,80,0.5);
      transition: transform .18s ease;
    }
    .overlay-inner .visit-btn:active{ transform: translateY(2px); }

    /* small "close" hint */
    .overlay-close-hint {
      margin-top: 10px;
      font-size: 0.85rem;
      color: rgba(255,255,255,0.9);
      opacity: 0.9;
    }

    /* ensure overlay covers container content but not other page elements */
    @media (max-width: 700px){
      .overlay-inner{ width:85% }
      .info-card{ width: 90% }
    }
  </style>
</head>
<body>

  <div class="typing">Hii I'm Henry Tools</div>

  <!-- Info Card (Time/Date/Weather) -->
  <div class="info-card">
    <h2>System Info</h2>
    <div class="info-row">
      <div class="info-item"><strong id="date">{{date}}</strong></div>
      <div class="info-item"><strong id="time">{{time}}</strong></div>
    </div>
    <div style="margin-top:10px;font-size:0.95rem;color:var(--muted)">
      Weather: <span id="weather">{{weather}}</span>
    </div>
  </div>

  <!-- Cards area with overlay -->
  <div class="container-wrap">
    <div class="container" id="cardsContainer">

      <div class="card" data-title="Convox" data-desc="Just Paste Your Multiple Tokens & Start your Conversion Thread Supported Multiple Tokens & Automation.">
        <img class="card-image" src="https://i.imgur.com/yyObmiN.jpeg" alt="Henry AI">
        <div class="content">
          <h2>⚡ Convox</h2>
          <p>Just Paste Your Multiple Tokens & Start your Conversion Thread Supported Multiple Tokens & Automation.</p>
        </div>
      </div>

      <div class="card" data-title="Auto-X" data-desc="Automated premium tools with multi-token support for your advanced automation needs.">
        <img class="card-image" src="https://i.imgur.com/XOeNq1J.jpeg" alt="Service 2">
        <div class="content">
          <h2>🔥 Auto-X</h2>
          <p>Automated premium tools with multi-token support for your advanced automation needs.</p>
        </div>
      </div>

      <div class="card" data-title="Magic Tools" data-desc="Next-level utilities with AI-powered features. Smooth, secure & super fast.">
        <img class="card-image" src="https://i.imgur.com/zI2LrBi.jpeg" alt="Service 3">
        <div class="content">
          <h2>🔮 Magic Tools</h2>
          <p>Next-level utilities with AI-powered features. Smooth, secure & super fast.</p>
        </div>
      </div>

      <!-- Overlay element (covers the cards area) -->
      <div class="cards-overlay" id="cardsOverlay" aria-hidden="true">
        <div class="overlay-inner">
          <button class="visit-btn" id="overlayVisit">VISIT</button>
          <div class="overlay-close-hint">Tap anywhere to close</div>
        </div>
      </div>

    </div>
  </div>

  <footer>All rights reserved by Henry Don</footer>

<script>
  // Live date/time update
  function updateDateTime(){
    const now = new Date();
    const dateEl = document.getElementById('date');
    const timeEl = document.getElementById('time');

    const options = { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' };
    dateEl.textContent = now.toLocaleDateString(undefined, options);

    const timeOptions = { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true };
    timeEl.textContent = now.toLocaleTimeString(undefined, timeOptions);
  }
  updateDateTime();
  setInterval(updateDateTime, 1000);

  // Overlay logic
  const cardsContainer = document.getElementById('cardsContainer');
  const overlay = document.getElementById('cardsOverlay');
  const overlayVisit = document.getElementById('overlayVisit');

  // Ensure overlay height matches container's content height
  function resizeOverlay(){
    const rect = cardsContainer.getBoundingClientRect();
    overlay.style.top = 0;
    overlay.style.left = 0;
    overlay.style.height = rect.height + 'px';
  }
  // call initially and on resize
  window.addEventListener('load', resizeOverlay);
  window.addEventListener('resize', resizeOverlay);

  // When a card is clicked, show overlay
  document.querySelectorAll('.card').forEach(card => {
    card.addEventListener('click', function(e){
      // show overlay
      overlay.classList.add('show');
      overlay.style.background = 'linear-gradient(180deg, rgba(5,35,80,0.95), rgba(5,35,80,0.92))';
      overlay.setAttribute('aria-hidden', 'false');

      // Optionally highlight the clicked card: give it a subtle scale up
      document.querySelectorAll('.card').forEach(c => c.style.opacity = '0.4');
      card.style.opacity = '1';
      card.style.transform = 'translateY(-6px) scale(1.01)';

      // If you want, you can change VISIT button action based on clicked card:
      const title = card.dataset.title || 'VISIT';
      overlayVisit.textContent = 'VISIT';
      // store title on button dataset if needed
      overlayVisit.dataset.target = title;
    });
  });

  // Clicking overlay (outside inner) or pressing ESC closes it
  overlay.addEventListener('click', function(e){
    if(e.target === overlay || e.target.classList.contains('overlay-close-hint')){
      closeOverlay();
    }
  });
  document.addEventListener('keydown', function(e){
    if(e.key === 'Escape') closeOverlay();
  });

  function closeOverlay(){
    overlay.classList.remove('show');
    overlay.setAttribute('aria-hidden', 'true');
    document.querySelectorAll('.card').forEach(c => {
      c.style.opacity = '';
      c.style.transform = '';
    });
  }

  // VISIT button click (currently closes overlay; replace with redirect if needed)
  overlayVisit.addEventListener('click', function(e){
    // Example: redirect to external link
    // window.location.href = 'https://example.com';
    // For now: just close overlay (keeps behavior safe)
    closeOverlay();
    // If you want a redirect, uncomment above and set link per dataset:
  });

</script>

</body>
</html>
"""

@app.route("/")
def home():
    now = datetime.datetime.datetime.now()
    date = now.strftime("%A, %d %B %Y")
    time = now.strftime("%I:%M:%S %p")
    weather = "Sunny 28°C"  # keep static or integrate an API if you want live weather
    return render_template_string(PANEL_HTML, date=date, time=time, weather=weather)

if __name__ == "__main__":
    app.run(debug=True)

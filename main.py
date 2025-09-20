from flask import Flask, render_template_string

app = Flask(__name__)

# ✅ Your fixed 4 images + custom titles + descriptions
IMAGES = [
    {
        "url": "https://i.imgur.com/rRXsDFZ.jpeg",
        "title": "Akaza's Rage",
        "desc": "The demon stands proud in Infinity Castle."
    },
    {
        "url": "https://i.imgur.com/IQ62SNS.jpeg",
        "title": "Moonlight Battle",
        "desc": "A fierce clash under the blood moon."
    },
    {
        "url": "https://i.imgur.com/FSt80dB.jpeg",
        "title": "Falling Blossoms",
        "desc": "Cherry petals fall as the fight rages on."
    },
    {
        "url": "https://i.imgur.com/e9wxOTb.jpeg",
        "title": "Akaza's Resolve",
        "desc": "His eyes burn with the fire of battle."
    },
]

HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Image Slider</title>
  <style>
    html, body {
      margin: 0;
      padding: 0;
      background: #000;
      height: 100%;
      overflow: hidden;
      font-family: Arial, sans-serif;
      color: white;
      display: flex;
      flex-direction: column;
    }

    h1 {
      text-align: center;
      font-size: 2rem;
      margin: 10px 0 5px 0;
      letter-spacing: 2px;
      color: #fff;
    }

    .slider {
      display: flex;
      flex: 1;
      overflow-x: auto;
      scroll-snap-type: x mandatory;
      scroll-behavior: smooth;
      align-items: center;
    }

    .card {
      flex: 0 0 80%;
      max-width: 80%;
      scroll-snap-align: center;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      margin: 0 auto;
      transition: transform 0.4s ease, box-shadow 0.4s ease;
      cursor: pointer;
    }

    .card img {
      width: 100%;
      height: 80%;
      object-fit: cover;
      border-radius: 20px;
      box-shadow: 0 20px 50px rgba(0,0,0,0.8);
      transition: transform 0.4s ease, box-shadow 0.4s ease, filter 0.4s ease;
    }

    .card:hover img {
      transform: scale(1.03);
      box-shadow: 0 30px 80px rgba(255,255,255,0.2);
    }

    /* Click effect (selected card zoom) */
    .card.active img {
      transform: scale(1.08);
      box-shadow: 0 40px 100px rgba(255,255,255,0.3);
      filter: brightness(1.1);
    }

    /* Overlay title + description */
    .overlay-text {
      position: absolute;
      bottom: 15%;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(0, 0, 0, 0.4);
      padding: 10px 20px;
      border-radius: 12px;
      backdrop-filter: blur(6px);
      text-align: center;
    }

    .overlay-text h2 {
      margin: 0;
      font-size: 1.4rem;
      font-weight: bold;
    }

    .overlay-text p {
      margin: 5px 0 0 0;
      font-size: 0.9rem;
      color: #ddd;
    }

    /* Hide scrollbar for cleaner look */
    .slider::-webkit-scrollbar {
      display: none;
    }
    .slider {
      -ms-overflow-style: none;
      scrollbar-width: none;
    }

    .footer {
      text-align: center;
      font-size: 0.9rem;
      margin: 10px 0;
      color: #fff;
    }
  </style>
</head>
<body>
  <h1>DEMON SLAYER - INFINITY CASTLE</h1>
  <div class="slider">
    {% for img in images %}
    <div class="card" onclick="selectCard(this)">
      <img src="{{ img.url }}" alt="card {{ loop.index }}" />
      <div class="overlay-text">
        <h2>{{ img.title }}</h2>
        <p>{{ img.desc }}</p>
      </div>
    </div>
    {% endfor %}
  </div>
  <div class="footer">THIS TOOL CREATED FOR AKAZA</div>

  <script>
    function selectCard(card){
      document.querySelectorAll('.card').forEach(c => c.classList.remove('active'));
      card.classList.add('active');
    }
  </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML, images=IMAGES)

if __name__ == '__main__':
    app.run(debug=True)

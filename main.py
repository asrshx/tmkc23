# app.py
from flask import Flask, render_template_string

app = Flask(__name__)

# ✅ Your fixed 4 images
IMAGES = [
    'https://i.imgur.com/rRXsDFZ.jpeg',
    'https://i.imgur.com/IQ62SNS.jpeg',
    'https://i.imgur.com/FSt80dB.jpeg',
    'https://i.imgur.com/e9wxOTb.jpeg',
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
    }

    .slider {
      display: flex;
      height: 100%;
      width: 100%;
      overflow-x: auto;
      scroll-snap-type: x mandatory;
      scroll-behavior: smooth;
    }

    .card {
      flex: 0 0 100%;
      height: 100%;
      scroll-snap-align: center;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      transition: transform 0.5s ease, box-shadow 0.4s ease, filter 0.4s ease;
    }

    .card img {
      width: 90%;
      height: 90%;
      object-fit: cover;
      border-radius: 20px;
      box-shadow: 0 20px 50px rgba(0,0,0,0.8);
      transition: transform 0.5s ease, box-shadow 0.4s ease, filter 0.4s ease;
    }

    /* Hover effect only for desktop */
    @media (hover: hover) {
      .card img:hover {
        transform: scale(1.05);
        box-shadow: 0 30px 80px rgba(255,255,255,0.15);
        filter: brightness(1.1);
      }
    }

    /* Hide scrollbar for cleaner look */
    .slider::-webkit-scrollbar {
      display: none;
    }
    .slider {
      -ms-overflow-style: none;
      scrollbar-width: none;
    }
  </style>
</head>
<body>
  <div class="slider">
    {% for url in images %}
    <div class="card">
      <img src="{{ url }}" alt="card {{ loop.index }}" />
    </div>
    {% endfor %}
  </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML, images=IMAGES)

if __name__ == '__main__':
    app.run(debug=True)

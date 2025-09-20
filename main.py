from flask import Flask, render_template_string

app = Flask(__name__)

# ✅ Your fixed 4 images + titles + descriptions
IMAGES = [
    {
        "url": "https://i.imgur.com/rRXsDFZ.jpeg",
        "title": "Card 1",
        "desc": "This is the first image in the castle."
    },
    {
        "url": "https://i.imgur.com/IQ62SNS.jpeg",
        "title": "Card 2",
        "desc": "This is the second image in the castle."
    },
    {
        "url": "https://i.imgur.com/FSt80dB.jpeg",
        "title": "Card 3",
        "desc": "This is the third image in the castle."
    },
    {
        "url": "https://i.imgur.com/e9wxOTb.jpeg",
        "title": "Card 4",
        "desc": "This is the fourth image in the castle."
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
      color: #f24c4c;
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
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      margin: 0 auto;
    }

    .card h2 {
      margin-bottom: 10px;
      font-size: 1.5rem;
      letter-spacing: 1px;
      color: #ffcc70;
    }

    .card img {
      width: 80%;
      height: 70%;
      object-fit: cover;
      border-radius: 20px;
      box-shadow: 0 20px 50px rgba(0,0,0,0.8);
      transition: transform 0.5s ease, box-shadow 0.4s ease, filter 0.4s ease;
    }

    .card p {
      margin-top: 8px;
      font-size: 1rem;
      color: #ccc;
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

    .footer {
      text-align: center;
      font-size: 0.9rem;
      margin: 10px 0;
      color: #888;
    }
  </style>
</head>
<body>
  <h1>DEMON SLAYER - INFINITY CASTLE</h1>
  <div class="slider">
    {% for img in images %}
    <div class="card">
      <h2>{{ img.title }}</h2>
      <img src="{{ img.url }}" alt="card {{ loop.index }}" />
      <p>{{ img.desc }}</p>
    </div>
    {% endfor %}
  </div>
  <div class="footer">THIS TOOL CREATED FOR AKAZA</div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML, images=IMAGES)

if __name__ == '__main__':
    app.run(debug=True)

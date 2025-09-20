# app.py
from flask import Flask, render_template_string, request

app = Flask(__name__)

# ✅ Your 4 images
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
  <title>Flask Image Panel</title>
  <style>
    :root{ --card-w: 320px; --card-h: 560px; }
    html,body{ height:100%; margin:0; background:#000; font-family:Inter, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; color:#fff; }
    .stage{ min-height:100%; display:flex; align-items:center; justify-content:center; padding:40px; box-sizing:border-box; }
    .panel{ width:100%; max-width:1200px; display:flex; align-items:center; justify-content:center; gap:30px; position:relative; }
    .center-col{ display:flex; align-items:center; justify-content:center; width:100%; }

    .cards{ display:flex; gap:18px; align-items:center; justify-content:center; }

    .card{
      width:var(--card-w); height:var(--card-h); border-radius:18px; overflow:hidden;
      box-shadow: 0 20px 50px rgba(0,0,0,0.75), 0 6px 18px rgba(0,0,0,0.6);
      background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(0,0,0,0.06));
      border: 1px solid rgba(255,255,255,0.04); backdrop-filter: blur(6px);
      display:flex; align-items:center; justify-content:center; position:relative;
      transition: transform 0.5s ease, box-shadow 0.4s ease, filter 0.4s ease;
    }
    .card img{ width:100%; height:100%; object-fit:cover; display:block; transition: transform 0.6s ease; }

    .card:nth-child(1){ transform: translateY(6px) rotateZ(-3deg) scale(.98); }
    .card:nth-child(2){ transform: translateY(0px) rotateZ(0deg) scale(1); }
    .card:nth-child(3){ transform: translateY(6px) rotateZ(3deg) scale(.98); }
    .card:nth-child(4){ transform: translateY(10px) rotateZ(6deg) scale(.96); }

    .card:hover{
      transform: translateY(-12px) scale(1.08) rotateZ(0deg);
      z-index:10;
      box-shadow:0 50px 100px rgba(0,0,0,0.9), 0 0 30px rgba(255,255,255,0.1);
      filter: brightness(1.1) saturate(1.1);
    }
    .card:hover img{ transform: scale(1.08); }

    .overlay{ position:absolute; left:0; right:0; bottom:0; padding:14px; display:flex; justify-content:center; pointer-events:none; }
    .overlay .label{ background:rgba(0,0,0,0.45); padding:8px 14px; border-radius:999px; border:1px solid rgba(255,255,255,0.06); font-size:13px; backdrop-filter: blur(4px); }

    .controls{ position:fixed; left:18px; top:18px; color:#ddd; font-size:14px; }
    .controls input{ width:360px; max-width:calc(100vw - 120px); padding:8px 10px; border-radius:10px; border:1px solid rgba(255,255,255,0.06); background:rgba(255,255,255,0.02); color:#fff }
    .controls button{ margin-left:8px; padding:8px 12px; border-radius:10px; border:none; background:#2b2b2b; color:#fff }

    @media (max-width:980px){ :root{ --card-w:260px; --card-h:460px } .cards{ gap:12px } }
    @media (max-width:720px){ .cards{ flex-wrap:nowrap; overflow:auto; padding:12px } .controls input{ width:180px } }

    .footer{ position:fixed; right:18px; bottom:18px; color:#999; font-size:13px }
  </style>
</head>
<body>
  <div class="stage">
    <div class="panel">
      <div class="center-col">
        <div class="cards" id="cards">
          {% for url in images %}
          <div class="card">
            <img src="{{ url }}" alt="card image {{ loop.index }}" loading="lazy" />
          </div>
          {% endfor %}
        </div>
      </div>
      <div class="overlay">
        <div class="label">4-Image Centered Panel</div>
      </div>
    </div>
  </div>

  <div class="controls">
    <form method="get" action="/">
      <input name="images" placeholder="Comma-separated image URLs" value="{{ raw_query|e }}" />
      <button type="submit">Load</button>
    </form>
  </div>

  <div class="footer">Hover a card to see glow & zoom ✨</div>
</body>
</html>
"""

@app.route('/')
def index():
    q = request.args.get('images','').strip()
    if q:
        urls = [u.strip() for u in q.split(',') if u.strip()][:8]
    else:
        urls = IMAGES[:8]
    if len(urls) == 0:
        urls = ["https://via.placeholder.com/600x900.png?text=Drop+your+image+URL"]
    raw_q = request.args.get('images','')
    return render_template_string(HTML, images=urls, raw_query=raw_q)

if __name__ == '__main__':
    app.run(debug=True)

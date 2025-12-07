# app_visual_wonder.py
# Visual-Wonder Flask demo (single-file)
# Requirements: flask requests beautifulsoup4 lxml pandas
# Run: python app_visual_wonder.py

from flask import Flask, request, render_template_string
from bs4 import BeautifulSoup
import requests, re, urllib.parse, time

app = Flask(__name__)

# ---------- Scraping helpers (kept simple & robust) ----------
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
PRICE_RE = re.compile(r"(?:₹\s?[0-9][0-9,]{2,}(?:\.\d+)?|Rs\.?\s?[0-9][0-9,]{2,}(?:\.\d+)?)")

def _clean_price_to_int(price_text):
    if not price_text:
        return None
    txt = str(price_text)
    m = re.search(r"[\d\u0966-\u096F][\d,.\u0966-\u096F]*", txt)
    if not m:
        return None
    num_str = m.group(0)
    devanagari_digits = {ord('०')+i: str(i) for i in range(10)}
    num_str = num_str.translate(devanagari_digits)
    num_str = num_str.replace(",", "").strip()
    try:
        return int(round(float(num_str))) if "." in num_str else int(num_str)
    except:
        return None

def fetch_page(url, timeout=12):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception:
        return None

def extract_price_and_images(html, base_url=None):
    if not html:
        return None, None, None
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True)
    found_raw = None
    found_val = None
    for m in PRICE_RE.finditer(text):
        found_raw = m.group(0)
        found_val = _clean_price_to_int(found_raw)
        if found_val is not None:
            break
    og = soup.select_one('meta[property="og:image"], meta[name="og:image"]')
    img = None
    if og and og.get("content"):
        img = urllib.parse.urljoin(base_url or "", og.get("content"))
    return found_raw, found_val, img

def extract_specs_table(html):
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    rows = []
    for sel in ("div#specification","div#specifications","section#specification"):
        sec = soup.select_one(sel)
        if sec:
            t = sec.find("table")
            if t:
                for tr in t.find_all("tr"):
                    cols = tr.find_all(["th","td"])
                    if len(cols) == 2:
                        k = cols[0].get_text(" ", strip=True)
                        v = cols[1].get_text(" ", strip=True)
                        if k and v:
                            rows.append((k, v))
                if rows:
                    return rows
    # fallback: scan all <tr>
    for tr in soup.find_all("tr"):
        cols = tr.find_all(["th","td"])
        if len(cols)==2:
            k = cols[0].get_text(" ", strip=True)
            v = cols[1].get_text(" ", strip=True)
            if not k or not v: continue
            if "variant" in k.lower(): continue
            rows.append((k, v))
    return rows

# ---------- UI palette(s) ----------
PALETTES = {
    "Neon Purple": {
        "bg":"#0b0710","panel":"rgba(255,255,255,0.02)","muted":"#cdbbf0",
        "accent1":"#a64dff","accent2":"#ff6ad0","accent3":"#2ef0d8"
    },
    "Solar Cyan": {
        "bg":"#06121a","panel":"rgba(255,255,255,0.02)","muted":"#bff3ff",
        "accent1":"#00e5d4","accent2":"#6be8ff","accent3":"#ff8bd0"
    }
}

BRANDS = ["Honda","Royal Enfield","TVS","Yamaha","Hero","Bajaj","KTM"]

# ---------- page template (visual wonder) ----------
TEMPLATE = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bike price Finder</title>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
<style>
:root{
  --bg: {{ palette.bg }};
  --panel: {{ palette.panel }};
  --muted: {{ palette.muted }};
  --accent1: {{ palette.accent1 }};
  --accent2: {{ palette.accent2 }};
  --accent3: {{ palette.accent3 }};
  --text: #f7f3ff;
}

/* Page background with animated radial nebula */
html,body{height:100%;margin:0;font-family:Inter, Poppins, system-ui, sans-serif;background:var(--bg);color:var(--text);-webkit-font-smoothing:antialiased;}
.body-wrap{min-height:100vh;padding:32px 36px;box-sizing:border-box;position:relative;overflow-x:hidden;}
/* animated glowing blobs */
.bg-blobs{
  position:fixed; inset:0; z-index:0; pointer-events:none;
  background:
    radial-gradient(800px 400px at 10% 20%, rgba(166,77,255,0.12), transparent 8%),
    radial-gradient(600px 300px at 85% 80%, rgba(255,105,192,0.10), transparent 6%),
    radial-gradient(400px 200px at 50% 60%, rgba(46,240,216,0.06), transparent 6%);
  filter:blur(28px) saturate(1.3);
  animation: floatBlobs 12s ease-in-out infinite;
}
@keyframes floatBlobs{0%{transform:translateY(0)}50%{transform:translateY(-18px)}100%{transform:translateY(0)}}

/* Layout */
.header{display:flex;gap:16px;align-items:center;z-index:5;position:relative;}
.logo{
  width:86px; height:86px; border-radius:18px; display:flex;align-items:center;justify-content:center;
  background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01)); box-shadow: 0 12px 36px rgba(0,0,0,0.6);
  border:1px solid rgba(255,255,255,0.03);
}
/* glowing badge stroke */
.logo svg{filter:drop-shadow(0 10px 30px rgba(166,77,255,0.18))}

/* Headline */
.title{font-weight:800;font-size:44px;color:var(--accent1);text-shadow:0 8px 30px rgba(0,0,0,0.6);}
.subtitle{color:var(--muted);margin-top:6px;font-size:15px}

/* Grid */
.container{display:grid;grid-template-columns:1fr 1fr;gap:28px;margin-top:22px;z-index:5;position:relative;}
.card{background:var(--panel);padding:20px;border-radius:14px;border:1px solid rgba(255,255,255,0.03);box-shadow:0 12px 40px rgba(0,0,0,0.6);}

/* Form */
.form label{display:block;color:var(--muted);font-weight:600;margin-bottom:8px;font-size:13px;}
.select, .input{width:100%;padding:12px 14px;border-radius:10px;background:transparent;border:1px solid rgba(255,255,255,0.04);color:var(--text);font-size:15px;box-sizing:border-box}
.select option{color:#000}
.form-actions{display:flex;gap:12px;margin-top:14px;align-items:center}
.btn{
  background:linear-gradient(90deg,var(--accent2),var(--accent1));
  color:#fff;padding:12px 18px;border-radius:12px;border:0;font-weight:700;cursor:pointer;
  box-shadow: 0 10px 30px rgba(255,105,192,0.08), inset 0 -2px 10px rgba(0,0,0,0.15);
  transition:transform .14s ease, box-shadow .14s ease;
}
.btn:hover{transform:translateY(-2px); box-shadow: 0 18px 46px rgba(0,0,0,0.6);}
.reset{background:transparent;border:0;color:var(--muted);text-decoration:underline;cursor:pointer}

/* Hero area */
.hero{display:flex;gap:18px;align-items:flex-start;padding:18px;border-radius:14px}
.hero-left{flex:0 0 260px}
.hero-left img{width:260px;border-radius:10px;box-shadow:0 18px 60px rgba(0,0,0,0.6);border:1px solid rgba(255,255,255,0.03)}
.hero-right{flex:1}
.model-title{font-weight:800;font-size:20px;color:var(--text)}
.price{font-weight:900;font-size:32px;color:var(--accent1);margin-top:8px;text-shadow:0 18px 40px rgba(0,0,0,0.6)}
.raw{color:var(--muted);margin-top:10px}
.note{margin-top:12px;padding:12px;border-radius:10px;background:linear-gradient(90deg, rgba(255,255,255,0.01), rgba(0,0,0,0.05));color:var(--muted)}

/* Specs area: two panels */
.specs{grid-column:1 / span 2;display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:20px}
.spec-card{background:linear-gradient(180deg, rgba(255,255,255,0.01), rgba(0,0,0,0.02));padding:14px;border-radius:12px;border:1px solid rgba(255,255,255,0.02)}
.spec-table{width:100%;border-collapse:collapse;color:var(--text);font-size:15px}
.spec-table th{color:var(--muted);text-align:left;padding:8px 10px}
.spec-table td{padding:10px;border-top:1px solid rgba(255,255,255,0.02)}
/* CSS counter for serial numbers */
.spec-table tbody{counter-reset:spec-counter}
.spec-table tbody tr td.spec-no::before{counter-increment:spec-counter; content:counter(spec-counter); display:inline-block; width:28px; color:var(--muted); font-weight:700; margin-right:10px}

/* debug */
.debug{grid-column:1/-1;margin-top:18px;color:var(--muted);font-family:monospace;white-space:pre-wrap}

/* responsive */
@media (max-width:980px){
  .container{grid-template-columns:1fr}
  .specs{grid-template-columns:1fr}
  .hero-left img{width:180px}
}
</style>
</head>
<body>
  <div class="body-wrap">
    <div class="bg-blobs" aria-hidden="true"></div>

    <div class="header">
      <div class="logo" aria-hidden="true">
        <!-- Inline SVG neon logo -->
        <svg viewBox="0 0 120 120" width="66" height="66" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="{{ palette.accent2 }}"/><stop offset="1" stop-color="{{ palette.accent1 }}"/></linearGradient>
            <filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>
          </defs>
          <rect width="120" height="120" rx="16" fill="#05030a"/>
          <g filter="url(#glow)">
            <path d="M14 68c22-30 48-34 76-26" stroke="url(#g)" stroke-width="6" stroke-linecap="round" fill="none"/>
            <circle cx="36" cy="92" r="10" stroke="{{ palette.accent3 }}" stroke-width="4" fill="none"/>
            <circle cx="96" cy="92" r="10" stroke="{{ palette.accent2 }}" stroke-width="4" fill="none"/>
          </g>
        </svg>
      </div>
      <div>
        <div class="title">Bike Price Finder</div>
        <div class="subtitle">Beautiful neon UI ± smooth interactions. Heuristic scraping for quick price & specs lookup.</div>
      </div>
    </div>

    <div class="container">
      <div class="card form">
        <form method="post" action="/search">
          <label for="palette">Palette</label>
          {% if palettes|length > 1 %}
            <select class="select" id="palette" name="palette" onchange="document.getElementById('palette_changed').value='1'; this.form.submit()">
              {% for key in palettes %}
                <option value="{{key}}" {% if key==selected_palette %}selected{% endif %}>{{key}}</option>
              {% endfor %}
            </select>
          {% else %}
            <input type="hidden" name="palette" value="{{ selected_palette }}">
          {% endif %}
          <input type="hidden" id="palette_changed" name="palette_changed" value="0">

          <label for="brand" style="margin-top:12px">Brand</label>
          <select id="brand" name="brand" class="select" onchange="populateModels()">
            {% for b in brands %}<option value="{{b}}" {% if b==form.brand %}selected{% endif %}>{{b}}</option>{% endfor %}
          </select>

          <label for="model" style="margin-top:12px">Model</label>
          <select id="model" name="model" class="select">
            {% for m in models %}<option value="{{m}}" {% if m==form.model %}selected{% endif %}>{{m}}</option>{% endfor %}
          </select>

          <label for="city" style="margin-top:12px">City (optional)</label>
          <input id="city" name="city" class="input" placeholder="e.g. Pune" value="{{ form.city|default('') }}">

          <div class="form-actions">
            <button class="btn" type="submit">Get Details</button>
            <button class="reset" type="button" onclick="document.querySelector('form').reset();">Reset</button>
          </div>
        </form>
      </div>

      <div class="card hero">
        <div class="hero-left">
          {% if result.image %}
            <img src="{{ result.image }}" alt="model image">
          {% else %}
            <img src="https://via.placeholder.com/260x180?text=No+Image" alt="no image">
          {% endif %}
        </div>
        <div class="hero-right">
          <div class="model-title">{{ result.brand }}{% if result.model %} — {{ result.model }}{% endif %}</div>
          <div class="price">
            {% if result.found_price_int %}₹ {{ "{:,}".format(result.found_price_int) }}
            {% elif result.found_price_raw %}{{ result.found_price_raw }}
            {% else %}—{% endif %}
          </div>
          <div class="raw">Raw: {{ result.found_price_raw or '—' }}</div>
          {% if result.product_url %}<a href="{{ result.product_url }}" target="_blank" style="color:var(--accent3); margin-top:10px; display:inline-block;">Open product page</a>{% endif %}
          <div class="note">Note: Results come from quick heuristics scraping bikedekho. Page layout changes may break parsing.</div>
        </div>
      </div>

      <!-- specs -->
      <div class="specs">
        <div class="spec-card">
          <strong style="color:var(--muted)">Specifications</strong>
          {% if specs %}
            <table class="spec-table" role="table" aria-label="Specifications">
              <thead><tr><th style="width:60px">No.</th><th>Spec</th><th>Value</th></tr></thead>
              <tbody>
                {% for pair in specs %}
                <tr>
                  <td class="spec-no">{{ loop.index }}</td>
                  <td>{{ pair[0] }}</td>
                  <td>{{ pair[1] }}</td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          {% else %}
            <div style="color:var(--muted); margin-top:8px">No structured specs detected for this product page.</div>
          {% endif %}
        </div>

        <div class="spec-card">
          <strong style="color:var(--muted)">Result JSON</strong>
          <div style="font-family:monospace;color:var(--muted);margin-top:12px;white-space:pre-wrap;">{{ result|tojson(indent=2) }}</div>
        </div>
      </div>

      <div class="debug">{{ debug_message or "" }}</div>
    </div>
  </div>

<script>
  const brandToModels = {
    "Honda":["Activa 125","Activa 6G","Activa e","Hornet 2.0","NX200","NX500"],
    "Royal Enfield":["Continental GT 650","Classic 350","Guerrilla 450","Himalayan 450","Hunter 350"],
    "TVS":["Apache RTR 160","Jupiter 125","Raider","Ronin","Star City Plus"],
    "Yamaha":["FZ X","Fasino 125 Fi Hybrid","FZ-Rave","FZS-FI V3"],
    "Hero":["Glamour","Xtreme 250R","Xtreme 160R","Xtreme 160R 4V","Xtreme 125R"],
    "Bajaj":["Pulsar NS 125","Pulsar NS160","Pulsar NS200","Platina 100","Platina 110"],
    "KTM":["160 Duke","200 Duke","250 Adventure","RC 200","RC 390"]
  };
  function populateModels(){
    const brand = document.getElementById('brand').value;
    const list = brandToModels[brand] || [];
    const modelEl = document.getElementById('model');
    modelEl.innerHTML = '';
    for(const m of list){
      const opt = document.createElement('option'); opt.value = m; opt.text = m; modelEl.appendChild(opt);
    }
  }
  window.addEventListener('load', function(){ if(document.getElementById('model').options.length===0) populateModels(); });
</script>
</body>
</html>
"""

# ---------- routes ----------
@app.route("/", methods=["GET"])
def index():
    selected_palette = request.args.get("palette", list(PALETTES.keys())[0])
    palette = PALETTES.get(selected_palette, list(PALETTES.values())[0])
    result = {"brand": "", "model": "", "city": "", "product_url": "", "found_price_raw": None, "found_price_int": None, "image": None}
    return render_template_string(TEMPLATE,
                                  palettes=list(PALETTES.keys()),
                                  selected_palette=selected_palette,
                                  palette=palette,
                                  brands=BRANDS,
                                  models=[],
                                  form={},
                                  result=result,
                                  specs=[],
                                  debug_message="")

@app.route("/search", methods=["POST"])
def search():
    selected_palette = request.form.get("palette", list(PALETTES.keys())[0])
    palette = PALETTES.get(selected_palette, list(PALETTES.values())[0])
    brand = request.form.get("brand", "").strip() or "Honda"
    model = request.form.get("model", "").strip() or ""
    city = request.form.get("city", "").strip() or ""

    # build product url heuristically
    slug_brand = brand.lower().replace(" ", "-")
    slug_model = model.lower().replace(" ", "-").replace(".", "").replace("/", "-")
    product_url = f"https://www.bikedekho.com/{slug_brand}/{slug_model}"

    html = fetch_page(product_url)
    price_raw, price_int, img = extract_price_and_images(html, base_url=product_url) if html else (None, None, None)
    specs = extract_specs_table(html) if html else []

    result = {"brand": brand, "model": model, "city": city, "product_url": product_url,
              "found_price_raw": price_raw, "found_price_int": price_int, "image": img}

    models = []
    if brand in BRANDS:
        models = {
            "Honda":["Activa 125","Activa 6G","Activa e","Hornet 2.0","NX200","NX500"],
            "Royal Enfield":["Continental GT 650","Classic 350","Guerrilla 450","Himalayan 450","Hunter 350"],
            "TVS":["Apache RTR 160","Jupiter 125","Raider","Ronin","Star City Plus"],
            "Yamaha":["FZ X","Fasino 125 Fi Hybrid","FZ-Rave","FZS-FI V3"],
            "Hero":["Glamour","Xtreme 250R","Xtreme 160R","Xtreme 160R 4V","Xtreme 125R"],
            "Bajaj":["Pulsar NS 125","Pulsar NS160","Pulsar NS200","Platina 100","Platina 110"],
            "KTM":["160 Duke","200 Duke","250 Adventure","RC 200","RC 390"]
        }[brand]

    debug_message = ""
    if not html:
        debug_message = "Warning: Could not fetch product page. Check network or try another model."

    return render_template_string(TEMPLATE,
                                  palettes=list(PALETTES.keys()),
                                  selected_palette=selected_palette,
                                  palette=palette,
                                  brands=BRANDS,
                                  models=models,
                                  form={"brand":brand,"model":model,"city":city},
                                  result=result,
                                  specs=specs,
                                  debug_message=debug_message)

if __name__ == "__main__":
    app.run(debug=True, port=5000)

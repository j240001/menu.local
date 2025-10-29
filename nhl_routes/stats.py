# nhl_routes/stats.py
from flask import make_response, request
import requests, textwrap, os, json
from . import nhl_bp
from utils import TH1, TH2, TH3, alpha

# Local cache (written by /nhl/update-stats)
STATS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "nhl_stats_2025_26.json")

@nhl_bp.route("/nhl/stats")
def nhl_stats_html():
    url = "https://api-web.nhle.com/v1/skater-stats-leaders/current"
    limit = int(request.args.get("limit", 15))

    # --- Minimal change: try local cache first, else fall back to API ---
    data = None
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            data = None

    if data is None:
        try:
            # keep original behavior; API may ignore limit param, we still slice below
            data = requests.get(url, params={"limit": limit}, timeout=8).json()
        except Exception as e:
            return f"<pre>Error fetching NHL data: {e}</pre>"

    sections = [("points", "POINTS"), ("goals", "GOALS"), ("assists", "ASSISTS")]
    out = []

    for key, title in sections:
        leaders = data.get(key, []) or []
        out.append(title)
        out.append("-" * len(title))
        for p in leaders[:limit]:  # <-- limit still applied exactly as before
            first = p.get("firstName", {}).get("default", "")
            last = p.get("lastName", {}).get("default", "")
            team = p.get("teamAbbrev", "")
            val = p.get("value", "?")
            name = f"{first} {last}".strip()
            if team == "EDM":
                line = f"<span style='color:{TH2};font-weight:bold'>{name} ({team})  {val}</span>"
            else:
                line = f"{name} ({team})  {val}"
            out.append(line)
        out.append("")

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@600&display=swap">
<style>
  body {{
    background:{TH3};
    color:#eee;
    font-family:'Rajdhani',sans-serif;
    margin:0;
    padding:1em;
    text-align:left;
    min-height:100vh;
    overflow-y:auto;
    -webkit-overflow-scrolling:touch;
  }}

  /* --- NAVIGATION --- */
  .nav {{
    text-align:left;
    margin-bottom:1.2em;
  }}
  .menu-btn {{
    background:none;
    color:{TH1};
    text-decoration:none;
    font-weight:bold;
    font-size:clamp(22px,4vw,26px);
    display:inline-block;
    margin-bottom:0.5em;
  }}
  .submenu {{
    display:flex;
    justify-content:flex-start;
    flex-wrap:wrap;
    gap:0.6em;
  }}
  .submenu a {{
    background:{alpha(TH1,0.13)};
    color:{TH1};
    padding:0.3em 0.8em;
    border-radius:8px;
    text-decoration:none;
    font-weight:bold;
    font-size:clamp(17px,3.3vw,19px);
    transition:background 0.2s ease,color 0.2s ease;
  }}
  .submenu a:hover {{
    background:{alpha(TH2,0.25)};
    color:{TH2};
  }}
  .submenu a.active {{
    background:{TH2};
    color:#000;
  }}

  pre {{
    font-size:clamp(15px,2.5vw,18px);
    line-height:1.5em;
    white-space:pre-wrap;
    word-break:break-word;
  }}
  select {{
    padding:0.3em;
    border-radius:6px;
    font-size:1em;
  }}
</style>
</head>
<body>

  <div class="nav">
    <a href="/" class="menu-btn">← MENU</a>
    <div class="submenu">
      <a href="/nhl" class="{'active' if request.path == '/nhl' else ''}">SCORES</a>
      <a href="/nhl/standings" class="{'active' if request.path == '/nhl/standings' else ''}">STANDINGS</a>
      <a href="/nhl/stats" class="{'active' if request.path == '/nhl/stats' else ''}">STATS</a>
      <a href="/nhl/more" class="{'active' if request.path == '/nhl/more' else ''}">MORE</a>
    </div>
  </div>

  <form method="get" action="/nhl/stats" style="margin-bottom:1em;">
    <label for="limit" style="color:{TH1};font-weight:bold;">Show top:</label>
    <select name="limit" id="limit" onchange="this.form.submit()">
      <option value="15" {'selected' if limit==15 else ''}>15</option>
      <option value="25" {'selected' if limit==25 else ''}>25</option>
      <option value="50" {'selected' if limit==50 else ''}>50</option>
      <option value="100" {'selected' if limit==100 else ''}>100</option>
    </select>
  </form>

  <pre>{textwrap.dedent(chr(10).join(out))}</pre>

</body>
</html>"""

    response = make_response(html)
    response.headers["Cache-Control"] = "public, max-age=80"
    response.headers["Pragma"] = "cache"
    response.headers["Expires"] = "120"
    return response

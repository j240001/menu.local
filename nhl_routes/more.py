from flask import make_response, request
from . import nhl_bp
from utils import TH1, TH2, TH3, alpha

@nhl_bp.route("/nhl/more")
def nhl_more_html():
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@600&display=swap">
<style>
  body {{
    background:{TH3};
    color:#eee;
    font-family:'Rajdhani',sans-serif;
    margin:0;
    padding:1em;
    text-align:left;
  }}
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
  h2 {{
    color:{TH1};
  }}
  ul {{
    list-style:none;
    padding-left:0;
  }}
  li {{
    margin-bottom:0.5em;
  }}
  a.menu-item {{
    color:{TH2};
    font-weight:bold;
    text-decoration:none;
    font-size:clamp(18px,3vw,20px);
  }}
  a.menu-item:hover {{
    text-decoration:underline;
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

  <h2> ----------- </h2>
  <ul>
    <li><a href="/nhl/results" class="menu-item">Game Results – by Month</a></li>
    <li><a href="/nhl/updater" class="menu-item">Updater Control Panel</a></li>
  </ul>

</body>
</html>"""
    return make_response(html)

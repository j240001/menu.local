# nhl_routes/results_menu.py
from flask import make_response
from . import nhl_bp
from utils import TH1, TH2, TH3, alpha

@nhl_bp.route("/nhl/results")
def nhl_results_menu():
    months = [
        ("October", "/nhl/results/oct2025"),
        ("November", "/nhl/results/nov2025"),
        ("December", "/nhl/results/dec2025"),
        ("January", "/nhl/results/jan2026"),
        ("February", "/nhl/results/feb2026"),
        ("March", "/nhl/results/mar2026"),
        ("April", "/nhl/results/apr2026"),
    ]

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
  }}
  a.back {{
    color:{TH1};
    font-weight:bold;
    text-decoration:none;
    display:inline-block;
    margin-bottom:1em;
    font-size:clamp(20px,3.5vw,24px);
  }}
  h2 {{
    color:{TH1};
    margin:0.3em 0 0.6em;
  }}
  ul {{
    list-style:none;
    padding:0;
  }}
  li {{
    margin:0.4em 0;
  }}
  a.month {{
    color:{TH2};
    font-weight:bold;
    text-decoration:none;
    font-size:clamp(18px,3vw,20px);
  }}
  a.month:hover {{
    text-decoration:underline;
  }}
</style>
</head>
<body>
<a href="/nhl/more" class="back">← Back</a>
<h2>2025–26 Season</h2>
<ul>
"""
    for name, link in months:
        html += f'<li><a href="{link}" class="month">{name}</a></li>\n'

    html += "</ul></body></html>"
    return make_response(html)

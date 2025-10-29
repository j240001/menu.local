# nhl_routes/months/jan2026.py
from flask import make_response
import os, datetime
from .. import nhl_bp
from utils import TH1, TH2, TH3, alpha

@nhl_bp.route("/nhl/results/jan2026")
def nhl_results_jan2026():
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_file = os.path.join(base_path, "espn_games_2025_26.txt")

    games = []
    if os.path.exists(data_file):
        with open(data_file) as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 6 or "@" not in parts:
                    continue
                try:
                    date_str = parts[0]
                    date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                    if date.month != 1 or date.year != 2026:
                        continue
                    away, away_score = parts[1], parts[2]
                    home, home_score = parts[parts.index("@") + 1], parts[parts.index("@") + 2]
                    note = parts[parts.index("@") + 3] if len(parts) > parts.index("@") + 3 else ""
                    games.append((date, away, away_score, home, home_score, note.upper()))
                except Exception:
                    continue

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
    margin-top:0.3em;
  }}
  table {{
    width:100%;
    border-collapse:collapse;
    font-size:clamp(16px,2.6vw,17px);
  }}
  th, td {{
    border-bottom:1px solid #333;
    padding:0.25em 0.4em;
  }}
  th {{
    background:{alpha(TH1,0.25)};
    color:#000;
    text-align:left;
  }}
  tr:hover td {{
    background:{alpha(TH1,0.1)};
  }}
</style>
</head>
<body>

<a href="/nhl/results" class="back">← Back</a>
<h2>January 2026 Games</h2>
"""

    if not games:
        html += "<p>No data for this month.</p>"
    else:
        html += "<table><tr><th>Date</th><th>Away</th><th>Score</th><th>Home</th><th>Note</th></tr>"
        for (date, away, a_s, home, h_s, note) in sorted(games):
            html += f"<tr><td>{date.strftime('%b %d')}</td><td>{away}</td><td>{a_s} - {h_s}</td><td>{home}</td><td>{note}</td></tr>"
        html += "</table>"

    html += "</body></html>"
    return make_response(html)

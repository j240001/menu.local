# nhl_routes/months/oct2025.py
from flask import make_response
import os, datetime
from .. import nhl_bp
from utils import TH1, TH2, TH3, alpha

@nhl_bp.route("/nhl/results/oct2025")
def nhl_results_oct2025():
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_file = os.path.join(base_path, "espn_games_2025_26.txt")

    games = []
    if os.path.exists(data_file):
        with open(data_file) as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 7 or "@" not in parts:
                    continue
                try:
                    # Format: ID DATE AWAY SCORE @ HOME SCORE [NOTE]
                    date_str = parts[1]
                    date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                    if date.month != 10 or date.year != 2025:
                        continue
                    away, away_score = parts[2], parts[3]
                    home, home_score = parts[parts.index("@") + 1], parts[parts.index("@") + 2]
                    note = parts[-1].upper() if parts[-1] in ("OT", "SO") else ""
                    games.append((date, away, away_score, home, home_score, note))
                except Exception:
                    continue

    # --- HTML + CSS ---
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
    text-align:left;
  }}
  th {{
    background:{alpha(TH1,0.25)};
    color:{TH2}; /* orange header text */
    text-align:left;
  }}
  tr:hover td {{
    background:{alpha(TH1,0.1)};
  }}
</style>
</head>
<body>

<a href="/nhl/results" class="back">← Back</a>
<h2>October 2025 Games</h2>
"""

    # --- Table output ---
    if not games:
        html += "<p>No data for this month.</p>"
    else:
        html += "<table>"
        html += "<tr><th>Date</th><th>Away</th><th>Score</th><th>Home</th><th>Note</th></tr>"
        for (date, away, a_s, home, h_s, note) in sorted(games):
            highlight = f" style='color:{TH2};font-weight:bold;'" if ('EDM' in (away, home)) else ""
            html += (
                f"<tr{highlight}>"
                f"<td>{date.strftime('%b %d')}</td>"
                f"<td>{away}</td>"
                f"<td>{a_s} - {h_s}</td>"
                f"<td>{home}</td>"
                f"<td>{note}</td>"
                f"</tr>"
            )
        html += "</table>"

    html += "</body></html>"
    return make_response(html)

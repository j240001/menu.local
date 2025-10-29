from flask import make_response, request
import datetime, zoneinfo
from . import nhl_bp
from utils import TH1, TH2, TH3, alpha

@nhl_bp.route("/nhl/standings")
def nhl_standings_html():
    tz = zoneinfo.ZoneInfo("America/Edmonton")
    INPUT_FILE = "espn_games_2025_26.txt"

    def update_team(team, gf, ga, result):
        if team not in teams:
            teams[team] = {
                "W": 0, "L": 0, "OTL": 0,
                "GF": 0, "GA": 0, "PTS": 0,
                "GP": 0, "RW": 0
            }
        t = teams[team]
        t["GP"] += 1
        t["GF"] += gf
        t["GA"] += ga
        if result == "win":
            t["W"] += 1
            t["PTS"] += 2
        elif result == "loss":
            t["L"] += 1
        elif result == "otl":
            t["OTL"] += 1
            t["PTS"] += 1

    teams = {}
    try:
        with open(INPUT_FILE) as f:
            lines = [ln.strip() for ln in f if ln.strip()]
    except FileNotFoundError:
        return f"<pre>File '{INPUT_FILE}' not found.</pre>"

    for line in lines:
        parts = line.split()
        if len(parts) < 6 or "@" not in parts:
            continue
        at_index = parts.index("@")
        try:
            # Works for both old and new formats by anchoring on "@"
            away_score = int(parts[at_index - 1])
            away_abbr  = parts[at_index - 2]
            home_abbr  = parts[at_index + 1]
            home_score = int(parts[at_index + 2])
            note = parts[at_index + 3].upper() if len(parts) > at_index + 3 else ""
        except Exception:
            if "@" not in parts or len(parts) < 6:
                continue
 

        # --- Determine winners / losers and update stats ---
        if home_score > away_score:
            if note in ("OT", "SO"):
                # Home wins in OT/SO
                update_team(home_abbr, home_score, away_score, "win")
                update_team(away_abbr, away_score, home_score, "otl")
            else:
                # Home wins in regulation
                update_team(home_abbr, home_score, away_score, "win")
                update_team(away_abbr, away_score, home_score, "loss")
                teams[home_abbr]["RW"] += 1  # ✅ Regulation win

        elif away_score > home_score:
            if note in ("OT", "SO"):
                # Away wins in OT/SO
                update_team(away_abbr, away_score, home_score, "win")
                update_team(home_abbr, home_score, away_score, "otl")
            else:
                # Away wins in regulation
                update_team(away_abbr, away_score, home_score, "win")
                update_team(home_abbr, home_score, away_score, "loss")
                teams[away_abbr]["RW"] += 1  # ✅ Regulation win

    # --- Sort standings by points, then wins, then goal differential ---
    sorted_teams = sorted(
        teams.items(),
        key=lambda kv: (-kv[1]["PTS"], -kv[1]["W"], -(kv[1]["GF"] - kv[1]["GA"]))
    )

    now = datetime.datetime.now(tz).strftime("%-I:%M %p %b %d, %Y")

    # --- Generate HTML rows ---
    rows = "\n".join(
        (
            f"<tr style='color:{TH2};'>" if team == 'EDM' else "<tr>"
        ) +
        f"<td>{team}</td>"
        f"<td>{st['GP']}</td>"
        f"<td>{st['W']}</td>"
        f"<td>{st['L']}</td>"
        f"<td>{st['OTL']}</td>"
        f"<td>{st['RW']}</td>"
        f"<td>{st['GF']}</td>"
        f"<td>{st['GA']}</td>"
        f"<td>{st['PTS']}</td></tr>"
        for team, st in sorted_teams
    )

    # --- Build full HTML ---
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

  /* --- TABLE CONTAINER (COMPACT LAYOUT) --- */
  .table-container {{
    width:100%;
    overflow-x:auto;
    -webkit-overflow-scrolling:touch;
    text-align:left;
  }}

  table {{
    border-collapse:collapse;
    font-size:clamp(16px,2.6vw,15px);
    min-width:550px;
    margin-left:0;
    margin-right:auto;
    table-layout:auto;
  }}

  th, td {{
    border-bottom:1px solid #333;
    padding:0.2em 0.4em;
    white-space:nowrap;
    text-align:left;
  }}

  th {{
    background:{alpha(TH1,0.3)};
    color: {TH2};
    position:sticky;
    top:0;
    text-align:left;
    cursor:pointer;
    user-select:none;
    font-weight: bold;
    letter-spacing: 0.04em;
  }}

  tr:hover td {{
    background:{alpha(TH1,0.13)};
  }}

  caption {{
    caption-side:top;
    color:{TH1};
    margin-bottom:0.8em;
    font-size:1.3em;
    font-weight:bold;
    text-align:center;
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



  <div class="table-container">
    <table>
      <tr>
        <th>Team</th>
        <th>GP</th>
        <th>W</th>
        <th>L</th>
        <th>OTL</th>
        <th>RW</th>
        <th>GF</th>
        <th>GA</th>
        <th>PTS</th>
      </tr>
      {rows}
    </table>
  </div>

<script>


/* --- COLUMN SORTING --- */
document.addEventListener("DOMContentLoaded", () => {{
  const table = document.querySelector("table");
  const headers = table.querySelectorAll("th");
  let sortIndex = -1;
  let ascending = true;

  headers.forEach((th, i) => {{
    const isNumeric = i !== 0; // only Team column is text
    th.addEventListener("click", () => {{
      const rows = Array.from(table.querySelectorAll("tr")).slice(1);
      if (sortIndex === i) ascending = !ascending; else ascending = true;
      sortIndex = i;

      rows.sort((a, b) => {{
        const aText = a.children[i].innerText.trim();
        const bText = b.children[i].innerText.trim();
        if (isNumeric) {{
          const aNum = parseFloat(aText) || 0;
          const bNum = parseFloat(bText) || 0;
          return ascending ? aNum - bNum : bNum - aNum;
        }} else {{
          return ascending
            ? aText.localeCompare(bText)
            : bText.localeCompare(aText);
        }}
      }});

      rows.forEach(r => table.appendChild(r));

      headers.forEach(h => h.style.textDecoration = "");
      th.style.textDecoration = ascending ? "underline" : "overline";
    }});
  }});
}});
</script>
</body>
</html>"""

    response = make_response(html)
    response.headers["Cache-Control"] = "public, max-age=80"
    response.headers["Pragma"] = "cache"
    response.headers["Expires"] = "120"
    return response

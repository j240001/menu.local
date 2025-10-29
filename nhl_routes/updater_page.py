# nhl_routes/updater_page.py
from flask import make_response
import os, datetime
from . import nhl_bp
from utils import TH1, TH2, TH3, alpha

# --- Local data file paths ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_FILE = os.path.join(BASE_DIR, "espn_games_2025_26.txt")
SCHEDULE_FILE = os.path.join(BASE_DIR, "espn_schedule_2025_26.txt")
ROSTERS_FILE = os.path.join(BASE_DIR, "nhl_rosters_2025_26.json")
STATS_FILE = os.path.join(BASE_DIR, "nhl_stats_2025_26.json")

def fmt_time(path):
    """Format file modified time (or show 'Never')."""
    try:
        ts = os.path.getmtime(path)
        dt = datetime.datetime.fromtimestamp(ts)
        return dt.strftime("%b %d, %Y %I:%M %p")
    except Exception:
        return "Never"

@nhl_bp.route("/nhl/updater")
def nhl_updater_panel():
    # --- Grab timestamps for each file ---
    results_time = fmt_time(RESULTS_FILE)
    schedule_time = fmt_time(SCHEDULE_FILE)
    rosters_time = fmt_time(ROSTERS_FILE)
    stats_time = fmt_time(STATS_FILE)

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
  h2 {{ color:{TH1}; margin-top:0.3em; }}
  .row {{
    display:flex;
    align-items:center;
    flex-wrap:wrap;
    gap:0.8em;
    margin-bottom:0.9em;
  }}
  button {{
    background:{TH1};
    color:#000;
    font-weight:bold;
    border:none;
    border-radius:8px;
    padding:0.6em 1.2em;
    font-size:clamp(16px,2.5vw,18px);
    cursor:pointer;
    transition:background 0.2s ease;
  }}
  button:hover {{ background:{TH2}; }}
  .stamp {{
    color:{TH2};
    font-size:clamp(14px,2.2vw,16px);
    opacity:0.8;
  }}
  #msg {{ color:{TH2}; margin-top:1em; }}
</style>
<script>
async function runUpdate(endpoint, label) {{
  const msg = document.getElementById('msg');
  msg.textContent = "Updating " + label + "...";
  try {{
    const r = await fetch(endpoint, {{ method: "POST" }});
    const j = await r.json();
    msg.textContent = j.message || "Done!";
    setTimeout(() => msg.textContent = "", 4000);
    setTimeout(() => window.location.reload(), 1000);  // refresh to update timestamps
  }} catch (e) {{
    msg.textContent = "Error updating " + label;
  }}
}}
</script>
</head>
<body>

<a href="/nhl/more" class="back">← Back</a>
<h2>NHL Data Updater</h2>

<div class="row">
  <button onclick="runUpdate('/nhl/update-results','Completed Games')">Update Completed Games</button>
  <span class="stamp">Last updated: {results_time}</span>
</div>

<div class="row">
  <button onclick="runUpdate('/nhl/update-schedule','Schedule')">Update Schedule</button>
  <span class="stamp">Last updated: {schedule_time}</span>
</div>

<div class="row">
  <button onclick="runUpdate('/nhl/update-rosters','Rosters')">Update Rosters</button>
  <span class="stamp">Last updated: {rosters_time}</span>
</div>

<div class="row">
  <button onclick="runUpdate('/nhl/rebuild-standings','Standings')">Rebuild Standings</button>
  <span class="stamp">Uses local data</span>
</div>

<div class="row">
  <button onclick="runUpdate('/nhl/update-stats','Stats')">Update Stats</button>
  <span class="stamp">Last updated: {stats_time}</span>
</div>

<div id="msg"></div>

</body></html>"""
    return make_response(html)

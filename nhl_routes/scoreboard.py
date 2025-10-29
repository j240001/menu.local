# nhl_routes/scoreboard.py
from flask import make_response, request
import datetime, requests, zoneinfo, os
from . import nhl_bp
from utils import TH1, TH2, TH3, alpha

@nhl_bp.route("/nhl")
def nhl_scoreboard_html():
    tz = zoneinfo.ZoneInfo("America/Edmonton")
    base_url = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"

    # --- Local schedule file path (in main folder) ---
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    SCHEDULE_FILE = os.path.join(BASE_DIR, "espn_schedule_2025_26.txt")

    # ---------------- Helper: read schedule file ----------------
    def get_schedule_for_day(day):
        """Return list of (away, home, time_text) for a given date from local file."""
        datestr = day.strftime("%Y%m%d")
        games = []
        try:
            with open(SCHEDULE_FILE) as f:
                for line in f:
                    if line.startswith(datestr):
                        parts = line.strip().split()
                        # expected: YYYYMMDD AWAY @ HOME [time...]
                        if len(parts) >= 4 and parts[2] == "@":
                            # join everything after HOME so "7:30 PM" stays intact
                            time_field = " ".join(parts[4:]) if len(parts) >= 5 else "TBD"
                            games.append((parts[1], parts[3], time_field))  # (away, home, time_text)
        except FileNotFoundError:
            print("[Scoreboard] Schedule file not found:", SCHEDULE_FILE)
        return games

    # ---------------- Helper: fetch today's games (with scores) ----------------
    def get_todays_games(day):
        """Fetch current live/final scores for today only."""
        datestr = day.strftime("%Y%m%d")
        try:
            r = requests.get(f"{base_url}?dates={datestr}", timeout=8)
            r.raise_for_status()
            data = r.json()
        except Exception:
            return []

        games = []
        for ev in data.get("events", []):
            if ev.get("season", {}).get("type") != 2:
                continue

            comp = ev.get("competitions", [{}])[0]
            teams = comp.get("competitors", [])
            if len(teams) < 2:
                continue

            home = next((t for t in teams if t.get("homeAway") == "home"), {})
            away = next((t for t in teams if t.get("homeAway") == "away"), {})
            h_name = home.get("team", {}).get("abbreviation", "???")
            a_name = away.get("team", {}).get("abbreviation", "???")
            h_score = str(home.get("score", "0"))
            a_score = str(away.get("score", "0"))

            st = ev.get("status", {}).get("type", {})
            desc = (st.get("description") or "").lower()
            short = (st.get("shortDetail") or "").lower()
            detail = (st.get("detail") or "").lower()
            lower = f"{desc} {short} {detail}"

            comp_status = comp.get("status", {}).get("type", {})
            comp_desc = " ".join(
                str(comp_status.get(k, "")).lower()
                for k in ("shortDetail", "detail", "description")
            )
            lower_all = f"{lower} {comp_desc}"

            try:
                raw_date = ev.get("date", "")
                dt_local = None
                if raw_date:
                    dt_utc = datetime.datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                    dt_local = dt_utc.astimezone(tz)

                if "final" in lower_all:
                    right = st.get("shortDetail") or comp_status.get("shortDetail") or "FINAL"
                    state = "final"
                elif any(word in lower_all for word in ["in progress", "live", "1st", "2nd", "3rd", "ot", "so"]):
                    right = (
                        comp_status.get("shortDetail")
                        or comp_status.get("detail")
                        or st.get("shortDetail")
                        or st.get("detail")
                        or "LIVE"
                    )
                    state = "live"
                else:
                    if dt_local:
                        # include minutes + AM/PM + MST
                        right = dt_local.strftime("%-I:%M %p  ")
                    else:
                        right = "TBD"
                    state = "upcoming"
            except Exception:
                right, state = "TBD", "upcoming"

            games.append((a_name, a_score, h_name, h_score, right, state))
        return games

    # ---------------- HTML header ----------------
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
  h3 {{
    color:{TH1};
    margin:0.8em 0 0.4em;
  }}
  .gamerow {{
    display:inline-block;
    width:100%;
    font-size:clamp(20px,3vw,22px);
    line-height:1.6em;
  }}
  .rev {{
    vertical-align:middle;
    margin-right:.35em;
    transform:scale(1.0);
    cursor:pointer;
  }}
  .gamerow .reveal {{ color:{TH3}; transition:color .15s ease; }}
  .gamerow .rev:checked ~ .reveal {{ color:#eee; }}
</style>
</head>
<body>

  <!-- Unified Navigation -->
  <div class="nav">
    <a href="/" class="menu-btn">← MENU</a>
    <div class="submenu">
      <a href="/nhl" class="{'active' if request.path == '/nhl' else ''}">SCORES</a>
      <a href="/nhl/standings" class="{'active' if request.path == '/nhl/standings' else ''}">STANDINGS</a>
      <a href="/nhl/stats" class="{'active' if request.path == '/nhl/stats' else ''}">STATS</a>
      <a href="/nhl/more" class="{'active' if request.path == '/nhl/more' else ''}">MORE</a>
    </div>
</div>

  </div>
"""

    # ---------------- Build scoreboard ----------------
    today = datetime.date.today()
    now = datetime.datetime.now(tz).strftime("%-I:%M %p")
    days_to_show = 40
    gid = 0

    for offset in range(days_to_show):
        day = today + datetime.timedelta(days=offset)
        label = day.strftime("%a, %b %-d")

        # today uses live data, others local
        if offset == 0:
            games = get_todays_games(day)
        else:
            # include saved time text from schedule file
            games = [(a, "", h, "", t, "upcoming") for (a, h, t) in get_schedule_for_day(day)]

        html += f"<h3>{label}</h3>\n"
        if not games:
            html += "<div class='gamerow'>No Games Scheduled</div>\n"
            continue

        for (a, a_s, h, h_s, status, state) in games:
            gid += 1
            cid = f"rev_{a}_{h}_{gid}"
            row_style = f"color:{TH2};" if (a == 'EDM' or h == 'EDM') else ""

            if state in ("live", "final"):
                line = (
                    f'<div class="gamerow" style="{row_style}">'
                    f'<input id="{cid}" class="rev" type="checkbox">'
                    f'<label for="{cid}">{a} </label>'
                    f'<span class="reveal">{a_s}</span>'
                    f' @ {h} '
                    f'<span class="reveal">{h_s}</span>'
                    f'  -  <span class="reveal">{status}</span>'
                    f'</div>'
                )
            else:
                # append MST if we have a concrete time
                time_text = status.strip()
                if time_text and time_text.upper() != "TBD" and not time_text.upper().endswith(" "):
                    time_text = f"{time_text}  "
                line = f"<div class='gamerow' style='{row_style}'>{a} @ {h}  -  {time_text}</div>"
            html += line + "\n"

    html += f"""
  <div style="text-align:center;font-size:0.8em;opacity:0.3;margin-top:1em;">
    Last updated: {now} MST
  </div>
</body>
</html>"""

    response = make_response(html)
    response.headers["Cache-Control"] = "public, max-age=40"
    response.headers["Pragma"] = "cache"
    response.headers["Expires"] = "120"
    return response

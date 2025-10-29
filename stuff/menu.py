from flask import Flask
import requests
import datetime
import zoneinfo
import textwrap
import os, random
from flask import url_for
from flask import make_response

# ================================================================
# THEME SETTINGS
# ------------------------------------------------
# TH1 : Primary accent color (buttons, highlights)
# TH2 : Secondary shade (hover / active state)
# TH3 : Background shade (darkest layer)
# ------------------------------------------------
# Adjust these three in one place to recolor the entire app.
# ================================================================

TH1 = "#006FFF"   # blue
TH2 = "#FF9000"   # orange
TH3 = "#111111"   # dark background

def alpha(color, opacity=1.0):
    """Return color with hex alpha appended, e.g. alpha('#00BCD4', 0.8) -> '#00BCD4CC'"""
    a = int(opacity * 255)
    return f"{color}{a:02X}"



app = Flask(__name__)

@app.route("/")
def home():
    # pick a random cat background if available
    cat_dir = "static/cats"
    bg_url = ""
    try:
        files = [
            f for f in os.listdir(cat_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".gif"))
        ]
        if files:
            bg_url = f"/static/cats/{random.choice(files)}"
    except FileNotFoundError:
        pass

    html = f"""<!DOCTYPE html><html>
    <head>
    <link rel="apple-touch-icon" href="/static/apple-touch-icon.png">
    <link rel="icon" type="image/png" href="/static/apple-touch-icon.png">

    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Max's App</title>
    <style>
      body {{
        font-family:sans-serif;
        text-align:center;
        background:{TH3} url('{bg_url}') center/cover no-repeat;
        color:{TH2};
        height:100vh;
        margin:0;
        display:flex;
        flex-direction:column;
        justify-content:center;
        backdrop-filter:brightness(0.35) blur(2px);
      }}
      h2 {{
        margin-bottom:2em;
        font-size:1.6em;
        letter-spacing:1px;
        text-shadow:0 0 8px #000;
      }}
      a {{
        display:block;
        margin:1em auto;
        padding:1em 2em;
        width:120px;
        background:{alpha(TH1, 0.8)};
        color:{TH2};
        text-decoration:none;
        border-radius:7px;
        font-weight:bold;
        font-size: clamp(20px, 3vw, 22px);
      }}
      a:active {{
        background:{TH2};
      }}
    </style>
    </head>
    <body>
      <h2> </h2>
      <a href="/weather">Weather</a>
      <a href="/nhl">NHL</a>
      <a href="/game">Game</a>
      <a href="/cats">Photos</a>
    </body>
    </html>"""
    return html


@app.route("/cats")
def cats():
    cats_dir = os.path.join(app.static_folder or os.path.join(app.root_path, "static"), "cats")
    try:
        files = [
            f for f in os.listdir(cats_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp"))
        ]
    except FileNotFoundError:
        files = []

    if not files:
        return f"""
        <!DOCTYPE html><html><head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
          body{background:{TH3};color:#eee;font-family:monospace;margin:0;padding:1em;text-align:center}
          a{color:{TH1};text-decoration:none;display:inline-block;margin:1em}
        </style>
        </head><body>
          <a href="/">← MENU</a>
          <h2>🐈 Gallery</h2>
          <p>No images found in <code>static/cats</code>.</p>
        </body></html>
        """

    # pick 10 random photos (or fewer if not enough)
    sample = random.sample(files, min(10, len(files)))

    imgs = "\n".join(
        f'<img loading="lazy" src="{url_for("static", filename=f"cats/{name}")}" '
        f'style="width:min(900px,96%);max-width:100%;margin:0.75em auto;display:block;border-radius:12px;"/>'
        for name in sample
    )

    html = f"""
    <!DOCTYPE html><html><head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
      body{{background:{TH3};color:#eee;font-family:monospace;margin:0;padding:1em;text-align:center}}
      a{{color:{TH1};text-decoration:none;display:inline-block;margin:1em;font-size:1.6em}}
      h2{{margin:0.5em 0 0.25em}}
      .buttons{{margin:1em 0}}
    </style>
    </head><body>
      <div class="buttons">
        <a href="/">← BACK TO MENU</a>
        <a href="/cats?shuffle=1">🔀 SHUFFLE</a>
      </div>
      <h2> </h2>
      <p style="opacity:0.7;">Showing {len(sample)} of {len(files)} photos</p>
      {imgs}
      <div class="buttons">
        <a href="/">← MENU</a>
        <a href="/cats?shuffle=1">🔀 SHUFFLE</a>
      </div>
    </body></html>
    """
    return html



@app.route("/weather")
def weather():
    # Edmonton coordinates
    lat, lon = 53.5461, -113.4938
    url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        "&current_weather=true"
        "&hourly=relative_humidity_2m"
        "&daily=temperature_2m_max,temperature_2m_min,weathercode"
        "&timezone=America/Edmonton"
    )

    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"<pre>Weather\n=======\nError fetching data: {e}</pre>"

    current = data.get("current_weather", {})
    daily = data.get("daily", {})
    humidity_series = data.get("hourly", {}).get("relative_humidity_2m", [])
    humidity_times = data.get("hourly", {}).get("time", [])

    # Get latest humidity reading (most recent hour)
    humidity = None
    if humidity_series and humidity_times:
        try:
            # last value in hourly array should be most recent
            humidity = humidity_series[-1]
        except Exception:
            humidity = None

    def code_to_icon(code):
        icons = {
            0: "☀️ Clear",
            1: "🌤 Mostly clear",
            2: "⛅️ Partly cloudy",
            3: "☁️ Cloudy",
            45: "🌫 Fog",
            48: "🌫 Frost fog",
            51: "🌦 Drizzle",
            61: "🌧 Light rain",
            63: "🌧 Moderate rain",
            65: "🌧 Heavy rain",
            71: "🌨 Light snow",
            73: "🌨 Moderate snow",
            75: "🌨 Heavy snow",
            95: "⛈ Thunderstorm",
        }
        return icons.get(code, "❓")

    def deg_to_compass(deg):
        dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
                "S","SSW","SW","WSW","W","WNW","NW","NNW"]
        return dirs[int((deg / 22.5) + 0.5) % 16]

    lines = ["Edmonton Weather", ""]

    # Current conditions
    if current:
        icon = code_to_icon(current.get("weathercode", 0))
        temp = current.get("temperature")
        wind = current.get("windspeed")
        wind_dir = current.get("winddirection")
        wind_txt = f"{wind:.1f} km/h {deg_to_compass(wind_dir)}" if wind_dir is not None else ""
        hum_txt = f"{humidity:.0f} % humidity" if humidity is not None else ""
        lines.append(f"Now: {temp:.1f}°C  {icon}")
        lines.append(f"Wind: {wind_txt}   {hum_txt}")
        lines.append("")

    # Daily highs/lows
    temps_max = daily.get("temperature_2m_max", [])
    temps_min = daily.get("temperature_2m_min", [])
    codes = daily.get("weathercode", [])
    dates = daily.get("time", [])

    for i in range(min(3, len(dates))):
        if i == 0:
            label = "Today:"
        elif i == 1:
            label = "Tomorrow:"
        else:
            label = "Day After:"
        high = temps_max[i]
        low = temps_min[i]
        icon = code_to_icon(codes[i])
        lines.append(f"{label} {icon}  High {high:.1f} / Low {low:.1f}")

    now = datetime.datetime.now().strftime("%-I:%M %p")
    lines.append("")
    lines.append(f"Last updated {now} MST")
#
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="600">
<style>
  body {{
    background:{TH3};
    color:#eee;
    font-family: monospace;
    margin:0;
    font-size:1.3em;
    padding:1em;
    text-align:left;
  }}
  a {{
    color:{TH1};
    text-decoration:none;
    display:inline-block;
    margin-bottom:1em;
  }}
  pre {{
    font-size: clamp(15px, 3vw, 18px);
    line-height: 1.6em;
    white-space: pre-wrap;
    word-break: break-word;
  }}
</style>
</head>
<body>
  <a href="/">← MENU</a>
  <pre>{textwrap.dedent(chr(10).join(lines))}</pre>
</body>
</html>
"""

    response = make_response(html)
    response.headers["Cache-Control"] = "public, max-age=600"  # cache 10 minutes
    response.headers["Pragma"] = "cache"
    response.headers["Expires"] = "90"
    return response


    return html



@app.route("/nhl")
def nhl():
    base_url = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"
    tz = zoneinfo.ZoneInfo("America/Edmonton")
    now_local = datetime.datetime.now(tz)

    # --- Helper: Fetch data ---
    def get_data_for(date_str=None):
        url = base_url if not date_str else f"{base_url}?dates={date_str}"
        print("Fetching ESPN API:", url)
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return resp.json()

    # --- Helper: Format events ---
    def format_events(events, show_scores=True):
        lines = []

        def safe_score(team):
            if team.get("score"):
                return team["score"]
            val = team.get("linescores", [{}])[-1].get("value")
            if val not in (None, ""):
                return val
            val = team.get("statistics", [{}])[0].get("displayValue")
            if val and str(val).isdigit():
                return val
            val = team.get("records", [{}])[0].get("summary", "")
            if "-" in val:
                try:
                    return val.split("-")[-1].strip()
                except Exception:
                    pass
            return ""

        for ev in events:
            comp = ev.get("competitions", [{}])[0]
            teams = comp.get("competitors", [])
            if len(teams) < 2:
                continue

            home = next((t for t in teams if t.get("homeAway") == "home"), None)
            away = next((t for t in teams if t.get("homeAway") == "away"), None)
            if not home or not away:
                continue

            h_name, a_name = home["team"]["abbreviation"], away["team"]["abbreviation"]
            h_score = str(safe_score(home))
            a_score = str(safe_score(away))

            status_obj = ev.get("status", {})
            status_type = status_obj.get("type", {})
            desc = (status_type.get("description") or "").lower()
            clock = status_obj.get("displayClock", "")
            period = status_obj.get("period", 0)

            # --- Build readable status string ---
            if "final" in desc:
                status_str = "FINAL"
            elif "in progress" in desc or "live" in desc:
                period_names = {1:"1ST",2:"2ND",3:"3RD",4:"OT",5:"2OT"}
                per_str = period_names.get(period, f"P{period}")
                if clock == "0:00":
                    status_str = f"INT {per_str}"
                elif clock or period:
                    status_str = f"{clock} {per_str}".strip()
                else:
                    status_str = "LIVE"
            elif "scheduled" in desc or "pre" in desc:
                try:
                    date = ev.get("date", "")
                    dt = datetime.datetime.fromisoformat(date.replace("Z","+00:00")).astimezone(tz)
                    status_str = dt.strftime("%-I:%M %p").lower()
                except Exception:
                    status_str = "TBD"
            else:
                status_str = desc.upper() or "TBD"

            # --- Compose final line ---
            if show_scores:
                lines.append(f"{a_name} {a_score:<2} @ {h_name} {h_score:<2}  -  {status_str}")
            else:
                lines.append(f"{a_name} @ {h_name}  {status_str}")

        return lines

    # --- Main logic ---
    try:
        today_date = datetime.date.today()
        if now_local.hour < 9:
            show_scoreboard_for = today_date - datetime.timedelta(days=1)
        else:
            show_scoreboard_for = today_date

        sb_data = get_data_for(show_scoreboard_for.strftime("%Y%m%d"))
        today_data = get_data_for(today_date.strftime("%Y%m%d"))
        tomorrow_data = get_data_for((today_date + datetime.timedelta(days=1)).strftime("%Y%m%d"))

        sb_events = sb_data.get("events", [])
        today_events = today_data.get("events", [])
        tomorrow_events = tomorrow_data.get("events", [])

        any_started = any("in progress" in e.get("status", {}).get("type", {}).get("description", "").lower()
                          for e in today_events)
        any_final = any("final" in e.get("status", {}).get("type", {}).get("description", "").lower()
                        for e in today_events)

        lines = []
        if sb_events and now_local.hour < 9:
            lines += ["NHL SCOREBOARD", ""]
            lines += format_events(sb_events, show_scores=True)
            lines += ["", "Today's Games:", ""]
            lines += format_events(today_events, show_scores=False)
        elif today_events:
            if any_started or any_final:
                lines += ["NHL SCOREBOARD", ""]
                lines += format_events(today_events, show_scores=True)
            else:
                lines += ["Today's Games:", ""]
                lines += format_events(today_events, show_scores=False)
            lines += ["", "Tomorrow's Games:", ""]
            lines += format_events(tomorrow_events, show_scores=False)
        else:
            lines += ["No games scheduled today."]

        if now_local.hour < 9:
            refresh_seconds = 3600
        elif any_started:
            refresh_seconds = 120
        else:
            refresh_seconds = 1800

    except Exception as e:
        return f"<pre>Error fetching data: {e}</pre>"

    # --- HTML output (Rajdhani + submenu) ---
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="{refresh_seconds}">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@600&display=swap">
<style>
  body {{
    background:{TH3}; color:#eee; font-family:'Rajdhani',sans-serif;
    margin:0; padding:1em; text-align:left;
  }}
  a {{color:{TH1};text-decoration:none;display:inline-block;margin-bottom:1em;font-size:1.5em}}
  pre {{
    font-size:clamp(20px,3vw,18px);
    line-height:1.6em;
    white-space:pre-wrap;
    word-break:break-word;
  }}
  .submenu {{
    display:flex;
    justify-content:center;
    flex-wrap:wrap;
    gap:0.8em;
    margin-bottom:1em;
  }}
  .submenu a {{
    background:{alpha(TH1,0.13)};
    color:{TH1};
    padding:0.5em 1em;
    border-radius:8px;
    text-decoration:none;
    font-weight:bold;
    font-size:clamp(14px,3vw,18px);
  }}
  .submenu a:hover {{background:{alpha(TH1,0.13)};}}
  .submenu a.active {{background:{TH1};color:#000;}}
  
  .subnote {{
  text-align:center;
  font-size:0.8em;
  opacity:0.7;
  margin-top:-0.5em;
  margin-bottom:1em;
  color:{TH1};   /* or use #aaa if you want neutral gray */
  font-family:'Rajdhani',sans-serif;
}}
  
</style>
</head>
<body>
  <a href="/">← MENU</a>

  <!-- NHL sub-menu -->
  <div class="submenu">
    <a href="/nhl" class="active">Scoreboard</a>
    <a href="/nhl/standings">Standings</a>
    <a href="/nhl/stats">Stats</a>
  </div>
  <p class="subnote">Sponsored by Oreozempic</p>
  <pre>{chr(10).join(lines)}</pre>
</body>
</html>"""


    response = make_response(html)
    response.headers["Cache-Control"] = "public, max-age=40"  # 1 day
    response.headers["Pragma"] = "cache"
    response.headers["Expires"] = "30"
    return response


    return html



@app.route("/nhl/standings")
def nhl_standings_html():
    INPUT_FILE = "espn_games_2025_26.txt"
    tz = zoneinfo.ZoneInfo("America/Edmonton")

    # --- helper to update teams ---
    def update_team(team, gf, ga, result):
        if team not in teams:
            teams[team] = {"W":0,"L":0,"OTL":0,"GF":0,"GA":0,"PTS":0}
        t = teams[team]
        t["GF"] += gf
        t["GA"] += ga
        if result == "win":
            t["W"] += 1; t["PTS"] += 2
        elif result == "loss":
            t["L"] += 1
        elif result == "otl":
            t["OTL"] += 1; t["PTS"] += 1

    teams = {}

    # --- read file and build standings ---
    try:
        with open(INPUT_FILE) as f:
            lines = [ln.strip() for ln in f if ln.strip()]
    except FileNotFoundError:
        return f"<pre>File '{INPUT_FILE}' not found.</pre>"

    for line in lines:
        parts = line.split()
        if len(parts) < 6:
            continue
        if "@" not in parts:
            continue
        at_index = parts.index("@")
        try:
            away_abbr = parts[1]
            away_score = int(parts[2])
            home_abbr = parts[at_index + 1]
            home_score = int(parts[at_index + 2])
            note = parts[at_index + 3].upper() if len(parts) > at_index + 3 else ""
        except Exception:
            continue

        if home_score > away_score:
            if note in ("OT", "SO"):
                update_team(home_abbr, home_score, away_score, "win")
                update_team(away_abbr, away_score, home_score, "otl")
            else:
                update_team(home_abbr, home_score, away_score, "win")
                update_team(away_abbr, away_score, home_score, "loss")
        elif away_score > home_score:
            if note in ("OT", "SO"):
                update_team(away_abbr, away_score, home_score, "win")
                update_team(home_abbr, home_score, away_score, "otl")
            else:
                update_team(away_abbr, away_score, home_score, "win")
                update_team(home_abbr, home_score, away_score, "loss")

    sorted_teams = sorted(
        teams.items(),
        key=lambda kv: (-kv[1]["PTS"], -kv[1]["W"], -(kv[1]["GF"] - kv[1]["GA"]))
    )

    now = datetime.datetime.now(tz).strftime("%-I:%M %p %b %d, %Y")

    # --- build HTML table ---
    rows = "\n".join(
        f"<tr><td>{team}</td>"
        f"<td>{st['W']}</td>"
        f"<td>{st['L']}</td>"
        f"<td>{st['OTL']}</td>"
        f"<td>{st['GF']}</td>"
        f"<td>{st['GA']}</td>"
        f"<td>{st['PTS']}</td></tr>"
        for team, st in sorted_teams
    )

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@600&display=swap">
<style>
  body {{
    background:{TH3};color:#eee;font-family:'Rajdhani',sans-serif;
    margin:0; padding:1em; text-align:left;
  }}
  a {{color:{TH1};text-decoration:none;display:inline-block;margin-bottom:1em;font-size:1.5em}}
  table {{
    width:60%; margin-left:2em; margin-right:auto; border-collapse:collapse;
    font-size:clamp(20px,2vw,18px);
  }}
  th, td {{
    border-bottom:1px solid #333;
    padding:0.3em 0.5em;
  }}
  th {{
    background:{alpha(TH1,0.3)}; color:#000; position:sticky; top:0;
  }}
  tr:hover td {{ background:{alpha(TH1,0.13)}; }}
  td:first-child {{ text-align:left; }}
  caption {{
    caption-side:top; color:{TH1}; margin-bottom:0.8em;
    font-size:1.3em; font-weight:bold;
  }}
    .submenu {{
  display:flex;
  justify-content:center;
  flex-wrap:wrap;
  gap:0.8em;
  margin-bottom:1em;
}}
.submenu a {{
  background:{alpha(TH1,0.13)};
  color:{TH1};
  padding:0.5em 1em;
  border-radius:8px;
  text-decoration:none;
  font-weight:bold;
  font-size:clamp(14px,3vw,18px);
}}
.submenu a.active {{
  background:{TH1};
  color:#000;
}}
.submenu a:hover {{
  background:{alpha(TH1,0.25)};
}}
  
</style>
</head>
<body>
  <a href="/">← MENU</a>
    <!-- NHL sub-menu -->
  <div class="submenu">
    <a href="/nhl">Scoreboard</a>
    <a href="/nhl/standings" class="active">Standings</a>
    <a href="/nhl/stats">Stats</a>
  </div>
  <table>
    <caption>NHL Standings<br>
    <span style="font-size:0.7em;opacity:0.7;">Updated {now}</span></caption>
    <tr><th>Team</th><th>W</th><th>L</th><th>OTL</th><th>GF</th><th>GA</th><th>PTS</th></tr>
    {rows}
  </table>
</body>
</html>"""




    response = make_response(html)
    response.headers["Cache-Control"] = "public, max-age=40"  # 1 day
    response.headers["Pragma"] = "cache"
    response.headers["Expires"] = "120"
    return response


    return html




@app.route("/nhl/stats")
def nhl_stats():
    import textwrap, requests

    from flask import request

    url = "https://api-web.nhle.com/v1/skater-stats-leaders/current"
    limit = int(request.args.get("limit", 15))  # read ?limit= number from URL, default 15
    try:
        data = requests.get(url, params={"limit": limit}, timeout=8).json()

    except Exception as e:
        return f"<pre>Error fetching NHL data: {e}</pre>"

    sections = [("points", "POINTS"), ("goals", "GOALS"), ("assists", "ASSISTS")]
    out = []

    for key, title in sections:
        leaders = data.get(key, [])
        out.append(title)
        out.append("-" * len(title))
        for p in leaders[:limit]:
            first = p.get("firstName", {}).get("default", "")
            last  = p.get("lastName", {}).get("default", "")
            team  = p.get("teamAbbrev", "")
            val   = p.get("value", "?")
            name  = f"{first} {last}".strip()
            
            # highlight Edmonton players
            if team == "EDM":
                line = f"<span style='color:orange;font-weight:bold'>{name} ({team})  {val}</span>"
            else:
                line = f"{name} ({team})  {val}"
            
            out.append(line)
            
        out.append("")  # blank line between sections

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="600">
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
  h2 {{
    color:{TH1};
    text-align:left;
  }}
  a {{
    color:{TH1};
    text-decoration:none;
    display:inline-block;
    margin-bottom:1em;
    font-size:1.5em;
  }}
  pre {{
    font-size:clamp(16px,2.5vw,22px);
    line-height:1.6em;
    white-space:pre-wrap;
  }}
  .submenu {{
  display:flex;
  justify-content:center;
  flex-wrap:wrap;
  gap:0.8em;
  margin-bottom:1em;
}}
.submenu a {{
  background:{alpha(TH1,0.13)};
  color:{TH1};
  padding:0.5em 1em;
  border-radius:8px;
  text-decoration:none;
  font-weight:bold;
  font-size:clamp(14px,3vw,18px);
}}
.submenu a.active {{
  background:{TH1};
  color:#000;
}}
.submenu a:hover {{
  background:{alpha(TH1,0.25)};
}}

</style>
</head>
<body>
  <a href="/">← MENU</a>
    <!-- NHL sub-menu -->
  <div class="submenu">
    <a href="/nhl">Scoreboard</a>
    <a href="/nhl/standings">Standings</a>
    <a href="/nhl/stats" class="active">Stats</a>
  </div>
  <form method="get" action="/nhl/stats" style="margin-bottom:1em;">
   <label for="limit" style="color:{TH1};font-weight:bold;">Show top:</label>
   <select name="limit" id="limit" onchange="this.form.submit()" 
          style="padding:0.3em;border-radius:6px;font-size:1em;">
    <option value="15" {'selected' if limit==15 else ''}>15</option>
    <option value="25" {'selected' if limit==25 else ''}>25</option>
    <option value="50" {'selected' if limit==50 else ''}>50</option>
    <option value="100" {'selected' if limit==100 else ''}>100</option>
   </select>
  </form>

  <h2>Scoring Leaders</h2>
  <pre>{textwrap.dedent(chr(10).join(out))}</pre>
</body>
</html>
"""



    response = make_response(html)
    response.headers["Cache-Control"] = "public, max-age=40"  # 1 day
    response.headers["Pragma"] = "cache"
    response.headers["Expires"] = "120"
    return response


    return html





# --- Rock Paper Scissors game ---

import random
import time
from flask import request

# Keep per-IP stats + AI’s pending choice
scores = {}
ai_choices = {}


def get_client_ip():
    # Works behind simple local networks
    return request.headers.get("X-Forwarded-For", request.remote_addr)


@app.route("/game")
def game_home():
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body {{
    background:{TH3};
    color:#eee;
    font-family: monospace;
    margin:0;
    padding:2em;
    text-align:center;
    display:flex;
    flex-direction:column;
    justify-content:center;
    height:100vh;
  }}
  a.button {{
    display:inline-block;
    color:#000;
    background:{TH1};
    border:none;
    border-radius:12px;
    padding:1em 2.5em;
    margin:1em auto;
    font-weight:bold;
    text-decoration:none;
    font-size: clamp(16px,4vw,22px);
    width:200px;
  }}
  a.back {{
    background:{TH2};
    color:#eee;
  }}
</style>
</head>
<body>
  <h2>Rock Paper Scissors</h2>
  <a class="button" href="/game/prepare">PLAY</a>
  <a class="button back" href="/">← MENU</a>
</body>
</html>
"""
    return html




@app.route("/game/prepare")
def game_prepare():
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="2;url=/game/choose">
<style>
  body {{
    background:{TH3};
    color:#eee;
    font-family: monospace;
    margin:0;
    padding:2em;
    text-align:center;
  }}
</style>
</head>
<body>
  <h3>AI is preparing...</h3>
  <p>(please wait a moment)</p>
  <script>
    setTimeout(()=>{{window.location='/game/choose'}},1500);
  </script>
</body>
</html>
"""
    return html



@app.route("/game/choose")
def game_choose():
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body {{
    background:{TH3};
    color:#eee;
    font-family: monospace;
    margin:0;
    padding:2em;
    text-align:center;
  }}
  button {{
    color:#000;
    background:{TH1};
    border:none;
    border-radius:12px;
    padding:1em 2em;
    margin:0.5em;
    font-weight:bold;
    font-size: clamp(14px,3vw,18px);
  }}
</style>
</head>
<body>
  <h3>AI is ready.</h3>
  <p>Please choose:</p>
  <form action="/game/play" method="get">
    <button name="move" value="rock">🪨 ROCK</button>
    <button name="move" value="paper">📄 PAPER</button>
    <button name="move" value="scissors">✂️ SCISSORS</button>
  </form>
</body>
</html>
"""
    return html



@app.route("/game/play")
def game_play():
    ip = get_client_ip()
    player_move = request.args.get("move", "").lower()
    ai_move = ai_choices.get(ip, random.choice(["rock", "paper", "scissors"]))

    # --- Decide outcome ---
    if player_move == ai_move:
        outcome = "tie"
    elif (
        (player_move == "rock" and ai_move == "scissors")
        or (player_move == "scissors" and ai_move == "paper")
        or (player_move == "paper" and ai_move == "rock")
    ):
        outcome = "win"
    else:
        outcome = "loss"

    # --- Update per-IP stats safely ---
    stats = scores.setdefault(ip, {"wins": 0, "losses": 0, "ties": 0})
    if outcome == "win":
        stats["wins"] += 1
    elif outcome == "loss":
        stats["losses"] += 1
    else:
        stats["ties"] += 1

    ai_choices.pop(ip, None)

    result_text = {
        "win": "✅ YOU WIN!",
        "loss": "❌ YOU LOSE!",
        "tie": "🤝 TIE!",
    }[outcome]

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body {{
    background:{TH3};
    color:#eee;
    font-family: monospace;
    margin:0;
    padding:2em;
    text-align:center;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    min-height:100vh;
  }}
  h2, h3, p {{
    margin:0.5em 0;
  }}
  .buttons {{
    margin-top:2em;
    display:flex;
    flex-direction:column;
    align-items:center;
    gap:1em;
  }}
  a.button {{
    display:inline-block;
    color:#000;
    background:{TH1};
    border:none;
    border-radius:12px;
    padding:1em 2.5em;
    font-weight:bold;
    text-decoration:none;
    font-size: clamp(16px,4vw,22px);
    width:200px;
  }}
  a.back {{
    background:{TH2};
    color:#eee;
  }}
</style>
</head>
<body>
  <h3>RESULT</h3>
  <p>You chose: <b>{player_move.upper()}</b></p>
  <p>AI chose: <b>{ai_move.upper()}</b></p>
  <h2>{result_text}</h2>
  <p>(Your record: {stats['wins']}-{stats['losses']}-{stats['ties']})</p>
  <div class="buttons">
    <a class="button" href="/game/prepare">Play Again</a>
    <a class="button back" href="/">← MENU</a>
  </div>
</body>
</html>
"""
    return html




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)

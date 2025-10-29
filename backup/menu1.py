from flask import Flask
import requests
import datetime
import zoneinfo
import textwrap
import os, random
from flask import url_for

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
    <title>Maxwell's Wifi Menu</title>
    <style>
      body {{
        font-family:sans-serif;
        text-align:center;
        background:#111 url('{bg_url}') center/cover no-repeat;
        color:#eee;
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
        width:220px;
        background:#00bcd4cc;
        color:#000;
        text-decoration:none;
        border-radius:12px;
        font-weight:bold;
      }}
      a:active {{
        background:#0099aa;
      }}
    </style>
    </head>
    <body>
      <h2>Maxwell's Wifi Menu</h2>
      <a href="/weather">☀️ Weather</a>
      <a href="/nhl">🏒 NHL Stuff</a>
      <a href="/game">🎮 Game</a>
      <a href="/cats">🐈 Gallery</a>
    </body>
    </html>"""
    return html


@app.route("/cats")
def cats():
    # Resolve the absolute static/cats path safely
    cats_dir = os.path.join(app.static_folder or os.path.join(app.root_path, "static"), "cats")
    try:
        files = sorted(
            f for f in os.listdir(cats_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp"))
        )
    except FileNotFoundError:
        files = []

    # Simple empty-state
    if not files:
        return """
        <!DOCTYPE html><html><head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
          body{background:#111;color:#eee;font-family:monospace;margin:0;padding:1em;text-align:center}
          a{color:#0ff;text-decoration:none;display:inline-block;margin:1em}
        </style>
        </head><body>
          <a href="/">← Back</a>
          <h2>🐈 Gallery</h2>
          <p>No images found in <code>static/cats</code>.</p>
        </body></html>
        """

    # Build the gallery
    imgs = "\n".join(
        f'<img loading="lazy" src="{url_for("static", filename=f"cats/{name}")}" '
        f'style="width: min(900px, 96%); max-width: 100%; margin: 0.75em auto; display:block; border-radius:12px;"/>'
        for name in files
    )

    return f"""
    <!DOCTYPE html><html><head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
      body{{background:#111;color:#eee;font-family:monospace;margin:0;padding:1em;text-align:center}}
      a{{color:#0ff;text-decoration:none;display:inline-block;margin:1em}}
      h2{{margin:0.5em 0 0.25em}}
    </style>
    </head><body>
      <a href="/">← Back to Menu</a>
      <h2>🐈 Gallery</h2>
      {imgs}
    </body></html>
    """


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

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="600">
<style>
  body {{
    background:#111;
    color:#eee;
    font-family: monospace;
    margin:0;
    padding:1em;
    text-align:left;
  }}
  a {{
    color:#0ff;
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
  <a href="/">← Back</a>
  <pre>{textwrap.dedent(chr(10).join(lines))}</pre>
</body>
</html>
"""
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
            h_score, a_score = home.get("score", ""), away.get("score", "")

            status_obj = ev.get("status", {})
            status_type = status_obj.get("type", {})
            desc = (status_type.get("description") or "").lower()
            clock = status_obj.get("displayClock", "")
            period = status_obj.get("period", 0)

            # --- Build readable status string ---
            if "final" in desc:
                status_str = "FINAL"

            elif "in progress" in desc or "live" in desc:
                period_names = {1: "1ST", 2: "2ND", 3: "3RD", 4: "OT", 5: "2OT"}
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
                    dt = datetime.datetime.fromisoformat(date.replace("Z", "+00:00")).astimezone(tz)
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

        return lines  # ✅ Correctly indented inside the function

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

        lines = []
        if sb_events and now_local.hour < 9:
            lines += ["NHL SCOREBOARD", ""]
            lines += format_events(sb_events, show_scores=True)
            lines += ["", "Today's Games:", ""]
            lines += format_events(today_events, show_scores=False)
        elif today_events:
            any_started = any("in progress" in e["status"]["type"]["description"].lower()
                              for e in today_events)
            if any_started:
                lines += ["NHL SCOREBOARD", ""]
                lines += format_events(today_events, show_scores=True)
            else:
                lines += ["Today's Games:", ""]
                lines += format_events(today_events, show_scores=False)
            lines += ["", "Tomorrow's Games:", ""]
            lines += format_events(tomorrow_events, show_scores=False)
        else:
            lines += ["No games scheduled today."]

        # --- Smart refresh logic ---
        if now_local.hour < 9:
            refresh_seconds = 3600
        elif any("in progress" in e["status"]["type"]["description"].lower()
                 for e in sb_events + today_events):
            refresh_seconds = 120
        else:
            refresh_seconds = 1800

    except Exception as e:
        return f"<pre>Error fetching data: {e}</pre>"

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="{refresh_seconds}">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@600&display=swap">
<style>
  body{{background:#111;color:#eee;font-family:'Rajdhani',sans-serif;margin:0;padding:1em;text-align:left}}
  a{{color:#0ff;text-decoration:none;display:inline-block;margin-bottom:1em}}
  pre{{font-family:'Orbitron',sans-serif;font-size:clamp(20px,3vw,18px);line-height:1.6em;white-space:pre-wrap;word-break:break-word}}
  .submenu {{
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 0.8em;
    margin-bottom: 1em;
  }}
  .submenu a {{
    background: #0ff2;
    color: #0ff;
    padding: 0.5em 1em;
    border-radius: 8px;
    text-decoration: none;
    font-weight: bold;
    font-size: clamp(14px, 3vw, 18px);
  }}
  .submenu a:hover {{
    background: #0ff3;
  }}
  .submenu a.active {{
    background: #0ff;
    color: #000;
  }}
</style>
</head>
<body>
  <a href="/">← Back</a>
  <div class="submenu">
    <a href="/nhl/scoreboard" class="active">🏒 Scoreboard</a>
    <a href="/nhl/standings">📊 Standings</a>
    <a href="/nhl/stats">📈 Stats</a>
  </div>
  <pre>{textwrap.dedent(chr(10).join(lines))}</pre>
</body>
</html>"""
    return html


@app.route("/nhl/standings")
def nhl_standings():
    url = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/standings"
    tz = zoneinfo.ZoneInfo("America/Edmonton")

    try:
        print("Fetching ESPN API:", url)
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"<pre>Error fetching standings: {e}</pre>"

    lines = ["NHL STANDINGS", ""]

    try:
        # ESPN often uses data["children"] or data["standings"]["groups"]
        groups = (
            data.get("children")
            or data.get("standings", {}).get("groups")
            or data.get("groups")
            or []
        )

        if not groups:
            lines.append("(no standings data found)")
        else:
            for group in groups:
                name = group.get("name") or group.get("abbreviation") or "Division"
                lines.append(name)

                # Detect where entries live
                entries = (
                    group.get("standings", {}).get("entries")
                    or group.get("entries")
                    or []
                )

                for team in entries:
                    t = team.get("team", {}).get("abbreviation", "")
                    stats = {
                        s.get("name"): s.get("displayValue", "")
                        for s in team.get("stats", [])
                        if "displayValue" in s
                    }
                    w = stats.get("wins", "?")
                    l = stats.get("losses", "?")
                    otl = stats.get("otLosses", stats.get("ties", "0"))
                    pts = stats.get("points", "?")
                    lines.append(f"  {t:<4} {w}-{l}-{otl}  ({pts} pts)")
                lines.append("")
    except Exception as e:
        lines.append(f"Error parsing: {e}")

    now = datetime.datetime.now(tz).strftime("%-I:%M %p MST")
    lines.append(f"Updated {now}")

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500&display=swap">
<style>
  body{{background:#111;color:#eee;font-family:'Orbitron',sans-serif;margin:0;padding:1em;text-align:left}}
  a{{color:#0ff;text-decoration:none;display:inline-block;margin-bottom:1em}}
  pre{{font-size:clamp(15px,3vw,18px);line-height:1.6em;white-space:pre-wrap;word-break:break-word}}
  .submenu {{
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 0.8em;
    margin-bottom: 1em;
  }}
  .submenu a {{
    background: #0ff2;
    color: #0ff;
    padding: 0.5em 1em;
    border-radius: 8px;
    text-decoration: none;
    font-weight: bold;
    font-size: clamp(14px, 3vw, 18px);
  }}
  .submenu a:hover {{
    background: #0ff3;
  }}
  .submenu a.active {{
    background: #0ff;
    color: #000;
  }}
</style>
</head>
<body>
  <a href="/">← Back</a>

  <div class="submenu">
    <a href="/nhl/scoreboard">🏒 Scoreboard</a>
    <a href="/nhl/standings" class="active">📊 Standings</a>
    <a href="/nhl/stats">📈 Stats</a>
  </div>

  <pre>{textwrap.dedent(chr(10).join(lines))}</pre>
</body>
</html>"""
    return html




@app.route("/nhl/stats")
def nhl_stats():
    html = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500&display=swap">
<style>
  body{{background:#111;color:#eee;font-family:'Orbitron',sans-serif;
        margin:0;padding:1em;text-align:left}}
  a{{color:#0ff;text-decoration:none;display:inline-block;margin-bottom:1em}}
  h2{{text-align:center;margin-top:0.5em}}
  p{{text-align:center;opacity:0.8}}
</style>
</head>
<body>
  <a href="/nhl">← Back to NHL Menu</a>
  <h2>📈 NHL Stats</h2>
  <p>(coming soon)</p>
</body>
</html>
"""
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
    html = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body {
    background:#111;
    color:#eee;
    font-family: monospace;
    margin:0;
    padding:2em;
    text-align:center;
    display:flex;
    flex-direction:column;
    justify-content:center;
    height:100vh;
  }
  a.button {
    display:inline-block;
    color:#000;
    background:#0ff;
    border:none;
    border-radius:12px;
    padding:1em 2.5em;
    margin:1em auto;
    font-weight:bold;
    text-decoration:none;
    font-size: clamp(16px,4vw,22px);
    width:200px;
  }
  a.back {
    background:#555;
    color:#eee;
  }
</style>
</head>
<body>
  <h2>Rock Paper Scissors</h2>
  <a class="button" href="/game/prepare">PLAY</a>
  <a class="button back" href="/">← Back to Menu</a>
</body>
</html>
"""
    return html



@app.route("/game/prepare")
def game_prepare():
    ip = get_client_ip()
    ai_choices[ip] = random.choice(["rock", "paper", "scissors"])
    html = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="2;url=/game/choose">
<style>
  body {
    background:#111;
    color:#eee;
    font-family: monospace;
    margin:0;
    padding:2em;
    text-align:center;
  }
</style>
</head>
<body>
  <h3>AI is preparing...</h3>
  <p>(please wait a moment)</p>
  <script>
    setTimeout(()=>{window.location='/game/choose'},1500);
  </script>
</body>
</html>
"""
    return html


@app.route("/game/choose")
def game_choose():
    html = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body {
    background:#111;
    color:#eee;
    font-family: monospace;
    margin:0;
    padding:2em;
    text-align:center;
  }
  button {
    color:#000;
    background:#0ff;
    border:none;
    border-radius:12px;
    padding:1em 2em;
    margin:0.5em;
    font-weight:bold;
    font-size: clamp(14px,3vw,18px);
  }
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
    background:#111;
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
    background:#0ff;
    border:none;
    border-radius:12px;
    padding:1em 2.5em;
    font-weight:bold;
    text-decoration:none;
    font-size: clamp(16px,4vw,22px);
    width:200px;
  }}
  a.back {{
    background:#555;
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
    <a class="button back" href="/">← Back to Menu</a>
  </div>
</body>
</html>
"""
    return html




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)

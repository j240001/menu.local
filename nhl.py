# nhl.py
from flask import Blueprint, request, make_response
import requests, datetime, zoneinfo, os, threading, time, json
from datetime import date, timedelta
from utils import TH3, TH1, TH2, alpha

nhl_bp = Blueprint('nhl', __name__)

UPDATE_FILE = "espn_games_2025_26.txt"
STANDINGS_FILE = "espn_standings_2025_26.txt"
UPDATE_TOKEN = os.environ.get("NHL_UPDATE_TOKEN", "")
_update_lock = threading.Lock()
_last_run = 0

def update_espn_games_file(season_start=date(2025, 10, 7), out_file=UPDATE_FILE):
    """Incrementally append FINAL regular-season games to out_file.
       Returns a human-readable status string."""
    tz = zoneinfo.ZoneInfo("America/Edmonton")
    today = date.today()
    base_url = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"

    existing_lines, known_ids = [], set()
    if os.path.exists(out_file):
        with open(out_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                existing_lines.append(line)
                parts = line.split()
                if parts and parts[0].isdigit():
                    known_ids.add(parts[0])

    all_lines = existing_lines[:]
    added = 0
    d = season_start
    while d <= today:
        datestr = d.strftime("%Y%m%d")
        try:
            resp = requests.get(f"{base_url}?dates={datestr}", timeout=10)
            resp.raise_for_status()
            data = resp.json()
            for ev in data.get("events", []):
                gid = ev.get("id")
                if not gid or gid in known_ids:
                    continue

                st = ev.get("status", {}).get("type", {})
                desc = (st.get("description") or "").lower()
                if "final" not in desc:
                    continue
                if ev.get("season", {}).get("type") != 2:
                    continue

                comp = ev.get("competitions", [{}])[0]
                detail_text = " ".join([
                    str(st.get(x, "")) for x in ("shortDetail", "detail", "description")
                ] + [
                    str(comp.get("status", {}).get("type", {}).get(x, "")) for x in ("shortDetail", "detail", "description")
                ]).lower()
                note = "SO" if ("shootout" in detail_text or " so" in detail_text or "/so" in detail_text) \
                    else ("OT" if ("overtime" in detail_text or " ot" in detail_text or "/ot" in detail_text) else "")

                teams = comp.get("competitors", [])
                if len(teams) < 2:
                    continue
                home = next((t for t in teams if t.get("homeAway") == "home"), {})
                away = next((t for t in teams if t.get("homeAway") == "away"), {})

                h_name = home.get("team", {}).get("abbreviation", "???")
                a_name = away.get("team", {}).get("abbreviation", "???")
                h_score = home.get("score", "?")
                a_score = away.get("score", "?")

                line = f"{gid} {a_name} {a_score} @ {h_name} {h_score}"
                if note:
                    line += f" {note}"
                all_lines.append(line)
                known_ids.add(gid)
                added += 1
        except Exception as e:
            print(f"[NHL update] {datestr} error: {e}")
        d += timedelta(days=1)

    if added:
        with open(out_file, "w") as f:
            f.write("\n".join(all_lines))
    now = datetime.datetime.now(tz).strftime("%-I:%M %p %b %d, %Y")
    return f"Added {added} new games. Total lines: {len(all_lines)}. Updated {now}."

def update_espn_standings_file(out_file=STANDINGS_FILE):
    """Fetch and save current NHL standings to out_file."""
    tz = zoneinfo.ZoneInfo("America/Edmonton")
    standings_url = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/standings"
    try:
        resp = requests.get(standings_url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        teams = []
        for conf in data.get("standings", {}).get("conferences", []):
            for div in conf.get("divisions", []):
                for entry in div.get("teams", []):
                    t = entry.get("team", {})
                    stats = {s["name"]: s["value"] for s in entry.get("stats", [])}
                    teams.append({
                        "name": t.get("abbreviation", "???"),
                        "wins": int(stats.get("wins", 0)),
                        "losses": int(stats.get("losses", 0)),
                        "otLosses": int(stats.get("otLosses", 0)),
                        "goalsFor": int(stats.get("goalsFor", 0)),
                        "goalsAgainst": int(stats.get("goalsAgainst", 0)),
                        "points": int(stats.get("points", 0))
                    })
        teams.sort(key=lambda x: x["points"], reverse=True)
        lines = [f"NHL STANDINGS (Generated {datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')})"]
        lines.append("-" * 50)
        lines.append("Team     W   L   OTL    GF    GA   PTS")
        for team in teams:
            lines.append(f"{team['name']:<8} {team['wins']:>3} {team['losses']:>3} {team['otLosses']:>3} {team['goalsFor']:>4} {team['goalsAgainst']:>4} {team['points']:>3}")
        with open(out_file, "w") as f:
            f.write("\n".join(lines))
        return f"Standings updated with {len(teams)} teams. {datetime.datetime.now(tz).strftime('%-I:%M %p %b %d, %Y')}."
    except Exception as e:
        print(f"[NHL standings update] error: {e}")
        return f"Standings update failed: {e}"

def _should_run_now_edmonton():
    tz = zoneinfo.ZoneInfo("America/Edmonton")
    now = datetime.datetime.now(tz)
    return (18 <= now.hour <= 23) or (now.hour == 0) or (now.hour == 1) or (now.hour == 8)

def auto_updater_loop():
    global _last_run
    while True:
        try:
            if _should_run_now_edmonton():
                with _update_lock:
                    if time.time() - _last_run > 3600:  # Run at most once per hour
                        print("[NHL update] Running auto update...")
                        status_games = update_espn_games_file()
                        status_standings = update_espn_standings_file()
                        print(f"[NHL update] Games: {status_games}")
                        print(f"[NHL update] Standings: {status_standings}")
                        _last_run = time.time()
            time.sleep(300)  # Check every 5 minutes
        except Exception as e:
            print(f"[NHL update] auto loop error: {e}")
            time.sleep(300)

@nhl_bp.route("/nhl")
def nhl_scoreboard():
    tz = zoneinfo.ZoneInfo("America/Edmonton")
    today = date.today().strftime("%Y%m%d")
    base_url = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"
    try:
        resp = requests.get(f"{base_url}?dates={today}", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        events = data.get("events", [])
        games = []
        for ev in events:
            if ev.get("season", {}).get("type") != 2:  # regular season only
                continue
            st = ev.get("status", {}).get("type", {})
            desc = (st.get("description") or "").lower()
            comp = ev.get("competitions", [{}])[0]
            detail_text = " ".join([
                str(st.get(x, "")) for x in ("shortDetail", "detail", "description")
            ] + [
                str(comp.get("status", {}).get("type", {}).get(x, "")) for x in ("shortDetail", "detail", "description")
            ]).lower()
            note = "SO" if ("shootout" in detail_text or " so" in detail_text or "/so" in detail_text) \
                else ("OT" if ("overtime" in detail_text or " ot" in detail_text or "/ot" in detail_text) else "")

            teams = comp.get("competitors", [])
            if len(teams) < 2:
                continue
            home = next((t for t in teams if t.get("homeAway") == "home"), {})
            away = next((t for t in teams if t.get("homeAway") == "away"), {})

            h_name = home.get("team", {}).get("abbreviation", "???")
            a_name = away.get("team", {}).get("abbreviation", "???")
            h_score = home.get("score", "0")
            a_score = away.get("score", "0")
            status_class = "scheduled" if "scheduled" in desc else ("live" if "progress" in desc else "final")
            score_line = f"{a_name} {a_score} @ {h_name} {h_score}"
            if note:
                score_line += f" {note}"
            games.append({
                "line": score_line,
                "status": status_class,
                "gid": ev.get("id")
            })
    except Exception as e:
        games = [{"line": f"Error fetching today's games: {e}", "status": "error", "gid": None}]

    now = datetime.datetime.now(tz).strftime("%-I:%M %p %b %d, %Y")
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="60">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@600&display=swap">
<style>
  body {{ background:{TH3}; color:#eee; font-family:'Rajdhani',sans-serif; margin:0; padding:1em; text-align:left; }}
  a {{ color:{TH1}; text-decoration:none; display:inline-block; margin-bottom:1em; font-size:1.5em; }}
  pre {{ font-size:clamp(16px,2.5vw,22px); line-height:1.6em; white-space:pre-wrap; }}
  .submenu {{ display:flex; justify-content:center; flex-wrap:wrap; gap:0.8em; margin-bottom:1em; }}
  .submenu a {{ background:{alpha(TH1,0.13)}; color:{TH1}; padding:0.5em 1em; border-radius:8px; text-decoration:none; font-weight:bold; font-size:clamp(14px,3vw,18px); }}
  .submenu a.active {{ background:{TH1}; color:#000; }}
  .submenu a:hover {{ background:{alpha(TH1,0.25)}; }}
  .filters {{ margin-bottom:1em; text-align:center; }}
  .filters label {{ margin-right:1em; color:{TH1}; }}
  .game {{ padding:0.5em; border-bottom:1px solid #333; }}
  .scheduled {{ opacity:0.6; }}
  .live {{ color:{TH2}; font-weight:bold; }}
  .final {{ color:#4CAF50; }}
  input[type=checkbox] {{ margin-right:0.5em; }}
</style>
</head>
<body>
  <a href="/">← MENU</a>
  <div class="submenu">
    <a href="/nhl" class="active">Scoreboard</a>
    <a href="/nhl/standings">Standings</a>
    <a href="/nhl/stats">Stats</a>
  </div>
  <div class="filters">
    <label><input type="checkbox" id="show-scheduled" checked onchange="toggleGames('scheduled')"> Scheduled</label>
    <label><input type="checkbox" id="show-live" checked onchange="toggleGames('live')"> Live</label>
    <label><input type="checkbox" id="show-final" checked onchange="toggleGames('final')"> Final</label>
  </div>
  <pre id="games">
Today's NHL Games ({len([g for g in games if g['status'] != 'error'])})
{'='*50}
{chr(10).join(g['line'] for g in games)}
Last updated: {now}
  </pre>
  <script>
    function toggleGames(type) {{
      const cb = document.getElementById('show-' + type);
      const games = document.querySelectorAll('.game.' + type);
      games.forEach(g => g.style.display = cb.checked ? 'block' : 'none');
    }}
    const games = {json.dumps(games)};
    let grouped = {{ scheduled: [], live: [], final: [], error: [] }};
    games.forEach(g => grouped[g.status].push(g.line));
    let output = [`Today's NHL Games (${{games.filter(g => g.status !== 'error').length}}`, "=============================================="];
    for (let s of ['scheduled', 'live', 'final']) {{
      if (grouped[s].length > 0) {{
        output.push(`<div class="game ${{s}}">${{grouped[s].join('<br>')}}</div>`);
      }}
    }}
    if (grouped.error.length > 0) {{
      output.push(`<div class="game error">${{grouped.error.join('<br>')}}</div>`);
    }}
    output.push(`Last updated: {now}`);
    document.getElementById('games').innerHTML = output.join('<br>');
  </script>
</body>
</html>"""
    response = make_response(html)
    response.headers["Cache-Control"] = "no-cache"
    return response




@nhl_bp.route("/nhl/standings")
def nhl_standings():
    import textwrap
    tz = zoneinfo.ZoneInfo("America/Edmonton")
    standings_url = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/standings"
    try:
        resp = requests.get(standings_url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        teams = []
        for conf in data.get("standings", {}).get("conferences", []):
            for div in conf.get("divisions", []):
                for entry in div.get("teams", []):
                    t = entry.get("team", {})
                    stats = {s["name"]: s["value"] for s in entry.get("stats", [])}
                    teams.append({
                        "name": t.get("abbreviation", "???"),
                        "wins": int(stats.get("wins", 0)),
                        "losses": int(stats.get("losses", 0)),
                        "otLosses": int(stats.get("otLosses", 0)),
                        "goalsFor": int(stats.get("goalsFor", 0)),
                        "goalsAgainst": int(stats.get("goalsAgainst", 0)),
                        "points": int(stats.get("points", 0))
                    })
        teams.sort(key=lambda x: x["points"], reverse=True)
        out = [f"NHL STANDINGS (Live as of {datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')})"]
        out.append("-" * 50)
        out.append("Team     W   L   OTL    GF    GA   PTS")
        rows = []
        for team in teams:
            line = f"{team['name']:<8} {team['wins']:>3} {team['losses']:>3} {team['otLosses']:>3} {team['goalsFor']:>4} {team['goalsAgainst']:>4} {team['points']:>3}"
            out.append(line)
            team_html = f"<span style='color:orange;font-weight:bold'>{team['name']}</span>" if team['name'] == "EDM" else team['name']
            rows.append(f"<tr><td>{team_html}</td><td>{team['wins']}</td><td>{team['losses']}</td><td>{team['otLosses']}</td><td>{team['goalsFor']}</td><td>{team['goalsAgainst']}</td><td>{team['points']}</td></tr>")
        text = textwrap.dedent("\n".join(out))
    except Exception as e:
        text = f"Error fetching standings: {e}"
        rows = []

    now = datetime.datetime.now(tz).strftime("%-I:%M %p %b %d, %Y")
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="600">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@600&display=swap">
<style>
  body {{ background:{TH3}; color:#eee; font-family:'Rajdhani',sans-serif; margin:0; padding:1em; text-align:left; }}
  a {{ color:{TH1}; text-decoration:none; display:inline-block; margin-bottom:1em; font-size:1.5em; }}
  pre {{ font-size:clamp(16px,2.5vw,22px); line-height:1.6em; white-space:pre-wrap; }}
  table {{ width:100%; max-width:600px; border-collapse:collapse; font-size:clamp(14px,2vw,18px); margin-top:1em; }}
  th,td {{ border:1px solid #333; padding:0.5em; text-align:left; }}
  th {{ background:{alpha(TH1,0.2)}; color:{TH1}; }}
  .submenu {{ display:flex; justify-content:center; flex-wrap:wrap; gap:0.8em; margin-bottom:1em; }}
  .submenu a {{ background:{alpha(TH1,0.13)}; color:{TH1}; padding:0.5em 1em; border-radius:8px; text-decoration:none; font-weight:bold; font-size:clamp(14px,3vw,18px); }}
  .submenu a.active {{ background:{TH1}; color:#000; }}
  .submenu a:hover {{ background:{alpha(TH1,0.25)}; }}
</style>
</head>
<body>
  <a href="/">← MENU</a>
  <div class="submenu">
    <a href="/nhl">Scoreboard</a>
    <a href="/nhl/standings" class="active">Standings</a>
    <a href="/nhl/stats">Stats</a>
  </div>
  <pre>{text}</pre>
  <table>
    <tr><th>Team</th><th>W</th><th>L</th><th>OTL</th><th>GF</th><th>GA</th><th>PTS</th></tr>
    {''.join(rows)}
  </table>
  <p style="opacity:0.7;">Last updated: {now}</p>
</body>
</html>"""
    response = make_response(html)
    response.headers["Cache-Control"] = "no-cache"
    return response

@nhl_bp.route("/nhl/stats")
def nhl_stats():
    import textwrap
    url = "https://api-web.nhle.com/v1/skater-stats-leaders/current"
    limit = int(request.args.get("limit", 15))
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
            last = p.get("lastName", {}).get("default", "")
            team = p.get("teamAbbrev", "")
            val = p.get("value", "?")
            name = f"{first} {last}".strip()
            if team == "EDM":
                line = f"<span style='color:orange;font-weight:bold'>{name} ({team})  {val}</span>"
            else:
                line = f"{name} ({team})  {val}"
            out.append(line)
        out.append("")

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="600">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@600&display=swap">
<style>
  body {{ background:{TH3}; color:#eee; font-family:'Rajdhani',sans-serif; margin:0; padding:1em; text-align:left; }}
  h2 {{ color:{TH1}; text-align:left; }}
  a {{ color:{TH1}; text-decoration:none; display:inline-block; margin-bottom:1em; font-size:1.5em; }}
  pre {{ font-size:clamp(16px,2.5vw,22px); line-height:1.6em; white-space:pre-wrap; }}
  .submenu {{ display:flex; justify-content:center; flex-wrap:wrap; gap:0.8em; margin-bottom:1em; }}
  .submenu a {{ background:{alpha(TH1,0.13)}; color:{TH1}; padding:0.5em 1em; border-radius:8px; text-decoration:none; font-weight:bold; font-size:clamp(14px,3vw,18px); }}
  .submenu a.active {{ background:{TH1}; color:#000; }}
  .submenu a:hover {{ background:{alpha(TH1,0.25)}; }}
</style>
</head>
<body>
  <a href="/">← MENU</a>
  <div class="submenu">
    <a href="/nhl">Scoreboard</a>
    <a href="/nhl/standings">Standings</a>
    <a href="/nhl/stats" class="active">Stats</a>
  </div>
  <form method="get" action="/nhl/stats" style="margin-bottom:1em;">
   <label for="limit" style="color:{TH1};font-weight:bold;">Show top:</label>
   <select name="limit" id="limit" onchange="this.form.submit()" style="padding:0.3em;border-radius:6px;font-size:1em;">
    <option value="15" {'selected' if limit==15 else ''}>15</option>
    <option value="25" {'selected' if limit==25 else ''}>25</option>
    <option value="50" {'selected' if limit==50 else ''}>50</option>
    <option value="100" {'selected' if limit==100 else ''}>100</option>
   </select>
  </form>
  <h2>Scoring Leaders</h2>
  <pre>{textwrap.dedent(chr(10).join(out))}</pre>
</body>
</html>"""
    response = make_response(html)
    response.headers["Cache-Control"] = "public, max-age=40"
    response.headers["Pragma"] = "cache"
    response.headers["Expires"] = "120"
    return response

def register_nhl_updater(socketio):
    socketio.start_background_task(auto_updater_loop)

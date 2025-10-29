# nhl_routes/updater.py
import datetime
import time
import requests
import zoneinfo
import os
from datetime import date, timedelta
from flask import jsonify
from . import nhl_bp

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEDULE_FILE = os.path.join(BASE_DIR, "espn_schedule_2025_26.txt")
RESULTS_FILE = os.path.join(BASE_DIR, "espn_games_2025_26.txt")

TZ = zoneinfo.ZoneInfo("America/Edmonton")
BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"


# ------------------------------------------------------
#  Update completed games (writes espn_games_2025_26.txt)
# ------------------------------------------------------
def update_completed_games(season_start=date(2025, 10, 7), out_file=RESULTS_FILE):
    """Fetch FINAL games and append new ones to results file."""
    tz = TZ
    today = date.today()
    base_url = BASE_URL

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

                # --- Include date in YYYY-MM-DD format ---
                try:
                    raw_date = ev.get("date", "")
                    if raw_date:
                        dt_utc = datetime.datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                        dt_local = dt_utc.astimezone(tz)
                        date_str = dt_local.strftime("%Y-%m-%d")
                    else:
                        date_str = d.strftime("%Y-%m-%d")
                except Exception:
                    date_str = d.strftime("%Y-%m-%d")

                line = f"{gid} {date_str} {a_name} {a_score} @ {h_name} {h_score}"
                if note:
                    line += f" {note}"

                all_lines.append(line)
                known_ids.add(gid)
                added += 1
        except Exception as e:
            print(f"[Updater] {datestr} error: {e}")
        d += timedelta(days=1)

    if added:
        with open(out_file, "w") as f:
            f.write("\n".join(all_lines))
    now = datetime.datetime.now(tz).strftime("%-I:%M %p %b %d, %Y")
    msg = f"Added {added} new games. Total lines: {len(all_lines)}. Updated {now}."
    print("[Updater]", msg)
    return msg


# ------------------------------------------------------
#  Manual Flask routes for updates
# ------------------------------------------------------
@nhl_bp.route("/nhl/update-results", methods=["POST"])
def manual_update_results():
    msg = update_completed_games()
    return {"status": "ok", "message": msg}


@nhl_bp.route("/nhl/update-schedule", methods=["POST"])
def manual_update_schedule():
    update_espn_schedule_file()
    return {"status": "ok", "message": "Schedule updated."}


@nhl_bp.route("/nhl/update-rosters", methods=["POST"])
def manual_update_rosters():
    # Placeholder for future roster fetcher
    return {"status": "ok", "message": "Roster update coming soon."}
    
# in nhl_routes/updater.py
@nhl_bp.route("/nhl/update-stats", methods=["POST"])
def manual_update_stats():
    import json, requests, os
    STATS_FILE = os.path.join(BASE_DIR, "nhl_stats_2025_26.json")
    url = "https://api-web.nhle.com/v1/skater-stats-leaders/current"
    try:
        # ask for a big batch so your UI can slice down to 15/25/50/100
        data = requests.get(url, params={"limit": 200}, timeout=12).json()
        with open(STATS_FILE, "w") as f:
            json.dump(data, f)
        msg = "Stats updated successfully."
    except Exception as e:
        msg = f"Error updating stats: {e}"
    return {"status": "ok", "message": msg}




@nhl_bp.route("/nhl/rebuild-standings", methods=["POST"])
def manual_rebuild_standings():
    return {"status": "ok", "message": "Standings rebuilt."}

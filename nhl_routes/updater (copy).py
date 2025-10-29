# nhl_routes/updater.py
import datetime
import time
import requests
import zoneinfo
import os
from datetime import date, timedelta
import threading
from flask import jsonify
from . import nhl_bp

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEDULE_FILE = os.path.join(BASE_DIR, "espn_schedule_2025_26.txt")
RESULTS_FILE = os.path.join(BASE_DIR, "espn_games_2025_26.txt")

TZ = zoneinfo.ZoneInfo("America/Edmonton")
BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"


# ------------------------------------------------------
#  Fetch and update remaining regular-season schedule
# ------------------------------------------------------
def update_espn_schedule_file(out_file=SCHEDULE_FILE):
    """Fetch and store remaining regular-season games (dates + teams + time)."""
    print(f"[Updater] Updating schedule file: {out_file}")

    today = date.today()
    season_start = max(today - timedelta(days=1), date(2025, 10, 1))
    season_end = date(2026, 4, 30)

    d = season_start
    lines = []

    while d <= season_end:
        try:
            url = f"{BASE_URL}?dates={d.strftime('%Y%m%d')}"
            r = requests.get(url, timeout=8)
            r.raise_for_status()
            data = r.json()

            for ev in data.get("events", []):
                if ev.get("season", {}).get("type") != 2:
                    continue

                comp = ev.get("competitions", [{}])[0]
                teams = comp.get("competitors", [])
                if len(teams) < 2:
                    continue

                home = next((t for t in teams if t.get("homeAway") == "home"), {})
                away = next((t for t in teams if t.get("homeAway") == "away"), {})
                h = home.get("team", {}).get("abbreviation", "???")
                a = away.get("team", {}).get("abbreviation", "???")

                game_time = "TBD"
                try:
                    raw_date = ev.get("date", "")
                    if raw_date:
                        dt_utc = datetime.datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                        dt_local = dt_utc.astimezone(TZ)
                        game_time = dt_local.strftime("%-I:%M %p")
                except Exception:
                    pass

                lines.append(f"{d.strftime('%Y%m%d')} {a} @ {h} {game_time}")

            time.sleep(0.5)

        except Exception as e:
            print(f"[Schedule] {d} failed: {e}")
        d += timedelta(days=1)

    if not lines:
        print("[Updater] Warning: no schedule lines fetched!")
        return

    with open(out_file, "w") as f:
        f.write("\n".join(lines))

    print(f"[Updater] Schedule updated ({len(lines)} games written).")


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

                # --- include date in YYYY-MM-DD format ---
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
#  Background updater thread (for standings only)
# ------------------------------------------------------
def register_nhl_updater(app=None):
    """Launch background updater thread to refresh standings periodically."""
    print("[Updater] Background NHL updater starting (standings only).")

    def loop():
        while True:
            try:
                update_completed_games()
            except Exception as e:
                print(f"[Updater] Error updating completed games: {e}")
            time.sleep(900)  # every 15 minutes

    t = threading.Thread(target=loop, daemon=True)
    t.start()
    print("[Updater] Background NHL updater thread launched.")


# ------------------------------------------------------
#  Manual route for the 'Update Now' button
# ------------------------------------------------------
@nhl_bp.route("/nhl/update")
def manual_update():
    """Manual trigger from the standings page."""
    try:
        msg = update_completed_games()
        return jsonify({"status": "ok", "message": msg})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


# ------------------------------------------------------
#  Manual entry point (only runs schedule update)
# ------------------------------------------------------
if __name__ == "__main__":
    print("[Updater] Running one-time manual schedule update...")
    update_espn_schedule_file()
    print("[Updater] Done.")
    

# use this to only generate the completed games file    
#if __name__ == "__main__":
#    print("[Updater] Running one-time manual RESULTS rebuild...")
#    update_completed_games(out_file="espn_games_2025_26.txt")
#    print("[Updater] Done.")


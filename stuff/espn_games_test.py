from flask import Flask
import requests, datetime, zoneinfo, os

app = Flask(__name__)

@app.route("/")
def espn_games_to_file_incremental():
    tz = zoneinfo.ZoneInfo("America/Edmonton")
    today = datetime.date.today()
    season_start = datetime.date(2025, 10, 7)  # 2025–26 regular season

    out_file = "espn_games_2025_26.txt"
    base_url = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"

    # --- Step 1: read existing data and collect known IDs ---
    existing_lines = []
    known_ids = set()
    if os.path.exists(out_file):
        with open(out_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                existing_lines.append(line)
                # game ID is first token on each line
                parts = line.split()
                if parts and parts[0].isdigit():
                    known_ids.add(parts[0])

    print(f"Loaded {len(known_ids)} existing game IDs.")

    all_lines = existing_lines[:]
    added = 0

    # --- Step 2: iterate from season start to today ---
    d = season_start
    while d <= today:
        datestr = d.strftime("%Y%m%d")
        try:
            url = f"{base_url}?dates={datestr}"
            print("Fetching ESPN API:", url)
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            events = data.get("events", [])
            for ev in events:
                gid = ev.get("id")
                if not gid or gid in known_ids:
                    continue  # skip already stored games

                comp = ev.get("competitions", [{}])[0]
                status_type = ev.get("status", {}).get("type", {})
                desc = (status_type.get("description") or "").lower()
                if "final" not in desc:
                    continue
                season_type = ev.get("season", {}).get("type")
                if season_type != 2:
                    continue

                # detect OT/SO
                detail_text = " ".join([
                    str(status_type.get("shortDetail", "")),
                    str(status_type.get("detail", "")),
                    str(status_type.get("description", "")),
                    str(comp.get("status", {}).get("type", {}).get("shortDetail", "")),
                    str(comp.get("status", {}).get("type", {}).get("detail", "")),
                    str(comp.get("status", {}).get("type", {}).get("description", "")),
                ]).lower()

                note = ""
                if "shootout" in detail_text or "/so" in detail_text or " so" in detail_text:
                    note = "SO"
                elif "overtime" in detail_text or "/ot" in detail_text or " ot" in detail_text:
                    note = "OT"

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

            print(f"{datestr}: {len(events)} events processed")

        except Exception as e:
            print(f"Error fetching {datestr}: {e}")

        d += datetime.timedelta(days=1)

    # --- Step 3: write back only if we added new games ---
    if added > 0:
        with open(out_file, "w") as f:
            f.write("\n".join(all_lines))
        msg = f"Added {added} new games, total now {len(all_lines)}."
    else:
        msg = "No new games to add."

    print(msg)

    now = datetime.datetime.now(tz).strftime("%-I:%M %p %b %d, %Y")
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500&display=swap">
<style>
  body{{background:#111;color:#eee;font-family:'Orbitron',sans-serif;margin:0;padding:1em;text-align:left}}
  pre{{font-size:clamp(15px,3vw,18px);line-height:1.6em;white-space:pre-wrap;word-break:break-word}}
</style>
</head>
<body>
  <pre>{msg}\nUpdated {now}\nSaved as {out_file}</pre>
</body>
</html>"""
    return html


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

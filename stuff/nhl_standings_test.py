from flask import Flask
import requests, datetime, zoneinfo, textwrap

app = Flask(__name__)

@app.route("/")
def standings_test():
    url = "https://api-web.nhle.com/v1/standings/now"
    tz = zoneinfo.ZoneInfo("America/Edmonton")

    try:
        print("Fetching NHL API:", url)
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"<pre>Error fetching standings: {e}</pre>"

    lines = ["NHL STANDINGS (Official API)", ""]

    try:
        # This is the correct key layout: "standings" -> list of division groups
        divisions = data.get("standings", [])
        if not divisions:
            lines.append("(no standings found)")

        for div in divisions:
            division_name = div.get("divisionName") or div.get("conferenceName") or "Division"
            lines.append(division_name)

            for team in div.get("teamRecords", []):
                abbr = team.get("teamAbbrev", "")
                w = team.get("wins", "?")
                l = team.get("losses", "?")
                ot = team.get("otLosses", "?")
                pts = team.get("points", "?")
                lines.append(f"  {abbr:<4} {w}-{l}-{ot}  ({pts} pts)")

            lines.append("")  # blank line between divisions

    except Exception as e:
        lines.append(f"Error parsing data: {e}")

    now = datetime.datetime.now(tz).strftime("%-I:%M %p MST")
    lines.append(f"Updated {now}")

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
  <pre>{textwrap.dedent(chr(10).join(lines))}</pre>
</body>
</html>"""
    return html


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

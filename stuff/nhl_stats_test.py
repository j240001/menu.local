from flask import Flask
import requests, textwrap

app = Flask(__name__)

@app.route("/")
def leaders():
    # ask for top 15 instead of default 5
    url = "https://api-web.nhle.com/v1/skater-stats-leaders/current"
    try:
        data = requests.get(url, params={"limit": 15}, timeout=8).json()
    except Exception as e:
        return f"<pre>Error fetching NHL data: {e}</pre>"

    sections = [("points", "POINTS"), ("goals", "GOALS"), ("assists", "ASSISTS")]
    out = []

    for key, title in sections:
        leaders = data.get(key, [])
        out.append(title)
        out.append("-" * len(title))
        for p in leaders[:15]:
            first = p.get("firstName", {}).get("default", "")
            last  = p.get("lastName", {}).get("default", "")
            team  = p.get("teamAbbrev", "")
            val   = p.get("value", "?")
            name  = f"{first} {last}".strip()
            out.append(f"{name} ({team})  {val}")
        out.append("")  # blank line between categories

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="600">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@600&display=swap">
<style>
  body {{
    background:#111;
    color:#eee;
    font-family:'Rajdhani',sans-serif;
    margin:0;
    padding:1em;
  }}
  h2 {{
    color:#0ff;
    text-align:center;
  }}
  pre {{
    font-size:clamp(16px,2.5vw,22px);
    line-height:1.6em;
    white-space:pre-wrap;
  }}
</style>
</head>
<body>
  <h2>🏒 NHL Leaders</h2>
  <pre>{textwrap.dedent(chr(10).join(out))}</pre>
</body>
</html>
"""
    return html


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

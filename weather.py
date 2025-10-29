# weather.py
from flask import Blueprint, make_response
import requests, datetime, zoneinfo, textwrap
from utils import TH3, TH1

weather_bp = Blueprint('weather', __name__)

@weather_bp.route("/weather")
def weather():
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

    humidity = None
    if humidity_series and humidity_times:
        try:
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
    response.headers["Cache-Control"] = "public, max-age=600"
    response.headers["Pragma"] = "cache"
    response.headers["Expires"] = "90"
    return response

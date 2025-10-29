# app.py
import eventlet
eventlet.monkey_patch()

import os
import random
from flask import Flask
from flask_socketio import SocketIO
from chat import chat_bp, register_socketio_events  # Add register_socketio_events
from nhl_routes import nhl_bp
from weather import weather_bp
from game import game_bp
from photos import photos_bp

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB upload limit
socketio = SocketIO(app, cors_allowed_origins="*")

# Register blueprints
app.register_blueprint(chat_bp)
app.register_blueprint(nhl_bp)
app.register_blueprint(weather_bp)
app.register_blueprint(game_bp)
app.register_blueprint(photos_bp)

@app.route("/")
def home():
    from utils import TH3, TH2, TH1, alpha
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
      a {{
        display:block;
        margin:1em auto;
        padding:1em 2em;
        width:160px;
        background:{alpha(TH1, 0.8)};
        color:{TH2};
        text-decoration:none;
        border-radius:7px;
        font-weight:bold;
        font-size: clamp(20px, 3vw, 22px);
      }}
      a:active {{ background:{TH2}; }}
    </style>
    </head>
    <body>
      <a href="/weather">Weather</a>
      <a href="/nhl">NHL</a>
      <a href="/game">Game</a>
      <a href="/cats">Photos</a>
      <a href="/chat">Chat</a>
    </body>
    </html>"""
    return html

if __name__ == "__main__":
    register_socketio_events(socketio)  # Add chat SocketIO events
    socketio.run(app, host="0.0.0.0", port=8080)

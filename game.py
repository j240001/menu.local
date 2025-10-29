# game.py
from flask import Blueprint, request
import random
from utils import TH3, TH1, TH2

game_bp = Blueprint('game', __name__)

scores = {}
ai_choices = {}

def get_client_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr)

@game_bp.route("/game")
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

@game_bp.route("/game/prepare")
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
    setTimeout(() => {{window.location='/game/choose'}}, 1500);
  </script>
</body>
</html>
"""
    return html

@game_bp.route("/game/choose")
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

@game_bp.route("/game/play")
def game_play():
    ip = get_client_ip()
    player_move = request.args.get("move", "").lower()
    ai_move = ai_choices.get(ip, random.choice(["rock", "paper", "scissors"]))

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

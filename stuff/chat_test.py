from flask import Flask, request
from flask_socketio import SocketIO
from datetime import datetime
import json, os, random, time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

LOG_FILE = "chat_log.json"
MAX_HISTORY = 100
users = {}   # sid → {"name": str, "color": str}


# --- history helpers ---
def load_history():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return []

def save_history(history):
    with open(LOG_FILE, "w") as f:
        json.dump(history[-MAX_HISTORY:], f, indent=2)

history = load_history()


# --- main chat page ---
@app.route("/")
def chat_page():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <meta name="viewport" content="width=device-width,initial-scale=1">
      <title>Chat Room</title>
      <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@600&display=swap">
      <style>
        body {background:#111;color:#eee;font-family:'Rajdhani',sans-serif;margin:0;padding:1em;}
        #chatbox {height:70vh;overflow-y:auto;border:1px solid #333;padding:0.5em;margin-bottom:1em;background:#00000033;}
        #namebar {margin-bottom:1em;}
        input,button {font-size:1em;border:none;border-radius:6px;padding:0.4em;}
        input {width:75%;}
        button {background:#00bcd4;color:#000;font-weight:bold;padding:0.4em 1em;}
        .time {color:#888;font-size:0.8em;margin-right:0.4em;}
        .sys  {color:#0ff;}
      </style>
      <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
      <script>
        let socket;
        let username = localStorage.getItem("chat_name") || "";

        function setName(){
          const n = prompt("Enter your name:", username || "");
          if(!n) return;
          username = n.trim();
          localStorage.setItem("chat_name", username);
          socket.emit("register", username);
        }

        window.onload = () => {
          socket = io({ transports: ['websocket'] });
          if(!username) setName();
          else socket.emit("register", username);

          socket.on("history", data => {
            const chat = document.getElementById("chatbox");
            chat.innerHTML = "";
            data.forEach(m => addMsg(m));
            chat.scrollTop = chat.scrollHeight;
          });

          socket.on("chat", m => addMsg(m));
        };

        function sendMsg(){
          const box = document.getElementById('msg');
          const msg = box.value.trim();
          if(!msg) return;
          socket.emit("chat", msg);
          box.value='';
        }

        function addMsg(m){
          const chat = document.getElementById("chatbox");
          let line = `<div><span class="time">[${m.time}]</span>`;
          if(m.system) line += `<span class="sys">${m.text}</span>`;
          else line += `<span style="color:${m.color}"><b>${m.user}</b></span>: ${m.text}`;
          line += "</div>";
          chat.innerHTML += line;
          chat.scrollTop = chat.scrollHeight;
        }
      </script>
    </head>
    <body>
      <a href="/">← MENU</a>
      <h2>Chat Room</h2>
      <div id="chatbox"></div>
      <div id="namebar"><button onclick="setName()">Change name</button></div>
      <input id="msg" placeholder="Type message..." onkeydown="if(event.key==='Enter')sendMsg();">
      <button onclick="sendMsg()">Send</button>
    </body>
    </html>
    """
    return html


# --- WebSocket handlers ---
@socketio.on("connect")
def on_connect():
    sid = request.sid
    users[sid] = {"name": "Guest", "color": f"hsl({random.randint(0,359)},70%,60%)"}
    socketio.emit("history", history, to=sid)
    print(f"[+] {sid} connected")

@socketio.on("register")
def on_register(name):
    sid = request.sid
    user = users.get(sid)
    if not user:
        users[sid] = {"name": name, "color": f"hsl({random.randint(0,359)},70%,60%)"}
    else:
        user["name"] = name or "Guest"
    msg = {"time": datetime.now().strftime("%H:%M"), "system": True,
           "text": f"{name} joined the chat."}
    history.append(msg); save_history(history)
    socketio.emit("chat", msg)

@socketio.on("chat")
def on_chat(msg):
    sid = request.sid
    user = users.get(sid, {"name": "Guest", "color": "#ccc"})
    entry = {"time": datetime.now().strftime("%H:%M"),
             "user": user["name"], "text": msg, "color": user["color"]}
    history.append(entry); save_history(history)
    socketio.emit("chat", entry)

@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    user = users.pop(sid, None)
    if not user: return
    msg = {"time": datetime.now().strftime("%H:%M"), "system": True,
           "text": f"{user['name']} left the chat."}
    history.append(msg); save_history(history)
    # small delay to avoid flicker on quick refresh
    socketio.start_background_task(lambda: (time.sleep(2), socketio.emit("chat", msg)))
    print(f"[-] {sid} disconnected")


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080)

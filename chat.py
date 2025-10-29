# chat.py
from flask import Blueprint, request
from flask_socketio import SocketIO
import os, json, random, datetime, time

chat_bp = Blueprint('chat', __name__)

LOG_FILE = "chat_log.json"
MAX_HISTORY = 100
users = {}  # sid → {"name": str, "color": str}

def load_history():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return []

def save_history(history):
    with open(LOG_FILE, "w") as f:
        json.dump(history[-MAX_HISTORY:], f, indent=2)

history = load_history()

@chat_bp.route("/chat")
def chat_page():
    from utils import TH1
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
      <title>Chat Room</title>
      <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@600&display=swap">
      <style>
        html,body{{
          margin:0;
          padding:0;
          height:100%;
          background:#111;
          color:#eee;
          font-family:'Rajdhani',sans-serif;
        }}
        body{{
          display:flex;
          flex-direction:column;
          height:100dvh;
        }}
        header{{
          flex:0 0 auto;
          display:flex;
          justify-content:space-between;
          align-items:center;
          padding:0.4em 0.6em;
          background:#111;
        }}
        #chatwrap{{
          flex:1 1 auto;
          display:flex;
          flex-direction:column;
          overflow-y:auto;
          padding:0.6em;
          padding-bottom:5em;
          background:#0003;
          border-top:1px solid #333;
          border-bottom:1px solid #333;
          box-sizing:border-box;
        }}
        footer{{
          flex:0 0 auto;
          display:flex;
          gap:0.5em;
          padding:0.5em;
          background:#111;
          border-top:1px solid #333;
          position:sticky;
          bottom:env(safe-area-inset-bottom);
        }}
        #msg{{
          flex:1;
          font-size:16px;
          border:none;
          border-radius:6px;
          padding:0.6em;
          background:#222;
          color:#eee;
          overflow-y:auto;
          min-height:1.5em;
          max-height:6em;
        }}
        #msg:empty:before{{
          content:attr(data-placeholder);
          color:#777;
        }}
        button.send{{
          background:#00bcd4;
          color:#000;
          font-weight:bold;
          border:none;
          border-radius:6px;
          padding:0.6em 1.2em;
        }}
        #users{{
          position:absolute;
          right:0.5em;
          top:6em;
          width:35%;
          max-height:20vh;
          overflow-y:auto;
          border:1px solid #333;
          background:#0002;
          border-radius:6px;
          padding:0.5em;
          font-size:1em;
        }}
        .time{{color:#888;font-size:0.8em;margin-right:0.4em;}}
        .sys{{color:#666;}}
      </style>
      <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
      <script>
        let socket;
        let username = localStorage.getItem("chat_name") || "";

        function setName(){{
          const n = prompt("Enter your name:", username || "");
          if(!n) return;
          username = n.trim();
          localStorage.setItem("chat_name", username);
          socket.emit("register", username);
        }}

        window.onload = ()=>{{
          socket = io({{transports:['websocket']}});
          if(!username) setName(); else socket.emit("register", username);
          socket.on("history", data=>{{
            const chat=document.getElementById("chatwrap");
            chat.innerHTML="";
            data.forEach(m=>addMsg(m));
            chat.scrollTop=chat.scrollHeight;
          }});
          socket.on("chat", m=>addMsg(m));
          socket.on("users", list=>updateUsers(list));
        }};

        function sendMsg(){{
          const box=document.getElementById('msg');
          const msg=box.innerText.trim();
          if(!msg) return;
          socket.emit("chat", msg);
          box.innerText='';
        }}

        function addMsg(m){{
          const chat=document.getElementById("chatwrap");
          let line=`<div><span class="time">[${{m.time}}]</span>`;
          if(m.system) line+=`<span class="sys">${{m.text}}</span>`;
          else line+=`<span style="color:${{m.color}}"><b>${{m.user}}</b></span>: ${{m.text}}`;
          line+="</div>";
          chat.innerHTML+=line;
          chat.scrollTop=chat.scrollHeight;
        }}

        function updateUsers(list){{
          const u=document.getElementById("users");
          u.innerHTML="<b>Online</b><hr style='border:0;border-top:1px solid #333'>";
          list.forEach(n=>{{u.innerHTML+=`<div>${{n}}</div>`}});
        }}
      </script>
    </head>
    <body>
      <header>
        <h2><a href="/" style="color:#0ff;text-decoration:none;">← MENU</a> Chat Room</h2>
        <button onclick="setName()">Change name</button>
      </header>

      <div id="chatwrap"></div>

      <footer>
        <div id="msg"
             contenteditable="true"
             role="textbox"
             aria-label="Type message"
             data-placeholder="Type message..."
             onkeydown="if(event.key==='Enter'){{event.preventDefault();sendMsg();}}">
        </div>
        <button class="send" onclick="sendMsg()">Send</button>
      </footer>

      <div id="users"></div>
    </body>
    </html>
    """
    return html

def register_socketio_events(socketio):
    @socketio.on("chat")
    def on_chat(msg):
        sid = request.sid
        user = users.get(sid, {"name": "Guest", "color": "#ccc"})
        entry = {"time": datetime.datetime.now().strftime("%H:%M"),
                 "user": user["name"], "text": msg, "color": user["color"]}
        history.append(entry); save_history(history)
        socketio.emit("chat", entry)

    @socketio.on("connect")
    def on_connect():
        sid = request.sid
        users[sid] = {"name": "Guest", "color": f"hsl({random.randint(0,359)},70%,60%)"}
        socketio.emit("history", history, to=sid)
        socketio.emit("users", [u["name"] for u in users.values()])

    @socketio.on("register")
    def on_register(name):
        sid = request.sid
        user = users.get(sid, {"name": "Guest"})
        user["name"] = name or "Guest"
        users[sid] = user
        msg = {"time": datetime.datetime.now().strftime("%H:%M"), "system": True,
               "text": f"{user['name']} joined the chat."}
        history.append(msg); save_history(history)
        socketio.emit("chat", msg)
        socketio.emit("users", [u["name"] for u in users.values()])

    @socketio.on("disconnect")
    def on_disconnect():
        sid = request.sid
        user = users.pop(sid, None)
        if user:
            msg = {"time": datetime.datetime.now().strftime("%H:%M"), "system": True,
                   "text": f"{user['name']} left the chat."}
            history.append(msg); save_history(history)
            socketio.start_background_task(lambda: (time.sleep(1), socketio.emit("chat", msg)))
        socketio.emit("users", [u["name"] for u in users.values()])

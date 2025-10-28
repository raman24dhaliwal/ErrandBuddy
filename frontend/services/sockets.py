# frontend/services/socket.py
import socketio

# simple client
sio = socketio.Client()

def connect(url="http://127.0.0.1:5000"):
    try:
        sio.connect(url)
    except Exception as e:
        print("Socket connect error:", e)

def send_message(room, payload):
    sio.emit("message", {"room": room, **payload})

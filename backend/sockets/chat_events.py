# basic socketio handlers (requires hooking into socketio instance in app if needed)
# This file is a template; in this skeleton we use HTTP chat endpoints primarily.
from flask_socketio import emit, join_room, leave_room


def register_socket_handlers(socketio):
    @socketio.on("join")
    def handle_join(data):
        room = data.get("room")
        join_room(room)
        emit("status", {"msg": f"{data.get('username')} joined."}, room=room)

    @socketio.on("leave")
    def handle_leave(data):
        room = data.get("room")
        leave_room(room)
        emit("status", {"msg": f"{data.get('username')} left."}, room=room)

    @socketio.on("message")
    def handle_message(data):
        room = data.get("room")
        emit("message", data, room=room)


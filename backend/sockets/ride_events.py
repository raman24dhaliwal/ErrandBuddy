def register_ride_handlers(socketio):
    @socketio.on("ride_create")
    def handle_ride_create(data):
        # broadcast new ride
        socketio.emit("new_ride", data)


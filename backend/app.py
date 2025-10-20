from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO

from config import Config
from database import db

def create_app():
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(Config)

    # init extensions
    db.init_app(app)
    jwt = JWTManager(app)
    socketio = SocketIO(app, cors_allowed_origins="*")

    # register routes
    with app.app_context():
        # import blueprints
        from routes import auth, tasks, chat, rides, users
        app.register_blueprint(auth.bp)
        app.register_blueprint(tasks.bp)
        app.register_blueprint(chat.bp)
        app.register_blueprint(rides.bp)
        app.register_blueprint(users.bp)

    # simple health route
    @app.route("/")
    def index():
        return jsonify({"status": "ErrandBuddy Backend Running"})

    return app, socketio

if __name__ == "__main__":
    app, socketio = create_app()
    # create db if not exists
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)

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

        # register socket.io event handlers
        try:
            from sockets.chat_events import register_socket_handlers
            from sockets.ride_events import register_ride_handlers
            register_socket_handlers(socketio)
            register_ride_handlers(socketio)
        except Exception as e:
            # Avoid crashing app if sockets package missing; log to console
            print("Socket handlers not registered:", e)

    # simple health route
    @app.route("/")
    def index():
        return jsonify({"status": "ErrandBuddy Backend Running"})

    # overview JSON showing all tasks with owner usernames
    @app.route("/overview")
    def overview():
        from models.task import Task
        tasks = Task.query.order_by(Task.created_at.desc()).all()
        payload = []
        for t in tasks:
            payload.append({
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "user_id": t.user_id,
                "username": t.owner.username if getattr(t, 'owner', None) else None,
                "created_at": t.created_at.isoformat(),
            })
        return jsonify({"count": len(payload), "tasks": payload})

    # simple admin HTML table for quick viewing in browser
    @app.route("/admin/tasks")
    def admin_tasks():
        from models.task import Task
        rows = [
            f"<tr><td>{t.id}</td><td>{t.title}</td><td>{t.owner.username if getattr(t,'owner',None) else ''}</td><td>{t.created_at.strftime('%Y-%m-%d %H:%M:%S')}</td></tr>"
            for t in Task.query.order_by(Task.created_at.desc()).all()
        ]
        table = """
        <html><head><title>Tasks Admin</title>
        <style>body{font-family:Segoe UI,Arial} table{border-collapse:collapse} td,th{border:1px solid #ddd;padding:6px}</style>
        </head><body>
        <h3>All Tasks</h3>
        <table>
          <thead><tr><th>ID</th><th>Title</th><th>Username</th><th>Created</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>
        </body></html>
        """.replace("{rows}", "\n".join(rows))
        return table

    return app, socketio

if __name__ == "__main__":
    app, socketio = create_app()
    # create db if not exists
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)

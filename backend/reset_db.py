from app import create_app
from database import db


def reset_all():
    app, _ = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database reset: dropped and recreated all tables.")


if __name__ == "__main__":
    reset_all()


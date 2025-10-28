import sys
from sqlalchemy import or_

from app import create_app
from database import db
from models import User, Task, Message, Ride, EmailOTP


def delete_user_by_email(email: str) -> str:
    app, _ = create_app()
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            return "user-not-found"

        # Delete dependent rows first to satisfy FK constraints
        Message.query.filter(or_(Message.sender_id == user.id, Message.receiver_id == user.id)).delete(synchronize_session=False)
        Task.query.filter_by(user_id=user.id).delete(synchronize_session=False)
        Ride.query.filter_by(driver_id=user.id).delete(synchronize_session=False)
        EmailOTP.query.filter_by(user_id=user.id).delete(synchronize_session=False)

        db.session.delete(user)
        db.session.commit()
        return "user-deleted"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python backend/admin_delete_user.py <email>")
        sys.exit(1)
    email = sys.argv[1].strip()
    print(delete_user_by_email(email))


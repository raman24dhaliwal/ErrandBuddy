from datetime import datetime
from database import db

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    bio = db.Column(db.String(300), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tasks = db.relationship("Task", backref="owner", lazy=True)
    sent_messages = db.relationship("Message", backref="sender", foreign_keys="Message.sender_id", lazy=True)
    received_messages = db.relationship("Message", backref="receiver", foreign_keys="Message.receiver_id", lazy=True)
    rides = db.relationship("Ride", backref="driver", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "bio": self.bio,
            "created_at": self.created_at.isoformat(),
        }

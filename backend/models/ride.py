from datetime import datetime
from database import db

class Ride(db.Model):
    __tablename__ = "rides"
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    origin = db.Column(db.String(200))
    destination = db.Column(db.String(200))
    time = db.Column(db.String(100))  # simplified string for demo
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "driver_id": self.driver_id,
            "origin": self.origin,
            "destination": self.destination,
            "time": self.time,
            "created_at": self.created_at.isoformat(),
        }

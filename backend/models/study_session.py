from datetime import datetime
from database import db


class StudySession(db.Model):
    __tablename__ = "study_sessions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    course = db.Column(db.String(120), nullable=False)
    available = db.Column(db.Boolean, default=True)
    campus = db.Column(db.String(30), default="Surrey")
    teacher = db.Column(db.String(120), default="")
    description = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "course": self.course,
            "available": bool(self.available),
            "campus": self.campus,
            "teacher": self.teacher,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
        }

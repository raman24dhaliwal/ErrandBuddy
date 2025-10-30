from datetime import datetime
from database import db
from sqlalchemy import Integer, ForeignKey

class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    # Optional association to a task; when set, the conversation is between
    # the task owner and the assignee.
    task_id = db.Column(Integer, ForeignKey("tasks.id"), nullable=True)
    content = db.Column(db.String(2000))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "task_id": self.task_id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }

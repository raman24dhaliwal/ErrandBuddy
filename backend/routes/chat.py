from flask import Blueprint, request, jsonify
from database import db
from models.message import Message
from models.user import User
from models.task import Task
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint("chat", __name__, url_prefix="/chat")

@bp.route("/messages/<int:other_id>", methods=["GET"])
@jwt_required()
def get_conversation(other_id):
    user_id = int(get_jwt_identity())
    msgs = Message.query.filter(
        ((Message.sender_id == user_id) & (Message.receiver_id == other_id)) |
        ((Message.sender_id == other_id) & (Message.receiver_id == user_id))
    ).order_by(Message.timestamp.asc()).all()
    return jsonify([m.to_dict() for m in msgs])

@bp.route("/send", methods=["POST"])
@jwt_required()
def send_message():
    data = request.get_json() or {}
    user_id = int(get_jwt_identity())
    receiver_id = data.get("receiver_id")
    content = data.get("content")
    if not receiver_id or not content:
        return jsonify({"msg": "Missing data"}), 400
    # ensure receiver exists
    rec = User.query.get(receiver_id)
    if not rec:
        return jsonify({"msg": "Receiver not found"}), 404
    msg = Message(sender_id=user_id, receiver_id=receiver_id, content=content)
    db.session.add(msg)
    db.session.commit()
    return jsonify({"msg": "Message sent", "message": msg.to_dict()}), 201


@bp.route("/overview", methods=["GET"])
@jwt_required()
def conversations_overview():
    """Return a list of active conversations for the current user, most recent first.
    Each item may be a direct message (dm) or task chat.
    """
    user_id = int(get_jwt_identity())
    msgs = (
        Message.query
        .filter((Message.sender_id == user_id) | (Message.receiver_id == user_id))
        .order_by(Message.timestamp.desc())
        .limit(500)
        .all()
    )
    convs = {}
    other_ids = set()
    for m in msgs:
        if m.task_id:
            key = ("task", m.task_id)
            other_id = m.receiver_id if m.sender_id == user_id else m.sender_id
            if key not in convs:
                convs[key] = {
                    "type": "task",
                    "task_id": m.task_id,
                    "other_id": other_id,
                    "last_message": m.to_dict(),
                    "updated_at": m.timestamp.isoformat(),
                }
                if other_id:
                    other_ids.add(other_id)
        else:
            other_id = m.receiver_id if m.sender_id == user_id else m.sender_id
            key = ("dm", other_id)
            if key not in convs:
                convs[key] = {
                    "type": "dm",
                    "other_id": other_id,
                    "task_id": None,
                    "last_message": m.to_dict(),
                    "updated_at": m.timestamp.isoformat(),
                }
                if other_id:
                    other_ids.add(other_id)
    users = {}
    if other_ids:
        rows = User.query.filter(User.id.in_(list(other_ids))).all()
        for u in rows:
            users[u.id] = u.to_dict()
    items = []
    for v in convs.values():
        o = users.get(v.get("other_id")) if v.get("other_id") else None
        if o:
            v["other"] = {
                "id": o.get("id"),
                "username": o.get("username"),
                "first_name": o.get("first_name"),
                "last_name": o.get("last_name"),
            }
        items.append(v)
    items.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return jsonify(items)


@bp.route("/task/<int:task_id>", methods=["GET"])
@jwt_required()
def task_conversation(task_id):
    """Return messages for a specific task between owner and assignee.
    Only participants can view.
    """
    user_id = int(get_jwt_identity())
    t = Task.query.get_or_404(task_id)
    if not t.assignee_id:
        return jsonify({"msg": "Task has no assignee yet."}), 400
    if user_id not in (t.user_id, t.assignee_id):
        return jsonify({"msg": "Not authorized for this conversation."}), 403
    msgs = (
        Message.query.filter(Message.task_id == task_id)
        .order_by(Message.timestamp.asc())
        .all()
    )
    return jsonify([m.to_dict() for m in msgs])


@bp.route("/task/<int:task_id>/send", methods=["POST"])
@jwt_required()
def task_send(task_id):
    """Send a message for a specific task; receiver is inferred.
    Only owner or assignee may send.
    """
    user_id = int(get_jwt_identity())
    t = Task.query.get_or_404(task_id)
    if not t.assignee_id:
        return jsonify({"msg": "Task has no assignee yet."}), 400
    if user_id not in (t.user_id, t.assignee_id):
        return jsonify({"msg": "Not authorized to send for this task."}), 403
    other_id = t.assignee_id if user_id == t.user_id else t.user_id
    data = request.get_json() or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"msg": "Message content required."}), 400
    msg = Message(sender_id=user_id, receiver_id=other_id, task_id=task_id, content=content)
    db.session.add(msg)
    db.session.commit()
    return jsonify({"msg": "Message sent", "message": msg.to_dict()}), 201
